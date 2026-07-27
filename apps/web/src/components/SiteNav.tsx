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
    <header className="site-nav fixed inset-x-0 top-0 z-50 border-b border-white/5 pt-[env(safe-area-inset-top)]">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6 sm:py-4">
        <a href="#" className={`flex shrink-0 items-center gap-2 sm:gap-3 ${linkClass}`}>
          <img
            src="/logo-E-slate-teal.svg"
            alt="Mycelium"
            className="h-8 w-8 rounded-md"
          />
          <span className="font-display text-lg font-semibold tracking-tight text-[var(--color-fg)]">
            Mycelium
          </span>
        </a>
        <ul className="hidden items-center gap-x-5 text-sm font-medium text-[var(--color-muted)] sm:flex">
          {NAV_LINKS.map((link) => (
            <li key={`${link.href}-${link.label}`}>
              <a href={link.href} className={linkClass}>
                {link.label}
              </a>
            </li>
          ))}
          <li>
            <a
              href={LINKS.desktopDownload}
              download={LINKS.desktopFilename}
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
