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
                "snippet": _snip(str(row.get("snippet") or ""), 120),
                "id": row.get("id"),
                "workspace_name": row.get("workspace_name"),
                "workspace_id": row.get("workspace_id"),
            }
        )
    return out


def _with_receipt(text: str, packet: dict[str, Any] | None = None, receipt: dict[str, Any] | None = None) -> str:
    from mycelium.core.domain.context_receipt import format_receipt_line

    r = receipt or (packet or {}).get("receipt")
    line = format_receipt_line(r if isinstance(r, dict) else None)
    if not line:
        return text
    return text.rstrip() + "\n" + line + "\n"


def format_packet(label: str, packet: dict[str, Any]) -> str:
    """Human/agent-readable compact packet (not raw JSON dump)."""
    results = compact_results(list(packet.get("results") or []), max_items=6)
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
        return _with_receipt("\n".join(lines), packet)
    for i, row in enumerate(results, start=1):
        repo = row.get("workspace_name")
        prefix = f"@{repo} " if repo else ""
        lines.append(
            f"{i}. {prefix}[{row.get('kind')}] {row.get('title')} — {row.get('path')}"
        )
        if row.get("snippet"):
            lines.append(f"   {row['snippet']}")
    return _with_receipt("\n".join(lines), packet)


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


def format_bootstrap(
    *,
    workspace: dict[str, Any] | None,
    workspaces: list[dict[str, Any]],
    registered_new: bool,
    index_info: dict[str, Any] | None,
    sync_info: dict[str, Any] | None,
    brain_pack_text: str,
    open_file_sections: list[str],
    receipt: dict[str, Any] | None = None,
) -> str:
    """Session bootstrap — prefs slice + open-file focus only (not a chat journal)."""
    lines = ["# Mycelium session bootstrap", ""]
    if workspace:
        lines.append(
            f"workspace id={workspace.get('id')} name={workspace.get('name')} "
            f"status={workspace.get('status')} path={workspace.get('path')}"
        )
        if registered_new:
            lines.append("registered=new (auto-registered this session)")
    if index_info is not None:
        lines.append(
            f"index status={index_info.get('status')} "
            f"started={index_info.get('started')} "
            f"progress={index_info.get('progress', '')}"
        )
    if sync_info is not None:
        lines.append(
            f"sync files_synced={sync_info.get('files_synced_count', 0)} "
            f"fresh={sync_info.get('fresh')}"
        )
    others = max(0, len(workspaces) - (1 if workspace else 0))
    lines.append(f"workspaces_registered={len(workspaces)} others={others}")
    lines.append("")
    lines.append("## Brain (relevant only)")
    # Hard truncate brain text so bootstrap cannot dump the whole vault
    brain = (brain_pack_text or "").strip()
    if len(brain) > 2400:
        brain = brain[:2399] + "…"
    lines.append(brain or "(empty brain pack)")
    if open_file_sections:
        lines.append("")
        lines.append("## Open files (top hits only)")
        for section in open_file_sections[:5]:
            lines.append(section.strip())
            lines.append("")
    lines.append(
        "Cite the receipt below. Prefer mycelium_change_context / mycelium_debug_context "
        "over grepping. Do not re-pack the whole vault."
    )
    return _with_receipt("\n".join(lines).rstrip() + "\n", receipt=receipt)


def format_task_packet(
    label: str,
    *,
    query_packet: dict[str, Any] | None = None,
    focus_packet: dict[str, Any] | None = None,
    commits_text: str = "",
    vault_slice: str = "",
    hint: str | None = None,
) -> str:
    """Ranked task-shaped packet — search hits first; vault slice is optional & short."""
    parts = [f"# {label}"]
    if hint:
        parts.append(f"hint: {hint}")
    receipt = None
    if query_packet is not None:
        receipt = query_packet.get("receipt") or receipt
        parts.append(format_packet("Search hits", query_packet).rstrip())
    if focus_packet is not None:
        receipt = focus_packet.get("receipt") or receipt
        # Avoid double receipt line from nested format_packet — strip receipt lines
        focus_text = format_packet("Focus hits", focus_packet)
        focus_text = "\n".join(
            ln for ln in focus_text.splitlines() if not ln.startswith("receipt=")
        )
        parts.append(focus_text.rstrip())
    if vault_slice.strip():
        slice_text = vault_slice.strip()
        if len(slice_text) > 900:
            slice_text = slice_text[:899] + "…"
        parts.append("## Related vault (trimmed)")
        parts.append(slice_text)
    if commits_text.strip():
        # Keep at most ~8 commit lines
        c_lines = commits_text.strip().splitlines()[:12]
        parts.append("\n".join(c_lines))
    body = "\n\n".join(parts).rstrip() + "\n"
    # One receipt only (prefer search)
    if query_packet is not None:
        return body  # format_packet already appended receipt
    return _with_receipt(body, receipt=receipt if isinstance(receipt, dict) else None)

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
