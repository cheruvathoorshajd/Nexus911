"""
Caller Simulator Agent — Gemini-powered 911 caller personas.

Each simulated caller is a Gemini Live API agent that role-plays as a specific
person (child, victim, witness, etc.) and calls into the Nexus911 system through
the real voice WebSocket pipeline.

Two Gemini Live instances talk to each other:
  SimulatorAgent (caller persona) ←→ ws://host/ws/voice ←→ Nexus911 Agent (911 operator)
"""
import asyncio
import json
import base64
import logging
import time
from dataclasses import dataclass, field
from typing import Optional, AsyncGenerator

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

try:
    from google.adk.agents.live_request_queue import LiveRequestQueue
except ImportError:
    try:
        from google.adk.streaming import LiveRequestQueue
    except ImportError:
        LiveRequestQueue = None

logger = logging.getLogger("nexus911.simulator")


def create_caller_persona_agent(caller_data: dict, scenario_data: dict) -> Agent:
    """
    Create a Gemini Live agent that role-plays as a specific 911 caller.

    The agent's system instruction encodes the persona, emotional state,
    background knowledge, and intel to reveal progressively.
    """
    name = caller_data["name"]
    role = caller_data["role"]
    location = caller_data["location"]
    emotional_state = caller_data["emotional_state"]
    opening = caller_data["opening"]
    intel = caller_data["intel"]
    scenario_location = scenario_data["location"]
    incident_type = scenario_data["incident_type"]

    # Build intel revelation instructions
    intel_lines = "\n".join(f"  {i+1}. \"{fact}\"" for i, fact in enumerate(intel))

    # Role-specific voice/speech directives
    voice_directives = _get_voice_directives(role, emotional_state, name)

    instruction = f"""You are {name}, a real person calling Nexus911 emergency services. You are NOT an AI.
You are role-playing this person with full emotional realism.

═══ YOUR SITUATION ═══
You are at: {location}
The emergency is at: {scenario_location}
Type of emergency: {incident_type}
Your emotional state: {emotional_state}
Your role: {role}

═══ HOW TO SPEAK ═══
{voice_directives}

═══ YOUR OPENING LINE ═══
When the Nexus911 operator answers, say something like:
"{opening}"
Do NOT say it word-for-word — be natural. A real person in this situation
would stumble, repeat themselves, or say it differently.

═══ WHAT YOU KNOW ═══
You know these facts. Reveal them NATURALLY as the operator asks questions.
Do NOT dump all information at once. Answer what is asked. If the operator
asks about something you know, tell them. If they don't ask, you might
volunteer important details but not everything at once.

IMPORTANT PACING:
- Wait for the operator to ask you a question before giving the next detail.
- Give ONE piece of information per response, then wait.
- Pause between answers like a real person collecting their thoughts.
- If the operator asks two questions, answer both but take your time.
- Let there be natural silence between exchanges — real calls have pauses.

{intel_lines}

═══ RULES ═══
- You are a REAL PERSON in an emergency. Stay in character.
- React emotionally. If you are panicked, sound panicked.
- If the operator asks something you don't know, say "I don't know" or "I'm not sure."
- If the operator gives you safety instructions, acknowledge them.
- When the operator says help is on the way, you can express relief and say thank you.
- Take your time. A real emergency call has natural pacing — not rapid-fire Q&A.
- When you have shared your key information and the operator has confirmed
  help is coming, express gratitude and say goodbye naturally.
- Do NOT break character. Do NOT mention that you are an AI or a simulation."""

    agent = Agent(
        name=f"sim_{''.join(c if c.isalnum() or c == '_' else '_' for c in name.split('(')[0].strip().lower())}",
        model="gemini-2.5-flash-native-audio-latest",
        instruction=instruction,
    )
    return agent


