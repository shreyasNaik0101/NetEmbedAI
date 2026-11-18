import { useEffect, useRef, useState } from "react";
type Packet = { iat_ms: number; direction: 1 | -1; payload_bytes: number };
type Prediction = {
  status: string;
  label: string | null;
  alternatives: { label: string; score: number }[];
  pipeline_ms: number;
  observed_packets: number;
  model_packets?: number;
  model_prefix_limit?: number;
  artifact_id: string;
  policy_fitted?: boolean;
  policy_scope?: string;
  decision_reason?: string;
  queue_ms?: number;
  capture_to_event_ms?: number;
};
type Reference = { status: string; label: string | null; reason?: string };
type Observation = {
  version: string;
  quality: string;
  windows: {
    horizon_ms: number;
    state: string;
    client_packets: number;
    server_packets: number;
    client_bytes: number;
    server_bytes: number;
    mean_payload_bytes: number;
    late_packets_after_elapsed_snapshot: number;
  }[];
};
type Row = {
  packets: Packet[];
  prediction?: Prediction;
  reference?: Reference;
  observation?: Observation;
};
const icons = {
  activity: "M3 12h4l3-8 4 16 3-8h4",
  play: "m9 5 11 7-11 7V5Z",
  stop: "M6 6h12v12H6Z",
  network: "M12 3v6M5 15v-4h14v4M3 16h4v5H3Zm14 0h4v5h-4ZM10 2h4v5h-4Z",
  layers: "m12 3 10 6-10 6L2 9l10-6Zm-9 11 9 5 9-5M3 18l9 5 9-5",
  clock: "M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0ZM12 6v6l4 2",
  search: "M16 10a6 6 0 1 1-12 0 6 6 0 0 1 12 0Zm-1 5 6 6",
  file: "M14 2H5v20h14V7l-5-5Zm0 0v6h5M8 13h8m-8 4h6",
  chevron: "m9 5 7 7-7 7",
  info: "M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0ZM12 11v6m0-10v1",
  arrow: "M5 12h14m-6-6 6 6-6 6",
  check: "m5 12 4 4L19 6",
};
function Icon({ name }: { name: keyof typeof icons }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={icons[name]} />
    </svg>
  );
}
function serviceName(label: string) {
  const names: Record<string, string> = {
    youtube: "YouTube",
    instagram: "Instagram",
    spotify: "Spotify",
    tiktok: "TikTok",
    snapchat: "Snapchat",
    whatsapp: "WhatsApp",
    discord: "Discord",
    "facebook-messenger": "Messenger",
    "google-drive": "Google Drive",
    "microsoft-outlook": "Outlook",
  };
  return names[label] ?? label;
}
function bytes(value: number) {
  return value < 1024
    ? value + " B"
    : value < 1048576
      ? (value / 1024).toFixed(1) + " KB"
      : (value / 1048576).toFixed(1) + " MB";
}
function interfaceName(description: string) {
  const start = description.indexOf(" (");
  return description.startsWith("\\Device\\") &&
    start >= 0 &&
    description.endsWith(")")
    ? description.slice(start + 2, -1)
    : description;
}
function decisionText(prediction?: Prediction) {
  if (prediction?.label) return serviceName(prediction.label);
  if (prediction?.decision_reason === "policy_not_fitted")
    return "Confidence check pending";
  if (prediction?.decision_reason === "outside_policy_scope")
    return "Service outside this acceptance policy";
  if (prediction?.status === "insufficient_confidence")
    return "No confident match yet";
  if (prediction?.status === "insufficient_evidence")
    return "Still collecting packets";
  return prediction?.status.replaceAll("_", " ") ?? "Waiting for evidence";
}
function captureReason(reason: unknown) {
  const names: Record<string, string> = {
    idle: "Ready when you are",
    "event stream disconnected": "App connection lost",
    "viewer conflict": "Another app window is connected",
    "capture duration limit reached": "Two-minute session complete",
    "stopped by user": "Session stopped",
    "viewer disconnected": "Session ended after viewer disconnected",
    "viewer heartbeat expired":
      "Session ended after the app stopped responding",
    "viewer message too large": "Session ended after an invalid viewer message",
    "capture process exited": "Capture process ended",
  };
  return names[String(reason)] ?? String(reason ?? "Capture is off");
}
const api = import.meta.env.DEV ? "/api" : "";
async function request(path: string, body?: unknown) {
  const r = await fetch(api + path, {
    method: body === undefined ? "GET" : "POST",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await r.json();
  if (!r.ok)
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : JSON.stringify(data.detail),
    );
  return data;
}
export default function App() {
  const [mode, setMode] = useState<"Live" | "Replay">("Live");
  const [model, setModel] = useState<{
    artifact_id: string;
    labels: string[];
    kind?: string;
    architecture?: { fixed_prefix_packets?: number };
    policy?: { fitted: boolean; validation_scope?: string; note?: string };
  } | null>(null);
  const [modelLoading, setModelLoading] = useState(true);
  const [interfaces, setInterfaces] = useState<
    { id: string; description: string }[]
  >([]);
  const [iface, setIface] = useState("");
  const [referenceCheck, setReferenceCheck] = useState(() => {
    try {
      return sessionStorage.getItem("netembed-reference-check") === "true";
    } catch {
      return false;
    }
  });
  useEffect(() => {
    try {
      sessionStorage.setItem(
        "netembed-reference-check",
        String(referenceCheck),
      );
    } catch {
      /* Storage can be unavailable; the visible checkbox still works. */
    }
  }, [referenceCheck]);
  const [windowCheck, setWindowCheck] = useState(false);
  const [connected, setConnected] = useState(false);
  const [connectionAttempt, setConnectionAttempt] = useState(0);
  const reconnectFailures = useRef(0);
  const [retryDelay, setRetryDelay] = useState<number | null>(null);
  const [status, setStatus] = useState<Record<string, unknown>>({
    running: false,
    reason: "idle",
  });
  const [error, setError] = useState("");
  const [rows, setRows] = useState<Record<string, Row>>({});
  const [selected, setSelected] = useState("");
  const [filter, setFilter] = useState("");
  const [showGuide, setShowGuide] = useState(false);
  const [text, setText] = useState("");
  const [replay, setReplay] = useState<Packet[]>([]);
  const [prefix, setPrefix] = useState(5);
  const [result, setResult] = useState<Prediction | null>(null);
  const [busy, setBusy] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [evaluation, setEvaluation] = useState<unknown>(null);
  const [sessionSummary, setSessionSummary] = useState<{
    browser_receipt_n: number;
    browser_receipt_p50_ms: number | null;
    browser_receipt_p95_ms: number | null;
    observation_receipt_n?: number;
    observation_receipt_p50_ms?: number | null;
    observation_receipt_p95_ms?: number | null;
  } | null>(null);
  useEffect(() => {
    if (selected && !rows[selected] && Object.keys(rows).length)
      setSelected(Object.keys(rows)[0]);
  }, [rows, selected]);
  const epoch = useRef(0);
  const socket = useRef<WebSocket | null>(null);
  const session = useRef<string | null>(null);
  const pendingRows = useRef<Record<string, Partial<Row>>>({});
  const rowFrame = useRef<number | null>(null);
  function clearPendingRows() {
    if (rowFrame.current !== null) cancelAnimationFrame(rowFrame.current);
    rowFrame.current = null;
    pendingRows.current = {};
  }
  useEffect(() => {
    request("/model")
      .then(setModel)
      .catch((e) => setError(e.message))
      .finally(() => setModelLoading(false));
    request("/capture/interfaces")
      .then(setInterfaces)
      .catch((e) => setError(e.message));
    request("/evaluation")
      .then(setEvaluation)
      .catch(() => {});
  }, []);
  useEffect(() => {
    const ws = new WebSocket(
      (location.protocol === "https:" ? "wss://" : "ws://") +
        location.host +
        api +
        "/capture/events",
    );
    socket.current = ws;
    let retryTimer: number | undefined;
    ws.onopen = () => {
      setConnected(true);
      if (ws.readyState === WebSocket.OPEN)
        ws.send(JSON.stringify({ type: "heartbeat" }));
    };
    ws.onclose = (event) => {
      setConnected(false);
      setStatus((s) => ({
        ...s,
        running: false,
        reason:
          event?.code === 4009
            ? "viewer conflict"
            : "event stream disconnected",
      }));
      if (event?.code === 4009) {
        setRetryDelay(null);
        return;
      }
      const delays = [500, 1000, 2000, 4000, 8000];
      const delay = delays[reconnectFailures.current++];
      if (delay !== undefined) {
        setRetryDelay(delay);
        retryTimer = window.setTimeout(() => {
          setRetryDelay(null);
          setConnectionAttempt((n) => n + 1);
        }, delay);
      }
    };
    ws.onmessage = (e) => {
      const receivedAt = Date.now() / 1000;
      const v = JSON.parse(e.data);
      if (v.type === "heartbeat") {
        if (ws.readyState === WebSocket.OPEN)
          ws.send(JSON.stringify({ type: "heartbeat" }));
        return;
      }
      if (v.type === "status") {
        reconnectFailures.current = 0;
        setStatus(v);
        return;
      }
      if (session.current && v.session_id !== session.current) return;
      if (
        v.type === "packets" ||
        v.type === "prediction" ||
        v.type === "observation"
      ) {
        if (
          (v.type === "prediction" || v.type === "observation") &&
          ws.readyState === WebSocket.OPEN
        )
          ws.send(
            JSON.stringify({
              session_id: v.session_id,
              event_type: v.type,
              sequence: v.sequence,
              received_at: receivedAt,
            }),
          );
        // Acknowledge each prediction/window on receipt, independently of paint.
        // Keep only the latest display update per flow during a packet burst.
        const pending = pendingRows.current;
        const priorPackets = pending[v.flow_id]?.packets;
        pending[v.flow_id] = {
          ...pending[v.flow_id],
          ...(v.type === "packets"
            ? { packets: v.packets }
            : v.type === "prediction"
              ? {
                  prediction: v,
                  ...(Array.isArray(v.packets) ? { packets: v.packets } : {}),
                }
              : { observation: v.observation }),
          ...(v.reference ? { reference: v.reference } : {}),
        };
        if (
          priorPackets &&
          priorPackets.length > (pending[v.flow_id].packets?.length ?? 0)
        )
          pending[v.flow_id].packets = priorPackets;
        while (Object.keys(pending).length > 256)
          delete pending[Object.keys(pending)[0]];
        if (rowFrame.current === null)
          rowFrame.current = requestAnimationFrame(() => {
            rowFrame.current = null;
            const updates = pendingRows.current;
            pendingRows.current = {};
            setRows((old) => {
              const next = { ...old };
              for (const [id, update] of Object.entries(updates))
                next[id] = {
                  ...old[id],
                  ...update,
                  packets:
                    (update.packets?.length ?? 0) >=
                    (old[id]?.packets?.length ?? 0)
                      ? (update.packets ?? old[id]?.packets ?? [])
                      : old[id].packets,
                };
              while (Object.keys(next).length > 256)
                delete next[Object.keys(next)[0]];
              return next;
            });
            setSelected((s) => s || Object.keys(updates)[0] || "");
          });
      }
    };
    return () => {
      window.clearTimeout(retryTimer);
      clearPendingRows();
      ws.onclose = null;
      ws.onmessage = null;
      ws.onopen = null;
      ws.close();
    };
  }, [connectionAttempt]);
  useEffect(() => {
    if (status.running !== false || typeof status.session_id !== "string")
      return;
    let cancelled = false;
    const id = status.session_id;
    request("/capture/summary")
      .then((summary) => {
        if (!cancelled && summary.session_id === id) setSessionSummary(summary);
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
      });
    return () => {
      cancelled = true;
    };
  }, [status.running, status.session_id]);
  useEffect(() => {
    if (!playing) return;
    const timer = setInterval(
      () =>
        setPrefix((p) => {
          if (p >= replay.length) {
            setPlaying(false);
            return p;
          }
          return p + 1;
        }),
      700,
    );
    return () => clearInterval(timer);
  }, [playing, replay.length]);
  useEffect(() => {
    if (mode !== "Replay" || !replay.length) return;
    const ticket = ++epoch.current;
    setBusy(true);
    setResult(null);
    request("/predict", {
      schema_version: "1",
      packets: replay.slice(0, prefix),
    })
      .then((r) => {
        if (ticket === epoch.current) setResult(r);
      })
      .catch((e) => {
        if (ticket === epoch.current) setError(e.message);
      })
      .finally(() => {
        if (ticket === epoch.current) setBusy(false);
      });
    return () => {
      epoch.current++;
    };
  }, [mode, replay, prefix]);
  const current: Row | undefined =
    mode === "Live"
      ? rows[selected]
      : { packets: replay.slice(0, prefix), prediction: result ?? undefined };
  const packets = current?.packets ?? [];
  const prediction = current?.prediction;
  const reference = current?.reference;
  const flowEntries = Object.entries(rows);
  const visibleFlows = flowEntries.filter(([id, row]) =>
    [id, row.prediction?.label ?? "", row.prediction?.status ?? "collecting"]
      .join(" ")
      .toLowerCase()
      .includes(filter.toLowerCase().trim()),
  );
  const sentBytes = packets.reduce(
    (sum, p) => sum + (p.direction === 1 ? p.payload_bytes : 0),
    0,
  );
  const receivedBytes = packets.reduce(
    (sum, p) => sum + (p.direction === -1 ? p.payload_bytes : 0),
    0,
  );
  const running = Boolean(status.running);
  const recentSessions = Array.isArray(status.recent_sessions)
    ? (status.recent_sessions as {
        session_id: string;
        reason: string;
        connections: number;
        retained_packets: number;
      }[])
    : [];
  async function start() {
    setBusy(true);
    setError("");
    clearPendingRows();
    setRows({});
    setSelected("");
    setFilter("");
    setSessionSummary(null);
    session.current = null;
    try {
      const s = await request("/capture/start", {
        interface: iface,
        duration_seconds: 120,
        reference_check: referenceCheck,
        observation_windows: windowCheck,
      });
      clearPendingRows();
      session.current = s.session_id;
      setStatus(s);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }
  async function stop() {
    try {
      setStatus(await request("/capture/stop", {}));
    } catch (e) {
      setError(String(e));
    }
  }
  async function downloadEvidence(windows = false, savedSession?: string) {
    try {
      const evidence = await request(
        savedSession
          ? "/capture/recent-sessions/" + encodeURIComponent(savedSession)
          : windows
            ? "/capture/windows"
            : "/capture/local-evaluation",
      );
      const url = URL.createObjectURL(
        new Blob([JSON.stringify(evidence, null, 2)], {
          type: "application/json",
        }),
      );
      const link = document.createElement("a");
      link.href = url;
      link.download = `netembed-${savedSession ? "saved" : windows ? "windows" : "local"}-${evidence.session_id}.json`;
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 0);
    } catch (e) {
      setError(String(e));
    }
  }
  function load() {
    try {
      const parsed = JSON.parse(text);
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed))
        throw Error("Paste a JSON object containing recorded packets.");
      if (parsed.schema_version !== undefined && parsed.schema_version !== "1")
        throw Error('This recording needs schema_version "1".');
      if (
        !Array.isArray(parsed.packets) ||
        parsed.packets.length < 1 ||
        parsed.packets.length > 30
      )
        throw Error("Provide 1–30 recorded packets");
      for (const [index, packet] of parsed.packets.entries()) {
        if (!packet || typeof packet !== "object")
          throw Error("Packet " + (index + 1) + " must be an object.");
        if (!Number.isFinite(packet.iat_ms) || packet.iat_ms < 0)
          throw Error(
            "Packet " +
              (index + 1) +
              " needs a finite, nonnegative interval in milliseconds.",
          );
        if (packet.direction !== 1 && packet.direction !== -1)
          throw Error("Packet " + (index + 1) + " needs direction 1 or -1.");
        if (
          !Number.isInteger(packet.payload_bytes) ||
          packet.payload_bytes < 1 ||
          packet.payload_bytes > 65527
        )
          throw Error(
            "Packet " +
              (index + 1) +
              " needs a whole payload size from 1 to 65,527 bytes.",
          );
      }
      if (parsed.packets[0].iat_ms !== 0)
        throw Error("The first packet must have a zero interval.");
      setReplay(parsed.packets);
      setPrefix(Math.min(5, parsed.packets.length));
      setError("");
    } catch (e) {
      setError(String(e));
    }
  }
  return (
    <main className="app-shell">
      <header className="topbar">
        <a
          className="wordmark"
          href="#main-content"
          aria-label="NetEmbedAI home"
        >
          <span className="brand">
            <Icon name="activity" />
          </span>
          <span>
            NetEmbed<span className="brand-accent">AI</span>
            <small>LOCAL TRAFFIC EXPLORER</small>
          </span>
        </a>
        <div className="topbar-actions">
          <span className={"connection-pill " + (connected ? "connected" : "")}>
            <i />
            {connected
              ? "Stream connected"
              : retryDelay !== null
                ? "Reconnecting…"
                : status.reason === "viewer conflict"
                  ? "Another window connected"
                  : status.reason === "event stream disconnected"
                    ? "Stream disconnected"
                    : "Connecting…"}
          </span>
          {!connected &&
            ["event stream disconnected", "viewer conflict"].includes(
              String(status.reason),
            ) && (
              <button
                className="quiet-button"
                onClick={() => {
                  reconnectFailures.current = 0;
                  setRetryDelay(null);
                  setStatus((s) => ({ ...s, reason: "connecting" }));
                  setConnectionAttempt((n) => n + 1);
                }}
              >
                Reconnect
              </button>
            )}
          <button
            className="quiet-button"
            aria-expanded={showGuide}
            aria-controls="quick-guide"
            onClick={() => setShowGuide((v) => !v)}
          >
            <Icon name="info" />
            How to use
          </button>
        </div>
      </header>

      <section className="page-heading" id="main-content">
        <div>
          <p className="eyebrow">YOUR NETWORK, A CLOSER LOOK</p>
          <h1>Traffic, made visible.</h1>
          <p className="intro">
            Follow the packets. Explore the patterns. See which supported
            service a connection resembles.
          </p>
        </div>
        <nav aria-label="Analysis mode">
          {(["Live", "Replay"] as const).map((m) => (
            <button
              key={m}
              aria-pressed={mode === m}
              disabled={m === "Replay" && running}
              onClick={() => {
                setMode(m);
                setPlaying(false);
              }}
            >
              <Icon name={m === "Live" ? "activity" : "file"} />
              {m === "Live" ? "Live capture" : "Recorded replay"}
            </button>
          ))}
        </nav>
      </section>

      {showGuide && (
        <section
          className="quick-guide"
          id="quick-guide"
          aria-label="Getting started"
        >
          <div>
            <span className="step-number">1</span>
            <p>
              <strong>Choose your connection</strong>
              <span>
                Use Wi-Fi for wireless browsing, or Ethernet for a cable
                connection.
              </span>
            </p>
          </div>
          <div>
            <span className="step-number">2</span>
            <p>
              <strong>Start, then browse</strong>
              <span>
                Press Start capture before opening a fresh supported website
                connection.
              </span>
            </p>
          </div>
          <div>
            <span className="step-number">3</span>
            <p>
              <strong>Explore a connection</strong>
              <span>
                A flow is one connection. Select one to inspect its first 30
                packets and model estimate; other flows may belong to different
                services.
              </span>
            </p>
          </div>
        </section>
      )}

      {error && (
        <div className="error" role="alert">
          <Icon name="info" />
          <div>
            <strong>Something needs attention</strong>
            <span>{error}</span>
          </div>
          <button onClick={() => setError("")} aria-label="Dismiss error">
            ×
          </button>
        </div>
      )}

      <section
        className="controls panel"
        aria-label={mode === "Live" ? "Capture setup" : "Replay setup"}
      >
        <div className="panel-heading">
          <div className="heading-with-icon">
            <span className="icon-tile">
              <Icon name={mode === "Live" ? "network" : "file"} />
            </span>
            <div>
              <h2>
                {mode === "Live" ? "Capture a session" : "Explore a recording"}
              </h2>
              <p>
                {mode === "Live"
                  ? "Your interface. Your Start button. A two-minute session."
                  : "Step through saved packets with the same model."}
              </p>
            </div>
          </div>
          <span
            className={
              "state-pill " + (running && mode === "Live" ? "active" : "")
            }
          >
            <i />
            {mode === "Replay"
              ? "Recorded data"
              : running
                ? "Capturing"
                : "Capture is off"}
          </span>
        </div>
        {mode === "Live" ? (
          <>
            <div className="capture-form">
              <label className="interface-field">
                Network interface
                <select
                  aria-label="Local interface"
                  value={iface}
                  disabled={running}
                  onChange={(e) => setIface(e.target.value)}
                >
                  <option value="">Select Wi-Fi or Ethernet…</option>
                  {interfaces.map((i) => (
                    <option key={i.id} value={i.id} title={i.description}>
                      {interfaceName(i.description)}
                    </option>
                  ))}
                </select>
              </label>
              <div className="capture-actions">
                <button
                  className="primary"
                  disabled={!iface || !model || !connected || busy || running}
                  onClick={start}
                >
                  <Icon name="play" />
                  {busy ? "Starting…" : "Start capture"}
                </button>
                <button
                  className="stop-button"
                  disabled={!running}
                  onClick={stop}
                >
                  <Icon name="stop" />
                  Stop
                </button>
              </div>
              <div className="session-state" role="status">
                <span className={"status-dot " + (running ? "active" : "")} />
                <div>
                  <strong>
                    {running
                      ? "Listening for fresh QUIC traffic"
                      : captureReason(status.reason)}
                  </strong>
                  <small>
                    {status.error_detail
                      ? String(status.error_detail)
                      : !connected
                        ? status.reason === "viewer conflict"
                          ? "Close other NetEmbedAI tabs or VS Code previews, then click Reconnect here."
                          : status.reason === "event stream disconnected"
                            ? "Use one NetEmbedAI tab and refresh to reconnect."
                            : "Connecting to the local event stream…"
                        : !iface
                          ? "Choose the connection your browser uses."
                          : "Stops automatically after 2 minutes."}
                  </small>
                </div>
              </div>
            </div>
            <p className="setup-hint">
              {referenceCheck
                ? "Reference evidence ON for the next session. Remembered in this tab. "
                : "Reference evidence OFF: flow evidence for browser-matched studies will not be saved. Enable it below before Start. "}
            </p>
            <p className="setup-hint">
              <Icon name="info" />
              Start before opening new traffic. Only eligible QUIC connections
              appear; UDP/443 alone does not establish QUIC.
            </p>
            <details className="advanced">
              <summary>
                <span>
                  Optional research tools{" "}
                  <small>Reference checks & longer windows</small>
                </span>
                <Icon name="chevron" />
              </summary>
              <div className="advanced-grid">
                <div className="option-card">
                  <label className="reference-toggle">
                    <input
                      type="checkbox"
                      checked={referenceCheck}
                      disabled={running}
                      onChange={(e) => setReferenceCheck(e.target.checked)}
                    />
                    <span>
                      Check predictions against a separate handshake reference
                    </span>
                  </label>
                  <p className="hint">
                    Compare with a visible handshake name, when available. This
                    stays separate from the model and never changes its
                    prediction.
                  </p>
                </div>
                <div className="option-card">
                  <label className="reference-toggle">
                    <input
                      type="checkbox"
                      checked={windowCheck}
                      disabled={running}
                      onChange={(e) => setWindowCheck(e.target.checked)}
                    />
                    <span>Collect experimental 1- and 3-second statistics</span>
                  </label>
                  <p className="hint">
                    Count traffic beyond the first 30 packets. Descriptive
                    statistics only; no extra service or activity prediction.
                  </p>
                </div>
                <p className="hint advanced-note">
                  Options apply when you press Start. Up to 256 flow records
                  stay in memory until the next session. Evidence exports omit
                  hostnames, addresses and packet content; reference exports
                  include session connection tokens for an optional offline
                  Chrome NetLog check. Browser logging is separate.
                </p>
              </div>
            </details>
            {(Boolean(status.reference_enabled) ||
              Boolean(status.observation_windows_enabled)) &&
              !running && (
                <div className="export-actions">
                  <span>Keep a copy of this session</span>
                  {Boolean(status.reference_enabled) && (
                    <button onClick={() => downloadEvidence()}>
                      <Icon name="file" />
                      Download local trial evidence
                    </button>
                  )}
                  {Boolean(status.observation_windows_enabled) && (
                    <button onClick={() => downloadEvidence(true)}>
                      <Icon name="layers" />
                      Download observation windows
                    </button>
                  )}
                </div>
              )}
            {!running && recentSessions.length > 0 && (
              <details className="raw-evidence">
                <summary>
                  Recent stopped recordings ({recentSessions.length})
                </summary>
                <p className="hint">
                  The last three stopped recordings are kept in memory through
                  another Start. Download a copy to keep it after the service
                  closes.
                </p>
                <div className="export-actions">
                  {recentSessions.map((saved) => (
                    <button
                      key={saved.session_id}
                      onClick={() => downloadEvidence(false, saved.session_id)}
                    >
                      <Icon name="file" />
                      Save {saved.session_id.slice(0, 8)} · {saved.connections}{" "}
                      connections · {saved.retained_packets} packets ·{" "}
                      {captureReason(saved.reason)}
                    </button>
                  ))}
                </div>
              </details>
            )}
            {sessionSummary?.browser_receipt_n ||
            sessionSummary?.observation_receipt_n ? (
              <div className="delivery-summary">
                {sessionSummary?.browser_receipt_n ? (
                  <p className="hint">
                    Capture → browser receipt: p50{" "}
                    {sessionSummary.browser_receipt_p50_ms?.toFixed(1)} ms · p95{" "}
                    {sessionSummary.browser_receipt_p95_ms?.toFixed(1)} ms
                    across {sessionSummary.browser_receipt_n} acknowledged
                    predictions.
                  </p>
                ) : null}
                {sessionSummary?.observation_receipt_n ? (
                  <p className="hint">
                    Window event → browser receipt: p50{" "}
                    {sessionSummary.observation_receipt_p50_ms?.toFixed(1)} ms ·
                    p95 {sessionSummary.observation_receipt_p95_ms?.toFixed(1)}{" "}
                    ms across {sessionSummary.observation_receipt_n}{" "}
                    acknowledged updates. Starts at server emission; excludes
                    the observation wait and does not measure paint.
                  </p>
                ) : null}
              </div>
            ) : null}
          </>
        ) : (
          <>
            <div className="replay-form">
              <label className="recorded">
                Recorded flow JSON
                <textarea
                  aria-label="Recorded flow JSON"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="Paste a recorded flow with schema_version and packets"
                  spellCheck={false}
                  autoCorrect="off"
                  autoCapitalize="off"
                />
              </label>
              <button className="primary" onClick={load}>
                <Icon name="file" />
                Load recording
              </button>
            </div>
            <div className="replay-toolbar">
              <div className="prefix" aria-label="Prediction prefix">
                {[5, 10, 20, 30].map((n) => (
                  <button
                    key={n}
                    disabled={replay.length < n}
                    aria-pressed={prefix === n}
                    onClick={() => setPrefix(n)}
                  >
                    {n} packets
                  </button>
                ))}
              </div>
              <div className="replay-playback">
                <button
                  disabled={!replay.length}
                  onClick={() => setPlaying((v) => !v)}
                >
                  <Icon name={playing ? "stop" : "play"} />
                  {playing ? "Pause" : "Play"}
                </button>
                <button
                  disabled={!replay.length || prefix >= replay.length}
                  onClick={() => setPrefix((p) => p + 1)}
                >
                  Step
                  <Icon name="chevron" />
                </button>
              </div>
            </div>
            <p className="hint">
              Recorded replay · playback pacing is illustrative; packet
              intervals come from the recording. Replay does not start capture.
            </p>
          </>
        )}
      </section>

      <section className="metrics" aria-label="Session overview">
        <div className="metric">
          <span className="metric-icon">
            <Icon name="network" />
          </span>
          <div>
            <p>{mode === "Live" ? "Connections shown" : "Recorded input"}</p>
            <strong>
              {mode === "Live" ? flowEntries.length : replay.length ? 1 : 0}
            </strong>
            <small>
              {mode === "Live"
                ? "Up to 256 retained flows"
                : replay.length
                  ? replay.length +
                    " recorded packet" +
                    (replay.length === 1 ? "" : "s")
                  : "No recording loaded"}
            </small>
          </div>
        </div>
        <div className="metric">
          <span className="metric-icon purple">
            <Icon name="layers" />
          </span>
          <div>
            <p>Selected packet prefix</p>
            <strong>
              {packets.length}
              <span> / 30</span>
            </strong>
            <small>Sizes, directions & timing</small>
          </div>
        </div>
        <div className="metric">
          <span className="metric-icon blue">
            <Icon name="clock" />
          </span>
          <div>
            <p>Prediction time</p>
            <strong>
              {prediction ? prediction.pipeline_ms.toFixed(2) : "—"}
              <span>{prediction ? " ms" : ""}</span>
            </strong>
            <small>
              {prediction
                ? "Latest model pipeline call"
                : "Measured when a prediction arrives"}
            </small>
          </div>
        </div>
      </section>

      <div className="workspace">
        <aside className="flow-panel panel" aria-label="Connections">
          <div className="section-head">
            <h2>{mode === "Live" ? "Connections" : "Recording"}</h2>
            <span className="count-badge">
              {mode === "Live" ? flowEntries.length : replay.length ? 1 : 0}
            </span>
          </div>
          {mode === "Live" && flowEntries.length > 0 && (
            <label className="flow-search">
              <Icon name="search" />
              <input
                type="search"
                aria-label="Find a connection"
                placeholder="Find a service or flow…"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
              />
            </label>
          )}
          <div className="flow-list">
            {mode === "Live" ? (
              visibleFlows.map(([id, row]) => (
                <button
                  className="flow"
                  aria-pressed={id === selected}
                  key={id}
                  onClick={() => setSelected(id)}
                >
                  <span
                    className={
                      "flow-avatar " + (row.prediction?.label ? "matched" : "")
                    }
                  >
                    <Icon name={row.prediction?.label ? "check" : "network"} />
                  </span>
                  <span className="flow-copy">
                    <strong>
                      {row.prediction?.label
                        ? serviceName(row.prediction.label)
                        : row.prediction
                          ? "Uncertain service"
                          : "Collecting packets"}
                    </strong>
                    <span className="flow-id">{id}</span>
                    <span className="flow-meta">
                      {row.packets.length}/30 packets ·{" "}
                      {row.prediction?.label
                        ? "Model estimate"
                        : row.prediction
                          ? "No confident match"
                          : "Collecting"}
                    </span>
                    {row.reference?.status === "mapped" && (
                      <small>
                        Reference: {serviceName(row.reference.label ?? "")}
                      </small>
                    )}
                  </span>
                  <Icon name="chevron" />
                </button>
              ))
            ) : (
              <div className="empty-list">
                <Icon name="file" />
                <strong>
                  {replay.length ? "Recording loaded" : "No recording yet"}
                </strong>
                <p>
                  {replay.length
                    ? replay.length +
                      " recorded packet" +
                      (replay.length === 1 ? "" : "s") +
                      ". Use the prefix buttons to explore."
                    : "Paste a recorded flow above to begin."}
                </p>
              </div>
            )}
            {mode === "Live" && !flowEntries.length && (
              <div className="empty-list">
                <span className="empty-icon">
                  <Icon name="network" />
                </span>
                <strong>
                  {running
                    ? "Waiting for a new connection"
                    : "Your connections will appear here"}
                </strong>
                <p>
                  {running
                    ? "Open a fresh supported website connection. Background traffic may appear too."
                    : "Choose an interface and start a session to see eligible QUIC flows."}
                </p>
                <span className="mini-tag">
                  No capture starts automatically
                </span>
              </div>
            )}
            {mode === "Live" &&
              flowEntries.length > 0 &&
              !visibleFlows.length && (
                <div className="empty-list">
                  <Icon name="search" />
                  <strong>No matching connections</strong>
                  <p>Try a service name or flow ID.</p>
                  <button onClick={() => setFilter("")}>Clear search</button>
                </div>
              )}
          </div>
          <details className="diagnostics">
            <summary>
              Session diagnostics
              <Icon name="chevron" />
            </summary>
            <dl>
              <dt>Backlog</dt>
              <dd>{String(status.backlog ?? 0)}</dd>
              <dt>Dropped events/jobs</dt>
              <dd>{String(status.drops ?? 0)}</dd>
              <dt>Coalesced jobs</dt>
              <dd>{String(status.coalesced ?? 0)}</dd>
            </dl>
          </details>
        </aside>

        <article
          className="analysis-panel panel"
          aria-label="Selected connection analysis"
        >
          <div className="section-head analysis-heading">
            <div>
              <p className="eyebrow">
                {mode === "Live"
                  ? "CONNECTION INSIGHTS"
                  : "RECORDED FLOW INSIGHTS"}
              </p>
              <h2>
                {mode === "Live"
                  ? selected
                    ? "A closer look at this flow"
                    : "Select a connection to explore"
                  : "Explore the packet sequence"}
              </h2>
            </div>
            {selected && mode === "Live" && (
              <code className="selected-id">{selected}</code>
            )}
          </div>
          <div className="analysis-grid">
            <section className="packet-section" aria-label="Packet prefix">
              <div className="section-head">
                <h3>Packet prefix</h3>
                <span className="subtle-tag">
                  {packets.length} observed ·{" "}
                  {mode === "Live" ? "capture" : "replay"}
                </span>
              </div>
              {packets.length ? (
                <>
                  <div className="chart">
                    <div className="chart-axis">
                      <span>1,500 B</span>
                      <span>750 B</span>
                      <span>0</span>
                    </div>
                    <div
                      className="bars"
                      aria-label="Packet sizes and direction"
                    >
                      {packets.map((p, i) => (
                        <div
                          key={i}
                          className={
                            "bar " + (p.direction === 1 ? "out" : "in")
                          }
                          style={{
                            height:
                              Math.max(3, Math.min(100, p.payload_bytes / 15)) +
                              "%",
                          }}
                          title={
                            "Packet " +
                            (i + 1) +
                            ": " +
                            p.payload_bytes +
                            " B; " +
                            p.iat_ms.toFixed(3) +
                            " ms; " +
                            (p.direction === 1
                              ? "client → server"
                              : "server → client")
                          }
                        />
                      ))}
                    </div>
                  </div>
                  <div className="chart-caption">
                    <span>First packet</span>
                    <span>Up to packet 30</span>
                  </div>
                  <div className="chart-legend">
                    <span>
                      <i className="out" />
                      Sent <b>{bytes(sentBytes)}</b>
                    </span>
                    <span>
                      <i className="in" />
                      Received <b>{bytes(receivedBytes)}</b>
                    </span>
                  </div>
                  <p className="hint chart-note">
                    Client → server / server → client. Bars cap at 1,500 B;
                    exact values are in packet details. Each connection has its
                    own chart; only its first 30 packets are retained, not the
                    full traffic stream.
                  </p>
                  <details className="packet-details">
                    <summary>
                      View packet details
                      <span>
                        {packets.length} rows
                        <Icon name="chevron" />
                      </span>
                    </summary>
                    <div className="packet-table">
                      <table>
                        <caption className="sr-only">
                          Observed packet metadata for the selected prefix
                        </caption>
                        <thead>
                          <tr>
                            <th>#</th>
                            <th>Direction</th>
                            <th>Payload</th>
                            <th>Interval</th>
                          </tr>
                        </thead>
                        <tbody>
                          {packets.map((p, i) => (
                            <tr key={i}>
                              <td>{i + 1}</td>
                              <td>
                                <span
                                  className={
                                    "direction " +
                                    (p.direction === 1 ? "sent" : "received")
                                  }
                                >
                                  {p.direction === 1 ? "↗" : "↙"}
                                </span>
                                {p.direction === 1
                                  ? "Client → server"
                                  : "Server → client"}
                              </td>
                              <td>{p.payload_bytes} B</td>
                              <td>{p.iat_ms.toFixed(3)} ms</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </details>
                </>
              ) : (
                <div className="placeholder">
                  <span className="signal-illustration">
                    <Icon name="activity" />
                  </span>
                  <h3>
                    {mode === "Live"
                      ? "Ready for your first packets"
                      : "Bring a recording to life"}
                  </h3>
                  <p>
                    {mode === "Live"
                      ? running
                        ? "New eligible traffic will fill this chart as packets arrive."
                        : "Start capture, then open a fresh connection. Select a flow to see its packet sizes and directions."
                      : "Load a recorded flow above, then step through its packets."}
                  </p>
                  <span className="placeholder-legend">
                    <i className="out" />
                    Sent
                    <i className="in" />
                    Received
                  </span>
                </div>
              )}
            </section>

            <section
              className={"prediction " + (prediction?.label ? "has-match" : "")}
              aria-label="Model decision"
            >
              <div className="section-head">
                <p className="eyebrow">SERVICE ESTIMATE</p>
                <span
                  className={
                    "decision-badge " + (prediction?.label ? "matched" : "")
                  }
                >
                  {prediction?.label
                    ? "Model estimate"
                    : prediction
                      ? "Uncertain"
                      : "Waiting"}
                </span>
              </div>
              <span className="prediction-icon">
                <Icon name={prediction?.label ? "check" : "layers"} />
              </span>
              <h2>
                {busy && mode === "Replay"
                  ? "Computing…"
                  : decisionText(prediction)}
              </h2>
              {prediction ? (
                <>
                  <p className="prediction-description">
                    {prediction.model_prefix_limit ? (
                      prediction.model_packets ? (
                        <>
                          Prediction uses the first {prediction.model_packets}{" "}
                          packets; {prediction.observed_packets} packets
                          observed.
                        </>
                      ) : (
                        <>
                          Waiting for {prediction.model_prefix_limit} packets;{" "}
                          {prediction.observed_packets} observed. No model
                          scores yet.
                        </>
                      )
                    ) : (
                      <>
                        Prediction uses {prediction.observed_packets} packet
                        {prediction.observed_packets === 1 ? "" : "s"}
                        {prediction.observed_packets < packets.length
                          ? " (a newer prefix is collecting)"
                          : ""}
                        .
                      </>
                    )}
                  </p>
                  {!prediction.label && (
                    <p className="uncertainty-explanation">
                      {prediction.status === "insufficient_evidence"
                        ? "More packets are needed before this model can make a decision."
                        : prediction.decision_reason === "policy_not_fitted"
                          ? "This model's acceptance policy has not been fitted. Its top guesses are visible below, but no service label is accepted yet."
                          : prediction.decision_reason ===
                              "outside_policy_scope"
                            ? "The top guess is outside the services checked by this acceptance policy. No label is accepted; alternatives remain visible."
                            : "The model is holding back a label. Its closest alternatives are shown below."}
                    </p>
                  )}
                  <div className="alternatives">
                    <p className="eyebrow">CLOSEST ALTERNATIVES</p>
                    {prediction.alternatives.map((a) => (
                      <div className="score" key={a.label}>
                        <span>{serviceName(a.label)}</span>
                        <strong>{(a.score * 100).toFixed(1)}%</strong>
                        <meter
                          aria-label={serviceName(a.label) + " model score"}
                          min="0"
                          max="1"
                          value={a.score}
                        />
                      </div>
                    ))}
                  </div>
                  <details className="timing-details">
                    <summary>
                      Processing times
                      <Icon name="chevron" />
                    </summary>
                    <div className="timings">
                      <span>
                        Prediction pipeline
                        <b>{prediction.pipeline_ms.toFixed(2)} ms</b>
                      </span>
                      {prediction.queue_ms !== undefined && (
                        <span>
                          Queue<b>{prediction.queue_ms.toFixed(2)} ms</b>
                        </span>
                      )}
                      {prediction.capture_to_event_ms !== undefined && (
                        <span>
                          Capture → event
                          <b>{prediction.capture_to_event_ms.toFixed(2)} ms</b>
                        </span>
                      )}
                    </div>
                  </details>
                </>
              ) : (
                <p className="prediction-description">
                  {model?.architecture?.fixed_prefix_packets
                    ? `This model waits for ${model.architecture.fixed_prefix_packets} packets and uses only that first prefix. Later packets remain visible.`
                    : "Estimates appear at 5, 10, 20 and 30 packets. Nothing is predicted before traffic arrives."}
                </p>
              )}
              <p className="prediction-note">
                <Icon name="info" />
                {prediction
                  ? "A high score can still be wrong. These are model scores, not guaranteed correctness probabilities; refusal does not detect unknown services."
                  : "Local recognition is experimental. Results can differ from historical benchmark scores."}
              </p>
              {prediction && (
                <p className="prediction-note">
                  {prediction.model_prefix_limit ? (
                    <>
                      This model always uses the first{" "}
                      {prediction.model_prefix_limit} packets. Later packets do
                      not add classification evidence or improve this estimate.
                    </>
                  ) : (
                    <>
                      Each packet prefix gets a fresh decision. The leading
                      service can stay the same while its score falls below the
                      acceptance threshold. More packets do not always mean more
                      confidence; an earlier accepted label can become
                      uncertain.
                    </>
                  )}
                </p>
              )}
            </section>
          </div>

          {mode === "Live" && current?.observation && (
            <section
              className="reference-result window-section"
              aria-label="Experimental observation windows"
            >
              <div className="section-head">
                <div className="heading-with-icon">
                  <Icon name="clock" />
                  <h3>A longer look</h3>
                </div>
                <span className="subtle-tag">Statistics only</span>
              </div>
              <div className="window-cards">
                {current.observation.windows.map((window) => (
                  <div className="window-card" key={window.horizon_ms}>
                    <div>
                      <span>{window.horizon_ms / 1000}s window</span>
                      <small>{window.state.replaceAll("_", " ")}</small>
                    </div>
                    <strong>
                      {window.client_packets + window.server_packets}
                      <span> packets</span>
                    </strong>
                    <p>
                      {bytes(window.client_bytes)} sent ·{" "}
                      {bytes(window.server_bytes)} received
                    </p>
                    <small>
                      Mean {window.mean_payload_bytes.toFixed(1)} B
                      {window.late_packets_after_elapsed_snapshot > 0 &&
                        " · revised after delayed parsing"}
                    </small>
                  </div>
                ))}
              </div>
              <p className="hint">
                {current.observation.quality}. No activity label has been
                inferred.
              </p>
            </section>
          )}
          {mode === "Live" && Boolean(status.reference_enabled) && (
            <section
              className="reference-result"
              aria-label="Separate handshake reference"
            >
              <div className="section-head">
                <div>
                  <p className="eyebrow">SEPARATE HANDSHAKE REFERENCE</p>
                  <h3>
                    {reference?.label
                      ? serviceName(reference.label)
                      : "No verified name reference"}
                  </h3>
                </div>
                <span className="subtle-tag">Separate from model</span>
              </div>
              {reference?.reason && <p>{reference.reason}</p>}
              <p>
                Metadata identity:{" "}
                {reference?.status === "mapped"
                  ? serviceName(reference.label ?? "")
                  : "unresolved"}
                {reference?.status === "mapped" &&
                  " · basis: visible handshake name map"}
              </p>
              {reference?.status === "mapped" && prediction && (
                <p className="reference-comparison">
                  {prediction.label === null
                    ? "Model withheld a decision."
                    : prediction.label === reference.label
                      ? "Model agrees with this reference."
                      : "Model differs from this reference."}
                </p>
              )}
              <p className="hint">
                Name evidence and the packet-model estimate are separate
                outputs. Their scores are never combined. This historical map
                cannot guarantee app identity, and name-derived truth cannot
                independently grade this metadata identity. The chosen browser
                tab is not a label for every flow.
              </p>
            </section>
          )}
        </article>
      </div>

      <footer>
        <details className="model-details">
          <summary>
            <span>
              <Icon name="layers" />
              Model, supported services & evidence
            </span>
            <span className={"model-status " + (model ? "loaded" : "")}>
              <i />
              {model
                ? "Model loaded"
                : modelLoading
                  ? "Loading model…"
                  : "Model unavailable"}
              <Icon name="chevron" />
            </span>
          </summary>
          <div className="model-details-body">
            <p className="eyebrow">SUPPORTED SERVICES</p>
            <div className="service-tags">
              {model?.labels.map((label) => (
                <span key={label}>{serviceName(label)}</span>
              ))}
            </div>
            <p>
              Artifact{" "}
              <code>{model?.artifact_id ?? "No trained artifact loaded"}</code>
            </p>
            {model?.architecture?.fixed_prefix_packets && (
              <p role="note" aria-label="Model packet budget">
                Fixed {model.architecture.fixed_prefix_packets}-packet model.
                Scores use only the first{" "}
                {model.architecture.fixed_prefix_packets} packets; later packets
                are observation metadata only.
              </p>
            )}
            {model?.policy && (
              <p role="note" aria-label="Confidence policy evidence">
                {!model.policy.fitted
                  ? "Confidence calibration pending. Top guesses remain experimental; accepted labels are withheld."
                  : model.policy.validation_scope === "cesnet_calibration_only"
                    ? "Acceptance threshold fitted on historical CESNET data only. Local acceptance quality still needs validation. Scores are not correctness probabilities."
                    : "Stored acceptance policy loaded. Its calibration does not guarantee accuracy on this local network."}
              </p>
            )}
            <details className="raw-evidence">
              <summary>View stored evaluation report</summary>
              <pre>
                {JSON.stringify(
                  evaluation ?? { status: "No verified evaluation available" },
                  null,
                  2,
                )}
              </pre>
            </details>
          </div>
        </details>
        <div className="footer-line">
          <span>
            <Icon name="activity" />
            NetEmbedAI <span className="footer-divider">/</span> Local by design
          </span>
          <p>
            Packet model: sizes, directions and timing. Metadata identity stays
            separate. Unsupported traffic remains unresolved.
          </p>
        </div>
      </footer>
    </main>
  );
}
