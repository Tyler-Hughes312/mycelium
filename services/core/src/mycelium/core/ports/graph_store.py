"""Graph Store port — LanceDB/SQLite adapter implements this later."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class GraphStore(Protocol):
    """Persistence for Nodes, Edges, and vector indexes (AD-3)."""

    def upsert_node(self, node: dict[str, Any]) -> None:
        """Insert or update a graph node."""
        ...

    def upsert_edge(self, edge: dict[str, Any]) -> None:
        """Insert or update a graph edge."""
        ...

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        """Fetch a node by id, or None if missing."""
        ...
