import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  Siren, ArrowRight, ChevronDown, Radio, Shield, Database,
  Cpu, Zap, BarChart3, Users, Eye, GitMerge, Activity,
  ShieldCheck, AlertTriangle, Phone, Volume2, UserCircle2,
  CheckCircle2, Lock, Server, Brain,
} from "lucide-react";

/* ═══════════════════════════════════════════
   Intersection Observer hook for scroll reveal
   ═══════════════════════════════════════════ */
function useReveal() {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          el.classList.add("animate-slide-up");
          el.style.opacity = "1";
          observer.unobserve(el);
        }
      },
      { threshold: 0.1 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  return ref;
}

/* ═══════════════════════════════════════════
   Data
   ═══════════════════════════════════════════ */

const CAPABILITIES = [
  {
    icon: Users,
    title: "Autonomous Emergency Voice Agents",
    description:
      "Each caller gets a dedicated Gemini-powered agent that conducts the full 911 interview via the Gemini Live API — full-duplex audio with barge-in support. No hold queues. No transfers.",
    accent: "from-blue-500/20 to-blue-600/5",
    iconColor: "text-blue-400",
  },
  {
    icon: Shield,
    title: "VerifyLayer — Hallucination Detection",
    description:
      "Every AI-extracted fact is validated via NLI before entering the knowledge graph. Cross-call contradiction detection catches conflicting statements. Confidence scoring gives dispatchers transparent reliability signals.",
    accent: "from-emerald-500/20 to-emerald-600/5",
    iconColor: "text-emerald-400",
  },
  {
    icon: Brain,
    title: "Role-Aware Conversation",
    description:
      "Agents adapt vocabulary, pacing, and question strategy based on caller classification — child, victim, witness, or bystander. A terrified 8-year-old gets a different experience than a street witness.",
    accent: "from-purple-500/20 to-purple-600/5",
    iconColor: "text-purple-400",
  },
  {
    icon: GitMerge,
    title: "Cross-Call Intel Sharing",
    description:
      "When Agent 2 extracts an address, Agent 1 can confirm it with their caller in real time via the shared Knowledge Graph. Three fragments become one verified picture.",
    accent: "from-cyan-500/20 to-cyan-600/5",
    iconColor: "text-cyan-400",
  },
  {
    icon: Database,
    title: "Incident Deduplication",
    description:
      "Geo + temporal + semantic clustering merges multiple calls about the same event into one enriched dispatch record. Three callers, one incident, zero duplicates.",
    accent: "from-amber-500/20 to-amber-600/5",
    iconColor: "text-amber-400",
  },
  {
    icon: Radio,
    title: "Text Simulation Fallback",
    description:
      "When voice sessions fail, the system falls back to text-based simulation that still exercises the full pipeline — VerifyLayer, dedup, dispatch — ensuring demo reliability.",
    accent: "from-rose-500/20 to-rose-600/5",
    iconColor: "text-rose-400",
  },
];

const PIPELINE_STEPS = [
  {
    num: "01",
    title: "Listen",
    description: "Every call, every word captured. Gemini Live API streams full-duplex audio — the AI speaks naturally, listens for interruptions, and never puts anyone on hold.",
    detail: "Gemini 2.5 Flash · Native Audio",
    icon: Volume2,
  },
  {
    num: "02",
    title: "Verify",
    description: "VerifyLayer validates every extracted fact via NLI entailment scoring. Cross-call contradiction detection compares all active callers pairwise. Nothing enters the dispatch record unverified.",
    detail: "NLI Engine · Contradiction Detector · Penalization",
    icon: ShieldCheck,
  },
  {
    num: "03",
    title: "Dispatch",
    description: "Verified facts merge into a single enriched incident package. Geo + temporal + semantic clustering deduplicates automatically. Confidence-scored intelligence reaches responders in seconds.",
    detail: "Knowledge Graph · Dedup · Confidence Scoring",
    icon: Siren,
  },
];

