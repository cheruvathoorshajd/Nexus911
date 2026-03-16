import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { motion, AnimatePresence, useScroll, useTransform } from "framer-motion";
import {
  Activity, AlertTriangle, Phone, Shield, ShieldCheck, ShieldX, ShieldAlert,
  Radio, Users, Clock, MapPin, ChevronDown, Wifi, WifiOff, Zap,
  Eye, GitMerge, CheckCircle2, XCircle, Volume2, PhoneCall,
  BarChart3, RefreshCw, Play, Plus, X, Siren, UserCircle2,
  ArrowRight, Database, Cpu, Timer, TrendingUp, TrendingDown,
  AlertCircle, CircleDot, Mic, MicOff
} from "lucide-react";

/* ════════════════════════════════════════════════════════════════════
   TYPES — matching the FastAPI backend models
   ════════════════════════════════════════════════════════════════════ */

interface CallerInfo {
  id: string;
  role: string;
  name: string;
  phone: string;
  location: string;
  status: string;
  emotional_state: string;
  key_intel: string[];
  agent_id: string;
}

interface Incident {
  id: string;
  incident_type: string;
  severity: string;
  location: string;
  summary: string;
  callers: Record<string, CallerInfo>;
  suspect: Record<string, unknown>;
  victims_count: number;
  children_involved: boolean;
  dispatched_units: string[];
  timeline: TimelineEvent[];
  status: string;
  caller_count: number;
  dedup_confidence: number;
  merged_caller_count: number;
}

interface TimelineEvent {
  time: number;
  source: string;
  event: string;
  verification?: Record<string, unknown>;
}

interface Stats {
  total_incidents: number;
  active_incidents: number;
  total_callers: number;
  critical_incidents: number;
}

interface CacheStats {
  hits: number;
  misses: number;
  size: number;
  max_size: number;
  hit_rate: number;
  evictions: number;
}

interface WSMessage {
  type: string;
  data?: Record<string, Incident> | Incident;
}

/* ════════════════════════════════════════════════════════════════════
   DESIGN CONSTANTS
   ════════════════════════════════════════════════════════════════════ */

const SEVERITY: Record<string, { bg: string; border: string; text: string; dot: string; stripe: string; label: string }> = {
  CRITICAL: { bg: "bg-red-500/10", border: "border-red-500/25", text: "text-red-400", dot: "bg-red-500", stripe: "severity-stripe-critical", label: "CRITICAL" },
  HIGH:     { bg: "bg-orange-500/10", border: "border-orange-500/25", text: "text-orange-400", dot: "bg-orange-500", stripe: "severity-stripe-high", label: "HIGH" },
  MEDIUM:   { bg: "bg-yellow-500/10", border: "border-yellow-500/25", text: "text-yellow-400", dot: "bg-yellow-500", stripe: "severity-stripe-medium", label: "MEDIUM" },
  LOW:      { bg: "bg-green-500/10", border: "border-green-500/25", text: "text-green-400", dot: "bg-green-500", stripe: "severity-stripe-low", label: "LOW" },
};

const ROLES: Record<string, { bg: string; text: string; label: string }> = {
  VICTIM:          { bg: "bg-red-500/20", text: "text-red-300", label: "VICTIM" },
  WITNESS:         { bg: "bg-blue-500/20", text: "text-blue-300", label: "WITNESS" },
  BYSTANDER:       { bg: "bg-slate-500/20", text: "text-slate-300", label: "BYSTANDER" },
  CHILD:           { bg: "bg-yellow-500/20", text: "text-yellow-300", label: "CHILD" },
  OFFICIAL:        { bg: "bg-indigo-500/20", text: "text-indigo-300", label: "OFFICIAL" },
  REPORTING_PARTY: { bg: "bg-purple-500/20", text: "text-purple-300", label: "REPORTER" },
  INVOLVED_PARTY:  { bg: "bg-amber-500/20", text: "text-amber-300", label: "INVOLVED" },
  UNKNOWN:         { bg: "bg-gray-500/20", text: "text-gray-400", label: "UNKNOWN" },
};

const VERIFICATION: Record<string, { Icon: typeof Shield; color: string; bg: string; label: string }> = {
  entailment:    { Icon: ShieldCheck, color: "text-emerald-400", bg: "bg-emerald-500/15", label: "VERIFIED" },
  contradiction: { Icon: ShieldX, color: "text-red-400", bg: "bg-red-500/15", label: "CONTRADICTED" },
  neutral:       { Icon: ShieldAlert, color: "text-yellow-400", bg: "bg-yellow-500/15", label: "UNVERIFIED" },
  pending:       { Icon: Shield, color: "text-gray-400", bg: "bg-gray-500/15", label: "PENDING" },
  error:         { Icon: ShieldX, color: "text-gray-500", bg: "bg-gray-500/10", label: "ERROR" },
};

/* ════════════════════════════════════════════════════════════════════
   HOOKS
   ════════════════════════════════════════════════════════════════════ */

function useWebSocket(onMessage: (msg: WSMessage) => void) {
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout>>(undefined);
  const msgBufferRef = useRef<WSMessage[]>([]);
  const rafRef = useRef<number>(undefined);

  // RAF-batched message processing
  const flushMessages = useCallback(() => {
    const batch = msgBufferRef.current.splice(0);
    batch.forEach(onMessage);
    rafRef.current = undefined;
  }, [onMessage]);

  const connect = useCallback(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/dashboard`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        // Request all current incidents on connect
        ws.send(JSON.stringify({ type: "get_all_incidents" }));
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data) as WSMessage;
          msgBufferRef.current.push(msg);
          if (!rafRef.current) {
            rafRef.current = requestAnimationFrame(flushMessages);
          }
        } catch { /* skip malformed */ }
      };

      ws.onclose = () => {
        setConnected(false);
        reconnectRef.current = setTimeout(connect, 3000);
      };

      ws.onerror = () => ws.close();
    } catch {
      setConnected(false);
      reconnectRef.current = setTimeout(connect, 5000);
    }
  }, [flushMessages]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectRef.current);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { connected, ws: wsRef };
}

function useApi<T>(endpoint: string, interval: number = 5000, initial: T): T {
  const [data, setData] = useState<T>(initial);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(endpoint);
        if (res.ok) setData(await res.json());
      } catch { /* silent */ }
    };
    fetchData();
    const id = setInterval(fetchData, interval);
    return () => clearInterval(id);
  }, [endpoint, interval]);

  return data;
}

function useElapsed(since: number): string {
  const [elapsed, setElapsed] = useState("0:00");
  useEffect(() => {
    if (!since) return;
    const tick = () => {
      const secs = Math.max(0, Math.floor(Date.now() / 1000 - since));
      const m = Math.floor(secs / 60);
      const s = secs % 60;
      setElapsed(`${m}:${String(s).padStart(2, "0")}`);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [since]);
  return elapsed;
}

/* ════════════════════════════════════════════════════════════════════
   GLASS CARD — the fundamental UI surface
   ════════════════════════════════════════════════════════════════════ */

function Glass({
  children, className = "", tier = "standard", critical = false, onClick, layoutId,
}: {
  children: React.ReactNode; className?: string;
  tier?: "subtle" | "standard" | "prominent"; critical?: boolean;
  onClick?: () => void; layoutId?: string;
}) {
  const glassClass = critical ? "glass-critical" : `glass-${tier}`;
  const Wrapper = layoutId ? motion.div : "div";
  const props: Record<string, unknown> = {
    className: `rounded-2xl relative overflow-hidden glass-highlight ${glassClass} ${onClick ? "cursor-pointer transition-all duration-300 hover:scale-[1.01]" : ""} ${className}`,
    onClick,
    ...(layoutId ? { layoutId, transition: { type: "spring", stiffness: 400, damping: 30 } } : {}),
  };

  return <Wrapper {...props}>{children}</Wrapper>;
}

/* ════════════════════════════════════════════════════════════════════
   SMALL COMPONENTS
   ════════════════════════════════════════════════════════════════════ */

function StatusDot({ severity, pulse = false }: { severity: string; pulse?: boolean }) {
  const s = SEVERITY[severity] || SEVERITY.MEDIUM;
  return (
    <span className="relative flex items-center justify-center w-3 h-3">
      {pulse && <span className={`absolute inset-0 rounded-full ${s.dot} opacity-30 animate-ping`} />}
      <span className={`w-2 h-2 rounded-full ${s.dot}`} />
    </span>
  );
}

function SeverityBadge({ severity }: { severity: string }) {
  const s = SEVERITY[severity] || SEVERITY.MEDIUM;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-bold tracking-wider ${s.bg} ${s.text} ${s.border} border`}>
      <span className={`w-1.5 h-1.5 rounded-full ${s.dot}`} />
      {s.label}
    </span>
  );
}

