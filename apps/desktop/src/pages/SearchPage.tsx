import { type FormEvent, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ResultRow, type ProvenanceKind } from "@mycelium/ui";
import {
  listWorkspaces,
  runQuery,
  type QueryResult,
  type Workspace,
} from "../api/client";
import { openLocalFile } from "../lib/fs";

const ALL = "*";

const KIND_ICON: Record<string, string> = {
  Function: "functions",
  Method: "account_tree",
  Class: "data_object",
  Type: "category",
  Const: "pin",
  Symbol: "description",
  Commit: "commit",
  Note: "sticky_note_2",
  File: "draft",
};

function resultMeta(r: QueryResult) {
  if (r.meta?.length) return r.meta;
  const meta = [{ icon: "folder", text: r.path }];
  if (r.workspace_name) {
    meta.unshift({ icon: "folder_open", text: r.workspace_name });
  }
  return meta;
}

export function SearchPage() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [workspaceId, setWorkspaceId] = useState<string>(ALL);
  const [results, setResults] = useState<QueryResult[]>([]);
  const [mode, setMode] = useState("hybrid_rag");
  const [scope, setScope] = useState<string>("");
  const [selected, setSelected] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hint, setHint] = useState<string | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    void listWorkspaces()
      .then((rows) => {
        setWorkspaces(rows);
        setWorkspaceId(ALL);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to load workspaces");
      });
  }, []);

  useEffect(() => {
    if (!menuOpen) return;
    function onDoc(e: MouseEvent) {
      if (!menuRef.current?.contains(e.target as Node)) setMenuOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setMenuOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [menuOpen]);

  async function search(q: string, wsId: string) {
    const trimmed = q.trim();
    if (!trimmed || !wsId) {
      setResults([]);
      return;
    }
    setLoading(true);
    setError(null);
    setHint(null);
    try {
      const data = await runQuery(trimmed, wsId, 8);
      setResults(data.results);
      setMode(data.mode);
      setScope(data.scope ?? (wsId === ALL ? "all_workspaces" : "workspace"));
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
    if (!workspaceId || !query.trim()) return;
    void search(query, workspaceId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workspaceId]);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    void search(query, workspaceId);
  }

  function openResult(r: QueryResult, index: number) {
    setSelected(index);
    if (r.kind === "Note") {
      const id =
        typeof (r as { id?: string }).id === "string"
          ? (r as { id?: string }).id
          : undefined;
      const stem = id?.startsWith("note:")
        ? id.slice(5)
        : id || r.path.replace(/\.md$/, "");
      navigate(`/vault?note=${encodeURIComponent(stem)}`);
      return;
    }
    if (r.kind === "Commit") return;
    void openLocalFile(r.path, {
      line: r.start_line,
      workspaceRoot: r.workspace_path,
    });
  }

  function pickScope(id: string) {
    setWorkspaceId(id);
    setMenuOpen(false);
  }

  const activeName =
    workspaceId === ALL
      ? "All repos"
      : (workspaces.find((w) => w.id === workspaceId)?.name ?? "Workspace");

  const scopeLabel =
    scope === "all_workspaces"
      ? `all ${workspaces.length || ""} repos`.trim()
      : activeName;

  return (
    <main className="h-full overflow-y-auto px-8 py-8 flex justify-center bg-surface">
      <div className="w-full max-w-4xl flex flex-col gap-6">
        <form className="flex flex-col gap-3" onSubmit={onSubmit}>
          <div className="relative w-full">
            <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-muted text-[24px] pointer-events-none">
              search
            </span>
            <input
              ref={inputRef}
              className="w-full bg-surface-container border border-border focus:border-primary outline-none rounded-lg py-4 pl-12 pr-28 font-headline-md text-headline-md text-on-surface transition-colors duration-150 placeholder:text-muted/70"
              placeholder="how did we handle rate limits"
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              autoFocus
            />
            <div className="absolute right-3 top-1/2 -translate-y-1/2" ref={menuRef}>
              <button
                type="button"
                onClick={() => setMenuOpen((v) => !v)}
                className="flex items-center gap-1.5 max-w-[11rem] h-8 px-2.5 rounded-md bg-surface-container-high/80 border border-border/80 text-muted hover:text-on-surface hover:border-border transition-colors"
                aria-haspopup="listbox"
                aria-expanded={menuOpen}
                aria-label="Search scope"
              >
                <span className="material-symbols-outlined text-[15px] shrink-0">
                  {workspaceId === ALL ? "hub" : "folder_open"}
                </span>
                <span className="font-technical-mono-sm text-technical-mono-sm truncate">
                  {activeName}
                </span>
                <span className="material-symbols-outlined text-[14px] shrink-0 opacity-70">
                  expand_more
                </span>
              </button>
              {menuOpen && (
                <div
                  role="listbox"
                  className="absolute right-0 top-[calc(100%+6px)] z-20 w-64 max-h-72 overflow-y-auto rounded-lg border border-border bg-surface-container-lowest shadow-lg py-1"
                >
                  <button
                    type="button"
                    role="option"
                    aria-selected={workspaceId === ALL}
                    onClick={() => pickScope(ALL)}
                    className={`w-full flex items-center gap-2 px-3 py-2 text-left font-body-sm text-body-sm transition-colors ${
                      workspaceId === ALL
                        ? "bg-accent-dim text-primary"
                        : "text-on-surface hover:bg-surface-container-low"
                    }`}
                  >
                    <span className="material-symbols-outlined text-[16px]">hub</span>
                    <span className="flex-1 truncate">All repos</span>
                    {workspaceId === ALL ? (
                      <span className="material-symbols-outlined text-[14px]">check</span>
                    ) : null}
                  </button>
                  {workspaces.length > 0 && (
                    <div className="my-1 border-t border-border/60" />
                  )}
                  {workspaces.map((w) => {
                    const id = w.id ?? "";
                    const active = workspaceId === id;
                    return (
                      <button
                        key={id || w.path}
                        type="button"
                        role="option"
                        aria-selected={active}
                        disabled={!id}
                        onClick={() => id && pickScope(id)}
                        className={`w-full flex items-center gap-2 px-3 py-2 text-left transition-colors disabled:opacity-40 ${
                          active
                            ? "bg-accent-dim text-primary"
                            : "text-on-surface hover:bg-surface-container-low"
                        }`}
                      >
                        <span className="material-symbols-outlined text-[16px]">
                          folder_open
                        </span>
                        <span className="flex-1 min-w-0">
                          <span className="block font-body-sm text-body-sm truncate">
                            {w.name}
                          </span>
                          <span className="block font-technical-mono-sm text-technical-mono-sm text-muted truncate">
                            {w.path}
                          </span>
                        </span>
                        {active ? (
                          <span className="material-symbols-outlined text-[14px] shrink-0">
                            check
                          </span>
                        ) : null}
                      </button>
                    );
                  })}
                  {workspaces.length === 0 && (
                    <p className="px-3 py-2 font-technical-mono-sm text-technical-mono-sm text-muted">
                      No workspaces yet — add one in Library
                    </p>
                  )}
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between px-1 gap-3">
            <span className="font-technical-mono-sm text-technical-mono-sm text-muted tracking-wide">
              {loading
                ? "Querying…"
                : query.trim()
                  ? `${results.length} results · ${mode.replace(/_/g, " ")} · ${scopeLabel}`
                  : "Type a question and press Enter"}
            </span>
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
            const kind = (r.kind || "Symbol") as ProvenanceKind;
            return (
              <ResultRow
                key={`${r.workspace_id ?? ""}-${r.kind}-${r.title}-${r.path}-${i}`}
                title={r.title}
                snippet={r.snippet}
                kind={kind}
                selected={i === selected}
                meta={resultMeta(r)}
                icon={KIND_ICON[kind] ?? "description"}
                onClick={() => openResult(r, i)}
                onDoubleClick={() => openResult(r, i)}
              />
            );
          })}
        </div>
      </div>
    </main>
  );
}
