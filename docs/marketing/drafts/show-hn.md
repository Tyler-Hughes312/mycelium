# Show HN draft

**Title:**
```
Show HN: Mycelium – local codebase index so AI agents stop burning tokens re-grepping
```

**Body:**
```
I built Mycelium because every Cursor/Claude session I was either pasting huge files or watching the agent grep the same tree again — burning tokens before it answered.

Mycelium is a local-first context layer:
- Indexes symbols, files, and commits on your machine
- Returns tight context packets over MCP to Cursor / Claude
- Optional Thinking Vault for ADRs / decisions (not a chat diary)
- Desktop app bundles Core; privacy default is localhost

This is deliberately not another “agent memory vault.” Those remember conversations. Mycelium retrieves from project structure so agents spend context on the answer, not the haystack.

Site: https://getmycelium.vercel.app
Repo: https://github.com/Tyler-Hughes312/mycelium
Desktop: releases (v0.1.3) — or ./scripts/dev.sh for source

Quick dogfood: install → Library → add fixtures/dogfood-rate-limits → Index → ask MCP “how did we handle rate limits”.

Happy to answer questions about indexing, MCP setup, or the token-efficiency angle. Illustrative “% tokens saved” on the site is labeled illustrative until we publish live Impact dogfood numbers.
```

**When:** Tue/Wed ~9:00 AM ET. Reply to every comment for 2 hours.