function RoleBadge({ role }: { role: string }) {
  const r = ROLES[role] || ROLES.UNKNOWN;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-bold tracking-wider ${r.bg} ${r.text}`}>
      {r.label}
    </span>
  );
}

function VerificationBadge({ label }: { label: string }) {
  // Parse "[VERIFIED ✓ 85%] Some intel text" or "[CONTRADICTED ✗ — reason] text"
  const match = label.match(/^\[(VERIFIED|CONTRADICTED|PENDING|UNVERIFIED)[^\]]*\]/);
  if (!match) return null;
  const status = match[1].toLowerCase();
  const v = status === "verified" ? VERIFICATION.entailment
    : status === "contradicted" ? VERIFICATION.contradiction
    : status === "pending" ? VERIFICATION.pending
    : VERIFICATION.neutral;
  const { Icon } = v;

  // Extract confidence percentage if present (e.g., "85%" from "[VERIFIED ✓ 85%]")
  const confMatch = label.match(/(\d+)%/);
  const confidence = confMatch ? confMatch[1] + "%" : null;

  // Extract contradiction reason (e.g., "reason" from "[CONTRADICTED ✗ — reason]")
  const reasonMatch = label.match(/^\[CONTRADICTED[^\]]*—\s*([^\]]+)\]/);
  const reason = reasonMatch ? reasonMatch[1].trim() : null;

  return (
    <span className="inline-flex flex-col gap-0.5">
      <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold ${v.bg} ${v.color}`}>
        <Icon className="w-3 h-3" />
        {v.label}
        {confidence && <span className="font-mono opacity-80">{confidence}</span>}
      </span>
      {reason && (
        <span className="text-[9px] text-red-400/80 italic leading-tight pl-1">
          {reason}
        </span>
      )}
    </span>
  );
}

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 80 ? "bg-emerald-500" : pct >= 50 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
        <motion.div
          className={`h-full rounded-full ${color}`}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        />
      </div>
      <span className="font-mono text-[11px] text-gray-400 w-8 text-right">{pct}%</span>
    </div>
  );
}

function LiveIndicator({ connected }: { connected: boolean }) {
  return (
    <div className="flex items-center gap-2">
      {connected ? (
        <>
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-50" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500" />
          </span>
          <span className="text-xs font-medium text-emerald-400">LIVE</span>
        </>
      ) : (
        <>
          <WifiOff className="w-3.5 h-3.5 text-red-400" />
          <span className="text-xs font-medium text-red-400">RECONNECTING</span>
        </>
      )}
    </div>
  );
}

function AnimatedNumber({ value, className = "" }: { value: number; className?: string }) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    const start = display;
    const diff = value - start;
    if (diff === 0) return;
    const duration = 400;
    const startTime = performance.now();
    const step = (now: number) => {
      const progress = Math.min((now - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
      setDisplay(Math.round(start + diff * eased));
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [value]);
  return <span className={className}>{display}</span>;
}

/* ════════════════════════════════════════════════════════════════════
   STAT CARDS — top row of the dashboard
   ════════════════════════════════════════════════════════════════════ */

function StatCard({ icon: Icon, label, value, accent = "text-blue-400", sub }: {
  icon: typeof Activity; label: string; value: number; accent?: string; sub?: string;
}) {
  return (
    <Glass tier="standard" className="p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase">{label}</p>
          <p className={`text-3xl font-bold font-mono mt-1.5 tabular-nums ${accent}`}>
            <AnimatedNumber value={value} />
          </p>
          {sub && <p className="text-[11px] text-gray-500 mt-1">{sub}</p>}
        </div>
        <div className="p-2.5 rounded-xl bg-white/[0.04]">
          <Icon className={`w-5 h-5 ${accent}`} />
        </div>
      </div>
    </Glass>
  );
}

/* ════════════════════════════════════════════════════════════════════
   INCIDENT CARD — left sidebar feed
   ════════════════════════════════════════════════════════════════════ */

function IncidentCard({
  incident, selected, onSelect,
}: {
  incident: Incident; selected: boolean; onSelect: () => void;
}) {
  const s = SEVERITY[incident.severity] || SEVERITY.MEDIUM;
  const elapsed = useElapsed(incident.timeline?.[0]?.time || 0);
  const callerCount = incident.caller_count || Object.keys(incident.callers || {}).length;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ type: "spring", stiffness: 500, damping: 35 }}
    >
      <Glass
        tier={selected ? "prominent" : "standard"}
        critical={incident.severity === "CRITICAL"}
        onClick={onSelect}
        className={`p-4 ${s.stripe} ${selected ? "ring-1 ring-blue-500/30" : ""}`}
      >
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2">
            <StatusDot severity={incident.severity} pulse={incident.status === "active"} />
            <span className="text-sm font-semibold text-white truncate max-w-[160px]">
              {incident.incident_type?.replace(/_/g, " ").toUpperCase() || "UNKNOWN"}
            </span>
          </div>
          <SeverityBadge severity={incident.severity} />
        </div>

        <div className="flex items-center gap-1.5 text-xs text-gray-400 mb-2">
          <MapPin className="w-3 h-3 shrink-0" />
          <span className="truncate">{incident.location || "Unknown location"}</span>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1 text-xs text-gray-500">
              <Users className="w-3 h-3" />
              {callerCount}
            </span>
            <span className="flex items-center gap-1 text-xs text-gray-500">
              <Clock className="w-3 h-3" />
              <span className="font-mono">{elapsed}</span>
            </span>
          </div>
          {incident.children_involved && (
            <span className="text-[10px] font-bold text-red-400 bg-red-500/15 px-1.5 py-0.5 rounded">
              CHILDREN
            </span>
          )}
          {incident.merged_caller_count > 0 && (
            <span className="flex items-center gap-1 text-[10px] font-bold text-cyan-300 bg-cyan-500/15 px-1.5 py-0.5 rounded" title={`Deduplication confidence: ${Math.round(incident.dedup_confidence * 100)}%`}>
              <GitMerge className="w-3 h-3" />
              {Math.round(incident.dedup_confidence * 100)}%
            </span>
          )}
        </div>
      </Glass>
    </motion.div>
  );
}

/* ════════════════════════════════════════════════════════════════════
   INCIDENT DETAIL — center panel
   ════════════════════════════════════════════════════════════════════ */

