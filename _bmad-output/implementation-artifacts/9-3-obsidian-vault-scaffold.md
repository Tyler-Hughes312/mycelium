# Story 9.3: Obsidian-inspired vault scaffold

Status: done

## Delivered

- Default layout from kepano-obsidian + obsidian-mind: Home, AGENTS, brain/, work/, notes/, daily/, reference/, thinking/, templates/, clippings/, attachments/
- `scaffold_vault()` on `ensure_local_layout` + `POST /vault/scaffold` + `mycelium_vault_scaffold`
- Idempotent (never overwrites); agent filing rules in vault `AGENTS.md`
