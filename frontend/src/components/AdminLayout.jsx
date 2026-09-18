import { Link } from "react-router-dom";
import AdminNav from "./AdminNav.jsx";
import SiteHeader from "./SiteHeader.jsx";
import { LogOutIcon } from "./icons.jsx";
import { clearToken } from "../api/client.js";

function handleLogout() {
  clearToken();
  window.location.assign("/admin/login");
}

export default function AdminLayout({
  heading,
  headingExtra,
  backTo,
  backLabel,
  sidebar,
  children,
}) {
  return (
    <div className="site-shell admin-dashboard-shell">
      <SiteHeader
        eyebrow="Admin"
        action={
          <button type="button" className="secondary-button small-button" onClick={handleLogout}>
            <LogOutIcon />
            Log out
          </button>
        }
      />
      <AdminNav />
      <div className="admin-shell-body">
        {sidebar}
        <main className="site-main site-main--wide">
          {(heading || backTo) && (
            <div className="admin-header">
              {backTo && (
                <Link to={backTo} className="nav-link admin-header__back">
                  ← {backLabel ?? "Back"}
                </Link>
              )}
              {heading && (
                <div className="admin-header__row">
                  <h1>{heading}</h1>
                  {headingExtra}
                </div>
              )}
            </div>
          )}
          {children}
        </main>
      </div>
    </div>
  );
}
