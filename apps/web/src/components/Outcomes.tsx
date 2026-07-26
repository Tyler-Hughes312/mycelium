import { OUTCOMES, OUTCOMES_INTRO } from "../content";

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
        <h2 className="mt-3 max-w-3xl font-display text-4xl font-semibold tracking-tight text-[var(--color-fg)] sm:text-5xl">
          {OUTCOMES_INTRO.headline}
        </h2>
        <p className="mt-5 max-w-2xl text-lg leading-relaxed text-[var(--color-muted)]">
          {OUTCOMES_INTRO.sub}
        </p>

        <div className="mt-14 grid gap-4 sm:grid-cols-2">
          <div className="rounded-xl border border-white/10 bg-[var(--color-surface)] px-6 py-6">
            <p className="font-display text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-muted)]">
              Without Mycelium
            </p>
            <ul className="mt-4 space-y-3 text-base leading-relaxed text-[var(--color-muted)]">
              <li>Re-paste the same files every session</li>
              <li>Burn context window on noise</li>
              <li>Lose last month’s fix in another repo</li>
              <li>Answers that ignore your conventions</li>
            </ul>
          </div>
          <div className="rounded-xl border border-[var(--color-teal)]/35 bg-[var(--color-surface)] px-6 py-6">
            <p className="font-display text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-teal)]">
              With Mycelium
            </p>
            <ul className="mt-4 space-y-3 text-base leading-relaxed text-[var(--color-fg)]">
              <li>Retrieve the right slice on demand</li>
              <li>Keep prompts tight and relevant</li>
              <li>Reuse patterns across the Library</li>
              <li>Outputs that match how you already ship</li>
            </ul>
          </div>
        </div>

        <ol className="mt-16 flex flex-col divide-y divide-white/10 border-y border-white/10">
          {OUTCOMES.map((outcome, index) => (
            <li
              key={outcome.id}
              className="grid gap-3 py-8 sm:grid-cols-[4rem_1fr] sm:gap-8"
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