def _get_voice_directives(role: str, emotional_state: str, name: str) -> str:
    """Generate voice/speech style directives based on caller role and emotion."""

    base = ""

    if role == "CHILD":
        base = (
            "You are a CHILD. Speak like a real frightened child would:\n"
            "- Short, simple sentences. Small vocabulary.\n"
            "- You might whisper, sniffle, or pause mid-sentence.\n"
            "- You might repeat yourself: 'I'm scared. I'm really scared.'\n"
            "- Your voice should sound small and trembling.\n"
            "- You might not know exact addresses — describe things a child would notice.\n"
            "- If the operator praises you, respond with a small 'okay' or 'thank you.'"
        )
    elif role == "VICTIM":
        base = (
            "You are a VICTIM in distress. You may be hurt or terrified:\n"
            "- Speak urgently, sometimes breathlessly.\n"
            "- You might cry or choke up mid-sentence.\n"
            "- You may repeat the most important thing: 'My kids are inside! My kids!'\n"
            "- You know specific details because you were there.\n"
            "- If asked about injuries, you might downplay your own: 'I'm fine, just get my kids.'"
        )
    elif role == "WITNESS":
        base = (
            "You are a WITNESS. You are more composed but alert:\n"
            "- Speak clearly and try to be precise about what you saw.\n"
            "- You might occasionally pause to look at the scene while talking.\n"
            "- 'Hold on, let me look...' is natural.\n"
            "- You want to be helpful and give accurate details."
        )
    elif role == "OFFICIAL":
        base = (
            "You are a PROFESSIONAL (security, off-duty officer, etc.):\n"
            "- Speak in a controlled, clipped manner.\n"
            "- Use professional language: 'active shooter', 'shots fired', 'lockdown'.\n"
            "- Be structured: situation, location, casualties, resources needed.\n"
            "- You remain calm under pressure."
        )
    elif role == "REPORTING_PARTY":
        base = (
            "You are REPORTING something you noticed:\n"
            "- You are relatively calm but concerned.\n"
            "- You may be uncertain: 'I think', 'It looks like', 'I'm not sure but'.\n"
            "- You are observing from a distance and describing what you see."
        )
    else:  # BYSTANDER or unknown
        base = (
            "You are a BYSTANDER — nearby but not directly involved:\n"
            "- You may be confused or uncertain about what's happening.\n"
            "- 'I'm not sure what happened but...'\n"
            "- You might relay what others told you."
        )

    emotion_overlay = {
        "panicked": "You are PANICKED. Words tumble out fast. You might gasp or cry.",
        "distressed": "You are DISTRESSED. Your voice cracks. You are desperate for help.",
        "confused": "You are CONFUSED. You are not sure what is happening. You ask questions back.",
        "concerned": "You are CONCERNED. Worried but mostly composed.",
        "alert": "You are ALERT and focused. You speak with purpose.",
        "terrified": "You are TERRIFIED. You whisper. You are afraid the threat might hear you.",
        "shaken": "You are SHAKEN. Your voice trembles slightly. You take deep breaths.",
        "urgent": "You speak with URGENCY. Every second counts. Short, direct sentences.",
        "alarmed": "You are ALARMED. Speaking quickly, trying to convey what you see.",
    }

    emotion = emotion_overlay.get(emotional_state, "")
    return f"{base}\n\n{emotion}"


