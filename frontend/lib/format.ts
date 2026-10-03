export function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}


export function todayLocalIso(): string {
  return new Date().toLocaleDateString("en-CA");
}   