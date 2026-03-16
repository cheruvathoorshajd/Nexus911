"""Tools for incident management - shared across all agents."""
import asyncio
import logging
from core.incident_graph import incident_manager

logger = logging.getLogger("nexus911.tools")

try:
    from verification.hooks import verify_before_intel_submit, attach_verification_to_incident
    VERIFYLAYER_AVAILABLE = True
except ImportError:
    VERIFYLAYER_AVAILABLE = False
    logger.warning("VerifyLayer not available — intel will not be verified")


def create_incident(
    incident_type: str,
    location: str,
    description: str,
    caller_id: str,
    priority: int = 3,
) -> dict:
    """Create a new incident in the system.

    Args:
        incident_type: Type of incident (e.g., 'fire', 'medical', 'accident')
        location: Location of the incident
        description: Description of what happened
        caller_id: ID of the caller reporting
        priority: Priority level 1-5 (1=highest)

    Returns:
        dict with incident details
    """
    incident = incident_manager.create_incident(
        incident_type=incident_type,
        location=location,
        description=description,
        caller_id=caller_id,
        priority=priority,
    )
    return incident.to_dict()


def submit_intelligence(
    incident_id: str,
    caller_id: str,
    intel: str,
    caller_role: str = "UNKNOWN",
    agent_id: str = "",
    utterance: str = "",
) -> dict:
    """Submit new intelligence from a caller. Shared with ALL agents.

    Args:
        incident_id: The incident ID
        caller_id: The caller providing this intel
        intel: The new information
        caller_role: VICTIM, WITNESS, BYSTANDER, etc.
        agent_id: The agent handling this caller
        utterance: Raw transcript text (improves verification accuracy)

    Returns:
        dict confirming the intel was added
    """
    incident = incident_manager.get_incident(incident_id)
    if not incident:
        return {"status": "error", "message": "Incident not found"}

    # Intel ALWAYS enters the graph immediately (fail-open for 911 safety)
    incident.update_intel(caller_id, intel)

    # Fire-and-forget verification in background (non-blocking)
    if VERIFYLAYER_AVAILABLE:
        try:
            loop = asyncio.get_running_loop()
            # Mark as pending_verification immediately so dashboard shows status
            attach_verification_to_incident(
                incident_id, caller_id, intel,
                {"nli_label": "pending_verification", "confidence": 0.0},
            )
            loop.create_task(_verify_and_attach(
                incident_id, caller_id, caller_role, agent_id, intel, utterance
            ))
        except RuntimeError:
            pass  # No event loop running — skip verification in sync context

    return {"status": "intel_recorded", "updated_briefing": incident.get_briefing()}


async def _verify_and_attach(incident_id, caller_id, caller_role, agent_id, intel, utterance):
    """Background task: verify intel then attach metadata to timeline."""
    try:
        result = await verify_before_intel_submit(
            incident_id, caller_id, caller_role, agent_id, intel, utterance
        )
        attach_verification_to_incident(
            incident_id, caller_id, intel, result["verification"]
        )
    except Exception as e:
        logger.error(f"Background verification failed (non-fatal): {e}")


def get_incident_briefing(incident_id: str) -> dict:
    """Get current incident briefing for any agent.

    Args:
        incident_id: The incident to get briefing for

    Returns:
        dict with current incident status and all intel
    """
    incident = incident_manager.get_incident(incident_id)
    if not incident:
        return {"status": "error", "message": "Incident not found"}
    return {
        "status": "ok",
        "briefing": incident.get_briefing(),
        "incident": incident.to_dict(),
    }


def update_incident_priority(incident_id: str, new_priority: int) -> dict:
    """Update incident priority based on new information.

    Args:
        incident_id: The incident to update
        new_priority: New priority level 1-5

    Returns:
        dict confirming the update
    """
    incident = incident_manager.get_incident(incident_id)
    if not incident:
        return {"status": "error", "message": "Incident not found"}
    incident.priority = new_priority
    return {"status": "priority_updated", "new_priority": new_priority}


