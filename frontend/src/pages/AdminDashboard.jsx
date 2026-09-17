import { Fragment, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import SiteHeader from "../components/SiteHeader.jsx";
import {
  UnauthorizedError,
  clearToken,
  createDraw,
  downloadDrawPdf,
  getBallotStatus,
  getDraw,
  listDraws,
  listEntries,
  resetBallot,
  toggleBallotStatus,
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

function pad2(n) {
  return String(n).padStart(2, "0");
}

function statusBadgeClass(drawStatus) {
  if (drawStatus === "completed") return "badge badge--success";
  if (drawStatus === "failed") return "badge badge--danger";
  return "badge badge--neutral";
}

export default function AdminDashboard() {
  const [entries, setEntries] = useState(null);
  const [draws, setDraws] = useState(null);
  const [ballotStatus, setBallotStatus] = useState(null);
  const [loadError, setLoadError] = useState("");

  const [winnerCount, setWinnerCount] = useState("");
  const [runDrawStatus, setRunDrawStatus] = useState("idle");
  const [runDrawError, setRunDrawError] = useState("");
  const [lastDraw, setLastDraw] = useState(null);

  const [resetInput, setResetInput] = useState("");
  const [resetStatus, setResetStatus] = useState("idle");
  const [resetError, setResetError] = useState("");
  const [resetSummary, setResetSummary] = useState(null);

  const [toggleStatus, setToggleStatus] = useState("idle");
  const [toggleError, setToggleError] = useState("");

  const [exportError, setExportError] = useState("");

  const [expandedDrawIds, setExpandedDrawIds] = useState(() => new Set());
  const [drawDetails, setDrawDetails] = useState({});

  function loadDashboardData() {
    return Promise.all([listEntries(), listDraws(), getBallotStatus()]).then(
      ([entriesData, drawsData, statusData]) => {
        setEntries(entriesData);
        setDraws(drawsData);
        setBallotStatus(statusData);
      }
    );
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

  function handleToggleBallot() {
    setToggleStatus("submitting");
    setToggleError("");

    toggleBallotStatus()
      .then((status) => {
        setBallotStatus(status);
        setToggleStatus("idle");
      })
      .catch((err) => {
        if (err instanceof UnauthorizedError) return;
        setToggleStatus("idle");
        setToggleError(err.message);
      });
  }

  function toggleDrawWinners(drawId) {
    setExpandedDrawIds((prev) => {
      const next = new Set(prev);
      if (next.has(drawId)) {
        next.delete(drawId);
      } else {
        next.add(drawId);
      }
      return next;
    });
    if (!drawDetails[drawId]) {
      setDrawDetails((prev) => ({ ...prev, [drawId]: { status: "loading" } }));
      getDraw(drawId)
        .then((detail) => {
          setDrawDetails((prev) => ({ ...prev, [drawId]: { status: "loaded", detail } }));
        })
        .catch((err) => {
          if (err instanceof UnauthorizedError) return;
          setDrawDetails((prev) => ({
            ...prev,
            [drawId]: { status: "error", error: err.message },
          }));
        });
    }
  }

  function handleDownloadPdf(drawId) {
    setExportError("");
    downloadDrawPdf(drawId).catch((err) => {
      if (err instanceof UnauthorizedError) return;
      setExportError(err.message);
    });
  }

  function handleLogout() {
    clearToken();
    window.location.assign("/admin/login");
  }

  const isLoading = entries === null || draws === null || ballotStatus === null;

  return (
    <div className="site-shell admin-dashboard-shell">
      <SiteHeader
        eyebrow="Admin"
        action={
          <button type="button" className="secondary-button small-button" onClick={handleLogout}>
            Log out
          </button>
        }
      />
      <main className="site-main site-main--wide">
        <div className="admin-header">
          <div>
            <h1>Admin dashboard</h1>
          </div>
        </div>

        {loadError && <p className="error-text">{loadError}</p>}

        {isLoading && !loadError && (
          <p className="loading-text">
            <span className="spinner" aria-hidden="true" />
            Loading dashboard…
          </p>
        )}

        {!isLoading && (
          <>
            <section className="section">
              <div
                className={`status-strip ${
                  ballotStatus.is_open ? "status-strip--open" : "status-strip--closed"
                }`}
              >
                <div>
                  <span className="eyebrow">Ballot status</span>
                  <p className="status-line">
                    <span
                      className={`status-line__dot ${
                        ballotStatus.is_open ? "badge--success" : "badge--danger"
                      }`}
                      aria-hidden="true"
                    />
                    <span
                      className={`status-line__word ${
                        ballotStatus.is_open ? "badge--success" : "badge--danger"
                      }`}
                    >
                      {ballotStatus.is_open ? "Open" : "Closed"}
                    </span>
                    <span className="helper-text">to new entries</span>
                  </p>
                  {toggleError && <p className="error-text">{toggleError}</p>}
                </div>
                <button
                  type="button"
                  className={ballotStatus.is_open ? "warning-button" : ""}
                  onClick={handleToggleBallot}
                  disabled={toggleStatus === "submitting"}
                >
                  {toggleStatus === "submitting"
                    ? "Updating…"
                    : ballotStatus.is_open
                      ? "Close ballot"
                      : "Open ballot"}
                </button>
              </div>
            </section>

            <div className="section dashboard-grid">
              <section className="panel">
                <h2>
                  Entries <span className="mono">({entries.length})</span>
                </h2>
                {entries.length === 0 ? (
                  <p className="empty-state">No entries yet.</p>
                ) : (
                  <ul className="entries-list">
                    {entries.map((entry) => (
                      <li key={entry.id}>{entry.name}</li>
                    ))}
                  </ul>
                )}
              </section>

              <section className="panel">
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
                  <button
                    type="submit"
                    className="primary-button"
                    disabled={runDrawStatus === "submitting"}
                  >
                    {runDrawStatus === "submitting" ? "Running draw…" : "Run draw"}
                  </button>
                </form>

                {lastDraw && (
                  <div className="last-draw-result">
                    <span className="eyebrow">Draw #{lastDraw.id}</span>
                    <h3>Winners</h3>
                    <ol className="winners-list">
                      {lastDraw.winners.map((winner) => (
                        <li key={winner.position} className="winner-row">
                          <span className="winner-tile">{pad2(winner.position)}</span>
                          <span className="winner-name">{winner.entry.name}</span>
                        </li>
                      ))}
                    </ol>
                    <button
                      type="button"
                      className="secondary-button"
                      onClick={() => handleDownloadPdf(lastDraw.id)}
                    >
                      Download PDF
                    </button>
                  </div>
                )}
              </section>
            </div>

            <section className="section past-draws-section">
              <h2>Past draws</h2>
              {exportError && <p className="error-text">{exportError}</p>}
              {draws.length === 0 ? (
                <p className="empty-state">No draws yet.</p>
              ) : (
                <div className="table-scroll">
                  <table className="draws-table">
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Status</th>
                        <th>Winners</th>
                        <th>Drawn at</th>
                        <th>Seed</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {draws.map((draw) => {
                        const isExpanded = expandedDrawIds.has(draw.id);
                        const detailState = drawDetails[draw.id];
                        return (
                          <Fragment key={draw.id}>
                            <tr>
                              <td>{draw.id}</td>
                              <td>
                                <span className={statusBadgeClass(draw.status)}>
                                  {draw.status}
                                </span>
                              </td>
                              <td>{draw.winner_count}</td>
                              <td>{draw.drawn_at ? formatDateTime(draw.drawn_at) : "—"}</td>
                              <td className="seed-cell">{draw.seed}</td>
                              <td>
                                {draw.status === "completed" ? (
                                  <div className="table-actions">
                                    <button
                                      type="button"
                                      className="secondary-button small-button"
                                      aria-expanded={isExpanded}
                                      onClick={() => toggleDrawWinners(draw.id)}
                                    >
                                      {isExpanded ? "Hide" : "View"}
                                    </button>
                                    <button
                                      type="button"
                                      className="secondary-button small-button"
                                      onClick={() => handleDownloadPdf(draw.id)}
                                    >
                                      PDF
                                    </button>
                                  </div>
                                ) : (
                                  "—"
                                )}
                              </td>
                            </tr>
                            {isExpanded && (
                              <tr>
                                <td colSpan={6} className="draws-table-expanded">
                                  {(!detailState || detailState.status === "loading") && (
                                    <p className="loading-text">
                                      <span className="spinner" aria-hidden="true" />
                                      Loading winners…
                                    </p>
                                  )}
                                  {detailState?.status === "error" && (
                                    <p className="error-text">{detailState.error}</p>
                                  )}
                                  {detailState?.status === "loaded" && (
                                    <ol className="winners-list">
                                      {detailState.detail.winners.map((winner) => (
                                        <li key={winner.position} className="winner-row">
                                          <span className="winner-tile">
                                            {pad2(winner.position)}
                                          </span>
                                          <span className="winner-name">
                                            {winner.entry.name}
                                          </span>
                                        </li>
                                      ))}
                                    </ol>
                                  )}
                                </td>
                              </tr>
                            )}
                          </Fragment>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </section>

            <section className="section danger-zone">
              <h2>Reset ballot</h2>
              <p className="danger-warning">
                This permanently deletes every entry, draw, and winner so a new
                event can start from zero. It does not affect admin accounts.
                Only do this between events, after any results you need have
                already been recorded elsewhere, it is not a way to undo or
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
                  {resetStatus === "submitting" ? "Resetting…" : "Reset ballot"}
                </button>
              </form>
            </section>
          </>
        )}

        <Link className="nav-link" to="/results">
          View public results page
        </Link>
      </main>
    </div>
  );
}
