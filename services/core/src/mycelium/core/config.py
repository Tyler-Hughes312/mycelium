"""Local config + data directories (AD-2 / FR-19)."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

CURRENT_CONFIG_VERSION = 1

DEFAULT_CONFIG_TOML = """\
# Mycelium local configuration
# Code and Vault contents stay on this machine by default (FR-19 / AD-2).

config_version = 1

[network]
# When false, Core will not upload repo/Vault contents to remote services.
allow_code_upload = false
# Generative LLM calls require explicit opt-in + user-supplied credentials.
allow_remote_llm = false

[server]
# Bind address for the local HTTP API (AD-2).
host = "127.0.0.1"
port = 8787
# Optional shared secret for local multi-process clients (off by default).
# When set, clients must send Authorization: Bearer <token>.
api_token = ""

[paths]
# Relative to ~/.mycelium unless absolute.
data_dir = "data"
vault_dir = "vault"

[index]
# Max commits to ingest on initial index (FR-5).
history_depth = 500

[embedding]
# Local sentence-transformers model (downloads once into ~/.mycelium/models).
# Alternatives: jinaai/jina-embeddings-v2-base-code | mycelium-hashing-v1 (tests)
model = "sentence-transformers/all-MiniLM-L6-v2"

[github]
# Optional OAuth App client_id for device login (or set MYCELIUM_GITHUB_CLIENT_ID).
# Create at https://github.com/settings/developers — enable Device Flow.
# PAT paste in Settings works without this.
client_id = ""

[impact]
# Local token-savings estimates for recall (search / focus / vault pack). No cloud.
tracking_enabled = true
default_model = "claude-sonnet-4"

[llm]
# Optional OpenAI-compatible chat provider (requires allow_remote_llm + API key).
provider = "openai_compatible"
model = "gpt-4o-mini"
base_url = "https://api.openai.com/v1"
# Env var name holding the API key (preferred). Fallback file: ~/.mycelium/llm_api_key
api_key_env = "MYCELIUM_LLM_API_KEY"
api_key_file = "llm_api_key"
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
    api_token: str = ""


@dataclass(frozen=True)
class IndexSettings:
    history_depth: int


@dataclass(frozen=True)
class EmbeddingSettings:
    model: str


@dataclass(frozen=True)
class GitHubSettings:
    client_id: str = ""


@dataclass(frozen=True)
class ImpactSettings:
    tracking_enabled: bool = True
    default_model: str = "claude-sonnet-4"
    pricing_overrides: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class LlmSettings:
    provider: str = "openai_compatible"
    model: str = "gpt-4o-mini"
    base_url: str = "https://api.openai.com/v1"
    api_key_env: str = "MYCELIUM_LLM_API_KEY"
    api_key_file: str = "llm_api_key"


@dataclass(frozen=True)
class MyceliumConfig:
    paths: MyceliumPaths
    network: NetworkPolicy
    server: ServerBind
    index: IndexSettings
    embedding: EmbeddingSettings
    github: GitHubSettings = GitHubSettings()
    impact: ImpactSettings = ImpactSettings()
    llm: LlmSettings = LlmSettings()
    config_version: int = CURRENT_CONFIG_VERSION


def default_home() -> Path:
    return Path.home() / ".mycelium"


def migrate_config_raw(raw: dict, config_file: Path) -> dict:
    """Migrate-on-load stub: ensure config_version is present and current.

    Future migrations bump CURRENT_CONFIG_VERSION and rewrite here.
    """
    version = int(raw.get("config_version", 0) or 0)
    if version >= CURRENT_CONFIG_VERSION:
        return raw

    # v0 → v1: stamp version; preserve all existing keys.
    raw = dict(raw)
    raw["config_version"] = CURRENT_CONFIG_VERSION
    # Rewrite TOML lightly via reload path after parse — caller may persist.
    _rewrite_migrated(config_file, raw)
    return raw


