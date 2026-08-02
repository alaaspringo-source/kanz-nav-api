"""Shared helper for sources that genuinely need JS execution (confirmed via
diagnostic: Beltone is client-rendered Next.js; AFIM/AAIM serve a JS-driven
bot-challenge interstitial that must run before the real page loads).

This runs Playwright's headless Chromium directly inside the GitHub Actions
runner — no Cloud Run, no external rendering API, no billing dependency.
"""
import logging
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


def fetch_rendered_html(url: str, wait_selector: str = None, wait_ms: int = 6000) -> str | None:
    """Loads a URL in headless Chromium and returns the fully-rendered HTML.

    wait_selector: CSS selector to wait for before grabbing HTML (preferred
    when known — faster and more reliable than a fixed sleep).
    wait_ms: fallback fixed wait if no selector given (used for AFIM/AAIM's
    bot-challenge page, which reloads itself after ~5s with no stable
    selector to wait on beforehand).
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ))
            page.goto(url, timeout=30000)

            if wait_selector:
                page.wait_for_selector(wait_selector, timeout=20000)
            else:
                page.wait_for_timeout(wait_ms)

            html = page.content()
            browser.close()
            return html
    except Exception as e:
        logger.error(f"Playwright fetch failed for {url}: {e}")
        return None
