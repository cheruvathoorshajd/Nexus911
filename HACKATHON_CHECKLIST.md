# HACKATHON CHECKLIST — Nexus911 vs. Gemini Live Agent Challenge

> **Reference this file before every implementation decision.**
> Last updated: 2026-03-15 | Deadline: **2026-03-16 5:00 PM PT (8:00 PM EDT)**

---

## Section 1: DEADLINE & TIMELINE

| Event | Date/Time |
|---|---|
| Submission Opens | Feb 16, 2026, 10:00 AM PT |
| Cloud Credits Request Deadline | ~~Mar 13, 2026, 12:00 PM PT~~ (PASSED) |
| **SUBMISSION DEADLINE** | **Mar 16, 2026, 5:00 PM PT / 8:00 PM EDT** |
| Judging Begins | Mar 17, 2026, 9:00 AM PT |
| Judging Ends | Apr 3, 2026, 11:45 PM PT |
| Winners Announced | Apr 22-24, 2026 at Google Cloud NEXT 2026 |

**Post-submission rules:**
- NOTHING can be modified after submission deadline
- Video must be publicly visible on YouTube/Vimeo BEFORE submitting
- Repo must be PUBLIC with working README BEFORE submitting
- All team members must be added to Devpost project BEFORE submitting

---

## Section 2: CATEGORY ALIGNMENT

### Category: **Live Agents** (real-time audio/vision interaction)

| Mandatory Requirement | How Nexus911 Satisfies | Status |
|---|---|---|
| Real-time audio interaction | Gemini Live API full-duplex voice via `voice_session_manager.py` | ✅ |
| Handle natural interruptions / barge-in | ADK `LiveRequestQueue` + streaming in `voice_session_manager.py:start_streaming()` | ✅ |
| Distinct persona/voice | 6 role-specific agent personas in `agents/caller_agent/agent.py` (CHILD uses gentle language, OFFICIAL uses tactical terminology) | ✅ |
| Live and context-aware (not turn-based) | Full-duplex WebSocket streaming, shared Knowledge Graph updated mid-conversation | ✅ |
| Uses Gemini Live API or ADK | Both — `google.adk.agents.Agent` + `gemini-2.5-flash-preview-native-audio-dialog` model | ✅ |
| Hosted on Google Cloud | Cloud Run deployment via `cloudbuild.yaml` + `Dockerfile` | ⚠️ NEEDS ACTUAL DEPLOYMENT |

### Gaps:
- [ ] **Must actually deploy to Cloud Run before submission** — config exists but deployment proof is needed
- [ ] Live API voice streaming has not been tested end-to-end with a real caller

---

## Section 3: MANDATORY REQUIREMENTS AUDIT

### 1. Uses a Gemini model
**Status: ✅ MET**
- Voice agents: `gemini-2.5-flash-preview-native-audio-dialog` — `agent.py:25`, `agents/caller_agent/agent.py:78`, `agents/coordinator/agent.py:34`
- NLI verification: `gemini-2.0-flash` — `verification/nli_engine.py:21`, `verification/contradiction.py:26`
- Config: `core/config.py:14` (`GEMINI_MODEL`), `core/config.py:26` (`VERIFICATION_MODEL`)

### 2. Built with Google GenAI SDK or ADK
**Status: ✅ MET**
- ADK: `from google.adk.agents import Agent` — `agent.py:7`, `agents/caller_agent/agent.py:5`, `agents/coordinator/agent.py:5`
- ADK Runner + LiveRequestQueue: `services/voice_session_manager.py:15-17`
- GenAI SDK: `from google import genai` — `verification/nli_engine.py:14`, `verification/contradiction.py:16`
- Dependencies: `google-adk>=1.2.0`, `google-genai>=1.10.0` in `requirements.txt`

### 3. Uses at least one Google Cloud service
**Status: ⚠️ PARTIAL**
- Cloud Run deployment configured: `cloudbuild.yaml`, `Dockerfile`
- Firestore dependency in `requirements.txt:5` (`google-cloud-firestore>=2.19.0`)
- Secret Manager referenced in `cloudbuild.yaml:35`
- **GAP:** Firestore is NOT actually used in code (in-memory only). Cloud Run has NOT been deployed yet.
- **FIX:** Deploy to Cloud Run = satisfies this. Alternatively, add actual Firestore reads/writes.