def _rewrite_migrated(config_file: Path, raw: dict) -> None:
    """Persist a migrated raw dict without losing user fields we know about."""
    net = raw.get("network", {})
    srv = raw.get("server", {})
    paths = raw.get("paths", {})
    index = raw.get("index", {})
    emb = raw.get("embedding", {})
    gh = raw.get("github", {})
    impact = raw.get("impact", {})
    llm = raw.get("llm", {})
    token = str(srv.get("api_token", "") or "")
    client_id = str(gh.get("client_id", "") or "").replace('"', '\\"')
    tracking = bool(impact.get("tracking_enabled", True))
    default_model = str(impact.get("default_model", "claude-sonnet-4") or "claude-sonnet-4")
    default_model = default_model.replace("\\", "\\\\").replace('"', '\\"')
    overrides = _parse_pricing_overrides(impact.get("pricing_overrides"))
    overrides_toml = _format_pricing_overrides_toml(overrides)
    llm_provider = str(llm.get("provider", "openai_compatible") or "openai_compatible").replace(
        '"', '\\"'
    )
    llm_model = str(llm.get("model", "gpt-4o-mini") or "gpt-4o-mini").replace('"', '\\"')
    llm_base = str(llm.get("base_url", "https://api.openai.com/v1") or "https://api.openai.com/v1").replace(
        '"', '\\"'
    )
    llm_env = str(llm.get("api_key_env", "MYCELIUM_LLM_API_KEY") or "MYCELIUM_LLM_API_KEY").replace(
        '"', '\\"'
    )
    llm_file = str(llm.get("api_key_file", "llm_api_key") or "llm_api_key").replace('"', '\\"')
    text = f"""\
# Mycelium local configuration
# Code and Vault contents stay on this machine by default (FR-19 / AD-2).

config_version = {CURRENT_CONFIG_VERSION}

[network]
allow_code_upload = {"true" if bool(net.get("allow_code_upload", False)) else "false"}
allow_remote_llm = {"true" if bool(net.get("allow_remote_llm", False)) else "false"}

[server]
host = "{srv.get("host", "127.0.0.1")}"
port = {int(srv.get("port", 8787))}
api_token = "{token}"

[paths]
data_dir = "{paths.get("data_dir", "data")}"
vault_dir = "{paths.get("vault_dir", "vault")}"

[index]
history_depth = {int(index.get("history_depth", 500))}

[embedding]
model = "{emb.get("model", "sentence-transformers/all-MiniLM-L6-v2")}"

[github]
client_id = "{client_id}"

[impact]
tracking_enabled = {"true" if tracking else "false"}
default_model = "{default_model}"
{overrides_toml}
[llm]
provider = "{llm_provider}"
model = "{llm_model}"
base_url = "{llm_base}"
api_key_env = "{llm_env}"
api_key_file = "{llm_file}"
"""
    config_file.write_text(text, encoding="utf-8")


def ensure_local_layout(home: Path | None = None) -> MyceliumConfig:
    """Create ~/.mycelium/config.toml and data dirs on first run; load config."""
    root = home or default_home()
    root.mkdir(parents=True, exist_ok=True)
    config_file = root / "config.toml"
    if not config_file.exists():
        config_file.write_text(DEFAULT_CONFIG_TOML, encoding="utf-8")
    return load_config(root)


