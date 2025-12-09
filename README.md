# Competition Scout

A suite of Claude Code skills for scraping "25 words or less" competitions, analyzing strategy, composing entries, and persisting to GitHub.

## Skills

| Skill | Description |
|-------|-------------|
| **comp-scout-scrape** | Scrape competitions.com.au and netrewards.com.au with LLM-enhanced interpretation |
| **comp-scout-analyze** | Generate strategic analysis (tone, themes, angles) for a competition |
| **comp-scout-compose** | Create 25-words-or-less entries with multiple variations |
| **comp-scout-persist** | Store competitions as GitHub issues with project integration |

## Setup

```bash
# Install Python dependencies
pip install -e .

# Install Playwright browser
playwright install chromium
```

## Architecture

```
competition-scout/
├── skills/
│   ├── comp-scout-scrape/      # Playwright + LLM interpretation
│   ├── comp-scout-analyze/     # Pure SKILL.md workflow
│   ├── comp-scout-compose/     # Pure SKILL.md workflow
│   └── comp-scout-persist/     # gh CLI + hiivmind-pulse-gh
├── lib/
│   └── schemas/
│       └── competition.yaml    # Shared data schemas
├── pyproject.toml              # Minimal deps (playwright only)
└── CLAUDE.md                   # Skill documentation
```

## Data Flow

```
Scrape → Competition data
           │
           ├─────────────────┐
           ▼                 ▼
       Persist          Analyze → Strategy
                             │
                             ▼
                         Compose → Entries
                             │
                             ▼
                     Persist (add to issue)
```

## Key Features

### LLM-Enhanced Scraping
Unlike regex-based scrapers, Claude interprets page content to extract:
- Draw date and winner notification date
- The actual prompt (even when buried in marketing copy)
- Brand voice and context

### Simplified Deduplication
Competitions are deduplicated by fuzzy title matching (80% threshold). Duplicates from other sites are added as **comments** on existing issues - no complex parent-child relationships.

### Issue as Dumping Ground
Each competition issue collects all related info via comments:
- Additional sources from other aggregator sites
- Strategy analysis
- Draft entries
- Submission confirmation
- Winner notification

## Persistence

Competition data is stored in a **separate repository** (not this skills repo). Configure your target repo when using `comp-scout-persist`.

Requires:
- `gh` CLI authenticated
- hiivmind-pulse-gh workspace initialized

## Related Projects

- [comp-scout](https://github.com/discreteds/comp-scout) - Original Python implementation (being refactored into these skills)
- [hiivmind-pulse-gh](https://github.com/hiivmind/hiivmind-pulse-gh) - GitHub Projects integration skills
