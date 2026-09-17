import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import SiteHeader from "../components/SiteHeader.jsx";
import { getResults, getResultsHistory, getResultsHistoryDetail } from "../api/client.js";

function formatDate(isoString) {
  return new Date(isoString).toLocaleString(undefined, {
    dateStyle: "long",
    timeStyle: "short",
  });
}

function pad2(n) {
  return String(n).padStart(2, "0");
}

function pluralize(count, singular, plural) {
  return `${count} ${count === 1 ? singular : plural}`;
}

export default function Results() {
  const [status, setStatus] = useState("loading");
  const [results, setResults] = useState(null);
  const [error, setError] = useState("");

  const [history, setHistory] = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const [expandedIds, setExpandedIds] = useState(() => new Set());
  const [historyDetails, setHistoryDetails] = useState({});

  useEffect(() => {
    getResults()
      .then((data) => {
        setResults(data);
        setStatus("loaded");
      })
      .catch((err) => {
        setError(err.message);
        setStatus("error");
      });

    // History is secondary to the headline result -- if it fails to load,
    // don't block or error out the main results view over it.
    getResultsHistory()
      .then(setHistory)
      .catch(() => setHistory([]));
  }, []);

  function toggleDraw(drawId) {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(drawId)) {
        next.delete(drawId);
      } else {
        next.add(drawId);
      }
      return next;
    });
    if (!historyDetails[drawId]) {
      setHistoryDetails((prev) => ({ ...prev, [drawId]: { status: "loading" } }));
      getResultsHistoryDetail(drawId)
        .then((detail) => {
          setHistoryDetails((prev) => ({ ...prev, [drawId]: { status: "loaded", detail } }));
        })
        .catch((err) => {
          setHistoryDetails((prev) => ({
            ...prev,
            [drawId]: { status: "error", error: err.message },
          }));
        });
    }
  }

  return (
    <div className="site-shell">
      <SiteHeader eyebrow="Results" />
      <main className="site-main">
        <div className="panel panel--raised">
          <h1>Results</h1>

          {status === "loading" && (
            <p className="loading-text">
              <span className="spinner" aria-hidden="true" />
              Loading results…
            </p>
          )}

          {status === "error" && <p className="error-text">{error}</p>}

          {status === "loaded" && !results.has_results && (
            <p className="empty-state">No draw has been completed yet. Check back soon.</p>
          )}

          {status === "loaded" && results.has_results && (
            <>
              <p className="results-date">Drawn {formatDate(results.drawn_at)}</p>
              <ol className="winners-list">
                {results.winners.map((winner) => (
                  <li key={winner.position} className="winner-row">
                    <span className="winner-tile">{pad2(winner.position)}</span>
                    <span className="winner-name">{winner.name}</span>
                  </li>
                ))}
              </ol>
            </>
          )}
        </div>

        {status === "loaded" && results.has_results && history !== null && (
          <section className="section panel history-section">
            <h2>Previous draws</h2>
            <p className="helper-text">
              History covers every completed draw since the last ballot reset.
            </p>

            {history.length === 0 ? (
              <p className="helper-text">No previous draws yet.</p>
            ) : (
              <>
                <button
                  type="button"
                  className="secondary-button"
                  aria-expanded={showHistory}
                  onClick={() => setShowHistory((value) => !value)}
                >
                  {showHistory ? "Hide previous draws" : "View previous draws"}{" "}
                  <span className="mono">({history.length})</span>
                </button>

                {showHistory && (
                  <div className="history-list">
                    {history.map((draw) => {
                      const state = historyDetails[draw.id];
                      const isExpanded = expandedIds.has(draw.id);
                      const bodyId = `history-body-${draw.id}`;
                      return (
                        <div key={draw.id} className="history-item">
                          <button
                            type="button"
                            className="history-item__toggle"
                            aria-expanded={isExpanded}
                            aria-controls={bodyId}
                            onClick={() => toggleDraw(draw.id)}
                          >
                            <span className="history-item__meta">
                              <span className="mono">{formatDate(draw.drawn_at)}</span>
                              <span className="badge badge--neutral">
                                {pluralize(draw.winner_count, "winner", "winners")}
                              </span>
                            </span>
                            <span className="history-item__chevron" aria-hidden="true">
                              {isExpanded ? "−" : "+"}
                            </span>
                          </button>

                          {isExpanded && (
                            <div id={bodyId} className="history-item__body">
                              {(!state || state.status === "loading") && (
                                <p className="loading-text">
                                  <span className="spinner" aria-hidden="true" />
                                  Loading winners…
                                </p>
                              )}
                              {state?.status === "error" && (
                                <p className="error-text">{state.error}</p>
                              )}
                              {state?.status === "loaded" && (
                                <ol className="winners-list">
                                  {state.detail.winners.map((winner) => (
                                    <li key={winner.position} className="winner-row">
                                      <span className="winner-tile">
                                        {pad2(winner.position)}
                                      </span>
                                      <span className="winner-name">{winner.name}</span>
                                    </li>
                                  ))}
                                </ol>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </>
            )}
          </section>
        )}

        <Link className="nav-link" to="/">
          Back to entry form
        </Link>
      </main>
    </div>
  );
}
