import { useState } from "react";
import { useNavigate } from "react-router-dom";
import AdminLayout from "../components/AdminLayout.jsx";
import ProductsSidebar from "../components/ProductsSidebar.jsx";
import { PlusIcon, UploadIcon } from "../components/icons.jsx";
import { UnauthorizedError, bulkUploadProducts, createProduct } from "../api/client.js";
import { pluralize } from "../utils/format.js";

export default function AdminProductNew() {
  const navigate = useNavigate();

  const [newProductName, setNewProductName] = useState("");
  const [newProductClosesAt, setNewProductClosesAt] = useState("");
  const [createStatus, setCreateStatus] = useState("idle");
  const [createError, setCreateError] = useState("");

  const [bulkUploadFile, setBulkUploadFile] = useState(null);
  const [bulkUploadStatus, setBulkUploadStatus] = useState("idle");
  const [bulkUploadError, setBulkUploadError] = useState("");
  const [bulkUploadResult, setBulkUploadResult] = useState(null);
  const [bulkUploadInputKey, setBulkUploadInputKey] = useState(0);

  function handleCreateProduct(event) {
    event.preventDefault();
    const name = newProductName.trim();
    if (!name) {
      setCreateError("Enter a product name.");
      return;
    }

    setCreateStatus("submitting");
    setCreateError("");

    const closesAt = newProductClosesAt ? new Date(newProductClosesAt).toISOString() : null;

    createProduct(name, closesAt)
      .then((product) => {
        navigate(`/admin/products/${product.id}`);
      })
      .catch((err) => {
        if (err instanceof UnauthorizedError) return;
        setCreateStatus("idle");
        setCreateError(
          err.status === 409 ? "A product with this name already exists." : err.message
        );
      });
  }

  function handleBulkUploadProducts() {
    if (!bulkUploadFile) {
      setBulkUploadError("Choose a CSV file first.");
      return;
    }

    setBulkUploadStatus("submitting");
    setBulkUploadError("");
    setBulkUploadResult(null);

    bulkUploadProducts(bulkUploadFile)
      .then((result) => {
        setBulkUploadResult(result);
        setBulkUploadStatus("idle");
        setBulkUploadFile(null);
        setBulkUploadInputKey((key) => key + 1);
      })
      .catch((err) => {
        if (err instanceof UnauthorizedError) return;
        setBulkUploadStatus("idle");
        setBulkUploadError(err.message);
      });
  }

  return (
    <AdminLayout heading="New product" sidebar={<ProductsSidebar />}>
      <section className="section panel">
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
          <div className="field">
            <label htmlFor="productClosesAt">Closes at (optional)</label>
            <input
              id="productClosesAt"
              type="datetime-local"
              value={newProductClosesAt}
              onChange={(e) => setNewProductClosesAt(e.target.value)}
            />
            <p className="helper-text">
              Entries close automatically at this time. Leave blank to close only by hand.
            </p>
          </div>
          {createError && <p className="error-text">{createError}</p>}
          <button type="submit" className="primary-button" disabled={createStatus === "submitting"}>
            <PlusIcon />
            {createStatus === "submitting" ? "Creating…" : "Create product"}
          </button>
        </form>
      </section>

      <section className="section panel">
        <h2>Bulk upload products</h2>
        <p className="helper-text">
          CSV with a single <span className="mono">name</span> column and a header row. Each row
          creates a product; duplicate and blank names are skipped and reported below.
        </p>
        <div className="field">
          <label htmlFor="productsCsv">CSV file</label>
          <input
            key={bulkUploadInputKey}
            id="productsCsv"
            type="file"
            accept=".csv,text/csv"
            onChange={(e) => setBulkUploadFile(e.target.files?.[0] ?? null)}
          />
        </div>
        {bulkUploadError && <p className="error-text">{bulkUploadError}</p>}
        <button
          type="button"
          className="primary-button"
          onClick={handleBulkUploadProducts}
          disabled={bulkUploadStatus === "submitting"}
        >
          <UploadIcon />
          {bulkUploadStatus === "submitting" ? "Uploading…" : "Upload CSV"}
        </button>

        {bulkUploadResult && (
          <div className="last-draw-result">
            <h3>Upload summary</h3>
            <p>
              <strong>{pluralize(bulkUploadResult.created_count, "product", "products")}</strong>{" "}
              created.
              {bulkUploadResult.skipped.length > 0 && (
                <> {pluralize(bulkUploadResult.skipped.length, "row", "rows")} skipped.</>
              )}
            </p>
            {bulkUploadResult.skipped.length > 0 && (
              <div className="table-scroll">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Row</th>
                      <th>Name</th>
                      <th>Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bulkUploadResult.skipped.map((skip) => (
                      <tr key={skip.row}>
                        <td>{skip.row}</td>
                        <td>{skip.name || "—"}</td>
                        <td>{skip.reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </section>
    </AdminLayout>
  );
}
