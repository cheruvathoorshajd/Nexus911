"""
Tool functions for incident management. All agents use these.
"""
from core.incident_graph import (
    incident_manager,
    CallerInfo,
    CallerRole,
    IncidentSeverity,
)
from core.deduplication import DeduplicationEngine

dedup_engine = DeduplicationEngine(incident_manager)


def report_new_emergency(
    location: str,
    description: str,
    incident_type: str = "unknown",
    severity: str = "MEDIUM",
    latitude: float = 0.0,
    longitude: float = 0.0,
) -> dict:
    """Report a new emergency or link to an existing incident.

    Args:
        location: Address or location description
        description: Brief description of what is happening
        incident_type: Type of emergency
        severity: CRITICAL, HIGH, MEDIUM, or LOW
        latitude: GPS latitude if available
        longitude: GPS longitude if available

    Returns:
        dict with incident_id and status
    """
    coords = (latitude, longitude) if latitude and longitude else None
    existing = dedup_engine.find_matching_incident(
        location=location, location_coords=coords, description=description,
    )
    if existing:
        return {
            "status": "linked_to_existing",
            "incident_id": existing.id,
            "message": f"Linked to active incident {existing.id}. "
                       f"{len(existing.callers)} other callers already reporting.",
            "current_briefing": existing.get_briefing(),
        }
    sev = IncidentSeverity(severity) if severity in IncidentSeverity.__members__ else IncidentSeverity.MEDIUM
    incident = incident_manager.create_incident(
        incident_type=incident_type, severity=sev,
        location=location, location_coords=coords, summary=description,
    )
    return {"status": "new_incident_created", "incident_id": incident.id}


def add_caller_to_incident(
    incident_id: str,
    caller_role: str = "UNKNOWN",
    caller_name: str = "",
    caller_location: str = "",
    emotional_state: str = "unknown",
) -> dict:
    """Register a caller in an active incident.

    Args:
        incident_id: The incident this caller is part of
        caller_role: VICTIM, WITNESS, BYSTANDER, REPORTING_PARTY
        caller_name: Caller's name if provided
        caller_location: Where the caller currently is
        emotional_state: calm, distressed, panicked, injured

    Returns:
        dict with caller_id and briefing
    """
    incident = incident_manager.get_incident(incident_id)
    if not incident:
        return {"status": "error", "message": f"Incident {incident_id} not found"}
    role = CallerRole(caller_role) if caller_role in CallerRole.__members__ else CallerRole.UNKNOWN
    caller = CallerInfo(role=role, name=caller_name, location=caller_location, emotional_state=emotional_state)
    incident.add_caller(caller)
    return {
        "status": "success", "caller_id": caller.id,
        "incident_id": incident_id, "total_callers": len(incident.callers),
        "briefing": incident.get_briefing(),
    }


def submit_intelligence(incident_id: str, caller_id: str, intel: str) -> dict:
    """Submit new intelligence from a caller. Shared with ALL agents.

    Args:
        incident_id: The incident ID
        caller_id: The caller providing this intel
        intel: The new information

    Returns:
        dict confirming the intel was added
    """
    incident = incident_manager.get_incident(incident_id)
    if not incident:
        return {"status": "error", "message": "Incident not found"}
    incident.update_intel(caller_id, intel)
    return {"status": "intel_recorded", "updated_briefing": incident.get_briefing()}


def update_suspect_info(
    incident_id: str, description: str = "", armed: bool = None,
    weapon_type: str = "", last_known_location: str = "", name: str = "",
) -> dict:
    """Update suspect information. Critical for officer safety.

    Args:
        incident_id: The incident ID
        description: Physical description of suspect
        armed: Whether suspect is armed
        weapon_type: Type of weapon if armed
        last_known_location: Where suspect was last seen
        name: Suspect's name if known

    Returns:
        dict confirming update
    """
    incident = incident_manager.get_incident(incident_id)
    if not incident:
        return {"status": "error", "message": "Incident not found"}
    incident.update_suspect(
        description=description, armed=armed, weapon_type=weapon_type,
        last_known_location=last_known_location, name=name,
    )
    return {"status": "suspect_info_updated", "suspect": incident.suspect.to_dict()}


def get_incident_briefing(incident_id: str) -> dict:
    """Get current full briefing for an incident.

    Args:
        incident_id: The incident ID

    Returns:
        dict with full incident briefing
    """
    incident = incident_manager.get_incident(incident_id)
    if not incident:
        return {"status": "error", "message": "Incident not found"}
    return {"status": "success", "briefing": incident.get_briefing(), "data": incident.to_dict()}


def dispatch_units(incident_id: str, units: list) -> dict:
    """Record dispatched units for an incident.

    Args:
        incident_id: The incident ID
        units: List of unit identifiers

    Returns:
        dict confirming dispatch
    """
    incident = incident_manager.get_incident(incident_id)
    if not incident:
        return {"status": "error", "message": "Incident not found"}
    incident.dispatched_units.extend(units)
    incident._log(f"Units dispatched: {', '.join(units)}")
    incident.status = "units_dispatched"
    return {"status": "units_dispatched", "units": incident.dispatched_units}
