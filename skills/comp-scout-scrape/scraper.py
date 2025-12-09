"""Competition scraper with full extraction logic.

Scrapes competition aggregator sites and returns structured JSON data.
Uses Playwright (sync) for JS-rendered pages.

Usage:
    python scraper.py listings              # Scrape all listing pages, return structured data
    python scraper.py detail URL            # Scrape single competition page
    python scraper.py details-batch         # Fetch full details for multiple URLs (reads JSON from stdin)
    python scraper.py urls                  # Just list competition URLs (for debugging)

Batch details example:
    echo '{"urls": ["url1", "url2"]}' | python scraper.py details-batch
"""

import json
import re
import sys
from datetime import date, datetime
from playwright.sync_api import sync_playwright, Page

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


# =============================================================================
# Helper Functions
# =============================================================================

def _parse_closing_date(text: str) -> str | None:
    """Parse a closing date from various text formats.

    Args:
        text: Text potentially containing a date.

    Returns:
        Date as YYYY-MM-DD string, or None if unparseable.
    """
    if not text:
        return None

    month_map = {
        "jan": 1, "january": 1,
        "feb": 2, "february": 2,
        "mar": 3, "march": 3,
        "apr": 4, "april": 4,
        "may": 5,
        "jun": 6, "june": 6,
        "jul": 7, "july": 7,
        "aug": 8, "august": 8,
        "sep": 9, "september": 9,
        "oct": 10, "october": 10,
        "nov": 11, "november": 11,
        "dec": 12, "december": 12,
    }

    month_pattern = r"(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"

    # Try US format: "January 5, 2024", "Jan 5, 2024"
    us_pattern = month_pattern + r"\s+(\d{1,2}),?\s+(\d{4})"
    match = re.search(us_pattern, text, re.IGNORECASE)
    if match:
        month = month_map.get(match.group(1).lower()[:3], 1)
        day = int(match.group(2))
        year = int(match.group(3))
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            pass

    # Try UK format: "5 January 2024", "5 Jan 2024"
    uk_pattern = r"(\d{1,2})\s+" + month_pattern + r"\s+(\d{4})"
    match = re.search(uk_pattern, text, re.IGNORECASE)
    if match:
        day = int(match.group(1))
        month = month_map.get(match.group(2).lower()[:3], 1)
        year = int(match.group(3))
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            pass

    # Try ISO format: "2024-12-31"
    iso_pattern = r"(\d{4})-(\d{2})-(\d{2})"
    match = re.search(iso_pattern, text)
    if match:
        try:
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3))).isoformat()
        except ValueError:
            pass

    # Try AU/UK numeric: "31/12/2024" or "31-12-2024"
    numeric_pattern = r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})"
    match = re.search(numeric_pattern, text)
    if match:
        try:
            return date(int(match.group(3)), int(match.group(2)), int(match.group(1))).isoformat()
        except ValueError:
            pass

    return None


