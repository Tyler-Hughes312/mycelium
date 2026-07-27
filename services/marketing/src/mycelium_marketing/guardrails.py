from __future__ import annotations

import re
from dataclasses import dataclass


DISCLOSURE_HINTS = (
    "i'm the author",
    "i am the author",
    "maker here",
    "i built",
    "i made",
    "author here",
    "disclose",
)


BANNED_PHRASES = (
    "chat memory vault",
    "we remember your chats",
    "remembers your conversations and sells",
)

# Negations that make the phrase safe (contrastive positioning)
SAFE_NEGATION = re.compile(
    r"\b(not|never|isn't|is not|no longer)\b[^.!?\n]{0,40}\bchat memory vault\b"
    r"|\bchat memory vault\b[^.!?\n]{0,40}\b(not|never)\b",
    re.IGNORECASE,
)


PERCENT_CLAIM = re.compile(
    r"(?<!illustrative\s)(?<!labeled\s)(\d{2,3})\s*%\s*(token|tokens|saving|savings|less)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class GuardResult:
    ok: bool
    errors: list[str]


def check_content(text: str, *, require_disclosure: bool = False) -> GuardResult:
    errors: list[str] = []
    lower = text.lower()
    for phrase in BANNED_PHRASES:
        if phrase not in lower:
            continue
        if phrase == "chat memory vault" and SAFE_NEGATION.search(text):
            continue
        errors.append(f"banned positioning phrase: {phrase!r}")
    # Allow if "illustrative" appears near percent claims
    for m in PERCENT_CLAIM.finditer(text):
        window = text[max(0, m.start() - 40) : m.end() + 40].lower()
        if "illustrative" not in window and "labeled" not in window:
            errors.append(f"unlabeled percent claim near: {m.group(0)!r}")
    if require_disclosure:
        if not any(h in lower for h in DISCLOSURE_HINTS):
            errors.append("reddit post missing author/maker disclosure")
    return GuardResult(ok=not errors, errors=errors)


def assert_autopilot_allowed(*, i_understand: bool, env_flag: str | None) -> GuardResult:
    if i_understand or (env_flag or "").strip() == "1":
        return GuardResult(ok=True, errors=[])
    return GuardResult(
        ok=False,
        errors=["run requires --i-understand or MARKETING_AUTOPILOT=1"],
    )
