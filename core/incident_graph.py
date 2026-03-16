"""
Incident Knowledge Graph — Real-time shared intelligence.

All agents read/write to this graph. When one caller agent
learns the suspect is in the backyard, every other agent
and the dispatcher dashboard sees it instantly.
"""
import uuid
import time
import json
import asyncio
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class IncidentSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class CallerRole(str, Enum):
    VICTIM = "VICTIM"
    WITNESS = "WITNESS"
    BYSTANDER = "BYSTANDER"
    CHILD = "CHILD"
    REPORTING_PARTY = "REPORTING_PARTY"
    INVOLVED_PARTY = "INVOLVED_PARTY"
    OFFICIAL = "OFFICIAL"
    UNKNOWN = "UNKNOWN"


@dataclass
class CallerInfo:
    """Information about a single caller in the incident."""
    id: str = field(default_factory=lambda: f"caller_{uuid.uuid4().hex[:8]}")
    role: CallerRole = CallerRole.UNKNOWN
    name: str = ""
    phone: str = ""
    location: str = ""
    location_coords: Optional[tuple] = None
    status: str = "on_call"
    emotional_state: str = "unknown"
    key_intel: list = field(default_factory=list)
    agent_id: str = ""
    connected_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "role": self.role.value,
            "name": self.name,
            "phone": self.phone,
            "location": self.location,
            "status": self.status,
            "emotional_state": self.emotional_state,
            "key_intel": self.key_intel,
            "agent_id": self.agent_id,
        }


@dataclass
class SuspectInfo:
    """Known information about a suspect."""
    description: str = ""
    armed: Optional[bool] = None
    weapon_type: str = ""
    last_known_location: str = ""
    direction_of_travel: str = ""
    vehicle: str = ""
    name: str = ""

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v}


@dataclass
class Incident:
    """
    A single emergency incident involving multiple callers.
    This is the shared knowledge base all agents read/write.
    """
    id: str = field(default_factory=lambda: f"inc_{uuid.uuid4().hex[:8]}")
    incident_type: str = ""
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    location: str = ""
    location_coords: Optional[tuple] = None
    summary: str = ""
    callers: dict = field(default_factory=dict)
    suspect: SuspectInfo = field(default_factory=SuspectInfo)
    victims_count: int = 0
    children_involved: bool = False
    dispatched_units: list = field(default_factory=list)
    recommended_response: list = field(default_factory=list)
    timeline: list = field(default_factory=list)
    dedup_confidence: float = 0.0
    merged_caller_count: int = 0
    status: str = "active"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def add_caller(self, caller: CallerInfo):
        self.callers[caller.id] = caller
        self._log(f"New caller connected: {caller.role.value}", caller.id)
        self.updated_at = time.time()

    def update_intel(self, source_caller_id: str, intel: str):
        if source_caller_id in self.callers:
            self.callers[source_caller_id].key_intel.append(intel)
        self._log(intel, source_caller_id)
        self.updated_at = time.time()

    def update_suspect(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self.suspect, k) and v:
                setattr(self.suspect, k, v)
        self.updated_at = time.time()

    def _log(self, event: str, source: str = "system"):
        self.timeline.append({
            "time": time.time(),
            "source": source,
            "event": event,
        })

    def get_briefing(self) -> str:
        parts = [f"INCIDENT: {self.incident_type.upper()} at {self.location}"]
        parts.append(f"Severity: {self.severity.value}")
        parts.append(f"Active callers: {len(self.callers)}")
        if self.suspect.description:
            parts.append(f"Suspect: {self.suspect.description}")
            if self.suspect.armed is not None:
                armed_str = f"YES - {self.suspect.weapon_type}" if self.suspect.armed else "No"
                parts.append(f"Armed: {armed_str}")
            if self.suspect.last_known_location:
                parts.append(f"Suspect last seen: {self.suspect.last_known_location}")
        if self.children_involved:
            parts.append("WARNING: CHILDREN INVOLVED")
        for cid, caller in self.callers.items():
            parts.append(f"  Caller ({caller.role.value}): {caller.location} - {caller.emotional_state}")
            if caller.key_intel:
                parts.append(f"    Intel: {'; '.join(caller.key_intel[-3:])}")
        if self.dispatched_units:
            parts.append(f"Units dispatched: {', '.join(self.dispatched_units)}")
        return "\n".join(parts)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "incident_type": self.incident_type,
            "severity": self.severity.value,
            "location": self.location,
            "summary": self.summary,
            "callers": {k: v.to_dict() for k, v in self.callers.items()},
            "suspect": self.suspect.to_dict(),
            "victims_count": self.victims_count,
            "children_involved": self.children_involved,
            "dispatched_units": self.dispatched_units,
            "timeline": self.timeline[-20:],
            "status": self.status,
            "caller_count": len(self.callers),
            "dedup_confidence": round(self.dedup_confidence, 3),
            "merged_caller_count": self.merged_caller_count,
        }


class IncidentManager:
    """Manages all active incidents. Singleton."""

    def __init__(self):
        self.incidents: dict = {}
        self._listeners: list = []

    def create_incident(self, incident_type: str, location: str,
                        description: str, caller_id: str, priority: int = 3) -> 'Incident':
        severity_map = {1: IncidentSeverity.CRITICAL, 2: IncidentSeverity.HIGH,
                        3: IncidentSeverity.MEDIUM, 4: IncidentSeverity.LOW,
                        5: IncidentSeverity.LOW}
        incident = Incident(
            incident_type=incident_type,
            location=location,
            summary=description,
            severity=severity_map.get(priority, IncidentSeverity.MEDIUM),
        )
        # Register the first caller
        caller = CallerInfo(id=caller_id)
        incident.add_caller(caller)
        self.incidents[incident.id] = incident
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._notify({"type": "incident_created", "data": incident.to_dict()}))
        except RuntimeError:
            pass  # No event loop — skip WebSocket notification (sync context)
        return incident

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        return self.incidents.get(incident_id)

    def get_active_incidents(self) -> list:
        return [i for i in self.incidents.values() if i.status == "active"]

    def update_incident(self, incident_id: str, **kwargs) -> 'Incident':
        incident = self.incidents.get(incident_id)
        if incident:
            for k, v in kwargs.items():
                if hasattr(incident, k):
                    setattr(incident, k, v)
            incident.updated_at = time.time()
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._notify({"type": "incident_updated", "data": incident.to_dict()}))
            except RuntimeError:
                pass  # No event loop — skip WebSocket notification (sync context)
        return incident

    def add_listener(self, ws):
        self._listeners.append(ws)

    def remove_listener(self, ws):
        if ws in self._listeners:
            self._listeners.remove(ws)

    async def _notify(self, message: dict):
        dead = []
        for ws in self._listeners:
            try:
                await ws.send_text(json.dumps(message, default=str))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._listeners.remove(ws)


incident_manager = IncidentManager()
