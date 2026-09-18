import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import AdminLayout from "../components/AdminLayout.jsx";
import ProductsSidebar from "../components/ProductsSidebar.jsx";
import { LockIcon, PlusIcon, TrashIcon, UnlockIcon } from "../components/icons.jsx";
import {
  UnauthorizedError,
  deleteProduct,
  listProducts,
  setProductOpen,
} from "../api/client.js";
import { formatDateTime } from "../utils/format.js";

export default function AdminProducts() {
  const [products, setProducts] = useState(null);
  const [loadError, setLoadError] = useState("");

  const [productOpenState, setProductOpenState] = useState({});
  const [deleteProductState, setDeleteProductState] = useState({});

  useEffect(() => {
    listProducts()
      .then(setProducts)
      .catch((err) => {
        if (err instanceof UnauthorizedError) return;
        setLoadError(err.message);
      });
  }, []);

  function handleToggleProductOpen(product) {
    setProductOpenState((prev) => ({ ...prev, [product.id]: { status: "submitting" } }));

    setProductOpen(product.id, !product.is_open)
      .then((updated) => {
        setProducts((prev) => (prev ?? []).map((p) => (p.id === updated.id ? updated : p)));
        setProductOpenState((prev) => ({ ...prev, [product.id]: { status: "idle" } }));
      })
      .catch((err) => {
        if (err instanceof UnauthorizedError) return;
        setProductOpenState((prev) => ({
          ...prev,
          [product.id]: { status: "idle", error: err.message },
        }));
      });
  }

  function handleDeleteProduct(product) {
    if (
      !window.confirm(
        `Delete "${product.name}" and all of its candidates and draws? This cannot be undone.`
      )
    ) {
      return;
    }

    setDeleteProductState((prev) => ({ ...prev, [product.id]: { status: "submitting" } }));

    deleteProduct(product.id)
      .then(() => {
        setProducts((prev) => (prev ?? []).filter((p) => p.id !== product.id));
        setDeleteProductState((prev) => {
          const next = { ...prev };
          delete next[product.id];
          return next;
        });
      })
      .catch((err) => {
        if (err instanceof UnauthorizedError) return;
        setDeleteProductState((prev) => ({
          ...prev,
          [product.id]: { status: "idle", error: err.message },
        }));
      });
  }

  const isLoading = products === null;

  return (
    <AdminLayout sidebar={<ProductsSidebar />}>
      {loadError && <p className="error-text">{loadError}</p>}

      {isLoading && !loadError && (
        <p className="loading-text">
          <span className="spinner" aria-hidden="true" />
          Loading products…
        </p>
      )}

      {!isLoading && (
        <section className="section tinted-section">
          <div className="section-header-row">
            <h2>
              All products <span className="mono">({products.length})</span>
            </h2>
            <Link to="/admin/products/new" className="button-like primary-button small-button">
              <PlusIcon />
              New product
            </Link>
          </div>
          {products.length === 0 ? (
            <p className="empty-state">No products yet. Create one above.</p>
          ) : (
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {products.map((product) => {
                    const deleteState = deleteProductState[product.id] ?? { status: "idle" };
                    const openState = productOpenState[product.id] ?? { status: "idle" };

                    return (
                      <tr key={product.id}>
                        <td>{product.name}</td>
                        <td>
                          <span
                            className={
                              product.is_open ? "badge badge--success" : "badge badge--danger"
                            }
                          >
                            {product.is_open ? "Open" : "Closed"}
                          </span>
                        </td>
                        <td>{formatDateTime(product.created_at)}</td>
                        <td>
                          <div className="table-actions">
                            <Link
                              to={`/admin/products/${product.id}`}
                              className="button-like secondary-button small-button"
                            >
                              Manage
                            </Link>
                            <button
                              type="button"
                              className={
                                product.is_open
                                  ? "warning-button small-button"
                                  : "secondary-button small-button"
                              }
                              onClick={() => handleToggleProductOpen(product)}
                              disabled={openState.status === "submitting"}
                            >
                              {product.is_open ? <LockIcon /> : <UnlockIcon />}
                              {openState.status === "submitting"
                                ? "Updating…"
                                : product.is_open
                                  ? "Close"
                                  : "Open"}
                            </button>
                            <button
                              type="button"
                              className="danger-button small-button"
                              onClick={() => handleDeleteProduct(product)}
                              disabled={deleteState.status === "submitting"}
                            >
                              <TrashIcon />
                              {deleteState.status === "submitting" ? "Deleting…" : "Delete"}
                            </button>
                          </div>
                          {deleteState.error && <p className="error-text">{deleteState.error}</p>}
                          {openState.error && <p className="error-text">{openState.error}</p>}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
    </AdminLayout>
  );
}
