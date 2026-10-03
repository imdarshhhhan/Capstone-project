/** "2026-11-01T00:00:00" -> "1 Nov 2026" (null-safe). */
export function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

/** Today's date as YYYY-MM-DD in the user's local timezone. */
export function todayLocalIso(): string {
  return new Date().toLocaleDateString("en-CA");
}   