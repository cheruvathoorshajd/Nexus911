"""
Dispatcher Agent — Faces the human dispatcher.
Presents unified situational view and recommends actions.
"""
from google.adk.agents import Agent
from agents.tools.incident_tools import get_incident_briefing, dispatch_units
from agents.tools.dispatch_tools import recommend_response_units
from agents.tools.safety_tools import verify_emergency_protocol

root_agent = Agent(
    model="gemini-2.5-flash-native-audio-latest",
    name="dispatcher_agent",
    instruction="""You are Nexus911 Dispatcher Assistant. You help human dispatchers
    by providing a unified view of active incidents and recommending actions.

    You have access to real-time intelligence from multiple AI agents each
    handling different callers in the same incident. Present this information
    clearly and recommend appropriate response units.

    Always verify recommendations against emergency protocols before suggesting them.
    """,
    tools=[
        get_incident_briefing,
        dispatch_units,
        recommend_response_units,
        verify_emergency_protocol,
    ],
)
