# Install Mycelium Desktop

Download **0.1.3** from:
https://github.com/Tyler-Hughes312/mycelium/releases/tag/v0.1.3-desktop

| Platform | Asset |
|---|---|
| macOS (Apple Silicon) | [`Mycelium_0.1.3_aarch64.dmg`](https://github.com/Tyler-Hughes312/mycelium/releases/download/v0.1.3-desktop/Mycelium_0.1.3_aarch64.dmg) |
| Windows (x64) | [`Mycelium_0.1.3_x64-setup.exe`](https://github.com/Tyler-Hughes312/mycelium/releases/download/v0.1.3-desktop/Mycelium_0.1.3_x64-setup.exe) |

## First launch

1. Install / open the app.
2. Core starts automatically inside the app (binds `127.0.0.1:8787`).
3. On first run, Core **scaffolds the Thinking Vault** at `~/.mycelium/vault/` (`Home.md`, `brain/`, `work/`, …). Browse it under **Vault** in the app — no manual folder setup.
4. You should land on **Library**. Add a workspace and Index — no Python or Node required for Desktop alone.

Data and logs live in `~/.mycelium/` (vault, indexes, logs).

## Next: coding agents + vault (easy)

Desktop alone indexes and searches in the UI. To give **Cursor / VS Code / Codex / Claude / Windsurf** the same context (and vault read/write tools), follow the three-step guide:

**[GETTING-STARTED.md](GETTING-STARTED.md)** — Desktop → `./scripts/install.sh` wires MCP into your agents → vault already waiting under `~/.mycelium/vault`.

## Unsigned builds (current)

Releases are **not code-signed** yet. OS warnings are expected:

### macOS Gatekeeper

1. Open the `.dmg` and drag Mycelium to Applications (or run from the disk image).
2. If macOS blocks the app: **Right-click Mycelium → Open → Open**.
3. After the first Open, subsequent launches work normally.

### Windows SmartScreen

1. Run the installer.
2. If SmartScreen appears: **More info → Run anyway**.

## Recovery

If the UI shows **Core is offline**:

1. Click **Retry** (re-spawns the bundled Core).
2. Check `~/.mycelium/logs/`.
3. Confirm nothing else is bound to port `8787`, or stop the other process.

## Signing (later)

Apple Developer ID and Windows Authenticode can be plugged into `apps/desktop/src-tauri/tauri.conf.json` (`bundle.macOS.signingIdentity`, `bundle.windows.certificateThumbprint`) without changing app behavior.
