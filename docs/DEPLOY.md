# Deploy / operate Mycelium (local product)

Runbook for the **0.1.0** local-first install. Not cloud hosting.

## Artifacts

| Artifact | How to get it |
|---|---|
| Core + MCP | `pip install -e "services/core[dev]"` → `mycelium`, `mycelium-core`, `mycelium-mcp` on PATH |
| Desktop | `apps/desktop` → `npm run build` / `./scripts/run-desktop.sh` |
| VS Code extension | `apps/vscode` → `npm run package` → `*.vsix` |

## Install (fresh machine)

```bash
git clone <repo> && cd MemoryOptimization
./scripts/install.sh
```

Creates `venv/`, installs Core editable, Desktop + extension deps, dogfood fixture, Cursor MCP rule.

## Upgrade

```bash
git pull
./scripts/install.sh          # reinstall editable Core + npm deps
# or: ./venv/bin/pip install -e "services/core[dev]"
```

Config lives in `~/.mycelium/config.toml` (`config_version` migrates on load). Data/vault are preserved.

## Uninstall

```bash
# Stop Core / Desktop
rm -rf /path/to/MemoryOptimization/venv
# Optional — removes vault + indexes:
rm -rf ~/.mycelium
# VS Code: uninstall Mycelium extension / remove .vsix install
```

## Run (production-style)

```bash
./scripts/run-core.sh          # no --reload; logs → stderr + ~/.mycelium/logs/
./scripts/run-desktop.sh       # vite preview on :4173
# or day-to-day: ./scripts/dev.sh  (reload + Vite :5173)
```

Health: `curl -s http://127.0.0.1:8787/health`

## MCP (all IDEs / agents)

Friendly path (Desktop + vault + agents): **[GETTING-STARTED.md](GETTING-STARTED.md)**.  
Client matrix: **[MCP-CLIENTS.md](MCP-CLIENTS.md)** (Cursor, VS Code + Copilot, Codex, Claude Code, Claude Desktop, Windsurf).

After `./scripts/install.sh`, Mycelium is merged into user configs automatically. Core must be on `127.0.0.1:8787` (vault scaffolds on first Core start).

PATH-based binary (any client):

```json
{
  "command": "mycelium-mcp",
  "env": { "MYCELIUM_CORE_URL": "http://127.0.0.1:8787" }
}
```

If the IDE does not inherit your shell PATH, use the absolute `…/venv/bin/mycelium-mcp`.

No `PYTHONPATH` required.

## VS Code `.vsix`

```bash
cd apps/vscode && npm install && npm run package
code --install-extension mycelium-*.vsix
```

Marketplace publish is a maintainer step (publisher id in `package.json`).

## Privacy / ops knobs

| Setting | Default | Notes |
|---|---|---|
| `allow_code_upload` | false | Guard helpers block remote upload until enabled |
| `allow_remote_llm` | false | Same for remote LLM |
| `server.api_token` | `""` | When set, require `Authorization: Bearer …` (except `/health`) |
| bind | `127.0.0.1:8787` | Do not expose publicly without understanding the risk |

## Release gate

```bash
./scripts/release-check.sh
```

Runs Core pytest, Desktop lint+build, VS Code compile + vsce package.

## Out of scope (v1.1+)

- Tauri `.dmg` / sidecar (needs Rust toolchain)
- Windows installers
- PyPI / Marketplace credentials & publish
- Multi-tenant cloud
