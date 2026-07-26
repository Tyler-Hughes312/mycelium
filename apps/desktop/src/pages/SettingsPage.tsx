export function SettingsPage() {
  return (
    <div className="h-full overflow-y-auto p-xl scroll-smooth bg-surface">
      <div className="max-w-3xl mx-auto space-y-xl pb-xxl">
        <div className="mb-lg">
          <h1 className="font-headline-lg text-headline-lg text-foreground mb-xs">
            Local Environment Setup
          </h1>
          <p className="font-body-sm text-body-sm text-on-surface-variant">
            Configure core storage paths and embedded intelligence parameters.
          </p>
        </div>

        <section className="border border-border bg-surface-container-low rounded-lg p-lg flex items-start gap-md">
          <div className="mt-xs">
            <span
              className="material-symbols-outlined text-outline text-[24px]"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              lock
            </span>
          </div>
          <div>
            <h2 className="font-label-md text-label-md text-on-surface mb-xs flex items-center gap-xs">
              Stays on this machine
              <span className="w-2 h-2 rounded-full bg-primary" />
            </h2>
            <p className="font-body-sm text-body-sm text-on-surface-variant leading-relaxed">
              Mycelium operates entirely local-first. Your code, indices, and
              queries never leave this device by default. The local Core handles
              all processing, and no account or cloud sync is required for full
              functionality.
            </p>
          </div>
        </section>

        <section className="space-y-lg">
          <h3 className="font-label-caps text-label-caps text-on-surface-variant border-b border-border pb-xs uppercase tracking-widest">
            Paths &amp; Storage
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-md items-start">
            <div className="md:col-span-1 pt-sm">
              <label className="font-label-md text-label-md text-foreground block">
                Vault path
              </label>
              <span className="font-body-sm text-body-sm text-on-surface-variant block mt-xs">
                Root directory for semantic indices and metadata.
              </span>
            </div>
            <div className="md:col-span-3">
              <div className="flex gap-sm">
                <input
                  className="flex-1 bg-surface-container border border-border rounded-lg h-10 px-md font-technical-mono text-technical-mono text-primary focus:outline-none focus:border-primary transition-colors duration-150"
                  type="text"
                  defaultValue="~/mycelium-vault"
                />
                <button
                  type="button"
                  className="px-md h-10 border border-border rounded-lg bg-surface-container-high text-foreground font-label-md text-label-md hover:bg-surface-variant transition-colors duration-150 flex items-center gap-xs"
                >
                  <span className="material-symbols-outlined text-[16px]">
                    folder_open
                  </span>
                  Browse
                </button>
              </div>
              <div className="mt-sm flex items-center gap-xs text-on-surface-variant">
                <span className="material-symbols-outlined text-[14px]">
                  info
                </span>
                <span className="font-technical-mono-sm text-technical-mono-sm">
                  Space available: 124.5 GB on /dev/disk1s5
                </span>
              </div>
            </div>
          </div>
        </section>

        <section className="space-y-lg">
          <h3 className="font-label-caps text-label-caps text-on-surface-variant border-b border-border pb-xs uppercase tracking-widest">
            Local Indexing
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-md items-start">
            <div className="md:col-span-1 pt-sm">
              <label className="font-label-md text-label-md text-foreground block">
                Embedding model
              </label>
              <span className="font-body-sm text-body-sm text-on-surface-variant block mt-xs">
                Model used for code and docs vectorization.
              </span>
            </div>
            <div className="md:col-span-3">
              <div className="relative">
                <select
                  className="w-full bg-surface-container border border-border rounded-lg h-10 px-md pr-xl font-technical-mono text-technical-mono text-foreground appearance-none focus:outline-none focus:border-primary transition-colors duration-150"
                  defaultValue="jina-embeddings-v2-base-code"
                >
                  <option value="jina-embeddings-v2-base-code">
                    jina-embeddings-v2-base-code (8192 ctx)
                  </option>
                  <option value="nomic-embed-text-v1.5">
                    nomic-embed-text-v1.5 (8192 ctx)
                  </option>
                  <option value="bge-small-en-v1.5">
                    bge-small-en-v1.5 (512 ctx)
                  </option>
                </select>
                <span className="material-symbols-outlined absolute right-md top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none text-[18px]">
                  expand_more
                </span>
              </div>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-md items-start pt-md">
            <div className="md:col-span-1 pt-sm">
              <label className="font-label-md text-label-md text-foreground block">
                Git history depth
              </label>
              <span className="font-body-sm text-body-sm text-on-surface-variant block mt-xs">
                Commits to parse per repository for context.
              </span>
            </div>
            <div className="md:col-span-3">
              <div className="flex items-center gap-sm">
                <input
                  className="w-24 bg-surface-container border border-border rounded-lg h-10 px-sm font-technical-mono text-technical-mono text-foreground text-center focus:outline-none focus:border-primary transition-colors duration-150"
                  type="number"
                  defaultValue={500}
                />
                <span className="font-body-sm text-body-sm text-on-surface-variant">
                  commits
                </span>
              </div>
            </div>
          </div>
          <div className="flex justify-end pt-lg">
            <button
              type="button"
              className="px-xl h-10 rounded-xl bg-primary text-on-primary font-label-md text-label-md hover:brightness-110 transition-all duration-150 flex items-center gap-sm"
            >
              <span className="material-symbols-outlined text-[18px]">save</span>
              Apply Changes
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
