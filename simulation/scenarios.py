"""
Predefined emergency scenarios for demo and simulation.

Each scenario includes cross-caller contradictions to demonstrate
VerifyLayer's contradiction detection and confidence scoring.
"""

SCENARIOS = {
    "domestic_violence_with_children": {
        "name": "Domestic Violence — Active Threat with Children",
        "incident_type": "domestic_violence",
        "severity": "CRITICAL",
        "location": "742 Evergreen Terrace, Springfield",
        "latitude": 39.7817,
        "longitude": -89.6501,
        "callers": [
            {
                "name": "Tommy (child, age 8)",
                "role": "CHILD",
                "location": "Upstairs bedroom, hiding under bed",
                "opening": "Please help, my dad is really angry and my mom ran away. Me and my sister are hiding.",
                "emotional_state": "panicked",
                "intel": [
                    "My dad is really angry and yelling",
                    "My mom ran away, she went outside",
                    "Me and my sister are hiding under the bed upstairs",
                    # CONTRADICTION: child says "something in his hand" — vague
                    "I think dad has something in his hand but I can't see what it is",
                    "My sister Lisa is 5 and she is crying",
                ],
                "delay": 0.0,
            },
            {
                "name": "Sarah (mother)",
                "role": "VICTIM",
                "location": "Neighbor's garage at 744 Evergreen Terrace",
                "opening": "I just ran from my house, my husband was threatening me, my kids are still inside!",
                "emotional_state": "distressed",
                "intel": [
                    "My husband was threatening me with a kitchen knife",
                    "My two children are still inside at 742 Evergreen Terrace",
                    "I ran to the neighbor's garage at 744 Evergreen Terrace",
                    "He's been drinking all day, this has happened before",
                    "The children are Tommy age 8 and Lisa age 5",
                    # CONTRADICTION: mother says kitchen knife
                    "He grabbed the knife from the kitchen drawer",
                ],
                "delay": 2.0,
            },
            {
                "name": "Robert (garage owner)",
                "role": "REPORTING_PARTY",
                "location": "744 Evergreen Terrace",
                "opening": "A woman just ran into my garage screaming for help. There's a man next door who looks dangerous.",
                "emotional_state": "confused",
                "intel": [
                    "A woman just ran into my garage, she's very upset and shaking",
                    "She says her husband threatened her next door at 742",
                    "I can see a man pacing on the porch at 742 from here",
                    # CONTRADICTION: Robert says baseball bat — contradicts mother's "kitchen knife"
                    "He's holding what looks like a baseball bat, swinging it around",
                    "The woman has a bruise on her arm",
                ],
                "delay": 4.0,
            },
            {
                "name": "Mrs. Chen (neighbor across street)",
                "role": "WITNESS",
                "location": "739 Evergreen Terrace",
                "opening": "I can hear shouting from 742 Evergreen. A man is on the porch screaming.",
                "emotional_state": "concerned",
                "intel": [
                    "There is a man pacing in front of 742 Evergreen Terrace",
                    "He is shouting and looks very angry",
                    "I heard a woman screaming earlier, she ran to the neighbor's house",
                    "I've seen police here before, maybe 3 months ago for a similar situation",
                    # CONTRADICTION: Mrs. Chen says she doesn't see any weapon — contradicts both
                    "I don't see him holding anything from where I am, but he's very agitated",
                ],
                "delay": 5.0,
            },
        ],
    },
    "highway_accident": {
        "name": "Highway Multi-Vehicle Accident",
        "incident_type": "vehicle_accident",
        "severity": "CRITICAL",
        "location": "Route 9 and Elm Street",
        "latitude": 40.7580,
        "longitude": -73.9855,
        "callers": [
            {
                "name": "Tommy (child, age 8)",
                "role": "CHILD",
                "location": "Backseat of blue Camry",
                "opening": "We crashed and mommy isn't moving. There's a big truck.",
                "emotional_state": "panicked",
                "intel": [
                    "We crashed and mommy isn't moving",
                    "There's a big truck next to us",
                    "My sister is crying but she's okay",
                    "The car is making funny noises and there's smoke",
                    # Child says location differently — tests dedup
                    "We were going to grandma's house near the big bridge",
                ],
                "delay": 0.0,
            },
            {
                "name": "David Chen (witness)",
                "role": "WITNESS",
                "location": "Sidewalk across from Route 9 and Elm",
                "opening": "I just saw a bad accident. A sedan hit an 18-wheeler at Route 9 and Elm Street.",
                "emotional_state": "alert",
                "intel": [
                    "A sedan just hit an 18-wheeler at Route 9 and Elm",
                    "The sedan is a blue Camry, badly damaged on driver side",
                    "I can see two people in the sedan, driver appears unconscious",
                    "The truck driver is out of his cab, he looks okay",
                    "Traffic is backing up in both directions",
                    # CONTRADICTION: witness says truck ran the red light
                    "I saw it happen — the truck ran the red light and hit the car",
                ],
                "delay": 3.0,
            },
            {
                "name": "Maria Santos (truck driver)",
                "role": "VICTIM",
                "location": "Cab of 18-wheeler at Route 9 and Elm",
                "opening": "I was in my truck and a car came through the intersection and hit me. I need to report this.",
                "emotional_state": "shaken",
                "intel": [
                    "I was driving my 18-wheeler going north on Route 9",
                    "A blue car ran the red light and hit my truck on the passenger side",
                    "I'm okay but shaken up, my truck has minor damage",
                    "The car driver is not responding, I tried to check on them",
                    "There are kids in the backseat of the car, they're crying",
                    # CONTRADICTION: truck driver says car ran the red light — contradicts witness
                    "I had a green light, I am sure of it. The car ran the red.",
                ],
                "delay": 6.0,
            },
        ],
    },
    "active_shooter": {
        "name": "Active Shooter — Shopping Mall",
        "incident_type": "active_shooter",
        "severity": "CRITICAL",
        "location": "Riverside Mall, 500 Commerce Drive",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "callers": [
            {
                "name": "Jennifer Park (store employee)",
                "role": "VICTIM",
                "location": "Storage room, Macy's second floor",
                "opening": "Someone is shooting in the mall! I'm hiding in the back of Macy's!",
                "emotional_state": "terrified",
                "intel": [
                    "I heard gunshots on the first floor near the food court",
                    "I ran to the storage room on the second floor of Macy's",
                    "There are 4 other people hiding with me in here",
                    "I think I heard at least 6 or 7 shots",
                    # CONTRADICTION: says one shooter
                    "I saw one person with a gun, wearing all black, tall",
                ],
                "delay": 0.0,
            },
            {
                "name": "Marcus Williams (security guard)",
                "role": "OFFICIAL",
                "location": "Security office, Riverside Mall ground floor",
                "opening": "This is mall security at Riverside. We have an active shooter situation. Multiple shots fired.",
                "emotional_state": "urgent",
                "intel": [
                    "Active shooter in Riverside Mall, 500 Commerce Drive",
                    "Shots fired near the food court on ground floor, approximately 2 minutes ago",
                    "We are in lockdown, I've sealed the security office",
                    "On camera I can see the food court is cleared, people ran",
                    # CONTRADICTION: security sees TWO shooters on camera — contradicts Jennifer
                    "I see two individuals on camera near JCPenney, both appear armed",
                    "Estimate 200-300 people still in the mall",
                    "North entrance and south entrance are the main access points",
                ],
                "delay": 1.0,
            },
            {
                "name": "Carlos Mendez (bystander in parking lot)",
                "role": "BYSTANDER",
                "location": "Parking lot, west side of Riverside Mall",
                "opening": "People are running out of the mall screaming. I think there was a shooting.",
                "emotional_state": "alarmed",
                "intel": [
                    "People are pouring out of the mall through the west exit",
                    "I can hear screaming from inside",
                    "Someone said there's a shooter but I didn't see anything",
                    "There's a woman on the ground near the exit, she may be hurt",
                    # CONTRADICTION: says he heard it was near the movie theater, not food court
                    "A man running out told me the shooting was near the movie theater",
                ],
                "delay": 3.0,
            },
        ],
    },
}


def get_scenario(name: str) -> dict:
    """Get a scenario by name."""
    return SCENARIOS.get(name, {})


def list_scenarios() -> list:
    """List all available scenario names with descriptions."""
    return [
        {"name": name, "title": s["name"], "caller_count": len(s["callers"]),
         "severity": s["severity"], "incident_type": s["incident_type"]}
        for name, s in SCENARIOS.items()
    ]
