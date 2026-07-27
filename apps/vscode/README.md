# Mycelium VS Code / Cursor extension

Side panel Context Packet + New Note. Talks to local Core at `http://127.0.0.1:8787`.

## Install from `.vsix` (recommended)

```bash
cd apps/vscode
npm install
npm run package          # → mycelium-0.1.5.vsix
code --install-extension mycelium-0.1.5.vsix
# or Cursor: Extensions → … → Install from VSIX
```

Publisher id `mycelium-local` is a placeholder until Marketplace publish.

## Development (F5)

1. Start Core: `./scripts/run-core.sh` (or `./scripts/dev.sh`)
2. Register this repo in Mycelium Desktop **Library** and **Index** it
3. Open `apps/vscode` in VS Code/Cursor → **F5** (Run Extension)
4. Open a source file → Mycelium activity bar → **Context** panel

## Commands

- `Mycelium: Retry Connection`
- `Mycelium: Refresh Context`
- `Mycelium: New Note` — creates a vault note pre-linked to the current symbol/file
- `Mycelium: Open Panel`

## Settings

- `mycelium.coreUrl` — default `http://127.0.0.1:8787`
