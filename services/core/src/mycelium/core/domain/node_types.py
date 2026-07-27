"""Canonical node kinds for Graph / RAG provenance."""

from __future__ import annotations

import re
from typing import Any

# Coarse families used for fusion / filters
FAMILIES = frozenset({"Symbol", "Commit", "File", "Note", "Thread"})

# Fine display kinds shown in Context Packets / UI chips
DISPLAY_KINDS = frozenset(
    {
        "Function",
        "Method",
        "Class",
        "Type",
        "Const",
        "Symbol",
        "File",
        "Commit",
        "Note",
        "ThreadChunk",
    }
)

_SYMBOL_KIND_MAP = {
    "function": "Function",
    "func": "Function",
    "method": "Method",
    "class": "Class",
    "type": "Type",
    "struct": "Type",
    "interface": "Type",
    "const": "Const",
    "constant": "Const",
    "variable": "Const",
    "var": "Const",
    "symbol": "Symbol",
}

_INTENT_PATTERNS: list[tuple[re.Pattern[str], set[str]]] = [
    (re.compile(r"\bcommits?\b|\bgit\b|\bsha\b|\bchangelog\b|\bhistory\b", re.I), {"Commit"}),
    (re.compile(r"\bfiles?\b|\bpath\b|\bmodule\b|\bsource file\b", re.I), {"File"}),
    (re.compile(r"\bfunctions?\b|\bfuncs?\b|\bmethods?\b|\bcallable\b", re.I), {"Function", "Method"}),
    (re.compile(r"\bclasses?\b|\bstructs?\b|\btypes?\b|\binterfaces?\b", re.I), {"Class", "Type"}),
    (
        re.compile(
            r"\bnotes?\b|\bvault\b|\bmarkdown\b|\bdecisions?\b|\bADR\b|\bwhy we\b",
            re.I,
        ),
        {"Note"},
    ),
]

# Soft demotion so code questions prefer Symbols/Files over vault Notes (AD-4).
_NOTE_DEFAULT_MULT = 0.55
_NOTE_INTENT_MULT = 1.35
_OTHER_FAMILY_MULT = 0.82
_MATCH_MULT = 1.35


def display_kind_from_symbol_kind(symbol_kind: str | None) -> str:
    raw = (symbol_kind or "symbol").strip().lower()
    return _SYMBOL_KIND_MAP.get(raw, "Symbol")


def display_kind_for_row(row: dict[str, Any]) -> str:
    """Resolve fine-grained kind from a vector row or node dict."""
    meta = dict(row.get("meta") or {})
    stored = str(row.get("kind") or meta.get("kind") or "")
    if stored in DISPLAY_KINDS:
        return stored
    lower = stored.lower()
    if lower in {"commit"}:
        return "Commit"
    if lower in {"file"}:
        return "File"
    if lower in {"note"}:
        return "Note"
    if lower in {"threadchunk", "thread_chunk"}:
        return "ThreadChunk"
    if lower in {"symbol"}:
        return display_kind_from_symbol_kind(str(meta.get("symbol_kind") or meta.get("kind") or ""))
    mapped = _SYMBOL_KIND_MAP.get(lower)
    if mapped:
        return mapped
    sk = meta.get("symbol_kind") or meta.get("kind")
    if sk:
        return display_kind_from_symbol_kind(str(sk))
    return "Symbol"


def family_of(display_kind: str) -> str:
    if display_kind in {"Commit", "File", "Note"}:
        return display_kind
    if display_kind == "ThreadChunk":
        return "Thread"
    return "Symbol"


def embed_type_prefix(display_kind: str) -> str:
    """Strong type cue at the start of embed text so models separate kinds."""
    labels = {
        "Function": "code function definition",
        "Method": "code class method definition",
        "Class": "code class definition",
        "Type": "code type definition",
        "Const": "code constant binding",
        "Symbol": "code symbol",
        "File": "source file",
        "Commit": "git commit history entry",
        "Note": "markdown vault note",
        "ThreadChunk": "conversation thread chunk",
    }
    return labels.get(display_kind, f"code {display_kind.lower()}")


def intent_kinds(query: str) -> set[str]:
    """Kinds the query language appears to ask for (empty = no preference)."""
    hits: set[str] = set()
    for pattern, kinds in _INTENT_PATTERNS:
        if pattern.search(query):
            hits |= kinds
    return hits


def kind_boost(display_kind: str, intents: set[str]) -> float:
    fam = family_of(display_kind)
    if not intents:
        # Default: prefer live code over vault notes for agent/code questions.
        if fam == "Note":
            return _NOTE_DEFAULT_MULT
        return 1.0
    if display_kind in intents:
        return _MATCH_MULT if fam != "Note" else _NOTE_INTENT_MULT
    # Soft penalty when query clearly asks for another family
    intent_fams = {family_of(k) for k in intents}
    if fam not in intent_fams:
        return _OTHER_FAMILY_MULT
    return 1.0
