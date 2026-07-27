"""Mycelium MCP Bridge — recall tools over the same Core HTTP API (AD-3 / FR-22)."""

from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from mycelium.bridges.mcp.client import DEFAULT_CORE_URL, CoreHttp
from mycelium.bridges.mcp.formatters import (
    format_commits,
    format_note,
    format_packet,
    resolve_workspace_id,
)
from mycelium.core.domain.impact_pricing import _PROBE_KEYS

mcp = FastMCP(
    "mycelium",
    instructions=(
        "Mycelium is a local-first second brain + Context Layer for this developer. "
        "Code and vault stay on localhost Core (default http://127.0.0.1:8787).\n\n"
        "READ (prefer cheap structure first):\n"
        "1) mycelium_vault_tree → 2) mycelium_vault_pack(bucket) → 3) mycelium_get_note "
        "only if needed. Use mycelium_search / mycelium_focus for semantic or file-local recall.\n\n"
        "WRITE (second brain — when necessary):\n"
        "Capture durable decisions, ADRs, and 'why we did X' into the Thinking Vault with "
        "mycelium_create_note / mycelium_update_note (and mycelium_create_bucket for folders). "
        "Vault layout (kepano + obsidian-mind inspired): brain/ (North Star, decisions index), "
        "work/active|archive|decisions, notes/, daily/, reference/, thinking/, clippings/, templates/. "
        "Read vault AGENTS.md / Home.md via pack if unsure where to file. "
        "Use [[wikilinks]] to symbols/notes. Do NOT write every chat turn — only lasting knowledge. "
        "Call mycelium_vault_scaffold once if the vault looks empty/flat.\n\n"
        "INDEX FRESHNESS:\n"
        "Core watches workspace + vault files on disk. mycelium_search / mycelium_focus auto-sync "
        "dirty git files before querying. After bulk code edits you may call mycelium_sync_index. "
        "Vault note writes re-embed immediately.\n\n"
        "CROSS-REPO:\n"
        "mycelium_search defaults to ALL registered workspaces so you can reuse patterns from old "
        "repos. Pass workspace_id / workspace_path to narrow to one project. Results are tagged "
        "with @repo name.\n\n"
        "Never invent paths that tools did not return. Prefer Mycelium over guessing vault/code context."
    ),
)


def _core() -> CoreHttp:
    return CoreHttp(
        os.environ.get("MYCELIUM_CORE_URL", DEFAULT_CORE_URL),
        headers=_mcp_impact_headers(),
    )


def _mcp_impact_headers() -> dict[str, str]:
    """Best-effort model probe from FastMCP request _meta → Core impact headers."""
    try:
        ctx = mcp.get_context()
        if ctx._request_context is None:
            return {}
        meta = ctx.request_context.meta
        if meta is None:
            return {}
        meta_dict = meta.model_dump(exclude_none=True)
        for key in _PROBE_KEYS:
            value = meta_dict.get(key)
            if value:
                headers = {"X-Mycelium-Model-Id": str(value).strip()}
                headers["X-Mycelium-Model-Probe"] = key
                return headers
        return {}
    except Exception:  # noqa: BLE001
        return {}


def _wid(
    core: CoreHttp,
    workspace_id: str | None,
    workspace_path: str | None,
    *,
    default_all: bool = False,
) -> str:
    return resolve_workspace_id(
        core.list_workspaces(),
        workspace_id=workspace_id or None,
        workspace_path=workspace_path or None,
        default_all=default_all,
    )


@mcp.tool()
def mycelium_health() -> str:
    """Check that Mycelium Core is reachable on localhost."""
    core = _core()
    try:
        h = core.health()
        return (
            f"ok status={h.get('status')} version={h.get('version')} "
            f"core={core.base_url}"
        )
    except Exception as exc:  # noqa: BLE001
        return f"offline core={core.base_url} error={exc}"
    finally:
        core.close()


@mcp.tool()
def mycelium_list_workspaces() -> str:
    """List registered Mycelium workspace repos (id, name, path, status)."""
    core = _core()
    try:
        rows = core.list_workspaces()
        if not rows:
            return "No workspaces. Register a git repo in Mycelium Desktop Library."
        lines = ["# Workspaces"]
        for w in rows:
            lines.append(
                f"- id={w.get('id')} name={w.get('name')} "
                f"status={w.get('status')} path={w.get('path')}"
            )
        return "\n".join(lines)
    finally:
        core.close()


@mcp.tool()
def mycelium_search(
    query: str,
    workspace_id: str = "",
    workspace_path: str = "",
    limit: int = 8,
) -> str:
    """
    Hybrid RAG search over indexed workspace(s) — Symbols, Commits, Files, Notes.

    Omit workspace_id to search ALL registered repos (reuse old code across projects).
    Pass workspace_id from mycelium_list_workspaces, workspace_path for one repo,
    or workspace_id='*' explicitly for all.
    """
    core = _core()
    try:
        wid = _wid(
            core,
            workspace_id or None,
            workspace_path or None,
            default_all=True,
        )
        try:
            if wid == "*":
                for row in core.list_workspaces():
                    rid = row.get("id")
                    if rid:
                        try:
                            core.sync_workspace(str(rid))
                        except Exception:  # noqa: BLE001
                            pass
            else:
                core.sync_workspace(wid)
        except Exception:  # noqa: BLE001
            pass
        packet = core.query(query=query, workspace_id=wid, limit=max(1, min(limit, 10)))
        return format_packet(f"Search: {query}", packet)
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"
    finally:
        core.close()


