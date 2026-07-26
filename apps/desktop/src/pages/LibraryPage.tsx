import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ApiError,
  getGitHubStatus,
  importGitHubRepo,
  listGitHubRepos,
  listWorkspaces,
  registerWorkspace,
  type GitHubRepo,
  type GitHubStatus,
  type Workspace,
} from "../api/client";
import { isTauriShell, pickDirectory } from "../lib/fs";

function statusAccent(status: Workspace["status"]) {
  if (status === "healthy") return "bg-primary";
  if (status === "indexing") return "bg-secondary";
  return "bg-border group-hover:bg-outline";
}

function statusLabel(status: Workspace["status"]) {
  if (status === "healthy")
    return (
      <>
        <div className="w-1.5 h-1.5 rounded-full bg-primary" />
        <span className="font-label-caps text-label-caps text-muted uppercase">
          Healthy
        </span>
      </>
    );
  if (status === "indexing")
    return (
      <>
        <div className="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse" />
        <span className="font-label-caps text-label-caps text-secondary uppercase">
          Indexing
        </span>
      </>
    );
  return (
    <>
      <div className="w-1.5 h-1.5 rounded-full bg-muted" />
      <span className="font-label-caps text-label-caps text-muted uppercase">
        Idle
      </span>
    </>
  );
}

