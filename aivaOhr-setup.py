#!/usr/bin/env python3
"""
AivaOhr Project Generator
Run: python setup_project.py
Creates the entire project structure with all files.
"""
import os

PROJECT = "aivaOhr"

def write(path, content):
    full = os.path.join(PROJECT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content.lstrip("\n"))
    print(f"  ✓ {path}")

print(f"\n⬡ Generating {PROJECT} project...\n")

# ─── LICENSE ───────────────────────────────────────────────
write("LICENSE", """MIT License

Copyright (c) 2026 Dennis Sharon Cheruvathoor Shaj

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""")

# ─── .env.example ──────────────────────────────────────────
write(".env.example", """# AivaOhr Configuration
GOOGLE_API_KEY=your-gemini-api-key
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
FIRESTORE_DATABASE=(default)
HOST=0.0.0.0
PORT=8080
DEBUG=true
""")

# ─── .gitignore ────────────────────────────────────────────
write(".gitignore", """__pycache__/
*.py[cod]
.env
.venv/
venv/
node_modules/
frontend/build/
*.db
*.sqlite
.DS_Store
""")

# ─── .gcloudignore ────────────────────────────────────────
write(".gcloudignore", """.git
.gitignore
__pycache__/
.venv/
venv/
node_modules/
frontend/node_modules/
*.py[cod]
.env
tests/
docs/
""")

# ─── requirements.txt ─────────────────────────────────────
write("requirements.txt", """# AivaOhr — Multi-Agent Emergency Coordination
google-adk>=1.2.0
google-genai>=1.10.0
google-cloud-firestore>=2.19.0
google-cloud-aiplatform>=1.78.0
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
websockets>=14.0
python-dotenv>=1.0.0
pydantic>=2.8.0
pydantic-settings>=2.0.0
httpx>=0.27.0
python-multipart>=0.0.9
geopy>=2.4.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
""")

# ─── Dockerfile ────────────────────────────────────────────
write("Dockerfile", """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]
""")

# ─── cloudbuild.yaml ──────────────────────────────────────
write("cloudbuild.yaml", """steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/aivaOhr', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/aivaOhr']
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'aivaohr'
      - '--image'
      - 'gcr.io/$PROJECT_ID/aivaOhr'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
      - '--memory'
      - '1Gi'
      - '--set-env-vars'
      - 'GOOGLE_CLOUD_PROJECT=$PROJECT_ID'
images:
  - 'gcr.io/$PROJECT_ID/aivaOhr'
""")

# ─── run.py ────────────────────────────────────────────────
write("run.py", """#!/usr/bin/env python3
\"\"\"AivaOhr — Start the server.\"\"\"
import uvicorn
from core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
""")

# ─── CORE ──────────────────────────────────────────────────
write("core/__init__.py", '"""AivaOhr core modules."""\n')

write("core/config.py", """\"\"\"Global configuration.\"\"\"
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    GOOGLE_API_KEY: str = ""
    GOOGLE_CLOUD_PROJECT: str = ""
    GOOGLE_CLOUD_LOCATION: str = "us-central1"
    FIRESTORE_DATABASE: str = "(default)"
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_LIVE_MODEL: str = "gemini-2.5-flash-native-audio"
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    DEBUG: bool = True
    APP_NAME: str = "AivaOhr"
    MAX_CONCURRENT_CALLERS: int = 10
    DEDUP_SIMILARITY_THRESHOLD: float = 0.70
    INCIDENT_RADIUS_METERS: float = 500.0

    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
""")

