"""Local config + data directories (AD-2 / FR-19)."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONFIG_TOML = """\
# Mycelium local configuration
# Code and Vault contents stay on this machine by default (FR-19 / AD-2).

[network]
# When false, Core will not upload repo/Vault contents to remote services.
allow_code_upload = false
# Generative LLM calls require explicit opt-in + user-supplied credentials.
allow_remote_llm = false

[server]
# Bind address for the local HTTP API (AD-2).
host = "127.0.0.1"
port = 8787

[paths]
# Relative to ~/.mycelium unless absolute.
data_dir = "data"
vault_dir = "vault"

[index]
# Max commits to ingest on initial index (FR-5).
history_depth = 500
"""


@dataclass(frozen=True)
class MyceliumPaths:
    home: Path
    config_file: Path
    data_dir: Path
    vault_dir: Path


@dataclass(frozen=True)
class NetworkPolicy:
    allow_code_upload: bool
    allow_remote_llm: bool


@dataclass(frozen=True)
class ServerBind:
    host: str
    port: int


@dataclass(frozen=True)
class IndexSettings:
    history_depth: int


@dataclass(frozen=True)
class MyceliumConfig:
    paths: MyceliumPaths
    network: NetworkPolicy
    server: ServerBind
    index: IndexSettings


def default_home() -> Path:
    return Path.home() / ".mycelium"


def ensure_local_layout(home: Path | None = None) -> MyceliumConfig:
    """Create ~/.mycelium/config.toml and data dirs on first run; load config."""
    root = home or default_home()
    root.mkdir(parents=True, exist_ok=True)
    config_file = root / "config.toml"
    if not config_file.exists():
        config_file.write_text(DEFAULT_CONFIG_TOML, encoding="utf-8")

    raw = tomllib.loads(config_file.read_text(encoding="utf-8"))
    paths_cfg = raw.get("paths", {})
    net_cfg = raw.get("network", {})
    srv_cfg = raw.get("server", {})
    index_cfg = raw.get("index", {})

    def resolve(p: str, fallback: str) -> Path:
        candidate = Path(p or fallback)
        return candidate if candidate.is_absolute() else root / candidate

    data_dir = resolve(str(paths_cfg.get("data_dir", "data")), "data")
    vault_dir = resolve(str(paths_cfg.get("vault_dir", "vault")), "vault")
    data_dir.mkdir(parents=True, exist_ok=True)
    vault_dir.mkdir(parents=True, exist_ok=True)

    depth = int(index_cfg.get("history_depth", 500))
    if depth < 1:
        depth = 500

    return MyceliumConfig(
        paths=MyceliumPaths(
            home=root,
            config_file=config_file,
            data_dir=data_dir,
            vault_dir=vault_dir,
        ),
        network=NetworkPolicy(
            allow_code_upload=bool(net_cfg.get("allow_code_upload", False)),
            allow_remote_llm=bool(net_cfg.get("allow_remote_llm", False)),
        ),
        server=ServerBind(
            host=str(srv_cfg.get("host", "127.0.0.1")),
            port=int(srv_cfg.get("port", 8787)),
        ),
        index=IndexSettings(history_depth=depth),
    )
