const notes = [
  { title: "API Design", path: "~/mycelium-vault/api...", active: false },
  {
    title: "Rate limit retries — decision",
    path: "~/mycelium-vault/rate...",
    active: true,
  },
  { title: "Auth flow", path: "~/mycelium-vault/auth...", active: false },
  { title: "Database schema", path: "~/mycelium-vault/db...", active: false },
];

const backlinks = [
  {
    title: "authenticate",
    excerpt:
      "...implementation depends on the [[rate-limits]] module to prevent brute force...",
  },
  {
    title: "infrastructure-ops",
    excerpt:
      "Review [[rate-limits]] configuration prior to the next regional rollout...",
  },
  {
    title: "scaling-strategy",
    excerpt:
      "To mitigate thundering herds, we established standard [[rate-limits]] across all ingress nodes...",
  },
];

export function VaultPage() {
  return (
    <main className="flex h-full w-full bg-surface">
      <div className="w-64 border-r border-border bg-surface-container-lowest flex flex-col h-full shrink-0 hidden md:flex z-30">
        <div className="h-12 border-b border-border flex items-center justify-between px-4 bg-surface-dim sticky top-0">
          <span className="font-label-caps text-label-caps text-muted uppercase tracking-wider">
            Vault Notes
          </span>
          <button
            type="button"
            className="text-muted hover:text-primary transition-colors"
          >
            <span className="material-symbols-outlined text-[18px]">add</span>
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 flex flex-col gap-1">
          <div className="relative mb-2">
            <span className="material-symbols-outlined absolute left-2 top-1/2 -translate-y-1/2 text-muted text-[16px]">
              search
            </span>
            <input
              className="w-full bg-surface-container border border-border rounded-lg pl-8 pr-2 py-1.5 font-body-sm text-body-sm text-on-surface focus:outline-none focus:border-primary placeholder-muted/50 transition-colors duration-150"
              placeholder="Filter vault..."
              type="text"
            />
          </div>
          {notes.map((n) => (
            <button
              key={n.title}
              type="button"
              className={
                n.active
                  ? "w-full text-left px-3 py-2 rounded bg-surface-container-highest border-l-2 border-accent-hypha flex flex-col gap-1"
                  : "w-full text-left px-3 py-2 rounded hover:bg-surface-container-high transition-colors flex flex-col gap-1 group"
              }
            >
              <span
                className={
                  n.active
                    ? "font-body-md text-body-md text-primary font-medium truncate"
                    : "font-body-sm text-body-sm text-on-surface group-hover:text-primary transition-colors truncate"
                }
              >
                {n.title}
              </span>
              <span className="font-technical-mono-sm text-technical-mono-sm text-muted truncate">
                {n.path}
              </span>
            </button>
          ))}
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
              <span className="text-on-surface">rate-limits.md</span>
            </div>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <span className="bg-surface-container-high border border-border px-2 py-0.5 rounded font-technical-mono-sm text-technical-mono-sm text-muted flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-accent-hypha" /> Saved
            </span>
            <button
              type="button"
              className="text-muted hover:text-primary transition-colors"
              title="View History"
            >
              <span className="material-symbols-outlined text-[20px]">
                history
              </span>
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 md:p-12 lg:px-24 xl:px-32 relative">
          <div className="max-w-3xl mx-auto relative z-10">
            <div className="mb-10">
              <h1
                className="font-headline-lg text-headline-lg text-on-surface font-bold tracking-tight mb-3 outline-none"
                contentEditable
                suppressContentEditableWarning
              >
                Rate limit retries — decision
              </h1>
              <div className="flex items-center gap-4 text-muted border-b border-border pb-4">
                <div className="font-technical-mono text-technical-mono flex items-center gap-2">
                  <span className="material-symbols-outlined text-[16px]">
                    folder
                  </span>
                  ~/mycelium-vault/rate-limits.md
                </div>
                <div className="font-technical-mono-sm text-technical-mono-sm bg-surface-container px-2 py-0.5 rounded border border-border">
                  Last modified: 2h ago
                </div>
              </div>
            </div>

            <div className="prose prose-invert text-on-surface-variant outline-none min-h-[500px]">
              <p className="mb-6 font-body-md text-body-md leading-relaxed">
                After reviewing the <span className="note-link">[[authenticate]]</span>{" "}
                module, we decided to implement a jittered backoff. This ensures
                that <span className="note-link">[[rate-limiting]]</span>{" "}
                doesn&apos;t cause thundering herd issues during recovery.
              </p>
              <h3 className="font-headline-md text-headline-md font-medium text-on-surface mt-8 mb-4">
                Context
              </h3>
              <p className="mb-6 font-body-md text-body-md leading-relaxed">
                Initial testing revealed that during regional outages, client SDKs
                were aggressively polling the endpoint without variance in their
                sleep cycles. This created significant spikes in load precisely
                when the cluster was attempting to re-establish quorum.
              </p>
              <div className="bg-surface-container-low border border-border rounded-lg p-4 mb-6 font-technical-mono text-technical-mono text-muted relative overflow-hidden group">
                <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-accent-hypha" />
                <div className="flex justify-between items-center mb-2 text-on-surface-variant font-technical-mono-sm text-technical-mono-sm">
                  <span>src/net/backoff.rs</span>
                  <button
                    type="button"
                    className="opacity-0 group-hover:opacity-100 transition-opacity hover:text-primary"
                  >
                    <span className="material-symbols-outlined text-[16px]">
                      content_copy
                    </span>
                  </button>
                </div>
                <pre className="m-0 overflow-x-auto text-[13px]">
                  <code>{`fn calculate_jitter(base: Duration, attempt: u32) -> Duration {
    let max_sleep = base * (2_u32.pow(attempt));
    let jitter = rand::thread_rng().gen_range(0..=max_sleep.as_millis());
    Duration::from_millis(jitter as u64)
}`}</code>
                </pre>
              </div>
              <h3 className="font-headline-md text-headline-md font-medium text-on-surface mt-8 mb-4">
                Implementation Details
              </h3>
              <ul className="list-disc pl-5 space-y-2 mb-6 font-body-md text-body-md">
                <li>Base delay set to 100ms.</li>
                <li>
                  Max backoff capped at 30 seconds to prevent indefinite hangs in
                  interactive sessions.
                </li>
                <li>
                  Applied primarily to the{" "}
                  <span className="bg-surface-container-high border border-border px-1.5 py-0.5 rounded font-technical-mono-sm text-technical-mono-sm">
                    /v2/sync
                  </span>{" "}
                  and{" "}
                  <span className="bg-surface-container-high border border-border px-1.5 py-0.5 rounded font-technical-mono-sm text-technical-mono-sm">
                    /v2/ingest
                  </span>{" "}
                  endpoints.
                </li>
              </ul>
            </div>
          </div>
        </div>
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
        <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
          <div className="w-full h-24 border border-border rounded-lg bg-surface-dim relative overflow-hidden mb-2 flex items-center justify-center group cursor-pointer hover:border-outline-variant transition-colors duration-150">
            <span className="font-technical-mono-sm text-technical-mono-sm text-muted group-hover:text-primary transition-colors z-10 bg-surface-dim px-2 rounded-lg">
              View Graph
            </span>
            <svg
              className="absolute inset-0 w-full h-full opacity-20 group-hover:opacity-40 transition-opacity"
              preserveAspectRatio="none"
              viewBox="0 0 100 100"
            >
              <circle cx="50" cy="50" fill="#6ec8ff" r="4" />
              <circle cx="20" cy="30" fill="#8B979F" r="2" />
              <circle cx="80" cy="20" fill="#8B979F" r="2" />
              <circle cx="70" cy="80" fill="#8B979F" r="2" />
              <circle cx="30" cy="70" fill="#8B979F" r="2" />
              <line
                stroke="#2A333B"
                strokeDasharray="2,2"
                strokeWidth="1"
                x1="50"
                x2="20"
                y1="50"
                y2="30"
              />
              <line
                stroke="#2A333B"
                strokeDasharray="2,2"
                strokeWidth="1"
                x1="50"
                x2="80"
                y1="50"
                y2="20"
              />
              <line
                stroke="#2A333B"
                strokeDasharray="2,2"
                strokeWidth="1"
                x1="50"
                x2="70"
                y1="50"
                y2="80"
              />
              <line
                stroke="#2A333B"
                strokeDasharray="2,2"
                strokeWidth="1"
                x1="50"
                x2="30"
                y1="50"
                y2="70"
              />
            </svg>
          </div>

          <div className="flex flex-col gap-3 relative before:absolute before:left-2 before:top-4 before:bottom-4 before:w-px before:bg-border before:border-l before:border-dashed before:border-border">
            {backlinks.map((b) => (
              <div
                key={b.title}
                className="pl-6 relative hypha-connector group cursor-pointer"
              >
                <div className="bg-surface-container border border-border p-3 rounded-lg hover:border-accent-hypha transition-colors duration-150">
                  <div className="font-body-sm text-body-sm text-primary font-medium mb-1 truncate">
                    {b.title}
                  </div>
                  <div className="font-technical-mono-sm text-technical-mono-sm text-muted line-clamp-2">
                    {b.excerpt}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}
