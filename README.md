# AviaOhr

# ⬡ AivaOhr — *Father's Light*

### Multi-Agent Emergency Coordination System

> When a child whispers "help" from under a bed, their mother is fleeing to a neighbor's garage, and four people are dialing 911 simultaneously — one dispatcher cannot handle it all. AivaOhr can.

**AivaOhr** is a multi-agent AI system that autonomously handles multiple 911 callers in the same emergency simultaneously, shares intelligence between agents in real-time, and presents a unified operational picture to dispatchers.

Built with **Google Gemini Live API** + **Agent Development Kit (ADK)** + **Google Cloud**.

---

## The Problem

When a crisis unfolds, multiple people call 911 about the same incident. Each call ties up a human dispatcher. They don't share information between calls. A child hiding upstairs doesn't know that police already have their mother's description of the suspect — because two different dispatchers are handling those calls independently.

**The numbers are stark:**
- 8,000+ PSAPs (911 centers) in the US
- 86% experience high call volumes weekly
- 72% report up to 10 staff vacancies
- Average dispatcher handles 80 calls/day
- Non-emergency calls consume 60%+ of capacity

During a multi-caller crisis, dispatchers are overwhelmed, intelligence is siloed, and response coordination degrades.

## The Solution

AivaOhr deploys **multiple AI agents simultaneously** — one per caller — that:

1. **Talk** to each caller via Gemini Live API (real-time voice, natural interruptions)
2. **Adapt** their conversation to the caller's role (child gets calm, simple language; witness gets targeted questions)
3. **Share** every piece of intelligence to a common incident knowledge graph instantly
4. **Deduplicate** — automatically recognize that 4 callers are reporting the same incident
5. **Brief** the dispatcher with a unified situational picture via a real-time command dashboard

### What Makes This Different

| Capability | Traditional 911 | Prepared/Axon | AivaOhr |
|---|---|---|---|
| AI transcription | No | Yes | Yes |
| Autonomous caller handling | No | No — human required | **Yes — AI agents talk to callers** |
| Multi-agent coordination | No | No | **Yes — agents share intel in real-time** |
| Auto incident deduplication | No | Partial | **Yes — geo + temporal + semantic clustering** |
| Role-aware conversations | Human judgment | Human judgment | **Yes — child/victim/witness get different agents** |
| Scales without more humans | No | No | **Yes — spin up more agents** |
| Protocol-grounded responses | Manual | Manual | **Yes — verified against emergency protocols** |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   Multiple 911 Callers                        │
│          (Voice via Gemini Live API + WebSocket)              │
└───────┬──────────┬──────────┬──────────┬────────────────────┘
        │          │          │          │
        ▼          ▼          ▼          ▼