function IncidentDetail({ incident }: { incident: Incident }) {
  const callers = Object.values(incident.callers || {});
  const timeline = [...(incident.timeline || [])].reverse().slice(0, 20);
  const elapsed = useElapsed(incident.timeline?.[0]?.time || 0);

  return (
    <motion.div
      key={incident.id}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="space-y-4 overflow-y-auto max-h-[calc(100vh-220px)] pr-1"
    >
      {/* Header */}
      <Glass tier="prominent" className="p-5">
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h2 className="text-lg font-bold text-white">
                {incident.incident_type?.replace(/_/g, " ").toUpperCase()}
              </h2>
              <SeverityBadge severity={incident.severity} />
            </div>
            <div className="flex items-center gap-1.5 text-sm text-gray-400">
              <MapPin className="w-3.5 h-3.5" />
              {incident.location}
            </div>
          </div>
          <div className="text-right">
            <p className="font-mono text-2xl font-bold text-white tabular-nums">{elapsed}</p>
            <p className="text-[10px] text-gray-500 tracking-wider">ELAPSED</p>
          </div>
        </div>

        {incident.summary && (
          <p className="text-sm text-gray-300 leading-relaxed">{incident.summary}</p>
        )}

        {incident.dispatched_units?.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {incident.dispatched_units.map((unit, i) => (
              <span key={i} className="text-[10px] font-bold text-cyan-300 bg-cyan-500/15 px-2 py-0.5 rounded-md">
                {unit}
              </span>
            ))}
          </div>
        )}

        {incident.children_involved && (
          <div className="mt-3 flex items-center gap-2 p-2.5 rounded-lg bg-red-500/10 border border-red-500/20">
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
            <span className="text-xs font-bold text-red-300 tracking-wider">CHILDREN INVOLVED</span>
          </div>
        )}

        {/* Dedup confidence badge */}
        {incident.merged_caller_count > 0 && (
          <div className="mt-3 flex items-center gap-3 p-2.5 rounded-lg bg-cyan-500/8 border border-cyan-500/15">
            <GitMerge className="w-4 h-4 text-cyan-400 shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-bold text-cyan-300 tracking-wider">
                  INCIDENT MATCH: {Math.round(incident.dedup_confidence * 100)}%
                </span>
                <span className="text-[10px] text-gray-500">
                  ({incident.merged_caller_count} caller{incident.merged_caller_count > 1 ? "s" : ""} merged)
                </span>
              </div>
              <ConfidenceBar value={incident.dedup_confidence} />
            </div>
          </div>
        )}
      </Glass>

      {/* Callers Grid */}
      {callers.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-2 px-1">
            Active Callers ({callers.length})
          </h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            {callers.map((caller) => (
              <CallerCard key={caller.id} caller={caller} />
            ))}
          </div>
        </div>
      )}

      {/* Suspect Info */}
      {incident.suspect && Object.keys(incident.suspect).length > 0 && (
        <Glass tier="standard" className="p-4">
          <h3 className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-3">
            Suspect Information
          </h3>
          <div className="space-y-1.5">
            {Object.entries(incident.suspect).map(([key, value]) => (
              <div key={key} className="flex justify-between text-sm">
                <span className="text-gray-400 capitalize">{key.replace(/_/g, " ")}</span>
                <span className="text-white font-medium">{String(value)}</span>
              </div>
            ))}
          </div>
        </Glass>
      )}

      {/* Timeline */}
      {timeline.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-2 px-1">
            Timeline
          </h3>
          <Glass tier="subtle" className="p-4">
            <div className="space-y-3">
              {timeline.map((event, i) => (
                <TimelineItem key={i} event={event} isFirst={i === 0} />
              ))}
            </div>
          </Glass>
        </div>
      )}
    </motion.div>
  );
}

function CallerCard({ caller }: { caller: CallerInfo }) {
  return (
    <Glass tier="standard" className="p-3.5">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-white/[0.06] flex items-center justify-center">
            <UserCircle2 className="w-5 h-5 text-gray-400" />
          </div>
          <div>
            <p className="text-sm font-semibold text-white">{caller.name || caller.id}</p>
            <div className="flex items-center gap-1.5 mt-0.5">
              <RoleBadge role={caller.role} />
              <span className={`text-[10px] ${caller.status === "on_call" ? "text-emerald-400" : "text-gray-500"}`}>
                {caller.status === "on_call" ? "● ON CALL" : "○ " + caller.status?.toUpperCase()}
              </span>
            </div>
          </div>
        </div>
      </div>

      {caller.location && (
        <div className="flex items-center gap-1 text-xs text-gray-400 mb-2">
          <MapPin className="w-3 h-3" />
          {caller.location}
        </div>
      )}

      {caller.emotional_state && caller.emotional_state !== "unknown" && (
        <span className="text-[10px] text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded">
          {caller.emotional_state.toUpperCase()}
        </span>
      )}

      {/* Child-safe voice flag */}
      {caller.role === "CHILD" && (
        <div className="mt-2 flex items-center gap-1.5 p-2 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
          <Volume2 className="w-3.5 h-3.5 text-yellow-400 shrink-0" />
          <span className="text-[10px] font-bold text-yellow-300 tracking-wider">
            CHILD CALLER — SIMPLIFIED LANGUAGE ACTIVE
          </span>
        </div>
      )}

      {caller.key_intel?.length > 0 && (
        <div className="mt-2 space-y-1">
          {caller.key_intel.slice(-3).map((intel, i) => (
            <div key={i} className="flex items-start gap-1.5">
              <VerificationBadge label={intel} />
              <p className="text-[11px] text-gray-300 leading-tight">
                {intel.replace(/^\[.*?\]\s*/, "")}
              </p>
            </div>
          ))}
        </div>
      )}
    </Glass>
  );
}

function TimelineItem({ event, isFirst }: { event: TimelineEvent; isFirst: boolean }) {
  const time = new Date(event.time * 1000);
  const timeStr = time.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  const hasVerification = event.event?.startsWith("[");
  const isSystem = event.source === "system";
  const verification = event.verification as Record<string, unknown> | undefined;

  return (
    <div className="flex gap-3">
      <div className="flex flex-col items-center shrink-0">
        <div className={`w-2 h-2 rounded-full mt-1.5 ${isFirst ? "bg-blue-400" : "bg-white/20"}`} />
        <div className="w-px flex-1 bg-white/[0.06]" />
      </div>
      <div className="pb-3 min-w-0">
        <div className="flex items-center gap-2 mb-0.5 flex-wrap">
          <span className="font-mono text-[10px] text-gray-500">{timeStr}</span>
          {!isSystem && (
            <span className="text-[10px] text-gray-500">
              via {event.source}
            </span>
          )}
          {hasVerification && <VerificationBadge label={event.event} />}
          {verification && typeof verification.confidence === "number" && (verification.confidence as number) > 0 && (
            <span className="font-mono text-[10px] text-gray-500">
              conf: {Math.round((verification.confidence as number) * 100)}%
            </span>
          )}
          {verification && typeof verification.latency_ms === "number" && (
            <span className="font-mono text-[10px] text-gray-600">
              {verification.latency_ms}ms
            </span>
          )}
        </div>
        <p className="text-sm text-gray-300 leading-relaxed">
          {event.event?.replace(/^\[.*?\]\s*/, "") || "Event"}
        </p>
        {/* Show contradiction explanation if present */}
        {verification && (verification as Record<string, unknown>).contradiction_details ? (
          <p className="text-[11px] text-red-400/80 italic mt-0.5 leading-tight">
            Reason: {String((verification as Record<string, unknown>).contradiction_details)}
          </p>
        ) : null}
      </div>
    </div>
  );
}

/* ════════════════════════════════════════════════════════════════════
   VERIFYLAYER PANEL — right sidebar
   ════════════════════════════════════════════════════════════════════ */

function VerifyLayerPanel({ cacheStats }: { cacheStats: CacheStats }) {
  return (
    <div className="space-y-4">
      <Glass tier="standard" className="p-4">
        <div className="flex items-center gap-2 mb-4">
          <Shield className="w-4 h-4 text-blue-400" />
          <h3 className="text-xs font-bold tracking-widest text-gray-400 uppercase">VerifyLayer</h3>
        </div>

        <div className="space-y-3">
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-gray-500">Cache Hit Rate</span>
              <span className="font-mono text-emerald-400">{Math.round(cacheStats.hit_rate * 100)}%</span>
            </div>
            <ConfidenceBar value={cacheStats.hit_rate} />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="p-2.5 rounded-lg bg-white/[0.03]">
              <p className="text-[10px] text-gray-500 tracking-wider">CACHE HITS</p>
              <p className="text-lg font-bold font-mono text-emerald-400 tabular-nums">
                <AnimatedNumber value={cacheStats.hits} />
              </p>
            </div>
            <div className="p-2.5 rounded-lg bg-white/[0.03]">
              <p className="text-[10px] text-gray-500 tracking-wider">MISSES</p>
              <p className="text-lg font-bold font-mono text-amber-400 tabular-nums">
                <AnimatedNumber value={cacheStats.misses} />
              </p>
            </div>
            <div className="p-2.5 rounded-lg bg-white/[0.03]">
              <p className="text-[10px] text-gray-500 tracking-wider">CACHE SIZE</p>
              <p className="text-lg font-bold font-mono text-blue-400 tabular-nums">
                {cacheStats.size}/{cacheStats.max_size}
              </p>
            </div>
            <div className="p-2.5 rounded-lg bg-white/[0.03]">
              <p className="text-[10px] text-gray-500 tracking-wider">EVICTIONS</p>
              <p className="text-lg font-bold font-mono text-gray-400 tabular-nums">
                <AnimatedNumber value={cacheStats.evictions} />
              </p>
            </div>
          </div>
        </div>
      </Glass>

      <Glass tier="subtle" className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <Cpu className="w-4 h-4 text-purple-400" />
          <h3 className="text-xs font-bold tracking-widest text-gray-400 uppercase">Pipeline</h3>
        </div>
        <div className="space-y-2">
          {[
            { label: "NLI Engine", sub: "Gemini 2.0 Flash", color: "text-blue-400" },
            { label: "Contradiction Detector", sub: "Cross-call pairwise", color: "text-purple-400" },
            { label: "Penalization Engine", sub: "Confidence scoring", color: "text-cyan-400" },
            { label: "LRU Cache", sub: "Thread-safe async", color: "text-emerald-400" },
          ].map((item, i) => (
            <div key={i} className="flex items-center gap-2.5 p-2 rounded-lg bg-white/[0.02]">
              <div className={`w-1.5 h-1.5 rounded-full ${item.color.replace("text-", "bg-")}`} />
              <div className="min-w-0">
                <p className="text-xs font-medium text-gray-300">{item.label}</p>
                <p className="text-[10px] text-gray-500">{item.sub}</p>
              </div>
            </div>
          ))}
        </div>
      </Glass>
    </div>
  );
}

