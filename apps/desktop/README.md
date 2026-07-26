# Mycelium Desktop

Local Vite + React console for the Mycelium Context Layer (Library, Index, Search, Vault, Settings).

Talks to Core at `http://127.0.0.1:8787`.

## Packaged app (downloadable)

```bash
# From repo root (needs Rust via rustup + project venv)
./scripts/package-desktop.sh
```

Produces `.dmg` / `.app` (macOS) under `src-tauri/target/release/bundle/`.  
Windows installers are built on `windows-latest` via `.github/workflows/release-desktop.yml`.

End-user install: [docs/DESKTOP-INSTALL.md](../../docs/DESKTOP-INSTALL.md).

## Development (web)

```bash
npm install
npm run dev          # http://localhost:5173 — Core via Vite /api proxy
```

Core must be running (`./scripts/run-core.sh` or `./scripts/dev.sh`).

## Native shell (Tauri)

```bash
./scripts/build-core-sidecar.sh   # once (or after Core changes)
npm run tauri:dev                 # spawns bundled Core if port 8787 is free
npm run tauri:build               # production bundle
```

## Scripts

| Command | Purpose |
|---|---|
| `npm run dev` | Vite HMR |
| `npm run build` | Typecheck + production bundle → `dist/` |
| `npm run lint` | Oxlint |
| `npm run preview` | Serve `dist/` |
| `npm run tauri:dev` | Native window + Core sidecar lifecycle |
| `npm run tauri:build` | Installable Desktop artifacts |
