import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  UnauthorizedError,
  clearToken,
  createDraw,
  listDraws,
  listEntries,
} from "../api/client.js";

function formatDateTime(isoString) {
  return new Date(isoString).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export default function AdminDashboard() {
  const [entries, setEntries] = useState(null);
  const [draws, setDraws] = useState(null);
  const [loadError, setLoadError] = useState("");

  const [winnerCount, setWinnerCount] = useState("");
  const [runDrawStatus, setRunDrawStatus] = useState("idle");
  const [runDrawError, setRunDrawError] = useState("");
  const [lastDraw, setLastDraw] = useState(null);

  useEffect(() => {
    Promise.all([listEntries(), listDraws()])
      .then(([entriesData, drawsData]) => {
        setEntries(entriesData);
        setDraws(drawsData);
      })
      .catch((err) => {
        if (err instanceof UnauthorizedError) return;
        setLoadError(err.message);
      });
  }, []);

  function handleRunDraw(event) {
    event.preventDefault();
    const count = Number(winnerCount);
    if (!Number.isInteger(count) || count <= 0) {
      setRunDrawError("Enter a whole number greater than 0.");
      return;
    }

    setRunDrawStatus("submitting");
    setRunDrawError("");
    setLastDraw(null);

    createDraw(count)
      .then((draw) => {
        setLastDraw(draw);
        setWinnerCount("");
        setRunDrawStatus("idle");
        return listDraws().then(setDraws);
      })
      .catch((err) => {
        if (err instanceof UnauthorizedError) return;
        setRunDrawStatus("idle");
        setRunDrawError(err.message);
      });
  }

  function handleLogout() {
    clearToken();
    window.location.assign("/admin/login");
  }

  const isLoading = entries === null || draws === null;

  return (
    <div className="page">
      <div className="card admin-card">
        <div className="admin-header">
          <h1>Admin dashboard</h1>
          <button type="button" className="secondary-button" onClick={handleLogout}>
            Log out
          </button>
        </div>

        {loadError && <p className="error-text">{loadError}</p>}

        {isLoading && !loadError && <p>Loading dashboard...</p>}

        {!isLoading && (
          <>
            <section className="admin-section">
              <h2>Entries ({entries.length})</h2>
              {entries.length === 0 ? (
                <p>No entries yet.</p>
              ) : (
                <ul className="entries-list">
                  {entries.map((entry) => (
                    <li key={entry.id}>{entry.name}</li>
                  ))}
                </ul>
              )}
            </section>

            <section className="admin-section">
              <h2>Run a draw</h2>
              <form onSubmit={handleRunDraw} className="run-draw-form">
                <div className="field">
                  <label htmlFor="winnerCount">Number of winners</label>
                  <input
                    id="winnerCount"
                    type="number"
                    min="1"
                    value={winnerCount}
                    onChange={(e) => setWinnerCount(e.target.value)}
                  />
                </div>
                {runDrawError && <p className="error-text">{runDrawError}</p>}
                <button type="submit" disabled={runDrawStatus === "submitting"}>
                  {runDrawStatus === "submitting" ? "Running draw..." : "Run draw"}
                </button>
              </form>

              {lastDraw && (
                <div className="last-draw-result">
                  <h3>Draw #{lastDraw.id} winners</h3>
                  <ol className="winners-list">
                    {lastDraw.winners.map((winner) => (
                      <li key={winner.position}>
                        <span className="winner-position">#{winner.position}</span>{" "}
                        {winner.entry.name}
                      </li>
                    ))}
                  </ol>
                </div>
              )}
            </section>

            <section className="admin-section">
              <h2>Past draws</h2>
              {draws.length === 0 ? (
                <p>No draws yet.</p>
              ) : (
                <table className="draws-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Status</th>
                      <th>Winners</th>
                      <th>Drawn at</th>
                      <th>Seed</th>
                    </tr>
                  </thead>
                  <tbody>
                    {draws.map((draw) => (
                      <tr key={draw.id}>
                        <td>{draw.id}</td>
                        <td>{draw.status}</td>
                        <td>{draw.winner_count}</td>
                        <td>{draw.drawn_at ? formatDateTime(draw.drawn_at) : "—"}</td>
                        <td className="seed-cell">{draw.seed}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>
          </>
        )}

        <Link className="nav-link" to="/results">
          View public results page
        </Link>
      </div>
    </div>
  );
}
