"""Parse Obsidian-style [[wikilinks]] from markdown (FR-12)."""

from __future__ import annotations

import re
from dataclasses import dataclass

# [[target]] or [[target|alias]]
_WIKILINK_RE = re.compile(r"\[\[([^\]]+?)\]\]")


@dataclass(frozen=True)
class Wikilink:
    raw: str
    target: str
    alias: str | None = None

    @property
    def display(self) -> str:
        return self.alias or self.target


def parse_wikilinks(text: str) -> list[Wikilink]:
    found: list[Wikilink] = []
    seen: set[str] = set()
    for match in _WIKILINK_RE.finditer(text or ""):
        raw = match.group(1).strip()
        if not raw or raw in seen:
            continue
        seen.add(raw)
        if "|" in raw:
            target, alias = raw.split("|", 1)
            found.append(Wikilink(raw=raw, target=target.strip(), alias=alias.strip() or None))
        else:
            found.append(Wikilink(raw=raw, target=raw, alias=None))
    return found


def slugify_title(title: str) -> str:
    """Filename stem from a note title."""
    cleaned = re.sub(r"[^\w\s\-./]", "", title.strip(), flags=re.UNICODE)
    cleaned = re.sub(r"[\s/]+", "-", cleaned).strip("-._")
    return cleaned.lower() or "untitled"
