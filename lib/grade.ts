// Loose numerical/string answer comparison. Factored out for testability.

export function looselyEqual(a: string, b: string): boolean {
  const norm = (s: string) =>
    s
      .trim()
      .toLowerCase()
      .replace(/\s+/g, "")
      .replace(/^\\boxed\{|\}$/g, "");
  const na = norm(a);
  const nb = norm(b);
  if (na === nb) return true;

  const fa = Number.parseFloat(na);
  const fb = Number.parseFloat(nb);
  if (Number.isFinite(fa) && Number.isFinite(fb)) {
    if (fa === fb) return true;
    const diff = Math.abs(fa - fb);
    const scale = Math.max(1, Math.abs(fa), Math.abs(fb));
    return diff / scale < 1e-3;
  }
  return false;
}