/* ════════════════════════════════════════════════════════════════════
   VOICE CALL PANEL — live 911 call via Gemini Live API
   ════════════════════════════════════════════════════════════════════ */

function VoiceCallPanel({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [status, setStatus] = useState<"idle" | "connecting" | "active" | "ended">("idle");
  const [sessionId, setSessionId] = useState<string>("");
  const [incidentId, setIncidentId] = useState<string>("");
  const [transcripts, setTranscripts] = useState<{ speaker: string; text: string }[]>([]);
  const [isMuted, setIsMuted] = useState(false);
  const isMutedRef = useRef(false);
  const wsRef = useRef<WebSocket | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const playQueueRef = useRef<{ buffer: ArrayBuffer; sampleRate: number }[]>([]);
  const isPlayingRef = useRef(false);
  const transcriptEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll transcripts
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [transcripts]);

  const startCall = async () => {
    try {
      // 1. Get microphone access FIRST (before any state changes)
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { sampleRate: 16000, channelCount: 1, echoCancellation: true, noiseSuppression: true },
      });
      mediaStreamRef.current = stream;

      // 2. Now update UI state
      setStatus("connecting");
      setTranscripts([]);

      // 3. Set up AudioContext for mic capture
      const audioCtx = new AudioContext({ sampleRate: 16000 });
      audioContextRef.current = audioCtx;
      const source = audioCtx.createMediaStreamSource(stream);
      const processor = audioCtx.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;

      // 3. Connect to voice WebSocket
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const ws = new WebSocket(`${protocol}//${window.location.host}/ws/voice`);
      wsRef.current = ws;

      ws.onopen = () => {
        // Start session
        ws.send(JSON.stringify({
          type: "start_session",
          caller_name: "Live Caller",
          caller_role: "REPORTING_PARTY",
          location: "Live call from dashboard",
          description: "Live 911 call via browser microphone",
        }));
      };

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);

        if (msg.type === "session_started") {
          setSessionId(msg.session_id);
          setIncidentId(msg.incident_id);
          setStatus("active");

          // Start streaming mic audio
          source.connect(processor);
          processor.connect(audioCtx.destination);
          processor.onaudioprocess = (e) => {
            if (isMutedRef.current) return;
            const pcmData = e.inputBuffer.getChannelData(0);
            // Convert Float32 to Int16
            const int16 = new Int16Array(pcmData.length);
            for (let i = 0; i < pcmData.length; i++) {
              const s = Math.max(-1, Math.min(1, pcmData[i]));
              int16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
            }
            // Base64 encode and send
            const bytes = new Uint8Array(int16.buffer);
            const binary = Array.from(bytes).map(b => String.fromCharCode(b)).join("");
            const b64 = btoa(binary);
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({ type: "audio", data: b64 }));
            }
          };

          setTranscripts(prev => [...prev, { speaker: "system", text: "Connected to Nexus911. Speak now." }]);
        }

        if (msg.type === "audio") {
          // Decode and play agent audio
          playAudioChunk(msg.data, msg.mime_type || "audio/pcm");
        }

        if (msg.type === "transcript") {
          setTranscripts(prev => [...prev, { speaker: msg.speaker || "agent", text: msg.text }]);
        }

        if (msg.type === "tool_call") {
          setTranscripts(prev => [...prev, {
            speaker: "system",
            text: `[${msg.tool}] ${JSON.stringify(msg.args || {}).slice(0, 100)}`,
          }]);
        }

        if (msg.type === "error") {
          setTranscripts(prev => [...prev, { speaker: "system", text: `Error: ${msg.message}` }]);
          setStatus("ended");
        }

        if (msg.type === "session_ended") {
          setStatus("ended");
        }
      };

      ws.onerror = () => {
        setTranscripts(prev => [...prev, { speaker: "system", text: "WebSocket connection error" }]);
        setStatus("ended");
      };

      ws.onclose = () => {
        if (status === "active") {
          setStatus("ended");
        }
      };

    } catch (err) {
      setTranscripts(prev => [...prev, { speaker: "system", text: `Mic error: ${err}` }]);
      setStatus("idle");
    }
  };

  const playAudioChunk = (b64Data: string, mimeType: string) => {
    try {
      const binary = atob(b64Data);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);

      // Parse sample rate from mime_type (e.g. "audio/pcm;rate=24000")
      const rateMatch = mimeType.match(/rate=(\d+)/);
      const sampleRate = rateMatch ? parseInt(rateMatch[1], 10) : 24000;

      // Queue audio for sequential playback
      playQueueRef.current.push({ buffer: bytes.buffer, sampleRate });
      if (!isPlayingRef.current) {
        playNextChunk();
      }
    } catch { /* silent */ }
  };

  const playNextChunk = async () => {
    const ctx = audioContextRef.current;
    if (!ctx || playQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      return;
    }
    isPlayingRef.current = true;
    const { buffer, sampleRate } = playQueueRef.current.shift()!;

    try {
      // Try decoding as audio
      const audioBuffer = await ctx.decodeAudioData(buffer.slice(0));
      const source = ctx.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(ctx.destination);
      source.onended = () => playNextChunk();
      source.start();
    } catch {
      // If decoding fails, treat as raw PCM 16-bit mono at the detected sample rate
      const int16 = new Int16Array(buffer);
      const float32 = new Float32Array(int16.length);
      for (let i = 0; i < int16.length; i++) float32[i] = int16[i] / 32768;

      const audioBuffer = ctx.createBuffer(1, float32.length, sampleRate);
      audioBuffer.getChannelData(0).set(float32);
      const source = ctx.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(ctx.destination);
      source.onended = () => playNextChunk();
      source.start();
    }
  };

  const endCall = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "end_session" }));
      wsRef.current.close();
    }
    if (processorRef.current) processorRef.current.disconnect();
    if (mediaStreamRef.current) mediaStreamRef.current.getTracks().forEach(t => t.stop());
    if (audioContextRef.current) audioContextRef.current.close();
    setStatus("ended");
  };

  const handleClose = () => {
    if (status === "active") endCall();
    setStatus("idle");
    onClose();
  };

  if (!open) return null;

  const speakerStyles: Record<string, string> = {
    agent: "text-blue-300",
    caller: "text-green-300",
    system: "text-gray-500 italic",
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      onClick={handleClose}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-lg"
      >
        <Glass tier="prominent" className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <PhoneCall className="w-5 h-5 text-green-400" />
              <h2 className="text-lg font-bold text-white">Live 911 Call</h2>
              {status === "active" && (
                <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-red-500/20 text-red-400 text-[10px] font-bold">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
                  LIVE
                </span>
              )}
            </div>
            <button onClick={handleClose} className="p-1.5 rounded-lg hover:bg-white/[0.06] transition-colors">
              <X className="w-4 h-4 text-gray-400" />
            </button>
          </div>

          {incidentId && (
            <p className="text-[10px] text-gray-500 mb-3 font-mono">Incident: {incidentId}</p>
          )}

          {/* Transcript area */}
          <div className="h-64 overflow-y-auto mb-4 p-3 rounded-lg bg-black/30 border border-white/[0.06] space-y-2">
            {transcripts.length === 0 && status === "idle" && (
              <p className="text-gray-600 text-sm text-center mt-20">Click "Start Call" to connect to a Nexus911 agent</p>
            )}
            {transcripts.map((t, i) => (
              <div key={i} className={`text-sm ${speakerStyles[t.speaker] || "text-gray-300"}`}>
                <span className="font-bold text-[10px] uppercase tracking-wider opacity-60">
                  {t.speaker === "agent" ? "911 Operator" : t.speaker === "caller" ? "You" : ""}
                </span>
                {t.speaker !== "system" && <br />}
                {t.text}
              </div>
            ))}
            <div ref={transcriptEndRef} />
          </div>

          {/* Controls */}
          <div className="flex items-center gap-3">
            {status === "idle" || status === "ended" ? (
              <button
                onClick={startCall}
                className="flex-1 py-3 rounded-xl bg-green-600 hover:bg-green-500 text-sm font-bold text-white transition-colors flex items-center justify-center gap-2"
              >
                <PhoneCall className="w-4 h-4" />
                {status === "ended" ? "Call Again" : "Start Call"}
              </button>
            ) : status === "connecting" ? (
              <button disabled className="flex-1 py-3 rounded-xl bg-yellow-600/50 text-sm font-bold text-white flex items-center justify-center gap-2">
                <RefreshCw className="w-4 h-4 animate-spin" />
                Connecting...
              </button>
            ) : (
              <>
                <button
                  onClick={() => { isMutedRef.current = !isMuted; setIsMuted(!isMuted); }}
                  className={`p-3 rounded-xl border transition-colors ${
                    isMuted ? "bg-red-500/20 border-red-500/40 text-red-400" : "bg-white/[0.05] border-white/[0.1] text-white"
                  }`}
                >
                  {isMuted ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                </button>
                <button
                  onClick={endCall}
                  className="flex-1 py-3 rounded-xl bg-red-600 hover:bg-red-500 text-sm font-bold text-white transition-colors flex items-center justify-center gap-2"
                >
                  <PhoneCall className="w-4 h-4" />
                  End Call
                </button>
              </>
            )}
          </div>
        </Glass>
      </motion.div>
    </motion.div>
  );
}

