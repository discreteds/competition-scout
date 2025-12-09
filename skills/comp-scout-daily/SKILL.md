---
name: comp-scout-daily
description: End-to-end automated daily competition workflow. Orchestrates scrape, analyze, compose, and notify skills - all unattended for cron execution.
---

# Daily Competition Scout

Automated end-to-end workflow for cron/scheduled execution. **Orchestrates other skills** rather than duplicating their logic.

## What This Skill Does

This skill is a **workflow orchestrator** that invokes other skills in sequence:

```
┌─────────────────┐
│ comp-scout-daily│
└────────┬────────┘
         │
         ▼
┌─────────────────┐     Scrapes listings, fetches details,
│ comp-scout-scrape│────▶ checks duplicates, persists issues
└────────┬────────┘
         │
         ▼ (for each new, non-filtered issue)
┌─────────────────┐
│comp-scout-analyze│────▶ Generates strategy (--unattended)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│comp-scout-compose│────▶ Drafts entries (--unattended)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│comp-scout-notify │────▶ Sends email digest
└─────────────────┘
```

**Runs completely unattended - no user prompts during execution.**

## Prerequisites

- `gh` CLI authenticated
- Playwright installed: `pip install playwright && playwright install chromium`
- Target repository with CLAUDE.md containing user preferences
- SMTP credentials for email notifications (optional)

## Invocation

### Via Claude Code
```
"Perform daily competition scout"
"Run the daily comp scout workflow"
"Do the morning competition scrape and analysis"
```

### Via Cron
```bash
# Daily at 7am
0 7 * * * claude -p "Perform daily competition scout" >> /var/log/comp-scout.log 2>&1
```

## Workflow

### Phase 1: Configuration

Determine target repository and load user preferences:

```bash
TARGET_REPO="${TARGET_REPO:-discreteds/competition-scout-25WOL}"

# Fetch user preferences from data repo
gh api repos/$TARGET_REPO/contents/CLAUDE.md -H "Accept: application/vnd.github.raw" 2>/dev/null
```

Parse from CLAUDE.md:
- Auto-filter keywords (for-kids, cruise, etc.)
- Saved stories for entry composition
- Personal context (partner name, location)

### Phase 2: Invoke comp-scout-scrape

**Delegate to the scrape skill** - do not duplicate its logic.

The scrape skill handles:
1. Scraping all listing pages
2. Fetching full details for new competitions
3. Checking for duplicates against existing issues
4. Applying auto-filter rules
5. Creating issues (or closing if filtered)
6. Adding duplicate comments to existing issues

```
Invoke: comp-scout-scrape
Mode: Unattended (automatic)
Output: List of new issue numbers created
```

### Phase 3: Invoke comp-scout-analyze (for each new issue)

**Delegate to the analyze skill** with `--unattended` flag.

For each new, non-filtered competition issue:

```
Invoke: comp-scout-analyze --unattended
Input: Issue number from Phase 2
Output: Strategy comment added to issue
```

The analyze skill in unattended mode:
- Uses sponsor category to determine default tone
- Generates 5 standard angle ideas
- Auto-persists strategy as comment

### Phase 4: Invoke comp-scout-compose (for each new issue)

**Delegate to the compose skill** with `--unattended` flag.

For each new, non-filtered competition issue:

```
Invoke: comp-scout-compose --unattended
Input: Issue number, strategy from Phase 3
Output: Entry drafts comment added, entry-drafted label applied
```

The compose skill in unattended mode:
- Matches saved stories from CLAUDE.md to competition
- Uses best-matching story or generic approach
- Generates 3-5 entry variations
- Auto-persists with recommendation

### Phase 5: Check Closing Soon

Query for competitions closing within 3 days:

```bash
gh issue list -R "$TARGET_REPO" \
  --label "competition" \
  --state open \
  --json number,title,body,labels
```

Parse closing dates and flag urgent items.

### Phase 6: Invoke comp-scout-notify

**Delegate to the notify skill** for email digest.

```
Invoke: comp-scout-notify send
Output: Email sent to configured recipients
```

### Phase 7: Output Summary Report

