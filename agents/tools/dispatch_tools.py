"""Tools for dispatch operations."""


def recommend_response_units(
    incident_type: str, severity: str, armed_suspect: bool = False,
    children_involved: bool = False, victims_count: int = 0,
) -> dict:
    """Recommend appropriate emergency response units.

    Args:
        incident_type: Type of emergency
        severity: CRITICAL, HIGH, MEDIUM, LOW
        armed_suspect: Whether suspect is armed
        children_involved: Whether children are at risk
        victims_count: Number of known victims

    Returns:
        dict with recommended units and priority
    """
    units = []
    priority = "routine"
    if severity in ("CRITICAL", "HIGH"):
        priority = "emergency"
    if incident_type == "active_shooter":
        units.extend(["Patrol Unit x2", "SWAT Team", "EMS Standby"])
        priority = "emergency"
    elif incident_type == "domestic_violence":
        units.extend(["Patrol Unit x2"])
        if armed_suspect:
            units.append("Armed Response Unit")
    elif incident_type == "fire":
        units.extend(["Fire Engine", "Ladder Truck"])
    elif incident_type == "medical":
        units.extend(["EMS Ambulance"])
    if armed_suspect and "Armed Response Unit" not in units:
        units.append("Armed Response Unit")
    if children_involved:
        units.append("Child Services Alert")
    if victims_count > 3:
        units.append("Mass Casualty Protocol")
    if not any("Patrol" in u for u in units):
        units.append("Patrol Unit")
    return {"recommended_units": units, "priority": priority}
