import { IMPACT_DISCLAIMER, IMPACT_INTRO, IMPACT_METRICS } from "../content";

export function Impact() {
  return (
    <section
      id="impact"
      data-chapter="impact"
      className="relative overflow-hidden px-6 py-28"
    >
      <div className="relative z-10 mx-auto max-w-5xl">
        <p className="font-display text-sm font-medium uppercase tracking-[0.2em] text-[var(--color-teal)]">
          {IMPACT_INTRO.eyebrow}
        </p>
        <h2 className="mt-3 max-w-3xl font-display text-4xl font-semibold tracking-tight text-[var(--color-fg)] sm:text-5xl">
          {IMPACT_INTRO.headline}
        </h2>
        <p className="mt-5 max-w-2xl text-lg leading-relaxed text-[var(--color-muted)]">
          {IMPACT_INTRO.sub}
        </p>

        <ul className="mt-14 grid gap-8 sm:grid-cols-2">
          {IMPACT_METRICS.map((metric) => (
            <li
              key={metric.id}
              className="rounded-xl border border-white/10 bg-[var(--color-surface)] px-6 py-6"
            >
              <p className="font-display text-4xl font-semibold tracking-tight text-[var(--color-teal)] sm:text-5xl">
                {metric.stat}
              </p>
              <h3 className="mt-3 font-display text-xl font-semibold tracking-tight text-[var(--color-fg)]">
                {metric.title}
              </h3>
              <p className="mt-2 max-w-md text-base leading-relaxed text-[var(--color-muted)]">
                {metric.body}
              </p>
            </li>
          ))}
        </ul>

        <p className="mt-12 max-w-2xl text-sm leading-relaxed text-[var(--color-muted)]">
          {IMPACT_DISCLAIMER}
        </p>
      </div>
    </section>
  );
}