### 4. Backend hosted on Google Cloud
**Status: ⚠️ PARTIAL**
- `cloudbuild.yaml` and `Dockerfile` are production-ready
- **GAP:** No evidence of actual deployment. Need screen recording of Cloud Run console OR live URL.
- **FIX:** Run `gcloud builds submit --config cloudbuild.yaml` and capture proof.

### 5. Project is NEW (created during contest period)
**Status: ✅ MET**
- Earliest file timestamps: March 6, 2026 (`.gitignore`)
- Contest period: Feb 16 - Mar 16, 2026
- All files created within contest window

### 6. Public code repository with spin-up instructions in README
**Status: ⚠️ PARTIAL**
- README has detailed Quick Start section with setup commands: `README.md:113-148`
- **GAP:** No public GitHub remote configured. README references `.env.example` but file doesn't exist.
- **FIX:**
  - [ ] Create GitHub repo and push all code
  - [ ] Create `.env.example` file (without real API key)
  - [ ] Verify README clone-to-run instructions work

### 7. English language support
**Status: ✅ MET**
- All prompts, instructions, and UI in English
- Noted as English-only in `README.md:423`

### 8. Third-party integrations disclosed
**Status: ⚠️ PARTIAL**
- `# Code Citations.md` exists but content unclear
- `requirements.txt` lists all dependencies
- **GAP:** No explicit third-party disclosure section in README or submission text
- **FIX:** Add a "Third-Party Libraries" section or ensure Code Citations.md is complete

---

## Section 4: SUBMISSION DELIVERABLES CHECKLIST

### 1. Text description (summary, features, tech stack, learnings)
- [x] Summary: `README.md:1-5` (autonomous multi-agent 911 dispatch)
- [x] Features: `README.md:86-95` (5 capabilities table)
- [x] Tech stack: `README.md:98-110`
- [ ] **Learnings — MISSING.** Devpost submission needs a "what you learned" section. Draft this.

### 2. Public code repo URL with README spin-up instructions
- [x] README has Quick Start: `README.md:113-148`
- [x] README has Cloud Run deployment: `README.md:150-164`
- [x] README has test instructions: `README.md:166-170`
- [ ] **Public repo — NOT YET CREATED.** Must push to GitHub and make public.
- [ ] **`.env.example` — MISSING.** README references it at line 137 but file doesn't exist.

### 3. Proof of Google Cloud deployment
- [x] `cloudbuild.yaml` configured for Cloud Build + Cloud Run
- [x] `Dockerfile` with multi-stage build
- [ ] **Actual deployment — NOT DONE.** Need either:
  - Screen recording of app running on Cloud Run console, OR
  - Live Cloud Run URL showing the app working
- [ ] **Capture deployment proof (screenshot or screen recording)**

### 4. Architecture diagram
- [x] ASCII architecture diagram in `README.md:31-82` (VerifyLayer pipeline)
- [x] ASCII pipeline diagram in `README.md:273-306` (per-fact verification)
- [ ] **Visual architecture diagram — MISSING.** Rules require a visual showing:
  - User/frontend interaction
  - Gemini model placement
  - Backend infrastructure on Google Cloud
  - Data flow connections between all components
- [ ] **Create a proper visual diagram** (draw.io, Excalidraw, Figma — export as PNG)

### 5. Demo video (max 4 minutes)
- [ ] **DEMO VIDEO — NOT CREATED.** This is the highest-priority missing item. Requirements:
  - Max 4 minutes (only first 4 min evaluated)
  - Must show actual software functioning (NO mockups)
  - Must include pitch explaining problem and solution value
  - Upload to YouTube or Vimeo (publicly visible)
  - Must be in English or have English subtitles
- [ ] **Record and upload demo video**

---

## Section 5: JUDGING CRITERIA SCORECARD

### Innovation & Multimodal UX — 40% weight (MOST IMPORTANT)

