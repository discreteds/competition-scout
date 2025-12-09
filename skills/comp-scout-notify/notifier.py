"""Email notification for competition digest.

Queries GitHub issues, formats, and sends digest emails via SMTP.

Usage:
    python notifier.py send                    # Send digest email
    python notifier.py preview                 # Save HTML/TXT to /tmp for preview
    python notifier.py json                    # Output digest as JSON

Environment variables required for sending:
    SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD
    EMAIL_TO (comma-separated), EMAIL_FROM

    TARGET_REPO (e.g., "discreteds/competition-data")
"""

import json
import os
import re
import smtplib
import subprocess
import sys
from datetime import date, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path


# =============================================================================
# GitHub Issue Queries
# =============================================================================

def get_target_repo() -> str:
    """Get target repository from environment or config."""
    # Try environment variable first
    if os.environ.get("TARGET_REPO"):
        return os.environ["TARGET_REPO"]

    # Try hiivmind config
    config_path = Path(".hiivmind/github/config.yaml")
    if config_path.exists():
        try:
            result = subprocess.run(
                ["yq", ".repositories[0].full_name", str(config_path)],
                capture_output=True, text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except FileNotFoundError:
            pass

    # Default fallback
    return "discreteds/competition-data"


def query_competition_issues(repo: str) -> list[dict]:
    """Query open competition issues from GitHub.

    Args:
        repo: Repository in owner/name format.

    Returns:
        List of issue dicts with number, title, body, labels, comments.
    """
    # Get issues with competition label
    result = subprocess.run(
        [
            "gh", "issue", "list",
            "-R", repo,
            "--label", "competition",
            "--state", "open",
            "--json", "number,title,body,labels,url,createdAt",
            "--limit", "100"
        ],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print(f"Error querying issues: {result.stderr}", file=sys.stderr)
        return []

    issues = json.loads(result.stdout) if result.stdout else []

    # Get comments for each issue (for strategy/entries)
    for issue in issues:
        comments_result = subprocess.run(
            [
                "gh", "api",
                f"repos/{repo}/issues/{issue['number']}/comments",
                "--jq", ".[].body"
            ],
            capture_output=True, text=True
        )
        issue["comments"] = comments_result.stdout.split("\n") if comments_result.returncode == 0 else []

    return issues


def parse_issue_to_competition(issue: dict) -> dict:
    """Parse a GitHub issue into competition data structure.

    Args:
        issue: Raw issue dict from GitHub API.

    Returns:
        Structured competition dict.
    """
    body = issue.get("body", "")
    comments = issue.get("comments", [])

    # Extract fields from issue body
    url = _extract_field(body, r"\*\*URL:\*\*\s*(\S+)")
    brand = _extract_field(body, r"\*\*Brand:\*\*\s*(.+)")
    prize = _extract_field(body, r"\*\*Prize:\*\*\s*(.+)")
    word_limit = _extract_field(body, r"\*\*Word Limit:\*\*\s*(\d+)")
    closing_date = _extract_field(body, r"\*\*Closes:\*\*\s*(\S+)")
    draw_date = _extract_field(body, r"\*\*Draw Date:\*\*\s*(\S+)")
    winners_notified = _extract_field(body, r"\*\*Winners Notified:\*\*\s*(.+)")

    # Extract prompt (after > blockquote)
    prompt_match = re.search(r"## Prompt\s*\n>\s*(.+?)(?:\n\n|---)", body, re.DOTALL)
    prompt = prompt_match.group(1).strip() if prompt_match else ""

    # Parse strategy from comments
    strategy = _parse_strategy_from_comments(comments)

    # Parse entries from comments
    entries = _parse_entries_from_comments(comments)

    # Check labels
    labels = [l.get("name", "") for l in issue.get("labels", [])]
    has_strategy = bool(strategy.get("recommended_tone"))
    has_entries = "entry-drafted" in labels or bool(entries)
    is_submitted = "entry-submitted" in labels

    # Calculate days until closing
    days_until_close = None
    is_closing_soon = False
    if closing_date:
        try:
            close_dt = datetime.strptime(closing_date, "%Y-%m-%d").date()
            days_until_close = (close_dt - date.today()).days
            is_closing_soon = 0 <= days_until_close <= 3
        except ValueError:
            pass

    return {
        "issue_number": issue["number"],
        "issue_url": issue.get("url", ""),
        "title": issue["title"],
        "url": url or issue.get("url", ""),
        "brand": brand or "",
        "prize": prize or "",
        "word_limit": int(word_limit) if word_limit else 25,
        "prompt": prompt,
        "closing_date": closing_date,
        "draw_date": draw_date,
        "winners_notified": winners_notified,
        "days_until_close": days_until_close,
        "is_closing_soon": is_closing_soon,
        "strategy": strategy,
        "entries": entries,
        "has_strategy": has_strategy,
        "has_entries": has_entries,
        "is_submitted": is_submitted,
        "created_at": issue.get("createdAt", ""),
    }


def _extract_field(text: str, pattern: str) -> str | None:
    """Extract a field from text using regex."""
    match = re.search(pattern, text)
    return match.group(1).strip() if match else None


def _parse_strategy_from_comments(comments: list[str]) -> dict:
    """Parse strategy analysis from issue comments."""
    strategy = {
        "sponsor_category": "",
        "brand_voice": "",
        "recommended_tone": "",
        "approach": "",
        "themes": [],
        "words": [],
        "angles": [],
        "avoid": [],
    }

    for comment in comments:
        if "## Strategy Analysis" in comment or "**Sponsor Category:**" in comment:
            strategy["sponsor_category"] = _extract_field(comment, r"\*\*Sponsor Category:\*\*\s*(.+)") or ""
            strategy["brand_voice"] = _extract_field(comment, r"\*\*Brand Voice:\*\*\s*(.+)") or ""
            strategy["recommended_tone"] = _extract_field(comment, r"\*\*Recommended Tone:\*\*\s*(.+)") or ""

            # Extract approach (multiline)
            approach_match = re.search(r"### Approach\s*\n(.+?)(?:\n###|\n---|\Z)", comment, re.DOTALL)
            strategy["approach"] = approach_match.group(1).strip() if approach_match else ""

            # Extract list items
            strategy["themes"] = _extract_list(comment, r"### Themes to Use\s*\n((?:[-*]\s*.+\n?)+)")
            strategy["words"] = _extract_list(comment, r"### Words to Consider\s*\n((?:[-*]\s*.+\n?)+)")
            strategy["angles"] = _extract_list(comment, r"### Angle Ideas\s*\n((?:\d+\.\s*.+\n?)+)")
            strategy["avoid"] = _extract_list(comment, r"### Avoid\s*\n((?:[-*]\s*.+\n?)+)")
            break

    return strategy


def _extract_list(text: str, pattern: str) -> list[str]:
    """Extract a list from markdown text."""
    match = re.search(pattern, text)
    if not match:
        return []
    items = re.findall(r"[-*\d.]\s*(.+)", match.group(1))
    return [item.strip() for item in items if item.strip()]


def _parse_entries_from_comments(comments: list[str]) -> list[dict]:
    """Parse entry drafts from issue comments."""
    entries = []

    for comment in comments:
        if "## Entry Drafts" in comment or "### Option" in comment:
            # Find all options
            option_matches = re.finditer(
                r"### Option (\d+)[^\n]*\n>\s*(.+?)(?:\n\nArc:|---|\Z)",
                comment,
                re.DOTALL
            )
            for match in option_matches:
                entries.append({
                    "option": int(match.group(1)),
                    "text": match.group(2).strip().replace("\n> ", " "),
                })
            if entries:
                break

    return entries


# =============================================================================
# Digest Building
# =============================================================================

def build_digest(repo: str) -> dict:
    """Build digest from GitHub issues.

    Args:
        repo: Repository in owner/name format.

    Returns:
        Digest dict with competitions and stats.
    """
    issues = query_competition_issues(repo)
    competitions = [parse_issue_to_competition(issue) for issue in issues]

    # Sort by closing date (soonest first), then by title
    def sort_key(c):
        days = c.get("days_until_close")
        if days is None:
            return (999, c["title"])
        return (days, c["title"])

    competitions.sort(key=sort_key)

    # Identify closing soon
    closing_soon = [c for c in competitions if c["is_closing_soon"]]

    # Count new (created in last 24 hours)
    yesterday = datetime.now() - timedelta(days=1)
    new_count = sum(
        1 for c in competitions
        if c.get("created_at") and datetime.fromisoformat(c["created_at"].replace("Z", "+00:00")).replace(tzinfo=None) > yesterday
    )

    return {
        "generated_at": datetime.now().isoformat(),
        "generated_date": date.today().isoformat(),
        "repo": repo,
        "total_count": len(competitions),
        "new_count": new_count,
        "closing_soon_count": len(closing_soon),
        "with_strategy_count": sum(1 for c in competitions if c["has_strategy"]),
        "with_entries_count": sum(1 for c in competitions if c["has_entries"]),
        "competitions": competitions,
        "closing_soon": closing_soon,
    }


# =============================================================================
# HTML Formatting
# =============================================================================

def format_digest_html(digest: dict) -> str:
    """Format the digest as HTML email.

    Args:
        digest: Digest dict from build_digest().

    Returns:
        HTML string for email body.
    """
    generated_at = datetime.fromisoformat(digest["generated_at"])

    html_parts = [
        f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="color-scheme" content="light dark">
    <meta name="supported-color-schemes" content="light dark">
    <style>
        :root {{ color-scheme: light dark; }}
        @media (prefers-color-scheme: dark) {{
            .email-body {{ background-color: #1a1a2e !important; }}
            .email-container {{ background-color: #16213e !important; }}
            .text-primary {{ color: #e2e8f0 !important; }}
            .text-secondary {{ color: #a0aec0 !important; }}
        }}
    </style>
</head>
<body class="email-body" style="margin: 0; padding: 0; background-color: #1e1e2f; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #1e1e2f;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" class="email-container" style="max-width: 680px; background-color: #2d2d44; border-radius: 16px; overflow: hidden;">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); padding: 32px 40px;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 700; letter-spacing: -0.5px;">
                                Competition Scout
                            </h1>
                            <p style="margin: 8px 0 0 0; color: rgba(255,255,255,0.85); font-size: 16px;">
                                {generated_at.strftime('%A, %d %B %Y')}
                            </p>
                        </td>
                    </tr>

                    <!-- Stats Bar -->
                    <tr>
                        <td style="padding: 0;">
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                <tr>
                                    <td width="50%" style="background-color: #1a3a2f; padding: 20px; text-align: center; border-bottom: 1px solid #3d3d5c;">
                                        <div style="font-size: 32px; font-weight: 700; color: #34d399;">{digest['total_count']}</div>
                                        <div style="font-size: 13px; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.5px;">Total Open</div>
                                    </td>
                                    <td width="50%" style="background-color: #1a2a4a; padding: 20px; text-align: center; border-bottom: 1px solid #3d3d5c;">
                                        <div style="font-size: 32px; font-weight: 700; color: #60a5fa;">{digest['new_count']}</div>
                                        <div style="font-size: 13px; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.5px;">New Today</div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Quick Summary Table -->
                    <tr>
                        <td style="padding: 32px 40px 16px 40px;">
                            <h2 style="margin: 0 0 20px 0; font-size: 20px; font-weight: 600; color: #e2e8f0;">Quick Summary</h2>
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border: 1px solid #3d3d5c; border-radius: 12px; overflow: hidden;">
                                <tr style="background-color: #363652;">
                                    <th style="padding: 14px 16px; text-align: left; font-size: 12px; font-weight: 600; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #3d3d5c;">Competition</th>
                                    <th style="padding: 14px 16px; text-align: left; font-size: 12px; font-weight: 600; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #3d3d5c;">Prize</th>
                                    <th style="padding: 14px 16px; text-align: center; font-size: 12px; font-weight: 600; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #3d3d5c;">Closes</th>
                                    <th style="padding: 14px 16px; text-align: center; font-size: 12px; font-weight: 600; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #3d3d5c;">Status</th>
                                </tr>
""",
    ]

    # Summary table rows
    for i, comp in enumerate(digest["competitions"], 1):
        closing = _format_closing_date(comp.get("closing_date"))
        prize = (comp.get("prize") or "See page")[:30]
        bg_color = "#4a2532" if comp["is_closing_soon"] else ("#2d2d44" if i % 2 == 1 else "#363652")
        closing_color = "#f87171" if comp["is_closing_soon"] else "#9ca3af"
        border_style = "" if i == len(digest["competitions"]) else "border-bottom: 1px solid #3d3d5c;"

        # Status indicator
        if comp["is_submitted"]:
            status = '<span style="color: #34d399;">Submitted</span>'
        elif comp["has_entries"]:
            status = '<span style="color: #60a5fa;">Drafted</span>'
        elif comp["has_strategy"]:
            status = '<span style="color: #c4b5fd;">Analyzed</span>'
        else:
            status = '<span style="color: #6b7280;">New</span>'

        html_parts.append(f"""
                                <tr style="background-color: {bg_color};">
                                    <td style="padding: 14px 16px; {border_style}">
                                        <a href="{comp['url']}" style="color: #a5b4fc; text-decoration: none; font-weight: 500; font-size: 14px;">{comp['title'][:45]}</a>
                                    </td>
                                    <td style="padding: 14px 16px; color: #34d399; font-weight: 600; font-size: 14px; {border_style}">{prize}</td>
                                    <td style="padding: 14px 16px; text-align: center; color: {closing_color}; font-weight: 500; font-size: 14px; {border_style}">{closing}</td>
                                    <td style="padding: 14px 16px; text-align: center; font-size: 14px; {border_style}">{status}</td>
                                </tr>
""")

    html_parts.append("""
                            </table>
                        </td>
                    </tr>
""")

    # Closing soon section
    if digest["closing_soon"]:
        html_parts.append("""
                    <tr>
                        <td style="padding: 16px 40px;">
                            <div style="background: linear-gradient(135deg, #4a2532 0%, #5c2d3d 100%); border-radius: 12px; padding: 20px; border-left: 4px solid #f87171;">
                                <h2 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600; color: #fca5a5;">Closing Soon</h2>
""")
        for comp in digest["closing_soon"]:
            html_parts.append(_format_competition_html(comp, highlight=True))
        html_parts.append("""
                            </div>
                        </td>
                    </tr>
""")

    # All competitions section
    html_parts.append("""
                    <tr>
                        <td style="padding: 16px 40px 40px 40px;">
                            <h2 style="margin: 0 0 20px 0; font-size: 20px; font-weight: 600; color: #e2e8f0;">All Competitions</h2>
""")

    for comp in digest["competitions"]:
        if not comp["is_closing_soon"]:
            html_parts.append(_format_competition_html(comp))

    # Footer
    html_parts.append(f"""
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #252538; padding: 24px 40px; border-top: 1px solid #3d3d5c;">
                            <p style="margin: 0; text-align: center; color: #6b7280; font-size: 13px;">
                                Generated by Competition Scout - {generated_at.strftime('%d %b %Y at %H:%M')}
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
""")
    return "".join(html_parts)


def _format_closing_date(closing_date: str | None) -> str:
    """Format closing date for display."""
    if not closing_date:
        return "—"
    try:
        dt = datetime.strptime(closing_date, "%Y-%m-%d")
        return dt.strftime("%d %b")
    except ValueError:
        return closing_date[:10] if closing_date else "—"


def _format_competition_html(comp: dict, highlight: bool = False) -> str:
    """Format a single competition as HTML card.

    Args:
        comp: Competition dict.
        highlight: Whether to highlight (for closing soon).

    Returns:
        HTML string for this competition.
    """
    card_bg = "#363652" if not highlight else "transparent"
    card_border = "1px solid #3d3d5c" if not highlight else "none"

    # Closing badge
    closing_badge = ""
    if comp.get("closing_date"):
        badge_bg = "#4a2532" if comp["is_closing_soon"] else "#1a3a2f"
        badge_color = "#fca5a5" if comp["is_closing_soon"] else "#34d399"
        closing_text = _format_closing_date(comp["closing_date"])
        days = comp.get("days_until_close")
        if days is not None and days >= 0:
            closing_text = f"{closing_text} ({days}d)"
        closing_badge = f'<span style="display: inline-block; background-color: {badge_bg}; color: {badge_color}; font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 20px; margin-left: 12px;">{closing_text}</span>'

    # Status badge
    status_badge = ""
    if comp["is_submitted"]:
        status_badge = '<span style="display: inline-block; background-color: #1a3a2f; color: #34d399; font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 20px; margin-left: 8px;">Submitted</span>'
    elif comp["has_entries"]:
        status_badge = '<span style="display: inline-block; background-color: #1a2a4a; color: #60a5fa; font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 20px; margin-left: 8px;">Entries Drafted</span>'

    word_limit = f" ({comp['word_limit']} words)" if comp.get("word_limit") else ""

    # Strategy section
    strategy_html = ""
    if comp["has_strategy"]:
        strategy = comp["strategy"]

        # Themes
        themes_html = ""
        if strategy.get("themes"):
            tags = "".join(f'<span style="display: inline-block; background-color: #1a3a2f; color: #34d399; font-size: 12px; padding: 4px 10px; border-radius: 6px; margin: 3px 6px 3px 0;">{t}</span>' for t in strategy["themes"][:5])
            themes_html = f'<div style="margin-top: 12px;"><p style="margin: 0 0 6px 0; font-size: 11px; font-weight: 600; color: #9ca3af; text-transform: uppercase;">Themes</p><div>{tags}</div></div>'

        # Angles
        angles_html = ""
        if strategy.get("angles"):
            angle_items = "".join(f'<li style="margin-bottom: 6px; color: #d1d5db; font-size: 13px;">{a}</li>' for a in strategy["angles"][:3])
            angles_html = f'<div style="margin-top: 12px;"><p style="margin: 0 0 6px 0; font-size: 11px; font-weight: 600; color: #9ca3af; text-transform: uppercase;">Angle Ideas</p><ul style="margin: 0; padding-left: 20px;">{angle_items}</ul></div>'

        strategy_html = f'''
                                <div style="background: linear-gradient(135deg, #2e2a4a 0%, #3d3660 100%); border-radius: 10px; padding: 16px; margin-top: 16px;">
                                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                                        <span style="font-size: 11px; font-weight: 600; color: #c4b5fd; text-transform: uppercase; letter-spacing: 0.5px; margin-right: 8px;">Recommended Tone:</span>
                                        <span style="font-size: 14px; font-weight: 600; color: #a5b4fc;">{strategy.get("recommended_tone") or "Not specified"}</span>
                                    </div>
                                    {themes_html}
                                    {angles_html}
                                </div>'''

    # Entries section
    entries_html = ""
    if comp.get("entries"):
        entry_items = "".join(
            f'<div style="background-color: rgba(0,0,0,0.2); border-radius: 6px; padding: 10px; margin-bottom: 8px;"><span style="color: #9ca3af; font-size: 11px;">Option {e["option"]}:</span> <span style="color: #e2e8f0; font-size: 13px;">{e["text"][:100]}...</span></div>'
            for e in comp["entries"][:2]
        )
        entries_html = f'''
                                <div style="margin-top: 16px;">
                                    <p style="margin: 0 0 8px 0; font-size: 11px; font-weight: 600; color: #60a5fa; text-transform: uppercase;">Draft Entries</p>
                                    {entry_items}
                                </div>'''

    return f'''
                            <div style="background-color: {card_bg}; border: {card_border}; border-radius: 12px; padding: 24px; margin-bottom: 20px;">
                                <!-- Title & Prize -->
                                <div style="margin-bottom: 16px;">
                                    <h3 style="margin: 0; font-size: 18px; font-weight: 600;">
                                        <a href="{comp['url']}" style="color: #e2e8f0; text-decoration: none;">{comp['title']}</a>
                                        {closing_badge}{status_badge}
                                    </h3>
                                    <p style="margin: 8px 0 0 0; font-size: 16px; color: #34d399; font-weight: 600;">
                                        {comp.get('prize') or 'Prize details on page'}
                                    </p>
                                </div>

                                <!-- Prompt -->
                                <div style="background: linear-gradient(135deg, #1a2a4a 0%, #1e3a5f 100%); border-radius: 10px; padding: 16px; border-left: 4px solid #60a5fa;">
                                    <p style="margin: 0 0 4px 0; font-size: 11px; font-weight: 600; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.5px;">Prompt{word_limit}</p>
                                    <p style="margin: 0; font-size: 14px; color: #93c5fd; line-height: 1.5;">{comp.get('prompt') or 'See competition page'}</p>
                                </div>

                                {strategy_html}
                                {entries_html}

                                <!-- CTA Button -->
                                <div style="margin-top: 20px; text-align: center;">
                                    <a href="{comp['url']}" style="display: inline-block; background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: #ffffff; text-decoration: none; padding: 12px 28px; border-radius: 8px; font-weight: 600; font-size: 14px;">Enter Competition</a>
                                </div>
                            </div>
'''


# =============================================================================
# Plain Text Formatting
# =============================================================================

def format_digest_text(digest: dict) -> str:
    """Format the digest as plain text.

    Args:
        digest: Digest dict from build_digest().

    Returns:
        Plain text string for email body.
    """
    generated_at = datetime.fromisoformat(digest["generated_at"])

    lines = [
        f"COMPETITION SCOUT - {generated_at.strftime('%d %b %Y')}",
        f"Found {digest['total_count']} open competitions, {digest['new_count']} new",
        "=" * 60,
        "",
    ]

    for comp in digest["competitions"]:
        closing = ""
        if comp.get("closing_date"):
            closing = f" (Closes {_format_closing_date(comp['closing_date'])})"
            if comp["is_closing_soon"]:
                closing += " ** CLOSING SOON **"

        # Status
        status = ""
        if comp["is_submitted"]:
            status = " [SUBMITTED]"
        elif comp["has_entries"]:
            status = " [DRAFTED]"
        elif comp["has_strategy"]:
            status = " [ANALYZED]"

        lines.extend([
            f"{comp['title']}{closing}{status}",
            f"   {comp['url']}",
            f"   Prize: {comp.get('prize') or 'See page'}",
        ])

        if comp.get("prompt"):
            lines.extend([
                "",
                f"   PROMPT ({comp['word_limit']} words max):",
                f"   {comp['prompt']}",
            ])

        if comp["has_strategy"]:
            strategy = comp["strategy"]
            lines.extend([
                "",
                f"   TONE: {strategy.get('recommended_tone') or 'Not specified'}",
            ])
            if strategy.get("angles"):
                lines.append("   ANGLES:")
                for angle in strategy["angles"][:3]:
                    lines.append(f"   - {angle}")

        if comp.get("entries"):
            lines.append("")
            lines.append("   DRAFT ENTRIES:")
            for entry in comp["entries"][:2]:
                lines.append(f"   Option {entry['option']}: {entry['text'][:80]}...")

        lines.extend(["", "-" * 60, ""])

    lines.append(f"\nGenerated: {generated_at.strftime('%d %b %Y at %H:%M')}")
    return "\n".join(lines)


# =============================================================================
# Email Sending
# =============================================================================

def send_digest_email(digest: dict) -> bool:
    """Send the digest via email.

    Requires environment variables:
        SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD
        EMAIL_TO (comma-separated), EMAIL_FROM

    Args:
        digest: Digest dict from build_digest().

    Returns:
        True if email sent successfully.
    """
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USERNAME", "")
    smtp_pass = os.environ.get("SMTP_PASSWORD", "")
    email_to = os.environ.get("EMAIL_TO", "")
    email_from = os.environ.get("EMAIL_FROM", smtp_user)

    if not smtp_user or not smtp_pass:
        print("SMTP credentials not configured (SMTP_USERNAME, SMTP_PASSWORD)", file=sys.stderr)
        return False

    if not email_to:
        print("No recipients configured (EMAIL_TO)", file=sys.stderr)
        return False

    # Parse recipients
    recipients = [r.strip() for r in email_to.split(",") if r.strip()]
    if not recipients:
        print("No valid email recipients", file=sys.stderr)
        return False

    # Build message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Competition Scout - {digest['total_count']} open, {digest['new_count']} new"
    msg["From"] = email_from
    msg["To"] = ", ".join(recipients)

    # Attach both versions
    msg.attach(MIMEText(format_digest_text(digest), "plain"))
    msg.attach(MIMEText(format_digest_html(digest), "html"))

    try:
        print(f"Connecting to {smtp_host}:{smtp_port}...", file=sys.stderr)
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(email_from, recipients, msg.as_string())
        print(f"Email sent to {len(recipients)} recipient(s)", file=sys.stderr)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}", file=sys.stderr)
        return False


def save_digest_preview(digest: dict, path: str = "/tmp/competition-digest") -> None:
    """Save digest to local files for preview.

    Args:
        digest: Digest dict.
        path: Base path (without extension).
    """
    filepath = Path(path)

    filepath.with_suffix(".html").write_text(format_digest_html(digest), encoding="utf-8")
    filepath.with_suffix(".txt").write_text(format_digest_text(digest), encoding="utf-8")
    filepath.with_suffix(".json").write_text(json.dumps(digest, indent=2), encoding="utf-8")

    print(f"Saved preview files:", file=sys.stderr)
    print(f"  HTML: {filepath.with_suffix('.html')}", file=sys.stderr)
    print(f"  Text: {filepath.with_suffix('.txt')}", file=sys.stderr)
    print(f"  JSON: {filepath.with_suffix('.json')}", file=sys.stderr)


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python notifier.py [send|preview|json]", file=sys.stderr)
        print("  send    - Build and send digest email", file=sys.stderr)
        print("  preview - Save HTML/TXT/JSON to /tmp for preview", file=sys.stderr)
        print("  json    - Output digest as JSON to stdout", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    repo = get_target_repo()

    print(f"Building digest from {repo}...", file=sys.stderr)
    digest = build_digest(repo)

    print(f"Found {digest['total_count']} competitions ({digest['closing_soon_count']} closing soon)", file=sys.stderr)

    if command == "send":
        success = send_digest_email(digest)
        sys.exit(0 if success else 1)

    elif command == "preview":
        save_digest_preview(digest)
        print(f"\nOpen /tmp/competition-digest.html in a browser to preview", file=sys.stderr)

    elif command == "json":
        print(json.dumps(digest, indent=2))

    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
