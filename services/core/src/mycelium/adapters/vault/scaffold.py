"""Default Thinking Vault layout — inspired by kepano-obsidian + obsidian-mind.

Folders group by purpose; wikilinks group by meaning.
Idempotent: never overwrites existing notes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Bucket paths (posix). Nested dirs get their own `_index.md`.
BUCKETS: tuple[str, ...] = (
    "brain",
    "work",
    "work/active",
    "work/archive",
    "work/decisions",
    "notes",
    "daily",
    "reference",
    "thinking",
    "templates",
    "clippings",
    "attachments",
)

# Seed notes: relative path → (title, body). Skip if file already exists.
SEED_NOTES: dict[str, tuple[str, str]] = {
    "Home.md": (
        "Home",
        """\
Vault entry point (MOC). Inspired by [obsidian-mind](https://github.com/breferrari/obsidian-mind)
and [kepano-obsidian](https://github.com/kepano/kepano-obsidian).

## Buckets

- [[brain/_index|brain]] — goals, decisions, patterns, gotchas (agent session context)
- [[work/_index|work]] — active projects, archive, ADRs
- [[notes/_index|notes]] — evergreen atomic notes
- [[daily/_index|daily]] — day logs
- [[reference/_index|reference]] — codebase / architecture maps
- [[thinking/_index|thinking]] — scratch; promote then delete
- [[templates/_index|templates]] — note starters
- [[clippings/_index|clippings]] — captures from the web / chats
- [[attachments/_index|attachments]] — binary / media files

## Agent rules

See [[AGENTS]] for where to file durable knowledge.
""",
    ),
    "AGENTS.md": (
        "AGENTS",
        """\
# Vault filing rules (for AI agents)

Folders group by **purpose**. Links group by **meaning**. A note lives in one folder; link outward with `[[wikilinks]]`.

## Where to write

| Kind | Bucket | Notes |
|---|---|---|
| Goals / focus | `brain/` | Keep [[brain/North Star]] current |
| Durable decision / ADR | `work/decisions/` | Link symbols with `path#symbol` |
| Active project | `work/active/` | 1–3 at a time |
| Finished project | `work/archive/` | Move when done |
| Evergreen concept | `notes/` | Atomic; link to code + decisions |
| Day log | `daily/` | Optional; YYYY-MM-DD.md |
| Codebase map / architecture | `reference/` | Stable how-it-works docs |
| Scratch / draft | `thinking/` | Promote findings, then delete |
| Web / chat capture | `clippings/` | Raw capture before refining |
| Templates only | `templates/` | Do not store living notes here |

## Write policy

- Write **durable** knowledge (survives next week), not every chat turn.
- Prefer updating an existing note over creating duplicates — check tree/pack first.
- Always add `[[wikilinks]]` to related notes and code symbols.
- Update the bucket `_index.md` when you add a major note.
""",
    ),
    "brain/_index.md": (
        "Brain",
        "Session-critical second brain: North Star, decisions index, patterns, gotchas.\n\n"
        "See [[brain/North Star]], [[brain/Key Decisions]], [[brain/Patterns]], [[brain/Gotchas]].\n",
    ),
    "brain/North Star.md": (
        "North Star",
        "Goals and focus areas — agents should read this when starting meaningful work.\n\n"
        "## Now\n\n- \n\n## Later\n\n- \n",
    ),
    "brain/Key Decisions.md": (
        "Key Decisions",
        "Index of significant decisions. Link each to a note under `work/decisions/`.\n\n"
        "## Decisions\n\n- \n",
    ),
    "brain/Patterns.md": (
        "Patterns",
        "Recurring patterns across the codebase and process.\n\n## Patterns\n\n- \n",
    ),
    "brain/Gotchas.md": (
        "Gotchas",
        "Things that went wrong and why — landmines for future agents.\n\n## Gotchas\n\n- \n",
    ),
    "work/_index.md": (
        "Work",
        "Project execution.\n\n"
        "- [[work/active/_index|active]] — current work\n"
        "- [[work/archive/_index|archive]] — completed\n"
        "- [[work/decisions/_index|decisions]] — ADRs\n",
    ),
    "work/active/_index.md": (
        "Active work",
        "Current projects (keep to 1–3). Link to code symbols and decisions.\n",
    ),
    "work/archive/_index.md": (
        "Archive",
        "Completed projects. Prefer `work/archive/YYYY/` when it grows.\n",
    ),
    "work/decisions/_index.md": (
        "Decisions",
        "Architecture / product decision records. Template: [[templates/Decision Record]].\n",
    ),
    "notes/_index.md": (
        "Notes",
        "Evergreen atomic notes (kepano-style Notes). One idea per note; link heavily.\n",
    ),
    "daily/_index.md": (
        "Daily",
        "Day logs — `YYYY-MM-DD.md`. Optional; promote lasting items into notes/decisions.\n",
    ),
    "reference/_index.md": (
        "Reference",
        "Stable codebase knowledge, architecture maps, flow docs.\n",
    ),
    "thinking/_index.md": (
        "Thinking",
        "Scratchpad. Promote findings to notes/decisions/reference, then delete drafts.\n",
    ),
    "templates/_index.md": (
        "Templates",
        "Note starters. Copy into the right bucket; do not keep living content here.\n",
    ),
    "templates/Decision Record.md": (
        "Decision Record",
        "**Status:** proposed | accepted | deprecated\n\n"
        "**Context:**\n\n\n"
        "**Decision:**\n\n\n"
        "**Consequences:**\n\n\n"
        "**Links:**\n\n- \n",
    ),
    "templates/Work Note.md": (
        "Work Note",
        "**Status:** active | blocked | done\n\n"
        "**Goal:**\n\n\n"
        "**Next:**\n\n\n"
        "**Links:**\n\n- \n",
    ),
    "templates/Thinking Note.md": (
        "Thinking Note",
        "Scratch — promote then delete.\n\n**Context:**\n\n\n**Findings:**\n\n\n",
    ),
    "clippings/_index.md": (
        "Clippings",
        "Raw captures (kepano Clippings). Refine into notes/reference later.\n",
    ),
    "attachments/_index.md": (
        "Attachments",
        "Binary / media attachments for notes.\n",
    ),
}


def scaffold_vault(vault_dir: Path) -> dict[str, Any]:
    """
    Create the default Mycelium vault layout if missing.

    Returns counts of created folders/notes (existing files untouched).
    """
    root = vault_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)

    folders_created = 0
    for bucket in BUCKETS:
        path = root / bucket
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            folders_created += 1
        else:
            path.mkdir(parents=True, exist_ok=True)

    notes_created = 0
    for rel, (title, body) in SEED_NOTES.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            continue
        content = body.lstrip()
        if not content.startswith("# "):
            content = f"# {title}\n\n{content}"
        if not content.endswith("\n"):
            content += "\n"
        path.write_text(content, encoding="utf-8")
        notes_created += 1

    return {
        "vault": str(root),
        "folders_created": folders_created,
        "notes_created": notes_created,
        "buckets": list(BUCKETS),
        "layout": "mycelium-kepano-obsidian-mind-v1",
    }
