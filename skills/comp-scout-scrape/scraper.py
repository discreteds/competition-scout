"""Minimal Playwright fetcher for competition sites.

This script fetches raw HTML from competition aggregator sites.
Parsing/interpretation is done by Claude in the SKILL.md workflow.

Usage:
    python scraper.py listings              # Fetch all listing pages
    python scraper.py detail URL            # Fetch single competition page
    python scraper.py listing-urls SITE     # Just get URLs from a listing page
"""

import json
import sys
from playwright.sync_api import sync_playwright

SITES = {
    "competitions.com.au": {
        "listing_url": "https://www.competitions.com.au/tag/type/words-or-less-answer/",
        "wait_for": ".card",
    },
    "netrewards.com.au": {
        "listing_url": "https://netrewards.com.au/competitions-category/number-of-words/",
        "wait_for": ".competition-item",
    },
}


def fetch_page(url: str, wait_for: str | None = None) -> dict:
    """Fetch a page and return HTML + text content.

    Args:
        url: URL to fetch
        wait_for: Optional CSS selector to wait for before capturing content

    Returns:
        Dict with url, html, and text fields
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()

        try:
            page.goto(url, wait_until="networkidle", timeout=30000)

            if wait_for:
                try:
                    page.wait_for_selector(wait_for, timeout=10000)
                except:
                    pass  # Continue even if selector not found

            # Scroll to load lazy content
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000)

            html = page.content()
            text = page.inner_text("body")

        finally:
            browser.close()

    return {
        "url": url,
        "html": html,
        "text": text,
    }


def fetch_listing_page(site_name: str) -> dict:
    """Fetch a listing page for a specific site.

    Args:
        site_name: Key from SITES dict

    Returns:
        Dict with site, url, html, and text fields
    """
    config = SITES[site_name]
    result = fetch_page(config["listing_url"], config.get("wait_for"))
    result["site"] = site_name
    return result


def fetch_all_listings() -> dict:
    """Fetch listing pages from all configured sites.

    Returns:
        Dict mapping site name to page content
    """
    results = {}
    for site_name in SITES:
        try:
            results[site_name] = fetch_listing_page(site_name)
        except Exception as e:
            results[site_name] = {"error": str(e), "site": site_name}
    return results


def fetch_competition_detail(url: str) -> dict:
    """Fetch a single competition detail page.

    Args:
        url: Full URL to competition page

    Returns:
        Dict with url, html, and text fields
    """
    # Determine which site this is from
    site = "unknown"
    for site_name in SITES:
        if site_name in url:
            site = site_name
            break

    result = fetch_page(url)
    result["site"] = site
    return result


def main():
    """Entry point - outputs JSON to stdout."""
    if len(sys.argv) < 2:
        print("Usage: python scraper.py [listings|detail URL]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]

    if command == "listings":
        result = fetch_all_listings()
        print(json.dumps(result, indent=2))

    elif command == "detail":
        if len(sys.argv) < 3:
            print("Usage: python scraper.py detail URL", file=sys.stderr)
            sys.exit(1)
        url = sys.argv[2]
        result = fetch_competition_detail(url)
        print(json.dumps(result, indent=2))

    elif command == "listing":
        if len(sys.argv) < 3:
            print("Usage: python scraper.py listing SITE", file=sys.stderr)
            print(f"Available sites: {', '.join(SITES.keys())}", file=sys.stderr)
            sys.exit(1)
        site = sys.argv[2]
        if site not in SITES:
            print(f"Unknown site: {site}", file=sys.stderr)
            print(f"Available sites: {', '.join(SITES.keys())}", file=sys.stderr)
            sys.exit(1)
        result = fetch_listing_page(site)
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print("Usage: python scraper.py [listings|detail URL|listing SITE]", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
