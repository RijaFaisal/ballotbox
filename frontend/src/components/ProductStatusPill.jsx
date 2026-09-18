export default function ProductStatusPill({ isOpen, label }) {
  return (
    <span className={`status-pill ${isOpen ? "status-pill--open" : "status-pill--closed"}`}>
      <span className="status-pill__dot" aria-hidden="true" />
      {label ?? (isOpen ? "Open" : "Closed")}
    </span>
  );
}
