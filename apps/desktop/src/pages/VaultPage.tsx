import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { useSearchParams } from "react-router-dom";
import {
  createVaultBucket,
  createVaultNote,
  getVaultBacklinks,
  getVaultTree,
  listVaultNotes,
  updateVaultNote,
  type VaultBacklink,
  type VaultNote,
  type VaultTreeNode,
} from "../api/client";

function noteStem(id: string) {
  return id.startsWith("note:") ? id.slice(5) : id;
}

function noteBucket(note: VaultNote) {
  if (note.bucket) return note.bucket;
  const parts = note.path.replace(/\.md$/, "").split("/");
  return parts.length > 1 ? parts.slice(0, -1).join("/") : "";
}

export function VaultPage() {
  const [searchParams] = useSearchParams();
  const noteParam = searchParams.get("note");
  const [notes, setNotes] = useState<VaultNote[]>([]);
  const [treeRoot, setTreeRoot] = useState<VaultTreeNode | null>(null);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [selectedBucket, setSelectedBucket] = useState("");
  const [expanded, setExpanded] = useState<Record<string, boolean>>({ "": true });
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [filter, setFilter] = useState("");
  const [backlinks, setBacklinks] = useState<VaultBacklink[]>([]);
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved" | "error">(
    "idle",
  );
  const [error, setError] = useState<string | null>(null);
  const [unresolved, setUnresolved] = useState<VaultNote["unresolved_links"]>([]);

  const active = useMemo(
    () => notes.find((n) => n.id === activeId) ?? null,
    [notes, activeId],
  );

  const filteredNotes = useMemo(() => {
    const q = filter.trim().toLowerCase();
    if (!q) return notes;
    return notes.filter(
      (n) =>
        n.title.toLowerCase().includes(q) || n.path.toLowerCase().includes(q),
    );
  }, [notes, filter]);

  const load = useCallback(async () => {
    try {
      setError(null);
      const [rows, tree] = await Promise.all([listVaultNotes(), getVaultTree()]);
      setNotes(rows);
      setTreeRoot(tree.root);
      setExpanded((prev) => {
        const next: Record<string, boolean> = { ...prev, "": true };
        for (const n of rows) {
          const b = noteBucket(n);
          if (b) next[b] = prev[b] ?? true;
        }
        return next;
      });
      if (!activeId && rows[0]) {
        setActiveId(rows[0].id);
        setSelectedBucket(noteBucket(rows[0]));
      } else if (activeId && !rows.some((n) => n.id === activeId)) {
        setActiveId(rows[0]?.id ?? null);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load vault");
    }
  }, [activeId]);

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!noteParam || notes.length === 0) return;
    const match = notes.find(
      (n) =>
        n.id === `note:${noteParam}` ||
        n.id === noteParam ||
        n.path === noteParam ||
        n.path === `${noteParam}.md` ||
        noteStem(n.id) === noteParam,
    );
    if (match) {
      setActiveId(match.id);
      setSelectedBucket(noteBucket(match));
    }
  }, [noteParam, notes]);

  useEffect(() => {
    if (!activeId) {
      setTitle("");
      setBody("");
      setBacklinks([]);
      setUnresolved([]);
      return;
    }
    const note = notes.find((n) => n.id === activeId);
    if (!note) return;
    setTitle(note.title);
    setBody(note.body);
    setUnresolved(note.unresolved_links ?? []);
    setSelectedBucket(noteBucket(note));
    void getVaultBacklinks(activeId)
      .then(setBacklinks)
      .catch(() => setBacklinks([]));
  }, [activeId, notes]);

  useEffect(() => {
    if (!activeId) return;
    if (active && title === active.title && body === active.body) {
      setSaveState("saved");
      return;
    }
    setSaveState("saving");
    const handle = window.setTimeout(() => {
      void updateVaultNote(activeId, { title, body })
        .then(async (note) => {
          setNotes((prev) => prev.map((n) => (n.id === note.id ? note : n)));
          setUnresolved(note.unresolved_links ?? []);
          setSaveState("saved");
          const bl = await getVaultBacklinks(note.id);
          setBacklinks(bl);
        })
        .catch((err: unknown) => {
          setSaveState("error");
          setError(err instanceof Error ? err.message : "Save failed");
        });
    }, 450);
    return () => window.clearTimeout(handle);
  }, [activeId, title, body, active]);

  async function onCreateNote() {
    try {
      const note = await createVaultNote({
        title: "Untitled note",
        body: "Start writing…\n",
        bucket: selectedBucket || undefined,
      });
      setNotes((prev) => [note, ...prev]);
      setActiveId(note.id);
      await load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Create failed");
    }
  }

  async function onCreateBucket() {
    const name = window.prompt("Bucket name (folder path)", "decisions");
    if (!name?.trim()) return;
    try {
      const bucket = await createVaultBucket(name.trim());
      setSelectedBucket(bucket.bucket);
      setExpanded((prev) => ({ ...prev, [bucket.bucket]: true }));
      if (bucket.index?.id) setActiveId(bucket.index.id);
      await load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Create bucket failed");
    }
  }

  function toggleFolder(path: string) {
    setExpanded((prev) => ({ ...prev, [path]: !prev[path] }));
    setSelectedBucket(path);
  }

  function renderTree(node: VaultTreeNode, depth = 0): ReactNode {
    if (node.type === "folder") {
      const path = node.path;
      const isOpen = expanded[path] ?? depth < 2;
      const kids = node.children ?? [];
      // When filtering, only show folders that contain matches
      if (filter.trim()) {
        const q = filter.trim().toLowerCase();
        const hasMatch = filteredNotes.some(
          (n) =>
            noteBucket(n) === path ||
            noteBucket(n).startsWith(path ? `${path}/` : "") ||
            (path === "" && true),
        );
        if (path && !hasMatch && !kids.some(() => true)) return null;
        // still render if any filtered note under this path
        const under = filteredNotes.some((n) => {
          const b = noteBucket(n);
          return path === "" || b === path || b.startsWith(`${path}/`) || n.path.toLowerCase().includes(q);
        });
        if (path && !under) return null;
      }
      return (
        <div key={`folder:${path || "root"}`}>
          {path !== "" && (
            <button
              type="button"
              onClick={() => toggleFolder(path)}
              className={
                selectedBucket === path
                  ? "w-full text-left px-2 py-1.5 rounded bg-surface-container-high flex items-center gap-1"
                  : "w-full text-left px-2 py-1.5 rounded hover:bg-surface-container-high transition-colors flex items-center gap-1"
              }
              style={{ paddingLeft: 8 + depth * 10 }}
            >
              <span className="material-symbols-outlined text-[16px] text-muted">
                {isOpen ? "folder_open" : "folder"}
              </span>
              <span className="font-body-sm text-body-sm text-on-surface truncate">
                {node.name}
              </span>
            </button>
          )}
          {(path === "" || isOpen) &&
            kids.map((child) => renderTree(child, path === "" ? depth : depth + 1))}
        </div>
      );
    }

    // note node
    if (filter.trim()) {
      const match = filteredNotes.some((n) => n.id === node.id);
      if (!match) return null;
    }
    const isActive = node.id === activeId;
    return (
      <button
        key={node.id}
        type="button"
        onClick={() => {
          setActiveId(node.id);
          const parts = node.path.replace(/\.md$/, "").split("/");
          setSelectedBucket(parts.length > 1 ? parts.slice(0, -1).join("/") : "");
        }}
        className={
          isActive
            ? "w-full text-left px-2 py-1.5 rounded bg-surface-container-highest border-l-2 border-accent-hypha flex flex-col gap-0.5"
            : "w-full text-left px-2 py-1.5 rounded hover:bg-surface-container-high transition-colors flex flex-col gap-0.5 group"
        }
        style={{ paddingLeft: 8 + depth * 10 }}
      >
        <span
          className={
            isActive
              ? "font-body-sm text-body-sm text-primary font-medium truncate flex items-center gap-1"
              : "font-body-sm text-body-sm text-on-surface group-hover:text-primary transition-colors truncate flex items-center gap-1"
          }
        >
          {node.is_index && (
            <span className="material-symbols-outlined text-[14px] text-muted">
              sticky_note_2
            </span>
          )}
          {node.title}
        </span>
      </button>
    );
  }

  return (
    <main className="flex h-full w-full bg-surface">
      <div className="w-64 border-r border-border bg-surface-container-lowest flex flex-col h-full shrink-0 hidden md:flex z-30">
        <div className="h-12 border-b border-border flex items-center justify-between px-3 bg-surface-dim sticky top-0">
          <span className="font-label-caps text-label-caps text-muted uppercase tracking-wider">
            Vault
          </span>
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => void onCreateBucket()}
              className="text-muted hover:text-primary transition-colors"
              title="New bucket"
            >
              <span className="material-symbols-outlined text-[18px]">create_new_folder</span>
            </button>
            <button
              type="button"
              onClick={() => void onCreateNote()}
              className="text-muted hover:text-primary transition-colors"
              title={
                selectedBucket
                  ? `New note in ${selectedBucket}`
                  : "New note (vault root)"
              }
            >
              <span className="material-symbols-outlined text-[18px]">add</span>
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-2 flex flex-col gap-0.5">
          <div className="relative mb-2">
            <span className="material-symbols-outlined absolute left-2 top-1/2 -translate-y-1/2 text-muted text-[16px]">
              search
            </span>
            <input
              className="w-full bg-surface-container border border-border rounded-lg pl-8 pr-2 py-1.5 font-body-sm text-body-sm text-on-surface focus:outline-none focus:border-primary placeholder-muted/50 transition-colors duration-150"
              placeholder="Filter vault..."
              type="text"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            />
          </div>
          {selectedBucket && (
            <p className="px-2 mb-1 font-technical-mono-sm text-technical-mono-sm text-muted truncate">
              bucket: {selectedBucket}
            </p>
          )}
          {treeRoot ? (
            renderTree(treeRoot)
          ) : (
            <p className="font-body-sm text-body-sm text-muted px-2 py-4">
              No notes yet. Create a bucket or note.
            </p>
          )}
          {notes.length === 0 && (
            <p className="font-body-sm text-body-sm text-muted px-2 py-4">
              Empty vault — use folder+ or + to start.
            </p>
          )}
        </div>
      </div>

      <div className="flex-1 bg-surface flex flex-col h-full min-w-0 z-20 relative">
        <div className="h-12 border-b border-border flex items-center justify-between px-6 bg-surface-dim sticky top-0 shrink-0">
          <div className="flex items-center gap-4 min-w-0">
            <div className="flex items-center gap-2 text-muted font-technical-mono-sm text-technical-mono-sm truncate">
              <span>Vault</span>
              <span className="material-symbols-outlined text-[14px]">
                chevron_right
              </span>
              <span className="text-on-surface">
                {active ? active.path : "—"}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <span className="bg-surface-container-high border border-border px-2 py-0.5 rounded font-technical-mono-sm text-technical-mono-sm text-muted flex items-center gap-1">
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  saveState === "error"
                    ? "bg-danger"
                    : saveState === "saving"
                      ? "bg-muted"
                      : "bg-accent-hypha"
                }`}
              />
              {saveState === "saving"
                ? "Saving…"
                : saveState === "error"
                  ? "Error"
                  : "Saved"}
            </span>
          </div>
        </div>

        {error && (
          <p className="px-6 pt-3 font-body-sm text-body-sm text-danger">{error}</p>
        )}

        {activeId ? (
          <div className="flex-1 overflow-y-auto p-6 md:p-12 lg:px-24 xl:px-32 relative">
            <div className="max-w-3xl mx-auto relative z-10">
              <div className="mb-6">
                <input
                  className="w-full bg-transparent font-headline-lg text-headline-lg text-on-surface font-bold tracking-tight mb-3 outline-none border-none"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
                <div className="flex items-center gap-4 text-muted border-b border-border pb-4 flex-wrap">
                  <div className="font-technical-mono text-technical-mono flex items-center gap-2">
                    <span className="material-symbols-outlined text-[16px]">
                      folder
                    </span>
                    {active?.abs_path ?? active?.path}
                  </div>
                  <div className="font-technical-mono-sm text-technical-mono-sm bg-surface-container px-2 py-0.5 rounded border border-border">
                    id:{noteStem(activeId)}
                  </div>
                  {active?.is_index && (
                    <div className="font-technical-mono-sm text-technical-mono-sm bg-surface-container px-2 py-0.5 rounded border border-border text-primary">
                      bucket index
                    </div>
                  )}
                </div>
              </div>

              <textarea
                className="w-full min-h-[420px] bg-transparent font-body-md text-body-md text-on-surface-variant leading-relaxed outline-none resize-y"
                value={body}
                onChange={(e) => setBody(e.target.value)}
                placeholder="Write markdown. Use [[wikilinks]] to notes or symbols. Bucket _index.md briefs feed structure packs (no RAG)."
              />

              {unresolved && unresolved.length > 0 && (
                <div className="mt-6 border border-border rounded-lg p-4 bg-surface-container-low">
                  <div className="font-label-caps text-label-caps text-muted mb-2">
                    Unresolved links
                  </div>
                  <ul className="space-y-1">
                    {unresolved.map((u) => (
                      <li
                        key={u.raw}
                        className="font-technical-mono-sm text-technical-mono-sm text-muted"
                      >
                        [[{u.target}]]
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-muted font-body-md">
            Create a bucket or select a note
          </div>
        )}
      </div>

      <div className="w-64 border-l border-border bg-surface-container-lowest hidden xl:flex flex-col h-full shrink-0 z-30">
        <div className="h-12 border-b border-border flex items-center px-4 bg-surface-dim sticky top-0 shrink-0">
          <span className="font-label-caps text-label-caps text-muted uppercase tracking-wider flex items-center gap-2">
            <span className="material-symbols-outlined text-[16px]">
              device_hub
            </span>
            Backlinks
          </span>
        </div>
        <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
          {backlinks.length === 0 && (
            <p className="font-body-sm text-body-sm text-muted">
              No backlinks yet. Link here with [[
              {active ? noteStem(active.id) : "note"}]].
            </p>
          )}
          {backlinks.map((b) => (
            <button
              key={b.id}
              type="button"
              onClick={() => setActiveId(b.id)}
              className="text-left bg-surface-container border border-border p-3 rounded-lg hover:border-accent-hypha transition-colors duration-150"
            >
              <div className="font-body-sm text-body-sm text-primary font-medium mb-1 truncate">
                {b.title}
              </div>
              <div className="font-technical-mono-sm text-technical-mono-sm text-muted line-clamp-2">
                {b.excerpt}
              </div>
            </button>
          ))}
        </div>
      </div>
    </main>
  );
}
