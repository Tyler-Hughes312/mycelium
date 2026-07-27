from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone

from mycelium_marketing.channels import hackernews, reddit
from mycelium_marketing.drafts import load_launch_drafts
from mycelium_marketing.guardrails import assert_autopilot_allowed, check_content
from mycelium_marketing.ledger import (
    LedgerEntry,
    QueueItem,
    already_posted,
    append_ledger,
    enqueue,
    minutes_since_last_reddit,
    read_queue,
    reddit_posts_last_24h,
    set_queue_status,
)
from mycelium_marketing.paths import drafts_dir, env_file, ledger_path, queue_path
from mycelium_marketing.schedule import Job, launch_jobs
from mycelium_marketing.vault_log import append_engine_log


EXIT_OK = 0
EXIT_PARTIAL = 2
EXIT_BLOCKED = 3


def _load_env() -> None:
    reddit.load_dotenv_file(env_file())


def _jobs_for_wave(wave_id: str) -> list[Job]:
    show, reddit_drafts = load_launch_drafts(drafts_dir())
    return launch_jobs(wave_id, show, reddit_drafts)


def _validate_jobs(jobs: list[Job]) -> list[str]:
    errors: list[str] = []
    for job in jobs:
        require = job.channel == "reddit"
        result = check_content(f"{job.title}\n{job.body}", require_disclosure=require)
        if not result.ok:
            errors.extend(f"{job.channel}/{job.target}: {e}" for e in result.errors)
    return errors


def cmd_status(args: argparse.Namespace) -> int:
    _load_env()
    r_ok, r_msg = reddit.status_ready()
    h_ok, h_msg = hackernews.status_ready()
    payload = {
        "ok": r_ok or h_ok,
        "reddit": {"ok": r_ok, "detail": r_msg},
        "hackernews": {"ok": h_ok, "detail": h_msg},
        "env_file": str(env_file()),
        "env_exists": env_file().exists(),
        "ledger": str(ledger_path()),
    }
    if getattr(args, "json", False):
        print(json.dumps(payload))
    else:
        print(f"reddit: {'OK' if r_ok else 'BLOCKED'} — {r_msg}")
        print(f"hackernews: {'OK' if h_ok else 'BLOCKED'} — {h_msg}")
        print(f"env file: {env_file()} ({'exists' if env_file().exists() else 'missing'})")
        print(f"ledger: {ledger_path()}")
    if not r_ok and not h_ok:
        return EXIT_BLOCKED
    if not r_ok or not h_ok:
        return EXIT_PARTIAL
    return EXIT_OK


def cmd_dry_run(args: argparse.Namespace) -> int:
    _load_env()
    jobs = _jobs_for_wave(args.wave)
    errors = _validate_jobs(jobs)
    if errors:
        if getattr(args, "json", False):
            print(json.dumps({"ok": False, "errors": errors, "jobs": []}))
        else:
            print("guardrail failures:")
            for e in errors:
                print(f"  - {e}")
        return EXIT_BLOCKED
    job_rows = []
    for job in jobs:
        if job.channel == "reddit":
            res = reddit.submit_text_post(
                subreddit=job.target, title=job.title, body=job.body, dry_run=True
            )
        else:
            res = hackernews.submit_show_hn(title=job.title, body=job.body, dry_run=True)
        job_rows.append(
            {
                "delay_minutes": job.delay_minutes,
                "channel": job.channel,
                "target": job.target,
                "title": job.title,
                "ok": res.ok,
                "detail": res.detail or res.url,
            }
        )
    if getattr(args, "json", False):
        print(json.dumps({"ok": True, "wave": args.wave, "jobs": job_rows}))
    else:
        print(f"wave={args.wave} jobs={len(jobs)}")
        for row in job_rows:
            print(
                f"  +{row['delay_minutes']:>3}m  {row['channel']:12} {row['target']:12}  {row['title'][:60]}"
            )
            print(f"           dry-run: ok={row['ok']} {row['detail']}")
    return EXIT_OK


def _respect_reddit_limits() -> str | None:
    path = ledger_path()
    recent = reddit_posts_last_24h(path)
    if len(recent) >= 3:
        return "reddit rate limit: max 3 posts / 24h"
    mins = minutes_since_last_reddit(path)
    if mins is not None and mins < 25:
        return f"reddit rate limit: wait {25 - mins:.0f} more minutes between posts"
    return None


