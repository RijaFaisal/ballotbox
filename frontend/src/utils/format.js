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
