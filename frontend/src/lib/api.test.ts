import { afterEach, describe, expect, it, vi } from "vitest";

const getSession = vi.fn();
vi.mock("@/lib/supabase/client", () => ({
  createClient: () => ({ auth: { getSession } }),
}));

import { ApiError, apiFetch, buildHeaders } from "./api";

afterEach(() => {
  vi.restoreAllMocks();
  getSession.mockReset();
});

describe("buildHeaders", () => {
  it("adds the bearer token and JSON content type", () => {
    const headers = buildHeaders("abc");
    expect(headers.get("Authorization")).toBe("Bearer abc");
    expect(headers.get("Content-Type")).toBe("application/json");
  });

  it("omits Authorization when signed out", () => {
    expect(buildHeaders(null).has("Authorization")).toBe(false);
  });
});

describe("apiFetch", () => {
  it("sends the session access token to the backend", async () => {
    getSession.mockResolvedValue({ data: { session: { access_token: "tok" } } });
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response(JSON.stringify([{ id: 1 }]), { status: 200 }));

    const data = await apiFetch<{ id: number }[]>("/fields");

    expect(data).toEqual([{ id: 1 }]);
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toMatch(/\/fields$/);
    expect(new Headers(init?.headers).get("Authorization")).toBe("Bearer tok");
  });

  it("returns undefined for 204 responses", async () => {
    getSession.mockResolvedValue({ data: { session: null } });
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(null, { status: 204 }));
    await expect(apiFetch("/me/skills/1", { method: "DELETE" })).resolves.toBeUndefined();
  });

  it("throws ApiError with the backend detail message", async () => {
    getSession.mockResolvedValue({ data: { session: null } });
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "Profile not found" }), { status: 404 }),
    );
    await expect(apiFetch("/me/profile")).rejects.toMatchObject({
      status: 404,
      message: "Profile not found",
    });
    await expect(apiFetch("/me/profile")).rejects.toBeInstanceOf(ApiError);
  });
});
