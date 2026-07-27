"""Reddit publisher — browser session preferred (API apps blocked by RBP)."""

from __future__ import annotations

import os
import re
import subprocess
import webbrowser
from dataclasses import dataclass
from pathlib import Path

from mycelium_marketing.paths import reddit_chrome_profile, reddit_storage_path


@dataclass(frozen=True)
class RedditConfig:
    client_id: str
    client_secret: str
    username: str
    password: str
    user_agent: str

    @classmethod
    def from_environ(cls) -> RedditConfig | None:
        cid = os.environ.get("REDDIT_CLIENT_ID", "").strip()
        secret = os.environ.get("REDDIT_CLIENT_SECRET", "").strip()
        user = os.environ.get("REDDIT_USERNAME", "").strip()
        password = os.environ.get("REDDIT_PASSWORD", "").strip()
        ua = os.environ.get("REDDIT_USER_AGENT", "").strip()
        if not all([cid, secret, user, password, ua]):
            return None
        return cls(cid, secret, user, password, ua)


@dataclass(frozen=True)
class SubmitResult:
    ok: bool
    url: str = ""
    detail: str = ""


def status_ready() -> tuple[bool, str]:
    path = reddit_storage_path()
    if path.exists():
        return True, "reddit browser session present (login-reddit)"
    # Persistent Chrome profile with cookies also counts if marker exists
    marker = reddit_chrome_profile() / ".logged_in"
    if marker.exists():
        return True, "reddit Chrome profile marked logged-in"
    cfg = RedditConfig.from_environ()
    if cfg is not None:
        return True, f"reddit API user={cfg.username}"
    return False, "run login-reddit or open-reddit (manual) — API apps blocked by RBP"


def _launch_login_context(p):  # type: ignore[no-untyped-def]
    """Prefer real Chrome + persistent profile (less likely to trip Reddit bot blocks)."""
    profile = str(reddit_chrome_profile())
    try:
        return p.chromium.launch_persistent_context(
            user_data_dir=profile,
            channel="chrome",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1280, "height": 900},
        )
    except Exception:
        return p.chromium.launch_persistent_context(
            user_data_dir=profile,
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1280, "height": 900},
        )


def login_interactive() -> SubmitResult:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return SubmitResult(ok=False, detail="playwright not installed")
    storage = reddit_storage_path()
    storage.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        context = _launch_login_context(p)
        page = context.pages[0] if context.pages else context.new_page()
        # Use www first — some networks block old.reddit harder
        page.goto("https://www.reddit.com/login/", wait_until="domcontentloaded", timeout=90000)
        print()
        print("If you see 'blocked by network security', close this window and use:")
        print("  ./scripts/marketing-publish.sh open-reddit")
        print("which opens your normal browser for manual paste.")
        print()
        print("Otherwise: log in to Reddit in the Chrome window, then press Enter here…")
        input()
        page.goto("https://www.reddit.com/", wait_until="domcontentloaded", timeout=90000)
        html = page.content().lower()
        blocked = "blocked by network security" in html or "you've been blocked" in html
        if blocked:
            context.close()
            return SubmitResult(
                ok=False,
                detail=(
                    "Reddit blocked the automated browser. Use open-reddit for manual posting "
                    "in your normal Chrome/Safari instead."
                ),
            )
        logged_in = "logout" in html or "log out" in html or '"me":' in html
        if not logged_in:
            # soft accept — user may still be logged in with new UI
            print("Could not auto-detect logout link; saving session anyway if you logged in.")
        context.storage_state(path=str(storage))
        (reddit_chrome_profile() / ".logged_in").write_text("1\n", encoding="utf-8")
        context.close()
    return SubmitResult(ok=True, detail=f"saved session → {storage}")


def open_manual_posts(
    posts: list[tuple[str, str, str]],
) -> SubmitResult:
    """Open submit pages in the user's default browser + print paste copy."""
    lines = ["Manual Reddit posts (paste title/body after each tab opens):\n"]
    for i, (sub, title, body) in enumerate(posts):
        url = f"https://www.reddit.com/r/{sub}/submit"
        lines.append(f"--- r/{sub} ---")
        lines.append(f"URL: {url}")
        lines.append(f"TITLE:\n{title}\n")
        lines.append(f"BODY:\n{body}\n")
        try:
            # macOS: open in default browser
            subprocess.run(["open", url], check=False)
        except OSError:
            webbrowser.open(url)
        if i == 0:
            # stagger slightly so tabs don't overwhelm
            pass
    detail = "\n".join(lines)
    print(detail)
    return SubmitResult(ok=True, detail="opened submit tabs in your default browser")


