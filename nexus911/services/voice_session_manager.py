"""
Voice Session Manager — Manages multiple concurrent Gemini Live API sessions.

Each 911 caller gets their own voice session with a role-specific agent.
All agents share the Incident Knowledge Graph via tool functions.
"""
import asyncio
import uuid
import logging
import json
import base64
from typing import Optional
from dataclasses import dataclass, field

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.streaming import LiveRequestQueue

from core.incident_graph import incident_manager, CallerInfo, CallerRole
from core.config import settings
from agents.caller_agent.agent import create_caller_agent
from agents.tools.incident_tools import report_new_emergency, add_caller_to_incident

logger = logging.getLogger("nexus911.voice")


@dataclass
class VoiceSession:
    """Represents one active voice session with a caller."""
    session_id: str
    caller_id: str
    incident_id: str
    caller_role: str
    agent: Agent
    runner: Runner
    live_queue: LiveRequestQueue
    is_active: bool = True
    created_at: float = field(default_factory=lambda: __import__("time").time())


class VoiceSessionManager:
    """
    Manages all active voice sessions.

    Each caller gets:
    1. A role-specific ADK Agent
    2. A Runner with streaming enabled
    3. A LiveRequestQueue for bidirectional audio
    4. Connection to the shared Incident Knowledge Graph
    """

    def __init__(self):
        self.sessions: dict[str, VoiceSession] = {}
        self.session_service = InMemorySessionService()

    async def create_session(
        self,
        incident_id: str = "",
        caller_role: str = "UNKNOWN",
        caller_name: str = "",
        caller_location: str = "",
        description: str = "",
    ) -> VoiceSession:
        """
        Create a new voice session for an incoming 911 caller.

        1. If no incident_id, check for existing incident or create new
        2. Create role-specific agent
        3. Set up ADK Runner with streaming
        4. Return session ready for audio streaming
        """
        session_id = f"voice_{uuid.uuid4().hex[:8]}"

        # Step 1: Handle incident assignment
        if not incident_id:
            result = report_new_emergency(
                location=caller_location,
                description=description,
            )
            incident_id = result["incident_id"]
            logger.info(f"Caller assigned to incident {incident_id}: {result['status']}")

        # Step 2: Register caller in incident
        caller_result = add_caller_to_incident(
            incident_id=incident_id,
            caller_role=caller_role,
            caller_name=caller_name,
            caller_location=caller_location,
        )
        caller_id = caller_result.get("caller_id", f"caller_{uuid.uuid4().hex[:6]}")

        # Step 3: Create role-specific agent
        agent = create_caller_agent(caller_role, incident_id)

        # Step 4: Set up ADK Runner
        runner = Runner(
            agent=agent,
            app_name="nexus911",
            session_service=self.session_service,
        )

        # Step 5: Create LiveRequestQueue for streaming
        live_queue = LiveRequestQueue()

        # Step 6: Create session
        session = VoiceSession(
            session_id=session_id,
            caller_id=caller_id,
            incident_id=incident_id,
            caller_role=caller_role,
            agent=agent,
            runner=runner,
            live_queue=live_queue,
        )

        self.sessions[session_id] = session
        logger.info(
            f"Voice session created: {session_id} | "
            f"Caller: {caller_name} ({caller_role}) | "
            f"Incident: {incident_id}"
        )

        return session

    async def stream_audio_to_session(
        self, session_id: str, audio_data: bytes
    ):
        """Send audio data from caller's microphone to the agent."""
        session = self.sessions.get(session_id)
        if not session or not session.is_active:
            return

        # Send audio to the LiveRequestQueue
        # ADK handles the Gemini Live API WebSocket internally
        session.live_queue.send_realtime(
            audio=base64.b64encode(audio_data).decode("utf-8")
        )

    async def start_streaming(self, session_id: str):
        """
        Start the bidirectional streaming loop for a session.

        This runs the ADK Runner in live mode, which:
        1. Connects to Gemini Live API via WebSocket
        2. Streams audio in (from caller mic)
        3. Gets audio out (agent's voice response)
        4. Handles tool calls (submit_intel, report_emergency, etc.)
        5. Handles barge-in (caller can interrupt agent)

        Returns an async generator of events (audio, text, tool calls).
        """
        session = self.sessions.get(session_id)
        if not session:
            return

        logger.info(f"Starting streaming for session {session_id}")

        # Run the agent in live/streaming mode
        async for event in session.runner.run_live(
            session_id=session_id,
            live_request_queue=session.live_queue,
            user_id=session.caller_id,
        ):
            # Yield events to the WebSocket handler
            # Events include: audio responses, text transcriptions, tool calls
            yield event

    async def end_session(self, session_id: str):
        """End a voice session and clean up."""
        session = self.sessions.get(session_id)
        if session:
            session.is_active = False
            session.live_queue.close()
            logger.info(f"Session ended: {session_id}")

            # Update caller status in incident graph
            incident = incident_manager.get_incident(session.incident_id)
            if incident and session.caller_id in incident.callers:
                incident.callers[session.caller_id].status = "disconnected"

    def get_active_sessions(self) -> list[dict]:
        """Get all active voice sessions for the dashboard."""
        return [
            {
                "session_id": s.session_id,
                "caller_id": s.caller_id,
                "incident_id": s.incident_id,
                "caller_role": s.caller_role,
                "is_active": s.is_active,
            }
            for s in self.sessions.values()
            if s.is_active
        ]

    @property
    def active_count(self) -> int:
        return sum(1 for s in self.sessions.values() if s.is_active)


# Singleton
voice_manager = VoiceSessionManager()
