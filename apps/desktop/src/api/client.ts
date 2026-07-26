/** Mycelium Core HTTP client. Vite proxies `/api` → `127.0.0.1:8787`; Tauri talks direct. */

function coreBase(): string {
  const fromEnv = import.meta.env.VITE_CORE_URL as string | undefined;
  if (fromEnv) return fromEnv.replace(/\/$/, "");
  if (typeof window !== "undefined" && "__TAURI_INTERNALS__" in window) {
    return "http://127.0.0.1:8787";
  }
  return "/api";
}

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
  id?: string;
  title: string;
  kind:
    | "Function"
    | "Method"
    | "Class"
    | "Type"
    | "Const"
    | "Symbol"
    | "Commit"
    | "Note"
    | "File"
    | string;
  family?: "Symbol" | "Commit" | "File" | "Note" | string;
  snippet: string;
  path: string;
  start_line?: number | null;
  end_line?: number | null;
  meta?: { icon: string; text: string }[];
  score: number;
  provenance?: Record<string, unknown>;
  workspace_id?: string;
  workspace_name?: string;
  workspace_path?: string;
};

export type HealthResponse = {
  status: string;
  service: string;
  version?: string;
  config_version?: number;
  api_token_enabled?: boolean;
  privacy?: {
    allow_code_upload?: boolean;
    allow_remote_llm?: boolean;
  };
  embedding?: {
    backend?: string;
    model_id?: string;
    configured_model?: string;
  };
  watchers?: {
    available?: boolean;
    workspaces?: number;
  };
};

