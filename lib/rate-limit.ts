// In-memory per-key rate limiter. Resets on lambda cold-start, which is fine
// for a demo-day defense layer. Tightens the cost on the most expensive paths
// (embeddings, DPP, role mutations) so a hostile devtools user in the audience
// can't grief the bank during the pitch.

type Bucket = { count: number; windowStart: number };
const buckets = new Map<string, Bucket>();

export type RateLimitResult = {
  allowed: boolean;
  remaining: number;
  retryAfterMs: number;
};

export function rateLimit(
  key: string,
  max: number,
  windowMs: number
): RateLimitResult {
  const now = Date.now();
  const cur = buckets.get(key);
  if (!cur || now - cur.windowStart >= windowMs) {
    buckets.set(key, { count: 1, windowStart: now });
    return { allowed: true, remaining: max - 1, retryAfterMs: 0 };
  }
  if (cur.count >= max) {
    return {
      allowed: false,
      remaining: 0,
      retryAfterMs: windowMs - (now - cur.windowStart),
    };
  }
  cur.count++;
  return {
    allowed: true,
    remaining: max - cur.count,
    retryAfterMs: 0,
  };
}

export function clientKey(req: Request, userId: string | null): string {
  // Prefer authenticated user id; fall back to forwarded IP for anon endpoints.
  if (userId) return `u:${userId}`;
  const fwd = req.headers.get("x-forwarded-for");
  const ip = fwd ? fwd.split(",")[0].trim() : "anon";
  return `ip:${ip}`;
}