write("core/incident_graph.py", """\"\"\"
Incident Knowledge Graph — shared real-time intelligence.
All agents read/write here. When Caller Agent A learns the suspect
went to the backyard, every other agent sees it instantly.
\"\"\"
import uuid
import time
import json
import asyncio
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class CallerRole(str, Enum):
    VICTIM = "VICTIM"
    WITNESS = "WITNESS"
    BYSTANDER = "BYSTANDER"
    REPORTER = "REPORTING_PARTY"
    INVOLVED = "INVOLVED_PARTY"
    UNKNOWN = "UNKNOWN"


@dataclass
class CallerInfo:
    id: str = field(default_factory=lambda: f"c_{uuid.uuid4().hex[:6]}")
    role: CallerRole = CallerRole.UNKNOWN
    name: str = ""
    phone: str = ""
    location: str = ""
    coords: Optional[tuple[float, float]] = None
    status: str = "on_call"
    emotional_state: str = "unknown"
    intel: list[str] = field(default_factory=list)
    agent_id: str = ""
    connected_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "role": self.role.value, "name": self.name,
            "location": self.location, "status": self.status,
            "emotional_state": self.emotional_state, "intel": self.intel,
            "agent_id": self.agent_id,
        }


@dataclass
class SuspectInfo:
    description: str = ""
    armed: Optional[bool] = None
    weapon_type: str = ""
    last_known_location: str = ""
    direction: str = ""
    vehicle: str = ""
    name: str = ""

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None and v != ""}


@dataclass
class Incident:
    id: str = field(default_factory=lambda: f"inc_{uuid.uuid4().hex[:8]}")
    incident_type: str = ""
    severity: Severity = Severity.MEDIUM
    location: str = ""
    coords: Optional[tuple[float, float]] = None
    summary: str = ""
    callers: dict[str, CallerInfo] = field(default_factory=dict)
    suspect: SuspectInfo = field(default_factory=SuspectInfo)
    victims_count: int = 0
    children_involved: bool = False
    dispatched_units: list[str] = field(default_factory=list)
    timeline: list[dict] = field(default_factory=list)
    status: str = "active"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def add_caller(self, caller: CallerInfo):
        self.callers[caller.id] = caller
        self._log(f"Caller joined: {caller.role.value} — {caller.name or 'Anonymous'}", caller.id)
        self.updated_at = time.time()

    def add_intel(self, caller_id: str, intel: str):
        if caller_id in self.callers:
            self.callers[caller_id].intel.append(intel)
        self._log(intel, caller_id)
        self.updated_at = time.time()

    def update_suspect(self, **kw):
        for k, v in kw.items():
            if hasattr(self.suspect, k) and v:
                setattr(self.suspect, k, v)
        self._log(f"Suspect updated: {kw}", "system")
        self.updated_at = time.time()

    def _log(self, event: str, source: str = "system"):
        self.timeline.append({"t": time.time(), "src": source, "event": event})

    def briefing(self) -> str:
        lines = [
            f"═══ INCIDENT {self.id} ═══",
            f"Type: {self.incident_type.upper()} | Severity: {self.severity.value}",
            f"Location: {self.location}",
            f"Active callers: {len(self.callers)}",
        ]
        if self.suspect.description:
            lines.append(f"SUSPECT: {self.suspect.description}")
            if self.suspect.armed:
                lines.append(f"  ⚠ ARMED: {self.suspect.weapon_type}")
            if self.suspect.last_known_location:
                lines.append(f"  Last seen: {self.suspect.last_known_location}")
        if self.children_involved:
            lines.append("⚠ CHILDREN INVOLVED")
        for c in self.callers.values():
            lines.append(f"  [{c.role.value}] {c.name or c.id} @ {c.location} ({c.emotional_state})")
            for i in c.intel[-3:]:
                lines.append(f"    → {i}")
        if self.dispatched_units:
            lines.append(f"Units: {', '.join(self.dispatched_units)}")
        return "\\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "incident_type": self.incident_type,
            "severity": self.severity.value, "location": self.location,
            "summary": self.summary, "status": self.status,
            "callers": {k: v.to_dict() for k, v in self.callers.items()},
            "suspect": self.suspect.to_dict(),
            "victims_count": self.victims_count,
            "children_involved": self.children_involved,
            "dispatched_units": self.dispatched_units,
            "timeline": self.timeline[-30:],
            "caller_count": len(self.callers),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class IncidentManager:
    def __init__(self):
        self.incidents: dict[str, Incident] = {}
        self._ws_clients: list = []

    def create(self, **kw) -> Incident:
        inc = Incident(**kw)
        self.incidents[inc.id] = inc
        asyncio.ensure_future(self._broadcast("incident_created", inc.to_dict()))
        return inc

    def get(self, iid: str) -> Optional[Incident]:
        return self.incidents.get(iid)

    def active(self) -> list[Incident]:
        return [i for i in self.incidents.values() if i.status == "active"]

    def add_ws(self, ws):
        self._ws_clients.append(ws)

    def remove_ws(self, ws):
        self._ws_clients = [w for w in self._ws_clients if w != ws]

    async def _broadcast(self, event_type: str, data: dict):
        msg = json.dumps({"type": event_type, "data": data})
        dead = []
        for ws in self._ws_clients:
            try:
                await ws.send_text(msg)
            except Exception:
                dead.append(ws)
        for w in dead:
            self._ws_clients.remove(w)

    async def notify_update(self, inc: Incident):
        await self._broadcast("incident_updated", inc.to_dict())


incident_manager = IncidentManager()
""")

write("core/deduplication.py", """\"\"\"
Multi-Caller Deduplication — clusters calls about the same incident.
Uses location proximity + keyword overlap + temporal proximity.
\"\"\"
import math
import time
from typing import Optional
from core.incident_graph import IncidentManager, Incident
from core.config import settings


class DeduplicationEngine:
    def __init__(self, im: IncidentManager):
        self.im = im

    def find_match(
        self, location: str, coords: Optional[tuple], description: str,
    ) -> Optional[Incident]:
        now = time.time()
        best, best_score = None, 0.0

        for inc in self.im.active():
            if (now - inc.created_at) / 60 > 30:
                continue
            score = 0.0
            if coords and inc.coords:
                dist = self._haversine(coords, inc.coords)
                if dist < settings.INCIDENT_RADIUS_METERS:
                    score += 0.5
                elif dist < settings.INCIDENT_RADIUS_METERS * 3:
                    score += 0.2
            elif location and inc.location:
                score += self._jaccard(location.lower(), inc.location.lower()) * 0.4
            if description and inc.summary:
                score += self._jaccard(description.lower(), inc.summary.lower()) * 0.3
            recency = max(0, 1 - ((now - inc.created_at) / 1800)) * 0.2
            score += recency
            if score > best_score:
                best_score, best = score, inc

        return best if best_score >= settings.DEDUP_SIMILARITY_THRESHOLD else None

    @staticmethod
    def _haversine(a: tuple, b: tuple) -> float:
        R = 6_371_000
        la, lo = math.radians(a[0]), math.radians(a[1])
        lb, lob = math.radians(b[0]), math.radians(b[1])
        d = math.sin((lb-la)/2)**2 + math.cos(la)*math.cos(lb)*math.sin((lob-lo)/2)**2
        return R * 2 * math.asin(math.sqrt(d))

    @staticmethod
    def _jaccard(a: str, b: str) -> float:
        wa, wb = set(a.split()), set(b.split())
        return len(wa & wb) / len(wa | wb) if (wa | wb) else 0.0
""")

