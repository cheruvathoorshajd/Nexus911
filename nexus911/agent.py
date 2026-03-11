from google.adk.agents import Agent

def report_emergency(location: str, description: str, severity: str = "HIGH") -> str:
    """Report a new emergency.

    Args:
        location: Where the emergency is happening
        description: What is happening
        severity: CRITICAL, HIGH, MEDIUM, or LOW

    Returns:
        Confirmation message
    """
    return f"Emergency logged at {location}. Severity: {severity}. Units dispatched."


def submit_intel(incident_id: str, intel: str) -> str:
    """Submit new intelligence about the incident.

    Args:
        incident_id: The incident ID
        intel: New information from the caller

    Returns:
        Confirmation message
    """
    return f"Intel recorded: {intel}. Shared with all responding agents."


def get_safety_instructions(situation: str) -> str:
    """Get safety instructions for the caller.

    Args:
        situation: Type of danger (active_shooter, domestic_violence, fire, medical)

    Returns:
        Safety instructions
    """
    instructions = {
        "domestic_violence": "If safe to leave, do so now. Go to a neighbor. Officers dispatched.",
        "active_shooter": "Run if possible. Hide if not. Lock doors. Silence phone. Stay low.",
        "fire": "Leave immediately. Stay low. Do not use elevators.",
        "medical": "Stay with the person. Do not move them. Paramedics on the way.",
    }
    return instructions.get(situation, "Stay calm. Help is on the way. Stay on the line.")

root_agent = Agent(
    name="nexus911",
    model="gemini-2.5-flash-native-audio-latest",
    description="Nexus911 emergency coordination agent",
    instruction="""You are a Nexus911 Emergency Agent handling a live 911 call.

When someone contacts you:
1. Say: "911, what is your emergency?"
2. Listen and gather: location, what happened, weapons, injuries, children involved
3. Use report_emergency to log the incident
4. Use get_safety_instructions to provide safety guidance
5. Use submit_intel for any new details the caller shares
6. Keep the caller calm. Speak clearly and with empathy.
7. Confirm help is on the way.

Never hang up. Every detail matters. Be efficient but compassionate.""",
    tools=[report_emergency, submit_intel, get_safety_instructions],
)