const STATS = [
  { value: "3", label: "Simultaneous AI Agents", sub: "per incident" },
  { value: "20s", label: "To Verified Dispatch", sub: "end-to-end" },
  { value: "97%", label: "Confidence Score", sub: "with corroboration" },
  { value: "100%", label: "Call Coverage", sub: "zero hold time" },
];

const TECH_STACK = [
  { name: "Gemini Live API", desc: "Full-duplex voice streaming with barge-in", icon: Zap },
  { name: "Google ADK", desc: "Multi-agent orchestration framework", icon: GitMerge },
  { name: "Gemini 2.5 Flash", desc: "NLI verification & voice agents", icon: Brain },
  { name: "FastAPI", desc: "Real-time WebSocket backend", icon: Server },
  { name: "Cloud Run", desc: "Serverless container deployment", icon: Activity },
  { name: "VerifyLayer", desc: "Custom hallucination detection pipeline", icon: Eye },
];

const ROLES = [
  { role: "Child Caller", desc: "Simplified language, gentle pacing, safety-first prompts", color: "text-yellow-400", bg: "bg-yellow-500/10", border: "border-yellow-500/20" },
  { role: "Victim", desc: "Medical triage priority, location confirmation, injury assessment", color: "text-red-400", bg: "bg-red-500/10", border: "border-red-500/20" },
  { role: "Witness", desc: "Scene details, suspect description, vehicle identification", color: "text-blue-400", bg: "bg-blue-500/10", border: "border-blue-500/20" },
  { role: "Bystander", desc: "Directional context, crowd assessment, access information", color: "text-gray-400", bg: "bg-gray-500/10", border: "border-gray-500/20" },
];

/* ═══════════════════════════════════════════
   Landing Page
   ═══════════════════════════════════════════ */
