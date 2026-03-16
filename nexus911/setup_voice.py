"""
Nexus911 Voice Integration Setup Script
========================================
Run this to add voice capabilities to your existing nexus911 project.

Usage:
  cd nexus911
  python setup_voice.py

Then test:
  Step 1 (quick test):  cd streaming_test && adk web
  Step 2 (full system): python run.py
"""
import os

PROJECT_ROOT = "."  # Run from inside nexus911/

FILES = {}

# ══════════════════════════════════════════════════════════════
# STEP 0: Update requirements.txt with voice dependencies
# ══════════════════════════════════════════════════════════════
FILES["requirements_voice.txt"] = """# Additional voice dependencies — append to requirements.txt
# For Windows: pip install PyAudio (may need pipwin)
#   pip install pipwin
#   pipwin install pyaudio
# OR download from https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
PyAudio>=0.2.14
google-genai>=1.10.0
google-adk>=1.2.0
"""

# ══════════════════════════════════════════════════════════════
# STEP 1: QUICK TEST — Verify voice works with ADK web UI
# ══════════════════════════════════════════════════════════════
# This creates a standalone streaming agent you can test in 2 minutes
# using ADK's built-in web UI with microphone support

FILES["streaming_test/.env"] = """GOOGLE_API_KEY=PASTE_YOUR_KEY_HERE
GOOGLE_GENAI_USE_VERTEXAI=FALSE
"""

FILES["streaming_test/nexus911_voice_test/__init__.py"] = """from . import agent
"""

FILES["streaming_test/nexus911_voice_test/agent.py"] = """\"\"\"
Quick test: A single Nexus911 caller agent with voice.
Run with: cd streaming_test && adk web --no-reload
Then open http://localhost:8000, select nexus911_voice_test,
click the microphone button, and start talking.

Say something like: "Help, there's a man threatening my neighbor,
I'm at 742 Evergreen Terrace"
\"\"\"
from google.adk.agents import Agent


def report_emergency(location: str, description: str, severity: str = "HIGH") -> dict:
    \"\"\"Report a new emergency. Called when caller describes their situation.

    Args:
        location: Where the emergency is happening
        description: What is happening
        severity: CRITICAL, HIGH, MEDIUM, or LOW

    Returns:
        dict confirming the emergency was logged
    \"\"\"
    return {
        "status": "emergency_logged",
        "incident_id": "inc_test_001",
        "message": f"Emergency logged at {location}. Units being dispatched. Severity: {severity}",
    }


def submit_intel(incident_id: str, intel: str) -> dict:
    \"\"\"Submit new intelligence about the incident.

    Args:
        incident_id: The incident ID
        intel: New information from the caller

    Returns:
        dict confirming intel was recorded
    \"\"\"
    return {
        "status": "intel_recorded",
        "message": f"Intelligence recorded: {intel}. This has been shared with all responding units.",
    }


def get_safety_instructions(situation: str) -> dict:
    \"\"\"Get safety instructions for the caller based on their situation.

    Args:
        situation: Type of danger (active_shooter, domestic_violence, fire, medical)

    Returns:
        dict with safety instructions
    \"\"\"
    instructions = {
        "domestic_violence": [
            "If you can safely leave, do so now.",
            "Go to a neighbor's house or any public place.",
            "If you cannot leave, get to a room with a lock.",
            "Officers are being dispatched right now.",
        ],
        "active_shooter": [
            "If you can safely exit, run away from the sounds.",
            "If you cannot exit, find a room to lock or barricade.",
            "Turn off lights and silence your phone.",
            "Stay low and away from windows.",
        ],
        "fire": [
            "Leave the building immediately.",
            "Stay low to avoid smoke.",
            "Do not use elevators.",
            "Once outside, move away from the building.",
        ],
        "medical": [
            "Stay with the person.",
            "Do not move them unless they are in danger.",
            "Paramedics are on their way.",
        ],
    }
    result = instructions.get(situation, instructions["medical"])
    return {"instructions": result}


# ── The Agent ────────────────────────────────────────────────
# Use a Live API compatible model for voice streaming
root_agent = Agent(
    name="nexus911_caller_agent",
    model="gemini-2.5-flash-preview-native-audio-dialog",
    description="Nexus911 emergency caller agent with real-time voice",
    instruction=\"\"\"You are a Nexus911 Emergency Agent handling a live 911 call.

You speak with a calm, clear, empathetic voice. You are trained to handle
emergency situations and extract critical information from callers.

WHEN A CALLER CONNECTS:
1. Greet them: "911, what is your emergency?"
2. Listen carefully to their response
3. Use report_emergency to log the incident with location and description
4. Determine the type of emergency and use get_safety_instructions
5. Continue gathering intel using submit_intel for any new information
6. Keep the caller calm and informed that help is on the way

VOICE BEHAVIOR:
- Speak slowly and clearly
- Use short sentences
- Repeat critical information back to confirm
- If the caller is a child, use simple words and a gentle tone
- Never hang up — keep the line open

INFORMATION TO GATHER:
- Exact location (address, landmarks, floor/room)
- Nature of emergency
- Number of people involved
- Whether weapons are present
- Whether anyone is injured
- Description of suspect if applicable
- Whether children are involved

Remember: Every second counts. Be efficient but compassionate.
\"\"\",
    tools=[
        report_emergency,
        submit_intel,
        get_safety_instructions,
    ],
)
"""

