# Desktop packaging design — Tauri + Core sidecar

**Date:** 2026-07-26  
**Status:** Approved (conversation) — pending user review of this file  
**Goal:** Downloadable macOS + Windows desktop app that works on first open without Python/Node/repo setup.

## Decisions (locked)

| Topic | Choice |
|---|---|
| Platforms | macOS + Windows |
| Core delivery | Bundled PyInstaller sidecar |
| Signing | Unsigned now; Tauri signing config stubs for later |
| Shell | Tauri 2 (Approach A) |

## §1 — Runtime shape

### Artifacts

- **macOS:** `Mycelium.app` in a `.dmg` (unsigned → right-click → Open once).
- **Windows:** NSIS installer `.exe` (unsigned → SmartScreen → More info → Run anyway).

### Bundle contents

- Tauri shell hosts the existing React Desktop UI (no browser, no Vite server in production).
- **Sidecar:** `mycelium-core` (PyInstaller) — same FastAPI app as `mycelium serve`, binds `127.0.0.1:8787`.
- User data remains at `~/.mycelium/` (vault, indexes, logs).

### Lifecycle

1. App launch → if `/health` is not OK, spawn the bundled sidecar.
2. Poll until healthy, or show existing Core offline banner + Retry.
3. App quit → stop only the sidecar **this app started** (do not kill an externally started Core).

### Out of scope (v0.1 packaging)

- Vendoring embedding model weights (first Index may download once).
- MCP / VS Code VSIX packaging.
- Apple notarization / Windows Authenticode (stubs only).

## §2 — Build pipeline & repo layout

### Paths

```text
apps/desktop/
  src-tauri/                      # Tauri 2 project (replaces README stub)
  package.json                    # + tauri scripts / deps
scripts/
  build-core-sidecar.sh           # PyInstaller → mycelium-core(.exe)
  package-desktop.sh              # UI + sidecar + tauri build
.github/workflows/
  release-desktop.yml             # macOS + Windows → GitHub Releases
services/core/
  packaging/mycelium-core.spec    # PyInstaller spec
docs/
  DESKTOP-INSTALL.md              # End-user install / Gatekeeper notes
```

### Local build (macOS Apple Silicon)

```bash
./scripts/package-desktop.sh
# → apps/desktop/src-tauri/target/release/bundle/…
```

### CI

- `macos-latest`: build Core sidecar + Tauri → upload `.dmg`
- `windows-latest`: build Core sidecar + Tauri → upload `.exe`
- Trigger: tag `v*` or `workflow_dispatch`
- Attach artifacts to the GitHub Release for that tag

### Signing hooks

- Document env vars / `tauri.conf.json` fields for Apple identity and Windows cert.
- Leave unset so unsigned builds succeed.

### Dev path unchanged

- `./scripts/dev.sh` continues to use Vite + venv Core.
- Sidecar lifecycle applies to packaged builds and `tauri dev` only.

## §3 — First-run UX & download story

### Happy path

1. Install from GitHub Releases (`.dmg` / `.exe`).
2. Open Mycelium → sidecar starts → `/health` OK within a few seconds.
3. Library loads; add workspace + Index with no terminal / Python / Node.

### Failure path

- Existing offline banner (Retry + Settings).
- Retry re-spawns sidecar if the app owns the process.
- Point to `~/.mycelium/logs/` for diagnosis.

### Docs

- `docs/DESKTOP-INSTALL.md`: unsigned OS friction (macOS Gatekeeper, Windows SmartScreen).
- README: **Download Desktop** section above clone/dev contributor path; link to latest Release.

### Success criteria

On a machine without this repo or a venv: install artifact → open app → Library loads with Core healthy (or clear recoverable banner). No `pip` / `npm` required.

## Non-goals / known caveats

- Embedding model may still require network on first Index until vendored in a later release.
- Cross-compiling Windows from macOS is not supported; Windows artifacts come from CI (or a Windows host).
- Unsigned binaries will show OS warnings; expected until signing certs are added.

## Spec self-review

- [x] No unresolved placeholders (TODO/TBD left only as intentional “later signing”).
- [x] Consistent with PRD FR-14 (Desktop shell runs Core).
- [x] Scope bounded: packaging + lifecycle; not MCP/VSIX/model vendoring.
- [x] CI explicitly covers Windows (cannot build Windows installer on this Mac alone).
