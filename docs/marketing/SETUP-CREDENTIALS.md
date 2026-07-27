# Marketing publisher credentials

Secrets live at `~/.mycelium/marketing/marketing.env` (never commit).

## Reddit (required for autopilot)

1. Log in to Reddit → https://www.reddit.com/prefs/apps
2. Create app → type **script**
3. Copy client id (under app name) + secret
4. Create the env file:

```bash
mkdir -p ~/.mycelium/marketing
cat > ~/.mycelium/marketing/marketing.env <<'EOF'
REDDIT_CLIENT_ID=your_id
REDDIT_CLIENT_SECRET=your_secret
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password
REDDIT_USER_AGENT=mycelium-marketing/0.1 by u/your_username
MARKETING_AUTOPILOT=0
EOF
chmod 600 ~/.mycelium/marketing/marketing.env
```

5. Verify:

```bash
./scripts/marketing-publish.sh status
./scripts/marketing-publish.sh dry-run --wave launch
```

## Hacker News (required for Show HN)

1. Create an account at https://news.ycombinator.com/login (manually, like a human)
2. Capture a session:

```bash
./scripts/marketing-publish.sh login-hn
```

Log in in the Chromium window, then press Enter in the terminal. Session saves to `~/.mycelium/marketing/hn-storage.json`.

Optional: `HN_USERNAME=you` in `marketing.env` for status display.

## Live launch wave

```bash
# Preview
./scripts/marketing-publish.sh dry-run --wave launch

# Live (staggers HN → Reddit by 30/60/90 minutes)
MARKETING_AUTOPILOT=1 ./scripts/marketing-publish.sh run --wave launch --i-understand
```

Dev-only (no sleeps): add `--no-sleep` (still posts live — use carefully).

## Approval queue (PH / awesome-lists)

```bash
./scripts/marketing-publish.sh queue add --kind product-hunt --title "Mycelium"
./scripts/marketing-publish.sh queue list
./scripts/marketing-publish.sh queue approve <id>
```

## Install Python deps

```bash
./venv/bin/pip install -e "services/marketing[dev]"
./venv/bin/playwright install chromium
```