| What Judges Look For | What We Have | Score Estimate |
|---|---|---|
| Breaks "text box paradigm" | Full-duplex voice agents via Gemini Live API — no text input needed | Strong |
| Natural, immersive interaction | Barge-in support, role-adapted conversation pacing | Strong |
| "See, Hear, Speak" seamlessly | Voice (hear/speak) fully implemented. Vision not used. | Moderate |
| Category-specific: interruption handling | LiveRequestQueue with barge-in in `voice_session_manager.py` | Strong |
| Category-specific: distinct persona/voice | 6 role personas (CHILD, VICTIM, WITNESS, etc.) in `agents/caller_agent/agent.py` | Strong |
| Live and context-aware vs turn-based | Shared Knowledge Graph updated mid-call; cross-agent intel sharing | Very Strong |

**What's missing:**
- [ ] No vision/camera input (only audio) — could be a gap vs. competitors using multimodal
- [ ] No evidence of tested barge-in behavior in demo

**Score potential: 4-5/5** if demo shows real voice interaction with role switching

### Technical Implementation & Agent Architecture — 30% weight

| What Judges Look For | What We Have | File Evidence |
|---|---|---|
| GenAI SDK/ADK usage | ADK agents + GenAI SDK for NLI | `agent.py`, `verification/nli_engine.py` |
| Cloud Run/Vertex/Firestore hosting | Cloud Run configured (not yet deployed) | `cloudbuild.yaml`, `Dockerfile` |
| Backend robustness | FastAPI + WebSocket + async throughout | `api/main.py`, `api/voice_websocket.py` |
| Sound agent logic | Multi-agent with role-specific behavior, tool calling | `agents/caller_agent/agent.py`, `agents/tools/` |
| Error handling | Fail-open verification, timeout fallbacks, exception handling | `verification/hooks.py`, `agents/tools/incident_tools.py:74-86` |
| Edge case management | Pending verification fallback, cache eviction, dedup thresholds | `verification/cache.py`, `core/deduplication.py` |
| **Hallucination avoidance** | **VerifyLayer — NLI + contradiction detection + confidence scoring** | `verification/verifylayer.py` (entire module) |
| **Grounding evidence** | Fact provenance per-caller, confidence scores, contradiction explanations | `verification/penalization.py`, `verification/hooks.py:140-179` |

**What's missing:**
- [ ] Cloud Run not actually deployed — loses points on "hosted on Google Cloud"
- [ ] No Firestore integration (in-memory only) — misses a Google Cloud service

**Score potential: 4-5/5** — VerifyLayer is a huge differentiator for anti-hallucination

### Demo & Presentation — 30% weight

| What Judges Look For | What We Have | Status |
|---|---|---|
| Clear problem definition | 240M calls, 25% vacancy, hallucination risk | ✅ `README.md:15-23` |
| Solution narrative | 5-layer pipeline, VerifyLayer as key innovation | ✅ `README.md:27-82` |
| Clear architecture diagram | ASCII diagrams in README | ⚠️ Need visual diagram |
| Cloud deployment proof | cloudbuild.yaml exists | ❌ Need actual deployment |
| Actual software working | Frontend dashboard + API works locally | ⚠️ Need video showing it |

**What's missing (ALL CRITICAL):**
- [ ] Demo video — doesn't exist yet
- [ ] Visual architecture diagram — doesn't exist yet
- [ ] Cloud deployment proof — not yet deployed

**Score potential: 1-2/5 without video and diagram, 4-5/5 with them**

---

## Section 6: BONUS POINTS OPPORTUNITIES

### Blog/Podcast/Video Content — +0.6 pts max
**Status: ❌ NOT STARTED**
- Must be published on a public platform (Medium, Dev.to, YouTube, etc.)
- Must mention building with Google AI and Cloud
- Must include **#GeminiLiveAgentChallenge** hashtag
- Must state it was created for the hackathon
- **Action:** Write a quick Medium/Dev.to post about building VerifyLayer. Worth 10% of max possible score.
- [ ] Publish blog post with required disclosures

