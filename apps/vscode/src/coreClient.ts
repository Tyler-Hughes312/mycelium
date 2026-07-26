/** HTTP client for Mycelium Core (localhost). */

export type HealthResponse = {
  status: string;
  version?: string;
};

export type Workspace = {
  id: string;
  name: string;
  path: string;
  status?: string;
};

export type FocusResult = {
  id?: string;
  title: string;
  kind: string;
  family?: string;
  snippet: string;
  path: string;
  score?: number;
  meta?: { icon: string; text: string }[];
  provenance?: Record<string, unknown>;
};

export type FocusPacket = {
  workspace_id: string;
  path: string;
  symbol?: string | null;
  line?: number | null;
  mode: string;
  seed_id?: string | null;
  seed_kind?: string | null;
  count: number;
  results: FocusResult[];
  reason?: string;
  message?: string;
};

export type VaultNote = {
  id: string;
  title: string;
  path: string;
  abs_path?: string;
  body: string;
};

export class CoreClient {
  constructor(private baseUrl: string) {}

  setBaseUrl(url: string) {
    this.baseUrl = url.replace(/\/$/, "");
  }

  getBaseUrl() {
    return this.baseUrl;
  }

  async health(): Promise<HealthResponse> {
    return this.get<HealthResponse>("/health");
  }

  async listWorkspaces(): Promise<Workspace[]> {
    const data = await this.get<{ workspaces: Workspace[] }>("/workspaces");
    return data.workspaces ?? [];
  }

  async focus(input: {
    workspace_id: string;
    path: string;
    symbol?: string;
    line?: number;
    limit?: number;
  }): Promise<FocusPacket> {
    return this.post<FocusPacket>("/context/focus", input);
  }

  async createNote(input: {
    title: string;
    body?: string;
    link_symbol?: string;
  }): Promise<VaultNote> {
    const data = await this.post<{ note: VaultNote }>("/vault/notes", input);
    return data.note;
  }

  async getNote(id: string): Promise<VaultNote> {
    const stem = id.startsWith("note:") ? id.slice(5) : id;
    const data = await this.get<{ note: VaultNote }>(
      `/vault/notes/${encodeURIComponent(stem)}`,
    );
    return data.note;
  }

  private async get<T>(path: string): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      headers: { Accept: "application/json" },
    });
    if (!res.ok) {
      throw new Error(`${res.status} ${res.statusText} for ${path}`);
    }
    return (await res.json()) as T;
  }

  private async post<T>(path: string, body: unknown): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      let detail = `${res.status} ${res.statusText}`;
      try {
        const err = (await res.json()) as {
          detail?: { message?: string } | string;
        };
        if (typeof err.detail === "string") detail = err.detail;
        else if (err.detail?.message) detail = err.detail.message;
      } catch {
        // keep default
      }
      throw new Error(`${detail} for ${path}`);
    }
    return (await res.json()) as T;
  }
}
