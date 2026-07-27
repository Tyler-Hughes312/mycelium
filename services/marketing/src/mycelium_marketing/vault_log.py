from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from mycelium_marketing.paths import vault_marketing_engine


def append_engine_log(line: str) -> None:
    path = vault_marketing_engine()
    if not path.exists():
        return
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    row = f"| {stamp} | {line} | auto |\n"
    text = path.read_text(encoding="utf-8")
    marker = "## Log"
    if marker not in text:
        text = text.rstrip() + f"\n\n{marker}\n\n| Date | Action | Result |\n|------|--------|--------|\n"
    # append after table header block — simplest: append at end
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text + row, encoding="utf-8")