### Automated Cloud Deployment via Scripts/IaC — +0.2 pts
**Status: ✅ LIKELY MET**
- `cloudbuild.yaml` IS infrastructure-as-code for Cloud Build + Cloud Run
- `Dockerfile` IS automated container build
- Included in public repo
- **Just need to verify judges consider cloudbuild.yaml as qualifying IaC**

### Google Developer Group (GDG) Membership — +0.2 pts
**Status: ❌ NOT DONE**
- Sign up at developers.google.com/community/gdg
- Provide public profile link in submission
- **Action:** Takes 2 minutes. Free points.
- [ ] Sign up for GDG and get profile link

---

## Section 7: DISQUALIFICATION RISKS

| Risk | Our Status | Action Needed |
|---|---|---|
| Project not newly created during contest | ✅ SAFE — all files dated Mar 6-15, 2026 (within Feb 16 - Mar 16 window) | None |
| Pre-existing work | ✅ SAFE — no evidence of prior project | None |
| IP violations / third-party content | ⚠️ CHECK — `# Code Citations.md` exists but completeness unclear | Review and ensure all third-party code is attributed |
| Google Cloud Acceptable Use Policy | ✅ SAFE — emergency dispatch AI is legitimate use case | None |
| Missing required submission components | ❌ AT RISK — no demo video, no visual architecture diagram, no cloud deployment proof | **Must complete all three before deadline** |
| API key in .env committed to repo | ⚠️ RISK — `.env` contains real `GOOGLE_API_KEY` | **Remove .env from public repo, use .env.example instead** |
| Offensive/inappropriate content | ✅ SAFE — emergency dispatch scenarios are appropriate | None |
| Repo not public | ❌ AT RISK — no GitHub remote configured | Push to public GitHub repo |
| Third-party advertising/logos | ✅ SAFE — no third-party branding | None |

**CRITICAL DISQUALIFICATION RISK:** Submitting without a demo video, architecture diagram, or cloud deployment proof will cause a **Stage 1 fail** (pass/fail gate before scoring even begins). These are not optional.

---

## Section 8: PRIORITY ACTION ITEMS

Ordered by impact on judging score. Do these in order — stop when you run out of time.

### TIER 1: WITHOUT THESE YOU CANNOT WIN (Stage 1 pass/fail gate)

| # | Action | Affects | Weight | Est. Time |
|---|---|---|---|---|
| 1 | **Record and upload demo video to YouTube** | Demo & Presentation | 30% | 2-3 hrs |
| | - Show dashboard with live incident updates | | | |
| | - Show simulation running (multi-caller → dedup → verification) | | | |
| | - Pitch: problem (240M calls, hallucination risk) → solution (VerifyLayer) | | | |
| | - Keep under 4 minutes | | | |
| 2 | **Deploy to Cloud Run and capture proof** | Technical Implementation | 30% | 30 min |
| | - Run `gcloud builds submit --config cloudbuild.yaml` | | | |
| | - Screen-record the Cloud Run console showing deployment | | | |
| | - Test the live URL works | | | |
| 3 | **Create visual architecture diagram** | Demo & Presentation | 30% | 30 min |
| | - Must show: Frontend → Gemini agents → VerifyLayer → Knowledge Graph → Cloud Run | | | |
| | - Use draw.io, Excalidraw, or Figma | | | |
| | - Export as PNG, include in README and submission | | | |
| 4 | **Push to public GitHub repo** | Mandatory requirement | Pass/Fail | 15 min |
| | - Create repo, push all code | | | |
| | - Ensure `.env` is in `.gitignore` (real API key!) | | | |
| | - Create `.env.example` with placeholder values | | | |

### TIER 2: HIGH IMPACT ON SCORE (Innovation & Technical = 70% of scoring)

| # | Action | Affects | Weight | Est. Time |
|---|---|---|---|---|
| 5 | **Build simulation runner for demo** | Innovation (40%) + Demo (30%) | 70% combined | 1-2 hrs |
| | - `POST /api/simulate/scenario` endpoint | | | |
| | - Plays full scenario: staggered callers → intel → verification → dedup → dispatch | | | |
| | - Dashboard shows everything in real-time | | | |
| | - **This is what you demo in the video** | | | |
| 6 | **Add cross-caller contradictions to scenarios** | Innovation (40%) | 40% | 30 min |
| | - Without contradictions, VerifyLayer's best feature is invisible | | | |
| | - Add conflicting facts between callers (weapon type, red light blame, etc.) | | | |
| 7 | **Test voice pipeline end-to-end once** | Technical (30%) | 30% | 30 min |
| | - If it works: include in demo video (massive differentiator) | | | |
| | - If it breaks: demo simulation mode only (still strong) | | | |

