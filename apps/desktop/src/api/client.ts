/** Mycelium Core HTTP client. Proxied via Vite `/api` → `127.0.0.1:8787`. */

const BASE = import.meta.env.VITE_CORE_URL ?? "/api";

export type WorkspaceStatus = "healthy" | "indexing" | "idle";

export type Workspace = {
  id?: string;
  name: string;
  path: string;
  status: WorkspaceStatus;
  symbols: number;
  commits: number;
  notes: number;
  indexed_ago: string;
  registered_at?: string;
};

export type QueryResult = {
  title: string;
  kind: "Symbol" | "Commit" | "Note" | "File";
  snippet: string;
  path: string;
  meta?: { icon: string; text: string }[];
  score: number;
};

export type HealthResponse = {
  status: string;
  service: string;
  version?: string;
};

export type QueryResponse = {
  query: string;
  mode: string;
  count: number;
  results: QueryResult[];
};

export class ApiError extends Error {
  status: number;
  code?: string;

  constructor(status: number, message: string, code?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });
  if (!res.ok) {
    let message = `${res.status} ${res.statusText} for ${path}`;
    let code: string | undefined;
    try {
      const body = (await res.json()) as {
        detail?: { code?: string; message?: string } | string;
      };
      if (typeof body.detail === "string") {
        message = body.detail;
      } else if (body.detail && typeof body.detail === "object") {
        code = body.detail.code;
        message = body.detail.message ?? message;
      }
    } catch {
      // keep default message
    }
    throw new ApiError(res.status, message, code);
  }
  return res.json() as Promise<T>;
}

export function getHealth() {
  return request<HealthResponse>("/health");
}

export async function listWorkspaces() {
  const data = await request<{ workspaces: Workspace[] }>("/workspaces");
  return data.workspaces;
}

export async function registerWorkspace(path: string) {
  const data = await request<{ workspace: Workspace }>("/workspaces", {
    method: "POST",
    body: JSON.stringify({ path }),
  });
  return data.workspace;
}

export type IndexResult = {
  workspace_id: string;
  status: string;
  commits_indexed: number;
  commits_total: number;
  depth: number;
  finished_at: string;
  message: string;
};

export type IndexStatus = {
  workspace_id: string;
  status: string;
  phase?: string;
  progress?: number;
  message?: string;
  commits_indexed?: number;
  commits_total?: number;
  error?: { code: string; message: string };
};

export type CommitNode = {
  id: string;
  kind: "Commit";
  hash: string;
  author: string;
  timestamp: string;
  message: string;
  changed_paths: string[];
};

export async function startIndex(workspaceId: string) {
  const data = await request<{ index: IndexResult }>(
    `/workspaces/${workspaceId}/index`,
    { method: "POST" },
  );
  return data.index;
}

export async function getIndexStatus(workspaceId: string) {
  const data = await request<{ status: IndexStatus }>(
    `/workspaces/${workspaceId}/index/status`,
  );
  return data.status;
}

export async function listCommits(workspaceId: string, limit = 50) {
  const data = await request<{ commits: CommitNode[]; count: number }>(
    `/workspaces/${workspaceId}/commits?limit=${limit}`,
  );
  return data.commits;
}

export function runQuery(query: string, limit = 8) {
  return request<QueryResponse>("/query", {
    method: "POST",
    body: JSON.stringify({ query, limit }),
  });
}
