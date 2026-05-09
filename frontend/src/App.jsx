import { useState } from "react";
import VideoFeed from "./components/VideoFeed.jsx";
import ROIPanel from "./components/ROIPanel.jsx";
import StatusBar from "./components/StatusBar.jsx";
import "./App.css";

export default function App() {
  const [status, setStatus] = useState("idle"); // idle | connecting | streaming | error
  const [currentRoi, setCurrentRoi] = useState(null);
  const [sessionId, setSessionId] = useState(null);

  return (
    <div className="app">
      <header className="app-header">
        <div className="logo">
          <span className="logo-icon">◉</span>
          <span className="logo-text">VisionStream</span>
        </div>
        <StatusBar status={status} />
      </header>

      <main className="app-main">
        <section className="feed-section">
          <VideoFeed
            onStatusChange={setStatus}
            onRoiUpdate={setCurrentRoi}
            onSessionId={setSessionId}
          />
        </section>

        <aside className="data-section">
          <ROIPanel currentRoi={currentRoi} sessionId={sessionId} />
        </aside>
      </main>
    </div>
  );
}
