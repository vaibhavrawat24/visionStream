import { useRef, useState, useCallback, useEffect } from "react";

const WS_URL = `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/stream`;
const FRAME_INTERVAL_MS = 100; // ~10 fps sent to server

export default function VideoFeed({ onStatusChange, onRoiUpdate, onSessionId }) {
  const webcamRef = useRef(null);
  const canvasRef = useRef(null);       // offscreen — captures webcam frames
  const displayRef = useRef(null);      // visible — shows annotated frames
  const wsRef = useRef(null);
  const intervalRef = useRef(null);
  const streamingRef = useRef(false);

  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState(null);
  const [fps, setFps] = useState(0);
  const fpsCounterRef = useRef({ count: 0, ts: Date.now() });

  const stopStream = useCallback(() => {
    clearInterval(intervalRef.current);
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (webcamRef.current?.srcObject) {
      webcamRef.current.srcObject.getTracks().forEach((t) => t.stop());
      webcamRef.current.srcObject = null;
    }
    streamingRef.current = false;
    setStreaming(false);
    onStatusChange("idle");
    onRoiUpdate(null);
  }, [onStatusChange, onRoiUpdate]);

  const startStream = useCallback(async () => {
    setError(null);
    onStatusChange("connecting");

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      webcamRef.current.srcObject = stream;
      await webcamRef.current.play();
    } catch (e) {
      setError("Camera access denied. Please allow camera permissions.");
      onStatusChange("error");
      return;
    }

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      onStatusChange("streaming");
      streamingRef.current = true;
      setStreaming(true);

      const canvas = canvasRef.current;
      const ctx = canvas.getContext("2d");

      intervalRef.current = setInterval(() => {
        const video = webcamRef.current;
        if (!video || video.readyState < 2) return;

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0);

        const b64 = canvas.toDataURL("image/jpeg", 0.8);
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ frame: b64 }));
        }
      }, FRAME_INTERVAL_MS);
    };

    ws.onmessage = (evt) => {
      const msg = JSON.parse(evt.data);
      if (msg.error) {
        setError(msg.error);
        return;
      }
      if (msg.type === "pong") return;

      // Draw annotated frame onto display canvas
      if (msg.frame) {
        const img = new Image();
        img.onload = () => {
          const dc = displayRef.current;
          if (!dc) return;
          dc.width = img.width;
          dc.height = img.height;
          dc.getContext("2d").drawImage(img, 0, 0);
        };
        img.src = msg.frame;
      }

      if (msg.session_id) onSessionId(msg.session_id);
      onRoiUpdate(msg.roi ?? null);

      // FPS counter
      const fc = fpsCounterRef.current;
      fc.count++;
      const now = Date.now();
      if (now - fc.ts >= 1000) {
        setFps(fc.count);
        fc.count = 0;
        fc.ts = now;
      }
    };

    ws.onerror = () => {
      setError("WebSocket connection failed.");
      onStatusChange("error");
      stopStream();
    };

    ws.onclose = () => {
      if (streamingRef.current) stopStream();
    };
  }, [onStatusChange, onRoiUpdate, onSessionId, stopStream]);

  // Cleanup on unmount
  useEffect(() => () => stopStream(), [stopStream]);

  return (
    <div className="card">
      <div className="card-header">
        <span>◉</span> Live Camera Feed
        {streaming && (
          <span style={{ marginLeft: "auto", color: "#00ff41", fontSize: 12 }}>
            {fps} fps
          </span>
        )}
      </div>
      <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {error && (
          <div style={{
            background: "#2d1215", border: "1px solid #f85149",
            borderRadius: 6, padding: "8px 12px", color: "#f85149", fontSize: 13
          }}>
            {error}
          </div>
        )}

        {/* Annotated output canvas */}
        <div style={{ position: "relative", background: "#000", borderRadius: 8, overflow: "hidden", minHeight: 240 }}>
          <canvas
            ref={displayRef}
            style={{ width: "100%", display: streaming ? "block" : "none" }}
          />
          {!streaming && (
            <div style={{
              position: "absolute", inset: 0, display: "flex",
              alignItems: "center", justifyContent: "center",
              color: "#30363d", fontSize: 48
            }}>
              ◉
            </div>
          )}
        </div>

        {/* Hidden elements */}
        <video ref={webcamRef} style={{ display: "none" }} muted playsInline />
        <canvas ref={canvasRef} style={{ display: "none" }} />

        <div style={{ display: "flex", gap: 10 }}>
          {!streaming ? (
            <button className="btn btn-primary" onClick={startStream}>
              ▶ Start Stream
            </button>
          ) : (
            <button className="btn btn-danger" onClick={stopStream}>
              ■ Stop Stream
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
