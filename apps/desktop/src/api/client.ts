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
  query?: string;
  mode: string;
  count: number;
  results: QueryResult[];
  reason?: string;
  message?: string;
  workspace_id?: string;
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
  commits_indexed?: number;
  commits_total?: number;
  files_indexed?: number;
  symbols_indexed?: number;
  edges_indexed?: number;
  depth?: number;
  finished_at?: string;
  message?: string;
  progress?: number;
  phase?: string;
  cancellable?: boolean;
};

export type IndexStatus = {
  workspace_id: string;
  status: string;
  phase?: string;
  progress?: number;
  message?: string;
  commits_indexed?: number;
  commits_total?: number;
  files_indexed?: number;
  symbols_indexed?: number;
  edges_indexed?: number;
  cancellable?: boolean;
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

export type SymbolNode = {
  id: string;
  kind: "Symbol";
  path: string;
  name: string;
  symbol_kind: string;
  language: string;
  start_line: number;
  end_line: number;
};

export type EdgeNode = {
  id: string;
  kind: "Edge";
  edge_kind: string;
  source_id: string;
  target_id: string;
  source_name: string;
  target_name: string;
  source_path: string;
  target_path: string;
  commit_hash?: string;
};

export async function startIndex(workspaceId: string) {
  const data = await request<{ status: IndexStatus; accepted: boolean }>(
    `/workspaces/${workspaceId}/index`,
    { method: "POST" },
  );
  return data.status;
}

export async function cancelIndex(workspaceId: string) {
  const data = await request<{ status: IndexStatus }>(
    `/workspaces/${workspaceId}/index/cancel`,
    { method: "POST" },
  );
  return data.status;
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

export async function listSymbols(workspaceId: string, limit = 100) {
  const data = await request<{ symbols: SymbolNode[]; count: number }>(
    `/workspaces/${workspaceId}/symbols?limit=${limit}`,
  );
  return data.symbols;
}

export async function listEdges(workspaceId: string, limit = 50) {
  const data = await request<{ edges: EdgeNode[]; count: number }>(
    `/workspaces/${workspaceId}/edges?limit=${limit}`,
  );
  return data.edges;
}

export async function waitForIndex(
  workspaceId: string,
  onTick?: (status: IndexStatus) => void,
  timeoutMs = 120_000,
) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    const status = await getIndexStatus(workspaceId);
    onTick?.(status);
    if (
      status.status === "complete" ||
      status.status === "failed" ||
      status.status === "cancelled"
    ) {
      return status;
    }
    await new Promise((r) => setTimeout(r, 250));
  }
  throw new Error("Index timed out");
}

export async function notifyFileChanged(workspaceId: string, path: string) {
  const data = await request<{ update: Record<string, unknown> }>(
    `/workspaces/${workspaceId}/hooks/file-changed`,
    {
      method: "POST",
      body: JSON.stringify({ path }),
    },
  );
  return data.update;
}

export function runQuery(query: string, workspaceId: string, limit = 8) {
  return request<QueryResponse>("/query", {
    method: "POST",
    body: JSON.stringify({ query, workspace_id: workspaceId, limit }),
  });
}

export type FocusResponse = QueryResponse & {
  path: string;
  symbol?: string | null;
  line?: number | null;
  seed_id?: string | null;
  reason?: string;
  message?: string;
};

export function focusContext(
  workspaceId: string,
  path: string,
  opts?: { symbol?: string; line?: number; limit?: number },
) {
  return request<FocusResponse>("/context/focus", {
    method: "POST",
    body: JSON.stringify({
      workspace_id: workspaceId,
      path,
      symbol: opts?.symbol,
      line: opts?.line,
      limit: opts?.limit ?? 10,
    }),
  });
}

export type EmbeddingStatus = {
  configured_model: string;
  model_id: string;
  offline: boolean;
  cache_dir: string;
  dimension: number;
  backend: string;
  notice: string;
};

export function getEmbeddingStatus() {
  return request<EmbeddingStatus>("/embeddings/status");
}
