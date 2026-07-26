#!/usr/bin/env python3
"""Embedding model eval harness (Epic 8.2).

Compares candidate local embedders on the dogfood fixture + labeled queries.
Writes hit-rate report to docs/EMBEDDING-EVAL.md.

Usage (repo root):
  ./venv/bin/python scripts/eval_embeddings.py
  MYCELIUM_EVAL_MODELS=hashing,minilm ./venv/bin/python scripts/eval_embeddings.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "fixtures" / "dogfood-rate-limits"
QUERIES = FIX / "queries.json"
OUT = ROOT / "docs" / "EMBEDDING-EVAL.md"
sys.path.insert(0, str(ROOT / "services" / "core" / "src"))

from mycelium.adapters.embeddings.bootstrap import bootstrap_embedder  # noqa: E402
from mycelium.adapters.store.workspace_repo import JsonFileWorkspaceRepo  # noqa: E402
from mycelium.core.config import ensure_local_layout  # noqa: E402
from mycelium.core.domain.embedding_service import EmbeddingService  # noqa: E402
from mycelium.core.domain.index_service import IndexService  # noqa: E402
from mycelium.core.domain.rag_service import RagService  # noqa: E402
from mycelium.core.domain.vault_service import VaultService  # noqa: E402


CANDIDATES = {
    "hashing": "mycelium-hashing-v1",
    "minilm": "sentence-transformers/all-MiniLM-L6-v2",
}


@dataclass
class QuerySpec:
    id: str
    query: str
    expect_any: list[str]


def ensure_fixture() -> None:
    script = ROOT / "scripts" / "prepare_dogfood.sh"
    subprocess.run(["bash", str(script)], check=True, cwd=ROOT)


def load_queries() -> list[QuerySpec]:
    raw = json.loads(QUERIES.read_text(encoding="utf-8"))
    return [
        QuerySpec(id=r["id"], query=r["query"], expect_any=list(r["expect_any"]))
        for r in raw
    ]


def hit(results: list[dict], expect_any: list[str]) -> bool:
    blob = " ".join(
        f"{r.get('title', '')} {r.get('snippet', '')} {r.get('path', '')} {r.get('kind', '')}"
        for r in results
    ).lower()
    return any(token.lower() in blob for token in expect_any)


def eval_model(model_key: str, model_id: str, queries: list[QuerySpec]) -> dict:
    home = ROOT / ".mycelium-eval" / model_key
    if home.exists():
        # wipe prior run for clean vectors
        import shutil

        shutil.rmtree(home)
    cfg = ensure_local_layout(home)
    runtime, status = bootstrap_embedder(
        model=model_id,
        cache_dir=cfg.paths.home / "models",
    )
    repo = JsonFileWorkspaceRepo(cfg.paths.data_dir)
    index = IndexService(
        data_dir=cfg.paths.data_dir,
        workspace_repo=repo,
        history_depth=50,
        embedding_runtime=runtime,
        embedding_status=status,
        embedding_model=model_id,
    )
    vault = VaultService(
        vault_dir=cfg.paths.vault_dir,
        data_dir=cfg.paths.data_dir,
        workspace_repo=repo,
        runtime=runtime,
        status=status,
        model=model_id,
    )
    rag = RagService(
        data_dir=cfg.paths.data_dir,
        workspace_repo=repo,
        runtime=runtime,
        status=status,
        model=model_id,
        vault=vault,
    )

    ws = repo.register(str(FIX))
    result = index.run_initial_index(ws["id"])
    vault.create_note(
        title="Rate limit retries — decision",
        body=(
            "After reviewing authenticate(), we decided on jittered backoff via "
            "[[calculate_jitter]] so rate limiting does not cause thundering herds.\n"
        ),
        link_symbol="src/ratelimit.py#calculate_jitter",
    )
    vault.reindex(workspace_id=ws["id"])

    hits = 0
    rows = []
    for q in queries:
        packet = rag.query(workspace_id=ws["id"], query=q.query, limit=8)
        results = list(packet.get("results") or [])
        ok = hit(results, q.expect_any)
        hits += int(ok)
        top = ", ".join(
            f"{r.get('kind')}:{r.get('title')}" for r in results[:3]
        ) or "(none)"
        rows.append({"id": q.id, "ok": ok, "top": top, "query": q.query})

    rate = hits / max(len(queries), 1)
    return {
        "model_key": model_key,
        "model_id": status.model_id,
        "backend": status.backend,
        "notice": status.notice,
        "index_message": result.message,
        "hits": hits,
        "total": len(queries),
        "hit_rate": rate,
        "rows": rows,
    }


def write_report(reports: list[dict]) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    winner = max(reports, key=lambda r: (r["hit_rate"], r["model_key"] != "hashing"))
    lines = [
        "# Embedding eval results",
        "",
        f"Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Fixture: `fixtures/dogfood-rate-limits`",
        "",
        "## Summary",
        "",
        "| Model | Backend | Hits | Hit rate |",
        "|---|---|---:|---:|",
    ]
    for r in reports:
        lines.append(
            f"| `{r['model_id']}` | {r['backend']} | {r['hits']}/{r['total']} | "
            f"{r['hit_rate']:.0%} |"
        )
    lines += [
        "",
        f"**Winner (this run):** `{winner['model_id']}` ({winner['hit_rate']:.0%} hit rate).",
        "",
        "## Default in config",
        "",
        "Ship default remains `sentence-transformers/all-MiniLM-L6-v2` "
        "(semantic quality vs hashing). Hashing stays available for offline tests / CI.",
        "",
        "To try Jina code embeddings later:",
        "",
        "```toml",
        "# ~/.mycelium/config.toml",
        '[embedding]',
        'model = "jinaai/jina-embeddings-v2-base-code"',
        "```",
        "",
        "## Per-query detail",
        "",
    ]
    for r in reports:
        lines.append(f"### {r['model_id']}")
        lines.append("")
        for row in r["rows"]:
            mark = "PASS" if row["ok"] else "MISS"
            lines.append(f"- [{mark}] `{row['id']}` {row['query']} → {row['top']}")
        lines.append("")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"Winner: {winner['model_id']} @ {winner['hit_rate']:.0%}")


def main() -> int:
    ensure_fixture()
    queries = load_queries()
    keys = [
        k.strip()
        for k in os.environ.get("MYCELIUM_EVAL_MODELS", "hashing,minilm").split(",")
        if k.strip()
    ]
    reports = []
    for key in keys:
        if key not in CANDIDATES:
            print(f"skip unknown model key: {key}", file=sys.stderr)
            continue
        print(f"Evaluating {key} → {CANDIDATES[key]} …")
        reports.append(eval_model(key, CANDIDATES[key], queries))
        print(f"  hit_rate={reports[-1]['hit_rate']:.0%}")
    if not reports:
        print("No models evaluated", file=sys.stderr)
        return 1
    write_report(reports)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