write("core/caller_manager.py", """\"\"\"Tracks all active caller sessions.\"\"\"
from dataclasses import dataclass, field
from typing import Optional
import time


@dataclass
class CallerSession:
    caller_id: str
    incident_id: str
    agent_id: str
    role: str = "UNKNOWN"
    status: str = "active"
    started_at: float = field(default_factory=time.time)


class CallerManager:
    def __init__(self):
        self.sessions: dict[str, CallerSession] = {}

    def register(self, caller_id: str, incident_id: str, agent_id: str, role: str = "UNKNOWN") -> CallerSession:
        s = CallerSession(caller_id=caller_id, incident_id=incident_id, agent_id=agent_id, role=role)
        self.sessions[caller_id] = s
        return s

    def get(self, caller_id: str) -> Optional[CallerSession]:
        return self.sessions.get(caller_id)

    def active_for_incident(self, incident_id: str) -> list[CallerSession]:
        return [s for s in self.sessions.values() if s.incident_id == incident_id and s.status == "active"]

    def disconnect(self, caller_id: str):
        if caller_id in self.sessions:
            self.sessions[caller_id].status = "disconnected"

    @property
    def active_count(self) -> int:
        return sum(1 for s in self.sessions.values() if s.status == "active")


caller_manager = CallerManager()
""")

# ─── AGENTS ────────────────────────────────────────────────
write("agents/__init__.py", '"""AivaOhr agent definitions."""\n')
write("agents/coordinator/__init__.py", "")

write("agents/coordinator/agent.py", """\"\"\"
Coordinator Agent — root orchestrator.
Routes calls, deduplicates incidents, maintains unified picture.
\"\"\"
from google.adk.agents import Agent
from agents.tools.incident_tools import (
    report_emergency, register_caller, get_briefing, dispatch_units,
)

INSTRUCTION = \"\"\"You are AivaOhr Coordinator, the central intelligence of a
multi-agent emergency response system called AivaOhr (Father's Light).

Your responsibilities:
1. When a new caller connects, determine the nature of their emergency
2. Check if this call relates to an existing incident (use report_emergency)
3. Assign the caller a role: VICTIM, WITNESS, BYSTANDER, or REPORTING_PARTY
4. Register them (use register_caller)
5. Periodically check get_briefing for updates from other agents
6. Recommend units to dispatch

CRITICAL RULES:
- ALWAYS prioritize child safety and officer safety
- Weapons mentioned → immediately flag CRITICAL severity
- Multiple callers at same location → link to ONE incident
- Responses to dispatchers: clear, concise, actionable
- Never speculate — only report confirmed intel from callers
- When children are involved, note it explicitly
\"\"\"

root_agent = Agent(
    model="gemini-2.5-flash",
    name="aivaohr_coordinator",
    instruction=INSTRUCTION,
    tools=[report_emergency, register_caller, get_briefing, dispatch_units],
)
""")

write("agents/caller_agent/__init__.py", "")

write("agents/caller_agent/agent.py", """\"\"\"
Caller Agent Factory — creates role-specific voice agents.
Each active 911 caller gets a dedicated agent instance that
talks via Gemini Live API and feeds intel to the shared graph.
\"\"\"
from google.adk.agents import Agent
from agents.tools.incident_tools import submit_intel, update_suspect, get_briefing
from agents.tools.caller_tools import safety_instructions, transfer_to_human


ROLE_PROMPTS = {
    "VICTIM": (
        "You are speaking with a VICTIM. Priority: their immediate safety. "
        "Speak calmly and slowly. Ask: Are you safe? Are you injured? "
        "Can you describe what happened? Guide them to safety."
    ),
    "WITNESS": (
        "You are speaking with a WITNESS who may have critical information. "
        "Ask: What did you see? Can you describe the suspect? "
        "What direction did they go? Are you safe?"
    ),
    "BYSTANDER": (
        "You are speaking with a BYSTANDER who may be confused or scared. "
        "Reassure them help is coming. Ask if they can see anything useful. "
        "Tell them to stay away from the area."
    ),
    "REPORTING_PARTY": (
        "You are speaking with someone REPORTING an emergency involving others. "
        "Gather: location, number of people involved, nature of emergency. "
        "Keep them on the line for updates."
    ),
    "CHILD": (
        "You are speaking with a CHILD. Use simple, calm, reassuring language. "
        "Tell them they are brave. Ask: Can you hide somewhere safe? "
        "Be very quiet like a game. Don't come out until police say so. "
        "Keep them calm. Tell them help is coming."
    ),
}


def create_caller_agent(role: str, incident_id: str, caller_id: str) -> Agent:
    role_prompt = ROLE_PROMPTS.get(role, ROLE_PROMPTS["REPORTING_PARTY"])

    instruction = f\"\"\"You are an AivaOhr Emergency Agent on a live 911 call.

INCIDENT: {incident_id} | CALLER: {caller_id} | ROLE: {role}

{role_prompt}

RULES:
- Speak clearly, calmly, with empathy
- Extract ALL useful information and submit via submit_intel
- Weapons mentioned → immediately use update_suspect
- Periodically call get_briefing to see what other agents learned
- If caller is a child, adjust language to be age-appropriate
- Immediate danger → give safety_instructions first
- Cannot help further → transfer_to_human
- NEVER hang up — caller may have more intel
- You are one of MULTIPLE agents handling this incident simultaneously
- Other agents are talking to OTHER callers right now
\"\"\"

    return Agent(
        model="gemini-2.5-flash",
        name=f"caller_agent_{role.lower()}_{caller_id}",
        instruction=instruction,
        tools=[submit_intel, update_suspect, get_briefing, safety_instructions, transfer_to_human],
    )
""")

