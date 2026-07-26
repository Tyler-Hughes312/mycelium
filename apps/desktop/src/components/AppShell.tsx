import { useCallback, useEffect, useState } from "react";
import { Link, NavLink, Outlet } from "react-router-dom";
import { getHealth } from "../api/client";
import { isTauriShell } from "../lib/fs";

async function requestCoreRestart() {
  if (!isTauriShell()) return;
  try {
    const { invoke } = await import("@tauri-apps/api/core");
    await invoke("restart_core");
  } catch {
    // Sidecar missing or already starting
  }
}

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

const NAV_W = 220;

const mainNav = [
  { to: "/", label: "Library", icon: "folder_open", end: true },
  { to: "/index", label: "Index", icon: "hub", end: false },
  { to: "/search", label: "Search", icon: "search", end: false },
  { to: "/impact", label: "Impact", icon: "monitoring", end: false },
  { to: "/vault", label: "Vault", icon: "book_2", end: false },
  { to: "/settings", label: "Settings", icon: "tune", end: false },
] as const;

function navClass({ isActive }: { isActive: boolean }) {
  const base =
    "group relative flex items-center gap-3 mx-2 px-3 py-2.5 rounded-xl font-body-sm text-body-sm transition-all duration-200 ease-out outline-none focus-visible:ring-2 focus-visible:ring-primary/50";
  if (isActive) {
    return `${base} bg-accent-dim text-primary font-medium shadow-[inset_0_0_0_1px_rgba(0,209,178,0.28)]`;
  }
  return `${base} text-muted hover:text-on-surface hover:bg-surface-container-high/70`;
}

export function AppShell() {
  const inTauri = isTauriShell();
  const [coreConnected, setCoreConnected] = useState(false);
  const [booting, setBooting] = useState(inTauri);
  const [retrying, setRetrying] = useState(false);

  const poll = useCallback(async () => {
    try {
      const health = await getHealth();
      const ok = health.status === "ok";
      setCoreConnected(ok);
      return ok;
    } catch {
      setCoreConnected(false);
      return false;
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function boot() {
      if (inTauri) {
        setBooting(true);
        // Rust setup already tries to spawn; nudge again then wait for /health.
        await requestCoreRestart();
        for (let i = 0; i < 40 && !cancelled; i++) {
          if (await poll()) break;
          await sleep(250);
        }
        if (!cancelled) setBooting(false);
      } else {
        await poll();
      }
    }

    void boot();
    const id = window.setInterval(() => {
      void poll();
    }, 4000);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, [inTauri, poll]);

  async function onRetry() {
    setRetrying(true);
    if (inTauri) {
      await requestCoreRestart();
      for (let i = 0; i < 40; i++) {
        if (await poll()) break;
        await sleep(250);
      }
    } else {
      await poll();
    }
    setRetrying(false);
  }

  const showBanner = !coreConnected && !booting;

  return (
    <div className="h-screen w-screen overflow-hidden bg-surface-dim text-on-surface">
      <aside
        className="fixed left-0 top-0 h-full z-50 flex flex-col border-r border-border/80 bg-surface-container-lowest/95 backdrop-blur-md"
        style={{ width: NAV_W }}
      >
        <div className="px-4 pt-5 pb-4">
          <div className="flex items-center gap-3">
            <img
              src="/mycelium-logo.svg"
              alt=""
              width={36}
              height={36}
              className="w-9 h-9 rounded-[0.65rem] shrink-0 ring-1 ring-white/10"
            />
            <div className="min-w-0">
              <p className="font-headline-md text-[17px] font-semibold tracking-tight text-on-surface leading-none">
                Mycelium
              </p>
              <p className="mt-1 font-technical-mono-sm text-technical-mono-sm text-muted tracking-wide uppercase">
                Local
              </p>
            </div>
          </div>
        </div>

        <div className="px-4 pb-2">
          <p className="px-3 mb-1.5 font-label-caps text-label-caps text-muted/80 uppercase tracking-[0.12em]">
            Navigate
          </p>
        </div>

        <nav className="flex-1 flex flex-col gap-0.5 pb-4 overflow-y-auto">
          {mainNav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={navClass}
            >
              {({ isActive }) => (
                <>
                  <span
                    className={`material-symbols-outlined text-[20px] transition-transform duration-200 ${
                      isActive ? "scale-105" : "group-hover:scale-105"
                    }`}
                    style={
                      isActive
                        ? { fontVariationSettings: "'FILL' 1" }
                        : undefined
                    }
                  >
                    {item.icon}
                  </span>
                  <span className="truncate">{item.label}</span>
                  {isActive ? (
                    <span
                      className="ml-auto w-1.5 h-1.5 rounded-full bg-primary shrink-0"
                      aria-hidden
                    />
                  ) : null}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto p-3 border-t border-border/60">
          <div className="flex items-center gap-2 px-3 py-2.5 rounded-xl bg-surface-container/80 ring-1 ring-border/50">
            <span
              className={`material-symbols-outlined text-[16px] ${
                coreConnected ? "text-primary" : "text-muted"
              }`}
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              {coreConnected ? "cloud_done" : booting ? "hourglass_empty" : "cloud_off"}
            </span>
            <div className="min-w-0">
              <p className="font-label-md text-label-md text-on-surface leading-tight">
                {coreConnected
                  ? "Core online"
                  : booting
                    ? "Starting Core…"
                    : "Core offline"}
              </p>
              <p className="font-technical-mono-sm text-technical-mono-sm text-muted truncate">
                127.0.0.1:8787
              </p>
            </div>
          </div>
        </div>
      </aside>

      <div
        className="h-screen overflow-hidden flex flex-col"
        style={{ marginLeft: NAV_W }}
      >
        {booting && inTauri && (
          <div className="shrink-0 border-b border-border bg-surface-container-low px-lg py-sm">
            <p className="font-body-sm text-body-sm text-muted">
              Starting built-in Core…
            </p>
          </div>
        )}
        {showBanner && (
          <div className="shrink-0 border-b border-border bg-surface-container-low px-lg py-md flex items-start justify-between gap-md">
            <div>
              <p className="font-body-md text-body-md text-on-surface font-medium">
                Core is offline
              </p>
              <p className="font-body-sm text-body-sm text-muted mt-1">
                {inTauri ? (
                  <>
                    The desktop app could not reach Core on{" "}
                    <code className="font-technical-mono-sm text-technical-mono-sm text-primary">
                      127.0.0.1:8787
                    </code>
                    . Click Retry to restart the built-in Core. Logs:{" "}
                    <code className="font-technical-mono-sm text-technical-mono-sm">
                      ~/.mycelium/logs/
                    </code>
                  </>
                ) : (
                  <>
                    Browser preview needs Core running. Open the{" "}
                    <strong className="font-medium text-on-surface">
                      Mycelium desktop app
                    </strong>{" "}
                    (starts Core automatically), or from the repo:{" "}
                    <code className="font-technical-mono-sm text-technical-mono-sm text-primary">
                      ./scripts/run-core.sh
                    </code>
                  </>
                )}
              </p>
            </div>
            <div className="flex gap-sm shrink-0">
              <button
                type="button"
                onClick={() => void onRetry()}
                className="px-md h-9 rounded-lg bg-primary text-on-primary font-label-md text-label-md"
              >
                {retrying ? "Starting…" : "Retry"}
              </button>
              <Link
                to="/settings"
                className="px-md h-9 rounded-lg border border-border bg-surface-container font-label-md text-label-md flex items-center"
              >
                Settings
              </Link>
            </div>
          </div>
        )}
        <div className="flex-1 min-h-0 overflow-hidden">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
