import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import AdminLayout from "../components/AdminLayout.jsx";
import ProductsSidebar from "../components/ProductsSidebar.jsx";
import { DownloadIcon, PlayIcon, ResetIcon } from "../components/icons.jsx";
import {
  UnauthorizedError,
  clearProductCandidates,
  clearProductDraws,
  createDraw,
  downloadCandidatesCsv,
  downloadDrawPdf,
  getProduct,
  listCandidatesForProduct,
  listDrawsForProduct,
} from "../api/client.js";
import { formatDateTime, statusBadgeClass } from "../utils/format.js";

const CANDIDATES_PAGE_SIZE = 10;

function filterCandidates(candidates, search) {
  const term = search.trim().toLowerCase();
  if (!term) return candidates;
  return candidates.filter(
    (c) =>
      c.name.toLowerCase().includes(term) ||
      (c.email ?? "").toLowerCase().includes(term) ||
      (c.cnic ?? "").toLowerCase().includes(term)
  );
}

export default function AdminProductDetail() {
  const { productId } = useParams();

  const [product, setProduct] = useState(null);
  const [loadError, setLoadError] = useState("");

  const [candidateState, setCandidateState] = useState({ status: "loading" });
  const [drawState, setDrawState] = useState({ status: "loading" });

  const [candidateSearch, setCandidateSearch] = useState("");
  const [candidatePage, setCandidatePage] = useState(1);
  const [exportCsvError, setExportCsvError] = useState("");
  const [clearCandidatesState, setClearCandidatesState] = useState({ status: "idle" });

  const [runDrawState, setRunDrawState] = useState({ status: "idle" });
  const [clearDrawsState, setClearDrawsState] = useState({ status: "idle" });
  const [exportErrorByDraw, setExportErrorByDraw] = useState({});

  function loadCandidates() {
    setCandidateState({ status: "loading" });
    listCandidatesForProduct(productId)
      .then((candidates) => setCandidateState({ status: "loaded", candidates }))
      .catch((err) => {
        if (err instanceof UnauthorizedError) return;
        setCandidateState({ status: "error", error: err.message });
      });
  }

  function loadDraws() {
    setDrawState({ status: "loading" });
    listDrawsForProduct(productId)
      .then((draws) => setDrawState({ status: "loaded", draws }))
      .catch((err) => {
        if (err instanceof UnauthorizedError) return;
        setDrawState({ status: "error", error: err.message });
      });
  }

  useEffect(() => {
    getProduct(productId)
      .then(setProduct)
      .catch((err) => {
        if (err instanceof UnauthorizedError) return;
        setLoadError(err.message);
      });
    loadCandidates();
    loadDraws();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [productId]);

  function handleRunDraw() {
    setRunDrawState({ status: "submitting" });

    createDraw(productId)
      .then(() => {
        setRunDrawState({ status: "idle" });
        loadDraws();
        loadCandidates();
      })
      .catch((err) => {
        if (err instanceof UnauthorizedError) return;
        setRunDrawState({ status: "idle", error: err.message });
      });
  }

  function handleDownloadPdf(drawId) {
    setExportErrorByDraw((prev) => ({ ...prev, [drawId]: "" }));
    downloadDrawPdf(productId, drawId).catch((err) => {
      if (err instanceof UnauthorizedError) return;
      setExportErrorByDraw((prev) => ({ ...prev, [drawId]: err.message }));
    });
  }

  function handleExportCandidatesCsv() {
    setExportCsvError("");
    downloadCandidatesCsv(productId).catch((err) => {
      if (err instanceof UnauthorizedError) return;
      setExportCsvError(err.message);
    });
  }

  function handleClearDraws() {
    if (
      !window.confirm(
        "Clear all draws for this product? Candidates are kept, so you can run a fresh draw right after."
      )
    ) {
      return;
    }

    setClearDrawsState({ status: "submitting" });

    clearProductDraws(productId)
      .then(() => {
        setClearDrawsState({ status: "idle" });
        loadDraws();
      })
      .catch((err) => {
        if (err instanceof UnauthorizedError) return;
        setClearDrawsState({ status: "idle", error: err.message });
      });
  }

  function handleClearCandidates() {
    if (
      !window.confirm(
        "Clear all candidates for this product? This also clears its draw history, since past winners are recorded against these candidates."
      )
    ) {
      return;
    }

    setClearCandidatesState({ status: "submitting" });

    clearProductCandidates(productId)
      .then(() => {
        setClearCandidatesState({ status: "idle" });
        loadCandidates();
        loadDraws();
      })
      .catch((err) => {
        if (err instanceof UnauthorizedError) return;
        setClearCandidatesState({ status: "idle", error: err.message });
      });
  }

  const isLoading = product === null && !loadError;
  const candidateCount =
    candidateState.status === "loaded" ? candidateState.candidates.length : null;
  const allCandidates = candidateState.status === "loaded" ? candidateState.candidates : [];
  const filteredCandidates = filterCandidates(allCandidates, candidateSearch);
  const totalPages = Math.max(1, Math.ceil(filteredCandidates.length / CANDIDATES_PAGE_SIZE));
  const currentPage = Math.min(candidatePage, totalPages);
  const pageCandidates = filteredCandidates.slice(
    (currentPage - 1) * CANDIDATES_PAGE_SIZE,
    currentPage * CANDIDATES_PAGE_SIZE
  );

  return (
    <AdminLayout heading={product?.name ?? "Product"} sidebar={<ProductsSidebar />}>
      {loadError && <p className="error-text">{loadError}</p>}
      {isLoading && !loadError && (
        <p className="loading-text">
          <span className="spinner" aria-hidden="true" />
          Loading product…
        </p>
      )}

      {product && (
        <>
          <section className="section">
            <span
              className={product.is_open ? "badge badge--success" : "badge badge--danger"}
            >
              {product.is_open ? "Open" : "Closed"}
            </span>
          </section>

          <section className="section panel">
            <h2>
              Candidates
              {candidateCount !== null && <span className="mono"> ({candidateCount})</span>}
            </h2>
            {(candidateState.status === "loading") && (
              <p className="loading-text">
                <span className="spinner" aria-hidden="true" />
                Loading candidates…
              </p>
            )}
            {candidateState.status === "error" && (
              <p className="error-text">{candidateState.error}</p>
            )}
            {candidateState.status === "loaded" && allCandidates.length === 0 && (
              <p className="empty-state">No candidates yet.</p>
            )}
            {candidateState.status === "loaded" && allCandidates.length > 0 && (
              <>
                <div className="field">
                  <label htmlFor="candidateSearch">Search candidates</label>
                  <input
                    id="candidateSearch"
                    value={candidateSearch}
                    onChange={(e) => {
                      setCandidateSearch(e.target.value);
                      setCandidatePage(1);
                    }}
                    placeholder="Search by name, email, or CNIC"
                  />
                </div>
                {filteredCandidates.length === 0 ? (
                  <p className="empty-state">No candidates match your search.</p>
                ) : (
                  <>
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
                          {pageCandidates.map((candidate) => (
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
                    {totalPages > 1 && (
                      <div className="table-actions">
                        <button
                          type="button"
                          className="secondary-button small-button"
                          onClick={() => setCandidatePage(currentPage - 1)}
                          disabled={currentPage <= 1}
                        >
                          Prev
                        </button>
                        <span className="helper-text">
                          Page {currentPage} of {totalPages}
                        </span>
                        <button
                          type="button"
                          className="secondary-button small-button"
                          onClick={() => setCandidatePage(currentPage + 1)}
                          disabled={currentPage >= totalPages}
                        >
                          Next
                        </button>
                      </div>
                    )}
                  </>
                )}
              </>
            )}
            <div className="table-actions">
              <button
                type="button"
                className="secondary-button small-button"
                onClick={handleExportCandidatesCsv}
                disabled={candidateCount === 0}
              >
                <DownloadIcon />
                Export CSV
              </button>
              <button
                type="button"
                className="warning-button small-button"
                onClick={handleClearCandidates}
                disabled={clearCandidatesState.status === "submitting" || candidateCount === 0}
              >
                <ResetIcon />
                {clearCandidatesState.status === "submitting" ? "Clearing…" : "Clear candidates"}
              </button>
            </div>
            {exportCsvError && <p className="error-text">{exportCsvError}</p>}
            {clearCandidatesState.error && (
              <p className="error-text">{clearCandidatesState.error}</p>
            )}
          </section>

          <section className="section panel">
            <h2>Draw</h2>
            <div className="table-actions">
              <button
                type="button"
                className="primary-button small-button"
                onClick={handleRunDraw}
                disabled={runDrawState.status === "submitting"}
              >
                <PlayIcon />
                {runDrawState.status === "submitting" ? "Running draw…" : "Run draw"}
              </button>
              <button
                type="button"
                className="warning-button small-button"
                onClick={handleClearDraws}
                disabled={
                  clearDrawsState.status === "submitting" ||
                  drawState.status !== "loaded" ||
                  drawState.draws.length === 0
                }
              >
                <ResetIcon />
                {clearDrawsState.status === "submitting" ? "Clearing…" : "Reset draws"}
              </button>
            </div>
            {runDrawState.error && <p className="error-text">{runDrawState.error}</p>}
            {clearDrawsState.error && <p className="error-text">{clearDrawsState.error}</p>}

            {drawState.status === "loading" && (
              <p className="loading-text">
                <span className="spinner" aria-hidden="true" />
                Loading draws…
              </p>
            )}
            {drawState.status === "error" && <p className="error-text">{drawState.error}</p>}
            {drawState.status === "loaded" &&
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
                            <span className={statusBadgeClass(draw.status)}>{draw.status}</span>
                          </td>
                          <td>{draw.winners[0]?.candidate.name ?? "—"}</td>
                          <td>{draw.drawn_at ? formatDateTime(draw.drawn_at) : "—"}</td>
                          <td className="seed-cell">{draw.seed}</td>
                          <td>
                            {draw.status === "completed" ? (
                              <div className="table-actions">
                                <button
                                  type="button"
                                  className="secondary-button small-button"
                                  onClick={() => handleDownloadPdf(draw.id)}
                                >
                                  <DownloadIcon />
                                  PDF
                                </button>
                              </div>
                            ) : (
                              "—"
                            )}
                            {exportErrorByDraw[draw.id] && (
                              <p className="error-text">{exportErrorByDraw[draw.id]}</p>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ))}
          </section>
        </>
      )}
    </AdminLayout>
  );
}
