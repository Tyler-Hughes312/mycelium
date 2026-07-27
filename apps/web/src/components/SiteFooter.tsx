import { LINKS } from "../content";

const footerLink =
  "cursor-pointer text-[var(--color-muted)] transition-colors duration-200 hover:text-[var(--color-teal)]";

export function SiteFooter() {
  return (
    <footer className="border-t border-white/5 bg-[var(--color-bg)] px-6 py-12">
      <div className="mx-auto flex max-w-6xl flex-col gap-8 sm:flex-row sm:items-end sm:justify-between">
        <div className="max-w-md">
          <div className="flex items-center gap-3">
            <img
              src="/logo-E-slate-teal.svg"
              alt=""
              className="h-7 w-7 rounded-md"
            />
            <span className="font-display text-lg font-semibold text-[var(--color-fg)]">
              Mycelium
            </span>
          </div>
          <p className="mt-4 text-sm leading-relaxed text-[var(--color-muted)]">
            Local-first context layer. Code and Thinking Vault stay on your
            machine — MIT licensed.
          </p>
        </div>
        <nav aria-label="Footer">
          <ul className="flex flex-wrap gap-x-5 gap-y-3 text-sm font-medium sm:justify-end">
            <li>
              <a href="#features" className={footerLink}>
                Features
              </a>
            </li>
            <li>
              <a href="#why" className={footerLink}>
                Why
              </a>
            </li>
            <li>
              <a href="#setup" className={footerLink}>
                Setup
              </a>
            </li>
            <li>
              <a href="#impact" className={footerLink}>
                Impact
              </a>
            </li>
            <li>
              <a
                href={LINKS.desktopDownload}
                download={LINKS.desktopFilename}
                className={footerLink}
              >
                Download
              </a>
            </li>
            <li>
              <a
                href={LINKS.releases}
                target="_blank"
                rel="noreferrer"
                className={footerLink}
              >
                Releases
              </a>
            </li>
            <li>
              <a
                href={LINKS.github}
                target="_blank"
                rel="noreferrer"
                className={footerLink}
              >
                GitHub
              </a>
            </li>
          </ul>
        </nav>
      </div>
    </footer>
  );
}