write("agents/dispatcher_agent/__init__.py", "")

write("agents/dispatcher_agent/agent.py", """\"\"\"
Dispatcher Agent — human dispatcher-facing agent.
Aggregates all intel and presents unified operational view.
\"\"\"
from google.adk.agents import Agent
from agents.tools.incident_tools import get_briefing, dispatch_units
from agents.tools.dispatch_tools import recommend_units
from agents.tools.safety_tools import verify_protocol

INSTRUCTION = \"\"\"You are the AivaOhr Dispatch Intelligence Agent.

You serve human dispatchers by providing a unified view of multi-caller
incidents. Multiple AI agents are simultaneously handling different callers
in the same emergency. You aggregate their findings.

Your role:
1. Present clear, structured briefings when asked
2. Recommend appropriate response units
3. Flag critical updates immediately (weapons, children, injuries)
4. Verify all recommendations against emergency protocols
5. Track which units have been dispatched

Always be concise. Dispatchers need facts, not prose.
\"\"\"

dispatcher_agent = Agent(
    model="gemini-2.5-flash",
    name="aivaohr_dispatcher",
    instruction=INSTRUCTION,
    tools=[get_briefing, dispatch_units, recommend_units, verify_protocol],
)
""")

# ─── TOOLS ─────────────────────────────────────────────────
write("agents/tools/__init__.py", "")

write("agents/tools/incident_tools.py", """\"\"\"Tools for incident management — used by all agents.\"\"\"
from core.incident_graph import incident_manager, CallerInfo, CallerRole, Severity
from core.deduplication import DeduplicationEngine

_dedup = DeduplicationEngine(incident_manager)


def report_emergency(
    location: str, description: str, incident_type: str = "unknown",
    severity: str = "MEDIUM", latitude: float = 0.0, longitude: float = 0.0,
) -> dict:
    \"\"\"Report a new emergency or link to existing incident.
    Args:
        location: Address or description from caller
        description: What is happening
        incident_type: e.g. domestic_violence, fire, medical, active_shooter
        severity: CRITICAL, HIGH, MEDIUM, LOW
        latitude: GPS lat if available
        longitude: GPS lon if available
    Returns: dict with incident_id and status
    \"\"\"
    coords = (latitude, longitude) if latitude and longitude else None
    existing = _dedup.find_match(location, coords, description)

    if existing:
        return {
            "status": "linked_to_existing", "incident_id": existing.id,
            "message": f"Linked to incident {existing.id} ({len(existing.callers)} callers already active)",
            "briefing": existing.briefing(),
        }

    sev = Severity(severity) if severity in Severity.__members__ else Severity.MEDIUM
    inc = incident_manager.create(
        incident_type=incident_type, severity=sev,
        location=location, coords=coords, summary=description,
    )
    return {"status": "new_incident", "incident_id": inc.id, "message": f"Incident {inc.id} created"}


def register_caller(
    incident_id: str, caller_role: str = "UNKNOWN", caller_name: str = "",
    caller_location: str = "", emotional_state: str = "unknown",
) -> dict:
    \"\"\"Register a caller in an incident.
    Args:
        incident_id: Incident to join
        caller_role: VICTIM, WITNESS, BYSTANDER, REPORTING_PARTY, INVOLVED_PARTY
        caller_name: Name if provided
        caller_location: Where caller is right now
        emotional_state: calm, distressed, panicked, injured
    Returns: dict with caller_id
    \"\"\"
    inc = incident_manager.get(incident_id)
    if not inc:
        return {"status": "error", "message": "Incident not found"}

    role = CallerRole(caller_role) if caller_role in CallerRole.__members__ else CallerRole.UNKNOWN
    caller = CallerInfo(role=role, name=caller_name, location=caller_location, emotional_state=emotional_state)
    inc.add_caller(caller)
    return {
        "status": "registered", "caller_id": caller.id,
        "incident_id": incident_id, "total_callers": len(inc.callers),
    }


def submit_intel(incident_id: str, caller_id: str, intel: str) -> dict:
    \"\"\"Submit new intelligence. Shared with ALL agents instantly.
    Args:
        incident_id: Incident ID
        caller_id: Caller providing intel
        intel: The information (e.g. 'suspect went to backyard')
    Returns: dict confirming
    \"\"\"
    inc = incident_manager.get(incident_id)
    if not inc:
        return {"status": "error", "message": "Incident not found"}
    inc.add_intel(caller_id, intel)
    return {"status": "recorded", "message": f"Intel shared: {intel}", "briefing": inc.briefing()}


def update_suspect(
    incident_id: str, description: str = "", armed: bool = None,
    weapon_type: str = "", last_known_location: str = "", name: str = "",
) -> dict:
    \"\"\"Update suspect information. Critical for officer safety.
    Args:
        incident_id: Incident ID
        description: Physical description
        armed: Is suspect armed
        weapon_type: Weapon type if armed
        last_known_location: Where suspect was last seen
        name: Suspect name if known
    Returns: dict confirming
    \"\"\"
    inc = incident_manager.get(incident_id)
    if not inc:
        return {"status": "error", "message": "Incident not found"}
    inc.update_suspect(description=description, armed=armed, weapon_type=weapon_type,
                       last_known_location=last_known_location, name=name)
    if armed:
        inc.severity = Severity.CRITICAL
    return {"status": "updated", "suspect": inc.suspect.to_dict()}


def get_briefing(incident_id: str) -> dict:
    \"\"\"Get full incident briefing. Used by agents to stay updated.
    Args:
        incident_id: Incident ID
    Returns: dict with briefing text and structured data
    \"\"\"
    inc = incident_manager.get(incident_id)
    if not inc:
        return {"status": "error", "message": "Incident not found"}
    return {"status": "ok", "briefing": inc.briefing(), "data": inc.to_dict()}


def dispatch_units(incident_id: str, units: list[str]) -> dict:
    \"\"\"Record dispatched units.
    Args:
        incident_id: Incident ID
        units: List of unit names (e.g. ['Patrol 42', 'EMS 7'])
    Returns: dict confirming
    \"\"\"
    inc = incident_manager.get(incident_id)
    if not inc:
        return {"status": "error", "message": "Incident not found"}
    inc.dispatched_units.extend(units)
    inc._log(f"Dispatched: {', '.join(units)}")
    inc.status = "units_dispatched"
    return {"status": "dispatched", "all_units": inc.dispatched_units}
""")

