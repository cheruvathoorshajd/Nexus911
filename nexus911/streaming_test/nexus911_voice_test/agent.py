"""
Quick test: A single Nexus911 caller agent with voice.
Run with: cd streaming_test && adk web --no-reload
Then open http://localhost:8000, select nexus911_voice_test,
click the microphone button, and start talking.

Say something like: "Help, there's a man threatening my neighbor,
I'm at 742 Evergreen Terrace"
"""
from google.adk.agents import Agent


def report_emergency(location: str, description: str, severity: str = "HIGH") -> dict:
    """Report a new emergency. Called when caller describes their situation.

    Args:
        location: Where the emergency is happening
        description: What is happening
        severity: CRITICAL, HIGH, MEDIUM, or LOW

    Returns:
        dict confirming the emergency was logged
    """
    return {
        "status": "emergency_logged",
        "incident_id": "inc_test_001",
        "message": f"Emergency logged at {location}. Units being dispatched. Severity: {severity}",
    }


def submit_intel(incident_id: str, intel: str) -> dict:
    """Submit new intelligence about the incident.

    Args:
        incident_id: The incident ID
        intel: New information from the caller

    Returns:
        dict confirming intel was recorded
    """
    return {
        "status": "intel_recorded",
        "message": f"Intelligence recorded: {intel}. This has been shared with all responding units.",
    }


def get_safety_instructions(situation: str) -> dict:
    """Get safety instructions for the caller based on their situation.

    Args:
        situation: Type of danger (active_shooter, domestic_violence, fire, medical)

    Returns:
        dict with safety instructions
    """
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
    instruction="""You are a Nexus911 Emergency Agent handling a live 911 call.

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
""",
    tools=[
        report_emergency,
        submit_intel,
        get_safety_instructions,
    ],
)
