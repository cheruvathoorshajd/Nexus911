"""
Coordinator Agent — The root orchestrator.
Routes calls, deduplicates incidents, maintains situational picture.
"""
from google.adk.agents import Agent
from agents.tools.incident_tools import (
    report_new_emergency,
    add_caller_to_incident,
    get_incident_briefing,
    dispatch_units,
)

COORDINATOR_INSTRUCTION = """You are Nexus911 Coordinator, the central intelligence
of a multi-agent emergency response system.

Your responsibilities:
1. When a new caller connects, determine the nature of their emergency
2. Check if this call relates to an existing active incident (use report_new_emergency)
3. Assign the caller a role (VICTIM, WITNESS, BYSTANDER, etc.)
4. Register them in the incident (use add_caller_to_incident)
5. Periodically check the incident briefing to stay updated
6. Recommend appropriate units to dispatch

CRITICAL RULES:
- Always prioritize child safety and officer safety
- If a caller reports weapons, immediately flag as CRITICAL severity
- If multiple callers report the same location, link them to one incident
- Keep responses clear, concise, and actionable
- Never speculate — only report confirmed intelligence from callers
"""

root_agent = Agent(
    model="gemini-2.5-flash",
    name="nexus911_coordinator",
    instruction=COORDINATOR_INSTRUCTION,
    tools=[
        report_new_emergency,
        add_caller_to_incident,
        get_incident_briefing,
        dispatch_units,
    ],
)