/* ════════════════════════════════════════════════════════════════════
   SIMULATE CALL MODAL — dispatch-center-style per-caller monitoring
   ════════════════════════════════════════════════════════════════════ */

interface ScenarioInfo {
  name: string;
  title: string;
  caller_count: number;
  severity: string;
  incident_type: string;
}

interface CallerDialog {
  name: string;
  role: string;
  status: "waiting" | "connecting" | "active" | "completed" | "error";
  transcripts: { speaker: string; text: string }[];
  duration?: number;
}

function SimulateModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [scenarios, setScenarios] = useState<ScenarioInfo[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [mode, setMode] = useState<"voice" | "text">("voice");
  const [loading, setLoading] = useState(false);
  const [simStatus, setSimStatus] = useState<string>("");
  const [callerDialogs, setCallerDialogs] = useState<Map<string, CallerDialog>>(new Map());
  const [unmutedCaller, setUnmutedCaller] = useState<string | null>(null);
  const unmutedCallerRef = useRef<string | null>(null);
  const [globalEvents, setGlobalEvents] = useState<string[]>([]);

  // Per-caller audio: only the unmuted caller's audio plays
  const simAudioCtxRef = useRef<AudioContext | null>(null);
  const simAudioQueueRef = useRef<{ buffer: ArrayBuffer; sampleRate: number }[]>([]);
  const simIsPlayingRef = useRef(false);
  const transcriptEndRefs = useRef<Map<string, HTMLDivElement | null>>(new Map());

  // Keep ref in sync with state
  useEffect(() => { unmutedCallerRef.current = unmutedCaller; }, [unmutedCaller]);

  // Auto-scroll transcripts when new messages arrive
  useEffect(() => {
    callerDialogs.forEach((_, name) => {
      const el = transcriptEndRefs.current.get(name);
      el?.scrollIntoView({ behavior: "smooth" });
    });
  }, [callerDialogs]);

  // Fetch available scenarios on mount
  useEffect(() => {
    if (open) {
      fetch("/api/simulation/scenarios")
        .then((r) => r.json())
        .then((d) => {
          setScenarios(d.scenarios || []);
          if (d.scenarios?.length && !selected) setSelected(d.scenarios[0].name);
        })
        .catch(() => {});
    }
  }, [open]);

  // Connect to simulation WebSocket for live events
  useEffect(() => {
    if (!loading) return;

    if (!simAudioCtxRef.current) {
      simAudioCtxRef.current = new AudioContext();
    }

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/simulation`);

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        const callerName: string = msg.caller || "";

        if (msg.type === "caller_waiting" || msg.type === "caller_connecting") {
          setCallerDialogs((prev) => {
            const next = new Map(prev);
            if (!next.has(callerName)) {
              next.set(callerName, {
                name: callerName,
                role: msg.role || "",
                status: "waiting",
                transcripts: [],
              });
            } else {
              const d = { ...next.get(callerName)! };
              d.status = msg.type === "caller_connecting" ? "connecting" : "waiting";
              next.set(callerName, d);
            }
            return next;
          });
        } else if (msg.type === "caller_connected") {
          setCallerDialogs((prev) => {
            const next = new Map(prev);
            const existing = next.get(callerName);
            next.set(callerName, {
              name: callerName,
              role: msg.role || existing?.role || "",
              status: "active",
              transcripts: existing?.transcripts || [],
            });
            return next;
          });
          setGlobalEvents((prev) => [...prev, `${callerName} connected`]);
        } else if (msg.type === "transcript") {
          setCallerDialogs((prev) => {
            const next = new Map(prev);
            const existing = next.get(callerName);
            if (existing) {
              const updated = { ...existing };
              updated.transcripts = [...updated.transcripts, { speaker: msg.speaker, text: msg.text }];
              next.set(callerName, updated);
            }
            return next;
          });
        } else if (msg.type === "audio") {
          // Only play if this caller is unmuted
          if (callerName === unmutedCallerRef.current) {
            playSimAudio(msg.data, msg.mime_type || "audio/pcm;rate=24000");
          }
        } else if (msg.type === "caller_completed") {
          setCallerDialogs((prev) => {
            const next = new Map(prev);
            const existing = next.get(callerName);
            if (existing) {
              next.set(callerName, { ...existing, status: "completed", duration: msg.duration });
            }
            return next;
          });
          setGlobalEvents((prev) => [...prev, `${callerName} completed (${msg.duration?.toFixed(1)}s)`]);
        } else if (msg.type === "caller_error") {
          setCallerDialogs((prev) => {
            const next = new Map(prev);
            const existing = next.get(callerName);
            if (existing) {
              next.set(callerName, { ...existing, status: "error" });
            }
            return next;
          });
        } else if (msg.type === "intel_submitted") {
          setGlobalEvents((prev) => [...prev, `[Intel] ${msg.intel}`]);
        } else if (msg.type === "tool_call") {
          setCallerDialogs((prev) => {
            const next = new Map(prev);
            const existing = next.get(callerName);
            if (existing) {
              const updated = { ...existing };
              updated.transcripts = [...updated.transcripts, { speaker: "system", text: `Tool: ${msg.tool}` }];
              next.set(callerName, updated);
            }
            return next;
          });
        } else if (msg.type === "units_dispatched") {
          setGlobalEvents((prev) => [...prev, `DISPATCH: ${(msg.units || []).join(", ")}`]);
        } else if (msg.type === "dedup_merged") {
          setGlobalEvents((prev) => [...prev, `DEDUP: ${callerName} merged into incident`]);
        } else if (msg.type === "simulation_completed") {
          setLoading(false);
          setSimStatus(`Completed in ${msg.total_duration?.toFixed(1)}s — ${msg.callers_completed} callers processed`);
        }
      } catch { /* silent */ }
    };

    return () => {
      ws.close();
      if (simAudioCtxRef.current) {
        simAudioCtxRef.current.close();
        simAudioCtxRef.current = null;
      }
      simAudioQueueRef.current = [];
      simIsPlayingRef.current = false;
    };
  }, [loading]);

  const playSimAudio = (b64Data: string, mimeType: string) => {
    try {
      const binary = atob(b64Data);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
      const rateMatch = mimeType.match(/rate=(\d+)/);
      const sampleRate = rateMatch ? parseInt(rateMatch[1], 10) : 24000;
      simAudioQueueRef.current.push({ buffer: bytes.buffer, sampleRate });
      if (!simIsPlayingRef.current) playNextSimChunk();
    } catch { /* silent */ }
  };

  const playNextSimChunk = () => {
    const ctx = simAudioCtxRef.current;
    if (!ctx || simAudioQueueRef.current.length === 0) {
      simIsPlayingRef.current = false;
      return;
    }
    simIsPlayingRef.current = true;
    const { buffer, sampleRate } = simAudioQueueRef.current.shift()!;
    const int16 = new Int16Array(buffer);
    const float32 = new Float32Array(int16.length);
    for (let i = 0; i < int16.length; i++) float32[i] = int16[i] / 32768;
    const audioBuffer = ctx.createBuffer(1, float32.length, sampleRate);
    audioBuffer.getChannelData(0).set(float32);
    const source = ctx.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(ctx.destination);
    source.onended = () => playNextSimChunk();
    source.start();
  };

  const toggleMute = (callerName: string) => {
    if (unmutedCaller === callerName) {
      // Mute this caller
      setUnmutedCaller(null);
      // Flush audio queue when muting
      simAudioQueueRef.current = [];
      simIsPlayingRef.current = false;
    } else {
      // Unmute this caller (auto-mutes the previous one)
      setUnmutedCaller(callerName);
      // Flush audio queue from previous caller
      simAudioQueueRef.current = [];
      simIsPlayingRef.current = false;
    }
  };

  const startSimulation = async () => {
    if (!selected) return;
    setLoading(true);
    setSimStatus("Starting simulation...");
    setCallerDialogs(new Map());
    setGlobalEvents([]);
    setUnmutedCaller(null);
    try {
      const r = await fetch("/api/simulation/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario: selected, mode }),
      });
      const d = await r.json();
      if (r.ok) {
        setSimStatus(d.message || "Simulation started");
      } else {
        setSimStatus(`Error: ${d.detail || "Failed to start"}`);
        setLoading(false);
      }
    } catch {
      setSimStatus("Error: Could not connect to server");
      setLoading(false);
    }
  };

  const stopSimulation = async () => {
    try {
      await fetch("/api/simulation/stop", { method: "POST" });
    } catch {}
    setLoading(false);
    setSimStatus("Simulation stopped");
    setUnmutedCaller(null);
    simAudioQueueRef.current = [];
    simIsPlayingRef.current = false;
    if (simAudioCtxRef.current) {
      simAudioCtxRef.current.close();
      simAudioCtxRef.current = null;
    }
  };

  if (!open) return null;

  const selectedScenario = scenarios.find((s) => s.name === selected);
  const severityColor: Record<string, string> = {
    CRITICAL: "text-red-400", HIGH: "text-orange-400", MEDIUM: "text-yellow-400", LOW: "text-green-400",
  };
  const statusColor: Record<string, string> = {
    waiting: "text-yellow-400", connecting: "text-blue-400", active: "text-green-400",
    completed: "text-gray-500", error: "text-red-400",
  };
  const statusDot: Record<string, string> = {
    waiting: "bg-yellow-400", connecting: "bg-blue-400 animate-pulse", active: "bg-green-400 animate-pulse",
    completed: "bg-gray-500", error: "bg-red-400",
  };
  const dialogs = Array.from(callerDialogs.values());
  const isRunning = loading && dialogs.length > 0;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
        className={`w-full ${isRunning ? "max-w-5xl" : "max-w-lg"} max-h-[90vh] overflow-y-auto transition-all duration-300`}
      >
        <Glass tier="prominent" className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              {isRunning ? <Radio className="w-5 h-5 text-green-400 animate-pulse" /> : <Play className="w-5 h-5 text-blue-400" />}
              <h2 className="text-lg font-bold text-white">
                {isRunning ? "Dispatch Center — Active Simulation" : "Run Scenario Simulation"}
              </h2>
            </div>
            <div className="flex items-center gap-2">
              {loading && (
                <button
                  onClick={stopSimulation}
                  className="px-3 py-1.5 rounded-lg bg-red-600/80 hover:bg-red-600 text-xs font-bold text-white transition-colors flex items-center gap-1.5"
                >
                  <X className="w-3 h-3" />
                  Stop
                </button>
              )}
              <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-white/[0.06] transition-colors">
                <X className="w-4 h-4 text-gray-400" />
              </button>
            </div>
          </div>

          {/* ── Pre-launch: Scenario & Mode Selection ── */}
          {!isRunning && (
            <>
              <div className="mb-4">
                <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-2">Select Scenario</p>
                <div className="space-y-2">
                  {scenarios.map((s) => (
                    <button
                      key={s.name}
                      onClick={() => setSelected(s.name)}
                      className={`w-full text-left p-3 rounded-lg border transition-colors ${
                        selected === s.name
                          ? "bg-blue-600/15 border-blue-500/40"
                          : "bg-white/[0.03] border-white/[0.06] hover:bg-white/[0.06]"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium text-white">{s.title}</p>
                        <span className={`text-[10px] font-bold ${severityColor[s.severity] || "text-gray-400"}`}>
                          {s.severity}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 mt-1">
                        <span className="text-[10px] text-gray-500">{s.caller_count} callers</span>
                        <span className="text-[10px] text-gray-500">{s.incident_type}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="mb-4">
                <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-2">Simulation Mode</p>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => setMode("voice")}
                    className={`p-3 rounded-lg border text-center transition-colors ${
                      mode === "voice"
                        ? "bg-purple-600/15 border-purple-500/40"
                        : "bg-white/[0.03] border-white/[0.06] hover:bg-white/[0.06]"
                    }`}
                  >
                    <Volume2 className={`w-4 h-4 mx-auto mb-1 ${mode === "voice" ? "text-purple-400" : "text-gray-500"}`} />
                    <p className="text-xs font-medium text-white">Voice (Live API)</p>
                    <p className="text-[10px] text-gray-500 mt-0.5">Gemini-to-Gemini audio</p>
                  </button>
                  <button
                    onClick={() => setMode("text")}
                    className={`p-3 rounded-lg border text-center transition-colors ${
                      mode === "text"
                        ? "bg-cyan-600/15 border-cyan-500/40"
                        : "bg-white/[0.03] border-white/[0.06] hover:bg-white/[0.06]"
                    }`}
                  >
                    <Cpu className={`w-4 h-4 mx-auto mb-1 ${mode === "text" ? "text-cyan-400" : "text-gray-500"}`} />
                    <p className="text-xs font-medium text-white">Text (Fallback)</p>
                    <p className="text-[10px] text-gray-500 mt-0.5">Direct pipeline test</p>
                  </button>
                </div>
              </div>

              {simStatus && (
                <div className="mb-4 p-3 rounded-lg bg-white/[0.03] border border-white/[0.06]">
                  <p className="text-xs text-gray-300">{simStatus}</p>
                </div>
              )}

              <div className="space-y-2">
                <button
                  onClick={startSimulation}
                  disabled={!selected || loading}
                  className="w-full py-3 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-sm font-bold text-white transition-colors flex items-center justify-center gap-2"
                >
                  {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                  {loading ? "Starting..." : `Run ${selectedScenario ? `"${selectedScenario.title}"` : "Scenario"}`}
                  {selectedScenario && !loading && <span className="text-blue-200 font-normal">({selectedScenario.caller_count} callers)</span>}
                </button>
                <button
                  onClick={stopSimulation}
                  className="w-full py-2 rounded-lg bg-white/[0.04] hover:bg-red-600/30 border border-white/[0.08] hover:border-red-500/40 text-xs font-medium text-gray-400 hover:text-red-300 transition-colors flex items-center justify-center gap-1.5"
                >
                  <X className="w-3 h-3" />
                  Force Stop All Simulations
                </button>
              </div>
            </>
          )}

          {/* ── Active Simulation: Per-Caller Dispatch Board ── */}
          {isRunning && (
            <>
              {/* Caller cards grid */}
              <div className={`grid gap-4 mb-4 ${dialogs.length <= 2 ? "grid-cols-1 sm:grid-cols-2" : "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3"}`}>
                {dialogs.map((dialog) => {
                  const isUnmuted = unmutedCaller === dialog.name;
                  const isActive = dialog.status === "active";
                  return (
                    <motion.div
                      key={dialog.name}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`rounded-xl border p-4 transition-all duration-200 ${
                        isUnmuted
                          ? "bg-green-600/10 border-green-500/50 ring-1 ring-green-500/30"
                          : dialog.status === "completed"
                          ? "bg-white/[0.02] border-white/[0.06] opacity-60"
                          : "bg-white/[0.03] border-white/[0.08]"
                      }`}
                    >
                      {/* Card header */}
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2 min-w-0">
                          <div className={`w-2 h-2 rounded-full flex-shrink-0 ${statusDot[dialog.status] || "bg-gray-500"}`} />
                          <div className="min-w-0">
                            <p className="text-sm font-semibold text-white truncate">{dialog.name}</p>
                            <p className="text-[10px] text-gray-500 uppercase tracking-wider">{dialog.role}</p>
                          </div>
                        </div>
                        {/* Mute/Unmute button */}
                        {(isActive || dialog.status === "completed") && mode === "voice" && (
                          <button
                            onClick={() => toggleMute(dialog.name)}
                            className={`p-2 rounded-lg transition-all ${
                              isUnmuted
                                ? "bg-green-500/20 text-green-400 hover:bg-green-500/30 ring-1 ring-green-500/40"
                                : "bg-white/[0.06] text-gray-500 hover:bg-white/[0.1] hover:text-white"
                            }`}
                            title={isUnmuted ? "Mute this caller" : "Listen to this caller"}
                          >
                            {isUnmuted ? <Volume2 className="w-4 h-4" /> : <MicOff className="w-4 h-4" />}
                          </button>
                        )}
                      </div>

                      {/* Status badge */}
                      <div className="mb-2">
                        <span className={`text-[10px] font-bold uppercase tracking-wider ${statusColor[dialog.status] || "text-gray-400"}`}>
                          {dialog.status}
                          {dialog.duration != null && ` — ${dialog.duration.toFixed(1)}s`}
                        </span>
                      </div>

                      {/* Transcript feed */}
                      <div className="h-36 overflow-y-auto rounded-lg bg-black/30 border border-white/[0.06] p-2 space-y-1 font-mono text-[11px]">
                        {dialog.transcripts.length === 0 && (
                          <div className="flex items-center justify-center h-full text-gray-600 text-[10px]">
                            {dialog.status === "waiting" ? "Waiting to connect..." : dialog.status === "connecting" ? "Connecting..." : "No transcript yet"}
                          </div>
                        )}
                        {dialog.transcripts.map((t, i) => (
                          <div key={i} className={
                            t.speaker === "agent" ? "text-blue-300" :
                            t.speaker === "system" ? "text-purple-400/70 italic" :
                            "text-amber-200"
                          }>
                            <span className="text-gray-600 mr-1">{t.speaker === "agent" ? "NEXUS:" : t.speaker === "system" ? "SYS:" : "CALLER:"}</span>
                            {t.text}
                          </div>
                        ))}
                        <div ref={(el) => { transcriptEndRefs.current.set(dialog.name, el); }} />
                      </div>

                      {/* Listening indicator */}
                      {isUnmuted && isActive && (
                        <div className="mt-2 flex items-center gap-1.5 text-green-400">
                          <Volume2 className="w-3 h-3" />
                          <span className="text-[10px] font-semibold uppercase tracking-wider animate-pulse">Listening</span>
                          {/* Audio bars animation */}
                          <div className="flex items-end gap-0.5 ml-auto h-3">
                            {[1, 2, 3, 4].map((n) => (
                              <div
                                key={n}
                                className="w-0.5 bg-green-400 rounded-full animate-pulse"
                                style={{ height: `${4 + Math.random() * 8}px`, animationDelay: `${n * 0.15}s` }}
                              />
                            ))}
                          </div>
                        </div>
                      )}
                    </motion.div>
                  );
                })}
              </div>

              {/* Global event log (collapsed) */}
              {globalEvents.length > 0 && (
                <div className="mb-4">
                  <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-2">System Events</p>
                  <div className="h-24 overflow-y-auto p-2 rounded-lg bg-black/20 border border-white/[0.06] space-y-0.5 font-mono text-[10px]">
                    {globalEvents.map((ev, i) => (
                      <div key={i} className={
                        ev.startsWith("DISPATCH") ? "text-green-400 font-bold" :
                        ev.startsWith("DEDUP") ? "text-cyan-400" :
                        ev.startsWith("[Intel]") ? "text-yellow-300/70" :
                        ev.includes("completed") ? "text-gray-500" :
                        ev.includes("connected") ? "text-blue-400" :
                        "text-gray-400"
                      }>{ev}</div>
                    ))}
                  </div>
                </div>
              )}

              {/* Status bar */}
              <div className="flex items-center justify-between p-3 rounded-lg bg-white/[0.03] border border-white/[0.06]">
                <div className="flex items-center gap-3">
                  <RefreshCw className="w-3.5 h-3.5 text-green-400 animate-spin" />
                  <span className="text-xs text-gray-300">{simStatus}</span>
                </div>
                <div className="flex items-center gap-2 text-[10px] text-gray-500">
                  <span>{dialogs.filter((d) => d.status === "active").length} active</span>
                  <span>·</span>
                  <span>{dialogs.filter((d) => d.status === "completed").length} done</span>
                </div>
              </div>
            </>
          )}
        </Glass>
      </motion.div>
    </motion.div>
  );
}

