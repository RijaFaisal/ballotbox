import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { UnauthorizedError, listProducts } from "../api/client.js";

export default function ProductsSidebar() {
  const [products, setProducts] = useState(null);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    listProducts()
      .then(setProducts)
      .catch((err) => {
        if (err instanceof UnauthorizedError) return;
        setError(err.message);
      });
  }, []);

  function linkClass({ isActive }) {
    return isActive
      ? "products-sidebar__link products-sidebar__link--active"
      : "products-sidebar__link";
  }

  function newProductLinkClass({ isActive }) {
    return isActive
      ? "products-sidebar__link products-sidebar__link--active"
      : "products-sidebar__link products-sidebar__link--accent";
  }

  const term = search.trim().toLowerCase();
  const filtered = products ? products.filter((p) => p.name.toLowerCase().includes(term)) : [];

  return (
    <nav className="products-sidebar" aria-label="Products">
      <ul className="products-sidebar__list">
        <li>
          <NavLink to="/admin/products" end className={linkClass}>
            All products
          </NavLink>
        </li>
        <li>
          <NavLink to="/admin/products/new" className={newProductLinkClass}>
            + New product
          </NavLink>
        </li>
      </ul>

      {error && <p className="error-text">{error}</p>}

      {products && products.length > 5 && (
        <div className="products-sidebar__search">
          <input
            aria-label="Filter products"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Filter products…"
          />
        </div>
      )}

      {products && (
        <ul className="products-sidebar__list">
          {filtered.length === 0 ? (
            <li className="products-sidebar__empty">No products match.</li>
          ) : (
            filtered.map((product) => (
              <li key={product.id}>
                <NavLink to={`/admin/products/${product.id}`} className={linkClass}>
                  {product.name}
                </NavLink>
              </li>
            ))
          )}
        </ul>
      )}
    </nav>
  );
}