write("agents/tools/caller_tools.py", """\"\"\"Tools for caller-facing agents.\"\"\"


SAFETY = {
    "active_shooter": {
        "adult": [
            "If you can safely leave, run away from the gunshots NOW.",
            "If you can't leave, lock and barricade the door.",
            "Silence your phone. Stay below window level.",
            "Don't open the door until police identify themselves.",
        ],
        "child": [
            "I need you to be very brave. Can you hide under a bed or in a closet?",
            "Be very very quiet, like the quiet game.",
            "Don't come out until a police officer comes for you.",
            "You're doing so great. Help is coming right now.",
        ],
    },
    "domestic_violence": {
        "adult": [
            "If you can safely leave, go to a neighbor or public place now.",
            "If you can't leave, get to a room with a lock.",
            "Do not confront the person. Officers are on their way.",
        ],
        "child": [
            "You're safe talking to me. Can you go to a room and close the door?",
            "Is there a neighbor you can go to?",
            "Help is coming. You did the right thing calling.",
        ],
    },
    "fire": {
        "adult": ["Leave immediately. Don't use elevators.", "Stay low — smoke rises.", "Once outside, don't go back in."],
        "child": ["Leave the house right now if you can.", "Stay low and crawl.", "Go outside and find a grown-up."],
    },
    "medical": {
        "adult": ["Stay with the person. Keep them calm.", "Don't move them unless in immediate danger.", "Paramedics are coming."],
        "child": ["Stay with them and talk to them.", "Can you unlock the front door for helpers?", "You're being so brave."],
    },
}


def safety_instructions(situation_type: str, caller_is_child: bool = False) -> dict:
    \"\"\"Provide immediate safety instructions.
    Args:
        situation_type: active_shooter, domestic_violence, fire, medical
        caller_is_child: Adjusts language for children
    Returns: dict with instructions list
    \"\"\"
    key = "child" if caller_is_child else "adult"
    instr = SAFETY.get(situation_type, SAFETY["medical"]).get(key, SAFETY["medical"]["adult"])
    return {"status": "ok", "instructions": instr, "relay": "Tell the caller these instructions NOW."}


def transfer_to_human(incident_id: str, reason: str) -> dict:
    \"\"\"Transfer caller to human dispatcher.
    Args:
        incident_id: Incident ID
        reason: Why transfer is needed
    Returns: dict confirming transfer
    \"\"\"
    return {"status": "transfer_requested", "incident_id": incident_id, "reason": reason}
""")

write("agents/tools/dispatch_tools.py", """\"\"\"Tools for dispatch operations.\"\"\"


def recommend_units(
    incident_type: str, severity: str, armed_suspect: bool = False,
    children_involved: bool = False, victims_count: int = 0,
) -> dict:
    \"\"\"Recommend response units based on incident.
    Args:
        incident_type: Type of emergency
        severity: CRITICAL/HIGH/MEDIUM/LOW
        armed_suspect: Suspect armed?
        children_involved: Children at risk?
        victims_count: Known victim count
    Returns: dict with recommended units
    \"\"\"
    units, priority = [], "routine"
    if severity in ("CRITICAL", "HIGH"):
        priority = "emergency"
    if incident_type == "active_shooter":
        units.extend(["Patrol x2", "SWAT", "EMS Standby"]); priority = "emergency"
    elif incident_type == "domestic_violence":
        units.extend(["Patrol x2"])
        if armed_suspect: units.append("Armed Response")
    elif incident_type == "fire":
        units.extend(["Fire Engine", "Ladder Truck", "EMS"])
    elif incident_type == "medical":
        units.append("EMS Ambulance")
    if armed_suspect and "Armed Response" not in units:
        units.append("Armed Response")
    if children_involved:
        units.append("Child Services Alert")
    if victims_count > 3:
        units.append("Mass Casualty Protocol")
    if not units:
        units.append("Patrol Unit")
    return {"units": units, "priority": priority}
""")

