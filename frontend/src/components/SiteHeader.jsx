import { Link, useLocation } from "react-router-dom";
import { getToken } from "../api/client.js";
import { ArrowLeftIcon, SettingsIcon } from "./icons.jsx";

export default function SiteHeader({ eyebrow, action }) {
  const { pathname } = useLocation();
  const inAdmin = pathname.startsWith("/admin");
  const isLoggedIn = Boolean(getToken());

  return (
    <header className="site-header">
      <div className="site-header__inner">
        <Link to="/" className="site-header__brand">
          BallotBox
        </Link>
        {eyebrow && <span className="site-header__eyebrow">{eyebrow}</span>}
        {action && <div className="site-header__action">{action}</div>}
      </div>
      {inAdmin
        ? !isLoggedIn && (
            <Link to="/" className="admin-access-button" title="Back to site">
              <ArrowLeftIcon /> Back to site
            </Link>
          )
        : (
            <Link to="/admin" className="admin-access-button" title="Admin">
              <SettingsIcon /> Admin
            </Link>
          )}
    </header>
  );
}
