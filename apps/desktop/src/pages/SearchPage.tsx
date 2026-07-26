import { type FormEvent, useEffect, useState } from "react";
import { ProvenanceChip, type ProvenanceKind } from "@mycelium/ui";
import {
  listWorkspaces,
  runQuery,
  type QueryResult,
  type Workspace,
} from "../api/client";

const KIND_ICON: Record<ProvenanceKind, string> = {
  Symbol: "description",
  Commit: "code_blocks",
  Note: "sticky_note_2",
  File: "draft",
};

function resultMeta(r: QueryResult) {
  if (r.meta?.length) return r.meta;
  return [{ icon: "folder", text: r.path }];
}

export function SearchPage() {
  const [query, setQuery] = useState("greet");
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [workspaceId, setWorkspaceId] = useState<string>("");
  const [results, setResults] = useState<QueryResult[]>([]);
  const [mode, setMode] = useState("hybrid_rag");
  const [selected, setSelected] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hint, setHint] = useState<string | null>(null);

  useEffect(() => {
    void listWorkspaces()
      .then((rows) => {
        setWorkspaces(rows);
        const first = rows.find((w) => w.id)?.id ?? "";
        setWorkspaceId(first);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to load workspaces");
      });
  }, []);

  async function search(q: string, wsId: string) {
    const trimmed = q.trim();
    if (!trimmed || !wsId) return;
    setLoading(true);
    setError(null);
    setHint(null);
    try {
      const data = await runQuery(trimmed, wsId, 8);
      setResults(data.results);
      setMode(data.mode);
      setSelected(0);
      if ("reason" in data && data.reason === "empty_index") {
        setHint(
          (data as { message?: string }).message ??
            "No embeddings yet — index a workspace first.",
        );
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Query failed");
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (workspaceId) void search(query, workspaceId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workspaceId]);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    void search(query, workspaceId);
  }

  return (
    <main className="h-full overflow-y-auto px-8 py-8 flex justify-center bg-surface">
      <div className="w-full max-w-4xl flex flex-col gap-6">
        <form className="flex flex-col gap-2" onSubmit={onSubmit}>
          <div className="flex gap-2">
            <select
              className="bg-surface-container border border-border rounded-lg px-3 py-2 font-technical-mono-sm text-technical-mono-sm text-on-surface min-w-[12rem]"
              value={workspaceId}
              onChange={(e) => setWorkspaceId(e.target.value)}
              aria-label="Workspace"
            >
              {workspaces.length === 0 && (
                <option value="">No workspaces</option>
              )}
              {workspaces.map((w) => (
                <option key={w.id ?? w.path} value={w.id ?? ""}>
                  {w.name}
                </option>
              ))}
            </select>
          </div>
          <div className="relative w-full">
            <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-muted text-[24px]">
              search
            </span>
            <input
              className="w-full bg-surface-container border border-border focus:border-primary outline-none rounded-lg py-4 pl-12 pr-12 font-headline-md text-headline-md text-on-surface transition-colors duration-150"
              placeholder="Search codebase, notes, or run a query..."
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <div className="absolute right-4 top-1/2 -translate-y-1/2 flex items-center gap-1">
              <span className="font-technical-mono text-technical-mono-sm text-muted bg-surface-container-highest border border-border px-1.5 py-0.5 rounded">
                ⌘K
              </span>
            </div>
          </div>
          <div className="flex items-center justify-between px-1">
            <span className="font-technical-mono-sm text-technical-mono-sm text-muted tracking-wide">
              {loading
                ? "Querying Core…"
                : `${results.length} results · ${mode.replace("_", " ")}`}
            </span>
            <div className="flex gap-2">
              <span className="font-technical-mono-sm text-technical-mono-sm text-muted flex items-center gap-1 cursor-pointer hover:text-on-surface">
                <span className="material-symbols-outlined text-[14px]">
                  tune
                </span>{" "}
                Filter
              </span>
            </div>
          </div>
          {error && (
            <p className="font-body-sm text-body-sm text-danger px-1">
              Core unreachable: {error}
            </p>
          )}
          {hint && !error && (
            <p className="font-body-sm text-body-sm text-muted px-1">{hint}</p>
          )}
        </form>

        <div className="flex flex-col gap-2 pb-12">
          {results.map((r, i) => {
            const isSelected = i === selected;
            const kind = r.kind as ProvenanceKind;
            return (
              <button
                type="button"
                key={`${r.kind}-${r.title}-${r.path}-${i}`}
                onClick={() => setSelected(i)}
                className={
                  isSelected
                    ? "group relative flex flex-col gap-1 p-4 rounded-lg bg-accent-dim/60 border border-primary cursor-pointer transition-colors duration-150 text-left"
                    : "group relative flex flex-col gap-1 p-4 rounded-lg bg-surface-container-low border border-transparent hover:border-border hover:bg-surface-container cursor-pointer transition-colors duration-150 text-left"
                }
              >
                {isSelected && (
                  <div className="absolute left-0 top-0 bottom-0 w-[2px] bg-primary rounded-l" />
                )}
                <div className="flex justify-between items-start mb-1">
                  <h3
                    className={`font-body-md text-body-md text-on-surface group-hover:text-primary transition-colors flex items-center gap-2 ${
                      isSelected ? "font-semibold" : "font-medium"
                    }`}
                  >
                    <span
                      className={`material-symbols-outlined text-[16px] ${
                        isSelected ? "text-primary" : "text-muted"
                      }`}
                    >
                      {KIND_ICON[kind] ?? "description"}
                    </span>
                    {r.title}
                  </h3>
                  <div className="flex gap-2">
                    <ProvenanceChip kind={kind} />
                  </div>
                </div>
                <p
                  className={`font-body-sm text-body-sm truncate ${
                    isSelected ? "text-on-surface-variant" : "text-muted"
                  }`}
                >
                  {r.snippet}
                </p>
                <div className="flex items-center gap-4 mt-2">
                  {resultMeta(r).map((m) => (
                    <span
                      key={m.text}
                      className="font-technical-mono-sm text-technical-mono-sm text-muted flex items-center gap-1"
                    >
                      <span className="material-symbols-outlined text-[12px]">
                        {m.icon}
                      </span>
                      {m.text}
                    </span>
                  ))}
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </main>
  );
}
