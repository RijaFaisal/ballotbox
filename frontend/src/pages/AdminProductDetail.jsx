import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import AdminLayout from "../components/AdminLayout.jsx";
import ProductsSidebar from "../components/ProductsSidebar.jsx";
import ProductStatusPill from "../components/ProductStatusPill.jsx";
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
  setProductClosesAt,
} from "../api/client.js";
import { formatDateTime, productStatusLabel, statusBadgeClass } from "../utils/format.js";

function toDatetimeLocalValue(isoString) {
  if (!isoString) return "";
  const date = new Date(isoString);
  const pad = (n) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(
    date.getHours()
  )}:${pad(date.getMinutes())}`;
}

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

  const [winnerCount, setWinnerCount] = useState("1");
  const [runDrawState, setRunDrawState] = useState({ status: "idle" });
  const [clearDrawsState, setClearDrawsState] = useState({ status: "idle" });
  const [exportErrorByDraw, setExportErrorByDraw] = useState({});

  const [closesAtInput, setClosesAtInput] = useState("");
  const [scheduleState, setScheduleState] = useState({ status: "idle" });

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
      .then((loaded) => {
        setProduct(loaded);
        setClosesAtInput(toDatetimeLocalValue(loaded.closes_at));
      })
      .catch((err) => {
        if (err instanceof UnauthorizedError) return;
        setLoadError(err.message);
      });
    loadCandidates();
    loadDraws();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [productId]);

  function handleRunDraw() {
    const count = Math.max(1, Number(winnerCount) || 1);
    setRunDrawState({ status: "submitting" });

    createDraw(productId, count)
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

  function handleSaveSchedule(event) {
    event.preventDefault();
    setScheduleState({ status: "submitting" });

    const closesAt = closesAtInput ? new Date(closesAtInput).toISOString() : null;

    setProductClosesAt(productId, closesAt)
      .then((updated) => {
        setProduct(updated);
        setScheduleState({ status: "idle" });
      })
      .catch((err) => {
        if (err instanceof UnauthorizedError) return;
        setScheduleState({ status: "idle", error: err.message });
      });
  }

  function handleClearSchedule() {
    setScheduleState({ status: "submitting" });

    setProductClosesAt(productId, null)
      .then((updated) => {
        setProduct(updated);
        setClosesAtInput("");
        setScheduleState({ status: "idle" });
      })
      .catch((err) => {
        if (err instanceof UnauthorizedError) return;
        setScheduleState({ status: "idle", error: err.message });
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
    <AdminLayout
      heading={product?.name ?? "Product"}
      headingExtra={
        product && (
          <ProductStatusPill
            isOpen={product.effectively_open}
            label={productStatusLabel(product)}
          />
        )
      }
      sidebar={<ProductsSidebar />}
    >
      {loadError && <p className="error-text">{loadError}</p>}
      {isLoading && !loadError && (
        <p className="loading-text">
          <span className="spinner" aria-hidden="true" />
          Loading product…
        </p>
      )}

      {product && (
        <>
          <section className="section panel">
            <h2>Schedule</h2>
            <p className="helper-text">
              Entries close automatically at this time, regardless of the open/closed toggle
              above. Leave blank to close only by hand.
            </p>
            <form onSubmit={handleSaveSchedule} className="run-draw-form">
              <div className="field">
                <label htmlFor="closesAt">Closes at</label>
                <input
                  id="closesAt"
                  type="datetime-local"
                  value={closesAtInput}
                  onChange={(e) => setClosesAtInput(e.target.value)}
                />
              </div>
              {scheduleState.error && <p className="error-text">{scheduleState.error}</p>}
              <div className="table-actions">
                <button
                  type="submit"
                  className="primary-button small-button"
                  disabled={scheduleState.status === "submitting"}
                >
                  {scheduleState.status === "submitting" ? "Saving…" : "Save schedule"}
                </button>
                {product.closes_at && (
                  <button
                    type="button"
                    className="secondary-button small-button"
                    onClick={handleClearSchedule}
                    disabled={scheduleState.status === "submitting"}
                  >
                    Clear schedule
                  </button>
                )}
              </div>
            </form>
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
            <div className="field run-draw-form">
              <label htmlFor="winnerCount">Number of winners</label>
              <input
                id="winnerCount"
                type="number"
                min="1"
                value={winnerCount}
                onChange={(e) => setWinnerCount(e.target.value)}
              />
            </div>
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
                        <th>Winners</th>
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
                          <td>
                            {draw.winners.length === 0 ? (
                              "—"
                            ) : draw.winners.length === 1 ? (
                              draw.winners[0].candidate.name
                            ) : (
                              <ol className="winners-inline-list">
                                {draw.winners.map((winner) => (
                                  <li key={winner.position}>{winner.candidate.name}</li>
                                ))}
                              </ol>
                            )}
                          </td>
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