def _run_job(job: Job, *, dry_run: bool, sleep: bool) -> LedgerEntry:
    if already_posted(ledger_path(), job.wave_id, job.channel, job.target):
        return LedgerEntry(
            wave_id=job.wave_id,
            channel=job.channel,
            target=job.target,
            status="skipped",
            detail="already posted for this wave",
        )
    if sleep and job.delay_minutes > 0 and not dry_run:
        print(f"sleeping {job.delay_minutes} minutes before {job.channel}/{job.target}…")
        time.sleep(job.delay_minutes * 60)

    if job.channel == "reddit":
        limit = _respect_reddit_limits()
        if limit and not dry_run:
            return LedgerEntry(
                wave_id=job.wave_id,
                channel=job.channel,
                target=job.target,
                status="skipped",
                detail=limit,
            )
        res = reddit.submit_text_post(
            subreddit=job.target, title=job.title, body=job.body, dry_run=dry_run
        )
    else:
        res = hackernews.submit_show_hn(title=job.title, body=job.body, dry_run=dry_run)

    status = "posted" if res.ok and not dry_run else ("dry-run" if res.ok else "failed")
    if dry_run and res.ok:
        status = "dry-run"
    entry = LedgerEntry(
        wave_id=job.wave_id,
        channel=job.channel,
        target=job.target,
        status=status if res.ok else "failed",
        url=res.url,
        detail=res.detail,
    )
    append_ledger(ledger_path(), entry)
    return entry


def cmd_run(args: argparse.Namespace) -> int:
    _load_env()
    gate = assert_autopilot_allowed(
        i_understand=args.i_understand,
        env_flag=os.environ.get("MARKETING_AUTOPILOT"),
    )
    if not gate.ok:
        if getattr(args, "json", False):
            print(json.dumps({"ok": False, "error": gate.errors[0], "results": []}))
        else:
            print(gate.errors[0])
        return EXIT_BLOCKED

    jobs = _jobs_for_wave(args.wave)
    errors = _validate_jobs(jobs)
    if errors:
        if getattr(args, "json", False):
            print(json.dumps({"ok": False, "errors": errors, "results": []}))
        else:
            print("guardrail failures:")
            for e in errors:
                print(f"  - {e}")
        return EXIT_BLOCKED

    posted = 0
    failed = 0
    skipped = 0
    results: list[dict] = []
    for job in jobs:
        # Skip HN if not ready rather than failing whole wave
        if job.channel == "hackernews":
            ready, msg = hackernews.status_ready()
            if not ready:
                entry = LedgerEntry(
                    wave_id=job.wave_id,
                    channel=job.channel,
                    target=job.target,
                    status="skipped",
                    detail=f"HN blocked: {msg}",
                )
                append_ledger(ledger_path(), entry)
                append_engine_log(f"HN blocked — {msg}")
                if not getattr(args, "json", False):
                    print(f"skip HN: {msg}")
                results.append(
                    {
                        "channel": entry.channel,
                        "target": entry.target,
                        "status": entry.status,
                        "url": entry.url,
                        "detail": entry.detail,
                    }
                )
                skipped += 1
                continue
        if job.channel == "reddit":
            ready, msg = reddit.status_ready()
            if not ready:
                entry = LedgerEntry(
                    wave_id=job.wave_id,
                    channel=job.channel,
                    target=job.target,
                    status="skipped",
                    detail=msg,
                )
                append_ledger(ledger_path(), entry)
                if not getattr(args, "json", False):
                    print(f"skip reddit/{job.target}: {msg}")
                results.append(
                    {
                        "channel": entry.channel,
                        "target": entry.target,
                        "status": entry.status,
                        "url": entry.url,
                        "detail": entry.detail,
                    }
                )
                skipped += 1
                continue

        entry = _run_job(job, dry_run=False, sleep=not args.no_sleep)
        if not getattr(args, "json", False):
            print(f"{entry.status:8} {entry.channel}/{entry.target} {entry.url or entry.detail}")
        results.append(
            {
                "channel": entry.channel,
                "target": entry.target,
                "status": entry.status,
                "url": entry.url,
                "detail": entry.detail,
            }
        )
        if entry.status == "posted":
            posted += 1
            append_engine_log(f"posted {entry.channel}/{entry.target} {entry.url}")
        elif entry.status == "failed":
            failed += 1
            append_engine_log(f"failed {entry.channel}/{entry.target} {entry.detail}")
        else:
            skipped += 1

    if getattr(args, "json", False):
        print(
            json.dumps(
                {
                    "ok": posted > 0 and failed == 0,
                    "posted": posted,
                    "failed": failed,
                    "skipped": skipped,
                    "results": results,
                }
            )
        )

    if posted == 0 and failed == 0:
        return EXIT_BLOCKED
    if failed or skipped:
        return EXIT_PARTIAL if posted else EXIT_BLOCKED
    return EXIT_OK