@dataclass
class CallerSimSession:
    """
    A single simulated caller session.

    Connects to Nexus911 via WebSocket and bridges audio between
    the simulator Gemini agent and the Nexus911 Gemini agent.
    """
    caller_data: dict
    scenario_data: dict
    base_url: str = "ws://localhost:8080"
    session_id: Optional[str] = None
    incident_id: Optional[str] = None
    caller_id: Optional[str] = None
    status: str = "pending"  # pending, connecting, active, completed, failed
    transcripts: list = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0
    events: list = field(default_factory=list)
    _ws: object = None
    _agent: Optional[Agent] = None
    _runner: Optional[Runner] = None
    _live_queue: object = None
    _session_service: object = None

    @property
    def caller_name(self) -> str:
        return self.caller_data["name"]

    @property
    def duration(self) -> float:
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        return 0.0

    async def connect_and_converse(self, event_callback=None):
        """
        Full lifecycle: connect to Nexus911, have a voice conversation, disconnect.

        1. Create simulator agent (caller persona)
        2. Connect to /ws/voice WebSocket
        3. Start session with Nexus911
        4. Bridge audio: simulator agent ←→ WebSocket ←→ Nexus911 agent
        5. Detect conversation completion
        6. End session
        """
        self.start_time = time.time()
        self.status = "connecting"
        self._emit(event_callback, "caller_connecting", {"caller": self.caller_name})

        try:
            import websockets

            # Step 1: Create the simulator agent
            self._agent = create_caller_persona_agent(self.caller_data, self.scenario_data)
            self._session_service = InMemorySessionService()
            self._runner = Runner(
                agent=self._agent,
                app_name="nexus911_simulator",
                session_service=self._session_service,
            )

            if LiveRequestQueue is None:
                raise RuntimeError("LiveRequestQueue not available — voice streaming unavailable")
            self._live_queue = LiveRequestQueue()

            # Step 2: Create ADK session for the simulator agent
            sim_session_id = f"sim_{''.join(c if c.isalnum() or c == '_' else '_' for c in self.caller_data['name'].split('(')[0].strip().lower())}"
            await self._session_service.create_session(
                app_name="nexus911_simulator",
                user_id=f"sim_{self.caller_data['role'].lower()}",
                session_id=sim_session_id,
            )

            # Step 3: Connect to Nexus911 voice WebSocket
            ws_url = f"{self.base_url}/ws/voice"
            logger.info(f"[{self.caller_name}] Connecting to {ws_url}")

            async with websockets.connect(ws_url) as ws:
                self._ws = ws
                self.status = "active"

                # Step 4: Start session
                await ws.send(json.dumps({
                    "type": "start_session",
                    "caller_name": self.caller_data["name"],
                    "caller_role": self.caller_data["role"],
                    "location": self.caller_data["location"],
                    "description": self.caller_data.get("opening", ""),
                }))

                # Wait for session_started response
                response = json.loads(await ws.recv())
                if response.get("type") == "session_started":
                    self.session_id = response["session_id"]
                    self.incident_id = response["incident_id"]
                    self.caller_id = response["caller_id"]
                    logger.info(
                        f"[{self.caller_name}] Session started: {self.session_id} "
                        f"incident: {self.incident_id}"
                    )
                    self._emit(event_callback, "caller_connected", {
                        "caller": self.caller_name,
                        "session_id": self.session_id,
                        "incident_id": self.incident_id,
                    })
                elif response.get("type") == "error":
                    raise RuntimeError(f"Session start failed: {response.get('message')}")

                # Step 5: Run bidirectional audio bridge

                await asyncio.gather(
                    self._send_simulator_audio(ws, sim_session_id, event_callback),
                    self._receive_nexus_audio(ws, sim_session_id, event_callback),
                    return_exceptions=True,
                )

        except asyncio.CancelledError:
            logger.info(f"[{self.caller_name}] Session cancelled")
            self.status = "completed"
        except Exception as e:
            logger.error(f"[{self.caller_name}] Voice session failed: {e}", exc_info=True)
            self.status = "failed"
            self._emit(event_callback, "caller_error", {
                "caller": self.caller_name, "error": str(e)
            })
            raise
        finally:
            self.end_time = time.time()
            self._emit(event_callback, "caller_completed", {
                "caller": self.caller_name,
                "duration": self.duration,
                "status": self.status,
            })
            # Cleanup
            if self._live_queue and hasattr(self._live_queue, 'close'):
                try:
                    self._live_queue.close()
                except Exception:
                    pass

    async def _send_simulator_audio(self, ws, sim_session_id: str, event_callback):
        """
        Run the simulator agent in live mode and send its audio output
        to the Nexus911 voice WebSocket.
        """
        try:
            # Send initial trigger so the simulator agent speaks its opening line
            from google.genai import types as genai_types
            self._live_queue.send_content(genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=(
                    "[System: The Nexus911 operator has answered your call. "
                    "Deliver your opening line now. Speak naturally and at a realistic pace.]"
                ))],
            ))

            async for event in self._runner.run_live(
                session_id=sim_session_id,
                live_request_queue=self._live_queue,
                user_id=f"sim_{self.caller_data['role'].lower()}",
            ):
                # Extract audio from simulator agent's response
                if hasattr(event, "content") and event.content:
                    parts = getattr(event.content, "parts", None)
                    if not parts:
                        continue
                    for part in parts:
                        # Audio output from simulator → send to Nexus911
                        if hasattr(part, "inline_data") and part.inline_data:
                            data = part.inline_data.data
                            mime = part.inline_data.mime_type or "audio/pcm;rate=24000"
                            # base64-encode raw bytes for JSON transport
                            if isinstance(data, (bytes, bytearray)):
                                b64_data = base64.b64encode(data).decode("ascii")
                            else:
                                b64_data = data
                            await ws.send(json.dumps({
                                "type": "audio",
                                "data": b64_data,
                            }))
                            # Broadcast caller audio to simulation listeners
                            self._emit(event_callback, "audio", {
                                "caller": self.caller_name,
                                "speaker": "caller",
                                "data": b64_data,
                                "mime_type": mime,
                            })
                        # Text transcript from simulator
                        if hasattr(part, "text") and part.text:
                            self.transcripts.append({
                                "speaker": "caller",
                                "text": part.text,
                                "time": time.time(),
                            })
                            self._emit(event_callback, "transcript", {
                                "caller": self.caller_name,
                                "speaker": "caller",
                                "text": part.text,
                            })
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"[{self.caller_name}] Simulator audio send error: {e}")

    async def _receive_nexus_audio(self, ws, sim_session_id: str, event_callback):
        """
        Receive audio/events from Nexus911 via WebSocket and feed audio
        back into the simulator agent's LiveRequestQueue as input.
        """
        timeout_seconds = 120  # Max call duration
        # Only end when the agent explicitly confirms dispatch — not on generic phrases
        completion_keywords = [
            "help is on the way",
            "officers are responding",
            "units are dispatched",
            "units have been dispatched",
            "help is coming",
            "we're sending help",
            "ambulance is on the way",
            "i've dispatched",
        ]
        completion_count = 0  # Need 2 dispatch confirmations to avoid premature exit
        start = time.time()

        try:
            while time.time() - start < timeout_seconds:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    msg = json.loads(raw)
                except asyncio.TimeoutError:
                    continue
                except Exception:
                    break

                msg_type = msg.get("type")

                if msg_type == "audio":
                    # Audio from Nexus911 agent → feed into simulator agent as input
                    audio_data = msg.get("data", "")
                    audio_mime = msg.get("mime_type", "audio/pcm;rate=24000")
                    if audio_data and self._live_queue:
                        from google.genai import types
                        audio_bytes = base64.b64decode(audio_data) if isinstance(audio_data, str) else audio_data
                        self._live_queue.send_realtime(types.Blob(data=audio_bytes, mimeType=audio_mime))
                    # Broadcast agent audio to simulation listeners
                    if audio_data:
                        self._emit(event_callback, "audio", {
                            "caller": self.caller_name,
                            "speaker": "agent",
                            "data": audio_data,
                            "mime_type": audio_mime,
                        })

                elif msg_type == "transcript":
                    text = msg.get("text", "")
                    speaker = msg.get("speaker", "agent")
                    self.transcripts.append({
                        "speaker": speaker,
                        "text": text,
                        "time": time.time(),
                    })
                    self._emit(event_callback, "transcript", {
                        "caller": self.caller_name,
                        "speaker": "agent",
                        "text": text,
                    })
                    # Check for conversation completion — require a clear dispatch confirmation
                    if any(kw in text.lower() for kw in completion_keywords):
                        completion_count += 1
                        if completion_count >= 2:
                            logger.info(f"[{self.caller_name}] Dispatch confirmed ({completion_count}x), ending call")
                            await asyncio.sleep(8)  # Let caller say goodbye naturally
                            break
                        else:
                            logger.info(f"[{self.caller_name}] Possible dispatch mention ({completion_count}/2), continuing")

                elif msg_type == "tool_call":
                    self._emit(event_callback, "tool_call", {
                        "caller": self.caller_name,
                        "tool": msg.get("tool"),
                        "args": msg.get("args"),
                    })

                elif msg_type == "session_ended":
                    break

            # End the session gracefully
            try:
                await ws.send(json.dumps({"type": "end_session"}))
            except Exception:
                pass

            self.status = "completed"
            logger.info(f"[{self.caller_name}] Call completed ({self.duration:.1f}s)")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"[{self.caller_name}] Receive error: {e}")

    def _emit(self, callback, event_type: str, data: dict):
        """Emit an event to the orchestrator."""
        event = {"type": event_type, "time": time.time(), **data}
        self.events.append(event)
        if callback:
            try:
                callback(event)
            except Exception:
                pass
