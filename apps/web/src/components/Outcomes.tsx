import { OUTCOMES, OUTCOMES_COMPARE, OUTCOMES_INTRO } from "../content";

export function Outcomes() {
  return (
    <section
      id="why"
      data-chapter="outcomes"
      className="relative overflow-hidden px-6 py-28"
    >
      <div className="relative z-10 mx-auto max-w-5xl">
        <p className="font-display text-sm font-medium uppercase tracking-[0.2em] text-[var(--color-teal)]">
          {OUTCOMES_INTRO.eyebrow}
        </p>
        <h2 className="mt-3 max-w-3xl font-display text-[clamp(2rem,5vw,3rem)] font-semibold tracking-tight text-[var(--color-fg)]">
          {OUTCOMES_INTRO.headline}
        </h2>
        <p className="mt-5 max-w-2xl text-lg leading-relaxed text-[var(--color-muted)]">
          {OUTCOMES_INTRO.sub}
        </p>

        <div className="mt-14 grid grid-cols-2 gap-3 sm:gap-4">
          <div className="rounded-xl border border-white/10 bg-[var(--color-surface)] px-4 py-5 sm:px-6 sm:py-6">
            <p className="font-display text-[0.65rem] font-semibold uppercase tracking-[0.18em] text-[var(--color-muted)] sm:text-xs">
              {OUTCOMES_COMPARE.withoutTitle}
            </p>
            <ul className="mt-4 space-y-2 text-sm leading-relaxed text-[var(--color-muted)] sm:space-y-3 sm:text-base">
              {OUTCOMES_COMPARE.without.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </div>
          <div className="rounded-xl border border-[var(--color-teal)]/35 bg-[var(--color-surface)] px-4 py-5 sm:px-6 sm:py-6">
            <p className="font-display text-[0.65rem] font-semibold uppercase tracking-[0.18em] text-[var(--color-teal)] sm:text-xs">
              {OUTCOMES_COMPARE.withTitle}
            </p>
            <ul className="mt-4 space-y-2 text-sm leading-relaxed text-[var(--color-fg)] sm:space-y-3 sm:text-base">
              {OUTCOMES_COMPARE.with.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </div>
        </div>

        <ol className="mt-16 flex flex-col divide-y divide-white/10 border-y border-white/10">
          {OUTCOMES.map((outcome, index) => (
            <li
              key={outcome.id}
              className="grid grid-cols-[3rem_1fr] gap-4 py-8 sm:grid-cols-[4rem_1fr] sm:gap-8"
            >
              <span className="font-display text-sm font-semibold text-[var(--color-teal)]">
                {String(index + 1).padStart(2, "0")}
              </span>
              <div>
                <h3 className="font-display text-2xl font-semibold tracking-tight text-[var(--color-fg)]">
                  {outcome.title}
                </h3>
                <p className="mt-3 max-w-2xl text-base leading-relaxed text-[var(--color-muted)]">
                  {outcome.body}
                </p>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