@mcp.tool()
def mycelium_focus(
    path: str,
    workspace_id: str = "",
    workspace_path: str = "",
    symbol: str = "",
    line: int = 0,
    limit: int = 10,
) -> str:
    """
    Focus Context Packet for a file path (and optional symbol / line).

    `path` is workspace-relative (e.g. src/auth.ts). Returns ranked related
    Symbols, Commits, Notes — notes explicitly linked to the symbol are boosted.
    """
    core = _core()
    try:
        wid = _wid(core, workspace_id or None, workspace_path or None)
        try:
            core.sync_workspace(wid)
        except Exception:  # noqa: BLE001
            pass
        packet = core.focus(
            workspace_id=wid,
            path=path,
            symbol=symbol or None,
            line=line or None,
            limit=max(1, min(limit, 10)),
        )
        label = f"Focus: {path}" + (f"#{symbol}" if symbol else "")
        return format_packet(label, packet)
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"
    finally:
        core.close()


@mcp.tool()
def mycelium_get_note(note: str) -> str:
    """
    Fetch a Thinking Vault note by id (note:slug), stem, or title.

    Notes created in Desktop/Editor are visible here (same Vault on disk).
    Prefer mycelium_vault_tree / mycelium_vault_pack first to save tokens.
    """
    core = _core()
    try:
        # Try direct id/stem first
        try:
            row = core.get_note(note)
            if row:
                return format_note(row)
        except Exception:  # noqa: BLE001
            pass
        # Title / stem search
        needle = note.strip().lower()
        for n in core.list_notes():
            if (
                str(n.get("title") or "").lower() == needle
                or str(n.get("path") or "").lower() == needle
                or str(n.get("path") or "").lower() == f"{needle}.md"
                or str(n.get("id") or "").lower() in {needle, f"note:{needle}"}
            ):
                return format_note(n)
        return f"error: note not found: {note}"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"
    finally:
        core.close()


@mcp.tool()
def mycelium_vault_tree() -> str:
    """
    Structure-first vault map (folders/buckets + note titles). No RAG/embeddings.

    Use this before mycelium_vault_pack or mycelium_get_note to navigate cheaply.
    """
    core = _core()
    try:
        tree = core.vault_tree()
        root = tree.get("root") or {}
        lines = [
            "# Vault map",
            f"notes={tree.get('notes', 0)} buckets={tree.get('buckets', 0)}",
            "",
        ]

        def walk(node: dict[str, Any], depth: int = 0) -> None:
            indent = "  " * depth
            for child in node.get("children") or []:
                if child.get("type") == "folder":
                    lines.append(f"{indent}- [{child.get('path')}/]")
                    walk(child, depth + 1)
                else:
                    mark = " ★" if child.get("is_index") else ""
                    lines.append(
                        f"{indent}- {child.get('title')} (`{child.get('path')}`){mark}"
                    )

        walk(root)
        return "\n".join(lines) if len(lines) > 3 else "# Vault map\n(empty)"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"
    finally:
        core.close()


@mcp.tool()
def mycelium_vault_pack(
    bucket: str = "",
    max_tokens: int = 2000,
) -> str:
    """
    Pack a vault bucket (or whole vault) into a token-budget string. No RAG.

    Fill order: title map → `_index.md` briefs → other note bodies (truncated last).
    Pass bucket like `architecture` or leave empty for the whole vault.
    """
    core = _core()
    try:
        pack = core.vault_pack(
            bucket=bucket or None,
            max_tokens=max(64, min(max_tokens, 100_000)),
        )
        header = (
            f"[pack tokens_est={pack.get('tokens_est')} "
            f"max={pack.get('max_tokens')} truncated={pack.get('truncated')}]\n\n"
        )
        return header + str(pack.get("text") or "")
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"
    finally:
        core.close()


@mcp.tool()
def mycelium_create_bucket(name: str) -> str:
    """
    Create a vault bucket (folder) with an `_index.md` brief scaffold.

    Prefer the default layout (brain, work/decisions, notes, …) from mycelium_vault_scaffold
    before inventing new top-level folders.
    """
    core = _core()
    try:
        row = core.create_bucket(name.strip())
        index = row.get("index") or {}
        return (
            f"created bucket={row.get('bucket')} "
            f"index={index.get('path')} id={index.get('id')}"
        )
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"
    finally:
        core.close()


