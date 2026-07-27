from __future__ import annotations

from dataclasses import dataclass

from mycelium_marketing.drafts import RedditDraft, ShowHNDraft


@dataclass(frozen=True)
class Job:
    wave_id: str
    channel: str  # hackernews | reddit
    target: str  # show-hn | subreddit name
    delay_minutes: int
    title: str
    body: str


def launch_jobs(
    wave_id: str,
    show: ShowHNDraft,
    reddit: list[RedditDraft],
) -> list[Job]:
    jobs = [
        Job(
            wave_id=wave_id,
            channel="hackernews",
            target="show-hn",
            delay_minutes=0,
            title=show.title,
            body=show.body,
        )
    ]
    # Spec: T+30, T+60, T+90 for the three subs
    for i, draft in enumerate(reddit):
        jobs.append(
            Job(
                wave_id=wave_id,
                channel="reddit",
                target=draft.subreddit,
                delay_minutes=30 * (i + 1),
                title=draft.title,
                body=draft.body,
            )
        )
    return jobs
