import { Link } from "react-router-dom";

export default function SiteHeader({ eyebrow, action }) {
  return (
    <header className="site-header">
      <div className="site-header__inner">
        <Link to="/" className="site-header__brand">
          BallotBox
        </Link>
        {eyebrow && <span className="site-header__eyebrow">{eyebrow}</span>}
        {action && <div className="site-header__action">{action}</div>}
      </div>
    </header>
  );
}
