import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getResults } from "../api/client.js";

function formatDate(isoString) {
  return new Date(isoString).toLocaleString(undefined, {
    dateStyle: "long",
    timeStyle: "short",
  });
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
    <div className="page">
      <div className="card">
        <h1>Results</h1>

        {status === "loading" && <p>Loading results...</p>}

        {status === "error" && <p className="error-text">{error}</p>}

        {status === "loaded" && !results.has_results && (
          <p>No draw has been completed yet. Check back soon.</p>
        )}

        {status === "loaded" && results.has_results && (
          <>
            <p className="results-date">Drawn on {formatDate(results.drawn_at)}</p>
            <ol className="winners-list">
              {results.winners.map((winner) => (
                <li key={winner.position}>
                  <span className="winner-position">#{winner.position}</span> {winner.name}
                </li>
              ))}
            </ol>
          </>
        )}

        <Link className="nav-link" to="/">
          Back to entry form
        </Link>
      </div>
    </div>
  );
}
