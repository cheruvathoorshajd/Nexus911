"""Predefined emergency scenarios for demo."""

SCENARIOS = {
    "domestic_violence_with_children": {
        "name": "Domestic Violence — Active Threat with Children",
        "incident_type": "domestic_violence",
        "severity": "CRITICAL",
        "location": "742 Evergreen Terrace, Springfield",
        "callers": [
            {
                "name": "Tommy (child, age 8)",
                "role": "VICTIM",
                "location": "Upstairs bedroom, hiding under bed",
                "opening": "Please help, my dad is really angry and my mom ran away. Me and my sister are hiding.",
                "emotional_state": "panicked",
            },
            {
                "name": "Sarah (mother)",
                "role": "VICTIM",
                "location": "Neighbor's garage at 744 Evergreen Terrace",
                "opening": "I just ran from my house, my husband was threatening me, my kids are still inside!",
                "emotional_state": "distressed",
            },
            {
                "name": "Robert (garage owner)",
                "role": "REPORTING_PARTY",
                "location": "744 Evergreen Terrace",
                "opening": "A woman just ran into my garage screaming. Should I call police?",
                "emotional_state": "confused",
            },
            {
                "name": "Mrs. Chen (neighbor)",
                "role": "WITNESS",
                "location": "739 Evergreen Terrace",
                "opening": "I can see a man pacing in front of 742. He's shouting.",
                "emotional_state": "concerned",
            },
        ],
    },
}


def get_scenario(name: str) -> dict:
    return SCENARIOS.get(name, {})


def list_scenarios() -> list:
    return list(SCENARIOS.keys())
