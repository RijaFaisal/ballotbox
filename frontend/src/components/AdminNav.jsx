import { NavLink } from "react-router-dom";

export default function AdminNav() {
  function linkClass({ isActive }) {
    return isActive ? "admin-nav__link admin-nav__link--active" : "admin-nav__link";
  }

  return (
    <nav className="admin-nav">
      <div className="admin-nav__inner">
        <NavLink to="/admin" end className={linkClass}>
          Dashboard
        </NavLink>
        <NavLink to="/admin/products" className={linkClass}>
          Products
        </NavLink>
        <NavLink to="/admin/controls" className={linkClass}>
          Admin controls
        </NavLink>
      </div>
    </nav>
  );
}
