# Code Citations & Third-Party Disclosures

> Required for Gemini Live Agent Challenge hackathon submission.
> All third-party libraries, APIs, and references used in Nexus911.

## Google APIs & SDKs

| Library | Version | License | Usage |
|---|---|---|---|
| [google-adk](https://github.com/google/adk-python) | >=1.2.0 | Apache 2.0 | Multi-agent orchestration framework (Agent, Runner, LiveRequestQueue) |
| [google-genai](https://github.com/googleapis/python-genai) | >=1.10.0 | Apache 2.0 | Gemini API client for NLI verification and contradiction detection |
| [google-cloud-firestore](https://github.com/googleapis/python-firestore) | >=2.19.0 | Apache 2.0 | Firestore client (dependency, designed for production migration) |

## Python Backend

| Library | Version | License | Usage |
|---|---|---|---|
| [FastAPI](https://github.com/tiangolo/fastapi) | >=0.115.0 | MIT | REST API and WebSocket server |
| [uvicorn](https://github.com/encode/uvicorn) | >=0.30.0 | BSD-3-Clause | ASGI server |
| [websockets](https://github.com/python-websockets/websockets) | >=14.0 | BSD-3-Clause | WebSocket protocol implementation |
| [Pydantic](https://github.com/pydantic/pydantic) | >=2.8.0 | MIT | Data validation and settings management |
| [pydantic-settings](https://github.com/pydantic/pydantic-settings) | >=2.0.0 | MIT | Environment-based configuration |
| [httpx](https://github.com/encode/httpx) | >=0.27.0 | BSD-3-Clause | Async HTTP client |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | >=1.0.0 | BSD-3-Clause | .env file loading |
| [python-multipart](https://github.com/Kludex/python-multipart) | >=0.0.9 | Apache 2.0 | Multipart form data parsing |

## Frontend

| Library | Version | License | Usage |
|---|---|---|---|
| [React](https://github.com/facebook/react) | ^19.2.0 | MIT | UI framework |
| [React DOM](https://github.com/facebook/react) | ^19.2.0 | MIT | DOM rendering |
| [React Router](https://github.com/remix-run/react-router) | ^7.13.1 | MIT | Client-side routing (/ → Landing, /dashboard → Dashboard) |
| [Framer Motion](https://github.com/framer/motion) | ^12.37.0 | MIT | Animation library for dashboard UI |
| [Lucide React](https://github.com/lucide-icons/lucide) | ^0.468.0 | ISC | Icon library |
| [Tailwind CSS](https://github.com/tailwindlabs/tailwindcss) | ^4.1.3 | MIT | Utility-first CSS framework |
| [Vite](https://github.com/vitejs/vite) | ^6.3.0 | MIT | Frontend build tool and dev server |
| [TypeScript](https://github.com/microsoft/TypeScript) | ~5.9.3 | Apache 2.0 | Type-safe JavaScript |

## Google Cloud Services

| Service | Usage |
|---|---|
| Google Cloud Run | Production container hosting |
| Google Cloud Build | CI/CD pipeline (cloudbuild.yaml) |
| Google Secret Manager | API key storage |
| Gemini 2.5 Flash (Live API) | Voice agent model — full-duplex native audio |
| Gemini 2.5 Flash (Text) | NLI verification engine |

## Algorithms & Techniques

| Technique | Source | Usage in Nexus911 |
|---|---|---|
| Haversine formula | Standard geodesic distance formula | Geo-distance calculation in deduplication engine (`core/deduplication.py`) |
| Natural Language Inference (NLI) | Standard NLP task (entailment/contradiction/neutral) | VerifyLayer fact verification via Gemini (`verification/nli_engine.py`) |
| LRU Cache with TTL | Standard caching pattern | Verification result caching (`verification/cache.py`) |

## Fonts

| Font | License | Usage |
|---|---|---|
| [Inter](https://github.com/rsms/inter) | OFL 1.1 | Body text (via Google Fonts CDN) |
| [Space Grotesk](https://github.com/nicholasgross/Space-Grotesk) | OFL 1.1 | Headings (via Google Fonts CDN) |
| [JetBrains Mono](https://github.com/JetBrains/JetBrainsMono) | OFL 1.1 | Monospace text (via Google Fonts CDN) |

## AI-Assisted Development

This project was developed with assistance from AI coding tools (GitHub Copilot / Claude) for code generation, debugging, and documentation. All generated code was reviewed, tested, and modified by the developer.

## No Pre-Existing Code

Nexus911 was built entirely during the Gemini Live Agent Challenge contest period (February 16 – March 16, 2026). No pre-existing codebase, template, or starter kit was used.
