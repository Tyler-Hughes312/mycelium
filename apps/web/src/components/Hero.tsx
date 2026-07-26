import { HERO, LINKS } from "../content";
import { HyphaStroke } from "./HyphaStroke";

export function Hero() {
  return (
    <section
      data-chapter="hero"
      className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden px-6 pb-24 pt-32 text-center"
    >
      <HyphaStroke className="pointer-events-none absolute inset-0 h-full w-full" />
      <div className="relative z-10 flex max-w-3xl flex-col items-center gap-7 pt-8">
        <div data-hero-animate className="flex flex-col items-center gap-3">
          <img
            src="/logo-E-slate-teal.svg"
            alt=""
            className="h-20 w-20 rounded-2xl shadow-2xl sm:h-24 sm:w-24"
          />
          <span className="font-display text-5xl font-semibold tracking-tight text-[var(--color-fg)] sm:text-6xl">
            {HERO.brand}
          </span>
        </div>

        <h1
          data-hero-animate
          className="max-w-2xl font-display text-3xl font-semibold leading-[1.15] tracking-tight text-[var(--color-fg)] sm:text-5xl"
        >
          {HERO.headline}
        </h1>

        <p
          data-hero-animate
          className="max-w-xl text-base leading-relaxed text-[var(--color-muted)] sm:text-lg"
        >
          {HERO.sub}
        </p>

        <p
          data-hero-animate
          className="font-display text-xs font-medium uppercase tracking-[0.2em] text-[var(--color-teal)]"
        >
          {HERO.proof}
        </p>

        <div data-hero-animate className="mt-1 flex flex-col gap-3 sm:flex-row">
          <a
            href={LINKS.desktopDownload}
            target="_blank"
            rel="noreferrer"
            className="btn-primary"
          >
            {HERO.primaryCta}
          </a>
          <a href="#features" className="btn-secondary">
            {HERO.secondaryCta}
          </a>
        </div>

        <a
          data-hero-animate
          href={LINKS.github}
          target="_blank"
          rel="noreferrer"
          className="cursor-pointer text-sm text-[var(--color-muted)] transition-colors duration-200 hover:text-[var(--color-teal)]"
        >
          or view the source on GitHub
        </a>

        <a
          href="#features"
          className="mt-10 cursor-pointer font-display text-xs uppercase tracking-[0.22em] text-[var(--color-muted)] transition-colors duration-200 hover:text-[var(--color-teal)]"
          aria-label="Scroll to features"
        >
          Scroll
        </a>
      </div>
    </section>
  );
}
