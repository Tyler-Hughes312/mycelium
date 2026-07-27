from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from mycelium_marketing.paths import hn_storage_path


@dataclass(frozen=True)
class SubmitResult:
    ok: bool
    url: str = ""
    detail: str = ""


def status_ready() -> tuple[bool, str]:
    path = hn_storage_path()
    if path.exists():
        user = os.environ.get("HN_USERNAME", "").strip() or "session"
        return True, f"hn storage present ({user})"
    return False, "run login-hn after creating an HN account"


def login_interactive() -> SubmitResult:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return SubmitResult(ok=False, detail="playwright not installed")
    storage = hn_storage_path()
    storage.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://news.ycombinator.com/login", wait_until="domcontentloaded")
        print("Log in to Hacker News in the browser window, then press Enter here…")
        input()
        # Confirm logged in by looking for logout link
        html = page.content()
        if "logout" not in html.lower():
            browser.close()
            return SubmitResult(ok=False, detail="HN login not detected (no logout link)")
        context.storage_state(path=str(storage))
        browser.close()
    return SubmitResult(ok=True, detail=f"saved session → {storage}")


def submit_show_hn(
    *,
    title: str,
    body: str,
    dry_run: bool = True,
) -> SubmitResult:
    if dry_run:
        ready, msg = status_ready()
        detail = msg if ready else f"would post after login-hn ({msg})"
        return SubmitResult(ok=True, url="dry-run://hackernews/show", detail=detail)

    storage = hn_storage_path()
    if not storage.exists():
        return SubmitResult(ok=False, detail="HN session missing — run login-hn")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return SubmitResult(ok=False, detail="playwright not installed")

    # HN "submit" form: title + url OR text. Show HN typically uses URL to repo
    # plus text. Prefer repo URL from body if present.
    url = "https://github.com/Tyler-Hughes312/mycelium"
    for line in body.splitlines():
        if "github.com/Tyler-Hughes312/mycelium" in line:
            url = "https://github.com/Tyler-Hughes312/mycelium"
            break

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(storage_state=str(storage))
            page = context.new_page()
            page.goto("https://news.ycombinator.com/submit", wait_until="domcontentloaded")
            if "login" in page.url or "logout" not in page.content().lower():
                browser.close()
                return SubmitResult(ok=False, detail="HN session expired — re-run login-hn")
            page.fill('input[name="title"]', title)
            page.fill('input[name="url"]', url)
            # text field
            if page.locator('textarea[name="text"]').count():
                page.fill('textarea[name="text"]', body)
            page.click('input[type="submit"]')
            page.wait_for_load_state("domcontentloaded")
            final = page.url
            browser.close()
            if "item?id=" in final:
                return SubmitResult(ok=True, url=final)
            return SubmitResult(ok=True, url=final, detail="submitted (verify URL)")
    except Exception as exc:  # noqa: BLE001
        return SubmitResult(ok=False, detail=str(exc))
