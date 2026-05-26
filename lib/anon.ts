"use client";

// Anonymous practice key: stored in localStorage so anonymous users can
// resume sessions across page reloads. On sign-in we can claim these
// sessions by updating their user_id (handled server-side later).

const KEY = "amplify_anon_key";

export function getAnonKey(): string {
  if (typeof window === "undefined") return "";
  let v = localStorage.getItem(KEY);
  if (!v) {
    v = crypto.randomUUID();
    localStorage.setItem(KEY, v);
  }
  return v;
}
