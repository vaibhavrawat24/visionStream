import { useState, useEffect, useCallback } from "react";

const API = "/api/roi";

export default function ROIPanel({ currentRoi, sessionId }) {
  const [history, setHistory] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);

  const fetchHistory = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}?session_id=${sessionId}&limit=20`);
      if (!r.ok) return;
      const data = await r.json();
      setHistory(data.items);
      setTotal(data.total);
    } catch (_) {
      // network error — silently ignore
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  // Refresh history whenever the current ROI changes (new detection)
  useEffect(() => {
    if (currentRoi) fetchHistory();
  }, [currentRoi, fetchHistory]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

      {/* Current ROI card */}
      <div className="card">
        <div className="card-header"><span>⬚</span> Current ROI</div>
        <div className="card-body">
          {currentRoi ? (
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <tbody>
                {[
                  ["X", currentRoi.x, "px"],
                  ["Y", currentRoi.y, "px"],
                  ["Width", currentRoi.width, "px"],
                  ["Height", currentRoi.height, "px"],
                  ["Confidence", (currentRoi.confidence * 100).toFixed(1), "%"],
                ].map(([k, v, unit]) => (
                  <tr key={k} style={{ borderBottom: "1px solid #30363d" }}>
                    <td style={{ padding: "6px 0", color: "#8b949e", width: 90 }}>{k}</td>
                    <td style={{ padding: "6px 0", color: "#00ff41", fontWeight: 600, fontFamily: "monospace" }}>
                      {v}<span style={{ color: "#8b949e", fontSize: 11 }}> {unit}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p style={{ color: "#8b949e", fontSize: 13, textAlign: "center", padding: "12px 0" }}>
              No face detected
            </p>
          )}
        </div>
      </div>

      {/* Detection history */}
      <div className="card" style={{ flex: 1 }}>
        <div className="card-header">
          <span>⏱</span> Detection History
          {total > 0 && (
            <span style={{ marginLeft: "auto", color: "#8b949e", fontWeight: 400 }}>
              {total} total
            </span>
          )}
        </div>
        <div className="card-body" style={{ padding: 0, maxHeight: 360, overflowY: "auto" }}>
          {loading && history.length === 0 ? (
            <p style={{ color: "#8b949e", fontSize: 13, padding: 16 }}>Loading…</p>
          ) : history.length === 0 ? (
            <p style={{ color: "#8b949e", fontSize: 13, padding: 16 }}>No detections yet</p>
          ) : (
            history.map((item) => (
              <div key={item.id} style={{
                padding: "8px 16px",
                borderBottom: "1px solid #21262d",
                fontSize: 12,
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}>
                <span style={{ color: "#e6edf3", fontFamily: "monospace" }}>
                  [{item.x}, {item.y}, {item.width}×{item.height}]
                </span>
                <span style={{ color: "#00ff41" }}>
                  {(item.confidence * 100).toFixed(0)}%
                </span>
                <span style={{ color: "#8b949e" }}>
                  {new Date(item.detected_at).toLocaleTimeString()}
                </span>
              </div>
            ))
          )}
        </div>
      </div>

    </div>
  );
}
