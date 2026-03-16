"""REST API routes for dashboard and simulation."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.incident_graph import incident_manager

router = APIRouter(tags=["nexus911"])


class SimulateCallRequest(BaseModel):
    caller_name: str = "Anonymous"
    location: str
    description: str
    latitude: float = 0.0
    longitude: float = 0.0


@router.get("/incidents")
async def get_all_incidents():
    return {"incidents": [inc.to_dict() for inc in incident_manager.get_active_incidents()]}


@router.get("/incidents/{incident_id}")
async def get_incident(incident_id: str):
    incident = incident_manager.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident.to_dict()


@router.get("/incidents/{incident_id}/briefing")
async def get_briefing(incident_id: str):
    incident = incident_manager.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"briefing": incident.get_briefing()}


@router.post("/simulate/call")
async def simulate_call(request: SimulateCallRequest):
    from agents.tools.incident_tools import report_new_emergency, add_caller_to_incident
    result = report_new_emergency(
        location=request.location, description=request.description,
        latitude=request.latitude, longitude=request.longitude,
    )
    incident_id = result["incident_id"]
    caller_result = add_caller_to_incident(
        incident_id=incident_id, caller_name=request.caller_name, caller_location=request.location,
    )
    return {"status": "call_simulated", "incident": result, "caller": caller_result}


@router.get("/stats")
async def get_stats():
    incidents = list(incident_manager.incidents.values())
    active = [i for i in incidents if i.status == "active"]
    return {
        "total_incidents": len(incidents),
        "active_incidents": len(active),
        "total_callers": sum(len(i.callers) for i in incidents),
        "critical_incidents": sum(1 for i in active if i.severity.value == "CRITICAL"),
    }
