# Tauri shell

Native Mycelium Desktop (Tauri 2). Bundles the React UI and a PyInstaller Core
sidecar under `resources/mycelium-core/`.

## Lifecycle

On launch the shell checks `http://127.0.0.1:8787/health`. If Core is down it
spawns the bundled `mycelium-core` binary. On quit it stops only a Core process
it started.

## Build

```bash
# From repo root
./scripts/build-core-sidecar.sh
cd apps/desktop && npm run tauri:build
# or
./scripts/package-desktop.sh
```

## Signing stubs

`tauri.conf.json` includes `bundle.macOS.signingIdentity` and
`bundle.windows.certificateThumbprint` (null / empty). Set them when you have
Apple / Authenticode credentials — unsigned builds work without them.
