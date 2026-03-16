# Voice WebSocket for 911 caller agents.
# Browser connects here, streams mic audio, receives agent voice responses.
import json
import base64
import logging
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from services.voice_session_manager import voice_manager

logger = logging.getLogger("nexus911.voice_ws")


async def handle_voice_websocket(websocket: WebSocket):
    """Handle a single voice WebSocket connection from the browser."""
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
    """Stream agent responses back to the browser."""
    try:
        logger.info(f"Starting streaming responses for {session_id}")
        async for event in voice_manager.start_streaming(session_id):
            # Parse ADK streaming events
            response = _parse_streaming_event(event)
            if response:
                await websocket.send_text(json.dumps(response, default=str))

                # If we got a transcript, fire background verification
                if response.get("type") == "transcript":
                    session = voice_manager.sessions.get(session_id)
                    if session:
                        try:
                            from verification.hooks import verify_transcript_chunk
                            asyncio.create_task(verify_transcript_chunk(
                                incident_id=session.incident_id,
                                caller_id=session.caller_id,
                                caller_role=session.caller_role,
                                agent_id=session.agent.name,
                                transcript_text=response["text"],
                            ))
                        except Exception:
                            pass  # Non-blocking — fail-open
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Streaming error for {session_id}: {e}", exc_info=True)


def _parse_streaming_event(event) -> dict | None:
    """Convert ADK streaming events to our WebSocket protocol."""
    # ADK events have different structures based on type
    # This handles the common cases

    if hasattr(event, "content") and event.content:
        parts = getattr(event.content, "parts", None)
        if not parts:
            return None
        for part in parts:
            # Audio response from agent
            if hasattr(part, "inline_data") and part.inline_data:
                data = part.inline_data.data
                # inline_data.data is raw bytes — must base64-encode for JSON/WebSocket
                if isinstance(data, (bytes, bytearray)):
                    data = base64.b64encode(data).decode("ascii")
                return {
                    "type": "audio",
                    "data": data,
                    "mime_type": part.inline_data.mime_type or "audio/pcm;rate=24000",
                }
            # Text transcription
            if hasattr(part, "text") and part.text:
                return {
                    "type": "transcript",
                    "text": part.text,
                    "speaker": getattr(event, "author", "agent"),
                }

    # Tool call events — surface to dashboard
    if hasattr(event, "actions") and event.actions:
        if hasattr(event.actions, "function_calls"):
            calls = event.actions.function_calls
            if calls:
                return {
                    "type": "tool_call",
                    "tool": calls[0].name if calls else "unknown",
                    "args": dict(calls[0].args) if calls else {},
                }

    return None