```markdown
## Daily Competition Scout Report - 2025-12-09

### Summary
- **New competitions:** 5
- **Auto-filtered:** 2 (1 for-kids, 1 cruise)
- **Analyzed and drafted:** 3
- **Duplicates added:** 1

### New Competitions (Ready for Entry)

| Issue | Competition | Closes | Story Used | Recommended |
|-------|-------------|--------|------------|-------------|
| #15 | Win $500 Coles Gift Card | Dec 31 | Generic | Option 2 |
| #16 | Win a Spa Day | Jan 5 | Margot Deserves Pampering | Option 1 |
| #17 | Win Kitchen Appliance | Dec 20 | Generic | Option 3 |

### Auto-Filtered (Created + Closed)

| Issue | Competition | Reason |
|-------|-------------|--------|
| #18 | Win Lego Set | for-kids (keyword: Lego) |
| #19 | Win P&O Cruise | cruise (keyword: P&O) |

### Closing Soon - Action Needed

| Issue | Competition | Days Left | Status |
|-------|-------------|-----------|--------|
| #12 | Woolworths Gift Cards | 1 | entry-drafted |
| #14 | TVSN Prize Pack | 2 | entry-drafted |

### Recommendations

1. **Priority:** #12 closes tomorrow - entry drafted, recommend Option 2
2. **High value:** #16 Spa Day ($500) - entry uses saved story, strong fit
3. **Review:** #17 Kitchen Appliance - closes in 11 days, time to refine
```

## Unattended Operation

The skill makes NO interactive prompts during execution:

| Decision | Automatic Behavior |
|----------|-------------------|
| Story selection | Use best keyword-matching saved story, or generic approach |
| Entry generation | All entries drafted with star ratings; recommendation noted |
| Filter decisions | Based on keywords in CLAUDE.md preferences |
| Duplicates | Add comment to existing issue automatically |
| Tone selection | Based on sponsor category (see comp-scout-analyze) |

All choices are logged in the report for user review.

## Error Handling

| Error | Behavior |
|-------|----------|
| Scrape fails for one site | Log error, continue with other site |
| Issue creation fails | Log error, skip to next competition |
| Analyze fails for one issue | Log error, skip compose for that issue |
| Compose fails for one issue | Log error, continue to next issue |
| Notify fails | Log error, report still generated |
| No new competitions | Report "No new competitions found" |

Errors are included in the final report.

## Configuration

### Environment Variables

```bash
TARGET_REPO=discreteds/competition-scout-25WOL
```

### Data Repo CLAUDE.md

Must contain:
- **User Preferences**: Auto-filter rules with keywords
- **Saved Stories**: Personal stories for automatic matching (optional)
- **Personal Context**: Partner name, location, interests

## Skill Invocation Pattern

This skill **orchestrates** - it does not duplicate logic:

| Skill | Invoked By Daily | Mode |
|-------|------------------|------|
| comp-scout-scrape | Yes | Automatic (handles own persistence) |
| comp-scout-analyze | Yes | `--unattended` flag |
| comp-scout-compose | Yes | `--unattended` flag |
| comp-scout-notify | Yes | Automatic |
| comp-scout-persist | No | Logic merged into scrape |

Individual skills remain available for interactive use when you want manual control.

## Example Cron Log Output

```
$ claude -p "Perform daily competition scout"

Starting daily competition scout...

Phase 1: Loading configuration
  Target repo: discreteds/competition-scout-25WOL
  Filter rules: for-kids (9 keywords), cruise (6 keywords)
  Saved stories: 2 available

Phase 2: Invoking comp-scout-scrape
  competitions.com.au: 8 competitions
  netrewards.com.au: 5 competitions
  New issues created: #43, #44, #45
  Filtered issues (closed): #46, #47
  Duplicate comments: #38

Phase 3: Invoking comp-scout-analyze (--unattended)
  #43: Strategy added (Food/beverage → Relatable, sensory)
  #44: Strategy added (Travel → Discovery, bucket-list)
  #45: Strategy added (Tech → Knowledgeable, self-aware humor)

Phase 4: Invoking comp-scout-compose (--unattended)
  #43: 3 entries drafted (using saved story: Sunday BBQ)
  #44: 4 entries drafted (generic approach)
  #45: 3 entries drafted (generic approach)

Phase 5: Checking closing soon
  3 competitions closing within 3 days

Phase 6: Invoking comp-scout-notify
  Email sent to 2 recipients

## Daily Competition Scout Report - 2025-12-09
[Full report as shown above]
```

## Key Design Principle

**DRY (Don't Repeat Yourself)**: This skill invokes other skills rather than reimplementing their logic. This means:

1. Bug fixes in individual skills automatically apply to daily workflow
2. Interactive and unattended modes share the same core logic
3. Each skill has a single source of truth for its behavior
4. Testing individual skills also tests the daily workflow

If you need to change how analysis works, change `comp-scout-analyze` - the daily workflow will automatically use the updated logic.
