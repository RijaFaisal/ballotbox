import { useEffect, useState } from "react";
import AdminLayout from "../components/AdminLayout.jsx";
import { UnauthorizedError, getDashboardSummary } from "../api/client.js";

export default function AdminDashboard() {
  const [summary, setSummary] = useState(null);
  const [loadError, setLoadError] = useState("");

  useEffect(() => {
    getDashboardSummary()
      .then(setSummary)
      .catch((err) => {
        if (err instanceof UnauthorizedError) return;
        setLoadError(err.message);
      });
  }, []);

  const isLoading = summary === null;

  return (
    <AdminLayout>
      {loadError && <p className="error-text">{loadError}</p>}

      {isLoading && !loadError && (
        <p className="loading-text">
          <span className="spinner" aria-hidden="true" />
          Loading dashboard…
        </p>
      )}

      {!isLoading && (
        <section className="section">
          <div className="stats-row">
            <div className="stat-tile">
              <span className="eyebrow">Open to entries</span>
              <p className="stat-tile__value">{summary.open_product_count}</p>
            </div>
            <div className="stat-tile">
              <span className="eyebrow">Total candidates</span>
              <p className="stat-tile__value">{summary.candidate_count}</p>
            </div>
          </div>
        </section>
      )}
    </AdminLayout>
  );
}