def _extract_word_limit(text: str) -> int:
    """Extract word limit from text.

    Args:
        text: Full page text to search.

    Returns:
        Word limit found, defaults to 25.
    """
    # Look for patterns like "25 words or less", "in 25 words", etc.
    patterns = [
        r"(\d+)\s*words?\s*or\s*less",
        r"in\s*(\d+)\s*words?",
        r"(\d+)\s*word\s*limit",
        r"maximum\s*(\d+)\s*words?",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            limit = int(match.group(1))
            if 1 <= limit <= 100:  # Sanity check
                return limit

    return 25  # Default


def _extract_prompt_from_text(text: str) -> str:
    """Try to extract the competition prompt from full page text.

    Args:
        text: Full page text.

    Returns:
        Extracted prompt or empty string.
    """
    # Look for common prompt patterns
    patterns = [
        r"tell us .*? in \d+ words or less[.!?]?",
        r"in \d+ words or less,? .*?[.!?]",
        r"complete the sentence[:\s]+[\"']?.*?[\"']?",
        r"answer the question[:\s]+[\"']?.*?[\"']?",
        r"why do you .*?\?",
        r"what makes .*?\?",
        r"describe .*? in \d+ words",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            # Return the matched text, cleaned up
            prompt = match.group(0).strip()
            # Capitalize first letter
            return prompt[0].upper() + prompt[1:] if prompt else ""

    return ""


def extract_winner_notification(html: str) -> dict | None:
    """Extract winner notification info from competitions.com.au FAQ JSON-LD.

    Looks for FAQPage structured data with questions about winner notification
    and selection dates.

    Args:
        html: Full HTML content of the page.

    Returns:
        Dict with notification info if found, None otherwise.
    """
    # Find all JSON-LD script blocks
    pattern = r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>'
    matches = re.findall(pattern, html, re.DOTALL)

    notification_text = ""
    notification_date = None
    notification_days = None
    selection_text = ""
    selection_date = None

    for match in matches:
        try:
            data = json.loads(match)
            if data.get("@type") != "FAQPage":
                continue

            for q in data.get("mainEntity", []):
                name = q.get("name", "").lower()
                text = q.get("acceptedAnswer", {}).get("text", "")

                if "notified" in name or "notification" in name:
                    notification_text = text
                    # Try to extract specific date
                    notification_date = _parse_closing_date(text)
                    # Try to extract relative days ("within X days")
                    days_match = re.search(
                        r"within\s+(\w+)\s+(?:business\s+)?days?",
                        text,
                        re.IGNORECASE,
                    )
                    if days_match:
                        day_word = days_match.group(1).lower()
                        word_to_num = {
                            "one": 1, "two": 2, "three": 3, "four": 4,
                            "five": 5, "six": 6, "seven": 7, "eight": 8,
                            "nine": 9, "ten": 10,
                        }
                        if day_word.isdigit():
                            notification_days = int(day_word)
                        else:
                            notification_days = word_to_num.get(day_word)

                elif "selected" in name or "selection" in name:
                    selection_text = text
                    # Try to extract selection date
                    selection_date = _parse_closing_date(text)

        except json.JSONDecodeError:
            continue

    # Only return if we found something
    if notification_text or selection_text:
        return {
            "notification_text": notification_text,
            "notification_date": notification_date,
            "notification_days": notification_days,
            "selection_text": selection_text,
            "selection_date": selection_date,
        }

    return None


def normalize_title(title: str) -> str:
    """Normalize a competition title for matching.

    Removes common prefixes, punctuation, and normalizes whitespace.

    Args:
        title: Raw competition title.

    Returns:
        Normalized title string for comparison.
    """
    # Lowercase
    normalized = title.lower()
    # Remove common prefixes
    for prefix in ["win ", "win a ", "win an ", "win the ", "win 1 of ", "win one of "]:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):]
            break
    # Remove punctuation and extra whitespace
    normalized = re.sub(r"[^\w\s]", " ", normalized)
    normalized = " ".join(normalized.split())
    return normalized


def extract_prize_value(prize_text: str) -> int | None:
    """Extract numeric prize value from text.

    Args:
        prize_text: Prize description text.

    Returns:
        Integer value in dollars, or None if not found.
    """
    if not prize_text:
        return None
    # Look for $XX,XXX patterns
    match = re.search(r"\$\s*([\d,]+)", prize_text)
    if match:
        try:
            return int(match.group(1).replace(",", ""))
        except ValueError:
            pass
    return None


# =============================================================================
# Site-Specific Extraction: competitions.com.au
# =============================================================================

