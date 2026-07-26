import { LINKS } from "../content";

const NAV_LINKS = [
  { href: "#features", label: "Features" },
  { href: "#why", label: "Why" },
  { href: "#setup", label: "Setup" },
  { href: "#impact", label: "Impact" },
] as const;

const linkClass =
  "cursor-pointer rounded-sm transition-colors duration-200 hover:text-[var(--color-teal)]";

export function SiteNav() {
  return (
    <header className="site-nav fixed inset-x-0 top-0 z-50 border-b border-white/5">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <a href="#" className={`flex items-center gap-3 ${linkClass}`}>
          <img
            src="/logo-E-slate-teal.svg"
            alt="Mycelium"
            className="h-8 w-8 rounded-md"
          />
          <span className="font-display text-lg font-semibold tracking-tight text-[var(--color-fg)]">
            Mycelium
          </span>
        </a>
        <ul className="flex flex-wrap items-center justify-end gap-x-5 gap-y-2 text-sm font-medium text-[var(--color-muted)]">
          {NAV_LINKS.map((link) => (
            <li key={link.href}>
              <a href={link.href} className={linkClass}>
                {link.label}
              </a>
            </li>
          ))}
          <li>
            <a
              href={LINKS.releases}
              target="_blank"
              rel="noreferrer"
              className={linkClass}
            >
              Download
            </a>
          </li>
          <li>
            <a
              href={LINKS.github}
              target="_blank"
              rel="noreferrer"
              className={linkClass}
            >
              GitHub
            </a>
          </li>
        </ul>
      </nav>
    </header>
  );
}
