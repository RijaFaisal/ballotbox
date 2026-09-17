import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import SiteHeader from "../components/SiteHeader.jsx";
import { getBallotStatus, getEntryCount, submitEntry } from "../api/client.js";

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const CNIC_PATTERN = /^\d{5}-?\d{7}-?\d{1}$/;

function validateIdentifier(value) {
  const trimmed = value.trim();
  if (EMAIL_PATTERN.test(trimmed) || CNIC_PATTERN.test(trimmed)) {
    return null;
  }
  return "Enter a valid email address or CNIC (e.g. 12345-1234567-1)";
}

export default function EntryForm() {
  const [name, setName] = useState("");
  const [identifier, setIdentifier] = useState("");
  const [errors, setErrors] = useState({});
  const [status, setStatus] = useState("idle");
  const [serverError, setServerError] = useState("");

  const [pageState, setPageState] = useState("loading"); // loading | closed | ready
  const [entryCount, setEntryCount] = useState(null);

  useEffect(() => {
    Promise.all([getBallotStatus(), getEntryCount()])
      .then(([ballotStatus, countData]) => {
        setEntryCount(countData.count);
        setPageState(ballotStatus.is_open ? "ready" : "closed");
      })
      .catch(() => {
        // If the status/count check itself fails (e.g. a network blip),
        // don't block the form on it -- the backend still enforces the
        // real open/closed rule on submit.
        setPageState("ready");
      });
  }, []);

  function refreshEntryCount() {
    getEntryCount()
      .then((data) => setEntryCount(data.count))
      .catch(() => {});
  }

  function handleSubmit(event) {
    event.preventDefault();
    const nextErrors = {};

    if (!name.trim()) {
      nextErrors.name = "Name is required";
    }

    const identifierError = validateIdentifier(identifier);
    if (identifierError) {
      nextErrors.identifier = identifierError;
    }

    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) {
      return;
    }

    setStatus("submitting");
    setServerError("");

    submitEntry({ name: name.trim(), identifier: identifier.trim() })
      .then(() => {
        setStatus("success");
        setName("");
        setIdentifier("");
        refreshEntryCount();
      })
      .catch((err) => {
        setStatus("idle");
        if (err.status === 409) {
          setServerError("Looks like you're already entered — each person can only enter once.");
        } else {
          setServerError(err.message);
        }
      });
  }

  if (pageState === "loading") {
    return (
      <div className="site-shell">
        <SiteHeader />
        <main className="site-main">
          <p className="loading-text">
            <span className="spinner" aria-hidden="true" />
            Loading…
          </p>
        </main>
      </div>
    );
  }

  if (pageState === "closed") {
    return (
      <div className="site-shell">
        <SiteHeader />
        <main className="site-main">
          <div className="panel panel--raised">
            <span className="eyebrow">Ballot status</span>
            <h1>Ballot closed</h1>
            <p>This ballot isn't accepting new entries right now. Check back later.</p>
            <Link className="nav-link" to="/results">
              View results
            </Link>
          </div>
        </main>
      </div>
    );
  }

  if (status === "success") {
    return (
      <div className="site-shell">
        <SiteHeader />
        <main className="site-main">
          <div className="panel panel--raised">
            <h1>You're in.</h1>
            <p>Thanks — your entry has been recorded.</p>
            {entryCount !== null && (
              <p className="stat-chip">
                <strong>{entryCount}</strong>{" "}
                {entryCount === 1 ? "person has" : "people have"} entered
              </p>
            )}
            <button type="button" onClick={() => setStatus("idle")}>
              Submit another entry
            </button>
            <Link className="nav-link" to="/results">
              View results
            </Link>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="site-shell">
      <SiteHeader />
      <main className="site-main">
        <div className="panel panel--raised">
          <h1>Enter the ballot</h1>
          {entryCount !== null && (
            <p className="stat-chip">
              <strong>{entryCount}</strong>{" "}
              {entryCount === 1 ? "person has" : "people have"} entered
            </p>
          )}
          <form onSubmit={handleSubmit} noValidate>
            <div className="field">
              <label htmlFor="name">Name</label>
              <input id="name" value={name} onChange={(e) => setName(e.target.value)} />
              {errors.name && <p className="error-text">{errors.name}</p>}
            </div>

            <div className="field">
              <label htmlFor="identifier">Email or CNIC</label>
              <input
                id="identifier"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
              />
              {errors.identifier && <p className="error-text">{errors.identifier}</p>}
            </div>

            {serverError && <p className="error-text">{serverError}</p>}

            <button type="submit" className="primary-button" disabled={status === "submitting"}>
              {status === "submitting" ? "Submitting…" : "Submit entry"}
            </button>
          </form>
          <Link className="nav-link" to="/results">
            View results
          </Link>
        </div>
      </main>
    </div>
  );
}
