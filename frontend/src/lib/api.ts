import { createClient } from "@/lib/supabase/client";

const PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Server components inside Docker reach the backend by its service name. */
export function apiBaseUrl(): string {
  return typeof window === "undefined" ? (process.env.API_URL ?? PUBLIC_API_URL) : PUBLIC_API_URL;
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export interface HealthResponse {
  status: string;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${apiBaseUrl()}/health`, { cache: "no-store" });
  if (!res.ok) throw new Error(`health check failed: ${res.status}`);
  return (await res.json()) as HealthResponse;
}

export function buildHeaders(token: string | null, extra?: HeadersInit): Headers {
  const headers = new Headers(extra);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  return headers;
}

async function accessToken(): Promise<string | null> {
  const client = createClient();
  if (!client) return null;
  const { data } = await client.auth.getSession();
  return data.session?.access_token ?? null;
}

async function errorMessage(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: unknown };
    if (typeof body.detail === "string") return body.detail;
  } catch {
    // fall through to the status text
  }
  return res.statusText || `Request failed (${res.status})`;
}

/** Call the backend as the signed-in user. Resolves to undefined for 204 responses. */
export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = await accessToken();
  const res = await fetch(`${apiBaseUrl()}${path}`, {
    ...init,
    headers: buildHeaders(token, init.headers),
    cache: "no-store",
  });
  if (!res.ok) throw new ApiError(res.status, await errorMessage(res));
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
