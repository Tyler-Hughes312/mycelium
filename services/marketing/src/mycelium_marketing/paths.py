from __future__ import annotations

import os
from pathlib import Path


def repo_root() -> Path:
    env = os.environ.get("MYCELIUM_REPO_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    # services/marketing/src/mycelium_marketing/paths.py → repo root
    return Path(__file__).resolve().parents[4]


def drafts_dir() -> Path:
    return repo_root() / "docs" / "marketing" / "drafts"


def marketing_home() -> Path:
    base = Path(os.environ.get("MYCELIUM_HOME", Path.home() / ".mycelium"))
    path = base / "marketing"
    path.mkdir(parents=True, exist_ok=True)
    return path


def env_file() -> Path:
    return marketing_home() / "marketing.env"


def ledger_path() -> Path:
    return marketing_home() / "ledger.jsonl"


def queue_path() -> Path:
    return marketing_home() / "queue.jsonl"


def hn_storage_path() -> Path:
    return marketing_home() / "hn-storage.json"


def reddit_storage_path() -> Path:
    return marketing_home() / "reddit-storage.json"


def reddit_chrome_profile() -> Path:
    path = marketing_home() / "chrome-reddit-profile"
    path.mkdir(parents=True, exist_ok=True)
    return path


def vault_marketing_engine() -> Path:
    base = Path(os.environ.get("MYCELIUM_HOME", Path.home() / ".mycelium"))
    return base / "vault" / "work" / "active" / "marketing-engine.md"
