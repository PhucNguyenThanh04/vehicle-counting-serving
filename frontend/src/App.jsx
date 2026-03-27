import { useEffect, useState } from "react";
import "./App.css";

function Dashboard() {
  const [stats, setStats] = useState({});
  const [dataList, setDataList] = useState([]);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/counts");
    ws.onopen = () => console.log("WebSocket connected");
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setStats(data.counts || {});
      if (Array.isArray(data.events)) setDataList(data.events);
    };
    ws.onerror = (err) => console.error("WebSocket error:", err);
    ws.onclose = () => console.log("WebSocket disconnected");
    return () => ws.close();
  }, []);

  return (
    <div className="app">
      {/* HEADER */}
      <div className="header">
        <span className="dot" />
        <span className="title">Vehicle Detection Dashboard</span>
        <span className="live">● LIVE</span>
      </div>

      {/* TOP */}
      <div className="top">
        {/* VIDEO */}
        <div className="video">
          <img src="http://localhost:8000/stream" alt="stream" />
          <div className="cam-label">CAM 01</div>
        </div>

        {/* STATS */}
        <div className="stats">
          <div className="stats-title">Zone Counts</div>

          <div className="grid">
            {[1, 2, 3, 4, 5, 6].map((zoneId) => {
              const counts = stats[zoneId] || {};
              const total = Object.values(counts).reduce((a, b) => a + b, 0);

              return (
                <div key={zoneId} className="card">
                  <div className="card-header">
                    <span className="zone">Zone {zoneId}</span>
                    <span className="total">{total}</span>
                  </div>

                  <div className="card-body">
                    {Object.keys(counts).length === 0 ? (
                      <span className="nodata">No data</span>
                    ) : (
                      Object.entries(counts)
                        .sort((a, b) => b[1] - a[1])
                        .map(([type, value]) => (
                          <div key={type} className="row">
                            <span className="type">{type}</span>
                            <span className="value">{value}</span>
                          </div>
                        ))
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* BOTTOM */}
      <div className="bottom">
        <div className="bottom-header">
          <span>Event Log</span>
          <span className="event-count">{dataList.length} events</span>
        </div>

        <div className="event-list">
          {dataList.length > 0 ? (
            dataList.map((item, index) => (
              <div key={index} className="event-card">
                {[
                  ["ID", item.track_id],
                  ["Type", item.cls],
                  ["Zone", item.zone_id],
                  ["Time", item.timestamp],
                ].map(([k, v]) => (
                  <div key={k} className="event-row">
                    <span className="event-key">{k}</span>
                    <span className="event-value">{v}</span>
                  </div>
                ))}
              </div>
            ))
          ) : (
            <span className="waiting">Waiting for events...</span>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
