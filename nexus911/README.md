# Nexus911

**Multi-Agent Emergency Coordination System powered by Gemini Live API**

> When multiple people call 911 about the same emergency, Nexus911 deploys autonomous AI agents — one per caller — that coordinate in real-time, share intelligence, and present a unified picture to dispatchers.

Built for the [Gemini Live Agent Challenge](https://geminiliveagentchallenge.devpost.com/) #GeminiLiveAgentChallenge

---

## The Problem

When an emergency happens, multiple people call 911 simultaneously — the victim, witnesses, bystanders, neighbors. Each call ties up a human dispatcher. With 86% of 911 centers experiencing high call volumes weekly and 72% reporting staff vacancies, this creates dangerous delays.

Existing AI tools (Prepared/Axon, RapidSOS) make individual dispatchers faster, but they don't solve the fundamental bottleneck: **one human per call**.

## The Solution

Nexus911 deploys **autonomous AI agents** — one per caller — that:

1. **Talk to callers naturally** via Gemini Live API (voice in, voice out)
2. **Adapt to each caller's role** — a child hiding gets a different conversation than a witness across the street
3. **Share intelligence in real-time** — when Agent A learns the suspect went to the backyard, Agent B (talking to the child) immediately knows
4. **Deduplicate incidents automatically** — recognizes that 4 calls from the same block are one incident
5. **Present a unified dashboard** to one human dispatcher overseeing all agents

## Architecture

```
Multiple 911 Callers (voice via Gemini Live API)
        |
        v
+---------------------------------------+
|   Coordinator Agent (ADK)              |
|   - Deduplication engine               |
|   - Caller role assignment             |
+----+----------+----------+------------+
     |          |          |
  Agent A    Agent B    Agent C
  (Child)    (Mother)   (Witness)
     |          |          |
     +----+-----+----------+
          v
  Shared Incident Knowledge Graph
  (Firestore, real-time updates)
          |
          v
  Command Dashboard (React)
  - Live incident map
  - Caller status panels
  - Agent activity stream
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Multi-Agent Framework | Google ADK (Agent Development Kit) |
| Voice Interaction | Gemini Live API |
| LLM | Gemini 2.5 Flash |
| Backend | FastAPI + WebSocket |
| Database | Google Cloud Firestore |
| Deployment | Google Cloud Run |
| Frontend | React |

## Quick Start

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/nexus911.git
cd nexus911

# Virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your GOOGLE_API_KEY

# Run
python run.py
```

Server starts at http://localhost:8080

## Project Structure

```
nexus911/
├── agents/
│   ├── coordinator/agent.py      # Root orchestrator
│   ├── caller_agent/agent.py     # Per-caller voice agent factory
│   ├── dispatcher_agent/agent.py # Dispatcher-facing agent
│   └── tools/                    # Shared tool functions
├── core/
│   ├── incident_graph.py         # Real-time shared knowledge base
│   ├── deduplication.py          # Multi-caller incident clustering
│   └── config.py                 # Configuration
├── api/
│   ├── main.py                   # FastAPI + WebSocket
│   └── routes.py                 # REST endpoints
├── simulation/
│   └── scenarios.py              # Demo scenarios
├── tests/
├── Dockerfile
├── cloudbuild.yaml               # Automated Cloud deployment
└── README.md
```

## Category

**Live Agents** — Real-time voice interaction using Gemini Live API + ADK

## License

MIT
