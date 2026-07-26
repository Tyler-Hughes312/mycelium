import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  getImpactEvents,
  getImpactSummary,
  getSettings,
  type ImpactEvent,
  type ImpactSummary,
} from "../api/client";

type Range = "today" | "week" | "all";

const RANGES: { id: Range; label: string }[] = [
  { id: "today", label: "Today" },
  { id: "week", label: "Week" },
  { id: "all", label: "All time" },
];

function formatTokens(n: number) {
  return n.toLocaleString();
}

export function ImpactPage() {
  const [range, setRange] = useState<Range>("today");
  const [summary, setSummary] = useState<ImpactSummary | null>(null);
  const [events, setEvents] = useState<ImpactEvent[]>([]);
  const [trackingEnabled, setTrackingEnabled] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async (selected: Range) => {
    setLoading(true);
    setError(null);
    try {
      const [sumRes, evRes, settingsRes] = await Promise.all([
        getImpactSummary(selected),
        getImpactEvents(40),
        getSettings(),
      ]);
      setSummary(sumRes.summary);
      setEvents(evRes.events);
      setTrackingEnabled(settingsRes.settings.impact_tracking_enabled !== false);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load impact");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh(range);
  }, [range, refresh]);

  return (
    <main className="h-full overflow-y-auto p-xl bg-surface">
      <div className="max-w-4xl mx-auto flex flex-col gap-lg">
      <header className="space-y-xs">
        <h1 className="font-display text-[28px] text-on-surface tracking-tight">
          Impact
        </h1>
        <p className="font-body-sm text-body-sm text-on-surface-variant max-w-2xl">
          Estimated tokens avoided by serving tight recall packets instead of
          dumping matched files or filling a vault pack ceiling. Counts stay on
          this machine under{" "}
          <code className="font-technical-mono-sm text-technical-mono-sm text-primary">
            ~/.mycelium/data
          </code>
          .
        </p>
      </header>

      {!trackingEnabled && (
        <div className="rounded-xl border border-border bg-surface-container-high/60 px-md py-md">
          <p className="font-label-md text-label-md text-on-surface">
            Tracking paused
          </p>
          <p className="font-body-sm text-body-sm text-on-surface-variant mt-xs">
            Impact logging is off. Enable it in{" "}
            <Link to="/settings" className="text-primary underline-offset-2 hover:underline">
              Settings
            </Link>{" "}
            to resume.
          </p>
        </div>
      )}

      <div className="flex flex-wrap gap-sm">
        {RANGES.map((r) => (
          <button
            key={r.id}
            type="button"
            onClick={() => setRange(r.id)}
            className={`px-md h-9 rounded-xl font-label-md text-label-md transition-colors ${
              range === r.id
                ? "bg-accent-dim text-primary shadow-[inset_0_0_0_1px_rgba(0,209,178,0.28)]"
                : "text-muted hover:text-on-surface hover:bg-surface-container-high/70"
            }`}
          >
            {r.label}
          </button>
        ))}
      </div>

      {error && (
        <p className="font-body-sm text-body-sm text-danger">{error}</p>
      )}

      {loading && !summary ? (
        <p className="font-body-sm text-body-sm text-muted">Loading…</p>
      ) : summary && summary.event_count === 0 ? (
        <section className="rounded-xl border border-border bg-surface-container-lowest px-lg py-xl space-y-sm">
          <p className="font-label-md text-label-md text-on-surface">
            No impact events yet
          </p>
          <p className="font-body-sm text-body-sm text-on-surface-variant max-w-lg">
            Use Desktop Search, Focus via MCP, or Vault pack — Core will log
            estimated savings here after each recall.
          </p>
        </section>
      ) : summary ? (
        <section className="grid gap-md sm:grid-cols-3">
          <div className="rounded-xl border border-border bg-surface-container-lowest px-md py-md">
            <p className="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-widest">
              Tokens saved
            </p>
            <p className="mt-sm font-display text-[32px] text-primary tracking-tight">
              {formatTokens(summary.tokens_saved)}
            </p>
          </div>
          <div className="rounded-xl border border-border bg-surface-container-lowest px-md py-md">
            <p className="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-widest">
              Savings
            </p>
            <p className="mt-sm font-display text-[32px] text-on-surface tracking-tight">
              {summary.savings_pct}%
            </p>
          </div>
          <div className="rounded-xl border border-border bg-surface-container-lowest px-md py-md">
            <p className="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-widest">
              Recalls
            </p>
            <p className="mt-sm font-display text-[32px] text-on-surface tracking-tight">
              {formatTokens(summary.event_count)}
            </p>
          </div>
        </section>
      ) : null}

      <p className="font-technical-mono-sm text-technical-mono-sm text-muted">
        Estimated vs dumping matched files / pack ceiling · served{" "}
        {formatTokens(summary?.served_tokens ?? 0)} · baseline{" "}
        {formatTokens(summary?.baseline_tokens ?? 0)}
      </p>

      <section className="space-y-sm">
        <h2 className="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-widest">
          Why this helps
        </h2>
        <ul className="space-y-sm font-body-sm text-body-sm text-on-surface-variant">
          <li>Spend context on answers, not haystacks of pasted files.</li>
          <li>Reuse Library patterns without re-explaining the codebase.</li>
          <li>Ground agent output in your naming, errors, and vault decisions.</li>
        </ul>
      </section>

      <section className="space-y-sm">
        <h2 className="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-widest">
          Recent events
        </h2>
        {events.length === 0 ? (
          <p className="font-body-sm text-body-sm text-muted">No events yet.</p>
        ) : (
          <ul className="divide-y divide-border rounded-xl border border-border bg-surface-container-lowest">
            {events.map((ev, i) => (
              <li
                key={`${ev.ts}-${ev.tool}-${i}`}
                className="flex flex-wrap items-baseline justify-between gap-sm px-md py-sm"
              >
                <div>
                  <p className="font-label-md text-label-md text-on-surface">
                    {ev.tool}
                    {ev.workspace_id ? (
                      <span className="text-muted font-technical-mono-sm text-technical-mono-sm ml-sm">
                        {ev.workspace_id}
                      </span>
                    ) : null}
                  </p>
                  <p className="font-technical-mono-sm text-technical-mono-sm text-muted">
                    {new Date(ev.ts).toLocaleString()}
                  </p>
                </div>
                <p className="font-technical-mono-sm text-technical-mono-sm text-primary">
                  −{formatTokens(ev.tokens_saved)} tok
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>
      </div>
    </main>
  );
}
