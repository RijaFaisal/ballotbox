import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  UnauthorizedError,
  clearToken,
  createDraw,
  listDraws,
  listEntries,
  resetBallot,
} from "../api/client.js";

const RESET_CONFIRM_PHRASE = "RESET";

function formatDateTime(isoString) {
  return new Date(isoString).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function pluralize(count, singular, plural) {
  return `${count} ${count === 1 ? singular : plural}`;
}

export default function AdminDashboard() {
  const [entries, setEntries] = useState(null);
  const [draws, setDraws] = useState(null);
  const [loadError, setLoadError] = useState("");

  const [winnerCount, setWinnerCount] = useState("");
  const [runDrawStatus, setRunDrawStatus] = useState("idle");
  const [runDrawError, setRunDrawError] = useState("");
  const [lastDraw, setLastDraw] = useState(null);

  const [resetInput, setResetInput] = useState("");
  const [resetStatus, setResetStatus] = useState("idle");
  const [resetError, setResetError] = useState("");
  const [resetSummary, setResetSummary] = useState(null);

  function loadDashboardData() {
    return Promise.all([listEntries(), listDraws()]).then(([entriesData, drawsData]) => {
      setEntries(entriesData);
      setDraws(drawsData);
    });
  }

  useEffect(() => {
    loadDashboardData().catch((err) => {
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

  function handleReset(event) {
    event.preventDefault();
    if (resetInput !== RESET_CONFIRM_PHRASE) {
      setResetError(`Type ${RESET_CONFIRM_PHRASE} exactly to confirm.`);
      return;
    }

    setResetStatus("submitting");
    setResetError("");
    setResetSummary(null);

    resetBallot(resetInput)
      .then((result) => {
        setResetSummary(result);
        setResetInput("");
        setResetStatus("idle");
        setLastDraw(null);
        return loadDashboardData();
      })
      .catch((err) => {
        if (err instanceof UnauthorizedError) return;
        setResetStatus("idle");
        setResetError(err.message);
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

            <section className="admin-section danger-zone">
              <h2>Reset ballot</h2>
              <p className="danger-warning">
                This permanently deletes every entry, draw, and winner so a new
                event can start from zero. It does not affect admin accounts.
                Only do this between events, after any results you need have
                already been recorded elsewhere — it is not a way to undo or
                hide a completed draw.
              </p>
              <form onSubmit={handleReset} className="reset-form">
                <div className="field">
                  <label htmlFor="resetConfirm">
                    Type <strong>{RESET_CONFIRM_PHRASE}</strong> to confirm
                  </label>
                  <input
                    id="resetConfirm"
                    value={resetInput}
                    onChange={(e) => setResetInput(e.target.value)}
                    autoComplete="off"
                  />
                </div>
                {resetError && <p className="error-text">{resetError}</p>}
                {resetSummary && (
                  <p className="reset-summary">
                    Cleared {pluralize(resetSummary.entries_deleted, "entry", "entries")},{" "}
                    {pluralize(resetSummary.draws_deleted, "draw", "draws")}, and{" "}
                    {pluralize(resetSummary.winners_deleted, "winner", "winners")}.
                  </p>
                )}
                <button
                  type="submit"
                  className="danger-button"
                  disabled={
                    resetStatus === "submitting" || resetInput !== RESET_CONFIRM_PHRASE
                  }
                >
                  {resetStatus === "submitting" ? "Resetting..." : "Reset ballot"}
                </button>
              </form>
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