export type QueryResponse = {
  query?: string;
  mode: string;
  count: number;
  results: QueryResult[];
  reason?: string;
  message?: string;
  workspace_id?: string;
  workspace_ids?: string[];
  scope?: "workspace" | "all_workspaces" | string;
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
  const res = await fetch(`${coreBase()}${path}`, {
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
  embedding_notice?: string;
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

export function runQuery(query: string, workspaceId = "*", limit = 8) {
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

export type AppSettings = {
  vault_dir: string;
  data_dir: string;
  config_file: string;
  config_version?: number;
  history_depth: number;
  embedding_model: string;
  allow_code_upload: boolean;
  allow_remote_llm: boolean;
  impact_tracking_enabled?: boolean;
  api_token_enabled?: boolean;
  github_client_id?: string;
  github_oauth_configured?: boolean;
  server: { host: string; port: number };
  privacy: {
    local_first: boolean;
    cloud_account_required: boolean;
    summary: string;
  };
};

export type GitHubStatus = {
  connected: boolean;
  login?: string | null;
  auth_mode?: string | null;
  oauth_configured: boolean;
  client_id_set?: boolean;
  repos_clone_root?: string;
};

export type GitHubRepo = {
  id: number;
  full_name: string;
  name: string;
  private: boolean;
  clone_url: string;
  ssh_url?: string;
  html_url?: string;
  default_branch?: string;
  description?: string;
  updated_at?: string;
};

export async function getSettings() {
  const data = await request<{
    settings: AppSettings;
    embedding_runtime: EmbeddingStatus | Record<string, never>;
    github?: GitHubStatus;
  }>("/settings");
  return data;
}

export async function patchSettings(input: {
  vault_dir?: string;
  history_depth?: number;
  embedding_model?: string;
  allow_code_upload?: boolean;
  allow_remote_llm?: boolean;
  github_client_id?: string;
  impact_tracking_enabled?: boolean;
}) {
  return request<{
    settings: AppSettings;
    github?: GitHubStatus;
    restart_hint?: string | null;
  }>("/settings", {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function getGitHubStatus() {
  return request<GitHubStatus>("/integrations/github/status");
}

export function startGitHubDevice() {
  return request<{
    user_code: string;
    verification_uri: string;
    interval: number;
    expires_in: number;
  }>("/integrations/github/device/start", { method: "POST" });
}

export function pollGitHubDevice() {
  return request<{
    status: string;
    connected?: boolean;
    login?: string;
    auth_mode?: string;
    interval?: number;
  }>("/integrations/github/device/poll", { method: "POST" });
}

export function saveGitHubPat(token: string) {
  return request<{ connected: boolean; login?: string; auth_mode?: string }>(
    "/integrations/github/token",
    { method: "POST", body: JSON.stringify({ token }) },
  );
}

export function disconnectGitHub() {
  return request<{ connected: boolean }>("/integrations/github", {
    method: "DELETE",
  });
}

export async function listGitHubRepos(page = 1, perPage = 30) {
  const data = await request<{
    repos: GitHubRepo[];
    page: number;
    per_page: number;
  }>(`/integrations/github/repos?page=${page}&per_page=${perPage}`);
  return data;
}

export function importGitHubRepo(input: {
  clone_url: string;
  dest?: string;
  full_name?: string;
}) {
  return request<{
    workspace: Workspace;
    path: string;
    cloned: boolean;
    full_name?: string | null;
  }>("/integrations/github/import", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export type VaultNote = {
  id: string;
  kind: "Note";
  title: string;
  path: string;
  abs_path?: string;
  body: string;
  updated_at: string;
  bucket?: string;
  is_index?: boolean;
  wikilinks?: { target: string; alias?: string | null; raw: string }[];
  unresolved_links?: { target: string; raw: string; reason: string }[];
  outgoing_edges?: Record<string, unknown>[];
};

export type VaultTreeNode =
  | {
      type: "folder";
      name: string;
      path: string;
      children: VaultTreeNode[];
    }
  | {
      type: "note";
      id: string;
      title: string;
      path: string;
      name: string;
      is_index?: boolean;
      updated_at?: string;
    };

export type VaultTree = {
  root: VaultTreeNode & { type: "folder" };
  notes: number;
  buckets: number;
};

export type VaultBacklink = {
  id: string;
  title: string;
  path: string;
  excerpt: string;
};

function noteApiId(id: string) {
  // Allow nested bucket paths: note:architecture/_index → architecture/_index
  // FastAPI uses {note_id:path}; leave slashes unencoded so the path converter matches.
  const stem = id.startsWith("note:") ? id.slice(5) : id;
  return stem
    .split("/")
    .map((part) => encodeURIComponent(part))
    .join("/");
}

export async function listVaultNotes() {
  const data = await request<{ notes: VaultNote[]; count: number }>("/vault/notes");
  return data.notes;
}

export async function getVaultTree() {
  return request<VaultTree>("/vault/tree");
}

export async function createVaultBucket(name: string) {
  const data = await request<{
    bucket: {
      bucket: string;
      path: string;
      created_index: boolean;
      index: { id: string; title: string; path: string } | null;
    };
  }>("/vault/buckets", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
  return data.bucket;
}

export async function packVault(input?: {
  bucket?: string;
  max_tokens?: number;
  include_bodies?: boolean;
}) {
  const data = await request<{
    pack: {
      text: string;
      tokens_est: number;
      max_tokens: number;
      bucket: string;
      truncated: boolean;
      included: Record<string, unknown>[];
    };
  }>("/vault/pack", {
    method: "POST",
    body: JSON.stringify(input ?? {}),
  });
  return data.pack;
}

export async function getVaultNote(id: string) {
  const data = await request<{ note: VaultNote }>(`/vault/notes/${noteApiId(id)}`);
  return data.note;
}

export async function createVaultNote(input: {
  title: string;
  body?: string;
  filename?: string;
  link_symbol?: string;
  bucket?: string;
}) {
  const data = await request<{ note: VaultNote }>("/vault/notes", {
    method: "POST",
    body: JSON.stringify(input),
  });
  return data.note;
}

export async function updateVaultNote(
  id: string,
  input: { title?: string; body?: string },
) {
  const data = await request<{ note: VaultNote }>(`/vault/notes/${noteApiId(id)}`, {
    method: "PUT",
    body: JSON.stringify(input),
  });
  return data.note;
}

export async function deleteVaultNote(id: string) {
  return request<{ deleted: boolean; id: string }>(`/vault/notes/${noteApiId(id)}`, {
    method: "DELETE",
  });
}

export async function getVaultBacklinks(id: string) {
  const data = await request<{
    note_id: string;
    title: string;
    count: number;
    backlinks: VaultBacklink[];
  }>(`/vault/notes/${noteApiId(id)}/backlinks`);
  return data.backlinks;
}

export async function reindexVault(workspaceId?: string) {
  const q = workspaceId ? `?workspace_id=${encodeURIComponent(workspaceId)}` : "";
  const data = await request<{ reindex: Record<string, unknown> }>(
    `/vault/reindex${q}`,
    { method: "POST" },
  );
  return data.reindex;
}

export type ImpactSummary = {
  range: "today" | "week" | "all";
  event_count: number;
  served_tokens: number;
  baseline_tokens: number;
  tokens_saved: number;
  savings_pct: number;
};

export type ImpactEvent = {
  ts: string;
  tool: string;
  workspace_id: string;
  served_tokens: number;
  baseline_tokens: number;
  tokens_saved: number;
};

export function getImpactSummary(range: "today" | "week" | "all" = "all") {
  return request<{ summary: ImpactSummary }>(
    `/impact/summary?range=${encodeURIComponent(range)}`,
  );
}

export function getImpactEvents(limit = 50) {
  return request<{ events: ImpactEvent[]; count: number }>(
    `/impact/events?limit=${limit}`,
  );
}

export function clearImpactEvents() {
  return request<{ cleared: boolean }>("/impact/events", { method: "DELETE" });
}
