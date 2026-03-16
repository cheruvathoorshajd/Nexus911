# Nexus911 — Claude Code Project Context

## What This Is
Multi-agent autonomous 911 dispatch system with real-time hallucination verification.
Built for the Gemini Live Agent Challenge hackathon.
Category: **Live Agents**

## DEADLINE: March 16, 2026 @ 5:00 PM Pacific Time

## Tech Stack
- Python 3.11+, FastAPI, WebSockets
- Google ADK (Agent Development Kit) for multi-agent orchestration
- Gemini 2.5 Flash (voice agents) via Gemini Live API
- Gemini 2.5 Flash (NLI verification via VerifyLayer)
- google-genai SDK (NOT google-cloud-aiplatform)
- React + TypeScript frontend (Vite)
- Deployment: Google Cloud Run via cloudbuild.yaml

## Key Architecture
- Voice agents: `agent.py` (root ADK agent), `services/voice_session_manager.py`
- VerifyLayer pipeline: `verification/` module (verifylayer.py -> nli_engine.py -> contradiction.py -> penalization.py -> cache.py)
- Knowledge graph: `core/incident_graph.py`
- Deduplication: `core/deduplication.py`
- API: `api/main.py`, `api/routes.py`, `api/voice_websocket.py`, `api/simulation_routes.py`
- Tools: `agents/tools/incident_tools.py`, `caller_tools.py`, `dispatch_tools.py`, `safety_tools.py`
- Frontend: `frontend/src/App.tsx`
- Simulation: `simulation/simulator_agent.py`, `simulation/orchestrator.py`, `simulation/text_fallback.py`, `simulation/scenarios.py`

## Google Cloud Credits ($100 available)
- Billing account: "Marketing - Gemini Live Agent Challenge"
- Credits cover Vertex AI API calls and Cloud Run deployment
- To use credits for Gemini API calls, switch from AI Studio key to Vertex AI:
```python
  # Instead of: genai.Client(api_key=self._api_key)
  # Use: genai.Client(vertexai=True, project="PROJECT_ID", location="us-central1")
```
- This also satisfies the "at least one Google Cloud service" requirement

## Hackathon Mandatory Requirements
1. Uses Gemini model (2.5 Flash for voice, 2.0 Flash for NLI)
2. Built with ADK (agent.py uses google.adk.agents.Agent)
3. Must use at least one Google Cloud service (Cloud Run deployment needed, or switch to Vertex AI)
4. Backend must be hosted on Google Cloud (deploy via cloudbuild.yaml)
5. Project is new (built during contest period Feb 16 - Mar 16, 2026)
6. Public code repo with spin-up instructions in README

## Submission Deliverables (all required)
1. Text description (features, tech, learnings)
2. Public GitHub repo URL with README spin-up instructions
3. Proof of Google Cloud deployment (screen recording OR code file link)
4. Architecture diagram (Gemini -> backend -> frontend -> DB flow)
5. Demo video (<4 min, real software working, pitch + demo, YouTube/Vimeo)

## Bonus Points
- Blog/video about build process (+0.6 pts) — must say "created for the Gemini Live Agent Challenge hackathon", use #GeminiLiveAgentChallenge
- Automated cloud deployment via cloudbuild.yaml (+0.2 pts) — already exists
- GDG membership link (+0.2 pts)

## Judging Criteria
- Innovation & Multimodal UX (40%): barge-in support, distinct persona, live/context-aware, "beyond text"
- Technical Implementation (30%): GenAI SDK/ADK usage, Cloud hosting, error handling, anti-hallucination
- Demo & Presentation (30%): problem/solution story, architecture diagram, cloud proof, live demo

## Known Issues to Fix
- CallerRole enum mismatch: verification/models.py uses lowercase, core/incident_graph.py uses uppercase — penalization falls through to UNKNOWN (0.50 credibility)
- Corroboration matching in verifylayer.py L137-141 is exact string match — needs semantic similarity
- No periodic cache cleanup (cleanup_expired never called)
- First fact for any incident always gets NLI score 0.0 (empty premise)
- API key is on free tier with zero quota — need to switch to Vertex AI with cloud credits

## Dev Environment
- Windows, VS Code, .venv inside nexus911 folder
- ADK must be run from D:\AviaOhr (parent directory)
- Run server: python run.py (or uvicorn api.main:app --host 0.0.0.0 --port 8080)
- Run tests: pytest tests/ -v

## Simulation System
- Voice mode: `POST /api/simulation/start {"scenario": "highway_accident", "mode": "voice"}`
  - Uses Gemini Live API agent-to-agent (simulator persona <-> Nexus911 operator)
  - Requires working API quota
- Text mode: `POST /api/simulation/start {"scenario": "highway_accident", "mode": "text"}`
  - Direct tool calls through real pipeline (dedup, VerifyLayer, dispatch)
  - Always works, no API dependency for core flow
- Available scenarios: domestic_violence_with_children, highway_accident, active_shooter
- Fallback: voice mode auto-falls back to text if all voice sessions fail

## Conventions
- Logging: logging.getLogger("nexus911.xxx")
- Enums: str Enum pattern
- Module singletons at bottom of files
- google-genai SDK (not google-cloud-aiplatform)
- Fail-open design: intel always enters knowledge graph immediately, verification runs async in background
- 911 protocol: NENA/APCO standard — location first, then callback, nature, weapons, injuries, suspect, dispatch