# ══════════════════════════════════════════════════════════════
# STEP 2: FULL MULTI-AGENT VOICE SERVICE
# ══════════════════════════════════════════════════════════════
# Manages multiple simultaneous Gemini Live API sessions,
# one per caller, all feeding the shared Incident Knowledge Graph

FILES["services/voice_session_manager.py"] = """\"\"\"
Voice Session Manager — Manages multiple concurrent Gemini Live API sessions.

Each 911 caller gets their own voice session with a role-specific agent.
All agents share the Incident Knowledge Graph via tool functions.
\"\"\"
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
    \"\"\"Represents one active voice session with a caller.\"\"\"
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
    \"\"\"
    Manages all active voice sessions.

    Each caller gets:
    1. A role-specific ADK Agent
    2. A Runner with streaming enabled
    3. A LiveRequestQueue for bidirectional audio
    4. Connection to the shared Incident Knowledge Graph
    \"\"\"

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
        \"\"\"
        Create a new voice session for an incoming 911 caller.

        1. If no incident_id, check for existing incident or create new
        2. Create role-specific agent
        3. Set up ADK Runner with streaming
        4. Return session ready for audio streaming
        \"\"\"
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
        \"\"\"Send audio data from caller's microphone to the agent.\"\"\"
        session = self.sessions.get(session_id)
        if not session or not session.is_active:
            return

        # Send audio to the LiveRequestQueue
        # ADK handles the Gemini Live API WebSocket internally
        session.live_queue.send_realtime(
            audio=base64.b64encode(audio_data).decode("utf-8")
        )

    async def start_streaming(self, session_id: str):
        \"\"\"
        Start the bidirectional streaming loop for a session.

        This runs the ADK Runner in live mode, which:
        1. Connects to Gemini Live API via WebSocket
        2. Streams audio in (from caller mic)
        3. Gets audio out (agent's voice response)
        4. Handles tool calls (submit_intel, report_emergency, etc.)
        5. Handles barge-in (caller can interrupt agent)

        Returns an async generator of events (audio, text, tool calls).
        \"\"\"
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
        \"\"\"End a voice session and clean up.\"\"\"
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
        \"\"\"Get all active voice sessions for the dashboard.\"\"\"
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
"""

# ══════════════════════════════════════════════════════════════
# STEP 3: WebSocket endpoint for browser-based voice
# ══════════════════════════════════════════════════════════════

