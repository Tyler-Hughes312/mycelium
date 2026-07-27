import { useCallback, useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import {
  getImpactEvents,
  getImpactSummary,
  getSettings,
  type ImpactByModel,
  type ImpactByTool,
  type ImpactEvent,
  type ImpactModelSource,
  type ImpactSummary,
} from "../api/client";

type Range = "today" | "week" | "all";

const RANGES: { id: Range; label: string }[] = [
  { id: "today", label: "Today" },
  { id: "week", label: "Week" },
  { id: "all", label: "All time" },
];

const IMPACT_DISCLAIMER =
  "Estimated vs dumping matched files into the model context. Uses API list prices you can edit in Settings — not Cursor subscription billing. When Cursor does not send a model id, Mycelium uses your Impact default model and labels it Assumed.";

function formatTokens(n: number) {
  return n.toLocaleString();
}

export function formatUsd(amount: number) {
  const abs = Math.abs(amount);
  let min = 2;
  let max = 4;
  if (abs >= 1) {
    min = 2;
    max = 2;
  } else if (abs >= 0.01) {
    min = 2;
    max = 2;
  } else if (abs >= 0.0001) {
    min = 3;
    max = 4;
  } else {
    min = 4;
    max = 4;
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: min,
    maximumFractionDigits: max,
  }).format(amount);
}

function modelSourceLabel(source: ImpactModelSource | undefined) {
  if (source === "inferred") return "Inferred";
  if (source === "default") return "Assumed";
  return "Unknown";
}

const UNPRICED_MODEL_HINT =
  "No list price for this model — add a rate in Settings.";

function showUnpricedModelHint(params: {
  usdSaved: number;
  tokensSaved?: number;
  modelSource?: ImpactModelSource;
  modelId?: string;
  usdPer1mInput?: number;
}): boolean {
  const { usdSaved, tokensSaved = 0, modelSource, modelId, usdPer1mInput } =
    params;
  if (usdSaved !== 0) return false;
  if (modelSource === "inferred") return true;
  if (!modelId) return false;
  if (usdPer1mInput !== undefined) return usdPer1mInput === 0;
  return tokensSaved > 0;
}

function ModelSourceBadge({
  source,
}: {
  source: ImpactModelSource | undefined;
}) {
  const label = modelSourceLabel(source);
  const tone =
    source === "inferred"
      ? "border-primary/30 bg-accent-dim text-primary"
      : source === "default"
        ? "border-border bg-surface-container-high text-on-surface-variant"
        : "border-border bg-surface-container-high/60 text-muted";
  return (
    <span
      className={`inline-flex items-center rounded-md px-sm py-px font-label-caps text-label-caps uppercase tracking-wider ${tone}`}
    >
      {label}
    </span>
  );
}

