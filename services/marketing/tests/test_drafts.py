from pathlib import Path

from mycelium_marketing.drafts import load_launch_drafts, parse_reddit, parse_show_hn


ROOT = Path(__file__).resolve().parents[3]
DRAFTS = ROOT / "docs" / "marketing" / "drafts"


def test_parse_show_hn():
    draft = parse_show_hn(DRAFTS / "show-hn.md")
    assert draft.title.startswith("Show HN:")
    assert "Mycelium" in draft.body
    assert "github.com/Tyler-Hughes312/mycelium" in draft.body


def test_parse_reddit_expands_subs():
    drafts = parse_reddit(DRAFTS / "reddit.md")
    subs = {d.subreddit for d in drafts}
    assert {"LocalLLaMA", "cursor", "ClaudeAI"} <= subs


def test_load_launch_drafts_order():
    show, reddit = load_launch_drafts(DRAFTS)
    assert show.title
    assert [d.subreddit for d in reddit] == ["LocalLLaMA", "cursor", "ClaudeAI"]