def load_config(home: Path | None = None) -> MyceliumConfig:
    root = home or default_home()
    config_file = root / "config.toml"
    raw = tomllib.loads(config_file.read_text(encoding="utf-8"))
    raw = migrate_config_raw(raw, config_file)
    paths_cfg = raw.get("paths", {})
    net_cfg = raw.get("network", {})
    srv_cfg = raw.get("server", {})
    index_cfg = raw.get("index", {})
    emb_cfg = raw.get("embedding", {})
    gh_cfg = raw.get("github", {})
    impact_cfg = raw.get("impact", {})
    llm_cfg = raw.get("llm", {})

    def resolve(p: str, fallback: str) -> Path:
        candidate = Path(p or fallback).expanduser()
        return candidate if candidate.is_absolute() else root / candidate

    data_dir = resolve(str(paths_cfg.get("data_dir", "data")), "data")
    vault_dir = resolve(str(paths_cfg.get("vault_dir", "vault")), "vault")
    data_dir.mkdir(parents=True, exist_ok=True)
    vault_dir.mkdir(parents=True, exist_ok=True)

    from mycelium.adapters.vault.scaffold import scaffold_vault

    scaffold_vault(vault_dir)

    depth = int(index_cfg.get("history_depth", 500))
    if depth < 1:
        depth = 500

    from mycelium.adapters.embeddings.bootstrap import DEFAULT_EMBEDDING_MODEL

    model = str(emb_cfg.get("model", DEFAULT_EMBEDDING_MODEL)).strip() or DEFAULT_EMBEDDING_MODEL
    client_id = str(gh_cfg.get("client_id", "") or "").strip()
    default_model = str(impact_cfg.get("default_model", "claude-sonnet-4") or "").strip()
    if not default_model:
        default_model = "claude-sonnet-4"
    pricing_overrides = _parse_pricing_overrides(impact_cfg.get("pricing_overrides"))
    llm_settings = LlmSettings(
        provider=str(llm_cfg.get("provider", "openai_compatible") or "openai_compatible").strip()
        or "openai_compatible",
        model=str(llm_cfg.get("model", "gpt-4o-mini") or "gpt-4o-mini").strip() or "gpt-4o-mini",
        base_url=str(
            llm_cfg.get("base_url", "https://api.openai.com/v1") or "https://api.openai.com/v1"
        ).strip()
        or "https://api.openai.com/v1",
        api_key_env=str(
            llm_cfg.get("api_key_env", "MYCELIUM_LLM_API_KEY") or "MYCELIUM_LLM_API_KEY"
        ).strip()
        or "MYCELIUM_LLM_API_KEY",
        api_key_file=str(llm_cfg.get("api_key_file", "llm_api_key") or "llm_api_key").strip()
        or "llm_api_key",
    )

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
            api_token=str(srv_cfg.get("api_token", "") or ""),
        ),
        index=IndexSettings(history_depth=depth),
        embedding=EmbeddingSettings(model=model),
        github=GitHubSettings(client_id=client_id),
        impact=ImpactSettings(
            tracking_enabled=bool(impact_cfg.get("tracking_enabled", True)),
            default_model=default_model,
            pricing_overrides=pricing_overrides,
        ),
        llm=llm_settings,
        config_version=int(raw.get("config_version", CURRENT_CONFIG_VERSION)),
    )


def _parse_pricing_overrides(raw: object) -> dict[str, float]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, float] = {}
    for key, value in raw.items():
        try:
            out[str(key)] = float(value)
        except (TypeError, ValueError):
            continue
    return out


def _format_pricing_overrides_toml(overrides: dict[str, float]) -> str:
    if not overrides:
        return ""
    lines = ["[impact.pricing_overrides]"]
    for model_id, rate in sorted(overrides.items()):
        escaped = model_id.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'"{escaped}" = {float(rate)}')
    return "\n".join(lines) + "\n"


def _path_for_toml(home: Path, path: Path) -> str:
    try:
        rel = path.resolve().relative_to(home.resolve())
        return rel.as_posix()
    except ValueError:
        return str(path.resolve())


