import { CAPABILITIES, type Capability } from "../content";

const WASH_INK: Record<Capability["wash"], string> = {
  magenta: "text-[var(--color-fg)]",
  sage: "text-[#0f1113]",
  violet: "text-[var(--color-fg)]",
  teal: "text-[#0f1113]",
  amber: "text-[#0f1113]",
};

export function Capabilities() {
  return (
    <section
      id="features"
      data-chapter="capabilities"
      className="relative h-screen overflow-hidden bg-[var(--color-bg)]"
    >
      <div
        data-caps-track
        className="flex h-full w-max will-change-transform"
      >
        {CAPABILITIES.map((cap, index) => (
          <article
            key={cap.id}
            className={`flex h-full w-screen shrink-0 flex-col justify-between px-8 py-24 sm:px-16 lg:px-24 wash-${cap.wash} ${WASH_INK[cap.wash]}`}
          >
            <div className="flex items-baseline justify-between gap-4">
              <p className="font-display text-sm font-medium uppercase tracking-[0.2em] opacity-70">
                {String(index + 1).padStart(2, "0")} /{" "}
                {String(CAPABILITIES.length).padStart(2, "0")}
              </p>
            </div>
            <div className="max-w-2xl">
              <h2 className="font-display text-5xl font-semibold tracking-tight sm:text-7xl">
                {cap.title}
              </h2>
              <p className="mt-6 max-w-lg text-lg leading-relaxed opacity-90 sm:text-xl">
                {cap.body}
              </p>
            </div>
            <p className="font-display text-sm uppercase tracking-[0.18em] opacity-60">
              Capabilities
            </p>
          </article>
        ))}
      </div>
    </section>
  );
}
