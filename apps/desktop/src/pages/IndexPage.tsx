import { type ReactNode, useCallback, useEffect, useState } from "react";
import {
  ApiError,
  getIndexStatus,
  listCommits,
  listWorkspaces,
  registerWorkspace,
  startIndex,
  type CommitNode,
  type IndexStatus,
  type Workspace,
} from "../api/client";

function formatTime(iso?: string) {
  if (!iso) return "--:--:--";
  try {
    return new Date(iso).toLocaleTimeString();
  } catch {
    return iso.slice(11, 19) || iso;
  }
}

export function IndexPage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [pathDraft, setPathDraft] = useState("");
  const [status, setStatus] = useState<IndexStatus | null>(null);
  const [commits, setCommits] = useState<CommitNode[]>([]);
  const [logs, setLogs] = useState<{ time: string; text: string; tone?: "ok" | "err" }[]>(
    [],
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selected = workspaces.find((w) => w.id === selectedId) ?? null;

  const pushLog = useCallback((text: string, tone?: "ok" | "err") => {
    setLogs((prev) => [
      ...prev.slice(-40),
      { time: new Date().toLocaleTimeString(), text, tone },
    ]);
  }, []);

  const refreshWorkspaces = useCallback(async () => {
    const rows = await listWorkspaces();
    setWorkspaces(rows);
    setSelectedId((prev) => {
      if (prev && rows.some((r) => r.id === prev)) return prev;
      return rows[0]?.id ?? null;
    });
    return rows;
  }, []);

  const refreshSelected = useCallback(
    async (id: string) => {
      const [st, rows] = await Promise.all([
        getIndexStatus(id),
        listCommits(id, 30),
      ]);
      setStatus(st);
      setCommits(rows);
    },
    [],
  );

  useEffect(() => {
    void refreshWorkspaces().catch((err: unknown) => {
      setError(err instanceof Error ? err.message : "Failed to load workspaces");
    });
  }, [refreshWorkspaces]);

  useEffect(() => {
    if (!selectedId) {
      setStatus(null);
      setCommits([]);
      return;
    }
    void refreshSelected(selectedId).catch(() => {
      /* empty until first index */
      setCommits([]);
    });
  }, [selectedId, refreshSelected]);

  async function onRegister() {
    const path = pathDraft.trim();
    if (!path) return;
    setBusy(true);
    setError(null);
    try {
      const ws = await registerWorkspace(path);
      pushLog(`Registered ${ws.path}`, "ok");
      setPathDraft("");
      await refreshWorkspaces();
      setSelectedId(ws.id ?? null);
    } catch (err: unknown) {
      const msg = err instanceof ApiError ? err.message : "Register failed";
      setError(msg);
      pushLog(msg, "err");
    } finally {
      setBusy(false);
    }
  }

  async function onIndex(id: string) {
    setBusy(true);
    setError(null);
    pushLog(`Starting index job for ${id}…`);
    try {
      const result = await startIndex(id);
      pushLog(result.message, "ok");
      await refreshWorkspaces();
      await refreshSelected(id);
    } catch (err: unknown) {
      const msg = err instanceof ApiError ? err.message : "Index failed";
      setError(msg);
      pushLog(msg, "err");
      if (selectedId) {
        try {
          setStatus(await getIndexStatus(selectedId));
        } catch {
          /* ignore */
        }
      }
    } finally {
      setBusy(false);
    }
  }

  async function onRefreshAll() {
    setBusy(true);
    setError(null);
    try {
      const rows = await refreshWorkspaces();
      for (const ws of rows) {
        if (!ws.id) continue;
        pushLog(`Indexing ${ws.name}…`);
        await startIndex(ws.id);
      }
      pushLog("Refresh all complete", "ok");
      if (selectedId) await refreshSelected(selectedId);
      await refreshWorkspaces();
    } catch (err: unknown) {
      const msg = err instanceof ApiError ? err.message : "Refresh failed";
      setError(msg);
      pushLog(msg, "err");
    } finally {
      setBusy(false);
    }
  }

  const progress = status?.progress ?? 0;
  const indexing = status?.status === "indexing" || busy;

  return (
    <main className="h-full p-xl overflow-y-auto space-y-xl max-w-5xl">
      <div className="flex items-center justify-between border-b border-border pb-sm">
        <h2 className="font-headline-lg text-headline-lg text-on-surface">
          Index console
        </h2>
        <button
          type="button"
          disabled={busy || workspaces.length === 0}
          onClick={() => void onRefreshAll()}
          className="flex items-center bg-surface-container-low border border-border hover:bg-surface-container-high px-md py-sm rounded-lg text-foreground font-body-sm text-body-sm transition-colors disabled:opacity-50"
        >
          <span className="material-symbols-outlined mr-xs text-[18px]">sync</span>
          Refresh All
        </button>
      </div>

      {error && (
        <p className="font-body-sm text-body-sm text-danger">{error}</p>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-lg items-start">
        <div className="lg:col-span-1 space-y-lg flex flex-col">
          <section className="bg-surface-container-low border border-border p-md rounded-lg flex flex-col gap-sm">
            <h3 className="font-label-md text-label-md text-on-surface-variant flex items-center">
              <span className="material-symbols-outlined mr-xs text-[16px]">
                folder_open
              </span>
              Add Workspace
            </h3>
            <input
              className="flex-1 bg-surface-container-lowest border border-border rounded-lg px-sm py-xs text-on-surface font-technical-mono text-technical-mono focus:outline-none focus:border-primary transition-colors h-8"
              type="text"
              placeholder="~/dev/my-repo"
              value={pathDraft}
              onChange={(e) => setPathDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") void onRegister();
              }}
            />
            <button
              type="button"
              disabled={busy || !pathDraft.trim()}
              onClick={() => void onRegister()}
              className="bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20 hover:border-primary/40 px-md py-sm rounded-lg font-label-md text-label-md transition-colors mt-xs flex items-center justify-center w-full disabled:opacity-50"
            >
              <span className="material-symbols-outlined mr-xs text-[16px]">add</span>
              Initialize Path
            </button>
          </section>

          <section className="bg-surface-container-lowest border border-border rounded-lg p-md flex flex-col gap-sm">
            <h3 className="font-label-md text-label-md text-muted">Workspaces</h3>
            {workspaces.length === 0 && (
              <p className="font-technical-mono-sm text-technical-mono-sm text-muted">
                None registered yet
              </p>
            )}
            {workspaces.map((ws) => (
              <button
                key={ws.id ?? ws.path}
                type="button"
                onClick={() => setSelectedId(ws.id ?? null)}
                className={`text-left p-sm rounded border transition-colors ${
                  ws.id === selectedId
                    ? "border-primary bg-surface-container-low"
                    : "border-border hover:border-outline"
                }`}
              >
                <div className="font-body-sm text-body-sm text-on-surface truncate">
                  {ws.name}
                </div>
                <div className="font-technical-mono-sm text-technical-mono-sm text-muted truncate">
                  {ws.commits} commits · {ws.status}
                </div>
              </button>
            ))}
          </section>

          {status?.status === "failed" && (
            <section className="bg-surface-container-lowest border border-danger/30 rounded-lg p-md relative flex items-start gap-sm">
              <span className="material-symbols-outlined text-danger mt-[2px]">
                error
              </span>
              <div className="flex-1">
                <h4 className="font-label-md text-label-md text-danger mb-xs">
                  Index Failed
                </h4>
                <p className="font-technical-mono-sm text-technical-mono-sm text-on-surface-variant break-all">
                  {status.error?.message ?? status.message}
                </p>
              </div>
            </section>
          )}
        </div>

        <div className="lg:col-span-2 space-y-lg flex flex-col h-full">
          <section className="bg-surface-container-low border border-border rounded-lg p-lg relative overflow-hidden flex flex-col gap-md border-l-2 border-l-primary">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-label-md text-label-md text-primary flex items-center mb-xs">
                  <span
                    className={`material-symbols-outlined mr-xs text-[16px] ${
                      indexing ? "animate-spin" : ""
                    }`}
                    style={indexing ? { animationDuration: "3s" } : undefined}
                  >
                    autorenew
                  </span>
                  {indexing
                    ? "Indexing Active"
                    : status?.status === "complete"
                      ? "Index Complete"
                      : "Ready to Index"}
                </h3>
                <p className="font-technical-mono-sm text-technical-mono-sm text-muted">
                  {selected?.path ?? "Select a workspace"}
                </p>
              </div>
              <button
                type="button"
                disabled={!selectedId || busy}
                onClick={() => selectedId && void onIndex(selectedId)}
                className="text-primary border border-border hover:border-primary bg-surface-container-lowest px-sm py-xs rounded-lg font-label-caps text-label-caps transition-colors flex items-center disabled:opacity-50"
              >
                <span className="material-symbols-outlined mr-xs text-[14px]">
                  play_arrow
                </span>
                Run Index
              </button>
            </div>
            <div className="space-y-sm">
              <div className="flex justify-between font-technical-mono-sm text-technical-mono-sm">
                <span className="text-on-surface-variant">
                  {status?.message ?? "Waiting…"}
                </span>
                <span className="text-primary font-bold">{progress}%</span>
              </div>
              <div className="h-1 w-full bg-surface-container-highest rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full transition-all"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
            <div className="flex gap-md font-technical-mono-sm text-technical-mono-sm pt-xs border-t border-border mt-xs">
              <div className="flex items-center text-on-surface">
                <span className="material-symbols-outlined text-[14px] mr-xs text-muted">
                  commit
                </span>
                {selected?.commits ?? 0} commits
              </div>
              <div className="w-px h-4 bg-border" />
              <div className="flex items-center text-on-surface">
                <span className="material-symbols-outlined text-[14px] mr-xs text-muted">
                  data_object
                </span>
                {selected?.symbols ?? 0} symbols
              </div>
            </div>
          </section>

          <section className="bg-surface-container-low border border-border rounded-lg flex flex-col flex-1 min-h-[180px] overflow-hidden">
            <div className="p-sm border-b border-border flex items-center justify-between">
              <h3 className="font-label-md text-label-md text-on-surface-variant flex items-center">
                <span className="material-symbols-outlined mr-xs text-[16px]">
                  commit
                </span>
                Commit Nodes
              </h3>
            </div>
            <div className="p-md font-technical-mono-sm text-technical-mono-sm bg-surface-container-lowest flex-1 overflow-y-auto space-y-xs max-h-56">
              {commits.length === 0 && (
                <p className="text-muted">No commits indexed yet.</p>
              )}
              {commits.map((c) => (
                <div key={c.hash} className="border-b border-border/50 pb-xs">
                  <div className="text-on-surface truncate">
                    <span className="text-primary">{c.hash.slice(0, 7)}</span>{" "}
                    {c.message}
                  </div>
                  <div className="text-muted">
                    {c.author} · {formatTime(c.timestamp)} ·{" "}
                    {c.changed_paths.length} files
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="bg-surface-container-low border border-border rounded-lg flex flex-col flex-1 min-h-[160px] overflow-hidden">
            <div className="p-sm border-b border-border bg-surface-container-low flex items-center justify-between">
              <h3 className="font-label-md text-label-md text-on-surface-variant flex items-center">
                <span className="material-symbols-outlined mr-xs text-[16px]">
                  terminal
                </span>
                Recent Activity
              </h3>
            </div>
            <div className="p-md font-technical-mono-sm text-technical-mono-sm text-muted bg-surface-container-lowest flex-1 overflow-y-auto space-y-xs leading-relaxed max-h-40">
              {logs.length === 0 && (
                <LogLine time="--:--:--">Waiting for index activity…</LogLine>
              )}
              {logs.map((line, i) => (
                <LogLine key={`${line.time}-${i}`} time={line.time}>
                  <span
                    className={
                      line.tone === "ok"
                        ? "text-primary"
                        : line.tone === "err"
                          ? "text-danger"
                          : "text-on-surface"
                    }
                  >
                    {line.text}
                  </span>
                </LogLine>
              ))}
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}

function LogLine({
  time,
  children,
}: {
  time: string;
  children: ReactNode;
}) {
  return (
    <div className="flex relative">
      <span className="w-20 text-on-surface-variant opacity-50 shrink-0 select-none">
        {time}
      </span>
      <span>{children}</span>
    </div>
  );
}
