import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { StatusPill } from "@mycelium/ui";
import { getHealth } from "../api/client";

const mainNav = [
  { to: "/", label: "Library", icon: "folder_open", end: true },
  { to: "/index", label: "Index", icon: "sync", end: false },
  { to: "/search", label: "Search", icon: "search", end: false },
  { to: "/vault", label: "Vault", icon: "security", end: false },
  { to: "/settings", label: "Settings", icon: "settings", end: false },
] as const;

const footerNav = [
  { label: "Docs", icon: "menu_book" },
  { label: "Update", icon: "system_update_alt" },
] as const;

function navClass({ isActive }: { isActive: boolean }) {
  return isActive
    ? "flex items-center gap-md py-sm cursor-pointer text-primary border-l-2 border-primary pl-3 bg-accent-dim/80 font-body-sm text-body-sm font-medium transition-colors duration-150"
    : "flex items-center gap-md py-sm cursor-pointer text-muted pl-4 hover:bg-surface-container-high hover:text-on-surface transition-colors duration-150 font-body-sm text-body-sm";
}

export function AppShell() {
  const [coreConnected, setCoreConnected] = useState(false);
  const [coreLabel, setCoreLabel] = useState("Core · Connecting…");

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      try {
        const health = await getHealth();
        if (cancelled) return;
        const ok = health.status === "ok";
        setCoreConnected(ok);
        setCoreLabel(
          ok
            ? `Core · Connected${health.version ? ` · v${health.version}` : ""}`
            : "Core · Degraded",
        );
      } catch {
        if (cancelled) return;
        setCoreConnected(false);
        setCoreLabel("Core · Offline");
      }
    }

    void poll();
    const id = window.setInterval(poll, 4000);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, []);

  return (
    <div className="h-screen w-screen overflow-hidden bg-surface-dim text-on-surface">
      <nav className="fixed left-0 top-0 h-full w-[176px] bg-surface-container-lowest border-r border-border flex flex-col py-lg z-50">
        <div className="px-lg mb-xl flex items-center gap-sm">
          <div className="w-8 h-8 rounded-full bg-surface-container flex items-center justify-center border border-border">
            <span className="material-symbols-outlined text-primary text-[18px]">
              account_tree
            </span>
          </div>
          <div>
            <h1 className="font-headline-md text-headline-md font-bold text-on-surface leading-tight">
              Mycelium
            </h1>
            <p className="font-body-sm text-body-sm text-muted leading-tight">
              Local Instrument
            </p>
          </div>
        </div>

        <div className="px-lg mb-xl">
          <button
            type="button"
            className="w-full flex items-center justify-center gap-sm bg-primary text-on-primary hover:brightness-110 py-sm rounded-xl transition-colors duration-150 font-body-sm text-body-sm font-medium"
          >
            <span className="material-symbols-outlined text-[16px]">add</span>
            New note
          </button>
        </div>

        <div className="flex-1 flex flex-col gap-xs">
          {mainNav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={navClass}
            >
              <span className="material-symbols-outlined text-[20px]">
                {item.icon}
              </span>
              {item.label}
            </NavLink>
          ))}
        </div>

        <div className="mt-auto flex flex-col gap-xs font-body-sm text-body-sm pt-xl border-t border-border/50">
          {footerNav.map((item) => (
            <button
              key={item.label}
              type="button"
              className="flex items-center gap-md py-sm cursor-pointer text-muted pl-4 hover:bg-surface-container-high hover:text-on-surface transition-colors duration-150 text-left"
            >
              <span className="material-symbols-outlined text-[18px]">
                {item.icon}
              </span>
              {item.label}
            </button>
          ))}
        </div>
      </nav>

      <header className="fixed top-0 right-0 w-[calc(100%-176px)] h-12 bg-surface-dim border-b border-border flex items-center justify-between px-lg z-40">
        <div className="flex items-center gap-lg">
          <div className="flex items-center gap-xs text-muted">
            <span className="material-symbols-outlined text-[16px]">lock</span>
            <span className="font-technical-mono text-technical-mono text-primary-fixed-dim">
              Local Only
            </span>
          </div>
        </div>
        <div className="flex items-center gap-lg">
          <StatusPill connected={coreConnected} label={coreLabel} />
        </div>
      </header>

      <div className="ml-[176px] mt-12 h-[calc(100vh-48px)] overflow-hidden">
        <Outlet />
      </div>
    </div>
  );
}
