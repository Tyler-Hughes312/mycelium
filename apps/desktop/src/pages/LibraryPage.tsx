import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ApiError,
  listWorkspaces,
  registerWorkspace,
  type Workspace,
} from "../api/client";

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

  return (
    <main className="w-full h-full overflow-y-auto bg-surface-dim p-xl">
      <div className="max-w-5xl mx-auto flex flex-col gap-xl">
        <div className="flex items-end justify-between border-b border-border pb-md">
          <h2 className="font-headline-lg text-headline-lg font-medium text-on-surface">
            Library
          </h2>
          <button
            type="button"
            onClick={() => setAdding((v) => !v)}
            className="flex items-center gap-xs px-md py-sm bg-surface-container-low border border-border rounded-lg text-on-surface hover:bg-surface-container-high transition-colors duration-150 font-body-sm text-body-sm"
          >
            <span className="material-symbols-outlined text-[16px]">
              add_box
            </span>
            Add workspace
          </button>
        </div>

        {adding && (
          <div className="flex flex-col gap-sm p-md bg-surface-container-lowest border border-border rounded-lg">
            <label className="font-body-sm text-body-sm text-muted">
              Local git repository path
            </label>
            <div className="flex gap-sm">
              <input
                className="flex-1 bg-surface-container border border-border rounded-lg px-md py-sm text-on-surface font-technical-mono text-technical-mono focus:outline-none focus:border-primary placeholder:text-muted"
                placeholder="/Users/you/project or ~/dev/my-repo"
                value={pathDraft}
                onChange={(e) => setPathDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") void onRegister();
                }}
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
          </div>
        )}

        <div className="relative group">
          <span className="absolute left-md top-1/2 -translate-y-1/2 material-symbols-outlined text-muted text-[18px]">
            search
          </span>
          <input
            className="w-full bg-surface-container border border-border rounded-lg pl-xl pr-md py-md text-on-surface font-body-md text-body-md focus:outline-none focus:border-primary transition-colors duration-150 placeholder:text-muted"
            placeholder="Search your graph..."
            type="text"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
          <div className="absolute right-md top-1/2 -translate-y-1/2 flex items-center gap-xs px-xs py-[2px] bg-surface-container-high border border-border rounded-lg text-muted font-technical-mono-sm text-technical-mono-sm">
            <span>⌘K</span>
          </div>
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
            No workspaces yet. Add a local git repo path to get started.
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
