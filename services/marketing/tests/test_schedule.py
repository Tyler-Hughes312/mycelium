from mycelium_marketing.drafts import RedditDraft, ShowHNDraft
from mycelium_marketing.schedule import launch_jobs


def test_launch_jobs_stagger():
    show = ShowHNDraft(title="Show HN: X", body="body")
    reddit = [
        RedditDraft("LocalLLaMA", "t", "I built x"),
        RedditDraft("cursor", "t", "I built x"),
        RedditDraft("ClaudeAI", "t", "I built x"),
    ]
    jobs = launch_jobs("launch", show, reddit)
    assert jobs[0].channel == "hackernews" and jobs[0].delay_minutes == 0
    assert [j.delay_minutes for j in jobs[1:]] == [30, 60, 90]
    assert [j.target for j in jobs[1:]] == ["LocalLLaMA", "cursor", "ClaudeAI"]