def report_new_emergency(
    location: str,
    description: str,
    latitude: float = 0.0,
    longitude: float = 0.0,
    incident_type: str = "emergency",
) -> dict:
    """Report a new emergency and create or deduplicate into an incident.

    Args:
        location: Where the emergency is happening
        description: What is happening
        latitude: GPS latitude (optional)
        longitude: GPS longitude (optional)
        incident_type: Type of incident (e.g. 'domestic_violence', 'accident')

    Returns:
        dict with incident_id and status
    """
    from core.deduplication import DeduplicationEngine

    dedup = DeduplicationEngine(incident_manager)
    coords = (latitude, longitude) if latitude and longitude else None

    # Try to find an existing incident
    existing, match_score = dedup.find_matching_incident(
        location=location,
        location_coords=coords,
        description=description,
    )

    if existing:
        existing.update_intel("system", f"New caller reporting: {description}")
        # Track dedup confidence — keep the highest score seen
        if match_score > existing.dedup_confidence:
            existing.dedup_confidence = match_score
        existing.merged_caller_count += 1
        logger.info(f"Deduplicated into existing incident {existing.id} (confidence={match_score:.2%})")
        return {
            "incident_id": existing.id,
            "status": "deduplicated",
            "dedup_confidence": match_score,
            "message": f"Merged with existing incident at {existing.location} (match: {match_score:.0%})",
        }

    # Create new incident
    import uuid
    caller_id = f"caller_{uuid.uuid4().hex[:8]}"
    incident = incident_manager.create_incident(
        incident_type=incident_type,
        location=location,
        description=description,
        caller_id=caller_id,
    )
    if coords:
        incident.location_coords = coords

    logger.info(f"New incident created: {incident.id}")
    return {
        "incident_id": incident.id,
        "status": "new_incident",
        "message": f"New incident created at {location}",
    }


def add_caller_to_incident(
    incident_id: str,
    caller_name: str = "Anonymous",
    caller_role: str = "UNKNOWN",
    caller_location: str = "",
) -> dict:
    """Add a new caller to an existing incident.

    Args:
        incident_id: The incident to add the caller to
        caller_name: Name of the caller
        caller_role: VICTIM, WITNESS, BYSTANDER, REPORTING_PARTY, etc.
        caller_location: Where the caller is located

    Returns:
        dict with caller_id and status
    """
    from core.incident_graph import CallerInfo, CallerRole as CR

    incident = incident_manager.get_incident(incident_id)
    if not incident:
        return {"status": "error", "message": "Incident not found"}

    try:
        role = CR(caller_role)
    except ValueError:
        role = CR.UNKNOWN

    caller = CallerInfo(
        role=role,
        name=caller_name,
        location=caller_location,
    )
    incident.add_caller(caller)

    logger.info(f"Caller {caller.id} ({caller_role}) added to incident {incident_id}")
    return {
        "status": "caller_added",
        "caller_id": caller.id,
        "incident_id": incident_id,
    }


def update_suspect_info(
    incident_id: str,
    description: str = "",
    armed: bool = False,
    weapon_type: str = "",
    last_known_location: str = "",
    direction_of_travel: str = "",
    vehicle: str = "",
    name: str = "",
) -> dict:
    """Update suspect information for an incident.

    Args:
        incident_id: The incident ID
        description: Physical description of suspect
        armed: Whether suspect is armed
        weapon_type: Type of weapon if armed
        last_known_location: Where suspect was last seen
        direction_of_travel: Direction suspect is moving
        vehicle: Vehicle description
        name: Suspect name if known

    Returns:
        dict confirming the update
    """
    incident = incident_manager.get_incident(incident_id)
    if not incident:
        return {"status": "error", "message": "Incident not found"}

    incident.update_suspect(
        description=description,
        armed=armed,
        weapon_type=weapon_type,
        last_known_location=last_known_location,
        direction_of_travel=direction_of_travel,
        vehicle=vehicle,
        name=name,
    )

    # Escalate severity if armed
    if armed:
        from core.incident_graph import IncidentSeverity
        incident.severity = IncidentSeverity.CRITICAL
        incident._log(f"CRITICAL: Suspect is armed with {weapon_type or 'unknown weapon'}", "system")

    logger.info(f"Suspect info updated for incident {incident_id}")
    return {
        "status": "suspect_updated",
        "armed": armed,
        "suspect": incident.suspect.to_dict(),
    }


def dispatch_units(
    incident_id: str,
    units: list[str] = None,
) -> dict:
    """Dispatch emergency response units to an incident.

    Args:
        incident_id: The incident ID
        units: List of unit types to dispatch (e.g. ['Patrol Unit', 'EMS'])

    Returns:
        dict confirming dispatch
    """
    if units is None:
        units = ["Patrol Unit"]

    incident = incident_manager.get_incident(incident_id)
    if not incident:
        return {"status": "error", "message": "Incident not found"}

    for unit in units:
        if unit not in incident.dispatched_units:
            incident.dispatched_units.append(unit)
            incident._log(f"Unit dispatched: {unit}", "dispatch")

    logger.info(f"Dispatched {units} to incident {incident_id}")
    return {
        "status": "units_dispatched",
        "incident_id": incident_id,
        "dispatched_units": incident.dispatched_units,
    }
