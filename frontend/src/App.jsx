// import { useEffect, useState } from "react";
// import "./App.css";

// function Dashboard() {
//   const [stats, setStats] = useState({});
//   const [dataList, setDataList] = useState([]);

//   useEffect(() => {
//     const ws = new WebSocket("ws://localhost:8000/counts");
//     ws.onopen = () => console.log("WebSocket connected");
//     ws.onmessage = (event) => {
//       const data = JSON.parse(event.data);
//       setStats(data.counts || {});
//       if (Array.isArray(data.events)) setDataList(data.events);
//     };
//     ws.onerror = (err) => console.error("WebSocket error:", err);
//     ws.onclose = () => console.log("WebSocket disconnected");
//     return () => ws.close();
//   }, []);

//   return (
//     <div
//       style={{
//         height: "100vh",
//         display: "flex",
//         flexDirection: "column",
//         background: "#0d0f14",
//         color: "#e8ecf4",
//         fontFamily: "monospace",
//         overflow: "hidden",
//       }}
//     >
//       {/* HEADER */}
//       <div
//         style={{
//           height: "36px",
//           flexShrink: 0,
//           display: "flex",
//           alignItems: "center",
//           padding: "0 16px",
//           gap: "10px",
//           background: "#151820",
//           borderBottom: "1px solid #2a2f3e",
//         }}
//       >
//         <span
//           style={{
//             width: 8,
//             height: 8,
//             borderRadius: "50%",
//             background: "#00e5ff",
//             boxShadow: "0 0 8px #00e5ff",
//             flexShrink: 0,
//           }}
//         />
//         <span
//           style={{
//             flex: 1,
//             fontSize: 13,
//             fontWeight: 700,
//             letterSpacing: "0.1em",
//             textTransform: "uppercase",
//           }}
//         >
//           Vehicle Detection Dashboard
//         </span>
//         <span
//           style={{
//             fontSize: 11,
//             color: "#22c55e",
//             animation: "blink 1.5s infinite",
//           }}
//         >
//           ● LIVE
//         </span>
//       </div>

//       {/* TOP — video 70% | stats 30% */}
//       <div
//         style={{
//           flex: "0 0 70%" /* chiếm đúng 70% chiều cao còn lại */,
//           display: "flex",
//           flexDirection: "row" /* ← nằm ngang */,
//           overflow: "hidden",
//           borderBottom: "1px solid #2a2f3e",
//         }}
//       >
//         {/* VIDEO — 70% chiều ngang */}
//         <div
//           style={{
//             width: "70%",
//             flexShrink: 0,
//             background: "#000",
//             position: "relative",
//             overflow: "hidden",
//           }}
//         >
//           <img
//             src="http://localhost:8000/stream"
//             alt="stream"
//             style={{
//               width: "100%",
//               height: "100%",
//               objectFit: "contain",
//               display: "block",
//             }}
//           />
//           <div
//             style={{
//               position: "absolute",
//               top: 10,
//               left: 12,
//               fontFamily: "monospace",
//               fontSize: 11,
//               color: "#00e5ff",
//               background: "rgba(0,0,0,0.6)",
//               padding: "3px 8px",
//               borderRadius: 4,
//               border: "1px solid #00e5ff",
//               letterSpacing: "0.1em",
//             }}
//           >
//             CAM 01
//           </div>
//         </div>

//         {/* STATS — 30% chiều ngang */}
//         <div
//           style={{
//             width: "30%",
//             flexShrink: 0,
//             background: "#151820",
//             borderLeft: "1px solid #2a2f3e",
//             display: "flex",
//             flexDirection: "column",
//             overflow: "hidden",
//           }}
//         >
//           <div
//             style={{
//               flexShrink: 0,
//               padding: "7px 12px",
//               fontSize: 10,
//               textTransform: "uppercase",
//               letterSpacing: "0.14em",
//               color: "#6b7394",
//               borderBottom: "1px solid #2a2f3e",
//             }}
//           >
//             Zone Counts
//           </div>