FILES["api/voice_websocket.py"] = """# Voice WebSocket for 911 caller agents.
# Browser connects here, streams mic audio, receives agent voice responses.
import json
import base64
import logging
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from services.voice_session_manager import voice_manager

logger = logging.getLogger("nexus911.voice_ws")


async def handle_voice_websocket(websocket: WebSocket):
    \"\"\"Handle a single voice WebSocket connection from the browser.\"\"\"
    await websocket.accept()
    session_id = None
    streaming_task = None

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type")

            if msg_type == "start_session":
                # Create a new voice session
                session = await voice_manager.create_session(
                    caller_name=msg.get("caller_name", "Anonymous"),
                    caller_location=msg.get("location", ""),
                    caller_role=msg.get("caller_role", "UNKNOWN"),
                    description=msg.get("description", ""),
                )
                session_id = session.session_id

                await websocket.send_text(json.dumps({
                    "type": "session_started",
                    "session_id": session_id,
                    "incident_id": session.incident_id,
                    "caller_id": session.caller_id,
                }))

                # Start the streaming loop in background
                streaming_task = asyncio.create_task(
                    _stream_responses(websocket, session_id)
                )

                logger.info(f"Voice WebSocket session started: {session_id}")

            elif msg_type == "audio" and session_id:
                # Forward audio from browser to agent
                audio_bytes = base64.b64decode(msg["data"])
                await voice_manager.stream_audio_to_session(
                    session_id, audio_bytes
                )

            elif msg_type == "end_session" and session_id:
                await voice_manager.end_session(session_id)
                await websocket.send_text(json.dumps({
                    "type": "session_ended",
                    "session_id": session_id,
                }))
                break

    except WebSocketDisconnect:
        logger.info(f"Voice WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"Voice WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": str(e),
            }))
        except Exception:
            pass
    finally:
        if session_id:
            await voice_manager.end_session(session_id)
        if streaming_task:
            streaming_task.cancel()


async def _stream_responses(websocket: WebSocket, session_id: str):
    \"\"\"Stream agent responses back to the browser.\"\"\"
    try:
        async for event in voice_manager.start_streaming(session_id):
            # Parse ADK streaming events
            response = _parse_streaming_event(event)
            if response:
                await websocket.send_text(json.dumps(response, default=str))
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Streaming error for {session_id}: {e}")


def _parse_streaming_event(event) -> dict | None:
    \"\"\"Convert ADK streaming events to our WebSocket protocol.\"\"\"
    # ADK events have different structures based on type
    # This handles the common cases

    if hasattr(event, "content") and event.content:
        for part in event.content.parts:
            # Audio response from agent
            if hasattr(part, "inline_data") and part.inline_data:
                return {
                    "type": "audio",
                    "data": part.inline_data.data,  # Already base64
                    "mime_type": part.inline_data.mime_type,
                }
            # Text transcription
            if hasattr(part, "text") and part.text:
                return {
                    "type": "transcript",
                    "text": part.text,
                    "speaker": getattr(event, "author", "agent"),
                }

    # Tool call events
    if hasattr(event, "actions") and event.actions:
        # Check for function calls
        if hasattr(event.actions, "artifact_delta"):
            pass  # Handle artifacts if needed

    return None
"""

# ══════════════════════════════════════════════════════════════
# STEP 4: Update main.py to include voice WebSocket
# ══════════════════════════════════════════════════════════════

FILES["api/main_voice_patch.txt"] = """# PATCH FOR api/main.py — Add voice WebSocket support
#
# 1. Open api/main.py
# 2. Add this endpoint after the /ws/dashboard endpoint:
#
# @app.websocket("/ws/voice")
# async def voice_websocket(websocket: WebSocket):
#     from api.voice_websocket import handle_voice_websocket
#     await handle_voice_websocket(websocket)
#
# @app.get("/api/voice/sessions")
# async def get_voice_sessions():
#     from services.voice_session_manager import voice_manager
#     return {
#         "active_sessions": voice_manager.get_active_sessions(),
#         "total_active": voice_manager.active_count,
#     }
"""

# ══════════════════════════════════════════════════════════════
# STEP 5: CLI test — talk to agent from terminal
# ══════════════════════════════════════════════════════════════

