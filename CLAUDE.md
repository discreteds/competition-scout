# Competition Scout Skills

Claude Code skills for scraping competitions, analyzing strategy, composing entries, and persisting to GitHub.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     comp-scout-daily                            │
│                   (workflow orchestrator)                       │
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┬───────────────┐
          │               │               │               │
          ▼               ▼               ▼               ▼
┌─────────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ comp-scout-     │ │ comp-scout- │ │ comp-scout- │ │ comp-scout- │
│ scrape          │ │ analyze     │ │ compose     │ │ notify      │
│                 │ │             │ │             │ │             │
│ • Scrape sites  │ │ • Strategy  │ │ • Entries   │ │ • Email     │
│ • Dedup check   │ │ • Tone      │ │ • Arcs      │ │ • Digest    │
│ • Create issues │ │ • Angles    │ │ • Recommend │ │             │
│ • Apply filters │ └─────────────┘ └─────────────┘ └─────────────┘
└─────────────────┘
        │
        └──────▶ [GitHub Issues] ◀────────────────────────┘
```

## Skills Overview

| Skill | Purpose | Mode | Python |
|-------|---------|------|--------|
| `comp-scout-scrape` | Scrape + persist to GitHub | Automatic | Yes |
| `comp-scout-analyze` | Generate strategy analysis | Interactive / Unattended | No |
| `comp-scout-compose` | Create 25-words-or-less entries | Interactive / Unattended | No |
| `comp-scout-notify` | Send email digest | Automatic | Yes |
| `comp-scout-daily` | Orchestrate full workflow | Unattended only | No |
| `comp-scout-persist` | **DEPRECATED** - merged into scrape | N/A | No |

## Execution Modes

Skills support two execution modes:

| Mode | When Used | Behavior |
|------|-----------|----------|
| **Interactive** | Individual skill invocation | Asks clarifying questions |
| **Unattended** | `comp-scout-daily` or `--unattended` flag | Uses defaults, no prompts |

### Interactive Example
```
User: "Analyze issue #42 for strategy"
Claude: "What tone would you prefer? (sincere/humorous/mix)"
```

### Unattended Example (via daily workflow)
```
comp-scout-daily automatically invokes:
  comp-scout-analyze --unattended  → Uses sponsor category defaults
  comp-scout-compose --unattended  → Uses saved stories or generic
```

## Prerequisites

### For scraping
```bash
pip install playwright
playwright install chromium
```

### For GitHub persistence
- `gh` CLI authenticated
- Target repository for competition issues (separate from this skills repo)

### For email notifications
- SMTP credentials configured (see comp-scout-notify)

## Data Flow

```
Scrape (scraper.py)
    │
    ▼
competition_listing  ──▶  Dedup Check  ──▶  GitHub Issue
    │                                            │
    ▼                                            ▼
competition_detail   ──────────────────────▶  Issue Body
                                                 │
                          ┌──────────────────────┤
                          ▼                      ▼
                    strategy (comment)    entry_set (comment)
```

See `lib/schemas/competition.yaml` for full data schemas.

## Invoking Skills

### Individual Skills (Interactive)

```
"Scrape competitions"
→ Uses comp-scout-scrape (creates issues automatically)

"Analyze issue #42 for strategy"
→ Uses comp-scout-analyze (may ask questions)

"Write entries for issue #42"
→ Uses comp-scout-compose (may ask questions)

"Send me a competition digest"
→ Uses comp-scout-notify
```

### Daily Workflow (Unattended)

```
"Perform daily competition scout"
→ Runs full workflow: scrape → analyze → compose → notify
→ No questions asked - uses defaults and saved stories
```

### Cron Automation

```bash
# Daily at 7am
0 7 * * * claude -p "Perform daily competition scout" >> /var/log/comp-scout.log 2>&1
```

## Target Repository

These skills persist data to a **separate repository** (e.g., `competition-scout-25WOL`), not this skills repo.

Configure via environment variable:
```bash
export TARGET_REPO=discreteds/competition-scout-25WOL
```

The target repo's CLAUDE.md should contain:
- Auto-filter keywords
- Saved stories for entry composition
- Personal context

## Key Patterns

### Deduplication
1. Normalize title (strip "Win ", "Win a " prefixes, lowercase)
2. Compare to existing issues at 80% similarity threshold
3. Duplicates become **comments** on existing issues

### Auto-Filtering
Competitions matching filter keywords are:
1. Created as issues (for record-keeping)
2. Labeled with filter reason (e.g., `for-kids`)
3. Immediately closed with explanation

### Issue as Dumping Ground
Each competition issue collects all related info via comments:
- Additional sources (from other aggregator sites)
- Strategy analysis
- Draft entries
- Submission confirmation
- Winner notification

### Tone Matrix (Unattended Mode)

| Sponsor Type | Default Tone |
|--------------|--------------|
| Wellness/luxury | Sincere, aspirational |
| Tech/gaming | Knowledgeable, self-aware humor |
| Food/beverage | Relatable moments, sensory |
| Travel | Discovery, bucket-list energy |
| Retail/general | Personality, memorability |
| Rural/agricultural | Practical, financially savvy |

## DRY Principle

The daily workflow **invokes** other skills rather than duplicating their logic:

- Bug fixes in individual skills automatically apply to daily workflow
- Interactive and unattended modes share the same core logic
- Each skill has a single source of truth for its behavior

If you need to change how analysis works, change `comp-scout-analyze` - the daily workflow will automatically use the updated logic.