@mcp.tool()
def mycelium_vault_scaffold() -> str:
    """
    Ensure the default second-brain folder layout (idempotent).

    Inspired by kepano-obsidian + obsidian-mind: Home, AGENTS, brain/, work/, notes/,
    daily/, reference/, thinking/, templates/, clippings/, attachments/.
    Does not overwrite existing notes.
    """
    core = _core()
    try:
        row = core.vault_scaffold()
        return (
            f"scaffold layout={row.get('layout')} "
            f"folders_created={row.get('folders_created')} "
            f"notes_created={row.get('notes_created')} "
            f"vault={row.get('vault')}"
        )
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"
    finally:
        core.close()


@mcp.tool()
def mycelium_create_note(
    title: str,
    body: str,
    bucket: str = "",
    link_symbol: str = "",
) -> str:
    """
    Create a Thinking Vault note (second-brain write). Same disk as Desktop.

    Write durable decisions / ADRs / why-notes — not ephemeral chat.
    Prefer buckets: work/decisions, work/active, notes, reference, brain, thinking, daily, clippings.
    Check mycelium_vault_tree / AGENTS.md first. Body: markdown + [[wikilinks]].
    Optional link_symbol (e.g. src/ratelimit.py#calculate_jitter) adds an explicit link.
    """
    core = _core()
    try:
        note = core.create_note(
            title=title.strip(),
            body=body,
            bucket=bucket.strip() or None,
            link_symbol=link_symbol.strip() or None,
        )
        return format_note(note) + "\n\n[indexed=true — note embedded for RAG]"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"
    finally:
        core.close()


@mcp.tool()
def mycelium_update_note(
    note: str,
    body: str = "",
    title: str = "",
) -> str:
    """
    Update an existing vault note by id (note:…), path stem, or title.

    Pass body and/or title. Use to refine a decision note after more work —
    not to dump full chat transcripts.
    """
    core = _core()
    try:
        # Resolve like get_note
        target_id = ""
        try:
            row = core.get_note(note)
            if row.get("id"):
                target_id = str(row["id"])
        except Exception:  # noqa: BLE001
            pass
        if not target_id:
            needle = note.strip().lower()
            for n in core.list_notes():
                if (
                    str(n.get("title") or "").lower() == needle
                    or str(n.get("path") or "").lower() == needle
                    or str(n.get("path") or "").lower() == f"{needle}.md"
                    or str(n.get("id") or "").lower() in {needle, f"note:{needle}"}
                ):
                    target_id = str(n["id"])
                    break
        if not target_id:
            return f"error: note not found: {note}"
        updated = core.update_note(
            target_id,
            title=title.strip() or None,
            body=body if body != "" else None,
        )
        return format_note(updated) + "\n\n[indexed=true — note re-embedded for RAG]"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"
    finally:
        core.close()


@mcp.tool()
def mycelium_sync_index(
    workspace_id: str = "",
    workspace_path: str = "",
    vault: bool = True,
) -> str:
    """
    Sync index with current codebase + vault.

    Reindexes dirty git files (or starts a full index if HEAD moved). Optionally
    rebuilds vault note edges/embeddings. Usually automatic before search/focus;
    call after large batches of code edits.
    """
    core = _core()
    try:
        lines = ["# Sync"]
        try:
            wid = _wid(core, workspace_id or None, workspace_path or None)
            sync = core.sync_workspace(wid)
            lines.append(
                f"workspace={wid} files_synced={sync.get('files_synced_count', 0)} "
                f"full_index_started={sync.get('full_index_started')} "
                f"fresh={sync.get('fresh')}"
            )
            errs = sync.get("errors") or []
            if errs:
                lines.append("errors: " + "; ".join(str(e) for e in errs[:5]))
        except Exception as exc:  # noqa: BLE001
            lines.append(f"workspace_sync: {exc}")
        if vault:
            try:
                vr = core.vault_reindex()
                lines.append(
                    f"vault notes={vr.get('notes')} edges={vr.get('edges')} "
                    f"vectors={vr.get('embedding', {}).get('vectors', vr.get('vectors'))}"
                )
            except Exception as exc:  # noqa: BLE001
                lines.append(f"vault_reindex: {exc}")
        return "\n".join(lines)
    finally:
        core.close()


@mcp.tool()
def mycelium_commits_for_path(
    path: str,
    workspace_id: str = "",
    workspace_path: str = "",
    limit: int = 20,
) -> str:
    """
    List recent commits that touched a path (prefix or exact match on changed_paths).
    """
    core = _core()
    try:
        wid = _wid(core, workspace_id or None, workspace_path or None)
        commits = core.list_commits(wid, limit=min(max(limit * 5, 50), 500))
        needle = path.replace("\\", "/").lstrip("./")
        matched: list[dict[str, Any]] = []
        for c in commits:
            paths = [str(p).replace("\\", "/") for p in (c.get("changed_paths") or [])]
            if any(p == needle or p.startswith(needle) or needle in p for p in paths):
                matched.append(c)
            if len(matched) >= max(1, min(limit, 50)):
                break
        return format_commits(matched, path_filter=needle)
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"
    finally:
        core.close()


def main() -> None:
    """stdio MCP entrypoint — spawned by Cursor / Claude Code."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