def extract_competitions_com_au_listings(page: Page) -> list[dict]:
    """Extract competitions from competitions.com.au listing page.

    Args:
        page: Playwright page already navigated to the listing.

    Returns:
        List of competition dicts with extracted data.
    """
    # Extract competition data using JavaScript
    competitions = page.evaluate(
        """
        () => {
            const cards = document.querySelectorAll('.card');
            const results = [];

            for (const card of cards) {
                // Skip sponsored/exit cards
                if (card.querySelector('a[href*="/exit/"]')) continue;

                // Must have words-or-less tag
                if (!card.textContent.toLowerCase().includes('words or less')) continue;

                // Find the actual competition link
                const detailLink = card.querySelector('a.loadcomp, a[href*="/win-"], a[href*="/competition/"]');
                if (!detailLink || !detailLink.href) continue;

                // Get title from h2 or h5
                const titleEl = card.querySelector('h2 a, h2, h5');
                const title = titleEl?.textContent?.trim() || '';

                // Get prize from badge
                const prizeEl = card.querySelector('.badge-success, [class*="prize"]');
                const prize = prizeEl?.textContent?.trim() || '';

                // Get closing date - look for "Ends Jan 5, 2026", "X days left", or "Ends Today"
                let closingText = '';
                const fullDateMatch = card.textContent.match(/Ends?\\s+(\\w+\\s+\\d{1,2},?\\s*\\d{4})/i);
                const shortDateMatch = card.textContent.match(/Ends?\\s+(\\w+\\s+\\d{1,2})(?![,\\d])/i);
                const daysLeftMatch = card.textContent.match(/(\\d+)\\s+days?\\s+left/i);
                const endsTodayMatch = card.textContent.match(/Ends?\\s+Today/i);

                if (fullDateMatch) {
                    closingText = fullDateMatch[1];
                } else if (endsTodayMatch) {
                    // Today
                    const today = new Date();
                    closingText = today.toLocaleDateString('en-AU', {day: 'numeric', month: 'long', year: 'numeric'});
                } else if (daysLeftMatch) {
                    // Convert "X days left" to actual date
                    const daysLeft = parseInt(daysLeftMatch[1]);
                    const closeDate = new Date();
                    closeDate.setDate(closeDate.getDate() + daysLeft);
                    closingText = closeDate.toLocaleDateString('en-AU', {day: 'numeric', month: 'long', year: 'numeric'});
                } else if (shortDateMatch) {
                    // Add current year if no year provided, handle year rollover
                    const monthDay = shortDateMatch[1];
                    const now = new Date();
                    let year = now.getFullYear();
                    // If the date looks like it's in the past (e.g., Jan when we're in Dec), use next year
                    const monthMatch = monthDay.match(/^(Jan|Feb|Mar)/i);
                    if (monthMatch && now.getMonth() >= 10) {
                        year = now.getFullYear() + 1;
                    }
                    closingText = monthDay + ', ' + year;
                }

                // Get brand
                const brandEl = card.querySelector('a[href*="/tag/brand/"]');
                const brand = brandEl?.textContent?.trim() || '';

                results.push({
                    url: detailLink.href,
                    title: title,
                    prize_summary: prize,
                    closing_text: closingText,
                    brand: brand
                });
            }

            return results;
        }
        """
    )

    results = []
    for comp in competitions:
        closing_date = _parse_closing_date(comp.get("closing_text", ""))
        prize_value = extract_prize_value(comp.get("prize_summary", ""))

        results.append({
            "url": comp["url"],
            "site": "competitions.com.au",
            "title": comp["title"],
            "normalized_title": normalize_title(comp["title"]),
            "brand": comp.get("brand", ""),
            "prize_summary": comp.get("prize_summary", ""),
            "prize_value": prize_value,
            "closing_date": closing_date,
        })

    return results