### TIER 3: BONUS POINTS (free points, low effort)

| # | Action | Affects | Points | Est. Time |
|---|---|---|---|---|
| 8 | **Sign up for GDG** | Bonus | +0.2 pts | 2 min |
| 9 | **Publish quick blog post** | Bonus | +0.6 pts | 30-60 min |
| | - "Building an Anti-Hallucination Layer for Autonomous 911 AI" | | | |
| | - Include #GeminiLiveAgentChallenge and hackathon disclosure | | | |
| 10 | **Verify cloudbuild.yaml counts as automated deployment** | Bonus | +0.2 pts | Already done |

### TIER 4: POLISH (only if time remains)

| # | Action | Affects | Weight | Est. Time |
|---|---|---|---|---|
| 11 | Clean up dispatcher agent (remove or wire in) | Technical (30%) | Minor | 15 min |
| 12 | Write Devpost "what you learned" section | Demo (30%) | Minor | 15 min |
| 13 | Review `# Code Citations.md` for completeness | Disqualification risk | Safety | 10 min |
| 14 | Create `.env.example` file | Mandatory requirement | Pass/Fail | 5 min |

---

## QUICK REFERENCE: Files That Prove Compliance

| Requirement | Primary Evidence File |
|---|---|
| Gemini model usage | `agent.py:25`, `verification/nli_engine.py:21` |
| ADK usage | `agent.py:7`, `services/voice_session_manager.py:15` |
| GenAI SDK usage | `verification/nli_engine.py:14` |
| Google Cloud service | `cloudbuild.yaml` (Cloud Run + Cloud Build + Secret Manager) |
| Live API / voice streaming | `services/voice_session_manager.py`, `api/voice_websocket.py` |
| Anti-hallucination | `verification/verifylayer.py` (entire module) |
| Multi-agent architecture | `agents/caller_agent/agent.py`, `core/incident_graph.py` |
| Real-time dashboard | `frontend/src/App.tsx`, `api/main.py:51-67` |
| Deduplication | `core/deduplication.py` |
| Role-specific agents | `agents/caller_agent/agent.py:10-70` |
| Fail-open safety | `verification/hooks.py:22-112`, `agents/tools/incident_tools.py:70-86` |
| Automated deployment (IaC) | `cloudbuild.yaml`, `Dockerfile` |
| Tests | `tests/test_verifylayer.py`, `tests/test_deduplication.py`, `tests/test_incident_graph.py` |

---

## THE BRUTAL TRUTH

**What will win this hackathon:**
1. Innovation score (40%) — VerifyLayer is genuinely novel. No other 911 AI has real-time hallucination verification. This is your strongest card.
2. Demo video (30%) — Without a compelling 4-min video showing the system working, none of the code matters. Judges won't read your source files.
3. Technical depth (30%) — ADK + GenAI SDK + Cloud Run + multi-agent + verification pipeline. This is deep. But it needs to be deployed and provable.

**What will lose this hackathon:**
- Submitting without a demo video = **automatic Stage 1 fail**
- Submitting without cloud deployment proof = **automatic Stage 1 fail**
- Submitting without an architecture diagram = **significant score reduction**
- Not having contradictions in the demo = VerifyLayer looks like dead weight

**Time allocation for remaining hours:**
- 3 hrs: Build simulation runner + add contradictions + test it
- 2 hrs: Record and edit demo video
- 1 hr: Deploy to Cloud Run + capture proof
- 30 min: Create architecture diagram
- 30 min: Push to GitHub + create .env.example
- 30 min: Blog post + GDG signup (bonus points)
- 30 min: Buffer for problems

**Total: ~8 hours of focused work. You have ~18 hours. This is doable.**