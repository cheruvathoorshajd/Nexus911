"""
CLI Voice Test — Talk to a Nexus911 agent from your terminal.

This uses PyAudio to capture your microphone and play back
the agent's voice response. Requires headphones to avoid echo.

Usage:
    python test_voice_cli.py

Requirements:
    pip install pyaudio google-genai
"""
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
SYSTEM_INSTRUCTION = """You are a Nexus911 Emergency Agent handling a live 911 call.

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
"""

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
    """Capture audio from microphone."""
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
    """Play agent's audio responses through speakers."""
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
            print("\nSession ended.")
        finally:
            play_task.cancel()
            pya.terminate()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye.")
