import { LINKS, SETUP_STEPS } from "../content";

export function Setup() {
  return (
    <section
      id="setup"
      data-chapter="setup"
      className="relative flex min-h-screen flex-col justify-center px-6 py-28"
    >
      <div className="mx-auto w-full max-w-4xl">
        <p className="font-display text-sm font-medium uppercase tracking-[0.2em] text-[var(--color-teal)]">
          Setup
        </p>
        <h2 className="mt-3 font-display text-[clamp(2rem,5vw,3rem)] font-semibold tracking-tight text-[var(--color-fg)]">
          Three steps to a local context layer
        </h2>
        <ol className="mt-12 flex flex-col gap-8">
          {SETUP_STEPS.map((step) => (
            <li
              key={step.n}
              data-setup-step
              className="rounded-xl border border-white/10 bg-[var(--color-surface)] px-6 py-6 sm:px-8"
            >
              <div className="flex flex-row items-baseline gap-4 sm:gap-6">
                <span className="shrink-0 font-display text-sm font-semibold text-[var(--color-teal)]">
                  {String(step.n).padStart(2, "0")}
                </span>
                <div>
                  <h3 className="font-display text-2xl font-semibold text-[var(--color-fg)]">
                    {step.title}
                  </h3>
                  <p className="mt-2 text-base leading-relaxed text-[var(--color-muted)]">
                    {step.body}
                  </p>
                </div>
              </div>
            </li>
          ))}
        </ol>
        <div className="mt-10 flex flex-row flex-wrap items-center gap-4">
          <a
            href={LINKS.desktopDownload}
            download={LINKS.desktopFilename}
            className="btn-primary"
          >
            Download Desktop
          </a>
          <p className="text-sm text-[var(--color-muted)]">
            macOS Gatekeeper / Windows SmartScreen notes:{" "}
            <a
              href={LINKS.desktopInstallDoc}
              target="_blank"
              rel="noreferrer"
              className="cursor-pointer text-[var(--color-teal)] underline-offset-4 transition-colors duration-200 hover:underline"
            >
              Desktop install guide
            </a>
            .
          </p>
        </div>
      </div>
    </section>
  );
}
