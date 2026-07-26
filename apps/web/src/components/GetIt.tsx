import { LINKS } from "../content";

export function GetIt() {
  return (
    <section
      id="download"
      data-chapter="get-it"
      className="relative overflow-hidden bg-[var(--color-bg)] px-6 py-28"
    >
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 opacity-40"
        style={{
          background:
            "radial-gradient(ellipse at 70% 20%, rgba(0, 209, 178, 0.22), transparent 55%)",
        }}
      />
      <div className="relative z-10 mx-auto flex max-w-3xl flex-col items-start gap-8">
        <div>
          <p className="font-display text-sm font-medium uppercase tracking-[0.2em] text-[var(--color-teal)]">
            Get it
          </p>
          <h2 className="mt-3 font-display text-4xl font-semibold tracking-tight text-[var(--color-fg)] sm:text-5xl">
            Run Mycelium on your machine
          </h2>
          <p className="mt-4 max-w-xl text-lg text-[var(--color-muted)]">
            Packaged Desktop bundles Core on{" "}
            <code className="rounded bg-white/5 px-1.5 py-0.5 text-[var(--color-fg)]">
              127.0.0.1:8787
            </code>
            . No cloud account required.
          </p>
        </div>
        <div className="flex flex-col gap-4 sm:flex-row">
          <a
            href={LINKS.releases}
            target="_blank"
            rel="noreferrer"
            className="btn-primary"
          >
            Download Desktop
          </a>
          <a
            href={LINKS.github}
            target="_blank"
            rel="noreferrer"
            className="btn-secondary"
          >
            View on GitHub
          </a>
        </div>
        <img
          src="/stitch/download.png"
          alt=""
          className="mt-4 w-full max-w-lg rounded-lg opacity-90"
        />
      </div>
    </section>
  );
}
