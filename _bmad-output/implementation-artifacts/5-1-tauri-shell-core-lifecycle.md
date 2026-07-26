# Story 5.1: Tauri shell + Core lifecycle

Status: done

## Notes

Rust/`cargo` were not available on the build machine, so the **native Tauri binary** is deferred (`apps/desktop/src-tauri/README.md`). Lifecycle acceptance is met via:

- `./scripts/dev.sh` — starts Core + Desktop together
- AppShell `/health` poll + **Core offline** recovery banner (Retry / Settings)

## AC

- Desktop connects to localhost Core and loads home — **done**
- Core failure shows recovery actions — **done**