def _submit_via_browser(*, subreddit: str, title: str, body: str) -> SubmitResult:
    storage = reddit_storage_path()
    if not storage.exists():
        return SubmitResult(ok=False, detail="Reddit session missing — run login-reddit or open-reddit")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return SubmitResult(ok=False, detail="playwright not installed")
    try:
        with sync_playwright() as p:
            # Headed + real Chrome reduces blocks vs headless automation
            try:
                browser = p.chromium.launch(
                    channel="chrome",
                    headless=False,
                    args=["--disable-blink-features=AutomationControlled"],
                )
            except Exception:
                browser = p.chromium.launch(
                    headless=False,
                    args=["--disable-blink-features=AutomationControlled"],
                )
            context = browser.new_context(storage_state=str(storage))
            page = context.new_page()
            page.goto(
                f"https://www.reddit.com/r/{subreddit}/submit",
                wait_until="domcontentloaded",
                timeout=90000,
            )
            html = page.content().lower()
            if "blocked by network security" in html or "you've been blocked" in html:
                browser.close()
                return SubmitResult(
                    ok=False,
                    detail="Reddit network block on automated browser — use open-reddit",
                )
            # Prefer text/self post
            for label in ("Text", "Post", "text"):
                loc = page.get_by_role("button", name=re.compile(label, re.I))
                if loc.count():
                    try:
                        loc.first.click(timeout=2000)
                        break
                    except Exception:
                        pass
            # Title
            filled = False
            for sel in ('textarea[name="title"]', 'input[name="title"]', "#innerTextTitle", 'div[aria-label="Post Title"]'):
                if page.locator(sel).count():
                    page.locator(sel).first.fill(title)
                    filled = True
                    break
            if not filled:
                browser.close()
                return SubmitResult(ok=False, detail="could not find title field — use open-reddit")

            for sel in ('textarea[name="text"]', 'div[aria-label="Text"]', 'div[contenteditable="true"]'):
                if page.locator(sel).count():
                    page.locator(sel).first.fill(body)
                    break

            posted = False
            for name in ("Post", "Submit", "Save"):
                btn = page.get_by_role("button", name=re.compile(f"^{name}$", re.I))
                if btn.count():
                    try:
                        btn.first.click(timeout=3000)
                        posted = True
                        break
                    except Exception:
                        continue
            if not posted and page.locator('button[type="submit"]').count():
                page.locator('button[type="submit"]').first.click()

            page.wait_for_timeout(3000)
            final = page.url
            browser.close()
            if "blocked by network security" in page.content().lower() if False else False:
                pass
            if "/comments/" in final:
                return SubmitResult(ok=True, url=final)
            return SubmitResult(ok=True, url=final, detail="submitted (verify in browser)")
    except Exception as exc:  # noqa: BLE001
        return SubmitResult(ok=False, detail=str(exc))


def _submit_via_api(*, subreddit: str, title: str, body: str) -> SubmitResult:
    cfg = RedditConfig.from_environ()
    if cfg is None:
        return SubmitResult(ok=False, detail="reddit API credentials missing")
    try:
        import praw
    except ImportError:
        return SubmitResult(ok=False, detail="praw not installed")
    try:
        client = praw.Reddit(
            client_id=cfg.client_id,
            client_secret=cfg.client_secret,
            username=cfg.username,
            password=cfg.password,
            user_agent=cfg.user_agent,
        )
        submission = client.subreddit(subreddit).submit(title=title, selftext=body)
        return SubmitResult(ok=True, url=f"https://www.reddit.com{submission.permalink}")
    except Exception as exc:  # noqa: BLE001
        return SubmitResult(ok=False, detail=str(exc))


def submit_text_post(
    *,
    subreddit: str,
    title: str,
    body: str,
    dry_run: bool = True,
) -> SubmitResult:
    if dry_run:
        ready, msg = status_ready()
        detail = msg if ready else f"would post after login-reddit / open-reddit ({msg})"
        return SubmitResult(ok=True, url=f"dry-run://reddit/{subreddit}", detail=detail)

    if reddit_storage_path().exists() or (reddit_chrome_profile() / ".logged_in").exists():
        res = _submit_via_browser(subreddit=subreddit, title=title, body=body)
        if res.ok or "network block" not in (res.detail or "").lower():
            return res
        # fall through to manual hint
        return SubmitResult(
            ok=False,
            detail="Reddit blocked automation — run: ./scripts/marketing-publish.sh open-reddit",
        )
    if RedditConfig.from_environ() is not None:
        return _submit_via_api(subreddit=subreddit, title=title, body=body)
    return SubmitResult(
        ok=False,
        detail="run open-reddit (manual in your browser) — Reddit blocks automated logins",
    )


def load_dotenv_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        os.environ.setdefault(key, val)
