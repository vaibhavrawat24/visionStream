const STATUS_CONFIG = {
  idle:       { color: "#8b949e", dot: "○", label: "Idle" },
  connecting: { color: "#e3b341", dot: "◌", label: "Connecting…" },
  streaming:  { color: "#00ff41", dot: "●", label: "Live" },
  error:      { color: "#f85149", dot: "✕", label: "Error" },
};

export default function StatusBar({ status }) {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.idle;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13 }}>
      <span style={{ color: cfg.color, fontSize: 16 }}>{cfg.dot}</span>
      <span style={{ color: cfg.color, fontWeight: 600 }}>{cfg.label}</span>
    </div>
  );
}