//           {/* Grid 2 cột × 3 hàng — fit vừa khung, không scroll */}
//           <div
//             style={{
//               flex: 1,
//               minHeight: 0,
//               display: "grid",
//               gridTemplateColumns: "1fr 1fr",
//               gridTemplateRows: "1fr 1fr 1fr",
//               gap: 6,
//               padding: 8,
//               overflow: "hidden",
//             }}
//           >
//             {[1, 2, 3, 4, 5, 6].map((zoneId) => {
//               const counts = stats[zoneId] || {};
//               const total = Object.values(counts).reduce((a, b) => a + b, 0);
//               return (
//                 <div
//                   key={zoneId}
//                   style={{
//                     background: "#181c28",
//                     border: "1px solid #2a2f3e",
//                     borderRadius: 7,
//                     padding: "8px 10px",
//                     display: "flex",
//                     flexDirection: "column",
//                     gap: 4,
//                     overflow: "hidden",
//                     minHeight: 0,
//                   }}
//                 >
//                   <div
//                     style={{
//                       display: "flex",
//                       justifyContent: "space-between",
//                       alignItems: "center",
//                       flexShrink: 0,
//                     }}
//                   >
//                     <span
//                       style={{
//                         fontSize: 10,
//                         fontWeight: 700,
//                         color: "#00e5ff",
//                         textTransform: "uppercase",
//                         letterSpacing: "0.1em",
//                       }}
//                     >
//                       Zone {zoneId}
//                     </span>
//                     <span
//                       style={{
//                         fontSize: 20,
//                         fontWeight: 700,
//                         color: "#e8ecf4",
//                         lineHeight: 1,
//                       }}
//                     >
//                       {total}
//                     </span>
//                   </div>
//                   <div
//                     style={{
//                       display: "flex",
//                       flexDirection: "column",
//                       gap: 3,
//                       overflow: "hidden",
//                       flex: 1,
//                     }}
//                   >
//                     {Object.keys(counts).length === 0 ? (
//                       <span
//                         style={{
//                           fontSize: 10,
//                           color: "#6b7394",
//                           fontStyle: "italic",
//                         }}
//                       >
//                         No data
//                       </span>
//                     ) : (
//                       Object.entries(counts)
//                         .sort((a, b) => b[1] - a[1])
//                         .map(([type, value]) => (
//                           <div
//                             key={type}
//                             style={{
//                               display: "flex",
//                               justifyContent: "space-between",
//                               fontSize: 11,
//                             }}
//                           >
//                             <span
//                               style={{
//                                 color: "#6b7394",
//                                 textTransform: "capitalize",
//                               }}
//                             >
//                               {type}
//                             </span>
//                             <span style={{ fontWeight: 600, color: "#e8ecf4" }}>
//                               {value}
//                             </span>
//                           </div>
//                         ))
//                     )}
//                   </div>
//                 </div>
//               );
//             })}
//           </div>
//         </div>
//       </div>

//       {/* BOTTOM — event log */}
//       <div
//         style={{
//           flex: 1,
//           minHeight: 0,
//           display: "flex",
//           flexDirection: "column",
//           background: "#151820",
//           overflow: "hidden",
//         }}
//       >
//         <div
//           style={{
//             flexShrink: 0,
//             display: "flex",
//             justifyContent: "space-between",
//             alignItems: "center",
//             padding: "6px 14px",
//             fontSize: 10,
//             textTransform: "uppercase",
//             letterSpacing: "0.14em",
//             color: "#6b7394",
//             borderBottom: "1px solid #2a2f3e",
//           }}
//         >
//           <span>Event Log</span>
//           <span style={{ color: "#7b61ff" }}>{dataList.length} events</span>
//         </div>

//         <div
//           style={{
//             flex: 1,
//             minHeight: 0,
//             display: "flex",
//             flexDirection: "row",
//             gap: 8,
//             padding: "8px 10px",
//             overflowX: "auto",
//             overflowY: "hidden",
//             alignItems: "flex-start",
//           }}
//         >
//           {dataList.length > 0 ? (
//             dataList.map((item, index) => (
//               <div
//                 key={index}
//                 style={{
//                   flexShrink: 0,
//                   width: 150,
//                   background: "#181c28",
//                   border: "1px solid #2a2f3e",
//                   borderRadius: 7,
//                   padding: "9px 10px",
//                   display: "flex",
//                   flexDirection: "column",
//                   gap: 5,
//                 }}
//               >
//                 {[
//                   ["ID", item.track_id],
//                   ["Type", item.cls],
//                   ["Zone", item.zone_id],
//                   ["Time", item.timestamp],
//                 ].map(([k, v]) => (
//                   <div
//                     key={k}
//                     style={{
//                       display: "flex",
//                       justifyContent: "space-between",
//                       alignItems: "center",
//                     }}
//                   >
//                     <span
//                       style={{
//                         fontSize: 10,
//                         color: "#6b7394",
//                         textTransform: "uppercase",
//                         letterSpacing: "0.08em",
//                       }}
//                     >
//                       {k}
//                     </span>
//                     <span style={{ fontSize: 11, color: "#e8ecf4" }}>{v}</span>
//                   </div>
//                 ))}
//               </div>
//             ))
//           ) : (
//             <span
//               style={{
//                 margin: "auto",
//                 fontSize: 12,
//                 color: "#6b7394",
//                 fontStyle: "italic",
//               }}
//             >
//               Waiting for events...
//             </span>
//           )}
//         </div>
//       </div>
//     </div>
//   );
// }

// export default Dashboard;

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