export default function LandingPage() {
  const navigate = useNavigate();
  const capRef = useReveal();
  const pipeRef = useReveal();
  const statsRef = useReveal();
  const rolesRef = useReveal();
  const techRef = useReveal();
  const scenarioRef = useReveal();

  const enterDashboard = () => {
    document.body.style.opacity = "0";
    document.body.style.transition = "opacity 350ms cubic-bezier(0.4,0,0.2,1)";
    setTimeout(() => {
      navigate("/dashboard");
      document.body.style.opacity = "1";
    }, 350);
  };

  return (
    <div className="bg-surface-base min-h-screen text-white">

      {/* ═══════════════════════════════════════
          HERO
          ═══════════════════════════════════════ */}
      <section className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden">
        {/* Animated gradient blobs */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div
            className="absolute top-1/4 -left-32 w-[500px] h-[500px] rounded-full blur-[120px] animate-gradient-blob"
            style={{ background: "radial-gradient(circle, rgba(96,165,250,0.25), rgba(96,165,250,0.05))" }}
          />
          <div
            className="absolute bottom-1/3 -right-32 w-[450px] h-[450px] rounded-full blur-[120px] animate-gradient-blob"
            style={{ background: "radial-gradient(circle, rgba(34,211,238,0.2), rgba(34,211,238,0.05))", animationDelay: "-3s" }}
          />
          <div
            className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full blur-[140px] animate-gradient-blob"
            style={{ background: "radial-gradient(circle, rgba(239,68,68,0.06), transparent)", animationDelay: "-5s" }}
          />
        </div>

        {/* Dot grid */}
        <div
          className="absolute inset-0 opacity-[0.15] pointer-events-none"
          style={{
            backgroundImage: "radial-gradient(rgba(255,255,255,0.08) 1px, transparent 1px)",
            backgroundSize: "48px 48px",
          }}
        />

        {/* Content */}
        <div className="relative z-10 text-center px-6 max-w-5xl mx-auto">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass-subtle mb-8 animate-slide-up stagger-1" style={{ opacity: 0 }}>
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            <span className="text-[11px] font-semibold text-gray-300 tracking-[0.15em] uppercase">
              Gemini Live Agent Challenge 2026
            </span>
          </div>

          {/* Title */}
          <h1 className="font-display text-6xl sm:text-7xl lg:text-8xl xl:text-9xl font-bold tracking-[-0.03em] leading-[0.9] mb-6 animate-slide-up stagger-2" style={{ opacity: 0 }}>
            <span className="block text-white">Autonomous 911</span>
            <span className="block text-gradient">Dispatch</span>
          </h1>

          {/* Subtitle — hear.ai style: bold statement */}
          <p className="text-lg sm:text-xl lg:text-2xl text-gray-400 max-w-3xl mx-auto leading-relaxed mb-4 animate-slide-up stagger-3" style={{ opacity: 0 }}>
            Three callers. Three AI agents. One verified incident.
            <span className="text-white font-semibold"> Zero hallucinations.</span>
          </p>

          <p className="text-sm text-gray-500 max-w-xl mx-auto mb-10 font-mono tracking-wide animate-slide-up stagger-4" style={{ opacity: 0 }}>
            Multi-agent voice dispatch with real-time hallucination verification
          </p>

          {/* CTA */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-slide-up stagger-5" style={{ opacity: 0 }}>
            <button
              onClick={enterDashboard}
              className="group inline-flex items-center gap-3 px-8 py-4 rounded-2xl bg-accent-cyan/10 border border-accent-cyan/30 hover:bg-accent-cyan/20 transition-all duration-300 text-white font-semibold glow-cyan-hover"
            >
              <Siren className="w-5 h-5 text-accent-cyan" />
              Enter Command Center
              <ArrowRight className="w-4 h-4 text-gray-400 group-hover:translate-x-1 transition-transform duration-200" />
            </button>
            <a
              href="#capabilities"
              className="inline-flex items-center gap-2 px-6 py-4 rounded-2xl text-gray-400 hover:text-white transition-colors text-sm font-medium"
            >
              See how it works
              <ChevronDown className="w-4 h-4" />
            </a>
          </div>

          {/* Tech badges */}
          <div className="flex items-center justify-center gap-4 sm:gap-8 mt-16 flex-wrap animate-slide-up stagger-6" style={{ opacity: 0 }}>
            {["GEMINI LIVE API", "GOOGLE ADK", "CLOUD RUN", "VERIFYLAYER", "FASTAPI"].map((tech) => (
              <span key={tech} className="text-[10px] font-bold tracking-[0.2em] text-gray-600 uppercase">
                {tech}
              </span>
            ))}
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce-down">
          <ChevronDown className="w-6 h-6 text-gray-600" />
        </div>
      </section>

      {/* ═══════════════════════════════════════
          STATS BAR — inspired by hear.ai metrics
          ═══════════════════════════════════════ */}
      <section className="py-16 px-6 border-t border-white/[0.06]">
        <div ref={statsRef} className="max-w-6xl mx-auto" style={{ opacity: 0 }}>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            {STATS.map((stat, i) => (
              <div
                key={i}
                className="stat-card text-center p-6 rounded-2xl bg-surface-card border border-white/[0.06]"
              >
                <p className="font-display text-4xl sm:text-5xl font-bold text-gradient mb-2">{stat.value}</p>
                <p className="text-sm font-semibold text-white mb-0.5">{stat.label}</p>
                <p className="text-[11px] text-gray-500 uppercase tracking-wider">{stat.sub}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════
          CAPABILITIES — "Built for Every Emergency"
          (hear.ai style: role cards → capability cards)
          ═══════════════════════════════════════ */}
      <section id="capabilities" className="py-24 px-6 border-t border-white/[0.06]">
        <div ref={capRef} className="max-w-6xl mx-auto" style={{ opacity: 0 }}>
          <p className="text-[11px] font-bold tracking-[0.25em] text-accent-cyan uppercase text-center mb-3">
            Core Capabilities
          </p>
          <h2 className="font-display text-4xl sm:text-5xl font-bold text-white text-center tracking-tight mb-4">
            Built for Every Emergency
          </h2>
          <p className="text-gray-500 text-center max-w-2xl mx-auto mb-16 text-lg">
            Six interconnected systems that transform emergency dispatch from reactive to autonomous.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {CAPABILITIES.map((cap, i) => (
              <article
                key={i}
                className="feature-card rounded-2xl p-6 bg-surface-card group"
              >
                <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${cap.accent} flex items-center justify-center mb-5 group-hover:scale-110 transition-transform duration-300`}>
                  <cap.icon className={`w-5 h-5 ${cap.iconColor}`} />
                </div>
                <h3 className="font-display text-lg font-bold text-white mb-2 tracking-tight">
                  {cap.title}
                </h3>
                <p className="text-sm text-gray-400 leading-relaxed">
                  {cap.description}
                </p>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════
          HOW IT WORKS — "Think Different. We Already Built It."
          (hear.ai style: numbered steps with big descriptions)
          ═══════════════════════════════════════ */}
      <section className="py-24 px-6 border-t border-white/[0.06]">
        <div ref={pipeRef} className="max-w-5xl mx-auto" style={{ opacity: 0 }}>
          <p className="text-[11px] font-bold tracking-[0.25em] text-accent-cyan uppercase text-center mb-3">
            The Pipeline
          </p>
          <h2 className="font-display text-4xl sm:text-5xl font-bold text-white text-center tracking-tight mb-4">
            Listen. Verify. Dispatch.
          </h2>
          <p className="text-gray-500 text-center max-w-xl mx-auto mb-20 text-lg">
            Three steps from caller to confirmed dispatch — every fact checked, every call correlated.
          </p>

          <div className="space-y-16">
            {PIPELINE_STEPS.map((step, i) => (
              <div key={i} className="flex flex-col md:flex-row items-start gap-8 group">
                {/* Step number */}
                <div className="flex-shrink-0">
                  <div className="w-16 h-16 rounded-2xl bg-surface-card border border-white/[0.08] flex items-center justify-center group-hover:border-accent-cyan/30 transition-colors duration-300">
                    <span className="font-mono text-2xl font-bold text-gradient">{step.num}</span>
                  </div>
                </div>

                {/* Content */}
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <step.icon className="w-5 h-5 text-accent-cyan" />
                    <h3 className="font-display text-2xl font-bold text-white">{step.title}</h3>
                  </div>
                  <p className="text-gray-400 leading-relaxed mb-3 text-base max-w-2xl">
                    {step.description}
                  </p>
                  <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-surface-card border border-white/[0.06] text-[11px] font-mono text-gray-500 tracking-wide">
                    {step.detail}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════
          ROLE AWARENESS — "Built for Every Role"
          (hear.ai style: horizontal role cards)
          ═══════════════════════════════════════ */}
      <section className="py-24 px-6 border-t border-white/[0.06]">
        <div ref={rolesRef} className="max-w-5xl mx-auto" style={{ opacity: 0 }}>
          <p className="text-[11px] font-bold tracking-[0.25em] text-accent-cyan uppercase text-center mb-3">
            Adaptive Intelligence
          </p>
          <h2 className="font-display text-4xl sm:text-5xl font-bold text-white text-center tracking-tight mb-4">
            Every Caller Gets a Different Agent
          </h2>
          <p className="text-gray-500 text-center max-w-xl mx-auto mb-16 text-lg">
            Role-aware conversation that adapts vocabulary, pacing, and question strategy in real time.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {ROLES.map((r, i) => (
              <div
                key={i}
                className={`rounded-2xl p-5 ${r.bg} border ${r.border} transition-all duration-300 hover:scale-[1.02]`}
              >
                <div className="flex items-center gap-3 mb-3">
                  <UserCircle2 className={`w-6 h-6 ${r.color}`} />
                  <h3 className={`font-display text-lg font-bold ${r.color}`}>{r.role}</h3>
                </div>
                <p className="text-sm text-gray-400 leading-relaxed">{r.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════
          DEMO SCENARIO — the 20-second story
          ═══════════════════════════════════════ */}
      <section className="py-24 px-6 border-t border-white/[0.06]">
        <div ref={scenarioRef} className="max-w-5xl mx-auto" style={{ opacity: 0 }}>
          <p className="text-[11px] font-bold tracking-[0.25em] text-accent-cyan uppercase text-center mb-3">
            Live Demo Scenario
          </p>
          <h2 className="font-display text-4xl sm:text-5xl font-bold text-white text-center tracking-tight mb-4">
            Highway Multi-Vehicle Accident
          </h2>
          <p className="text-gray-500 text-center max-w-xl mx-auto mb-16 text-lg">
            3 callers · 3 AI agents · 1 verified incident · 20 seconds
          </p>

          <div className="rounded-2xl bg-surface-card border border-white/[0.08] overflow-hidden">
            {/* Timeline */}
            <div className="divide-y divide-white/[0.06]">
              {[
                { time: "T+0s", caller: "Child (age 8)", icon: "👧", quote: "We crashed and mommy isn't moving", action: "Agent 1 → role: CHILD, extracts: vehicle_accident, unresponsive_adult", verify: "Entailed ✅ 0.87" },
                { time: "T+8s", caller: "Witness", icon: "👁", quote: "Sedan hit an 18-wheeler at Route 9 and Elm", action: "Agent 2 → role: WITNESS, extracts: location, vehicles", verify: "Cross-check ✅ consistent" },
                { time: "T+12s", caller: "Cross-call", icon: "🔗", quote: "Agent 1 asks child: 'Are you near Route 9 and Elm?'", action: "Child confirms → confidence: 0.97", verify: "Corroborated ✅" },
                { time: "T+15s", caller: "Victim (driver)", icon: "🚗", quote: "I was in my blue Camry, truck ran the red light", action: "Agent 3 → role: VICTIM, extracts: vehicle, cause", verify: "Entailed ✅ consistent" },
                { time: "T+18s", caller: "System", icon: "🔀", quote: "Deduplication: 3 calls merged into 1 incident", action: "Geo ✅ Temporal ✅ Semantic (0.94) ✅", verify: "Merged" },
                { time: "T+20s", caller: "Dispatch", icon: "🚨", quote: "2 ambulances, 1 fire unit, 1 police unit", action: "Full confidence-scored intel package sent", verify: "Dispatched ✅" },
              ].map((row, i) => (
                <div key={i} className="flex items-start gap-4 p-5 hover:bg-white/[0.02] transition-colors">
                  <span className="font-mono text-xs text-accent-cyan font-bold w-12 flex-shrink-0 pt-0.5">{row.time}</span>
                  <span className="text-xl flex-shrink-0 pt-0.5">{row.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">{row.caller}</span>
                      <span className="text-[10px] font-mono text-emerald-400/70 bg-emerald-500/10 px-1.5 py-0.5 rounded">{row.verify}</span>
                    </div>
                    <p className="text-sm text-white font-medium italic mb-1">"{row.quote}"</p>
                    <p className="text-[11px] text-gray-500">{row.action}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* Dispatch package */}
            <div className="p-5 bg-emerald-500/[0.04] border-t border-emerald-500/20">
              <p className="text-xs font-bold text-emerald-400 uppercase tracking-[0.15em] mb-3">Dispatch Package (T+20s)</p>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-[11px]">
                <div>
                  <span className="text-gray-500 block">Location</span>
                  <span className="text-white font-medium">Route 9 & Elm Street</span>
                  <span className="text-gray-500 block font-mono text-[10px]">conf: 0.97 · 3 sources</span>
                </div>
                <div>
                  <span className="text-gray-500 block">Vehicles</span>
                  <span className="text-white font-medium">Blue Camry + 18-wheeler</span>
                  <span className="text-gray-500 block font-mono text-[10px]">corroborated</span>
                </div>
                <div>
                  <span className="text-gray-500 block">Injuries</span>
                  <span className="text-white font-medium">1 unresponsive, 1 mobile</span>
                  <span className="text-gray-500 block font-mono text-[10px]">conf: 0.87</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════
          TECH STACK
          ═══════════════════════════════════════ */}
      <section className="py-24 px-6 border-t border-white/[0.06]">
        <div ref={techRef} className="max-w-5xl mx-auto" style={{ opacity: 0 }}>
          <p className="text-[11px] font-bold tracking-[0.25em] text-accent-cyan uppercase text-center mb-3">
            Powered By
          </p>
          <h2 className="font-display text-4xl sm:text-5xl font-bold text-white text-center tracking-tight mb-16">
            Tech Architecture
          </h2>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {TECH_STACK.map((t) => (
              <div
                key={t.name}
                className="feature-card rounded-xl p-5 bg-surface-card group"
              >
                <t.icon className="w-5 h-5 text-accent-cyan mb-3 group-hover:scale-110 transition-transform duration-200" />
                <h4 className="font-display text-sm font-bold text-white mb-1">{t.name}</h4>
                <p className="text-[11px] text-gray-500 leading-relaxed">{t.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════
          VERIFYLAYER DEEP DIVE — "What VerifyLayer Prevents"
          (hear.ai style: before/after comparison)
          ═══════════════════════════════════════ */}
      <section className="py-24 px-6 border-t border-white/[0.06]">
        <div className="max-w-5xl mx-auto">
          <p className="text-[11px] font-bold tracking-[0.25em] text-accent-cyan uppercase text-center mb-3">
            Safety Layer
          </p>
          <h2 className="font-display text-4xl sm:text-5xl font-bold text-white text-center tracking-tight mb-4">
            What VerifyLayer Prevents
          </h2>
          <p className="text-gray-500 text-center max-w-xl mx-auto mb-16 text-lg">
            The verification layer is not optional safety theater — it's what makes autonomous operation defensible.
          </p>

          <div className="space-y-4">
            {[
              {
                failure: "Hallucinated address",
                without: "Agent fabricates '123 Oak St' when caller said 'near the oak tree' → responders go to wrong location",
                withVL: "NLI detects non-entailment → fact flagged, agent re-asks",
              },
              {
                failure: "Cross-call contamination",
                without: "Detail from Call A leaks into Call B's context → confused dispatch record",
                withVL: "Fact provenance tracked per-agent, contamination blocked",
              },
              {
                failure: "Contradictory facts merged",
                without: "'Blue Honda' and 'Red Toyota' both enter dispatch as ground truth",
                withVL: "Contradiction detected → both penalized, flagged for review",
              },
              {
                failure: "Confidence inflation",
                without: "Every extracted fact treated as equally reliable",
                withVL: "Penalization weights by caller role, corroboration, and entailment",
              },
            ].map((row, i) => (
              <div key={i} className="grid grid-cols-1 md:grid-cols-12 gap-4 items-start">
                <div className="md:col-span-3">
                  <div className="rounded-xl p-4 bg-surface-card border border-white/[0.06]">
                    <p className="text-sm font-bold text-white">{row.failure}</p>
                  </div>
                </div>
                <div className="md:col-span-4">
                  <div className="rounded-xl p-4 bg-red-500/[0.06] border border-red-500/20">
                    <p className="text-[10px] font-bold text-red-400 uppercase tracking-wider mb-1">Without VerifyLayer</p>
                    <p className="text-xs text-gray-400 leading-relaxed">{row.without}</p>
                  </div>
                </div>
                <div className="md:col-span-1 flex items-center justify-center">
                  <ArrowRight className="w-4 h-4 text-gray-600 hidden md:block" />
                </div>
                <div className="md:col-span-4">
                  <div className="rounded-xl p-4 bg-emerald-500/[0.06] border border-emerald-500/20">
                    <p className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider mb-1">With VerifyLayer</p>
                    <p className="text-xs text-gray-400 leading-relaxed">{row.withVL}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════
          CONFIDENCE SCORING — penalization weights
          ═══════════════════════════════════════ */}
      <section className="py-24 px-6 border-t border-white/[0.06]">
        <div className="max-w-4xl mx-auto">
          <p className="text-[11px] font-bold tracking-[0.25em] text-accent-cyan uppercase text-center mb-3">
            Trust Architecture
          </p>
          <h2 className="font-display text-4xl sm:text-5xl font-bold text-white text-center tracking-tight mb-16">
            Confidence Scoring
          </h2>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { weight: "40%", label: "NLI Score", desc: "Entailment strength", color: "text-blue-400", bar: "bg-blue-500" },
              { weight: "30%", label: "Credibility", desc: "Caller role weight", color: "text-purple-400", bar: "bg-purple-500" },
              { weight: "20%", label: "Corroboration", desc: "Cross-caller match", color: "text-emerald-400", bar: "bg-emerald-500" },
              { weight: "10%", label: "Contradiction", desc: "Conflict penalty", color: "text-red-400", bar: "bg-red-500" },
            ].map((f, i) => (
              <div key={i} className="rounded-xl p-5 bg-surface-card border border-white/[0.06] text-center">
                <p className={`font-display text-3xl font-bold ${f.color} mb-2`}>{f.weight}</p>
                <p className="text-sm font-semibold text-white mb-1">{f.label}</p>
                <p className="text-[11px] text-gray-500 mb-3">{f.desc}</p>
                <div className="h-1 rounded-full bg-white/[0.06] overflow-hidden">
                  <div className={`h-full rounded-full ${f.bar}`} style={{ width: f.weight }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════
          FINAL CTA — "New Freedom to Grow" style banner
          ═══════════════════════════════════════ */}
      <section className="py-24 px-6 border-t border-white/[0.06]">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="font-display text-4xl sm:text-5xl lg:text-6xl font-bold text-white tracking-tight mb-6">
            Every Second Counts.
            <br />
            <span className="text-gradient">Make Every Second Smarter.</span>
          </h2>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto mb-10">
            See the full pipeline in action — launch a multi-caller simulation and watch three AI agents handle, verify, and dispatch in real time.
          </p>
          <button
            onClick={enterDashboard}
            className="group inline-flex items-center gap-3 px-10 py-5 rounded-2xl bg-accent-cyan/10 border border-accent-cyan/30 hover:bg-accent-cyan/20 transition-all duration-300 text-white font-bold text-lg glow-cyan-hover"
          >
            <Siren className="w-6 h-6 text-accent-cyan" />
            Enter Command Center
            <ArrowRight className="w-5 h-5 text-gray-400 group-hover:translate-x-1.5 transition-transform duration-200" />
          </button>
        </div>
      </section>

      {/* ═══════════════════════════════════════
          FOOTER
          ═══════════════════════════════════════ */}
      <footer className="py-12 px-6 border-t border-white/[0.06] text-center">
        <p className="font-display text-lg font-bold text-white mb-1">
          NEXUS<span className="text-gradient">911</span>
        </p>
        <p className="text-xs text-gray-600 mb-4">
          Built for the Gemini Live Agent Challenge 2026
        </p>
        <div className="flex items-center justify-center gap-4 mb-4">
          {["Gemini Live API", "Google ADK", "Cloud Run"].map((t) => (
            <span key={t} className="text-[10px] font-mono text-gray-700 tracking-wider">{t}</span>
          ))}
        </div>
        <p className="text-[10px] text-gray-700">
          &copy; 2026 Nexus911. MIT License.
        </p>
      </footer>
    </div>
  );
}
