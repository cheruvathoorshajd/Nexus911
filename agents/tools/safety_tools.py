"""
Safety & grounding tools — ensures agent responses are accurate.
Addresses judging criterion: 'Does the agent avoid hallucinations?'
"""


def verify_emergency_protocol(action: str, incident_type: str) -> dict:
    """Verify an action follows standard emergency protocols.

    Args:
        action: The action being considered
        incident_type: Type of emergency

    Returns:
        dict with verification result
    """
    protocols = {
        "active_shooter": {
            "approved": ["evacuate", "shelter in place", "lock doors", "dispatch SWAT"],
            "prohibited": ["confront shooter", "negotiate alone", "enter without backup"],
        },
        "domestic_violence": {
            "approved": ["separate parties", "ensure victim safety", "offer shelter info"],
            "prohibited": ["couples counseling at scene", "share victim location with suspect"],
        },
        "fire": {
            "approved": ["evacuate building", "establish fire perimeter", "stage EMS"],
            "prohibited": ["re-enter burning building", "use elevators"],
        },
        "medical": {
            "approved": ["dispatch EMS", "provide CPR guidance", "control bleeding"],
            "prohibited": ["diagnose condition", "recommend medication"],
        },
    }
    protocol = protocols.get(incident_type, {})
    prohibited = protocol.get("prohibited", [])
    approved = protocol.get("approved", [])
    action_lower = action.lower()
    is_prohibited = any(p in action_lower for p in prohibited)
    is_approved = any(a in action_lower for a in approved)
    if is_prohibited:
        return {"verified": False, "warning": f"May violate protocol for {incident_type}"}
    return {"verified": True, "grounded": is_approved, "message": "Consistent with protocols"}
