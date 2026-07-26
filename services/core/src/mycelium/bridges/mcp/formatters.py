"""Compact Context Packet formatting for agent context windows."""

from __future__ import annotations

from typing import Any


def _snip(text: str, limit: int = 180) -> str:
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def compact_results(results: list[dict[str, Any]], *, max_items: int = 8) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in results[:max_items]:
        out.append(
            {
                "kind": row.get("kind"),
                "title": row.get("title"),
                "path": row.get("path"),
                "score": row.get("score"),
                "snippet": _snip(str(row.get("snippet") or "")),
                "id": row.get("id"),
                "workspace_name": row.get("workspace_name"),
                "workspace_id": row.get("workspace_id"),
            }
        )
    return out


def format_packet(label: str, packet: dict[str, Any]) -> str:
    """Human/agent-readable compact packet (not raw JSON dump)."""
    results = compact_results(list(packet.get("results") or []))
    lines = [
        f"# {label}",
        f"count={packet.get('count', len(results))} mode={packet.get('mode', '')}",
    ]
    if packet.get("scope") == "all_workspaces":
        n = len(packet.get("workspace_ids") or [])
        lines.append(f"scope=all_workspaces ({n} repos)")
    if packet.get("reason"):
        lines.append(f"reason={packet['reason']}: {packet.get('message', '')}")
    if not results:
        lines.append("(no results)")
        return "\n".join(lines)
    for i, row in enumerate(results, start=1):
        repo = row.get("workspace_name")
        prefix = f"@{repo} " if repo else ""
        lines.append(
            f"{i}. {prefix}[{row.get('kind')}] {row.get('title')} — {row.get('path')}"
        )
        if row.get("snippet"):
            lines.append(f"   {row['snippet']}")
    return "\n".join(lines)


def format_note(note: dict[str, Any], *, body_limit: int = 2000) -> str:
    body = str(note.get("body") or "")
    if len(body) > body_limit:
        body = body[: body_limit - 1] + "…"
    unresolved = note.get("unresolved_links") or []
    lines = [
        f"# Note: {note.get('title')}",
        f"id={note.get('id')} path={note.get('path')}",
        f"abs={note.get('abs_path', '')}",
        "",
        body,
    ]
    if unresolved:
        lines.append("")
        lines.append("unresolved: " + ", ".join(u.get("target", "") for u in unresolved))
    return "\n".join(lines)


def format_commits(commits: list[dict[str, Any]], *, path_filter: str) -> str:
    lines = [f"# Commits touching `{path_filter}`", f"count={len(commits)}"]
    if not commits:
        lines.append("(none)")
        return "\n".join(lines)
    for c in commits[:20]:
        sha = str(c.get("hash") or "")[:7]
        msg = _snip(str(c.get("message") or ""), 120)
        lines.append(f"- {sha} {msg}")
        paths = list(c.get("changed_paths") or [])[:8]
        if paths:
            lines.append("  files: " + ", ".join(str(p) for p in paths))
    return "\n".join(lines)


def resolve_workspace_id(
    workspaces: list[dict[str, Any]],
    *,
    workspace_id: str | None = None,
    workspace_path: str | None = None,
    default_all: bool = False,
) -> str:
    """Return a workspace id, or '*' when searching all repos.

    When default_all is True and no id/path is given with multiple workspaces,
    returns '*' so agents can reuse code across old repos without picking one.
    """
    if workspace_id and workspace_id.strip() in {"*", "all"}:
        return "*"
    if workspace_id:
        for w in workspaces:
            if w.get("id") == workspace_id:
                return str(w["id"])
        raise ValueError(f"Unknown workspace_id: {workspace_id}")
    if workspace_path:
        needle = workspace_path.rstrip("/")
        for w in workspaces:
            wp = str(w.get("path") or "").rstrip("/")
            if wp == needle or needle.startswith(wp + "/") or wp.endswith(needle):
                return str(w["id"])
        raise ValueError(f"No registered workspace matching path: {workspace_path}")
    if len(workspaces) == 1:
        return str(workspaces[0]["id"])
    if not workspaces:
        raise ValueError("No workspaces registered. Add one in Mycelium Desktop Library.")
    if default_all:
        return "*"
    names = ", ".join(f"{w.get('name')}({w.get('id')})" for w in workspaces[:8])
    raise ValueError(
        "Multiple workspaces — pass workspace_id, workspace_path, or '*' for all. "
        f"Available: {names}"
    )
