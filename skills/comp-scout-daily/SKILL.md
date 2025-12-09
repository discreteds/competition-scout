---
name: comp-scout-daily
description: End-to-end automated daily competition workflow. Scrapes, filters, persists, analyzes, composes entries, and outputs report - all unattended for cron execution.
---

# Daily Competition Scout

Automated end-to-end workflow for cron/scheduled execution. Runs completely unattended with no user prompts.

## What This Skill Does

1. Scrapes all listing pages (competitions.com.au, netrewards.com.au)
2. Fetches full details for each new competition
3. Checks for duplicates against existing GitHub issues
4. Applies auto-filter tags based on user preferences
5. Creates GitHub issues for new competitions
6. For each new, non-filtered competition:
   - Runs strategy analysis
   - Generates entry drafts using matching saved stories
   - Persists analysis and entries as comments
7. Outputs structured summary report

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

```bash
# Determine target repository
TARGET_REPO="${TARGET_REPO:-discreteds/competition-scout-25WOL}"

# Fetch user preferences from data repo
PREFERENCES=$(gh api repos/$TARGET_REPO/contents/CLAUDE.md -H "Accept: application/vnd.github.raw" 2>/dev/null)
```

Parse from CLAUDE.md:
- Auto-filter keywords (for-kids, cruise, etc.)
- Saved stories for entry composition
- Personal context (partner name, location)

### Phase 2: Scrape Listings

```bash
# Scrape all listing pages
python skills/comp-scout-scrape/scraper.py listings > /tmp/listings.json
```

Output: List of competitions with basic info (URL, title, prize, closing date)

### Phase 3: Check for Existing Issues

```bash
# Get all existing competition issues
gh issue list -R "$TARGET_REPO" \
  --label "competition" \
  --state all \
  --json number,title,body,state,labels \
  --limit 500 > /tmp/existing.json
```

Compare by:
1. URL in issue body (exact match)
2. Normalized title similarity (>80%)

Categorize each scraped competition:
- **New**: Not found in existing issues
- **Duplicate**: Same competition found on different site (add comment)
- **Tracked**: Already has an issue

### Phase 4: Fetch Full Details

For new competitions only:

```bash
# Build URL list
NEW_URLS='{"urls": ["url1", "url2", ...]}'

# Batch fetch details
echo "$NEW_URLS" | python skills/comp-scout-scrape/scraper.py details-batch > /tmp/details.json
```

### Phase 5: Apply Auto-Filters

For each new competition, check against filter keywords from CLAUDE.md:

```
for-kids keywords: kids, children, baby, toddler, Lego, Disney, family pack
cruise keywords: cruise, P&O, Carnival, Royal Caribbean
```

If competition title/prize matches keywords:
- Mark as filtered
- Will be created + immediately closed with filter label

### Phase 6: Persist New Competitions

#### For Non-Filtered Competitions

```bash
gh issue create -R "$TARGET_REPO" \
  --title "$TITLE" \
  --label "competition" \
  --label "25wol" \
  --body "..."

gh issue edit $ISSUE_NUMBER -R "$TARGET_REPO" --milestone "$CLOSING_MONTH"
```

#### For Filtered Competitions

```bash
# Create for record-keeping
gh issue create -R "$TARGET_REPO" \
  --title "$TITLE" \
  --label "competition" \
  --label "$FILTER_LABEL" \
  --body "..."

# Immediately close
gh issue close $ISSUE_NUMBER -R "$TARGET_REPO" \
  --comment "Auto-filtered: matches '$KEYWORD' in preferences"
```

#### For Duplicate Sources

```bash
gh issue comment $EXISTING_ISSUE -R "$TARGET_REPO" \
  --body "### Also found on $OTHER_SITE..."
```

### Phase 7: Analyze and Compose (Non-Filtered Only)

For each new, non-filtered competition:

#### 7a. Strategy Analysis

Generate strategy using comp-scout-analyze patterns:
- Identify sponsor category and brand voice
- Determine winning tone
- Generate 3-5 angle ideas

```bash
gh issue comment $ISSUE_NUMBER -R "$TARGET_REPO" --body "## Strategy Analysis..."
```

#### 7b. Match Saved Stories

Check saved stories from CLAUDE.md against competition:
- Match story keywords to prompt/brand/prize
- Select best matching story (or use generic approach)

#### 7c. Compose Entries

Generate 3-5 entry variations using:
- Matched story context (if available)
- Appropriate arc structure for sponsor type
- Personal context from CLAUDE.md

```bash
gh issue comment $ISSUE_NUMBER -R "$TARGET_REPO" --body "## Entry Drafts..."
gh issue edit $ISSUE_NUMBER -R "$TARGET_REPO" --add-label "entry-drafted"
```

### Phase 8: Check Closing Soon

Query for competitions closing within 3 days:

```bash
gh issue list -R "$TARGET_REPO" \
  --label "competition" \
  --state open \
  --json number,title,body,labels
```

Parse closing dates and flag urgent items.

### Phase 9: Output Summary Report

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

All choices are logged in the report for user review.

## Error Handling

| Error | Behavior |
|-------|----------|
| Scrape fails for one site | Log error, continue with other site |
| Issue creation fails | Log error, skip to next competition |
| Detail fetch fails | Use listing data only, note incomplete |
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

## Integration with Other Skills

This skill **orchestrates** the workflow using patterns from:

| Skill | Used For |
|-------|----------|
| comp-scout-scrape | Scraping and batch detail fetching |
| comp-scout-analyze | Strategy analysis patterns |
| comp-scout-compose | Entry generation patterns |
| comp-scout-persist | GitHub issue creation |

Individual skills remain available for interactive use when you want manual control.

## Example Cron Log Output

```
$ claude -p "Perform daily competition scout"

Starting daily competition scout...

Phase 1: Loading configuration
  Target repo: discreteds/competition-scout-25WOL
  Filter rules: for-kids (9 keywords), cruise (6 keywords)
  Saved stories: 2 available

Phase 2: Scraping listings
  competitions.com.au: 8 competitions
  netrewards.com.au: 5 competitions
  Total: 13 competitions

Phase 3: Checking existing issues
  Existing issues: 42
  New: 5
  Duplicates: 1
  Already tracked: 7

Phase 4: Fetching full details
  Fetched 5 competition details

Phase 5: Applying filters
  Filtered: 2 (1 for-kids, 1 cruise)
  Remaining: 3

Phase 6: Persisting
  Created 3 new issues: #43, #44, #45
  Created 2 filtered issues (closed): #46, #47
  Added 1 duplicate comment to #38

Phase 7: Analyzing and composing
  #43: Strategy added, 3 entries drafted (using saved story)
  #44: Strategy added, 4 entries drafted
  #45: Strategy added, 3 entries drafted

## Daily Competition Scout Report - 2025-12-09
[Full report as shown above]
```
