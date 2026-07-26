"""Mycelium console entrypoints: `mycelium serve` / `mycelium-core`."""

from __future__ import annotations

import argparse
import logging
import signal
import sys

from mycelium import __version__
from mycelium.core.config import ensure_local_layout
from mycelium.core.logging import setup_logging

log = logging.getLogger("mycelium.cli")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mycelium",
        description="Mycelium local-first Context Layer",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command")

    serve = sub.add_parser("serve", help="Run Core HTTP API (production; no reload)")
    serve.add_argument("--host", default=None, help="Override bind host from config")
    serve.add_argument("--port", type=int, default=None, help="Override bind port from config")
    serve.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload (dev only; not for production)",
    )
    return parser


def cmd_serve(host: str | None, port: int | None, reload: bool) -> int:
    import uvicorn

    from mycelium.adapters.http.app import app as fastapi_app

    cfg = ensure_local_layout()
    logs_dir = cfg.paths.home / "logs"
    setup_logging(logs_dir)
    bind_host = host or cfg.server.host
    bind_port = port or cfg.server.port

    log.info(
        "Starting Mycelium Core %s on http://%s:%s (config_version=%s)",
        __version__,
        bind_host,
        bind_port,
        cfg.config_version,
    )
    log.info("Logs: %s", logs_dir)

    # Pass the app object (not an import string) so PyInstaller sidecars work.
    config = uvicorn.Config(
        fastapi_app,
        host=bind_host,
        port=bind_port,
        reload=reload and not getattr(sys, "frozen", False),
        log_level="info",
    )
    server = uvicorn.Server(config)

    def _stop(signum: int, _frame: object) -> None:
        log.info("Received signal %s — shutting down", signum)
        server.should_exit = True

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    server.run()
    return 0 if server.started or not server.should_exit else 0


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        raise SystemExit(0)
    if args.command == "serve":
        raise SystemExit(cmd_serve(args.host, args.port, args.reload))
    parser.error(f"Unknown command: {args.command}")


def core_main() -> None:
    """Entry for `mycelium-core` — always serves."""
    main(["serve", *sys.argv[1:]])


if __name__ == "__main__":
    main()