def write_config(cfg: MyceliumConfig) -> None:
    """Persist config.toml from a MyceliumConfig snapshot."""
    home = cfg.paths.home
    token = cfg.server.api_token.replace("\\", "\\\\").replace('"', '\\"')
    client_id = cfg.github.client_id.replace("\\", "\\\\").replace('"', '\\"')
    default_model = cfg.impact.default_model.replace("\\", "\\\\").replace('"', '\\"')
    overrides_toml = _format_pricing_overrides_toml(cfg.impact.pricing_overrides)
    llm_provider = cfg.llm.provider.replace("\\", "\\\\").replace('"', '\\"')
    llm_model = cfg.llm.model.replace("\\", "\\\\").replace('"', '\\"')
    llm_base = cfg.llm.base_url.replace("\\", "\\\\").replace('"', '\\"')
    llm_env = cfg.llm.api_key_env.replace("\\", "\\\\").replace('"', '\\"')
    llm_file = cfg.llm.api_key_file.replace("\\", "\\\\").replace('"', '\\"')
    text = f"""\
# Mycelium local configuration
# Code and Vault contents stay on this machine by default (FR-19 / AD-2).

config_version = {cfg.config_version}

[network]
allow_code_upload = {"true" if cfg.network.allow_code_upload else "false"}
allow_remote_llm = {"true" if cfg.network.allow_remote_llm else "false"}

[server]
host = "{cfg.server.host}"
port = {cfg.server.port}
api_token = "{token}"

[paths]
data_dir = "{_path_for_toml(home, cfg.paths.data_dir)}"
vault_dir = "{_path_for_toml(home, cfg.paths.vault_dir)}"

[index]
history_depth = {cfg.index.history_depth}

[embedding]
model = "{cfg.embedding.model}"

[github]
client_id = "{client_id}"

[impact]
tracking_enabled = {"true" if cfg.impact.tracking_enabled else "false"}
default_model = "{default_model}"
{overrides_toml}
[llm]
provider = "{llm_provider}"
model = "{llm_model}"
base_url = "{llm_base}"
api_key_env = "{llm_env}"
api_key_file = "{llm_file}"
"""
    cfg.paths.config_file.write_text(text, encoding="utf-8")
    cfg.paths.data_dir.mkdir(parents=True, exist_ok=True)
    cfg.paths.vault_dir.mkdir(parents=True, exist_ok=True)