def extract_competitions_com_au_detail(page: Page, url: str) -> dict:
    """Extract full details from a competitions.com.au competition page.

    Args:
        page: Playwright page already navigated to the competition.
        url: URL of the competition.

    Returns:
        Dict with full competition details.
    """
    # Get raw HTML for JSON-LD extraction
    html = page.content()
    winner_notification = extract_winner_notification(html)

    # Extract content using JavaScript
    content = page.evaluate(
        """
        () => {
            // Remove scripts/styles for cleaner text
            document.querySelectorAll('script, style, noscript').forEach(el => el.remove());

            // Get clean text from main content
            const main = document.querySelector('main, article, .content, #content');
            const mainText = (main || document.body).innerText || '';

            // Title from h1
            const title = document.querySelector('h1')?.innerText?.trim() || '';

            // Find the prompt - look for patterns like "in X words or less"
            let prompt = '';
            const promptPatterns = [
                /(?:tell us|share|describe|explain|complete)[^.]*?(?:\\d+\\s*words[^.]*)/i,
                /(?:in \\d+ words or less)[^.]*\\./i,
                /(?:answer|entry)[^.]*?\\d+\\s*words[^.]*/i
            ];
            for (const pattern of promptPatterns) {
                const match = mainText.match(pattern);
                if (match) {
                    prompt = match[0].trim();
                    break;
                }
            }

            // Find closing date
            let closing = '';
            const closingMatch = mainText.match(/(?:closes?|ends?|closing)[:\\s]*([^\\n]+)/i);
            if (closingMatch) {
                closing = closingMatch[1].trim();
            }

            // Find prize value
            let prize = '';
            const prizeMatch = mainText.match(/(?:prize pool|total prize|worth|valued at)[:\\s]*\\$?([\\d,]+)/i);
            if (prizeMatch) {
                prize = '$' + prizeMatch[1];
            }

            // Find brand from breadcrumb or link
            const brandEl = document.querySelector('a[href*="/tag/brand/"]');
            const brand = brandEl?.innerText?.trim() || '';

            // Entry method
            let method = '';
            const methodMatch = mainText.match(/(?:how to enter|to enter)[:\\s]*([^.]+\\.)/i);
            if (methodMatch) {
                method = methodMatch[1].trim();
            }

            return {
                title: title,
                prize: prize,
                prompt: prompt,
                closing: closing,
                method: method,
                brand: brand,
                full_text: mainText.substring(0, 10000),
            };
        }
        """
    )

    # Parse extracted data
    closing_date = _parse_closing_date(content.get("closing", ""))
    word_limit = _extract_word_limit(content.get("full_text", ""))
    prize_value = extract_prize_value(content.get("prize", ""))

    # If prompt wasn't found, try Python extraction
    prompt = content.get("prompt", "")
    if not prompt:
        prompt = _extract_prompt_from_text(content.get("full_text", ""))

    return {
        "url": url,
        "site": "competitions.com.au",
        "title": content.get("title", "Unknown Competition"),
        "normalized_title": normalize_title(content.get("title", "")),
        "brand": content.get("brand", ""),
        "prize_summary": content.get("prize", ""),
        "prize_value": prize_value,
        "prompt": prompt,
        "word_limit": word_limit,
        "closing_date": closing_date,
        "entry_method": content.get("method", ""),
        "winner_notification": winner_notification,
        "scraped_at": datetime.now().isoformat(),
    }


# =============================================================================
# Site-Specific Extraction: netrewards.com.au
# =============================================================================

def extract_netrewards_listings(page: Page) -> list[dict]:
    """Extract competitions from netrewards.com.au listing page.

    Args:
        page: Playwright page already navigated to the listing.

    Returns:
        List of competition dicts with extracted data.
    """
    competitions = page.evaluate(
        """
        () => {
            // Find all internal detail page links
            const links = document.querySelectorAll('a[href*="netrewards.com.au/competitions/"]');
            const results = [];
            const seen = new Set();

            for (const link of links) {
                const href = link.href;
                if (seen.has(href) || !href.includes('/competitions/')) continue;
                seen.add(href);

                // Find parent container with competition info
                let container = link.parentElement;
                for (let i = 0; i < 5 && container; i++) {
                    if (container.innerText && container.innerText.includes('Prize Value')) break;
                    container = container.parentElement;
                }

                const text = container?.innerText || '';

                // Extract title - look for "Win..." pattern
                const titleMatch = text.match(/Win[^\\n]+/i);
                const title = titleMatch ? titleMatch[0].trim() : '';

                // Extract prize value
                const prizeMatch = text.match(/Prize Value:\\s*\\$([\\d,]+)/);
                const prize = prizeMatch ? '$' + prizeMatch[1] : '';

                // Extract end date (format: "30 12 25" - DD MM YY)
                const endsMatch = text.match(/Ends:\\s*(\\d{1,2})\\s+(\\d{1,2})\\s+(\\d{2})/);
                let closingText = '';
                if (endsMatch) {
                    closingText = `${endsMatch[1]}/${endsMatch[2]}/20${endsMatch[3]}`;
                }

                if (title) {
                    results.push({
                        url: href,
                        title: title,
                        prize_summary: prize,
                        closing_text: closingText
                    });
                }
            }

            return results;
        }
        """
    )

    results = []
    for comp in competitions:
        closing_date = _parse_closing_date(comp.get("closing_text", ""))
        prize_value = extract_prize_value(comp.get("prize_summary", ""))

        results.append({
            "url": comp["url"],
            "site": "netrewards.com.au",
            "title": comp["title"],
            "normalized_title": normalize_title(comp["title"]),
            "brand": "",  # Not available in listing
            "prize_summary": comp.get("prize_summary", ""),
            "prize_value": prize_value,
            "closing_date": closing_date,
        })

    return results


