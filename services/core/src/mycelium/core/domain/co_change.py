"""Derive co_changed edges from commits + symbols (FR-7)."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from mycelium.adapters.git.history import CommitRecord
from mycelium.adapters.parse.symbols import SymbolRecord

MAX_PAIRS_PER_COMMIT = 200


def build_co_changed_edges(
    commits: list[CommitRecord],
    symbols: list[SymbolRecord],
) -> list[dict[str, Any]]:
    """
    When two Symbols' files change in the same Commit, link them with co_changed.
    Edge identity is unordered + content-addressed (AD-7).
    """
    by_path: dict[str, list[SymbolRecord]] = defaultdict(list)
    for sym in symbols:
        by_path[sym.path].append(sym)

    edges: dict[str, dict[str, Any]] = {}

    for commit in commits:
        changed = {_norm(p) for p in commit.changed_paths}
        involved: list[SymbolRecord] = []
        for path in changed:
            involved.extend(by_path.get(path, []))
        if len(involved) < 2:
            continue

        pairs = _select_pairs(involved, by_path, changed)
        for left, right in pairs:
            a, b = sorted(
                (left, right),
                key=lambda s: (s.path, s.name, s.start_line),
            )
            edge_id = f"co_changed:{a.node_id}:{b.node_id}"
            edges[edge_id] = {
                "id": edge_id,
                "kind": "Edge",
                "edge_kind": "co_changed",
                "source_id": a.node_id,
                "target_id": b.node_id,
                "commit_hash": commit.hash,
                "source_name": a.name,
                "target_name": b.name,
                "source_path": a.path,
                "target_path": b.path,
            }

    return list(edges.values())


def _norm(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def _select_pairs(
    involved: list[SymbolRecord],
    by_path: dict[str, list[SymbolRecord]],
    changed: set[str],
) -> list[tuple[SymbolRecord, SymbolRecord]]:
    pairs: list[tuple[SymbolRecord, SymbolRecord]] = []

    # Prefer same-file pairs (denser signal, fewer explosions).
    for path in sorted(changed):
        syms = by_path.get(path, [])
        for i, left in enumerate(syms):
            for right in syms[i + 1 :]:
                pairs.append((left, right))
                if len(pairs) >= MAX_PAIRS_PER_COMMIT:
                    return pairs

    # Then cross-file pairs among remaining involved symbols.
    for i, left in enumerate(involved):
        for right in involved[i + 1 :]:
            if left.path == right.path:
                continue
            pairs.append((left, right))
            if len(pairs) >= MAX_PAIRS_PER_COMMIT:
                return pairs

    return pairs
