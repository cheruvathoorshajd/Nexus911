"""
Caller Agent — Handles individual 911 callers via voice.
Each caller gets a role-specific agent instance.
"""
from google.adk.agents import Agent
from agents.tools.incident_tools import (
    submit_intelligence,
    update_suspect_info,
    get_incident_briefing,
)
from agents.tools.caller_tools import (
    provide_safety_instructions,
    transfer_to_human_dispatcher,
)


ROLE_INSTRUCTIONS = {
    "VICTIM": (
        "You are speaking with a VICTIM. Priority is their immediate safety. "
        "Speak calmly and slowly. Ask: Are you safe? Are you injured? "
        "Can you describe what happened? Guide them to safety if possible."
    ),
    "WITNESS": (
        "You are speaking with a WITNESS. They may have critical information. "
        "Ask: What did you see? Can you describe the suspect? What direction "
        "did they go? Are you in a safe location?"
    ),
    "BYSTANDER": (
        "You are speaking with a BYSTANDER who may be confused or frightened. "
        "Reassure them help is on the way. Ask if they can see anything useful."
    ),
    "REPORTING_PARTY": (
        "You are speaking with someone REPORTING an emergency involving others. "
        "Gather location details, number of people involved, and nature of emergency."
    ),
}


def create_caller_agent(caller_role: str, incident_id: str) -> Agent:
    role_inst = ROLE_INSTRUCTIONS.get(caller_role, ROLE_INSTRUCTIONS["REPORTING_PARTY"])

    instruction = f"""You are a Nexus911 Emergency Agent handling a live 911 call.

INCIDENT ID: {incident_id}
CALLER ROLE: {caller_role}

{role_inst}

RULES:
- Speak clearly, calmly, and with empathy
- Extract and submit ALL intelligence using submit_intelligence
- If caller mentions weapons, immediately use update_suspect_info
- Periodically check get_incident_briefing for updates from other callers
- If a child is involved, adjust language to be age-appropriate
- If caller is in immediate danger, provide safety_instructions first
- NEVER hang up on a caller
- If you cannot help further, use transfer_to_human_dispatcher

You are one of multiple agents handling this incident simultaneously.
Other agents are talking to other callers and gathering different intel.
"""

    return Agent(
        model="gemini-2.5-flash",
        name=f"caller_agent_{caller_role.lower()}",
        instruction=instruction,
        tools=[
            submit_intelligence,
            update_suspect_info,
            get_incident_briefing,
            provide_safety_instructions,
            transfer_to_human_dispatcher,
        ],
    )
