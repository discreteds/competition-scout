---
name: comp-scout-scrape
description: Scrape competition websites and extract structured data using LLM interpretation. Handles competitions.com.au and netrewards.com.au.
---

# Competition Scraper

Scrape "25 words or less" competitions from Australian aggregator sites with LLM-enhanced interpretation.

## Two-Phase Approach

1. **Python/Playwright** - Fetches raw HTML from JS-rendered pages
2. **Claude interpretation** - Extracts structured data using natural language understanding

This is better than regex-based scraping because Claude can:
- Understand varied date formats ("closes Dec 31" vs "31/12/2024" vs "in 7 days")
- Extract draw date and winner notification date from unstructured text
- Identify the actual prompt even when buried in marketing copy
- Determine brand from context clues

## Prerequisites

```bash
pip install playwright
playwright install chromium
```

## Workflow

### Step 1: Fetch Listing Pages

Run the scraper to get HTML from all listing pages:

```bash
python skills/comp-scout-scrape/scraper.py listings
```

This returns JSON with HTML content from:
- competitions.com.au
- netrewards.com.au

### Step 2: Interpret Listings

From the HTML, identify each competition and extract:

| Field | Look For |
|-------|----------|
| url | Link to competition detail page |
| title | Competition title/heading |
| prize_summary | Prize badge, "Win a...", prize value |
| closing_date | "Closes:", date badges, countdown timers |

**Present summary to user:** "Found X competitions from competitions.com.au, Y from netrewards.com.au"

### Step 3: Check for New Competitions

Before fetching details, check which competitions are new:
- Compare URLs against existing issues in target repo
- Only fetch details for competitions not already tracked

### Step 4: Fetch Detail Pages

For each new competition, fetch the full page:

```bash
python skills/comp-scout-scrape/scraper.py detail "https://competitions.com.au/win-example/"
```

### Step 5: Interpret Detail Page

From the page content, extract all fields:

| Field | Look For |
|-------|----------|
| title | Main heading, `<h1>`, og:title meta tag |
| brand | Logo alt text, "brought to you by", sponsor mentions, footer |
| prize_summary | Prize description, "win a...", prize details section |
| prize_value | $XX,XXX patterns, "valued at" |
| prompt | "In 25 words or less...", "Tell us why...", "Complete this sentence...", entry question |
| word_limit | "25 words", "50 words", "in X words or less" |
| closing_date | "Closes:", "Entries close:", "Competition ends:" + date |
| draw_date | "Winners drawn:", "Judging:", "Selection date:", "Draw date:" |
| winners_notified_date | "Winners notified by:", "within X days of draw", "notified by email" |

### Step 6: Output Structured Data

Return JSON for each competition:

```json
{
  "url": "https://competitions.com.au/win-example/",
  "site": "competitions.com.au",
  "title": "Win a $500 Gift Card",
  "brand": "Example Brand",
  "prize_summary": "$500 gift card to spend at Example Store",
  "prize_value": 500,
  "prompt": "Tell us in 25 words or less why you love shopping at Example Store",
  "word_limit": 25,
  "closing_date": "2024-12-31",
  "draw_date": "2025-01-07",
  "winners_notified_date": "2025-01-14"
}
```

## Date Extraction Tips

Competition pages express dates in many formats. Look for:

**Absolute dates:**
- "31 December 2024"
- "31/12/2024"
- "Dec 31, 2024"
- "2024-12-31"

**Relative dates (calculate from today or closing):**
- "Closes in 7 days"
- "Winners drawn 14 days after close"
- "Notified within 28 days"

**Implicit dates:**
- "Winners drawn the following week"
- "Notified by email after judging"

When dates are relative, calculate the actual date.

## Handling Missing Data

Not all fields will be available on every page:

| Field | If Missing |
|-------|------------|
| brand | Use site domain or "Unknown" |
| prize_value | Leave as null |
| draw_date | Leave as null |
| winners_notified_date | Leave as null |
| word_limit | Default to 25 |

## Output Schema

See `lib/schemas/competition.yaml` for the full schema definition.

```yaml
competition:
  url: string           # Required
  site: string          # Required
  title: string         # Required
  brand: string         # Required (use "Unknown" if not found)
  prize_summary: string # Required
  prize_value: int      # Optional
  prompt: string        # Required
  word_limit: int       # Default 25
  closing_date: date    # Required (YYYY-MM-DD)
  draw_date: date       # Optional
  winners_notified_date: date  # Optional
```

## Example Session

```
User: Scrape competitions

Claude: I'll fetch the listing pages from competitions.com.au and netrewards.com.au.

[Runs: python skills/comp-scout-scrape/scraper.py listings]

Found 15 competitions:
- competitions.com.au: 10 competitions
- netrewards.com.au: 5 competitions

Checking against existing issues... 3 are new.

Fetching details for new competitions...

[Runs: python skills/comp-scout-scrape/scraper.py detail URL for each]

Here are the 3 new competitions:

1. **Win a $500 Coles Gift Card** (Coles)
   - Prompt: "Tell us in 25 words or less what you'd buy..."
   - Closes: Dec 31, 2024
   - Prize: $500

2. **Win a Trip to Bali** (Flight Centre)
   - Prompt: "In 25 words or less, describe your dream holiday..."
   - Closes: Jan 15, 2025
   - Prize: ~$5,000

3. **Win a Year's Supply of Coffee** (Nespresso)
   - Prompt: "Complete this sentence in 25 words or less: My morning coffee..."
   - Closes: Dec 20, 2024
   - Prize: $1,200

Would you like me to:
- Analyze any of these for strategy?
- Persist them to GitHub?
```