def write_llm_api_key(cfg: MyceliumConfig, api_key: str) -> Path:
    """Write Chat LLM API key to ~/.mycelium/llm_api_key (mode 0600). Never logs the key."""
    key = (api_key or "").strip()
    if not key:
        raise ValueError("api_key must be non-empty")
    key_file = (cfg.llm.api_key_file or "llm_api_key").strip() or "llm_api_key"
    path = Path(key_file).expanduser()
    if not path.is_absolute():
        path = cfg.paths.home / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(key + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return path


def update_config(
    home: Path | None = None,
    *,
    vault_dir: str | None = None,
    history_depth: int | None = None,
    embedding_model: str | None = None,
    allow_code_upload: bool | None = None,
    allow_remote_llm: bool | None = None,
    github_client_id: str | None = None,
    impact_tracking_enabled: bool | None = None,
    impact_default_model: str | None = None,
    impact_pricing_overrides: dict[str, float] | None = None,
    llm_provider: str | None = None,
    llm_model: str | None = None,
    llm_base_url: str | None = None,
    llm_api_key: str | None = None,
) -> MyceliumConfig:
    """Patch selected settings and rewrite config.toml."""
    cfg = load_config(home)
    root = cfg.paths.home

    new_vault = cfg.paths.vault_dir
    if vault_dir is not None:
        candidate = Path(vault_dir).expanduser()
        new_vault = candidate if candidate.is_absolute() else root / candidate

    new_depth = cfg.index.history_depth
    if history_depth is not None:
        new_depth = max(1, int(history_depth))

    new_model = cfg.embedding.model
    if embedding_model is not None and embedding_model.strip():
        new_model = embedding_model.strip()

    new_net = NetworkPolicy(
        allow_code_upload=(
            cfg.network.allow_code_upload
            if allow_code_upload is None
            else bool(allow_code_upload)
        ),
        allow_remote_llm=(
            cfg.network.allow_remote_llm
            if allow_remote_llm is None
            else bool(allow_remote_llm)
        ),
    )

    new_gh = cfg.github
    if github_client_id is not None:
        new_gh = GitHubSettings(client_id=github_client_id.strip())

    new_impact = cfg.impact
    if (
        impact_tracking_enabled is not None
        or impact_default_model is not None
        or impact_pricing_overrides is not None
    ):
        new_default_model = cfg.impact.default_model
        if impact_default_model is not None:
            new_default_model = impact_default_model.strip() or "claude-sonnet-4"
        new_overrides = (
            dict(impact_pricing_overrides)
            if impact_pricing_overrides is not None
            else cfg.impact.pricing_overrides
        )
        new_impact = ImpactSettings(
            tracking_enabled=(
                cfg.impact.tracking_enabled
                if impact_tracking_enabled is None
                else bool(impact_tracking_enabled)
            ),
            default_model=new_default_model,
            pricing_overrides=new_overrides,
        )

    new_llm = cfg.llm
    if llm_provider is not None or llm_model is not None or llm_base_url is not None:
        new_llm = LlmSettings(
            provider=(
                llm_provider.strip()
                if llm_provider is not None and llm_provider.strip()
                else cfg.llm.provider
            ),
            model=(
                llm_model.strip()
                if llm_model is not None and llm_model.strip()
                else cfg.llm.model
            ),
            base_url=(
                llm_base_url.strip().rstrip("/")
                if llm_base_url is not None and llm_base_url.strip()
                else cfg.llm.base_url
            ),
            api_key_env=cfg.llm.api_key_env,
            api_key_file=cfg.llm.api_key_file,
        )

    updated = MyceliumConfig(
        paths=MyceliumPaths(
            home=root,
            config_file=cfg.paths.config_file,
            data_dir=cfg.paths.data_dir,
            vault_dir=new_vault,
        ),
        network=new_net,
        server=cfg.server,
        index=IndexSettings(history_depth=new_depth),
        embedding=EmbeddingSettings(model=new_model),
        github=new_gh,
        impact=new_impact,
        llm=new_llm,
        config_version=cfg.config_version,
    )
    write_config(updated)
    if llm_api_key is not None and llm_api_key.strip():
        write_llm_api_key(updated, llm_api_key)
    return load_config(root)


def settings_dict(cfg: MyceliumConfig) -> dict:
    return {
        "vault_dir": str(cfg.paths.vault_dir),
        "data_dir": str(cfg.paths.data_dir),
        "config_file": str(cfg.paths.config_file),
        "config_version": cfg.config_version,
        "history_depth": cfg.index.history_depth,
        "embedding_model": cfg.embedding.model,
        "allow_code_upload": cfg.network.allow_code_upload,
        "allow_remote_llm": cfg.network.allow_remote_llm,
        "impact_tracking_enabled": cfg.impact.tracking_enabled,
        "impact_default_model": cfg.impact.default_model,
        "impact_pricing_overrides": dict(cfg.impact.pricing_overrides),
        "llm_provider": cfg.llm.provider,
        "llm_model": cfg.llm.model,
        "llm_base_url": cfg.llm.base_url,
        "llm_api_key_env": cfg.llm.api_key_env,
        "llm_api_key_configured": bool(_resolve_llm_key_present(cfg)),
        "api_token_enabled": bool(cfg.server.api_token),
        "github_client_id": cfg.github.client_id,
        "github_oauth_configured": bool(cfg.github.client_id),
        "server": {"host": cfg.server.host, "port": cfg.server.port},
        "privacy": {
            "local_first": True,
            "cloud_account_required": False,
            "summary": (
                "Code and Vault stay on this machine by default. "
                "No cloud account is required. GitHub connect is optional."
            ),
        },
    }


def _resolve_llm_key_present(cfg: MyceliumConfig) -> bool:
    import os

    env_name = (cfg.llm.api_key_env or "MYCELIUM_LLM_API_KEY").strip() or "MYCELIUM_LLM_API_KEY"
    if os.environ.get(env_name, "").strip():
        return True
    key_file = (cfg.llm.api_key_file or "llm_api_key").strip() or "llm_api_key"
    path = Path(key_file).expanduser()
    if not path.is_absolute():
        path = cfg.paths.home / path
    return path.is_file() and bool(path.read_text(encoding="utf-8").strip())