/* ════════════════════════════════════════════════════════════════════
   HERO SECTION — cinematic landing
   ════════════════════════════════════════════════════════════════════ */

function HeroSection({ onEnter }: { onEnter: () => void }) {
  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden">
      {/* Animated gradient mesh */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 -left-48 w-[500px] h-[500px] bg-blue-600/15 rounded-full blur-[100px] animate-gradient-shift" />
        <div className="absolute bottom-1/4 -right-48 w-[500px] h-[500px] bg-purple-600/10 rounded-full blur-[100px] animate-gradient-shift" style={{ animationDelay: "-7s" }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] bg-cyan-600/8 rounded-full blur-[120px] animate-gradient-shift" style={{ animationDelay: "-14s" }} />
      </div>

      {/* Dot grid overlay */}
      <div className="absolute inset-0 opacity-30" style={{
        backgroundImage: "radial-gradient(rgba(255,255,255,0.08) 1px, transparent 1px)",
        backgroundSize: "48px 48px",
      }} />

      {/* Content */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="relative z-10 text-center px-6 max-w-4xl mx-auto"
      >
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass-subtle mb-8"
        >
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
          <span className="text-[11px] font-semibold text-gray-300 tracking-widest">
            GEMINI LIVE AGENT CHALLENGE 2026
          </span>
        </motion.div>

        {/* Title */}
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.7 }}
          className="font-display text-7xl sm:text-8xl lg:text-9xl font-black tracking-tighter leading-[0.85] mb-6"
        >
          <span className="block text-white">NEXUS</span>
          <span className="block text-gradient">911</span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="text-lg sm:text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed mb-3"
        >
          Autonomous multi-agent emergency dispatch with
          <span className="text-white font-semibold"> real-time hallucination verification</span>
        </motion.p>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="text-sm text-gray-500 max-w-xl mx-auto mb-10"
        >
          3 callers · 3 AI agents · 1 verified incident · 20 seconds
        </motion.p>

        {/* CTA */}
        <motion.button
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.98 }}
          onClick={onEnter}
          className="group inline-flex items-center gap-3 px-8 py-4 rounded-2xl bg-white/[0.08] border border-white/[0.12] hover:bg-white/[0.12] transition-all duration-300 text-white font-semibold"
        >
          <Siren className="w-5 h-5 text-blue-400" />
          Enter Command Center
          <ArrowRight className="w-4 h-4 text-gray-400 group-hover:translate-x-1 transition-transform" />
        </motion.button>

        {/* Tech badges */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.9 }}
          className="flex items-center justify-center gap-4 mt-12 flex-wrap"
        >
          {["Gemini Live API", "Google ADK", "Cloud Run", "VerifyLayer", "FastAPI"].map((tech) => (
            <span key={tech} className="text-[10px] font-semibold tracking-widest text-gray-600 uppercase">
              {tech}
            </span>
          ))}
        </motion.div>
      </motion.div>

      {/* Scroll indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.2 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2"
      >
        <motion.div
          animate={{ y: [0, 8, 0] }}
          transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
        >
          <ChevronDown className="w-6 h-6 text-gray-600" />
        </motion.div>
      </motion.div>
    </section>
  );
}

/* ════════════════════════════════════════════════════════════════════
   DASHBOARD — the operational command center
   ════════════════════════════════════════════════════════════════════ */

function Dashboard({
  incidents, stats, cacheStats, wsConnected, selectedId, onSelect,
}: {
  incidents: Incident[]; stats: Stats; cacheStats: CacheStats;
  wsConnected: boolean; selectedId: string | null; onSelect: (id: string | null) => void;
}) {
  const [showSimulate, setShowSimulate] = useState(false);
  const [showVoiceCall, setShowVoiceCall] = useState(false);

  const sortedIncidents = useMemo(() => {
    const order: Record<string, number> = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
    return [...incidents].sort((a, b) => {
      const sa = a.status === "active" ? 0 : 1;
      const sb = b.status === "active" ? 0 : 1;
      if (sa !== sb) return sa - sb;
      return (order[a.severity] ?? 9) - (order[b.severity] ?? 9);
    });
  }, [incidents]);

  const selectedIncident = incidents.find((i) => i.id === selectedId) || null;

  return (
    <motion.section
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="min-h-screen bg-surface-base"
    >
      {/* Top Bar */}
      <header className="sticky top-0 z-40 glass-subtle px-6 py-3">
        <div className="flex items-center justify-between max-w-[1800px] mx-auto">
          <div className="flex items-center gap-4">
            <h1 className="font-display text-lg font-black tracking-tight text-white">
              NEXUS<span className="text-gradient">911</span>
            </h1>
            <div className="h-4 w-px bg-white/[0.1]" />
            <LiveIndicator connected={wsConnected} />
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowVoiceCall(true)}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-green-600/20 border border-green-500/30 hover:bg-green-600/30 transition-colors text-sm font-semibold text-green-300"
            >
              <PhoneCall className="w-4 h-4" />
              Call 911
            </button>
            <button
              onClick={() => setShowSimulate(true)}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600/20 border border-blue-500/30 hover:bg-blue-600/30 transition-colors text-sm font-semibold text-blue-300"
            >
              <Play className="w-4 h-4" />
              Run Scenario
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-[1800px] mx-auto px-6 py-5">
        {/* Stats Row */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <StatCard icon={Siren} label="Active Incidents" value={stats.active_incidents} accent="text-red-400" sub={`${stats.total_incidents} total`} />
          <StatCard icon={Users} label="Connected Callers" value={stats.total_callers} accent="text-blue-400" />
          <StatCard icon={AlertTriangle} label="Critical" value={stats.critical_incidents} accent="text-orange-400" />
          <StatCard icon={ShieldCheck} label="Cache Hit Rate" value={Math.round(cacheStats.hit_rate * 100)} accent="text-emerald-400" sub={`${cacheStats.hits + cacheStats.misses} total checks`} />
        </div>

        {/* Main 3-Column Layout */}
        <div className="grid grid-cols-12 gap-5">
          {/* Left: Incident Feed */}
          <div className="col-span-12 lg:col-span-3">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-xs font-bold tracking-widest text-gray-500 uppercase">
                Incidents ({incidents.length})
              </h2>
              <button
                onClick={() => setShowSimulate(true)}
                className="p-1.5 rounded-lg hover:bg-white/[0.06] transition-colors"
                title="Simulate call"
              >
                <Plus className="w-4 h-4 text-gray-500" />
              </button>
            </div>

            <div className="space-y-3 overflow-y-auto max-h-[calc(100vh-280px)] pr-1">
              <AnimatePresence mode="popLayout">
                {sortedIncidents.length > 0 ? (
                  sortedIncidents.map((inc) => (
                    <IncidentCard
                      key={inc.id}
                      incident={inc}
                      selected={inc.id === selectedId}
                      onSelect={() => onSelect(inc.id === selectedId ? null : inc.id)}
                    />
                  ))
                ) : (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-center py-12"
                  >
                    <Radio className="w-8 h-8 text-gray-600 mx-auto mb-3" />
                    <p className="text-sm text-gray-500">No active incidents</p>
                    <p className="text-xs text-gray-600 mt-1">Simulate a call to get started</p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>

          {/* Center: Detail View */}
          <div className="col-span-12 lg:col-span-6">
            <AnimatePresence mode="wait">
              {selectedIncident ? (
                <IncidentDetail key={selectedIncident.id} incident={selectedIncident} />
              ) : (
                <motion.div
                  key="empty"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex flex-col items-center justify-center h-[60vh]"
                >
                  <div className="p-6 rounded-3xl bg-white/[0.02] mb-6">
                    <Eye className="w-12 h-12 text-gray-700" />
                  </div>
                  <p className="text-lg font-semibold text-gray-600 mb-2">Select an incident</p>
                  <p className="text-sm text-gray-700 max-w-xs text-center">
                    Choose an incident from the feed to see callers, intel, verification status, and timeline
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Right: VerifyLayer Panel */}
          <div className="col-span-12 lg:col-span-3">
            <h2 className="text-xs font-bold tracking-widest text-gray-500 uppercase mb-3">
              Verification Engine
            </h2>
            <VerifyLayerPanel cacheStats={cacheStats} />
          </div>
        </div>
      </div>

      <AnimatePresence>
        {showSimulate && <SimulateModal open={showSimulate} onClose={() => setShowSimulate(false)} />}
        {showVoiceCall && <VoiceCallPanel open={showVoiceCall} onClose={() => setShowVoiceCall(false)} />}
      </AnimatePresence>
    </motion.section>
  );
}

/* ════════════════════════════════════════════════════════════════════
   APP — root component with hero → dashboard transition
   ════════════════════════════════════════════════════════════════════ */

export default function App() {
  const [view, setView] = useState<"hero" | "dashboard">("hero");
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const stats = useApi<Stats>("/api/stats", 5000, {
    total_incidents: 0, active_incidents: 0, total_callers: 0, critical_incidents: 0,
  });
  const cacheStats = useApi<CacheStats>("/api/verify/cache/stats", 5000, {
    hits: 0, misses: 0, size: 0, max_size: 1024, hit_rate: 0, evictions: 0,
  });

  // WebSocket handler — updates incidents in real time
  const handleWsMessage = useCallback((msg: WSMessage) => {
    if (msg.type === "all_incidents" && msg.data) {
      setIncidents(Object.values(msg.data as Record<string, Incident>));
    } else if (msg.type === "incident_created" || msg.type === "incident_updated") {
      const updated = msg.data as Incident;
      setIncidents((prev) => {
        const exists = prev.find((i) => i.id === updated.id);
        return exists
          ? prev.map((i) => (i.id === updated.id ? updated : i))
          : [updated, ...prev];
      });
    }
  }, []);

  const { connected } = useWebSocket(handleWsMessage);

  const enterDashboard = useCallback(() => setView("dashboard"), []);

  return (
    <div className="bg-surface-base min-h-screen">
      <AnimatePresence mode="wait">
        {view === "hero" ? (
          <motion.div
            key="hero"
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.5 }}
          >
            <HeroSection onEnter={enterDashboard} />
          </motion.div>
        ) : (
          <motion.div
            key="dashboard"
            initial={{ opacity: 0, scale: 1.02 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          >
            <Dashboard
              incidents={incidents}
              stats={stats}
              cacheStats={cacheStats}
              wsConnected={connected}
              selectedId={selectedId}
              onSelect={setSelectedId}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ════════════════════════════════════════════════════════════════════
   DASHBOARD PAGE — self-contained dashboard for direct routing
   ════════════════════════════════════════════════════════════════════ */

export function DashboardPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const stats = useApi<Stats>("/api/stats", 5000, {
    total_incidents: 0, active_incidents: 0, total_callers: 0, critical_incidents: 0,
  });
  const cacheStats = useApi<CacheStats>("/api/verify/cache/stats", 5000, {
    hits: 0, misses: 0, size: 0, max_size: 1024, hit_rate: 0, evictions: 0,
  });

  const handleWsMessage = useCallback((msg: WSMessage) => {
    if (msg.type === "all_incidents" && msg.data) {
      setIncidents(Object.values(msg.data as Record<string, Incident>));
    } else if (msg.type === "incident_created" || msg.type === "incident_updated") {
      const updated = msg.data as Incident;
      setIncidents((prev) => {
        const exists = prev.find((i) => i.id === updated.id);
        return exists
          ? prev.map((i) => (i.id === updated.id ? updated : i))
          : [updated, ...prev];
      });
    }
  }, []);

  const { connected } = useWebSocket(handleWsMessage);

  return (
    <div className="bg-surface-base min-h-screen">
      <Dashboard
        incidents={incidents}
        stats={stats}
        cacheStats={cacheStats}
        wsConnected={connected}
        selectedId={selectedId}
        onSelect={setSelectedId}
      />
    </div>
  );
}
