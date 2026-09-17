import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import SiteHeader from "../components/SiteHeader.jsx";
import { getResults } from "../api/client.js";

function formatDate(isoString) {
  return new Date(isoString).toLocaleString(undefined, {
    dateStyle: "long",
    timeStyle: "short",
  });
}

function pad2(n) {
  return String(n).padStart(2, "0");
}

export default function Results() {
  const [status, setStatus] = useState("loading");
  const [results, setResults] = useState(null);
  const [error, setError] = useState("");

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
  }, []);

  return (
    <div className="site-shell">
      <SiteHeader eyebrow="Results" />
      <main className="site-main">
        <div className="panel panel--raised">
          <span className="eyebrow">Official results</span>
          <h1>Results</h1>

          {status === "loading" && <p className="helper-text">Loading results…</p>}

          {status === "error" && <p className="error-text">{error}</p>}

          {status === "loaded" && !results.has_results && (
            <p>No draw has been completed yet. Check back soon.</p>
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

          <Link className="nav-link" to="/">
            Back to entry form
          </Link>
        </div>
      </main>
    </div>
  );
}
