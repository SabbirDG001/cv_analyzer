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
    public readonly code: string | null = null,
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

export function buildHeaders(
  token: string | null,
  extra?: HeadersInit,
  json: boolean = true,
): Headers {
  const headers = new Headers(extra);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  // Multipart bodies need the browser to set the Content-Type (with its boundary).
  if (json && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  return headers;
}

async function accessToken(): Promise<string | null> {
  const client = createClient();
  if (!client) return null;
  const { data } = await client.auth.getSession();
  return data.session?.access_token ?? null;
}

interface ErrorInfo {
  message: string;
  code: string | null;
}

function isCodedDetail(detail: unknown): detail is { code: string; message: string } {
  if (typeof detail !== "object" || detail === null) return false;
  const d = detail as Record<string, unknown>;
  return typeof d.code === "string" && typeof d.message === "string";
}

async function errorInfo(res: Response): Promise<ErrorInfo> {
  try {
    const body = (await res.json()) as { detail?: unknown };
    if (typeof body.detail === "string") return { message: body.detail, code: null };
    if (isCodedDetail(body.detail)) return { message: body.detail.message, code: body.detail.code };
  } catch {
    // fall through to the status text
  }
  return { message: res.statusText || `Request failed (${res.status})`, code: null };
}

/** Call the backend as the signed-in user. Resolves to undefined for 204 responses. */
export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = await accessToken();
  const res = await fetch(`${apiBaseUrl()}${path}`, {
    ...init,
    headers: buildHeaders(token, init.headers, !(init.body instanceof FormData)),
    cache: "no-store",
  });
  if (!res.ok) {
    const info = await errorInfo(res);
    throw new ApiError(res.status, info.message, info.code);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
