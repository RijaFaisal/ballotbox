import { useEffect, useState } from "react";
import AdminLayout from "../components/AdminLayout.jsx";
import { PlusIcon, TrashIcon } from "../components/icons.jsx";
import {
  UnauthorizedError,
  createAdminAccount,
  deleteAdminAccount,
  listAdmins,
  resetBallot,
} from "../api/client.js";
import { pluralize } from "../utils/format.js";

const RESET_CONFIRM_PHRASE = "RESET";

export default function AdminControls() {
  const [admins, setAdmins] = useState(null);
  const [adminsError, setAdminsError] = useState("");

  const [newAdminUsername, setNewAdminUsername] = useState("");
  const [newAdminPassword, setNewAdminPassword] = useState("");
  const [createAdminStatus, setCreateAdminStatus] = useState("idle");
  const [createAdminError, setCreateAdminError] = useState("");

  const [deleteAdminState, setDeleteAdminState] = useState({});

  const [resetInput, setResetInput] = useState("");
  const [resetStatus, setResetStatus] = useState("idle");
  const [resetError, setResetError] = useState("");
  const [resetSummary, setResetSummary] = useState(null);

  function loadAdmins() {
    listAdmins()
      .then(setAdmins)
      .catch((err) => {
        if (err instanceof UnauthorizedError) return;
        setAdminsError(err.message);
      });
  }

  useEffect(() => {
    loadAdmins();
  }, []);

  function handleCreateAdmin(event) {
    event.preventDefault();
    const username = newAdminUsername.trim();
    if (!username) {
      setCreateAdminError("Enter a username.");
      return;
    }
    if (newAdminPassword.length < 8) {
      setCreateAdminError("Password must be at least 8 characters.");
      return;
    }

    setCreateAdminStatus("submitting");
    setCreateAdminError("");

    createAdminAccount({ username, password: newAdminPassword })
      .then((newAdmin) => {
        setAdmins((prev) => [...(prev ?? []), newAdmin]);
        setNewAdminUsername("");
        setNewAdminPassword("");
        setCreateAdminStatus("idle");
      })
      .catch((err) => {
        if (err instanceof UnauthorizedError) return;
        setCreateAdminStatus("idle");
        setCreateAdminError(
          err.status === 409 ? "An admin with this username already exists." : err.message
        );
      });
  }

  function handleDeleteAdmin(admin) {
    if (!window.confirm(`Delete admin account "${admin.username}"? This cannot be undone.`)) {
      return;
    }

    setDeleteAdminState((prev) => ({ ...prev, [admin.id]: { status: "submitting" } }));

    deleteAdminAccount(admin.id)
      .then(() => {
        setAdmins((prev) => (prev ?? []).filter((a) => a.id !== admin.id));
        setDeleteAdminState((prev) => {
          const next = { ...prev };
          delete next[admin.id];
          return next;
        });
      })
      .catch((err) => {
        if (err instanceof UnauthorizedError) return;
        setDeleteAdminState((prev) => ({
          ...prev,
          [admin.id]: { status: "idle", error: err.message },
        }));
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
      })
      .catch((err) => {
        if (err instanceof UnauthorizedError) return;
        setResetStatus("idle");
        setResetError(err.message);
      });
  }

  return (
    <AdminLayout>
      {adminsError && <p className="error-text">{adminsError}</p>}
      {admins === null ? (
        <p className="loading-text">
          <span className="spinner" aria-hidden="true" />
          Loading admins…
        </p>
      ) : (
        <>
          <section className="section tinted-section">
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Username</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {admins.map((admin) => {
                    const state = deleteAdminState[admin.id] ?? { status: "idle" };
                    return (
                      <tr key={admin.id}>
                        <td>{admin.username}</td>
                        <td>
                          <button
                            type="button"
                            className="danger-button small-button"
                            onClick={() => handleDeleteAdmin(admin)}
                            disabled={state.status === "submitting" || admins.length <= 1}
                          >
                            <TrashIcon />
                            {state.status === "submitting" ? "Deleting…" : "Delete"}
                          </button>
                          {state.error && <p className="error-text">{state.error}</p>}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>

          <section className="section panel">
            <h2>Add admin</h2>
            <form onSubmit={handleCreateAdmin} className="run-draw-form">
              <div className="field">
                <label htmlFor="newAdminUsername">Username</label>
                <input
                  id="newAdminUsername"
                  value={newAdminUsername}
                  onChange={(e) => setNewAdminUsername(e.target.value)}
                />
              </div>
              <div className="field">
                <label htmlFor="newAdminPassword">Password (min 8 characters)</label>
                <input
                  id="newAdminPassword"
                  type="password"
                  value={newAdminPassword}
                  onChange={(e) => setNewAdminPassword(e.target.value)}
                />
              </div>
              {createAdminError && <p className="error-text">{createAdminError}</p>}
              <button
                type="submit"
                className="primary-button"
                disabled={createAdminStatus === "submitting"}
              >
                <PlusIcon />
                {createAdminStatus === "submitting" ? "Creating…" : "Create admin"}
              </button>
            </form>
          </section>

          <section className="section danger-zone">
            <h2>Reset ballot</h2>
            <p className="danger-warning">
              This permanently deletes every product, candidate, draw, and
              winner so a new set of events can start from zero. It does
              not affect admin accounts. Only do this between events, after
              any results you need have already been recorded elsewhere --
              it is not a way to undo or hide a completed draw.
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
                  Cleared {pluralize(resetSummary.products_deleted, "product", "products")},{" "}
                  {pluralize(resetSummary.candidates_deleted, "candidate", "candidates")},{" "}
                  {pluralize(resetSummary.draws_deleted, "draw", "draws")}, and{" "}
                  {pluralize(resetSummary.winners_deleted, "winner", "winners")}.
                </p>
              )}
              <button
                type="submit"
                className="danger-button"
                disabled={resetStatus === "submitting" || resetInput !== RESET_CONFIRM_PHRASE}
              >
                <TrashIcon />
                {resetStatus === "submitting" ? "Resetting…" : "Reset ballot"}
              </button>
            </form>
          </section>
        </>
      )}
    </AdminLayout>
  );
}
