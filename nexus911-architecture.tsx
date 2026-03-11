import { useState } from "react";

const C = {
  bg: "#06080c",
  card: "#0d1117",
  cardAlt: "#111820",
  border: "#1e2a3a",
  borderHi: "#2d4a6f",
  accent: "#58a6ff",
  green: "#3fb950",
  red: "#f85149",
  yellow: "#d29922",
  orange: "#db6d28",
  purple: "#a371f7",
  cyan: "#39d2c0",
  pink: "#f778ba",
  text: "#e6edf3",
  textSec: "#8b949e",
  textDim: "#484f58",
  white: "#ffffff",
};

export default function ArchDiagram() {
  const [hover, setHover] = useState(null);
  const [view, setView] = useState("full");

  const flowData = [
    { id: "step1", label: "911 Call Received", detail: "Multiple callers dial 911 about the same incident. Voice streams via Gemini Live API WebSocket.", icon: "📞", color: C.cyan },
    { id: "step2", label: "Coordinator Routes", detail: "ADK Coordinator Agent deduplicates by location + keywords. Links to existing incident or creates new one. Assigns caller role.", icon: "🧠", color: C.orange },
    { id: "step3", label: "Caller Agent Assigned", detail: "Role-specific agent spawned (child protocol, victim protocol, witness protocol). Begins natural voice conversation.", icon: "🤖", color: C.accent },
    { id: "step4", label: "Intel Extracted & Shared", detail: "Agent extracts facts via conversation. Submits to shared Incident Knowledge Graph. All other agents see updates instantly.", icon: "🔗", color: C.purple },
    { id: "step5", label: "Verified & Grounded", detail: "Cross-caller verification checks contradictions. Protocol RAG grounds safety instructions. Emotional cascade adjusts priorities.", icon: "✅", color: C.green },
    { id: "step6", label: "Dashboard Updated", detail: "Dispatcher sees unified picture: all callers, suspect info, verified intel, recommended units. One human oversees all agents.", icon: "🖥️", color: C.yellow },
  ];

  return (
    <div style={{ background: C.bg, minHeight: "100vh", fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif", color: C.text, padding: "24px 16px" }}>
      <div style={{ maxWidth: 1000, margin: "0 auto" }}>

        {/* ── HEADER ── */}
        <div style={{ textAlign: "center", marginBottom: 28, position: "relative" }}>
          <div style={{ position: "absolute", top: -20, left: "50%", transform: "translateX(-50%)", width: 400, height: 120, background: `radial-gradient(ellipse, ${C.accent}10 0%, transparent 70%)`, pointerEvents: "none" }} />
          <div style={{ fontSize: "0.65rem", fontWeight: 600, letterSpacing: "0.15em", color: C.accent, textTransform: "uppercase", marginBottom: 6 }}>System Architecture</div>
          <h1 style={{ fontSize: "2.2rem", fontWeight: 800, letterSpacing: "-0.04em", margin: 0, color: C.white }}>
            Nexus<span style={{ color: C.red }}>911</span>
          </h1>
          <p style={{ color: C.textSec, fontSize: "0.82rem", margin: "6px 0 0", maxWidth: 600, marginLeft: "auto", marginRight: "auto", lineHeight: 1.5 }}>
            Multi-Agent Emergency Coordination System
          </p>
          <p style={{ color: C.textDim, fontSize: "0.7rem", margin: "2px 0 0" }}>
            Gemini Live API • Google ADK • Cloud Run • Firestore
          </p>
        </div>

        {/* ── VIEW TOGGLE ── */}
        <div style={{ display: "flex", gap: 4, justifyContent: "center", marginBottom: 20 }}>
          {[["full", "Full Architecture"], ["flow", "Data Flow"], ["novel", "Novelty Map"]].map(([id, label]) => (
            <button key={id} onClick={() => setView(id)} style={{
              padding: "6px 18px", borderRadius: 6, border: `1px solid ${view === id ? C.accent : C.border}`,
              background: view === id ? `${C.accent}18` : C.card, color: view === id ? C.accent : C.textSec,
              fontSize: "0.72rem", fontWeight: 600, cursor: "pointer", fontFamily: "inherit", transition: "all 0.2s",
            }}>{label}</button>
          ))}
        </div>

        {/* ══════════════════════════════════════════════════ */}
        {/* FULL ARCHITECTURE VIEW */}
        {/* ══════════════════════════════════════════════════ */}
        {view === "full" && (
          <div>
            {/* Row 1: Callers */}
            <div style={{ marginBottom: 2 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                <div style={{ width: 3, height: 16, background: C.cyan, borderRadius: 2 }} />
                <span style={{ fontSize: "0.7rem", fontWeight: 700, color: C.cyan, letterSpacing: "0.08em", textTransform: "uppercase" }}>Callers</span>
                <span style={{ fontSize: "0.65rem", color: C.textDim }}>Simultaneous 911 callers via voice</span>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 }}>
                {[
                  { name: "Tommy (8)", role: "CHILD/VICTIM", state: "Panicked", loc: "Hiding under bed", color: C.red, emoji: "👦" },
                  { name: "Sarah", role: "MOTHER/VICTIM", state: "Distressed", loc: "Neighbor's garage", color: C.red, emoji: "👩" },
                  { name: "Robert", role: "REPORTING PARTY", state: "Confused", loc: "His garage", color: C.yellow, emoji: "🧔" },
                  { name: "Mrs. Chen", role: "WITNESS", state: "Concerned", loc: "Across street", color: C.green, emoji: "👵" },
                ].map((c, i) => (
                  <div key={i} style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, padding: "12px 14px", borderLeft: `3px solid ${c.color}` }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                      <span style={{ fontSize: "1.2rem" }}>{c.emoji}</span>
                      <div>
                        <div style={{ fontSize: "0.78rem", fontWeight: 700, color: C.text }}>{c.name}</div>
                        <div style={{ fontSize: "0.6rem", color: c.color, fontWeight: 600 }}>{c.role}</div>
                      </div>
                    </div>
                    <div style={{ fontSize: "0.62rem", color: C.textSec, lineHeight: 1.4 }}>
                      <span style={{ color: C.textDim }}>State:</span> {c.state}<br />
                      <span style={{ color: C.textDim }}>Location:</span> {c.loc}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Connection arrows */}
            <div style={{ display: "flex", justifyContent: "center", padding: "6px 0" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <div style={{ width: 1, height: 20, background: `linear-gradient(${C.cyan}, ${C.accent})` }} />
                <span style={{ fontSize: "0.6rem", color: C.cyan, fontWeight: 600, padding: "2px 8px", background: `${C.cyan}12`, borderRadius: 4, border: `1px solid ${C.cyan}30` }}>🎙️ Gemini Live API — Real-time bidirectional voice (WebSocket)</span>
                <div style={{ width: 1, height: 20, background: `linear-gradient(${C.cyan}, ${C.accent})` }} />
              </div>
            </div>

            {/* Row 2: Agent Layer */}
            <div style={{ marginBottom: 2 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                <div style={{ width: 3, height: 16, background: C.accent, borderRadius: 2 }} />
                <span style={{ fontSize: "0.7rem", fontWeight: 700, color: C.accent, letterSpacing: "0.08em", textTransform: "uppercase" }}>Agent Layer</span>
                <span style={{ fontSize: "0.65rem", color: C.textDim }}>Google ADK Multi-Agent Orchestration</span>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "3fr 2fr", gap: 8 }}>
                {/* Caller Agents */}
                <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, padding: 14 }}>
                  <div style={{ fontSize: "0.7rem", fontWeight: 700, color: C.accent, marginBottom: 10 }}>🤖 Caller Agents (1 per caller)</div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
                    {[
                      { label: "Agent A", desc: "Child protocol — calm, simple language, quiet game", color: C.red },
                      { label: "Agent B", desc: "Victim protocol — safety first, extract suspect info", color: C.red },
                      { label: "Agent C", desc: "Bystander protocol — reassure, relay victim status", color: C.yellow },
                      { label: "Agent D", desc: "Witness protocol — intel priority, descriptions", color: C.green },
                    ].map((a, i) => (
                      <div key={i} style={{ background: C.cardAlt, borderRadius: 6, padding: "8px 10px", borderLeft: `2px solid ${a.color}` }}>
                        <div style={{ fontSize: "0.68rem", fontWeight: 700, color: C.text }}>{a.label}</div>
                        <div style={{ fontSize: "0.58rem", color: C.textSec, lineHeight: 1.3, marginTop: 2 }}>{a.desc}</div>
                      </div>
                    ))}
                  </div>
                </div>
                {/* Coordinator + Dispatcher */}
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  <div style={{ background: C.card, border: `1px solid ${C.orange}40`, borderRadius: 10, padding: 14, flex: 1 }}>
                    <div style={{ fontSize: "0.7rem", fontWeight: 700, color: C.orange, marginBottom: 4 }}>🧠 Coordinator Agent</div>
                    <div style={{ fontSize: "0.6rem", color: C.textSec, lineHeight: 1.5 }}>
                      Routes incoming calls<br />
                      Deduplicates incidents<br />
                      Assigns caller roles<br />
                      Manages agent lifecycle
                    </div>
                  </div>
                  <div style={{ background: C.card, border: `1px solid ${C.yellow}40`, borderRadius: 10, padding: 14 }}>
                    <div style={{ fontSize: "0.7rem", fontWeight: 700, color: C.yellow, marginBottom: 4 }}>👤 Dispatcher Agent</div>
                    <div style={{ fontSize: "0.6rem", color: C.textSec, lineHeight: 1.5 }}>
                      Faces human dispatcher<br />
                      Recommends response units
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Connection */}
            <div style={{ display: "flex", justifyContent: "center", padding: "6px 0" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <div style={{ width: 1, height: 20, background: `linear-gradient(${C.accent}, ${C.purple})` }} />
                <span style={{ fontSize: "0.6rem", color: C.purple, fontWeight: 600, padding: "2px 8px", background: `${C.purple}12`, borderRadius: 4, border: `1px solid ${C.purple}30` }}>🔗 All agents read/write to shared Incident Knowledge Graph</span>
                <div style={{ width: 1, height: 20, background: `linear-gradient(${C.accent}, ${C.purple})` }} />
              </div>
            </div>

            {/* Row 3: Intelligence Layer */}
            <div style={{ marginBottom: 2 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                <div style={{ width: 3, height: 16, background: C.purple, borderRadius: 2 }} />
                <span style={{ fontSize: "0.7rem", fontWeight: 700, color: C.purple, letterSpacing: "0.08em", textTransform: "uppercase" }}>Intelligence Layer</span>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr", gap: 8 }}>
                <div style={{ background: C.card, border: `1px solid ${C.purple}40`, borderRadius: 10, padding: 14 }}>
                  <div style={{ fontSize: "0.7rem", fontWeight: 700, color: C.purple, marginBottom: 6 }}>🔗 Incident Knowledge Graph</div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4, fontSize: "0.6rem", color: C.textSec }}>
                    <div style={{ background: C.cardAlt, borderRadius: 4, padding: "4px 8px" }}>📍 Caller locations</div>
                    <div style={{ background: C.cardAlt, borderRadius: 4, padding: "4px 8px" }}>🔫 Suspect info</div>
                    <div style={{ background: C.cardAlt, borderRadius: 4, padding: "4px 8px" }}>⏱️ Event timeline</div>
                    <div style={{ background: C.cardAlt, borderRadius: 4, padding: "4px 8px" }}>🚔 Dispatched units</div>
                    <div style={{ background: C.cardAlt, borderRadius: 4, padding: "4px 8px" }}>👶 Children status</div>
                    <div style={{ background: C.cardAlt, borderRadius: 4, padding: "4px 8px" }}>💬 All caller intel</div>
                  </div>
                </div>
                <div style={{ background: C.card, border: `1px solid ${C.red}50`, borderRadius: 10, padding: 14, position: "relative" }}>
                  <div style={{ position: "absolute", top: -6, right: 10, background: C.red, color: "#fff", fontSize: "0.55rem", fontWeight: 800, padding: "2px 8px", borderRadius: 4, letterSpacing: "0.05em" }}>NOVEL</div>
                  <div style={{ fontSize: "0.7rem", fontWeight: 700, color: C.red, marginBottom: 6 }}>⚡ Cross-Caller Verification</div>
                  <div style={{ fontSize: "0.58rem", color: C.textSec, lineHeight: 1.5 }}>
                    Reconciles contradictions across callers. Corroborated facts boosted. Conflicts flagged with both versions. Confidence scores per claim.
                  </div>
                </div>
                <div style={{ background: C.card, border: `1px solid ${C.pink}50`, borderRadius: 10, padding: 14, position: "relative" }}>
                  <div style={{ position: "absolute", top: -6, right: 10, background: C.pink, color: "#fff", fontSize: "0.55rem", fontWeight: 800, padding: "2px 8px", borderRadius: 4, letterSpacing: "0.05em" }}>NOVEL</div>
                  <div style={{ fontSize: "0.7rem", fontWeight: 700, color: C.pink, marginBottom: 6 }}>💓 Emotional Cascade</div>
                  <div style={{ fontSize: "0.58rem", color: C.textSec, lineHeight: 1.5 }}>
                    Detects panic spreading across callers. Prioritizes calm callers for intel. Auto-adjusts agent conversation strategies.
                  </div>
                </div>
              </div>
            </div>

            {/* Connection */}
            <div style={{ display: "flex", justifyContent: "center", padding: "6px 0" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <div style={{ width: 1, height: 20, background: `linear-gradient(${C.purple}, ${C.green})` }} />
                <span style={{ fontSize: "0.6rem", color: C.green, fontWeight: 600, padding: "2px 8px", background: `${C.green}12`, borderRadius: 4, border: `1px solid ${C.green}30` }}>✅ Ground every response before speaking</span>
                <div style={{ width: 1, height: 20, background: `linear-gradient(${C.purple}, ${C.green})` }} />
              </div>
            </div>

            {/* Row 4: RAG Layer */}
            <div style={{ marginBottom: 2 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                <div style={{ width: 3, height: 16, background: C.green, borderRadius: 2 }} />
                <span style={{ fontSize: "0.7rem", fontWeight: 700, color: C.green, letterSpacing: "0.08em", textTransform: "uppercase" }}>RAG & Grounding</span>
                <span style={{ fontSize: "0.65rem", color: C.textDim }}>Hallucination-free responses</span>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 }}>
                {[
                  { icon: "📋", label: "Protocol RAG", desc: "NENA / APCO guidelines, CPR, active shooter procedures", color: C.green },
                  { icon: "📍", label: "Location History", desc: "Prior incidents at address, restraining orders, hazards", color: C.green },
                  { icon: "🔀", label: "Cross-Caller RAG", desc: "Real-time retrieval from other agents' intel", color: C.green, novel: true },
                  { icon: "🛡️", label: "Protocol Verifier", desc: "Validates actions against emergency SOPs before execution", color: C.green },
                ].map((r, i) => (
                  <div key={i} style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, padding: "12px 14px", position: "relative" }}>
                    {r.novel && <div style={{ position: "absolute", top: -6, right: 10, background: C.green, color: "#fff", fontSize: "0.55rem", fontWeight: 800, padding: "2px 8px", borderRadius: 4 }}>NOVEL</div>}
                    <div style={{ fontSize: "0.9rem", marginBottom: 4 }}>{r.icon}</div>
                    <div style={{ fontSize: "0.68rem", fontWeight: 700, color: r.color }}>{r.label}</div>
                    <div style={{ fontSize: "0.57rem", color: C.textSec, lineHeight: 1.4, marginTop: 3 }}>{r.desc}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Connection */}
            <div style={{ display: "flex", justifyContent: "center", padding: "6px 0" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <div style={{ width: 1, height: 20, background: `linear-gradient(${C.green}, ${C.yellow})` }} />
                <span style={{ fontSize: "0.6rem", color: C.yellow, fontWeight: 600, padding: "2px 8px", background: `${C.yellow}12`, borderRadius: 4, border: `1px solid ${C.yellow}30` }}>☁️ Hosted entirely on Google Cloud</span>
                <div style={{ width: 1, height: 20, background: `linear-gradient(${C.green}, ${C.yellow})` }} />
              </div>
            </div>

            {/* Row 5: Google Cloud */}
            <div style={{ marginBottom: 2 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                <div style={{ width: 3, height: 16, background: C.yellow, borderRadius: 2 }} />
                <span style={{ fontSize: "0.7rem", fontWeight: 700, color: C.yellow, letterSpacing: "0.08em", textTransform: "uppercase" }}>Google Cloud</span>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 8 }}>
                {[
                  { icon: "🎙️", label: "Gemini Live API", desc: "Voice streaming" },
                  { icon: "⚡", label: "Gemini 2.5 Flash", desc: "Agent reasoning" },
                  { icon: "🔧", label: "ADK", desc: "Multi-agent framework" },
                  { icon: "☁️", label: "Cloud Run", desc: "Backend hosting" },
                  { icon: "🗄️", label: "Firestore", desc: "Data persistence" },
                  { icon: "🚀", label: "Cloud Build", desc: "CI/CD pipeline" },
                ].map((s, i) => (
                  <div key={i} style={{ background: C.card, border: `1px solid ${C.yellow}25`, borderRadius: 8, padding: "10px 10px", textAlign: "center" }}>
                    <div style={{ fontSize: "1.1rem", marginBottom: 3 }}>{s.icon}</div>
                    <div style={{ fontSize: "0.62rem", fontWeight: 700, color: C.yellow }}>{s.label}</div>
                    <div style={{ fontSize: "0.55rem", color: C.textDim, marginTop: 1 }}>{s.desc}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Connection */}
            <div style={{ display: "flex", justifyContent: "center", padding: "6px 0" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <div style={{ width: 1, height: 20, background: `linear-gradient(${C.yellow}, ${C.orange})` }} />
                <span style={{ fontSize: "0.6rem", color: C.orange, fontWeight: 600, padding: "2px 8px", background: `${C.orange}12`, borderRadius: 4, border: `1px solid ${C.orange}30` }}>📡 WebSocket real-time updates</span>
                <div style={{ width: 1, height: 20, background: `linear-gradient(${C.yellow}, ${C.orange})` }} />
              </div>
            </div>

            {/* Row 6: Dashboard */}
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                <div style={{ width: 3, height: 16, background: C.orange, borderRadius: 2 }} />
                <span style={{ fontSize: "0.7rem", fontWeight: 700, color: C.orange, letterSpacing: "0.08em", textTransform: "uppercase" }}>Command Dashboard</span>
                <span style={{ fontSize: "0.65rem", color: C.textDim }}>React + WebSocket — Unified dispatcher view</span>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 8 }}>
                {[
                  { icon: "🗺️", label: "Incident Map", desc: "Caller + suspect positions" },
                  { icon: "👥", label: "Caller Panels", desc: "Status, role, emotional state" },
                  { icon: "📊", label: "Agent Activity", desc: "Real-time action stream" },
                  { icon: "🔍", label: "Intel Board", desc: "Verified vs conflicting claims" },
                  { icon: "🚨", label: "Dispatch", desc: "Recommended units + actions" },
                ].map((d, i) => (
                  <div key={i} style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 8, padding: "10px 12px", textAlign: "center" }}>
                    <div style={{ fontSize: "1.1rem", marginBottom: 3 }}>{d.icon}</div>
                    <div style={{ fontSize: "0.64rem", fontWeight: 700, color: C.orange }}>{d.label}</div>
                    <div style={{ fontSize: "0.55rem", color: C.textDim, marginTop: 1 }}>{d.desc}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ══════════════════════════════════════════════════ */}
        {/* DATA FLOW VIEW */}
        {/* ══════════════════════════════════════════════════ */}
        {view === "flow" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {flowData.map((step, i) => (
              <div key={step.id}>
                <div style={{
                  display: "flex", gap: 16, alignItems: "flex-start",
                  background: C.card, border: `1px solid ${C.border}`, borderRadius: 12,
                  padding: "18px 20px", borderLeft: `4px solid ${step.color}`,
                  transition: "all 0.2s",
                }}
                  onMouseEnter={() => setHover(step.id)}
                  onMouseLeave={() => setHover(null)}
                >
                  <div style={{
                    width: 44, height: 44, borderRadius: 12, display: "flex", alignItems: "center", justifyContent: "center",
                    background: `${step.color}15`, border: `1px solid ${step.color}30`, fontSize: "1.3rem", flexShrink: 0,
                  }}>{step.icon}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                      <span style={{
                        width: 22, height: 22, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center",
                        background: step.color, color: "#000", fontSize: "0.65rem", fontWeight: 800,
                      }}>{i + 1}</span>
                      <span style={{ fontSize: "0.88rem", fontWeight: 700, color: C.text }}>{step.label}</span>
                    </div>
                    <div style={{ fontSize: "0.72rem", color: C.textSec, lineHeight: 1.6 }}>{step.detail}</div>
                  </div>
                  <div style={{ fontSize: "0.55rem", color: C.textDim, fontWeight: 600, textTransform: "uppercase", whiteSpace: "nowrap", paddingTop: 4, letterSpacing: "0.05em" }}>
                    {i === 0 ? "~1 sec" : i === 1 ? "~0.5 sec" : i === 2 ? "~0.3 sec" : i === 3 ? "Real-time" : i === 4 ? "~0.2 sec" : "Instant"}
                  </div>
                </div>
                {i < flowData.length - 1 && (
                  <div style={{ display: "flex", justifyContent: "center", padding: "2px 0" }}>
                    <div style={{ width: 2, height: 16, background: `linear-gradient(${step.color}, ${flowData[i + 1].color})`, borderRadius: 1 }} />
                  </div>
                )}
              </div>
            ))}
            <div style={{ background: C.card, border: `1px solid ${C.green}30`, borderRadius: 12, padding: 16, textAlign: "center", marginTop: 4 }}>
              <div style={{ fontSize: "0.8rem", fontWeight: 700, color: C.green, marginBottom: 4 }}>End-to-End Latency: ~2 seconds</div>
              <div style={{ fontSize: "0.65rem", color: C.textSec }}>From first word spoken to dispatcher seeing verified intelligence on dashboard</div>
            </div>
          </div>
        )}

        {/* ══════════════════════════════════════════════════ */}
        {/* NOVELTY MAP VIEW */}
        {/* ══════════════════════════════════════════════════ */}
        {view === "novel" && (
          <div>
            <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20, marginBottom: 12 }}>
              <div style={{ fontSize: "0.85rem", fontWeight: 700, color: C.text, marginBottom: 12, textAlign: "center" }}>What Exists vs. What Nexus911 Adds</div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr auto 1fr", gap: 0 }}>
                {/* Headers */}
                <div style={{ padding: "8px 12px", background: C.cardAlt, borderRadius: "6px 0 0 0", fontSize: "0.65rem", fontWeight: 700, color: C.red, textAlign: "center" }}>EXISTING SOLUTIONS</div>
                <div style={{ padding: "8px 12px", background: C.cardAlt, fontSize: "0.65rem", fontWeight: 700, color: C.textDim, textAlign: "center" }}>vs</div>
                <div style={{ padding: "8px 12px", background: C.cardAlt, borderRadius: "0 6px 0 0", fontSize: "0.65rem", fontWeight: 700, color: C.green, textAlign: "center" }}>NEXUS911 (NOVEL)</div>

                {[
                  ["AI assists ONE human dispatcher per call", "→", "AI agents autonomously handle MULTIPLE callers simultaneously"],
                  ["Each call is an isolated data silo", "→", "Shared Incident Knowledge Graph — all agents see everything"],
                  ["Human must recognize duplicate calls", "→", "Automatic deduplication by location + keywords + time"],
                  ["Same script for every caller", "→", "Role-specific agents: child protocol ≠ witness protocol"],
                  ["No cross-caller fact checking", "→", "Cross-Caller Verification: detects contradictions between callers"],
                  ["Single-caller sentiment analysis", "→", "Emotional Cascade: analyzes panic patterns ACROSS all callers"],
                  ["Hardcoded responses", "→", "3-layer RAG: protocols + location history + cross-caller intel"],
                  ["Scales by hiring more humans", "→", "Scales by spawning more AI agents"],
                ].map(([left, arrow, right], i) => (
                  <div key={i} style={{ display: "contents" }}>
                    <div style={{ padding: "8px 12px", fontSize: "0.63rem", color: C.textSec, borderTop: `1px solid ${C.border}`, display: "flex", alignItems: "center" }}>{left}</div>
                    <div style={{ padding: "8px 6px", fontSize: "0.7rem", color: C.textDim, borderTop: `1px solid ${C.border}`, display: "flex", alignItems: "center", justifyContent: "center" }}>{arrow}</div>
                    <div style={{ padding: "8px 12px", fontSize: "0.63rem", color: C.green, fontWeight: 600, borderTop: `1px solid ${C.border}`, display: "flex", alignItems: "center" }}>{right}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Novelty Deep Dives */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
              {[
                {
                  color: C.red, icon: "⚡", label: "Cross-Caller Verification",
                  tag: "Inspired by VerifyLayer",
                  points: [
                    "Caller A: 'He has a gun'",
                    "Caller B: 'No weapons visible'",
                    "System: CONFLICT DETECTED",
                    "→ Show both to dispatcher",
                    "→ Weight by caller proximity",
                    "→ Confidence: 60% armed",
                  ],
                  impact: "Prevents officers from walking into undetected armed situation OR overreacting to false reports"
                },
                {
                  color: C.pink, icon: "💓", label: "Emotional Cascade Detection",
                  tag: "No existing implementation",
                  points: [
                    "Child: PANIC (9/10)",
                    "Mother: DISTRESS (8/10)",
                    "Neighbor: CALM (2/10)",
                    "→ Cascade alert triggered",
                    "→ Neighbor promoted to primary intel",
                    "→ Child agent switches to comfort",
                  ],
                  impact: "Most reliable intel comes from calmest caller — system identifies this automatically"
                },
                {
                  color: C.green, icon: "🔀", label: "Cross-Caller RAG",
                  tag: "Live retrieval from other agents",
                  points: [
                    "Agent A asks child: 'Where is daddy?'",
                    "Child: 'I hear him downstairs'",
                    "→ Intel submitted to graph",
                    "→ Agent D (neighbor) retrieves this",
                    "→ Asks: 'Can you see ground floor?'",
                    "→ Neighbor confirms suspect location",
                  ],
                  impact: "Agents intelligently guide each caller based on what other callers have revealed"
                },
              ].map((n, i) => (
                <div key={i} style={{ background: C.card, border: `1px solid ${n.color}30`, borderRadius: 12, padding: 16, display: "flex", flexDirection: "column" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                    <span style={{ fontSize: "1.2rem" }}>{n.icon}</span>
                    <div>
                      <div style={{ fontSize: "0.75rem", fontWeight: 700, color: n.color }}>{n.label}</div>
                      <div style={{ fontSize: "0.55rem", color: C.textDim, fontStyle: "italic" }}>{n.tag}</div>
                    </div>
                  </div>
                  <div style={{ flex: 1, marginBottom: 10 }}>
                    {n.points.map((p, j) => (
                      <div key={j} style={{
                        fontSize: "0.6rem", color: p.startsWith("→") ? n.color : C.textSec,
                        fontWeight: p.startsWith("→") || p.includes("CONFLICT") || p.includes("Cascade") ? 600 : 400,
                        padding: "2px 0", fontFamily: "'SF Mono', 'Fira Code', monospace", lineHeight: 1.5,
                      }}>{p}</div>
                    ))}
                  </div>
                  <div style={{ fontSize: "0.58rem", color: C.textSec, padding: "8px 10px", background: `${n.color}08`, borderRadius: 6, borderLeft: `2px solid ${n.color}`, lineHeight: 1.4 }}>
                    <span style={{ fontWeight: 700, color: n.color }}>Impact: </span>{n.impact}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── FOOTER ── */}
        <div style={{ marginTop: 20, padding: "14px 20px", background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <span style={{ fontSize: "0.72rem", fontWeight: 700, color: C.text }}>AviaOhr — Nexus911</span>
            <span style={{ fontSize: "0.62rem", color: C.textDim, marginLeft: 8 }}>Multi-Agent Emergency Coordination System</span>
          </div>
          <div style={{ display: "flex", gap: 12, fontSize: "0.58rem", color: C.textDim }}>
            <span><span style={{ color: C.red, fontWeight: 700 }}>3</span> Novel Features</span>
            <span><span style={{ color: C.yellow, fontWeight: 700 }}>6</span> Google Services</span>
            <span><span style={{ color: C.green, fontWeight: 700 }}>3</span> RAG Layers</span>
            <span style={{ color: C.textDim }}>© 2026 Dennis Sharon</span>
          </div>
        </div>
      </div>
    </div>
  );
}
