import { HERO, LINKS } from "../content";
import { HyphaStroke } from "./HyphaStroke";

export function Hero() {
  return (
    <section
      data-chapter="hero"
      className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden px-6 py-32 text-center"
    >
      <HyphaStroke className="pointer-events-none absolute inset-0 h-full w-full" />
      <div className="relative z-10 flex max-w-3xl flex-col items-center gap-8 pt-16">
        <div data-hero-animate className="flex flex-col items-center gap-4">
          <img
            src="/logo-E-slate-teal.svg"
            alt="Mycelium"
            className="h-24 w-24 rounded-2xl shadow-2xl sm:h-28 sm:w-28"
          />
          <span className="font-display text-5xl font-semibold tracking-tight text-[var(--color-fg)] sm:text-6xl">
            {HERO.brand}
          </span>
        </div>
        <h1
          data-hero-animate
          className="max-w-2xl text-2xl font-semibold leading-tight text-[var(--color-fg)] sm:text-4xl"
        >
          {HERO.headline}
        </h1>
        <p data-hero-animate className="max-w-xl text-lg text-[var(--color-muted)]">
          {HERO.sub}
        </p>
        <div data-hero-animate className="flex flex-col gap-4 sm:flex-row">
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
      </div>
    </section>
  );
}