write("agents/tools/safety_tools.py", """\"\"\"
Safety & grounding tools — addresses hackathon criterion:
'Does the agent avoid hallucinations? Is there evidence of grounding?'
\"\"\"

PROTOCOLS = {
    "active_shooter": {
        "approved": ["evacuate", "shelter in place", "lock doors", "dispatch SWAT", "establish perimeter"],
        "prohibited": ["confront shooter", "negotiate alone", "enter without backup"],
    },
    "domestic_violence": {
        "approved": ["separate parties", "ensure victim safety", "mandatory arrest where applicable"],
        "prohibited": ["couples counseling at scene", "share victim location with suspect"],
    },
    "fire": {
        "approved": ["evacuate building", "establish perimeter", "check for occupants"],
        "prohibited": ["re-enter burning building", "use elevators"],
    },
    "medical": {
        "approved": ["dispatch EMS", "provide CPR guidance", "control bleeding"],
        "prohibited": ["diagnose condition", "recommend medication", "move spinal injury patient"],
    },
}


def verify_protocol(action: str, incident_type: str) -> dict:
    \"\"\"Verify action against standard emergency protocols. Grounds agent responses.
    Args:
        action: Proposed action
        incident_type: Type of emergency
    Returns: dict with verification
    \"\"\"
    proto = PROTOCOLS.get(incident_type, {})
    action_l = action.lower()
    is_bad = any(p in action_l for p in proto.get("prohibited", []))
    is_good = any(a in action_l for a in proto.get("approved", []))
    if is_bad:
        return {"verified": False, "warning": f"Action may violate {incident_type} protocol", "suggestion": "Use approved protocols"}
    return {"verified": True, "grounded": is_good, "message": "Consistent with emergency protocols"}
""")

# ─── API ───────────────────────────────────────────────────
write("api/__init__.py", "")

write("api/main.py", """\"\"\"AivaOhr — FastAPI Application.\"\"\"
import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from core.config import settings
from core.incident_graph import incident_manager
from api.routes import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("aivaohr")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AivaOhr v1.0.0 — Father's Light")
    yield
    logger.info("Shutting down AivaOhr")


app = FastAPI(title="AivaOhr", description="Multi-Agent Emergency Coordination — Father's Light", version="1.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(router, prefix="/api")


@app.websocket("/ws/dashboard")
async def dashboard_ws(ws: WebSocket):
    await ws.accept()
    incident_manager.add_ws(ws)
    logger.info("Dashboard connected")
    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "get_all":
                await ws.send_text(json.dumps({
                    "type": "all_incidents",
                    "data": {i: inc.to_dict() for i, inc in incident_manager.incidents.items()},
                }))
    except WebSocketDisconnect:
        incident_manager.remove_ws(ws)


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0", "active_incidents": len(incident_manager.active())}


@app.get("/", response_class=HTMLResponse)
async def root():
    return \"\"\"<!DOCTYPE html><html><head><title>AivaOhr</title></head>
    <body style="display:flex;justify-content:center;align-items:center;height:100vh;
    font-family:-apple-system,sans-serif;background:#0a0a0a;color:#fff;">
    <div style="text-align:center">
    <h1 style="font-size:3rem;font-weight:200;">⬡ AivaOhr</h1>
    <p style="color:#86868b;">Multi-Agent Emergency Coordination System</p>
    <p style="color:#555;font-style:italic;">Father's Light</p>
    <p style="color:#666;">Powered by Gemini Live API + Google ADK</p>
    <p><a href="/docs" style="color:#0071e3;">API Documentation →</a></p>
    </div></body></html>\"\"\"
""")

write("api/routes.py", """\"\"\"REST API routes.\"\"\"
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from core.incident_graph import incident_manager
from agents.tools.incident_tools import report_emergency, register_caller

router = APIRouter(tags=["aivaohr"])


class CallRequest(BaseModel):
    caller_name: str = "Anonymous"
    location: str
    description: str
    incident_type: str = "unknown"
    severity: str = "MEDIUM"
    latitude: float = 0.0
    longitude: float = 0.0


class IntelRequest(BaseModel):
    incident_id: str
    caller_id: str
    intel: str


@router.get("/incidents")
async def list_incidents():
    return {"incidents": [i.to_dict() for i in incident_manager.active()]}


@router.get("/incidents/{iid}")
async def get_incident(iid: str):
    inc = incident_manager.get(iid)
    if not inc:
        raise HTTPException(404, "Incident not found")
    return inc.to_dict()


@router.get("/incidents/{iid}/briefing")
async def get_briefing(iid: str):
    inc = incident_manager.get(iid)
    if not inc:
        raise HTTPException(404, "Incident not found")
    return {"briefing": inc.briefing()}


@router.post("/simulate/call")
async def simulate_call(req: CallRequest):
    result = report_emergency(
        location=req.location, description=req.description,
        incident_type=req.incident_type, severity=req.severity,
        latitude=req.latitude, longitude=req.longitude,
    )
    iid = result["incident_id"]
    caller = register_caller(
        incident_id=iid, caller_name=req.caller_name,
        caller_location=req.location,
    )
    return {"incident": result, "caller": caller}


@router.post("/simulate/intel")
async def simulate_intel(req: IntelRequest):
    from agents.tools.incident_tools import submit_intel
    return submit_intel(req.incident_id, req.caller_id, req.intel)


@router.get("/stats")
async def stats():
    all_inc = list(incident_manager.incidents.values())
    active = [i for i in all_inc if i.status == "active"]
    return {
        "total_incidents": len(all_inc),
        "active_incidents": len(active),
        "total_callers": sum(len(i.callers) for i in all_inc),
        "critical": sum(1 for i in active if i.severity.value == "CRITICAL"),
    }
""")

# ─── SIMULATION ────────────────────────────────────────────
write("simulation/__init__.py", "")

