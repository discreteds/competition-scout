---
name: comp-scout-scrape
description: Scrape competition websites and extract structured data. Returns JSON with all competition fields extracted - no HTML interpretation needed.
---

# Competition Scraper

Scrape "25 words or less" competitions from Australian aggregator sites.

## What's Changed

The scraper now returns **structured JSON** with all fields extracted. Claude no longer needs to interpret raw HTML - the Python extraction handles:
- Date parsing (multiple formats)
- Word limit extraction
- Prompt identification
- Winner notification from JSON-LD
- Title normalization for deduplication

## Prerequisites

```bash
pip install playwright
playwright install chromium
```

## Workflow

### Step 1: Scrape Listings

Run the scraper to get structured competition data from all sites:

```bash
python skills/comp-scout-scrape/scraper.py listings
```

**Output:**
```json
{
  "competitions": [
    {
      "url": "https://competitions.com.au/win-example/",
      "site": "competitions.com.au",
      "title": "Win a $500 Gift Card",
      "normalized_title": "500 gift card",
      "brand": "Example Brand",
      "prize_summary": "$500",
      "prize_value": 500,
      "closing_date": "2024-12-31"
    }
  ],
  "scrape_date": "2024-12-09",
  "errors": []
}
```

Progress is logged to stderr. JSON output goes to stdout.

### Step 2: Review Results

Present the competitions to the user:

```
Found 15 competitions:
- competitions.com.au: 10 competitions
- netrewards.com.au: 5 competitions

After deduplication: 12 unique competitions
```

### Step 3: Fetch Details (for new competitions)

For competitions that need full details (prompt, word limit, winner notification):

```bash
python skills/comp-scout-scrape/scraper.py detail "https://competitions.com.au/win-example/"
```

**Output:**
```json
{
  "url": "https://competitions.com.au/win-example/",
  "site": "competitions.com.au",
  "title": "Win a $500 Gift Card",
  "normalized_title": "500 gift card",
  "brand": "Example Brand",
  "prize_summary": "$500",
  "prize_value": 500,
  "prompt": "Tell us in 25 words or less why you love shopping",
  "word_limit": 25,
  "closing_date": "2024-12-31",
  "entry_method": "Submit via form below",
  "winner_notification": {
    "notification_text": "Winners will be notified within 7 days",
    "notification_date": null,
    "notification_days": 7,
    "selection_text": "Winners selected on 7 January 2025",
    "selection_date": "2025-01-07"
  },
  "scraped_at": "2024-12-09T10:30:00"
}
```

### Step 4: Debug Mode (URLs only)

To just get competition URLs without full extraction:

```bash
python skills/comp-scout-scrape/scraper.py urls
```

**Output:**
```json
{
  "competitions.com.au": [
    "https://competitions.com.au/win-example-1/",
    "https://competitions.com.au/win-example-2/"
  ],
  "netrewards.com.au": [
    "https://netrewards.com.au/competitions/example/"
  ]
}
```

## Output Fields

### Listing Output

| Field | Type | Description |
|-------|------|-------------|
| url | string | Full URL to competition detail page |
| site | string | Source site (competitions.com.au or netrewards.com.au) |
| title | string | Competition title as displayed |
| normalized_title | string | Lowercase, prefixes stripped, for matching |
| brand | string | Sponsor/brand name (if available in listing) |
| prize_summary | string | Prize description or value badge |
| prize_value | int/null | Numeric value in dollars |
| closing_date | string/null | YYYY-MM-DD format |

### Detail Output

All listing fields plus:

| Field | Type | Description |
|-------|------|-------------|
| prompt | string | The actual competition question/prompt |
| word_limit | int | Maximum words (default 25) |
| entry_method | string | How to submit entry |
| winner_notification | object/null | Notification details from JSON-LD |
| scraped_at | string | ISO timestamp of scrape |

### Winner Notification Object

Extracted from competitions.com.au JSON-LD FAQPage schema:

| Field | Type | Description |
|-------|------|-------------|
| notification_text | string | Raw notification text |
| notification_date | string/null | Specific date if mentioned |
| notification_days | int/null | Days after close/draw |
| selection_text | string | How winners are selected |
| selection_date | string/null | When judging occurs |

## Title Normalization

Titles are normalized for deduplication:

1. Lowercase
2. Strip prefixes: "Win ", "Win a ", "Win an ", "Win the ", "Win 1 of "
3. Remove punctuation
4. Collapse whitespace

**Example:**
```
Original: "Win a $500 Coles Gift Card"
Normalized: "500 coles gift card"
```

## Date Formats Supported

The scraper parses these date formats:

| Format | Example |
|--------|---------|
| Day Month Year | "31 December 2024", "31 Dec 2024" |
| ISO | "2024-12-31" |
| Slash | "31/12/2024" |
| netrewards format | "31 12 25" (DD MM YY) |

## Error Handling

Errors are captured per-site and returned in the response:

```json
{
  "competitions": [...],
  "errors": [
    {"site": "netrewards.com.au", "error": "Timeout after 60s"}
  ]
}
```

## Example Session

```
User: Scrape competitions

Claude: I'll fetch competitions from both sites.

[Runs: python skills/comp-scout-scrape/scraper.py listings]

Found 12 unique competitions:
- competitions.com.au: 8 competitions
- netrewards.com.au: 4 competitions

Checking against existing issues... 3 are new.

**New Competitions:**

1. **Win a $500 Coles Gift Card** (Coles)
   - Closes: Dec 31, 2024
   - Prize: $500

2. **Win a Trip to Bali** (Flight Centre)
   - Closes: Jan 15, 2025
   - Prize: $5,000

3. **Win a Year's Supply of Coffee** (Nespresso)
   - Closes: Dec 20, 2024
   - Prize: $1,200

Would you like me to:
- Get full details (prompts, word limits) for these?
- Persist them to GitHub?
- Generate entry strategies?
```

## Integration

The structured output integrates directly with other skills:

- **comp-scout-persist**: Use `normalized_title` for deduplication, `closing_date` for milestones
- **comp-scout-analyze**: Pass competition details for strategy generation
- **comp-scout-compose**: Use `prompt` and `word_limit` for entry generation
