import type { Catalog, PipelineOut } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `API ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  catalog: () => request<Catalog>("/catalog"),
  sample: () => request<Record<string, unknown>>("/sample"),
  pipeline: (body: Record<string, unknown>) =>
    request<PipelineOut>("/pipeline", { method: "POST", body: JSON.stringify(body) }),
};
