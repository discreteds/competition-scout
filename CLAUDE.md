# Competition Scout Skills

Claude Code skills for scraping competitions, analyzing strategy, composing entries, and persisting to GitHub.

## Skills Overview

| Skill | Purpose | Python |
|-------|---------|--------|
| `comp-scout-scrape` | Scrape competition websites with LLM interpretation | Yes |
| `comp-scout-analyze` | Generate strategy analysis (tone, themes, approach) | No |
| `comp-scout-compose` | Create 25-words-or-less entries | No |
| `comp-scout-persist` | Store to GitHub issues with project integration | No |
| `comp-scout-notify` | Send email digest of competitions | Yes |
| `comp-scout-daily` | End-to-end automated workflow for cron execution | No |

## Skill Hierarchy

### Interactive Mode (individual skills)

```
comp-scout-scrape
       │
       ├──────────────────┐
       ▼                  ▼
comp-scout-persist   comp-scout-analyze
                          │
                          ▼
                    comp-scout-compose
                          │
                          ▼
                    comp-scout-persist (update issue with entry)
```

### Automated Mode (daily workflow)

```
                    comp-scout-daily
                          │
    ┌─────────────────────┼──────────────────────┐
    │                     │                      │
    ▼                     ▼                      ▼
comp-scout-scrape   comp-scout-analyze    comp-scout-notify
    │                     │
    ▼                     ▼
comp-scout-persist  comp-scout-compose
                          │
                          ▼
                    comp-scout-persist
```

The daily workflow orchestrates all skills in sequence, running unattended for cron execution.

## Prerequisites

### For scraping (comp-scout-scrape)
```bash
pip install playwright
playwright install chromium
```

### For GitHub persistence (comp-scout-persist)
- `gh` CLI authenticated
- hiivmind-pulse-gh workspace initialized
- Target repository for competition issues (separate from this skills repo)

## Data Flow

1. **Scrape** → `competition` objects (JSON)
2. **Analyze** → `strategy` object per competition
3. **Compose** → `entry_set` with 3-5 entry variations
4. **Persist** → GitHub issue (or comment if duplicate)

See `lib/schemas/competition.yaml` for full data schemas.

## Target Repository

These skills persist data to a **separate repository** (e.g., `competition-data`), not this skills repo.

Configure the target repo in your workspace config or specify when invoking `comp-scout-persist`.

## Invoking Skills

Skills are invoked by asking Claude to use them:

```
"Scrape competitions from the usual sites"
→ Uses comp-scout-scrape

"Analyze this competition for strategy"
→ Uses comp-scout-analyze

"Write some entries for this competition"
→ Uses comp-scout-compose

"Save this competition to GitHub"
→ Uses comp-scout-persist

"Send me a competition digest"
→ Uses comp-scout-notify

"Perform daily competition scout"
→ Uses comp-scout-daily (full automated workflow)
```

### Cron Automation

For automated daily runs:
```bash
0 7 * * * claude -p "Perform daily competition scout" >> /var/log/comp-scout.log 2>&1
```

## Deduplication

When persisting, competitions are deduplicated by fuzzy title matching:
1. Normalize title (strip "Win ", "Win a " prefixes, lowercase)
2. Compare to existing issues at 80% similarity threshold
3. **Duplicates become comments** on existing issues (not separate issues)

## Key Patterns

### LLM-Enhanced Scraping
The scraper uses Playwright to fetch HTML, then Claude interprets the page content. This extracts fields that regex couldn't reliably get:
- Draw date
- Winner notification date
- The actual prompt (even when buried in marketing copy)

### Issue as Dumping Ground
Each competition issue collects all related info via comments:
- Additional sources (from other aggregator sites)
- Strategy analysis
- Draft entries
- Submission confirmation
- Winner notification

### Tone Matrix
Strategy analysis uses sponsor category to determine winning tone:

| Sponsor Type | Likely Winning Tone |
|--------------|---------------------|
| Wellness/luxury | Sincere, aspirational |
| Tech/gaming | Knowledgeable, self-aware humour |
| Food/beverage | Relatable moments, sensory |
| Travel | Discovery, bucket-list energy |
| Retail/general | Personality, memorability |
| Rural/agricultural | Practical, financially savvy |
