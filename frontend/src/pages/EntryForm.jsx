import { useState } from "react";
import { submitEntry } from "../api/client.js";

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
      })
      .catch((err) => {
        setStatus("idle");
        setServerError(err.message);
      });
  }

  if (status === "success") {
    return (
      <div className="page">
        <div className="card">
          <h1>You're entered</h1>
          <p>Thanks, your entry has been recorded.</p>
          <button type="button" onClick={() => setStatus("idle")}>
            Submit another entry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="card">
        <h1>Enter the ballot</h1>
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

          <button type="submit" disabled={status === "submitting"}>
            {status === "submitting" ? "Submitting..." : "Submit entry"}
          </button>
        </form>
      </div>
    </div>
  );
}