FILES["test_voice_cli.py"] = """\"\"\"
CLI Voice Test — Talk to a Nexus911 agent from your terminal.

This uses PyAudio to capture your microphone and play back
the agent's voice response. Requires headphones to avoid echo.

Usage:
    python test_voice_cli.py

Requirements:
    pip install pyaudio google-genai
\"\"\"
import asyncio
import sys
from google import genai

# ── Configuration ────────────────────────────────────────────
# Load from .env or set directly
import os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY", "")
if not API_KEY:
    print("ERROR: Set GOOGLE_API_KEY in .env file")
    sys.exit(1)

MODEL = "gemini-2.5-flash-preview-native-audio-dialog"
SYSTEM_INSTRUCTION = \"\"\"You are a Nexus911 Emergency Agent handling a live 911 call.

Greet the caller with "911, what is your emergency?"

Then listen carefully and gather:
- Location of the emergency
- Nature of the emergency
- Number of people involved
- Whether weapons are present
- Whether anyone is injured
- Whether children are involved

Speak calmly, clearly, and with empathy. Use short sentences.
Repeat critical information back to confirm.
\"\"\"

# ── Audio Setup ──────────────────────────────────────────────
try:
    import pyaudio
except ImportError:
    print("PyAudio not installed. On Windows, try:")
    print("  pip install pipwin")
    print("  pipwin install pyaudio")
    print("Or download from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio")
    sys.exit(1)

FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

pya = pyaudio.PyAudio()
client = genai.Client(api_key=API_KEY)

audio_out_queue = asyncio.Queue()


async def listen_microphone():
    \"\"\"Capture audio from microphone.\"\"\"
    mic_info = pya.get_default_input_device_info()
    stream = await asyncio.to_thread(
        pya.open,
        format=FORMAT,
        channels=CHANNELS,
        rate=SEND_SAMPLE_RATE,
        input=True,
        input_device_index=mic_info["index"],
        frames_per_buffer=CHUNK_SIZE,
    )
    print("Microphone active — speak now")
    while True:
        data = await asyncio.to_thread(
            stream.read, CHUNK_SIZE, exception_on_overflow=False
        )
        yield data


async def play_audio():
    \"\"\"Play agent's audio responses through speakers.\"\"\"
    stream = await asyncio.to_thread(
        pya.open,
        format=FORMAT,
        channels=CHANNELS,
        rate=RECEIVE_SAMPLE_RATE,
        output=True,
    )
    while True:
        data = await audio_out_queue.get()
        await asyncio.to_thread(stream.write, data)


async def main():
    print("=" * 50)
    print("  Nexus911 Voice Test")
    print("  USE HEADPHONES to avoid echo")
    print("  Press Ctrl+C to exit")
    print("=" * 50)
    print()

    config = {
        "response_modalities": ["AUDIO"],
        "system_instruction": SYSTEM_INSTRUCTION,
    }

    async with client.aio.live.connect(model=MODEL, config=config) as session:
        print("Connected to Gemini Live API")
        print("Agent will greet you momentarily...")
        print()

        # Start audio playback task
        play_task = asyncio.create_task(play_audio())

        try:
            # Send microphone audio and receive responses concurrently
            async def send_audio():
                async for chunk in listen_microphone():
                    await session.send({"data": chunk, "mime_type": "audio/pcm"})

            async def receive_responses():
                while True:
                    async for response in session.receive():
                        if response.data:
                            await audio_out_queue.put(response.data)
                        if hasattr(response, "text") and response.text:
                            print(f"Agent: {response.text}")

            await asyncio.gather(send_audio(), receive_responses())

        except KeyboardInterrupt:
            print("\\nSession ended.")
        finally:
            play_task.cancel()
            pya.terminate()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\nGoodbye.")
"""

# ══════════════════════════════════════════════════════════════
# STEP 6: Update .env with streaming model
# ══════════════════════════════════════════════════════════════

FILES["streaming_test/.env"] = f"""GOOGLE_API_KEY={os.environ.get("GOOGLE_API_KEY", "PASTE_YOUR_KEY_HERE")}
GOOGLE_GENAI_USE_VERTEXAI=FALSE
"""


# ══════════════════════════════════════════════════════════════
# GENERATOR
# ══════════════════════════════════════════════════════════════

def create_voice_files():
    created = 0
    for filepath, content in FILES.items():
        full_path = os.path.join(PROJECT_ROOT, filepath)
        directory = os.path.dirname(full_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content.lstrip("\n"))
        created += 1
        print(f"  + {filepath}")

    print(f"\n{'='*60}")
    print(f"  Voice integration added! ({created} files)")
    print(f"{'='*60}")
    print()
    print("  QUICK TEST (do this first!):")
    print("  ────────────────────────────")
    print("  1. Install PyAudio:")
    print("       pip install pipwin")
    print("       pipwin install pyaudio")
    print("     OR: pip install PyAudio")
    print()
    print("  2. Copy your GOOGLE_API_KEY into streaming_test/.env")
    print()
    print("  3. Test with ADK's built-in voice UI:")
    print("       cd streaming_test")
    print("       adk web --no-reload")
    print("       Open http://localhost:8000")
    print("       Select 'nexus911_voice_test'")
    print("       Click microphone button")
    print("       Say: 'Help, there is a domestic violence situation'")
    print()
    print("  4. Test from terminal (needs headphones):")
    print("       cd ..")
    print("       python test_voice_cli.py")
    print()
    print("  FULL INTEGRATION:")
    print("  ────────────────────────────")
    print("  See api/main_voice_patch.py for instructions")
    print("  to add the /ws/voice endpoint to your main app.")
    print()


if __name__ == "__main__":
    create_voice_files()
