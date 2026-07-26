"""Tests for RAG kind boost / intent (soft note demotion)."""

from __future__ import annotations

from mycelium.core.domain.node_types import intent_kinds, kind_boost


def test_default_query_demotes_notes_vs_code() -> None:
    intents = intent_kinds("how does workspace registration work?")
    assert "Note" not in intents
    assert kind_boost("Note", intents) == 0.55
    assert kind_boost("Function", intents) == 1.0
    assert kind_boost("File", intents) == 1.0


def test_note_intent_boosts_notes() -> None:
    for query in (
        "vault decision about local-first",
        "why we chose hexagonal architecture",
        "ADR for embedding backend",
        "notes about indexing",
    ):
        intents = intent_kinds(query)
        assert "Note" in intents, query
        assert kind_boost("Note", intents) == 1.35


def test_empty_intents_still_demote_notes() -> None:
    assert kind_boost("Note", set()) == 0.55
    assert kind_boost("Class", set()) == 1.0