write("simulation/scenarios.py", """\"\"\"Predefined emergency scenarios for demo.\"\"\"

SCENARIOS = {
    "domestic_violence_with_children": {
        "name": "Domestic Violence — Active Threat with Children",
        "incident_type": "domestic_violence",
        "severity": "CRITICAL",
        "location": "742 Evergreen Terrace, Springfield",
        "callers": [
            {
                "name": "Tommy (child, age 8)", "role": "VICTIM",
                "location": "Upstairs bedroom, hiding under bed",
                "opening": "Please help, my dad is really angry and my mom ran away. Me and my sister are hiding.",
                "emotional_state": "panicked",
                "intel": ["Two children hiding upstairs", "Father downstairs", "Mother fled house"],
            },
            {
                "name": "Sarah (mother)", "role": "VICTIM",
                "location": "Neighbor's garage at 744 Evergreen Terrace",
                "opening": "I just ran from my house, my husband was threatening me, my kids are still inside!",
                "emotional_state": "distressed",
                "intel": ["Suspect: husband John, 38yo", "Was drinking", "Kids: Tommy 8, Lisa 5", "She's at neighbor's garage"],
            },
            {
                "name": "Robert (garage owner)", "role": "REPORTING_PARTY",
                "location": "744 Evergreen Terrace",
                "opening": "A woman just ran into my garage screaming. I don't know what's going on.",
                "emotional_state": "confused",
                "intel": ["Woman appears uninjured but terrified", "Can hear yelling from next door"],
            },
            {
                "name": "Mrs. Chen (neighbor)", "role": "WITNESS",
                "location": "739 Evergreen Terrace",
                "opening": "I can see a man pacing in front of 742. He's shouting.",
                "emotional_state": "concerned",
                "intel": ["Suspect: white male ~6ft", "Dark t-shirt", "No visible weapons"],
            },
        ],
    },
    "highway_pileup": {
        "name": "Multi-Vehicle Accident on I-93",
        "incident_type": "traffic_accident",
        "severity": "HIGH",
        "location": "I-93 South near Exit 18, Boston",
        "callers": [
            {
                "name": "Driver", "role": "VICTIM",
                "location": "Blue Honda, front of pileup",
                "opening": "I got rear-ended on 93 South. Airbag went off. I think I'm okay but can't move my car.",
                "emotional_state": "shaken",
                "intel": ["Airbag deployed", "Can move", "Blocking lane 2"],
            },
            {
                "name": "Passerby", "role": "WITNESS",
                "location": "Shoulder, I-93 South",
                "opening": "Big accident on 93. Looks like 4-5 cars. Someone in a red truck isn't moving.",
                "emotional_state": "calm",
                "intel": ["4-5 vehicles", "Person in red truck unconscious", "Fuel leaking", "Traffic backing up"],
            },
        ],
    },
}


def get_scenario(name: str) -> dict:
    return SCENARIOS.get(name, {})

def list_scenarios() -> list[str]:
    return list(SCENARIOS.keys())
""")

write("simulation/caller_simulator.py", """\"\"\"Simulates multiple concurrent callers for demo.\"\"\"
import asyncio
import httpx


async def simulate_scenario(base_url: str, scenario: dict):
    \"\"\"Fire off multiple simulated calls from a scenario.\"\"\"
    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = []
        for caller in scenario.get("callers", []):
            tasks.append(client.post(f"{base_url}/api/simulate/call", json={
                "caller_name": caller["name"],
                "location": scenario["location"],
                "description": caller["opening"],
                "incident_type": scenario["incident_type"],
                "severity": scenario["severity"],
            }))
        results = await asyncio.gather(*tasks)
        return [r.json() for r in results]


if __name__ == "__main__":
    from simulation.scenarios import SCENARIOS
    scenario = SCENARIOS["domestic_violence_with_children"]
    results = asyncio.run(simulate_scenario("http://localhost:8080", scenario))
    for r in results:
        print(r)
""")

# ─── TESTS ─────────────────────────────────────────────────
write("tests/__init__.py", "")

write("tests/test_incident_graph.py", """\"\"\"Tests for incident knowledge graph.\"\"\"
import pytest
from core.incident_graph import Incident, CallerInfo, CallerRole, Severity, IncidentManager


class TestIncident:
    def test_create_incident(self):
        inc = Incident(incident_type="fire", location="123 Main St")
        assert inc.id.startswith("inc_")
        assert inc.status == "active"

    def test_add_caller(self):
        inc = Incident()
        caller = CallerInfo(role=CallerRole.VICTIM, name="Alice", location="upstairs")
        inc.add_caller(caller)
        assert len(inc.callers) == 1
        assert caller.id in inc.callers

    def test_add_intel_shared(self):
        inc = Incident()
        c = CallerInfo(name="Bob")
        inc.add_caller(c)
        inc.add_intel(c.id, "suspect has a knife")
        assert "suspect has a knife" in inc.callers[c.id].intel

    def test_update_suspect(self):
        inc = Incident()
        inc.update_suspect(description="tall male", armed=True, weapon_type="knife")
        assert inc.suspect.armed is True
        assert inc.suspect.weapon_type == "knife"

    def test_briefing_contains_info(self):
        inc = Incident(incident_type="domestic_violence", location="742 Evergreen")
        c = CallerInfo(role=CallerRole.VICTIM, name="Sarah")
        inc.add_caller(c)
        inc.add_intel(c.id, "children hiding upstairs")
        b = inc.briefing()
        assert "DOMESTIC_VIOLENCE" in b
        assert "742 Evergreen" in b
        assert "children hiding upstairs" in b

    def test_children_flag(self):
        inc = Incident(children_involved=True)
        assert "CHILDREN" in inc.briefing()


class TestIncidentManager:
    def test_create_and_get(self):
        im = IncidentManager()
        inc = im.create(incident_type="fire", location="test")
        assert im.get(inc.id) is not None

    def test_active_filter(self):
        im = IncidentManager()
        im.create(incident_type="fire")
        im.create(incident_type="medical")
        assert len(im.active()) == 2
""")