function BreakdownRow({
  title,
  eventCount,
  tokensSaved,
  usdSaved,
  badge,
  unpricedHint,
}: {
  title: string;
  eventCount: number;
  tokensSaved: number;
  usdSaved: number;
  badge?: ReactNode;
  unpricedHint?: boolean;
}) {
  return (
    <li className="flex flex-wrap items-baseline justify-between gap-sm px-md py-sm">
      <div className="min-w-0">
        <p className="font-label-md text-label-md text-on-surface flex flex-wrap items-center gap-sm">
          <span className="truncate">{title}</span>
          {badge}
        </p>
        <p className="font-technical-mono-sm text-technical-mono-sm text-muted">
          {formatTokens(eventCount)} recall{eventCount === 1 ? "" : "s"}
        </p>
      </div>
      <div className="text-right shrink-0">
        <p className="font-technical-mono-sm text-technical-mono-sm text-primary">
          −{formatTokens(tokensSaved)} tok
        </p>
        <p className="font-technical-mono-sm text-technical-mono-sm text-on-surface">
          {formatUsd(usdSaved)}
        </p>
        {unpricedHint ? (
          <p className="font-technical-mono-sm text-technical-mono-sm text-muted mt-px max-w-[14rem]">
            {UNPRICED_MODEL_HINT}
          </p>
        ) : null}
      </div>
    </li>
  );
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
      setEvents(evRes.events ?? []);
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

  const byTool = summary?.by_tool ?? [];
  const byModel = summary?.by_model ?? [];

  return (
    <main className="h-full overflow-y-auto p-xl bg-surface">
      <div className="max-w-4xl mx-auto flex flex-col gap-lg">
        <header className="space-y-xs">
          <h1 className="font-display text-[28px] text-on-surface tracking-tight">
            Impact
          </h1>
          <p className="font-body-sm text-body-sm text-on-surface-variant max-w-2xl">
            Estimated tokens and API list-price savings from serving tight recall
            packets instead of dumping matched files or filling a vault pack
            ceiling. Counts stay on this machine under{" "}
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
              <Link
                to="/settings"
                className="text-primary underline-offset-2 hover:underline"
              >
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
          <section className="grid gap-md sm:grid-cols-2 lg:grid-cols-4">
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
                $ saved
              </p>
              <p className="mt-sm font-display text-[32px] text-primary tracking-tight">
                {formatUsd(summary.usd_saved ?? 0)}
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

        {summary && summary.event_count > 0 ? (
          <>
            <section className="space-y-sm">
              <h2 className="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-widest">
                Where
              </h2>
              {byTool.length === 0 ? (
                <p className="font-body-sm text-body-sm text-muted">
                  No tool breakdown yet.
                </p>
              ) : (
                <ul className="divide-y divide-border rounded-xl border border-border bg-surface-container-lowest">
                  {byTool.map((row: ImpactByTool) => (
                    <BreakdownRow
                      key={row.tool}
                      title={row.tool}
                      eventCount={row.event_count}
                      tokensSaved={row.tokens_saved}
                      usdSaved={row.usd_saved ?? 0}
                    />
                  ))}
                </ul>
              )}
            </section>

            <section className="space-y-sm">
              <h2 className="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-widest">
                Which LLM
              </h2>
              {byModel.length === 0 ? (
                <p className="font-body-sm text-body-sm text-muted">
                  No model breakdown yet.
                </p>
              ) : (
                <ul className="divide-y divide-border rounded-xl border border-border bg-surface-container-lowest">
                  {byModel.map((row: ImpactByModel) => (
                    <BreakdownRow
                      key={row.model_id || "(unknown)"}
                      title={row.model_id || "Unknown model"}
                      eventCount={row.event_count}
                      tokensSaved={row.tokens_saved}
                      usdSaved={row.usd_saved ?? 0}
                      badge={
                        <ModelSourceBadge source={row.model_source_dominant} />
                      }
                      unpricedHint={showUnpricedModelHint({
                        usdSaved: row.usd_saved ?? 0,
                        tokensSaved: row.tokens_saved,
                        modelSource: row.model_source_dominant,
                        modelId: row.model_id,
                      })}
                    />
                  ))}
                </ul>
              )}
            </section>
          </>
        ) : null}

        <section className="space-y-sm">
          <h2 className="font-label-caps text-label-caps text-on-surface-variant uppercase tracking-widest">
            Why this helps
          </h2>
          <ul className="space-y-sm font-body-sm text-body-sm text-on-surface-variant">
            <li>Spend context on answers, not haystacks of pasted files.</li>
            <li>Reuse Library patterns without re-explaining the codebase.</li>
            <li>
              Ground agent output in your naming, errors, and vault decisions.
            </li>
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
                  <div className="min-w-0">
                    <p className="font-label-md text-label-md text-on-surface flex flex-wrap items-center gap-sm">
                      <span>{ev.tool}</span>
                      {(ev.model_id || ev.model_source) && (
                        <>
                          <span className="font-technical-mono-sm text-technical-mono-sm text-muted">
                            {ev.model_id || "unknown"}
                          </span>
                          <ModelSourceBadge source={ev.model_source} />
                        </>
                      )}
                      {ev.workspace_id ? (
                        <span className="text-muted font-technical-mono-sm text-technical-mono-sm">
                          {ev.workspace_id}
                        </span>
                      ) : null}
                    </p>
                    <p className="font-technical-mono-sm text-technical-mono-sm text-muted">
                      {new Date(ev.ts).toLocaleString()} · served{" "}
                      {formatTokens(ev.served_tokens)} · baseline{" "}
                      {formatTokens(ev.baseline_tokens)}
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="font-technical-mono-sm text-technical-mono-sm text-primary">
                      −{formatTokens(ev.tokens_saved)} tok
                    </p>
                    <p className="font-technical-mono-sm text-technical-mono-sm text-on-surface">
                      {formatUsd(ev.usd_saved ?? 0)}
                    </p>
                    {showUnpricedModelHint({
                      usdSaved: ev.usd_saved ?? 0,
                      tokensSaved: ev.tokens_saved,
                      modelSource: ev.model_source,
                      modelId: ev.model_id,
                      usdPer1mInput: ev.usd_per_1m_input,
                    }) ? (
                      <p className="font-technical-mono-sm text-technical-mono-sm text-muted mt-px max-w-[14rem]">
                        {UNPRICED_MODEL_HINT}
                      </p>
                    ) : null}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        <p className="font-body-sm text-body-sm text-muted border-t border-border pt-md">
          {IMPACT_DISCLAIMER}
        </p>
      </div>
    </main>
  );
}