def extract_netrewards_detail(page: Page, url: str) -> dict:
    """Extract full details from a netrewards.com.au competition page.

    Args:
        page: Playwright page already navigated to the competition.
        url: URL of the competition.

    Returns:
        Dict with full competition details.
    """
    content = page.evaluate(
        """
        () => {
            document.querySelectorAll('script, style').forEach(el => el.remove());
            const text = document.body.innerText;

            // Title - look for "Win..." in the content
            const titleMatch = text.match(/Win[^\\n]+/i);
            const title = titleMatch ? titleMatch[0].trim() : '';

            // Prompt - look for "TO ENTER:" section or word limit patterns
            let prompt = '';
            const toEnterMatch = text.match(/TO ENTER:\\s*([^\\n]+)/i);
            if (toEnterMatch) {
                prompt = toEnterMatch[1].trim();
            } else {
                const promptMatch = text.match(/(?:tell us|in \\d+ words or less)[^.?!]*[.?!]/i);
                if (promptMatch) prompt = promptMatch[0].trim();
            }

            // Prize value
            const prizeMatch = text.match(/Prize Value:\\s*\\$([\\d,]+)/);
            const prize = prizeMatch ? '$' + prizeMatch[1] : '';

            // End date (format: "30 12 25" - DD MM YY)
            const endsMatch = text.match(/Ends:\\s*(\\d{1,2})\\s+(\\d{1,2})\\s+(\\d{2})/);
            let closing = '';
            if (endsMatch) {
                closing = `${endsMatch[1]}/${endsMatch[2]}/20${endsMatch[3]}`;
            }

            // Brand - appears before the title usually
            const brandMatch = text.match(/^([A-Za-z][A-Za-z\\s&-]+)\\s*(?:\\||\\n)/m);
            const brand = brandMatch ? brandMatch[1].trim() : '';

            return {
                title: title,
                prompt: prompt,
                prize: prize,
                closing: closing,
                brand: brand,
                full_text: text.substring(0, 10000)
            };
        }
        """
    )

    closing_date = _parse_closing_date(content.get("closing", ""))
    word_limit = _extract_word_limit(content.get("full_text", ""))
    prize_value = extract_prize_value(content.get("prize", ""))

    prompt = content.get("prompt", "")
    if not prompt:
        prompt = _extract_prompt_from_text(content.get("full_text", ""))

    return {
        "url": url,
        "site": "netrewards.com.au",
        "title": content.get("title", "Unknown Competition"),
        "normalized_title": normalize_title(content.get("title", "")),
        "brand": content.get("brand", ""),
        "prize_summary": content.get("prize", ""),
        "prize_value": prize_value,
        "prompt": prompt,
        "word_limit": word_limit,
        "closing_date": closing_date,
        "entry_method": "",
        "winner_notification": None,  # netrewards doesn't have JSON-LD
        "scraped_at": datetime.now().isoformat(),
    }


# =============================================================================
# Main Scraping Functions
# =============================================================================