export function LibraryPage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const [pathDraft, setPathDraft] = useState("");
  const [registering, setRegistering] = useState(false);
  const [ghOpen, setGhOpen] = useState(false);
  const [ghStatus, setGhStatus] = useState<GitHubStatus | null>(null);
  const [ghRepos, setGhRepos] = useState<GitHubRepo[]>([]);
  const [ghLoading, setGhLoading] = useState(false);
  const [importing, setImporting] = useState<string | null>(null);
  const [hint, setHint] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const rows = await listWorkspaces();
      setWorkspaces(rows);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load workspaces");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
    void getGitHubStatus()
      .then(setGhStatus)
      .catch(() => setGhStatus(null));
  }, [refresh]);

  const visible = useMemo(() => {
    const q = filter.trim().toLowerCase();
    if (!q) return workspaces;
    return workspaces.filter(
      (ws) =>
        ws.name.toLowerCase().includes(q) || ws.path.toLowerCase().includes(q),
    );
  }, [workspaces, filter]);

  async function onRegister() {
    const path = pathDraft.trim();
    if (!path) return;
    setRegistering(true);
    setError(null);
    try {
      await registerWorkspace(path);
      setPathDraft("");
      setAdding(false);
      await refresh();
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(err instanceof Error ? err.message : "Register failed");
      }
    } finally {
      setRegistering(false);
    }
  }

  async function onAddWorkspaceClick() {
    if (isTauriShell()) {
      setError(null);
      const path = await pickDirectory("Choose a git repository folder");
      if (!path) return;
      setPathDraft(path);
      setRegistering(true);
      try {
        await registerWorkspace(path);
        setPathDraft("");
        setAdding(false);
        setHint(`Added workspace: ${path}`);
        await refresh();
      } catch (err: unknown) {
        setAdding(true);
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError(err instanceof Error ? err.message : "Register failed");
        }
      } finally {
        setRegistering(false);
      }
      return;
    }
    setAdding((v) => !v);
  }

  async function onBrowseFolder() {
    const path = await pickDirectory("Choose a git repository folder");
    if (path) setPathDraft(path);
  }

  async function openGitHubImport() {
    setGhOpen(true);
    setGhLoading(true);
    setError(null);
    try {
      const status = await getGitHubStatus();
      setGhStatus(status);
      if (!status.connected) {
        setError("Connect GitHub in Settings first (PAT or device OAuth).");
        setGhRepos([]);
        return;
      }
      const data = await listGitHubRepos(1, 40);
      setGhRepos(data.repos);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to list GitHub repos");
    } finally {
      setGhLoading(false);
    }
  }

  async function onImport(repo: GitHubRepo) {
    setImporting(repo.full_name);
    setError(null);
    try {
      await importGitHubRepo({
        clone_url: repo.clone_url,
        full_name: repo.full_name,
      });
      await refresh();
      setMessageQuiet(`${repo.full_name} imported — Index it next`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Import failed");
    } finally {
      setImporting(null);
    }
  }

  function setMessageQuiet(msg: string) {
    setHint(msg);
  }

  return (
    <main className="w-full h-full overflow-y-auto bg-surface-dim p-xl">
      <div className="max-w-5xl mx-auto flex flex-col gap-xl">
        <div className="flex items-end justify-between border-b border-border pb-md gap-md flex-wrap">
          <h2 className="font-headline-lg text-headline-lg font-medium text-on-surface">
            Library
          </h2>
          <div className="flex gap-sm">
            <button
              type="button"
              onClick={() => void openGitHubImport()}
              className="flex items-center gap-xs px-md py-sm bg-primary text-on-primary rounded-xl hover:brightness-110 transition-colors duration-150 font-body-sm text-body-sm"
            >
              <span className="material-symbols-outlined text-[16px]">cloud_download</span>
              Import from GitHub
            </button>
            <button
              type="button"
              onClick={() => void onAddWorkspaceClick()}
              disabled={registering}
              className="flex items-center gap-xs px-md py-sm bg-surface-container-low border border-border rounded-lg text-on-surface hover:bg-surface-container-high transition-colors duration-150 font-body-sm text-body-sm disabled:opacity-50"
            >
              <span className="material-symbols-outlined text-[16px]">add_box</span>
              {registering ? "Adding…" : "Add workspace"}
            </button>
          </div>
        </div>

        {hint && (
          <p className="font-body-sm text-body-sm text-primary">{hint}</p>
        )}

        {ghOpen && (
          <div className="flex flex-col gap-sm p-md bg-surface-container-lowest border border-border rounded-lg max-h-[360px]">
            <div className="flex items-center justify-between">
              <h3 className="font-label-md text-label-md text-on-surface">
                GitHub repos
                {ghStatus?.login ? ` · @${ghStatus.login}` : ""}
              </h3>
              <button
                type="button"
                className="text-muted font-body-sm text-body-sm"
                onClick={() => setGhOpen(false)}
              >
                Close
              </button>
            </div>
            {ghLoading && (
              <p className="font-technical-mono text-technical-mono text-muted">
                Loading…
              </p>
            )}
            <div className="overflow-y-auto flex flex-col gap-xs">
              {ghRepos.map((repo) => (
                <div
                  key={repo.id}
                  className="flex items-center justify-between gap-md py-sm px-sm rounded-lg hover:bg-surface-container-low"
                >
                  <div className="min-w-0">
                    <p className="font-body-md text-body-md text-on-surface truncate">
                      {repo.full_name}
                      {repo.private ? (
                        <span className="ml-sm text-muted font-technical-mono-sm text-technical-mono-sm">
                          private
                        </span>
                      ) : null}
                    </p>
                    <p className="font-technical-mono-sm text-technical-mono-sm text-muted truncate">
                      {repo.description || repo.clone_url}
                    </p>
                  </div>
                  <button
                    type="button"
                    disabled={importing === repo.full_name}
                    onClick={() => void onImport(repo)}
                    className="shrink-0 px-md h-9 rounded-lg bg-primary text-on-primary font-label-md text-label-md disabled:opacity-50"
                  >
                    {importing === repo.full_name ? "Importing…" : "Import"}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {adding && (
          <div className="flex flex-col gap-sm p-md bg-surface-container-lowest border border-border rounded-lg">
            <label className="font-body-sm text-body-sm text-muted">
              Local git repository
            </label>
            <div className="flex gap-sm flex-wrap">
              <button
                type="button"
                onClick={() => void onBrowseFolder()}
                className="flex items-center gap-xs px-md py-sm bg-surface-container border border-border rounded-lg text-on-surface hover:bg-surface-container-high font-body-sm text-body-sm"
              >
                <span className="material-symbols-outlined text-[16px]">folder_open</span>
                Choose folder…
              </button>
              <input
                className="flex-1 min-w-[200px] bg-surface-container border border-border rounded-lg px-md py-sm text-on-surface font-technical-mono text-technical-mono focus:outline-none focus:border-primary placeholder:text-muted"
                placeholder="Selected path appears here"
                value={pathDraft}
                onChange={(e) => setPathDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") void onRegister();
                }}
                readOnly={isTauriShell()}
              />
              <button
                type="button"
                disabled={registering || !pathDraft.trim()}
                onClick={() => void onRegister()}
                className="px-md py-sm bg-primary text-on-primary rounded-xl font-body-sm text-body-sm disabled:opacity-50 transition-colors duration-150"
              >
                {registering ? "Adding…" : "Register"}
              </button>
            </div>
            {!isTauriShell() && (
              <p className="font-technical-mono-sm text-technical-mono-sm text-muted">
                Folder picker is available in the desktop app. In the browser, paste an absolute path.
              </p>
            )}
          </div>
        )}

        <div className="relative group">
          <span className="absolute left-md top-1/2 -translate-y-1/2 material-symbols-outlined text-muted text-[18px]">
            search
          </span>
          <input
            className="w-full bg-surface-container border border-border rounded-lg pl-10 pr-md py-md text-on-surface font-body-md text-body-md focus:outline-none focus:border-primary transition-colors duration-150 placeholder:text-muted"
            placeholder="Search your graph..."
            type="text"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
        </div>

        {loading && (
          <p className="font-technical-mono text-technical-mono text-muted">
            Loading workspaces from Core…
          </p>
        )}
        {error && (
          <p className="font-body-sm text-body-sm text-danger">{error}</p>
        )}
        {!loading && !error && workspaces.length === 0 && (
          <p className="font-body-sm text-body-sm text-muted">
            No workspaces yet. Add a local path or Import from GitHub.
          </p>
        )}

        <div className="flex flex-col gap-sm">
          {visible.map((ws) => (
            <div
              key={ws.id ?? ws.path}
              className={`group flex items-center gap-md p-md bg-surface-container-lowest border border-border rounded-lg hover:bg-surface-container-low transition-colors duration-150 cursor-pointer relative overflow-hidden ${
                ws.status === "idle" ? "opacity-70 hover:opacity-100" : ""
              }`}
            >
              <div
                className={`absolute left-0 top-0 bottom-0 w-[2px] ${statusAccent(ws.status)} transition-colors`}
              />
              <div className="flex-1 min-w-0 flex flex-col gap-xs pl-sm">
                <div className="flex items-center justify-between">
                  <h3 className="font-headline-md text-headline-md text-on-surface truncate">
                    {ws.name}
                  </h3>
                  <div className="flex items-center gap-xs">
                    {statusLabel(ws.status)}
                  </div>
                </div>
                <div className="font-technical-mono text-technical-mono text-muted truncate">
                  {ws.path}
                </div>
              </div>
              <div className="flex items-center gap-md ml-xl border-l border-border pl-lg">
                <div className="flex flex-col gap-xs text-right min-w-[72px]">
                  <span className="font-body-sm text-body-sm text-on-surface">
                    {ws.symbols}
                  </span>
                  <span className="font-technical-mono-sm text-technical-mono-sm text-muted">
                    symbols
                  </span>
                </div>
                <div className="flex flex-col gap-xs text-right min-w-[72px]">
                  <span className="font-body-sm text-body-sm text-on-surface">
                    {ws.commits}
                  </span>
                  <span className="font-technical-mono-sm text-technical-mono-sm text-muted">
                    commits
                  </span>
                </div>
                <div className="flex flex-col gap-xs text-right min-w-[72px]">
                  <span className="font-body-sm text-body-sm text-on-surface">
                    {ws.notes}
                  </span>
                  <span className="font-technical-mono-sm text-technical-mono-sm text-muted">
                    notes
                  </span>
                </div>
              </div>
              <div className="ml-lg min-w-[100px] text-right font-technical-mono-sm text-technical-mono-sm text-muted">
                idx: {ws.indexed_ago}
              </div>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
