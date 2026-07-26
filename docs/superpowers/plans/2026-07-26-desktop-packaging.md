# Desktop Packaging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship downloadable macOS + Windows Mycelium Desktop apps with a bundled Core sidecar that starts on launch.

**Architecture:** Tauri 2 hosts the React UI; PyInstaller builds `mycelium-core` as a sidecar spawned/killed by the shell. CI builds both OS artifacts for GitHub Releases. Unsigned with signing stubs.

**Tech Stack:** Tauri 2, Rust, Vite/React, PyInstaller, GitHub Actions

## Global Constraints

- Platforms: macOS + Windows
- Core: bundled PyInstaller sidecar on `127.0.0.1:8787`
- Signing: unsigned now; config stubs for later
- Data: `~/.mycelium/` unchanged
- Dev path `./scripts/dev.sh` remains Vite + venv Core

---

### Task 1: API base URL works in Tauri (no Vite proxy)

**Files:**
- Modify: `apps/desktop/src/api/client.ts`
- Modify: `apps/desktop/vite.config.ts` (ensure `clearScreen: false`, `envPrefix` if needed)
- Modify: `services/core/src/mycelium/adapters/http/app.py` (CORS for Tauri origins)

- [ ] Point production/Tauri builds at `http://127.0.0.1:8787` when `VITE_CORE_URL` set or when `window.__TAURI_INTERNALS__` present
- [ ] Allow CORS origins: `tauri://localhost`, `https://tauri.localhost`, `http://localhost:5173`, `http://127.0.0.1:5173`, `http://localhost:4173`, `http://127.0.0.1:4173`

---

### Task 2: PyInstaller Core sidecar

**Files:**
- Create: `services/core/packaging/mycelium-core.spec`
- Create: `services/core/packaging/sidecar_entry.py` (calls `core_main`)
- Create: `scripts/build-core-sidecar.sh`

- [ ] Spec builds onedir binary named `mycelium-core` / `mycelium-core.exe`
- [ ] Script installs pyinstaller in venv, runs spec, copies to `apps/desktop/src-tauri/binaries/mycelium-core-{target-triple}`

---

### Task 3: Tauri 2 project + sidecar lifecycle

**Files:**
- Create: `apps/desktop/src-tauri/**` (Cargo.toml, tauri.conf.json, src/lib.rs, src/main.rs, capabilities, icons)
- Modify: `apps/desktop/package.json` (tauri deps + scripts)
- Replace: `apps/desktop/src-tauri/README.md`

- [ ] Install Rust via rustup if missing
- [ ] Init Tauri; configure productName Mycelium, identifier `dev.mycelium.app`
- [ ] ExternalBin sidecar; spawn on setup if health fails; kill on Exit if we started it
- [ ] Bundle targets: dmg (mac), nsis (win)
- [ ] Signing fields present but empty/env-based

---

### Task 4: package-desktop.sh + docs + CI

**Files:**
- Create: `scripts/package-desktop.sh`
- Create: `docs/DESKTOP-INSTALL.md`
- Create: `.github/workflows/release-desktop.yml`
- Modify: `README.md` (Download Desktop section)
- Modify: `apps/desktop/README.md`

- [ ] One-command local package on macOS
- [ ] CI: macos-latest + windows-latest on `v*` tags / workflow_dispatch
- [ ] Document Gatekeeper/SmartScreen

---

### Task 5: Verify local macOS package

- [ ] Run `./scripts/package-desktop.sh`
- [ ] Confirm `.app`/`.dmg` exists under bundle/
- [ ] Smoke: launch app or at least confirm sidecar binary runs `--help`/`health`

## Spec coverage

| Spec item | Task |
|---|---|
| Bundled Core sidecar lifecycle | 3 |
| macOS + Windows artifacts | 3, 4 |
| Unsigned + signing stubs | 3, 4 |
| First-run / docs / Releases | 4 |
| API without Vite proxy | 1 |
| Local package script | 4, 5 |
