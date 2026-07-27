import {
  type FormEvent,
  type KeyboardEvent as ReactKeyboardEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { Link } from "react-router-dom";
import {
  ApiError,
  createThread,
  getHealth,
  getThread,
  handoffThread,
  listThreads,
  listWorkspaces,
  sendThreadMessage,
  type ChatAssembly,
  type ChatReceiptItem,
  type ChatThread,
  type ChatTurn,
  type Workspace,
} from "../api/client";

function formatTokens(n: number) {
  return n.toLocaleString();
}

function threadLabel(t: ChatThread) {
  const title = t.title?.trim();
  if (title) return title;
  return `Thread ${t.id.replace(/^thread:/, "").slice(0, 8)}`;
}

/** Prefer real indexed repos over ephemeral /tmp test workspaces. */
function pickDefaultWorkspaceId(rows: Workspace[], prev = ""): string {
  if (prev && rows.some((w) => w.id === prev)) return prev;
  if (rows.length === 0) return "";
  const score = (w: Workspace) => {
    const path = (w.path || "").toLowerCase();
    const name = (w.name || "").toLowerCase();
    let s = 0;
    if (path.includes("/tmp/") || path.includes("/private/tmp/") || name.startsWith("tmp/")) {
      s -= 100;
    }
    if (w.status === "healthy" || w.status === "indexing") s += 40;
    if ((w.symbols ?? 0) > 0 || (w.commits ?? 0) > 0) s += 20;
    if (name.includes("memoryoptimization") || path.includes("memoryoptimization")) {
      s += 30;
    }
    return s;
  };
  const sorted = [...rows].sort((a, b) => score(b) - score(a));
  return sorted[0]?.id ?? "";
}

const TRANSCRIPT_PAGE = 100;

export function ChatPage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [workspaceId, setWorkspaceId] = useState("");
  const [threads, setThreads] = useState<ChatThread[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [turnCount, setTurnCount] = useState(0);
  const [turnsOffset, setTurnsOffset] = useState(0);
  const [loadingOlder, setLoadingOlder] = useState(false);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [creating, setCreating] = useState(false);
  const [loadingThreads, setLoadingThreads] = useState(false);
  const [loadingTurns, setLoadingTurns] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errorCode, setErrorCode] = useState<string | null>(null);
  const [coreOnline, setCoreOnline] = useState(true);
  const [contextOpen, setContextOpen] = useState(true);
  const [assembly, setAssembly] = useState<ChatAssembly | null>(null);
  const [receiptItems, setReceiptItems] = useState<ChatReceiptItem[]>([]);
  const [nudgeHandoff, setNudgeHandoff] = useState(false);
  const [handoffBusy, setHandoffBusy] = useState(false);
  const [handoffNote, setHandoffNote] = useState<string | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const transcriptRef = useRef<HTMLDivElement>(null);
  const composerRef = useRef<HTMLTextAreaElement>(null);
  const skipScrollRef = useRef(false);

  function setSendError(err: unknown, fallback: string) {
    if (err instanceof ApiError) {
      setError(err.message);
      setErrorCode(err.code ?? null);
    } else {
      setError(err instanceof Error ? err.message : fallback);
      setErrorCode(null);
    }
  }

  useEffect(() => {
    let cancelled = false;
    async function poll() {
      try {
        const health = await getHealth();
        if (!cancelled) setCoreOnline(health.status === "ok");
      } catch {
        if (!cancelled) setCoreOnline(false);
      }
    }
    void poll();
    const id = window.setInterval(() => void poll(), 4000);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, []);

  useEffect(() => {
    void listWorkspaces()
      .then((rows) => {
        setWorkspaces(rows);
        setWorkspaceId((prev) => pickDefaultWorkspaceId(rows, prev));
        setError(null);
        setErrorCode(null);
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

  const refreshThreads = useCallback(async (wsId: string) => {
    if (!wsId) {
      setThreads([]);
      setActiveId(null);
      return;
    }
    setLoadingThreads(true);
    try {
      const rows = await listThreads(wsId);
      setThreads(rows);
      setError(null);
      setErrorCode(null);
      setActiveId((prev) => {
        if (prev && rows.some((t) => t.id === prev)) return prev;
        return rows[0]?.id ?? null;
      });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to list threads");
      setThreads([]);
    } finally {
      setLoadingThreads(false);
    }
  }, []);

  useEffect(() => {
    void refreshThreads(workspaceId);
  }, [workspaceId, refreshThreads]);

  const loadThread = useCallback(async (threadId: string) => {
    setLoadingTurns(true);
    setError(null);
    setErrorCode(null);
    try {
      // Load newest page: probe count, then fetch trailing window.
      const probe = await getThread(threadId, 0, TRANSCRIPT_PAGE);
      const total = probe.turn_count ?? probe.turns?.length ?? 0;
      const offset = Math.max(0, total - TRANSCRIPT_PAGE);
      const detail =
        offset > 0
          ? await getThread(threadId, offset, TRANSCRIPT_PAGE)
          : probe;
      setTurns(detail.turns ?? []);
      setTurnCount(total);
      setTurnsOffset(offset);
      if (detail.last_receipt_items?.length) {
        setReceiptItems(detail.last_receipt_items);
      }
    } catch (err: unknown) {
      setSendError(err, "Failed to load thread");
      setTurns([]);
      setTurnCount(0);
      setTurnsOffset(0);
    } finally {
      setLoadingTurns(false);
    }
  }, []);

  const loadOlderTurns = useCallback(async () => {
    if (!activeId || turnsOffset <= 0 || loadingOlder) return;
    setLoadingOlder(true);
    setError(null);
    setErrorCode(null);
    const el = transcriptRef.current;
    const prevHeight = el?.scrollHeight ?? 0;
    try {
      const olderLimit = Math.min(TRANSCRIPT_PAGE, turnsOffset);
      const olderOffset = turnsOffset - olderLimit;
      const detail = await getThread(activeId, olderOffset, olderLimit);
      skipScrollRef.current = true;
      setTurns((prev) => [...(detail.turns ?? []), ...prev]);
      setTurnsOffset(olderOffset);
      requestAnimationFrame(() => {
        if (!el) return;
        el.scrollTop = el.scrollHeight - prevHeight;
      });
    } catch (err: unknown) {
      setSendError(err, "Failed to load older messages");
    } finally {
      setLoadingOlder(false);
    }
  }, [activeId, turnsOffset, loadingOlder]);

  useEffect(() => {
    if (!activeId) {
      setTurns([]);
      setTurnCount(0);
      setTurnsOffset(0);
      setAssembly(null);
      setReceiptItems([]);
      setNudgeHandoff(false);
      setHandoffNote(null);
      return;
    }
    setAssembly(null);
    setNudgeHandoff(false);
    setHandoffNote(null);
    void loadThread(activeId);
  }, [activeId, loadThread]);

  useEffect(() => {
    if (skipScrollRef.current) {
      skipScrollRef.current = false;
      return;
    }
    const el = transcriptRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [turns, sending]);

  const activeWorkspace =
    workspaces.find((w) => w.id === workspaceId) ?? null;

  async function onCreateThread() {
    if (!workspaceId || !coreOnline) return;
    setCreating(true);
    setError(null);
    setErrorCode(null);
    try {
      const thread = await createThread(workspaceId, "");
      setThreads((prev) => [thread, ...prev]);
      setActiveId(thread.id);
      setTurns([]);
      setTurnCount(0);
      setTurnsOffset(0);
      setAssembly(null);
      setReceiptItems([]);
      setNudgeHandoff(false);
      setHandoffNote(null);
      composerRef.current?.focus();
    } catch (err: unknown) {
      setSendError(err, "Failed to create thread");
    } finally {
      setCreating(false);
    }
  }

  async function onSend(e?: FormEvent) {
    e?.preventDefault();
    const text = draft.trim();
    if (!text || !activeId || !coreOnline || sending) return;
    setSending(true);
    setError(null);
    setErrorCode(null);
    const optimistic: ChatTurn = {
      id: `local:${Date.now()}`,
      role: "user",
      text,
      seq: turnCount + 1,
    };
    setTurns((prev) => [...prev, optimistic]);
    setDraft("");
    try {
      const res = await sendThreadMessage(activeId, text);
      setAssembly(res.assembly);
      setReceiptItems(res.receipt.items ?? []);
      setNudgeHandoff(Boolean(res.nudge_handoff));
      setHandoffNote(null);
      await loadThread(activeId);
      setThreads((prev) =>
        prev.map((t) =>
          t.id === activeId
            ? {
                ...t,
                updated_at: new Date().toISOString(),
                turn_count: (t.turn_count ?? 0) + 2,
                title: t.title || text.slice(0, 48),
              }
            : t,
        ),
      );
    } catch (err: unknown) {
      const code = err instanceof ApiError ? err.code : undefined;
      // llm_upstream persists user + short error assistant turns — reload.
      if (code === "llm_upstream" && activeId) {
        await loadThread(activeId);
      } else {
        setTurns((prev) => prev.filter((t) => t.id !== optimistic.id));
        setDraft(text);
      }
      setSendError(err, "Send failed");
    } finally {
      setSending(false);
    }
  }

  async function onHandoff() {
    if (!activeId || handoffBusy) return;
    setHandoffBusy(true);
    setError(null);
    setErrorCode(null);
    try {
      const res = await handoffThread(activeId);
      const path = res.handoff_path || res.path || res.note?.path || null;
      setHandoffNote(path);
      setNudgeHandoff(false);
    } catch (err: unknown) {
      setSendError(err, "Handoff failed");
    } finally {
      setHandoffBusy(false);
    }
  }

  function onComposerKey(e: ReactKeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void onSend();
    }
  }

  const canSend =
    coreOnline && Boolean(activeId) && Boolean(draft.trim()) && !sending;

  return (
    <main className="flex h-full w-full bg-surface">
      <aside className="w-64 border-r border-border bg-surface-container-lowest flex flex-col h-full shrink-0 hidden md:flex z-30">
        <div className="h-12 border-b border-border flex items-center justify-between px-3 bg-surface-dim sticky top-0 gap-2">
          <span className="font-label-caps text-label-caps text-muted uppercase tracking-wider">
            Chat
          </span>
          <button
            type="button"
            onClick={() => void onCreateThread()}
            disabled={!workspaceId || !coreOnline || creating}
            className="h-8 px-2.5 rounded-lg bg-primary text-on-primary font-label-md text-label-md disabled:opacity-40 disabled:pointer-events-none"
            title={
              workspaceId
                ? "New thread"
                : "Select a workspace to create a thread"
            }
          >
            {creating ? "…" : "New"}
          </button>
        </div>

        <div className="px-3 py-2 border-b border-border/60" ref={menuRef}>
          <button
            type="button"
            onClick={() => setMenuOpen((v) => !v)}
            className="w-full flex items-center gap-1.5 h-9 px-2.5 rounded-md bg-surface-container-high/80 border border-border/80 text-muted hover:text-on-surface hover:border-border transition-colors"
            aria-haspopup="listbox"
            aria-expanded={menuOpen}
            aria-label="Chat workspace"
          >
            <span className="material-symbols-outlined text-[15px] shrink-0">
              folder_open
            </span>
            <span className="font-technical-mono-sm text-technical-mono-sm truncate flex-1 text-left">
              {activeWorkspace?.name ?? "Select workspace"}
            </span>
            <span className="material-symbols-outlined text-[14px] shrink-0 opacity-70">
              expand_more
            </span>
          </button>
          {menuOpen && (
            <div
              role="listbox"
              className="mt-1.5 z-20 w-full max-h-56 overflow-y-auto rounded-lg border border-border bg-surface-container-lowest shadow-lg py-1"
            >
              {workspaces.length === 0 ? (
                <p className="px-3 py-2 font-body-sm text-body-sm text-muted">
                  No workspaces — add one in Library.
                </p>
              ) : (
                workspaces.map((w) => (
                  <button
                    key={w.id}
                    type="button"
                    role="option"
                    aria-selected={workspaceId === w.id}
                    onClick={() => {
                      setWorkspaceId(w.id ?? "");
                      setMenuOpen(false);
                    }}
                    className={`w-full flex items-center gap-2 px-3 py-2 text-left font-body-sm text-body-sm transition-colors ${
                      workspaceId === w.id
                        ? "bg-accent-dim text-primary"
                        : "text-on-surface hover:bg-surface-container-high/70"
                    }`}
                  >
                    <span className="material-symbols-outlined text-[16px]">
                      folder_open
                    </span>
                    <span className="truncate">{w.name}</span>
                  </button>
                ))
              )}
            </div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto py-1">
          {!workspaceId ? (
            <p className="px-3 py-3 font-body-sm text-body-sm text-muted">
              Select a workspace to list threads.
            </p>
          ) : loadingThreads && threads.length === 0 ? (
            <p className="px-3 py-3 font-body-sm text-body-sm text-muted">
              Loading threads…
            </p>
          ) : threads.length === 0 ? (
            <p className="px-3 py-3 font-body-sm text-body-sm text-muted">
              No threads yet. Create one to start chatting.
            </p>
          ) : (
            threads.map((t) => {
              const selected = t.id === activeId;
              return (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setActiveId(t.id)}
                  className={
                    selected
                      ? "w-full text-left px-3 py-2.5 bg-surface-container-highest border-l-2 border-accent-hypha flex flex-col gap-0.5"
                      : "w-full text-left px-3 py-2.5 hover:bg-surface-container-high transition-colors flex flex-col gap-0.5 border-l-2 border-transparent"
                  }
                >
                  <span
                    className={
                      selected
                        ? "font-body-sm text-body-sm text-primary font-medium truncate"
                        : "font-body-sm text-body-sm text-on-surface truncate"
                    }
                  >
                    {threadLabel(t)}
                  </span>
                  <span className="font-technical-mono-sm text-technical-mono-sm text-muted">
                    {t.turn_count ?? 0} turn{(t.turn_count ?? 0) === 1 ? "" : "s"}
                  </span>
                </button>
              );
            })
          )}
        </div>
      </aside>

      <div className="flex-1 min-w-0 flex flex-col h-full">
        <header className="shrink-0 px-6 py-4 border-b border-border/80 space-y-1">
          <h1 className="font-display text-[24px] text-on-surface tracking-tight">
            Mycelium Chat
          </h1>
          <p className="font-body-sm text-body-sm text-on-surface-variant max-w-2xl">
            Full transcript for you; the model only sees the RAG window shown in
            Context used.{" "}
            <span className="text-muted">
              Long threads stay in Mycelium Chat; Cursor&apos;s own window is
              unchanged.
            </span>
          </p>
        </header>

        {error && (
          <div className="shrink-0 px-6 py-2 border-b border-border/60 bg-surface-container-low flex flex-wrap items-center gap-3">
            <p className="font-body-sm text-body-sm text-danger flex-1 min-w-0">
              {error}
            </p>
            {(errorCode === "llm_not_configured" ||
              errorCode === "remote_llm_disabled") && (
              <Link
                to="/settings"
                className="shrink-0 font-label-md text-label-md text-primary underline-offset-2 hover:underline"
              >
                Open Settings
              </Link>
            )}
          </div>
        )}

        {nudgeHandoff && (
          <div className="shrink-0 px-6 py-3 border-b border-border/60 bg-accent-dim/40 flex items-center justify-between gap-md">
            <div>
              <p className="font-label-md text-label-md text-on-surface">
                Pin handoff to vault
              </p>
              <p className="font-body-sm text-body-sm text-on-surface-variant">
                Thread is large or truncated — pin a curated note under{" "}
                <code className="font-technical-mono-sm text-technical-mono-sm text-primary">
                  work/active/
                </code>
                , not a chat dump.
              </p>
            </div>
            <button
              type="button"
              onClick={() => void onHandoff()}
              disabled={handoffBusy || !coreOnline}
              className="shrink-0 px-md h-9 rounded-lg bg-primary text-on-primary font-label-md text-label-md disabled:opacity-40"
            >
              {handoffBusy ? "Pinning…" : "Pin handoff"}
            </button>
          </div>
        )}

        {handoffNote && (
          <div className="shrink-0 px-6 py-2 border-b border-border/60 bg-surface-container-low">
            <p className="font-body-sm text-body-sm text-on-surface-variant">
              Handoff saved:{" "}
              <Link
                to={`/vault?note=${encodeURIComponent(handoffNote.replace(/\.md$/, ""))}`}
                className="text-primary underline-offset-2 hover:underline font-technical-mono-sm text-technical-mono-sm"
              >
                {handoffNote}
              </Link>
            </p>
          </div>
        )}

        <div
          ref={transcriptRef}
          className="flex-1 min-h-0 overflow-y-auto px-6 py-4 space-y-3"
        >
          {!activeId ? (
            <section className="w-full rounded-xl border border-border bg-surface-container-lowest px-lg py-xl space-y-sm max-w-[36rem] mx-auto mt-8">
              <p className="font-label-md text-label-md text-on-surface">
                Start a Mycelium Chat thread
              </p>
              <p className="font-body-sm text-body-sm text-on-surface-variant">
                Pick a workspace, create a thread, then send a message. Long
                threads stay in Mycelium Chat; Cursor&apos;s own window is
                unchanged.
              </p>
              {!workspaceId ? (
                <p className="font-body-sm text-body-sm text-muted">
                  Add a repo in{" "}
                  <Link
                    to="/"
                    className="text-primary underline-offset-2 hover:underline"
                  >
                    Library
                  </Link>{" "}
                  first.
                </p>
              ) : (
                <button
                  type="button"
                  onClick={() => void onCreateThread()}
                  disabled={!coreOnline || creating}
                  className="mt-2 h-10 px-4 rounded-lg bg-primary text-on-primary font-label-md text-label-md disabled:opacity-40 disabled:pointer-events-none"
                >
                  {creating ? "Creating…" : "Create thread"}
                </button>
              )}
            </section>
          ) : loadingTurns && turns.length === 0 ? (
            <p className="font-body-sm text-body-sm text-muted">Loading…</p>
          ) : turns.length === 0 ? (
            <section className="w-full rounded-xl border border-border bg-surface-container-lowest px-lg py-xl space-y-sm max-w-[36rem] mx-auto mt-8">
              <p className="font-label-md text-label-md text-on-surface">
                Empty thread
              </p>
              <p className="font-body-sm text-body-sm text-on-surface-variant">
                Ask about this codebase. Long threads stay in Mycelium Chat;
                Cursor&apos;s own window is unchanged.
              </p>
            </section>
          ) : (
            <>
              {turnsOffset > 0 && (
                <div className="flex flex-col items-center gap-2 py-2">
                  <p className="font-body-sm text-body-sm text-muted text-center">
                    Showing newest {turns.length} of {turnCount} messages — older
                    messages are hidden.
                  </p>
                  <button
                    type="button"
                    onClick={() => void loadOlderTurns()}
                    disabled={loadingOlder || !coreOnline}
                    className="h-8 px-3 rounded-lg border border-border bg-surface-container-high font-label-md text-label-md text-on-surface hover:border-primary/40 disabled:opacity-40"
                  >
                    {loadingOlder ? "Loading…" : "Load older"}
                  </button>
                </div>
              )}
              {turns.map((turn) => {
                const isUser = turn.role === "user";
                return (
                  <div
                    key={turn.id}
                    className={`flex ${isUser ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-xl px-md py-sm space-y-1 ${
                        isUser
                          ? "bg-accent-dim text-on-surface shadow-[inset_0_0_0_1px_rgba(0,209,178,0.28)]"
                          : "bg-surface-container-lowest border border-border"
                      }`}
                    >
                      <p className="font-label-caps text-label-caps text-muted uppercase tracking-wider">
                        {isUser ? "You" : "Assistant"}
                      </p>
                      <p className="font-body-sm text-body-sm text-on-surface whitespace-pre-wrap break-words">
                        {turn.text}
                      </p>
                    </div>
                  </div>
                );
              })}
            </>
          )}
          {sending && (
            <p className="font-body-sm text-body-sm text-muted">Thinking…</p>
          )}
        </div>

        {assembly && (
          <div className="shrink-0 border-t border-border bg-surface-container-lowest">
            <button
              type="button"
              onClick={() => setContextOpen((v) => !v)}
              className="w-full flex items-center justify-between px-6 py-2.5 text-left hover:bg-surface-container-high/40 transition-colors"
            >
              <span className="font-label-md text-label-md text-on-surface flex items-center gap-2">
                <span className="material-symbols-outlined text-[18px] text-primary">
                  analytics
                </span>
                Context used
              </span>
              <span className="flex items-center gap-2">
                <span className="font-technical-mono-sm text-technical-mono-sm text-muted">
                  {formatTokens(assembly.tokens_assembled)} /{" "}
                  {formatTokens(assembly.tokens_full_thread_est)} tok
                </span>
                <span className="material-symbols-outlined text-[18px] text-muted">
                  {contextOpen ? "expand_less" : "expand_more"}
                </span>
              </span>
            </button>
            {contextOpen && (
              <div className="px-6 pb-4 space-y-3">
                <div className="flex flex-wrap gap-2">
                  <span className="inline-flex items-center rounded-md px-sm py-px font-technical-mono-sm text-technical-mono-sm border border-primary/30 bg-accent-dim text-primary">
                    assembled {formatTokens(assembly.tokens_assembled)}
                  </span>
                  <span className="inline-flex items-center rounded-md px-sm py-px font-technical-mono-sm text-technical-mono-sm border border-border bg-surface-container-high text-on-surface-variant">
                    full est {formatTokens(assembly.tokens_full_thread_est)}
                  </span>
                  <span className="inline-flex items-center rounded-md px-sm py-px font-technical-mono-sm text-technical-mono-sm border border-border bg-surface-container-high text-on-surface-variant">
                    saved ~{formatTokens(assembly.tokens_saved_est)}
                  </span>
                  {assembly.truncated ? (
                    <span className="inline-flex items-center rounded-md px-sm py-px font-label-caps text-label-caps uppercase tracking-wider border border-border bg-surface-container-high text-muted">
                      truncated
                    </span>
                  ) : null}
                  {assembly.reason ? (
                    <span className="inline-flex items-center rounded-md px-sm py-px font-label-caps text-label-caps uppercase tracking-wider border border-border bg-surface-container-high text-muted">
                      {assembly.reason}
                    </span>
                  ) : null}
                </div>
                {Object.keys(assembly.budgets ?? {}).length > 0 && (
                  <p className="font-technical-mono-sm text-technical-mono-sm text-muted">
                    budgets:{" "}
                    {Object.entries(assembly.budgets)
                      .map(([k, v]) => `${k}=${v}`)
                      .join(" · ")}
                  </p>
                )}
                {receiptItems.length > 0 ? (
                  <ul className="space-y-1 max-h-36 overflow-y-auto">
                    {receiptItems.map((item) => (
                      <li
                        key={item.id || `${item.path}:${item.title}`}
                        className="font-body-sm text-body-sm text-on-surface-variant flex gap-2 min-w-0"
                      >
                        <span className="font-label-caps text-label-caps text-muted uppercase shrink-0">
                          {item.kind || "hit"}
                        </span>
                        <span className="truncate text-on-surface">
                          {item.title || item.path || item.id}
                        </span>
                        {item.path ? (
                          <span className="font-technical-mono-sm text-technical-mono-sm text-muted truncate">
                            {item.path}
                          </span>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="font-body-sm text-body-sm text-muted">
                    No RAG hits in the last receipt.
                  </p>
                )}
              </div>
            )}
          </div>
        )}

        <form
          onSubmit={(e) => void onSend(e)}
          className="shrink-0 border-t border-border px-6 py-4 bg-surface-dim"
        >
          <div className="flex gap-3 items-end max-w-4xl mx-auto">
            <textarea
              ref={composerRef}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={onComposerKey}
              rows={2}
              disabled={!coreOnline || !activeId}
              placeholder={
                !coreOnline
                  ? "Core offline — composer disabled"
                  : !activeId
                    ? "Create or select a thread first"
                    : "Message Mycelium Chat… (Enter to send)"
              }
              className="flex-1 resize-none bg-surface-container border border-border focus:border-primary outline-none rounded-xl px-4 py-3 font-body-sm text-body-sm text-on-surface placeholder:text-muted/70 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!canSend}
              className="h-11 px-5 rounded-xl bg-primary text-on-primary font-label-md text-label-md disabled:opacity-40 disabled:pointer-events-none"
            >
              {sending ? "…" : "Send"}
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}
