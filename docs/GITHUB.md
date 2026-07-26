# Connect GitHub (optional)

Import repos into Mycelium Library so Search can reuse old code across projects.

## Quick path: Personal Access Token

1. GitHub → **Settings → Developer settings → Personal access tokens**
2. Create a token with at least **repo** (private) or public repo read
3. Mycelium Desktop → **Settings → GitHub** → paste PAT → **Save token**
4. **Library → Import from GitHub** → Import → **Index**

Token file: `~/.mycelium/secrets/github_token` (mode 600). Never committed.

## Device OAuth (optional)

1. Create an OAuth App at [GitHub Developer settings](https://github.com/settings/developers)
2. Enable **Device Flow**
3. Copy **Client ID** into Settings (or `~/.mycelium/config.toml` `[github] client_id`, or env `MYCELIUM_GITHUB_CLIENT_ID`)
4. Click **Device login** → open the verification URL → enter the code

No client secret is stored in Mycelium (device flow).

## API

| Method | Path |
|---|---|
| GET | `/integrations/github/status` |
| POST | `/integrations/github/device/start` |
| POST | `/integrations/github/device/poll` |
| POST | `/integrations/github/token` |
| DELETE | `/integrations/github` |
| GET | `/integrations/github/repos` |
| POST | `/integrations/github/import` |

Clones land under `~/.mycelium/repos/<owner__name>` by default, then register as workspaces.
