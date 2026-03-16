"""Tools for caller-facing agents."""


def provide_safety_instructions(situation_type: str, caller_is_child: bool = False) -> dict:
    """Provide immediate safety instructions to the caller.

    Args:
        situation_type: Type of danger (active_shooter, fire, domestic_violence, medical)
        caller_is_child: Whether the caller is a child

    Returns:
        dict with safety instructions
    """
    instructions = {
        "active_shooter": {
            "adult": [
                "If you can safely leave, do so immediately.",
                "If you cannot leave, find a room you can lock or barricade.",
                "Turn off lights, silence your phone, stay below window level.",
                "Do NOT open the door until police announce themselves.",
            ],
            "child": [
                "I need you to be very brave for me, okay?",
                "Can you hide somewhere safe? Under a bed or in a closet?",
                "Be very, very quiet like you're playing the quiet game.",
                "Don't come out until a police officer comes to get you.",
                "You're doing so great. Help is coming right now.",
            ],
        },
        "domestic_violence": {
            "adult": [
                "If you can safely leave the house, please do so now.",
                "Go to a neighbor's house or any public place.",
                "If you cannot leave, get to a room with a lock.",
                "Officers are on their way.",
            ],
            "child": [
                "You're safe talking to me. Can you go to a room and close the door?",
                "Help is coming. You did the right thing by calling.",
            ],
        },
        "fire": {
            "adult": [
                "Leave the building immediately. Do not use elevators.",
                "Stay low to avoid smoke. Feel doors before opening.",
                "Once outside, move away. Do NOT go back inside.",
            ],
            "child": [
                "Leave the house right now if you can.",
                "Stay low and crawl. Go outside and find a grown-up.",
            ],
        },
        "medical": {
            "adult": [
                "Stay with the person and keep them calm.",
                "Don't move them unless they're in immediate danger.",
                "Paramedics are being dispatched now.",
            ],
            "child": [
                "You're being so brave. Stay with them. Help is coming.",
                "Can you unlock the front door so helpers can get in?",
            ],
        },
    }
    key = "child" if caller_is_child else "adult"
    result = instructions.get(situation_type, instructions["medical"]).get(key, [])
    return {"status": "success", "instructions": result}


def transfer_to_human_dispatcher(incident_id: str, reason: str) -> dict:
    """Transfer caller to a human dispatcher.

    Args:
        incident_id: The incident ID
        reason: Why the transfer is needed

    Returns:
        dict confirming transfer request
    """
    return {"status": "transfer_requested", "reason": reason, "incident_id": incident_id}
