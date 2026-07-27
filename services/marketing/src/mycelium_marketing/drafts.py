from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ShowHNDraft:
    title: str
    body: str


@dataclass(frozen=True)
class RedditDraft:
    subreddit: str
    title: str
    body: str


_FENCE = re.compile(r"```(?:\w*)\n(.*?)```", re.DOTALL)
_SUB_HEADER = re.compile(r"^##\s+(.+)$", re.MULTILINE)


def _fenced_blocks(text: str) -> list[str]:
    return [m.group(1).strip() for m in _FENCE.finditer(text)]


def parse_show_hn(path: Path) -> ShowHNDraft:
    text = path.read_text(encoding="utf-8")
    blocks = _fenced_blocks(text)
    if len(blocks) < 2:
        raise ValueError(f"show-hn draft needs title + body fences: {path}")
    title, body = blocks[0], blocks[1]
    if not title.lower().startswith("show hn"):
        title = f"Show HN: {title}"
    return ShowHNDraft(title=title, body=body)


def _subs_from_header(header: str) -> list[str]:
    # "r/LocalLLaMA / r/ClaudeAI / r/cursor" or "r/selfhosted (optional)"
    header = re.sub(r"\(.*?\)", "", header).strip()
    parts = re.split(r"\s*/\s*|\s*,\s*", header)
    subs: list[str] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        m = re.search(r"(?:r/)?([A-Za-z0-9_]+)", part)
        if m:
            subs.append(m.group(1))
    return subs


def parse_reddit(path: Path) -> list[RedditDraft]:
    text = path.read_text(encoding="utf-8")
    # Split on ## headers; skip title-only "# Reddit drafts"
    sections = _SUB_HEADER.split(text)
    # sections[0] is preamble; then header, body, header, body...
    drafts: list[RedditDraft] = []
    i = 1
    while i + 1 < len(sections):
        header = sections[i].strip()
        body_md = sections[i + 1]
        i += 2
        if header.lower().startswith("rules"):
            continue
        blocks = _fenced_blocks(body_md)
        if len(blocks) < 2:
            continue  # optional stubs without real fences
        title, body = blocks[0], blocks[1]
        for sub in _subs_from_header(header):
            drafts.append(RedditDraft(subreddit=sub, title=title, body=body))
    return drafts


def load_launch_drafts(drafts: Path) -> tuple[ShowHNDraft, list[RedditDraft]]:
    show = parse_show_hn(drafts / "show-hn.md")
    reddit = parse_reddit(drafts / "reddit.md")
    wanted = {"LocalLLaMA", "cursor", "ClaudeAI"}
    reddit = [d for d in reddit if d.subreddit in wanted]
    # stable order
    order = ["LocalLLaMA", "cursor", "ClaudeAI"]
    reddit.sort(key=lambda d: order.index(d.subreddit) if d.subreddit in order else 99)
    return show, reddit
