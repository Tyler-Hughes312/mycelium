# Thread reply pack (paste into good existing threads)

Reddit blocks automated posting from this machine. Use these as **comments** on relevant threads (better than cold self-posts). Disclose you’re the author. Don’t spam identical text across 3 threads in 2 minutes.

Open feeds:
- https://www.reddit.com/r/LocalLLaMA/hot/
- https://www.reddit.com/r/cursor/hot/
- https://www.reddit.com/r/ClaudeAI/hot/

Search in each: `MCP`, `context`, `tokens`, `codebase`

---

## A — Someone complains agents re-read / re-grep / burn tokens

```
I'm the author of Mycelium — same pain. I built a local-first codebase index (symbols/files/commits on localhost) that feeds tight packets to Cursor/Claude over MCP so the agent spends context on the answer, not another full-tree grep.

Not a chat-memory vault — those remember conversations; this retrieves from project structure.

Repo: https://github.com/Tyler-Hughes312/mycelium
Site: https://getmycelium.vercel.app

Curious what still burns the most tokens in your setup after indexing.
```

---

## B — MCP / Cursor tooling thread

```
Author here — if you're wiring MCP for coding agents, Mycelium is aimed at the “index the repo once, query precise context” slot rather than dumping files into chat.

Local Core on :8787 → mycelium_search / mycelium_focus over MCP. Desktop optional.

https://github.com/Tyler-Hughes312/mycelium

Happy to answer MCP setup friction if you try it.
```

---

## C — Local-first / privacy / self-hosted AI coding

```
I'm the author — Mycelium stays local by default (indexes on your machine, localhost Core). Optional Thinking Vault is for ADRs/decisions, not a transcript dump.

https://github.com/Tyler-Hughes312/mycelium
https://getmycelium.vercel.app
```

---

## D — “What do you use instead of pasting whole files?”

```
I got tired of paste-the-file / re-grep loops, so I built Mycelium (author). Local index → MCP context packets for Cursor/Claude. Open source + Desktop release.

https://github.com/Tyler-Hughes312/mycelium
```

---

## Show HN (when you have an HN account)

Title + body: `docs/marketing/drafts/show-hn.md`
Submit: https://news.ycombinator.com/submit