┌──────────────────────────────────────────────────────────────┐
│              Coordinator Agent (Google ADK)                    │
│    • Incident deduplication (geo + temporal + semantic)        │
│    • Caller role assignment (VICTIM/WITNESS/CHILD/BYSTANDER) │
│    • Agent orchestration & lifecycle                          │
└───────┬──────────┬──────────┬──────────┬────────────────────┘
        │          │          │          │
        ▼          ▼          ▼          ▼
   ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌──────────┐
   │ Caller   │ │ Caller   │ │ Caller   │ │ Caller   │
   │ Agent    │ │ Agent    │ │ Agent    │ │ Agent    │
   │ (Child)  │ │ (Mother) │ │ (Witness)│ │(Bystander│
   └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
        │             │            │             │
        └──────┬──────┘────────────┘─────────────┘
               ▼
┌──────────────────────────────────────────────────────────────┐
│           Shared Incident Knowledge Graph                     │
│    • Real-time read/write by all agents                       │
│    • Suspect info, caller locations, timeline                 │
│    • Stored in Firestore for persistence                      │
└──────────────────────────┬───────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────┐
│        Dispatcher Agent + Command Dashboard (React)           │
│    • Unified situational awareness                            │
│    • Live incident map with caller positions                  │
│    • Agent activity stream                                    │
│    • Recommended response units                               │
│    • Protocol-verified actions (grounding layer)              │
└──────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Component | Technology |
|---|---|
| Multi-Agent Orchestration | **Google ADK** (Agent Development Kit) |
| Real-Time Voice | **Gemini Live API** (audio in/out, interruption handling) |
| Reasoning & Tool Calling | **Gemini 2.5 Flash** |
| Backend | **FastAPI** + WebSocket |
| Deployment | **Google Cloud Run** |
| Database | **Google Firestore** |
| Dashboard | **React** |
| CI/CD | **Cloud Build** (automated deployment) |

---

## Quick Start

### Prerequisites
- Python 3.11+
- Google Cloud account
- Gemini API key ([get one here](https://aistudio.google.com/apikey))

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/aivaOhr.git
cd aivaOhr

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env — add your GOOGLE_API_KEY and GOOGLE_CLOUD_PROJECT
```

### Run Locally

```bash
python run.py
# Server starts at http://localhost:8080
# API docs at http://localhost:8080/docs
```

### Deploy to Google Cloud Run

```bash
# Automated (uses cloudbuild.yaml)
gcloud builds submit

# OR manual
docker build -t gcr.io/YOUR_PROJECT/aivaohr .
docker push gcr.io/YOUR_PROJECT/aivaohr
gcloud run deploy aivaohr --image gcr.io/YOUR_PROJECT/aivaohr --region us-central1 --allow-unauthenticated
```

---

## Demo Scenario

**Domestic Violence with Children** — the scenario that demonstrates all of AivaOhr's capabilities:

1. **Tommy (8 years old)** calls 911 hiding under his bed — Agent speaks in calm, child-appropriate language
2. **Sarah (mother)** calls from a neighbor's garage — Agent extracts suspect description, confirms children's location
3. **Robert (garage owner)** calls confused — Agent tells him the woman is an innocent victim, asks him to keep her safe
4. **Mrs. Chen (neighbor)** calls as a witness — Agent asks what she can see, gets visual description of suspect

All four agents share intelligence in real-time. When Sarah tells her agent the suspect's name and description, Tommy's agent immediately knows. The dispatcher dashboard shows everything on one screen.

### Try the simulation:

```bash
# Start the server
python run.py

# In another terminal, run the scenario
python -m simulation.caller_simulator
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/api/incidents` | List active incidents |
| GET | `/api/incidents/{id}` | Get incident details |
| GET | `/api/incidents/{id}/briefing` | Natural-language briefing |
| POST | `/api/simulate/call` | Simulate a 911 call |
| POST | `/api/simulate/intel` | Submit intelligence |
| GET | `/api/stats` | Dashboard statistics |
| WS | `/ws/dashboard` | Real-time dashboard WebSocket |

---

## Project Structure

```
aivaOhr/
├── agents/
│   ├── coordinator/agent.py      # Root orchestrator — routes, deduplicates
│   ├── caller_agent/agent.py     # Per-caller voice agent factory
│   ├── dispatcher_agent/agent.py # Dispatcher-facing intelligence agent
│   └── tools/
│       ├── incident_tools.py     # Create/update incidents, submit intel
│       ├── caller_tools.py       # Safety instructions (adult/child)
│       ├── dispatch_tools.py     # Unit recommendations
│       └── safety_tools.py       # Protocol verification (grounding)
├── core/
│   ├── config.py                 # Settings via pydantic-settings
│   ├── incident_graph.py         # Shared real-time knowledge graph
│   ├── deduplication.py          # Multi-caller clustering engine
│   └── caller_manager.py         # Active session tracking
├── api/
│   ├── main.py                   # FastAPI app + WebSocket
│   └── routes.py                 # REST endpoints
├── simulation/
│   ├── scenarios.py              # Predefined demo scenarios
│   └── caller_simulator.py       # Multi-caller simulation script
├── tests/                        # Unit + integration tests
├── docs/architecture.md          # Architecture documentation
├── Dockerfile                    # Container for Cloud Run
├── cloudbuild.yaml               # Automated GCP deployment
├── requirements.txt
└── LICENSE                       # MIT
```

---

## Testing

```bash
pytest tests/ -v
```

| Suite | Tests | Coverage |
|---|---|---|
| `test_incident_graph.py` | 8 | Incident creation, callers, intel sharing, briefing, children flag |
| `test_deduplication.py` | 5 | Location matching, coordinate proximity, Jaccard similarity |
| `test_tools.py` | 8 | Emergency reporting, caller registration, safety instructions, protocol verification |

---

## Grounding & Safety

AivaOhr addresses hallucination prevention through multiple layers:

1. **Protocol Verification** — Every recommended action is checked against established emergency protocols (NENA/APCO guidelines)
2. **Intel Attribution** — Every piece of intelligence is tagged with the caller who provided it
3. **No Speculation** — Agents report only confirmed caller statements, never infer
4. **Crisis Routing** — Agents can transfer to human dispatchers when AI judgment is insufficient
5. **Child Safety Priority** — Children always receive age-appropriate communication

---

## The Name

**AivaOhr** (אבא אור) — *Father's Light* in Hebrew. Because in the darkest moments of crisis, this system aims to be a guiding light — coordinating help when people need it most.

---

## Hackathon

Built for the **Gemini Live Agent Challenge** by Google.

*This project was created for the purposes of entering the Gemini Live Agent Challenge hackathon.* #GeminiLiveAgentChallenge

---

## License

MIT — see [LICENSE](LICENSE)

---

## Author

**Dennis Sharon Cheruvathoor Shaj**
- Northeastern University — MS Information Systems
- [LinkedIn](https://linkedin.com) | [GitHub](https://github.com) | [Portfolio](https://portfolio.com)