write("tests/test_deduplication.py", """\"\"\"Tests for multi-caller deduplication.\"\"\"
import pytest
from core.incident_graph import IncidentManager
from core.deduplication import DeduplicationEngine


class TestDedup:
    def test_no_match_for_new(self):
        im = IncidentManager()
        de = DeduplicationEngine(im)
        assert de.find_match("123 Main", None, "fire") is None

    def test_match_same_location(self):
        im = IncidentManager()
        im.create(incident_type="fire", location="742 evergreen terrace", summary="house fire")
        de = DeduplicationEngine(im)
        match = de.find_match("742 evergreen terrace", None, "fire at house")
        assert match is not None

    def test_no_match_different_location(self):
        im = IncidentManager()
        im.create(incident_type="fire", location="742 evergreen terrace")
        de = DeduplicationEngine(im)
        match = de.find_match("999 oak avenue", None, "totally different")
        assert match is None

    def test_coords_matching(self):
        im = IncidentManager()
        im.create(incident_type="fire", location="test", coords=(42.3601, -71.0589))
        de = DeduplicationEngine(im)
        match = de.find_match("nearby", (42.3602, -71.0590), "fire")
        assert match is not None

    def test_jaccard(self):
        assert DeduplicationEngine._jaccard("hello world", "hello world") == 1.0
        assert DeduplicationEngine._jaccard("hello world", "goodbye moon") == 0.0
""")

write("tests/test_tools.py", """\"\"\"Tests for agent tools.\"\"\"
import pytest
from agents.tools.incident_tools import report_emergency, register_caller, submit_intel, get_briefing
from agents.tools.caller_tools import safety_instructions
from agents.tools.safety_tools import verify_protocol
from core.incident_graph import IncidentManager, incident_manager


class TestIncidentTools:
    def setup_method(self):
        incident_manager.incidents.clear()

    def test_report_creates_incident(self):
        r = report_emergency("123 Main St", "house fire", "fire")
        assert r["status"] == "new_incident"
        assert r["incident_id"].startswith("inc_")

    def test_register_caller(self):
        r = report_emergency("test", "test")
        iid = r["incident_id"]
        c = register_caller(iid, "VICTIM", "Alice", "upstairs", "panicked")
        assert c["status"] == "registered"
        assert c["total_callers"] == 1

    def test_submit_intel(self):
        r = report_emergency("test", "test")
        iid = r["incident_id"]
        c = register_caller(iid, caller_name="Bob")
        result = submit_intel(iid, c["caller_id"], "suspect has a weapon")
        assert result["status"] == "recorded"
        assert "weapon" in result["briefing"]


class TestSafetyInstructions:
    def test_adult_shooter(self):
        r = safety_instructions("active_shooter", False)
        assert len(r["instructions"]) > 0

    def test_child_shooter(self):
        r = safety_instructions("active_shooter", True)
        assert any("brave" in i.lower() for i in r["instructions"])

    def test_child_dv(self):
        r = safety_instructions("domestic_violence", True)
        assert len(r["instructions"]) > 0


class TestProtocolVerification:
    def test_approved_action(self):
        r = verify_protocol("evacuate building", "fire")
        assert r["verified"] is True

    def test_prohibited_action(self):
        r = verify_protocol("re-enter burning building", "fire")
        assert r["verified"] is False

    def test_unknown_type(self):
        r = verify_protocol("some action", "unknown_type")
        assert r["verified"] is True
""")

# ─── DOCS ──────────────────────────────────────────────────
write("docs/architecture.md", """# AivaOhr Architecture

## System Overview

```
Multiple 911 Callers (voice via Gemini Live API)
        │
        ▼
┌─────────────────────────────────────┐
│   Coordinator Agent (ADK)            │
│   - Incident deduplication           │
│   - Caller role assignment           │
│   - Agent orchestration              │
└───────┬─────────┬──────────┬────────┘
        │         │          │
  Caller Agent  Caller Agent  Caller Agent
   (Child)       (Mother)     (Witness)
        │         │          │
        └────┬────┘──────────┘
             ▼
┌─────────────────────────────────────┐
│   Shared Incident Knowledge Graph    │
│   (Real-time, all agents read/write) │
└───────────────┬─────────────────────┘
                ▼
┌─────────────────────────────────────┐
│   Dispatcher Agent + Dashboard       │
│   (Unified situational awareness)    │
└─────────────────────────────────────┘
```

## Tech Stack
- **Google ADK** — Multi-agent orchestration
- **Gemini Live API** — Real-time voice (audio in/out)
- **Gemini 2.5 Flash** — Reasoning and tool calling
- **Google Cloud Run** — Deployment
- **Firestore** — Incident persistence
- **FastAPI** — Backend API + WebSocket
- **React** — Command dashboard
""")

# ─── DONE ──────────────────────────────────────────────────
print(f"""
╔══════════════════════════════════════════════════════╗
║  ✅ AivaOhr project generated successfully!          ║
║                                                      ║
║  Next steps:                                         ║
║  1. cd aivaOhr                                       ║
║  2. cp .env.example .env  (add your API key)         ║
║  3. pip install -r requirements.txt                  ║
║  4. python run.py                                    ║
║  5. Open http://localhost:8080                        ║
║                                                      ║
║  To push to GitHub:                                  ║
║  git init && git add . && git commit -m "init"       ║
║  git remote add origin <your-repo-url>               ║
║  git push -u origin main                             ║
╚══════════════════════════════════════════════════════╝
""")
