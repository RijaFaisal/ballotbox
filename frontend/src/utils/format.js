export function formatDateTime(isoString) {
  return new Date(isoString).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function pluralize(count, singular, plural) {
  return `${count} ${count === 1 ? singular : plural}`;
}

export function statusBadgeClass(drawStatus) {
  if (drawStatus === "completed") return "badge badge--success";
  if (drawStatus === "failed") return "badge badge--danger";
  return "badge badge--neutral";
}

// A product can be closed two ways: the manual is_open toggle, or a
// closes_at deadline that has passed while is_open is still true.
export function productStatusLabel(product) {
  if (product.effectively_open) return "Open";
  if (product.is_open && product.closes_at) return "Closed (schedule passed)";
  return "Closed";
}
