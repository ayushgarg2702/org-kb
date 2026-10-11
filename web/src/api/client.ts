const ORG = import.meta.env.VITE_ORG_ID || "example-org";

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-Org-Id": ORG,
      "X-User-Id": "web-user",
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) {
    throw new Error(`${res.status} ${await res.text()}`);
  }
  return res.json() as Promise<T>;
}

export type GraphPayload = {
  nodes: Array<{ id: string; label: string; type: string; origin?: string; confidence?: string }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
    label: string;
    origin?: string;
    confidence_class?: string;
  }>;
  partial?: boolean;
  coverage?: Record<string, unknown>;
};

export const fetchOverview = () => api<GraphPayload>("/api/v1/graph/overview");
export const fetchNeighbors = (id: string) => api<GraphPayload>(`/api/v1/graph/nodes/${id}/neighbors`);
export const fetchNode = (id: string) => api<Record<string, unknown>>(`/api/v1/graph/nodes/${id}`);
export const fetchEvidence = (id: string) =>
  api<{ evidence: Array<Record<string, unknown>> }>(`/api/v1/entities/${id}/evidence`);
export const search = (q: string) =>
  api<{ results: Array<{ id: string; name: string; type: string }> }>(`/api/v1/search?q=${encodeURIComponent(q)}`);
export const ask = (question: string) =>
  api<Record<string, unknown>>("/api/v1/query", {
    method: "POST",
    body: JSON.stringify({ question }),
  });
