# Nexus911

**Autonomous multi-agent 911 dispatch with real-time hallucination verification.**

> When three people call 911 about the same car accident, today's system treats them as three separate emergencies. Nexus911 deploys a dedicated AI voice agent for each caller, cross-references their accounts in real time, verifies every fact before it enters the dispatch record, and merges them into a single enriched incident — in under 20 seconds.

[![Gemini Live Agent Challenge](https://img.shields.io/badge/Gemini_Live_Agent_Challenge-2026-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://geminiliveagentchallenge.devpost.com/)
[![Built with Gemini](https://img.shields.io/badge/Built_with-Gemini_Live_API-8E75B2?style=for-the-badge&logo=google&logoColor=white)]()
[![Google ADK](https://img.shields.io/badge/Google_ADK-Agent_Framework-34A853?style=for-the-badge&logo=google&logoColor=white)]()
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)]()
[![Live on Cloud Run](https://img.shields.io/badge/Live-Cloud_Run-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white)](https://nexus911-888823131112.us-central1.run.app)

**Live Demo:** [https://nexus911-888823131112.us-central1.run.app](https://nexus911-888823131112.us-central1.run.app)

---

## The Problem

240 million 911 calls hit US dispatch centers every year. **25–30% of dispatcher positions sit vacant.** When a major incident triggers a flood of simultaneous calls, each caller reaches a different dispatcher — if they reach one at all. The child in the backseat, the witness across the street, and the injured driver each provide a fragment of the truth. These fragments live in separate call records that may never be correlated until long after responders arrive.

As AI enters emergency dispatch — with Axon, RapidSOS, Motorola, and startups like Hyper and Aurelian all deploying AI tools — a new risk emerges: **large language models hallucinate.** A hallucinated address sends responders to the wrong location. A fabricated medical instruction causes harm. No deployed emergency AI system has a dedicated verification layer for LLM outputs.

No existing system deploys autonomous AI agents that simultaneously handle live emergency calls, share intelligence across them, and verify what the AI extracts before it enters the dispatch pipeline.

**Nexus911 does.**

---

## How It Works

Nexus911 operates as a **five-layer pipeline**:

```
 Caller A (Child)     Caller B (Witness)     Caller C (Victim)
       │                     │                      │
       ▼                     ▼                      ▼
  ┌─────────┐          ┌─────────┐           ┌─────────┐
  │ Agent 1 │          │ Agent 2 │           │ Agent 3 │
  │ Gemini  │          │ Gemini  │           │ Gemini  │
  │ Live API│          │ Live API│           │ Live API│
  └────┬────┘          └────┬────┘           └────┬────┘
       │                    │                     │
       └────────────┬───────┴─────────────────────┘
                    │
                    ▼
 ┌──────────────────────────────────────────────────────┐
 │                    VERIFY LAYER                       │
 │                                                       │
 │  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐ │
 │  │ NLI Engine  │  │ Contradiction│  │ Penalization  │ │
 │  │ (Gemini 2.5 │  │  Detector    │  │   Engine      │ │
 │  │  Flash)     │  │ (Cross-Call) │  │ (Confidence)  │ │
 │  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘ │
 │         └────────────┬───┴──────────────────┘         │
 │                      │                                │
 │              ┌───────▼────────┐                       │
 │              │  LRU Cache     │                       │
 │              │ (Thread-Safe)  │                       │
 │              └────────────────┘                       │
 └──────────────────────┬───────────────────────────────┘
                        │
                        ▼
          ┌──────────────────┐
          │ KNOWLEDGE GRAPH  │◄──── Agents subscribe to
          │ Verified facts   │      verified updates and
          │ with provenance  │      use them mid-conversation
          └────────┬─────────┘
                   │
                   ▼
          ┌──────────────────┐
          │  DEDUPLICATION   │
          │  Geo + Temporal  │
          │  + Semantic      │
          │  Clustering      │
          └────────┬─────────┘
                   │
                   ▼
            ┌─────────────┐
            │  DISPATCH    │
            │  Enriched    │
            │  incident    │
            │  package     │
            └─────────────┘
```

---

## Five Capabilities

| Capability | What it does |
|---|---|
| **Autonomous emergency voice agents** | Each caller gets a dedicated Gemini-powered agent that conducts the full 911 interview via the Gemini Live API with full-duplex audio and barge-in support |
| **Role-aware conversation** | Agents adapt vocabulary, pacing, and question strategy based on caller classification (child, victim, witness, bystander) |
| **Cross-call intel sharing** | When Agent 2 extracts an address, Agent 1 can confirm it with their caller in real time via the shared Knowledge Graph |
| **Hallucination verification (VerifyLayer)** | Every extracted fact is validated via NLI before it enters the knowledge graph — with cross-call contradiction detection and confidence scoring |
| **Incident deduplication** | Geo + temporal + semantic clustering merges multiple calls about the same event into one enriched dispatch record |
| **Text simulation fallback** | When voice sessions fail, the system falls back to text-based simulation that still exercises the full pipeline (VerifyLayer, dedup, dispatch) — ensuring demo reliability |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Voice | Gemini Live API — native full-duplex audio dialog with barge-in |
| Agent Orchestration | Google ADK (Agent Development Kit) — multi-agent coordination |
| LLM | Gemini 2.5 Flash (voice agents · NLI verification) |
| Backend | FastAPI + WebSocket |
| Verification | VerifyLayer — NLI engine, contradiction detector, penalization engine, async LRU cache |
| Knowledge Graph | In-memory incident graph with real-time WebSocket push (designed for Firestore) |
| Deduplication | Haversine geo-distance + temporal window + text-overlap semantic scoring |
| Deployment | Google Cloud Run via Cloud Build |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- Gemini API key ([Get one here](https://aistudio.google.com/apikey))

### Setup

```bash
# Clone
git clone https://github.com/<your-username>/nexus911.git
cd nexus911

# Virtual environment
python -m venv .venv
source .venv/bin/activate    # Linux/Mac
# .venv\Scripts\activate     # Windows

# Install backend dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..

# Configure
cp .env.example .env
# Edit .env — add your GOOGLE_API_KEY
```

### Running Locally

Start both the backend and frontend:

```bash
# Terminal 1 — Backend (FastAPI)
python run.py
# Or: uvicorn api.main:app --host 0.0.0.0 --port 8080 --reload

# Terminal 2 — Frontend (React + Vite)
cd frontend
npm run dev
```

- **Backend API**: http://localhost:8080
- **Frontend Dashboard**: http://localhost:5173 (proxies API calls to :8080)
- **API docs**: http://localhost:8080/docs
- **Health check**: http://localhost:8080/health
- **Dashboard WebSocket**: ws://localhost:8080/ws/dashboard
- **Voice WebSocket**: ws://localhost:8080/ws/voice

> **Windows users**: Use `.venv\Scripts\activate` instead of `source .venv/bin/activate`.

### Deploy to Cloud Run

```bash
gcloud run deploy nexus911 \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_API_KEY=$GOOGLE_API_KEY"
```

Or use Cloud Build for CI/CD:

```bash
gcloud builds submit --config cloudbuild.yaml
```

### Run Tests

```bash
python -m pytest tests/ -v
```

---

## Project Structure

```
nexus911/
├── agents/
│   ├── caller_agent/
│   │   └── agent.py                # Per-caller voice agent factory (role-specific)
│   ├── coordinator/
│   │   └── agent.py                # Root coordinator — routes calls, deduplicates incidents
│   ├── dispatcher_agent/
│   │   └── agent.py                # Dispatcher-facing coordination agent
│   └── tools/
│       ├── caller_tools.py         # Safety instructions, emotional support tools
│       ├── dispatch_tools.py       # Response unit recommendation engine
│       ├── incident_tools.py       # Intel submission with VerifyLayer hooks
│       └── safety_tools.py         # Caller safety guidance tools
│
├── api/
│   ├── main.py                     # FastAPI app + WebSocket endpoints
│   ├── routes.py                   # REST: incidents, simulation, stats
│   ├── simulation_routes.py        # REST: scenario simulation start/stop/status
│   └── voice_websocket.py          # Browser ↔ Agent voice streaming bridge
│
├── core/
│   ├── config.py                   # Pydantic settings (env-driven configuration)
│   ├── deduplication.py            # Geo + temporal + semantic incident clustering
│   └── incident_graph.py           # Real-time shared knowledge graph + WebSocket push
│
├── frontend/
│   └── src/
│       ├── App.tsx                  # React dashboard (Vite + TypeScript)
│       ├── App.css
│       ├── index.css
│       └── main.tsx
│
├── services/
│   └── voice_session_manager.py    # Gemini Live API session lifecycle manager
│
├── simulation/
│   ├── scenarios.py                # Predefined multi-caller demo scenarios
│   ├── simulator_agent.py          # Gemini Live caller persona agent + audio bridge
│   ├── orchestrator.py             # Multi-caller scenario runner with staggered timing
│   └── text_fallback.py            # Reliable text-based simulation fallback
│
├── tests/
│   ├── test_verifylayer.py         # VerifyLayer pipeline tests
│   ├── test_deduplication.py       # Deduplication engine tests
│   └── test_incident_graph.py      # Knowledge graph tests
│
├── verification/                   # ═══ VERIFYLAYER MODULE ═══
│   ├── verifylayer.py              # Pipeline orchestrator (cache → NLI → contradiction → scoring)
│   ├── nli_engine.py               # Gemini 2.5 Flash NLI: entailment / contradiction / neutral
│   ├── contradiction.py            # Cross-call pairwise contradiction detection
│   ├── penalization.py             # Confidence scoring (NLI + caller credibility + corroboration)
│   ├── cache.py                    # Thread-safe async LRU cache with TTL
│   ├── models.py                   # Pydantic models: ExtractedFact, NLIResult, FactConfidence, etc.
│   ├── hooks.py                    # Non-blocking integration hooks (fail-open for 911 safety)
│   └── middleware.py               # FastAPI verification REST endpoints
│
├── agent.py                        # Root ADK agent definition (Gemini 2.5 Flash native audio)
├── run.py                          # Server entrypoint
├── cloudbuild.yaml                 # Google Cloud Build CI/CD pipeline
├── Dockerfile                      # Container image for Cloud Run
├── requirements.txt
├── .env.example
├── LICENSE                         # MIT
└── README.md
```

---

## API Endpoints

### REST

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check with active incident count |
| `GET` | `/api/incidents` | List all active incidents |
| `GET` | `/api/incidents/{id}` | Get single incident detail |
| `GET` | `/api/incidents/{id}/briefing` | Get human-readable incident briefing |
| `POST` | `/api/simulate/call` | Simulate a single 911 call |
| `GET` | `/api/stats` | System statistics |
| `GET` | `/api/voice/sessions` | Get all active voice sessions |
| `GET` | `/api/simulation/scenarios` | List available simulation scenarios |
| `GET` | `/api/simulation/scenarios/{name}` | Get details for a specific scenario |
| `POST` | `/api/simulation/start` | Start a multi-caller scenario simulation |
| `GET` | `/api/simulation/status` | Get current simulation status |
| `POST` | `/api/simulation/stop` | Stop the running simulation |
| `POST` | `/api/verify/utterance` | Verify a caller utterance via VerifyLayer |
| `GET` | `/api/verify/facts/{incident_id}` | Get all verified facts for an incident |
| `GET` | `/api/verify/intel/{incident_id}/{agent_id}` | Get agent-specific verified facts |
| `GET` | `/api/verify/cache/stats` | VerifyLayer cache performance metrics |

### WebSocket

| Endpoint | Description |
|---|---|
| `ws://host/ws/voice` | Browser ↔ Agent bidirectional voice streaming |
| `ws://host/ws/dashboard` | Real-time incident updates for the dashboard |
| `ws://host/ws/simulation` | Real-time simulation events (transcripts, tool calls, status) |

---

## VerifyLayer: Hallucination Verification Middleware

VerifyLayer is the critical safety layer that distinguishes Nexus911 from every other AI dispatch system. It operates as middleware between the conversation engine and the knowledge graph, ensuring no unverified fact enters the shared intelligence pool.

### Pipeline (per fact)

```
Caller utterance
    │
    ▼
┌──────────────────┐
│  Fact Extraction  │  Gemini 2.5 Flash extracts discrete verifiable claims
└────────┬─────────┘
         │
    ┌────▼─────┐
    │  Cache?   │───── HIT ────▶ Return instantly (<5ms)
    └────┬─────┘
         │ MISS
         ▼
┌──────────────────┐
│  NLI Verification │  Entailment / Contradiction / Neutral scoring
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────┐
│  Cross-Call Contradiction Check   │  Pairwise comparison against all
│                                   │  facts from OTHER callers on the
│                                   │  same incident
└────────┬─────────────────────────┘
         │
         ▼
┌──────────────────┐
│  Penalization     │  Composite confidence score:
│  Engine           │  NLI score × 0.4 + Caller credibility × 0.3
│                   │  + Corroboration bonus × 0.2 - Contradiction penalty × 0.1
└────────┬─────────┘
         │
         ▼
   Cache result → Return VerificationResult
```

### Confidence Scoring

The penalization engine weights facts by four factors:

| Factor | Weight | Description |
|---|---|---|
| **NLI entailment score** | 40% | How directly the transcript supports the extracted claim |
| **Caller credibility** | 30% | Role-based weight: official (0.95) > victim (0.75) > witness (0.65) > bystander (0.50) > child (0.35) |
| **Cross-caller corroboration** | 20% | Bonus when independent callers report the same fact (up to +30%) |
| **Contradiction penalty** | 10% | Penalty when conflicting claims exist from other callers (up to -50%) |

### What VerifyLayer Prevents

| Failure Mode | Without VerifyLayer | With VerifyLayer |
|---|---|---|
| Hallucinated address | Agent fabricates "123 Oak St" when caller said "near the oak tree" → responders go to wrong location | NLI detects non-entailment → fact flagged, agent re-asks |
| Cross-call contamination | Detail from Call A leaks into Call B's context → confused dispatch record | Fact provenance tracked per-agent, contamination blocked |
| Contradictory facts merged | "Blue Honda" and "Red Toyota" both enter dispatch as ground truth | Contradiction detected → penalization scores both, flags for review |
| Confidence inflation | Every extracted fact treated as equally reliable | Penalization engine weights by caller role, corroboration, and entailment |

### Latency Budget

VerifyLayer is designed for a **200ms latency budget** per verification call:

| Component | Target |
|---|---|
| Cache lookup (hit) | <5ms |
| NLI inference | ~80–120ms |
| Penalization scoring | ~10–20ms |
| Knowledge graph write | ~20–40ms |

Facts that cannot be verified within budget are written as `pending_verification` and verified asynchronously — the conversation never stalls.

### Integration: Fail-Open for 911 Safety

VerifyLayer hooks are **non-blocking**. Intelligence always enters the knowledge graph immediately (fail-open), with verification running in the background. If verification fails or times out, the intel flows through unverified with appropriate uncertainty markers. In a 911 context, blocking a potentially life-saving piece of information is worse than passing it through unverified.

---

## Demo Scenario: Highway Accident

> **3 callers. 3 agents. 1 verified incident. 20 seconds.**

| Time | Caller | Agent Action | VerifyLayer |
|---|---|---|---|
| T+0s | Child: *"We crashed and mommy isn't moving"* | Agent 1 → role: CHILD, extracts: vehicle_accident, unresponsive_adult | Entailed ✅ confidence: 0.87 |
| T+8s | Witness: *"Sedan hit an 18-wheeler at Route 9 and Elm"* | Agent 2 → role: WITNESS, extracts: location, vehicles | Entailed ✅ "truck" ↔ "18-wheeler" consistent ✅ |
| T+12s | — | Agent 1 asks child: *"Are you near Route 9 and Elm?"* | Cross-call intel used. Child confirms → confidence: 0.97 |
| T+15s | Victim: *"I was in my blue Camry, truck ran the red light"* | Agent 3 → role: VICTIM, extracts: vehicle detail, cause | Entailed ✅ "blue Camry" ↔ "sedan" consistent ✅ |
| T+18s | — | Deduplication: 3 calls merged into 1 incident | Geo ✅ Temporal ✅ Semantic (0.94) ✅ |
| T+20s | — | **Dispatch: 2 ambulances, 1 fire, 1 police** | Full confidence-scored intelligence package sent |

### Dispatch Package (T+20s)

```
Location:   Route 9 and Elm Street          (confidence: 0.97, 3 sources)
Vehicles:   Blue Camry sedan + 18-wheeler    (confidence: 0.93, corroborated)
Injuries:   1 unresponsive adult in Camry    (confidence: 0.87, 1 source)
            1 mobile victim in second vehicle
Cause:      Red light violation              (confidence: 0.62, single source — unverified)
Dispatch:   2 ambulances, 1 fire unit, 1 police unit
```

---

## What Makes This Different

Nexus911 is **not** an AI assistant for human dispatchers. Every competitor in the market — Axon ($1.4B in acquisitions), RapidSOS (22,000+ agencies), Motorola (60% market share) — builds AI that sits alongside a human. Nexus911 builds AI that handles the call directly, with a verification layer that makes autonomous operation defensible.

The key architectural insight: **the verification layer is not optional safety theater — it's what makes the entire system possible.** Without VerifyLayer, autonomous AI agents handling 911 calls is irresponsible. With it, every fact is checked against the source transcript, contradictions between callers are caught before they contaminate the record, and confidence scores give dispatchers transparent reliability signals.

### Competitive Landscape

| Capability | Nexus911 | Axon 911 | RapidSOS HARMONY | Leidos/NVIDIA C2AI | Motorola |
|---|---|---|---|---|---|
| Autonomous emergency voice agents | ✅ Full | ❌ Non-emergency only | ❌ Non-emergency only | ❌ Backend only | ❌ Assistive only |
| Multi-agent concurrent operation | ✅ 3+ simultaneous | ❌ Single-call | ❌ Single copilot | ✅ Multi-agent (backend) | ❌ Single-call |
| Cross-call intel sharing (real-time) | ✅ Via knowledge graph | ❌ | ⚠️ Cross-agency (post-call) | ⚠️ Cross-sensor (not cross-caller) | ❌ |
| Role-aware conversation adaptation | ✅ Child / Victim / Witness | ❌ | ❌ | ❌ | ❌ |
| Incident deduplication (semantic) | ✅ Geo + Temporal + Semantic | ⚠️ Basic related-call detection | ⚠️ Device/sensor data fusion | ❌ | ❌ |
| Hallucination verification | ✅ NLI + cross-call contradiction | ❌ | ❌ | ❌ | ❌ |
| Knowledge graph architecture | ✅ | ❌ Flat records | ❌ LLM + RAG | ❌ | ❌ |

---

## Configuration

All configuration is via environment variables (`.env` file) or `core/config.py`:

| Variable | Default | Description |
|---|---|---|
| `GOOGLE_API_KEY` | — | Gemini API key (required) |
| `GOOGLE_CLOUD_PROJECT` | — | GCP project ID |
| `GOOGLE_CLOUD_LOCATION` | `us-central1` | GCP region |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Voice agent model |
| `VERIFICATION_MODEL` | `gemini-2.5-flash` | NLI verification model |
| `GOOGLE_GENAI_USE_VERTEXAI` | `false` | Use Vertex AI instead of API key auth |
| `FIRESTORE_DATABASE` | `(default)` | Firestore database ID |
| `VERIFYLAYER_ENABLED` | `true` | Enable/disable verification pipeline |
| `VERIFYLAYER_LATENCY_BUDGET_MS` | `200` | Max verification latency before async fallback |
| `VERIFYLAYER_CACHE_SIZE` | `1024` | LRU cache capacity |
| `VERIFYLAYER_CACHE_TTL` | `300.0` | Cache entry time-to-live (seconds) |
| `DEDUP_SIMILARITY_THRESHOLD` | `0.55` | Minimum score to merge incidents |
| `INCIDENT_RADIUS_METERS` | `200.0` | Geo-clustering radius |
| `MAX_CONCURRENT_CALLERS` | `10` | Maximum simultaneous voice sessions |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8080` | Server port |

---

## Known Limitations

Transparency about what this system can and cannot do:

- **This is a prototype.** Nexus911 has not been tested with real 911 callers, real dispatch systems, or real emergency outcomes. The demo uses simulated callers.
- **Latency under real load is unproven.** The 200ms verification budget is a design target, not a measured result. The `pending_verification` fallback path is the mitigation.
- **Role classification is heuristic, not benchmarked.** The child/victim/witness adaptation has not been evaluated against ground-truth labeled data.
- **The system assumes English.** While Gemini supports multilingual audio, the NLI verification pipeline and prompt templates are English-only.
- **In-memory state.** The knowledge graph and verification cache use in-memory Python data structures. In production, these would be backed by Firestore and Memorystore (Redis) respectively. The architecture is designed for this migration.

---

## Category

**Live Agents** — Real-time voice interaction using Gemini Live API + ADK

Built for the [Gemini Live Agent Challenge](https://geminiliveagentchallenge.devpost.com/) | Google Cloud Next 2026

---

## References

### Emergency Dispatch AI
- Hyper, Inc. — Voice AI for non-emergency 911 ($6.3M funding, July 2025)
- Aurelian AI — Autonomous dispatch agents for non-emergency triage ($14M Series A, August 2025)
- Axon/Prepared — AI-powered 911 communications (acquired ~$800M, September 2025)
- Axon/Carbyne — Cloud-native 911 call handling infrastructure (acquired $625M, November 2025)
- RapidSOS HARMONY — AI copilot for 911 (1B+ emergencies dataset)
- Leidos/NVIDIA C2AI — Multi-agent AI for disaster response command and control
- Motorola Solutions — Dispatcher Assist, Responder Assist, Narrative Assist (January 2026)
- Corti AI — Cardiac arrest detection from 911 audio (95% accuracy, 13M+ calls)

### Market Data
- 2025 Pulse of 9-1-1 Survey (1,379 respondents): 86% comfort with AI, 4% adoption, 25–30% vacancy rate
- MarketsandMarkets: Next Gen Emergency Response System market $2.4B (2023) → $3.3B (2028)

### Incident Deduplication & NLP
- PMC 8782712 (2022): BERT-Att-BiLSTM with 3W attributes for event clustering
- UBC Data Science: LaBSE embeddings + KMeans for 911 narrative categorization

---

## License

MIT — see [LICENSE](LICENSE)

---

*Every second counts. Nexus911 makes every second smarter.*
