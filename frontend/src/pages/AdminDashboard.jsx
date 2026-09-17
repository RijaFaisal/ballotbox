import { Fragment, useEffect, useState } from "react";
import SiteHeader from "../components/SiteHeader.jsx";
import {
  UnauthorizedError,
  clearToken,
  createDraw,
  createProduct,
  downloadDrawPdf,
  getBallotStatus,
  listCandidatesForProduct,
  listDrawsForProduct,
  listProducts,
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

function statusBadgeClass(drawStatus) {
  if (drawStatus === "completed") return "badge badge--success";
  if (drawStatus === "failed") return "badge badge--danger";
  return "badge badge--neutral";
}

export default function AdminDashboard() {
  const [products, setProducts] = useState(null);
  const [ballotStatus, setBallotStatus] = useState(null);
  const [loadError, setLoadError] = useState("");

  const [newProductName, setNewProductName] = useState("");
  const [createStatus, setCreateStatus] = useState("idle");
  const [createError, setCreateError] = useState("");

  const [toggleStatus, setToggleStatus] = useState("idle");
  const [toggleError, setToggleError] = useState("");

  const [resetInput, setResetInput] = useState("");
  const [resetStatus, setResetStatus] = useState("idle");
  const [resetError, setResetError] = useState("");
  const [resetSummary, setResetSummary] = useState(null);

  const [expandedProductIds, setExpandedProductIds] = useState(() => new Set());
  const [candidatesByProduct, setCandidatesByProduct] = useState({});
  const [drawsByProduct, setDrawsByProduct] = useState({});
  const [runDrawState, setRunDrawState] = useState({});
  const [exportErrorByDraw, setExportErrorByDraw] = useState({});

  function loadDashboardData() {
    return Promise.all([listProducts(), getBallotStatus()]).then(
      ([productsData, statusData]) => {
        setProducts(productsData);
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

  function handleCreateProduct(event) {
    event.preventDefault();
    const name = newProductName.trim();
    if (!name) {
      setCreateError("Enter a product name.");
      return;
    }

    setCreateStatus("submitting");
    setCreateError("");

    createProduct(name)
      .then((product) => {
        setProducts((prev) => [product, ...(prev ?? [])]);
        setNewProductName("");
        setCreateStatus("idle");
      })
      .catch((err) => {
        if (err instanceof UnauthorizedError) return;
        setCreateStatus("idle");
        setCreateError(
          err.status === 409 ? "A product with this name already exists." : err.message
        );
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

  function loadCandidates(productId) {
    setCandidatesByProduct((prev) => ({ ...prev, [productId]: { status: "loading" } }));
    listCandidatesForProduct(productId)
      .then((candidates) => {
        setCandidatesByProduct((prev) => ({
          ...prev,
          [productId]: { status: "loaded", candidates },
        }));
      })
      .catch((err) => {
        if (err instanceof UnauthorizedError) return;
        setCandidatesByProduct((prev) => ({
          ...prev,
          [productId]: { status: "error", error: err.message },
        }));
      });
  }

  function loadDraws(productId) {
    setDrawsByProduct((prev) => ({ ...prev, [productId]: { status: "loading" } }));
    listDrawsForProduct(productId)
      .then((draws) => {
        setDrawsByProduct((prev) => ({ ...prev, [productId]: { status: "loaded", draws } }));
      })
      .catch((err) => {
        if (err instanceof UnauthorizedError) return;
        setDrawsByProduct((prev) => ({
          ...prev,
          [productId]: { status: "error", error: err.message },
        }));
      });
  }

  function toggleProductRow(productId) {
    setExpandedProductIds((prev) => {
      const next = new Set(prev);
      if (next.has(productId)) {
        next.delete(productId);
      } else {
        next.add(productId);
      }
      return next;
    });
    if (!candidatesByProduct[productId]) loadCandidates(productId);
    if (!drawsByProduct[productId]) loadDraws(productId);
  }

  function handleRunDraw(productId) {
    setRunDrawState((prev) => ({ ...prev, [productId]: { status: "submitting" } }));

    createDraw(productId)
      .then(() => {
        setRunDrawState((prev) => ({ ...prev, [productId]: { status: "idle" } }));
        loadDraws(productId);
        loadCandidates(productId);
      })
      .catch((err) => {
        if (err instanceof UnauthorizedError) return;
        setRunDrawState((prev) => ({
          ...prev,
          [productId]: { status: "idle", error: err.message },
        }));
      });
  }

  function handleDownloadPdf(productId, drawId) {
    setExportErrorByDraw((prev) => ({ ...prev, [drawId]: "" }));
    downloadDrawPdf(productId, drawId).catch((err) => {
      if (err instanceof UnauthorizedError) return;
      setExportErrorByDraw((prev) => ({ ...prev, [drawId]: err.message }));
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
        setExpandedProductIds(new Set());
        setCandidatesByProduct({});
        setDrawsByProduct({});
        setRunDrawState({});
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

  const isLoading = products === null || ballotStatus === null;

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

            <section className="panel">
              <h2>New product</h2>
              <form onSubmit={handleCreateProduct} className="run-draw-form">
                <div className="field">
                  <label htmlFor="productName">Product name</label>
                  <input
                    id="productName"
                    value={newProductName}
                    onChange={(e) => setNewProductName(e.target.value)}
                    placeholder="e.g. Grand Prize"
                  />
                </div>
                {createError && <p className="error-text">{createError}</p>}
                <button
                  type="submit"
                  className="primary-button"
                  disabled={createStatus === "submitting"}
                >
                  {createStatus === "submitting" ? "Creating…" : "Create product"}
                </button>
              </form>
            </section>

            <section className="section tinted-section">
              <h2>
                Products <span className="mono">({products.length})</span>
              </h2>
              {products.length === 0 ? (
                <p className="empty-state">No products yet. Create one above.</p>
              ) : (
                <div className="table-scroll">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Created</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {products.map((product) => {
                        const isExpanded = expandedProductIds.has(product.id);
                        const candidateState = candidatesByProduct[product.id];
                        const drawState = drawsByProduct[product.id];
                        const runState = runDrawState[product.id] ?? { status: "idle" };
                        const candidateCount =
                          candidateState?.status === "loaded"
                            ? candidateState.candidates.length
                            : null;

                        return (
                          <Fragment key={product.id}>
                            <tr>
                              <td>{product.name}</td>
                              <td>{formatDateTime(product.created_at)}</td>
                              <td>
                                <button
                                  type="button"
                                  className="secondary-button small-button"
                                  aria-expanded={isExpanded}
                                  onClick={() => toggleProductRow(product.id)}
                                >
                                  {isExpanded ? "Hide" : "Manage"}
                                </button>
                              </td>
                            </tr>
                            {isExpanded && (
                              <tr>
                                <td colSpan={3} className="data-table-expanded">
                                  <h3>
                                    Candidates
                                    {candidateCount !== null && (
                                      <span className="mono"> ({candidateCount})</span>
                                    )}
                                  </h3>
                                  {(!candidateState || candidateState.status === "loading") && (
                                    <p className="loading-text">
                                      <span className="spinner" aria-hidden="true" />
                                      Loading candidates…
                                    </p>
                                  )}
                                  {candidateState?.status === "error" && (
                                    <p className="error-text">{candidateState.error}</p>
                                  )}
                                  {candidateState?.status === "loaded" &&
                                    (candidateState.candidates.length === 0 ? (
                                      <p className="empty-state">No candidates yet.</p>
                                    ) : (
                                      <div className="table-scroll">
                                        <table className="data-table">
                                          <thead>
                                            <tr>
                                              <th>Name</th>
                                              <th>Email</th>
                                              <th>CNIC</th>
                                              <th>Entered</th>
                                            </tr>
                                          </thead>
                                          <tbody>
                                            {candidateState.candidates.map((candidate) => (
                                              <tr key={candidate.id}>
                                                <td>{candidate.name}</td>
                                                <td>{candidate.email ?? "—"}</td>
                                                <td>{candidate.cnic ?? "—"}</td>
                                                <td>{formatDateTime(candidate.created_at)}</td>
                                              </tr>
                                            ))}
                                          </tbody>
                                        </table>
                                      </div>
                                    ))}

                                  <h3>Draw</h3>
                                  <button
                                    type="button"
                                    className="primary-button small-button"
                                    onClick={() => handleRunDraw(product.id)}
                                    disabled={runState.status === "submitting"}
                                  >
                                    {runState.status === "submitting"
                                      ? "Running draw…"
                                      : "Run draw"}
                                  </button>
                                  {runState.error && <p className="error-text">{runState.error}</p>}

                                  {(!drawState || drawState.status === "loading") && (
                                    <p className="loading-text">
                                      <span className="spinner" aria-hidden="true" />
                                      Loading draws…
                                    </p>
                                  )}
                                  {drawState?.status === "error" && (
                                    <p className="error-text">{drawState.error}</p>
                                  )}
                                  {drawState?.status === "loaded" &&
                                    (drawState.draws.length === 0 ? (
                                      <p className="empty-state">No draws yet.</p>
                                    ) : (
                                      <div className="table-scroll">
                                        <table className="data-table">
                                          <thead>
                                            <tr>
                                              <th>ID</th>
                                              <th>Status</th>
                                              <th>Winner</th>
                                              <th>Drawn at</th>
                                              <th>Seed</th>
                                              <th>Actions</th>
                                            </tr>
                                          </thead>
                                          <tbody>
                                            {drawState.draws.map((draw) => (
                                              <tr key={draw.id}>
                                                <td>{draw.id}</td>
                                                <td>
                                                  <span className={statusBadgeClass(draw.status)}>
                                                    {draw.status}
                                                  </span>
                                                </td>
                                                <td>{draw.winners[0]?.candidate.name ?? "—"}</td>
                                                <td>
                                                  {draw.drawn_at
                                                    ? formatDateTime(draw.drawn_at)
                                                    : "—"}
                                                </td>
                                                <td className="seed-cell">{draw.seed}</td>
                                                <td>
                                                  {draw.status === "completed" ? (
                                                    <div className="table-actions">
                                                      <button
                                                        type="button"
                                                        className="secondary-button small-button"
                                                        onClick={() =>
                                                          handleDownloadPdf(product.id, draw.id)
                                                        }
                                                      >
                                                        PDF
                                                      </button>
                                                    </div>
                                                  ) : (
                                                    "—"
                                                  )}
                                                  {exportErrorByDraw[draw.id] && (
                                                    <p className="error-text">
                                                      {exportErrorByDraw[draw.id]}
                                                    </p>
                                                  )}
                                                </td>
                                              </tr>
                                            ))}
                                          </tbody>
                                        </table>
                                      </div>
                                    ))}
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
      </main>
    </div>
  );
}