def cmd_login_hn(_: argparse.Namespace) -> int:
    res = hackernews.login_interactive()
    print(res.detail or res.url)
    return EXIT_OK if res.ok else EXIT_BLOCKED


def cmd_login_reddit(_: argparse.Namespace) -> int:
    res = reddit.login_interactive()
    print(res.detail or res.url)
    return EXIT_OK if res.ok else EXIT_BLOCKED


def cmd_open_reddit(args: argparse.Namespace) -> int:
    """Manual path when Reddit blocks automation — open submit tabs + print copy."""
    _load_env()
    jobs = [j for j in _jobs_for_wave(args.wave) if j.channel == "reddit"]
    posts = [(j.target, j.title, j.body) for j in jobs]
    if not posts:
        print("no reddit jobs in wave")
        return EXIT_BLOCKED
    res = reddit.open_manual_posts(posts)
    print(res.detail)
    append_engine_log("opened manual Reddit submit tabs")
    return EXIT_OK if res.ok else EXIT_BLOCKED


def cmd_queue(args: argparse.Namespace) -> int:
    path = queue_path()
    if args.queue_cmd == "list":
        items = read_queue(path)
        if not items:
            print("(empty queue)")
            return EXIT_OK
        for it in items:
            print(f"{it.id}  {it.status:8}  {it.kind}  {it.payload}")
        return EXIT_OK
    if args.queue_cmd == "add":
        item = QueueItem(
            id=uuid.uuid4().hex[:10],
            kind=args.kind,
            payload={"title": args.title or "", "note": args.note or ""},
        )
        enqueue(path, item)
        print(f"queued {item.id}")
        append_engine_log(f"queued {item.kind} {item.id}")
        return EXIT_OK
    if args.queue_cmd in {"approve", "reject"}:
        ok = set_queue_status(path, args.item_id, "approved" if args.queue_cmd == "approve" else "rejected")
        if not ok:
            print("item not found or not pending")
            return EXIT_BLOCKED
        print(f"{args.queue_cmd}d {args.item_id}")
        append_engine_log(f"{args.queue_cmd} {args.item_id}")
        if args.queue_cmd == "approve":
            print("Approval recorded. Execute the channel action manually or extend adapters.")
        return EXIT_OK
    print("unknown queue command")
    return EXIT_BLOCKED


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mycelium-marketing", description="Mycelium marketing publisher")
    sub = p.add_subparsers(dest="cmd", required=True)

    st = sub.add_parser("status", help="Credential / session readiness")
    st.add_argument("--json", action="store_true")

    d = sub.add_parser("dry-run", help="Parse drafts + simulate posts")
    d.add_argument("--wave", default="launch")
    d.add_argument("--json", action="store_true")

    r = sub.add_parser("run", help="Execute launch wave (live)")
    r.add_argument("--wave", default="launch")
    r.add_argument("--i-understand", action="store_true")
    r.add_argument("--no-sleep", action="store_true", help="Skip stagger sleeps (dev / HUD)")
    r.add_argument("--json", action="store_true")

    sub.add_parser("login-hn", help="Interactive HN session capture")
    sub.add_parser("login-reddit", help="Interactive Reddit session (real Chrome)")
    o = sub.add_parser("open-reddit", help="Manual Reddit: open submit tabs in your browser")
    o.add_argument("--wave", default="launch")

    q = sub.add_parser("queue", help="Approval-gated queue")
    q.add_argument("queue_cmd", choices=["list", "add", "approve", "reject"])
    q.add_argument("item_id", nargs="?")
    q.add_argument("--kind", default="product-hunt")
    q.add_argument("--title", default="")
    q.add_argument("--note", default="")
    q.add_argument("--json", action="store_true")
    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd == "status":
        code = cmd_status(args)
    elif args.cmd == "dry-run":
        code = cmd_dry_run(args)
    elif args.cmd == "run":
        code = cmd_run(args)
    elif args.cmd == "login-hn":
        code = cmd_login_hn(args)
    elif args.cmd == "login-reddit":
        code = cmd_login_reddit(args)
    elif args.cmd == "open-reddit":
        code = cmd_open_reddit(args)
    elif args.cmd == "queue":
        code = cmd_queue(args)
    else:
        code = EXIT_BLOCKED
    raise SystemExit(code)


if __name__ == "__main__":
    main()