def scrape_listings() -> dict:
    """Scrape all listing pages and return structured competition data.

    Returns:
        Dict with competitions list, scrape_date, and errors.
    """
    all_competitions = []
    errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Scrape competitions.com.au
        try:
            print("Scraping competitions.com.au...", file=sys.stderr)
            page.goto(SITES["competitions.com.au"]["listing_url"], wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector(SITES["competitions.com.au"]["wait_for"], timeout=30000)

            # Scroll to load more content
            for _ in range(3):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1000)

            listings = extract_competitions_com_au_listings(page)
            all_competitions.extend(listings)
            print(f"  Found {len(listings)} competitions", file=sys.stderr)
        except Exception as e:
            errors.append({"site": "competitions.com.au", "error": str(e)})
            print(f"  Error: {e}", file=sys.stderr)

        # Scrape netrewards.com.au
        try:
            print("Scraping netrewards.com.au...", file=sys.stderr)
            page.goto(SITES["netrewards.com.au"]["listing_url"], wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2000)  # Let content load

            listings = extract_netrewards_listings(page)
            all_competitions.extend(listings)
            print(f"  Found {len(listings)} competitions", file=sys.stderr)
        except Exception as e:
            errors.append({"site": "netrewards.com.au", "error": str(e)})
            print(f"  Error: {e}", file=sys.stderr)

        browser.close()

    # Deduplicate by normalized title (keep first occurrence)
    seen_titles = set()
    unique_competitions = []
    for comp in all_competitions:
        norm_title = comp.get("normalized_title", "")[:40]
        if norm_title and norm_title not in seen_titles:
            seen_titles.add(norm_title)
            unique_competitions.append(comp)

    print(f"Total unique: {len(unique_competitions)} competitions", file=sys.stderr)

    return {
        "competitions": unique_competitions,
        "scrape_date": date.today().isoformat(),
        "errors": errors,
    }


def scrape_detail(url: str) -> dict:
    """Scrape a single competition detail page.

    Args:
        url: URL of the competition page.

    Returns:
        Dict with full competition details.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)  # Allow content to render

        # Route to appropriate extractor
        if "netrewards.com.au" in url:
            result = extract_netrewards_detail(page, url)
        else:
            result = extract_competitions_com_au_detail(page, url)

        browser.close()

    return result


def scrape_details_batch(urls: list[str]) -> dict:
    """Scrape full details for multiple competition URLs.

    Reuses browser context for efficiency when fetching many pages.

    Args:
        urls: List of competition URLs to scrape.

    Returns:
        Dict with details list, scrape_date, and errors.
    """
    details = []
    errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        for url in urls:
            try:
                print(f"Fetching: {url}", file=sys.stderr)
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(2000)  # Allow content to render

                # Route to appropriate extractor
                if "netrewards.com.au" in url:
                    result = extract_netrewards_detail(page, url)
                else:
                    result = extract_competitions_com_au_detail(page, url)

                details.append(result)
            except Exception as e:
                errors.append({"url": url, "error": str(e)})
                print(f"  Error: {e}", file=sys.stderr)

        browser.close()

    print(f"Fetched {len(details)} details, {len(errors)} errors", file=sys.stderr)

    return {
        "details": details,
        "scrape_date": date.today().isoformat(),
        "errors": errors,
    }


def scrape_urls() -> dict:
    """Just get competition URLs from listing pages (for debugging).

    Returns:
        Dict mapping site names to URL lists.
    """
    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()

        for site_name, config in SITES.items():
            try:
                page.goto(config["listing_url"], wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(2000)

                if site_name == "competitions.com.au":
                    listings = extract_competitions_com_au_listings(page)
                else:
                    listings = extract_netrewards_listings(page)

                results[site_name] = [c["url"] for c in listings]
            except Exception as e:
                results[site_name] = {"error": str(e)}

        browser.close()

    return results


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """Entry point - outputs JSON to stdout."""
    if len(sys.argv) < 2:
        print("Usage: python scraper.py [listings|detail URL|details-batch|urls]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]

    if command == "listings":
        result = scrape_listings()
        print(json.dumps(result, indent=2))

    elif command == "detail":
        if len(sys.argv) < 3:
            print("Usage: python scraper.py detail URL", file=sys.stderr)
            sys.exit(1)
        url = sys.argv[2]
        result = scrape_detail(url)
        print(json.dumps(result, indent=2))

    elif command == "details-batch":
        # Read URLs from stdin as JSON: {"urls": ["url1", "url2", ...]}
        try:
            input_data = json.loads(sys.stdin.read())
            urls = input_data.get("urls", [])
            if not urls:
                print("No URLs provided. Expected JSON: {\"urls\": [...]}", file=sys.stderr)
                sys.exit(1)
            result = scrape_details_batch(urls)
            print(json.dumps(result, indent=2))
        except json.JSONDecodeError as e:
            print(f"Invalid JSON input: {e}", file=sys.stderr)
            sys.exit(1)

    elif command == "urls":
        result = scrape_urls()
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print("Usage: python scraper.py [listings|detail URL|details-batch|urls]", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
