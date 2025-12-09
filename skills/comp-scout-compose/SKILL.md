---
name: comp-scout-compose
description: Generate authentic, memorable competition entries (25 words or less) and auto-persist to GitHub issue. Creates multiple variations with different arcs and tones.
---

# Competition Entry Composer

Generate authentic, memorable "25 words or less" competition entries and **automatically save to GitHub issue**.

## What This Skill Does

1. Gathers user context to find authentic angles
2. Generates 3-5 entry variations with different arcs
3. Rates and recommends the strongest entries
4. **Auto-persists entries as comment on GitHub issue**
5. **Adds `entry-drafted` label to the issue**

**No manual "please save entries" step required.**

## Input

- Strategy from `comp-scout-analyze` (recommended)
- OR competition details (prompt, word_limit, brand)
- User context (personal connection, preferences)
- **issue_number** (for auto-persist)

## Workflow

### Step 1: Gather User Context

Before drafting, ask clarifying questions:

**Essential:**
- What genuine experience or connection do you have with this brand/product?
- Any specific memory or story that relates to the prompt?

**Helpful:**
- Tone preference: funny, sincere, or mix?
- Anyone you'd nominate instead of yourself? (partner, family member)
- Any personal details that might be relevant? (job, hobby, family situation)

**If user has no connection:**
- What's generally true for you that could relate?
- What would you actually do with this prize?
- What's the honest version of your situation?

### Step 2: Find the Authentic Hook

Generic entries lose. The goal is specificity that makes judges smile in recognition.

**Transformation examples:**

| Generic | Specific |
|---------|----------|
| "I love cooking" | "Sunday arvo freezer audit before the weekly shop" |
| "I want to relax" | "Like my shoulders have dropped from my ears" |
| "I like Japan" | "Horseback archery champs, bonsai masters, noodle competitions" |
| "I need ice" | "The person who forgot to refill the ice tray mid-barbecue" |
| "I love coffee" | "The only five minutes that's mine before school run chaos" |
| "I want to travel" | "We've done Japan at full speed. Time to walk it slowly." |

**Questions to surface hooks:**
- What's actually true for you?
- What's the embarrassing/honest version?
- What specific detail would make a judge smile in recognition?
- What do you already do that relates to this prize/brand?

### Step 3: Select Entry Arc Structure

Choose the arc that best fits the tone and content:

---

**Sincere Arc** (wellness, luxury, emotional prizes)

Structure:
1. Honest admission of current state
2. Aspiration or need
3. Warm landing

Example (wellness retreat):
> "My partner nurtures everyone else first. Always. Her mind, body, and soul have been running on empty. She's earned this."

---

**Comedic Arc** (setup → pivot → callback)

Structure:
1. Setup (unexpected angle or joke)
2. Pivot to genuine substance
3. Callback that recontextualises the setup

Example (solar panels):
> "Befriend a neighbour with a pool. Run the laundry while the sun shines. I can watch my panels work, while I float!"

---

**Self-Deprecating Arc** (relatable failure → redemption)

Structure:
1. Confession (the annual shame)
2. Constraint (why it persists)
3. Resolution (this fixes it)
4. Optional undercut (but there's always something else)

Example (ice maker):
> "Every summer barbecue I realise I'm the person who forgot to refill the ice tray, and I can't do a servo run mid-barbecue. Finally, I become the host who is prepared for everything—except an empty gas bottle."

---

**List → Pivot Arc** (travel, experience prizes)

Structure:
1. Quick list establishing credentials ("Done X, Y, Z")
2. Identify the gap ("But we've never...")
3. Land on the aspiration

Example (Japan walking tour):
> "Horseback archery world champs. World's best bonsai. Noodle-making competitions. We've done Japan at full speed. Time to finally walk it slowly."

---

**Sensory Arc** (food, beverage, experiential)

Structure:
1. Scene-setting
2. Vivid sensory detail
3. Emotional resonance

Example (early holiday memory):
> "Ulladulla at four. Dad handed me my first oyster. Too slimy to chew. Swallowed it whole like a little pelican."

---

### Step 4: Draft Multiple Versions

Generate 3-5 entries with different approaches:

For each entry, provide:
- The entry text
- Word count (must be ≤ word_limit)
- Arc type used
- Approach description
- Landing strength (1-5)
- Notes on why it works

### Step 5: Refine Based on Feedback

After user selects a direction:

**Tighten word economy:**
- Remove redundant words
- Combine phrases
- Use stronger single words instead of phrases

**Strengthen the landing:**
- Last line should resonate
- Consider callbacks to earlier elements
- Avoid trailing off

**Check rhythm:**
- Short sentences for punch
- Longer sentences for warmth
- Vary sentence length for flow

**Verify compliance:**
- Word count within limit
- Addresses the actual prompt
- Authentic to user's voice

### Step 6: Final Quality Check

Before delivering final entry:

- [ ] Meets word limit exactly or under
- [ ] Contains specific detail (not generic)
- [ ] Has clear structure/arc
- [ ] Landing line is strong
- [ ] Authentic to user's voice
- [ ] Appropriate tone for sponsor/audience
- [ ] No repeated words doing the same job
- [ ] No clichés or overused phrases
- [ ] Would make a judge smile or nod

### Step 7: Auto-Persist to GitHub Issue

Add entries as comment and add label:

```bash
# Add entry drafts as comment
gh issue comment $ISSUE_NUMBER -R "$TARGET_REPO" --body "$(cat <<'EOF'
## Entry Drafts

### Option 1 ({word_count} words) ⭐⭐⭐⭐⭐
> {entry_text}

Arc: {arc_type}
Notes: {notes}

### Option 2 ({word_count} words) ⭐⭐⭐⭐
> {entry_text}

Arc: {arc_type}
Notes: {notes}

### Option 3 ({word_count} words) ⭐⭐⭐
> {entry_text}

Arc: {arc_type}
Notes: {notes}

**Recommendation:** Option {n} - {reason}

---
*Generated: {date}*
EOF
)"

# Add label to indicate entries are drafted
gh issue edit $ISSUE_NUMBER -R "$TARGET_REPO" --add-label "entry-drafted"
```

### Step 8: Report Completion

```
✅ Entries saved to issue #42!

**3 entry options drafted:**
- Option 1 (24 words) ⭐⭐⭐⭐⭐ - Self-deprecating list
- Option 2 (25 words) ⭐⭐⭐⭐ - Confession
- Option 3 (23 words) ⭐⭐⭐ - Practical humour

**Recommendation:** Option 1

**Label added:** `entry-drafted`

Ready to submit? Let me know which option you choose!
```

## Anti-Patterns to Avoid

**Tone:**
- Generic enthusiasm ("I would love to win!")
- Empty superlatives ("This amazing prize")
- Begging or desperation ("Please pick me")
- Over-explaining the joke

**Content:**
- Lies or fabricated stories
- Clichés judges will see hundreds of times
- Vague generalities
- Repeated words doing the same job

**Structure:**
- Flat endings that don't land
- No clear arc or progression
- Starting with "I" (consider varying)
- Wasting words on setup

## Special Entry Types

### "Why do you deserve to win?" Prompts

- Avoid begging or sad stories unless genuinely relevant
- Frame around appreciation, not desperation
- Self-awareness wins over earnestness
- Consider nominating someone else for emotional weight

### Naming Competitions

- Name should be memorable, punchy, ideally wordplay
- Explanation builds the story behind the name
- Consider: cultural references, product features as wordplay, personality

### Haiku/Poetry Requests

- Count syllables carefully (5-7-5 for haiku)
- Prioritise imagery over explanation
- Land on a strong final image

## Output Format

```yaml
entries:
  - text: "The actual entry text goes here, exactly as it should be submitted."
    word_count: 24
    arc_type: "self_deprecating"
    approach: "Confession → resolution with self-aware undercut"
    landing_strength: 4
    notes: "Relatable summer hosting struggle, personality in the undercut"

  - text: "Second variation with different approach..."
    word_count: 23
    arc_type: "sincere"
    approach: "Problem → vivid consequence → hopeful resolution"
    landing_strength: 5
    notes: "Strongest landing, 'dignity melts' is memorable"

  - text: "Third variation..."
    word_count: 25
    arc_type: "comedic_list"
    approach: "Establish credentials → pivot to weakness"
    landing_strength: 3
    notes: "Solid structure but landing could be stronger"

recommendation: 1  # 0-indexed
recommendation_reason: "Best balance of specificity, personality, and strong landing"
issue_number: 42
persisted: true
```

## Example Session

```
User: Write entries for issue #42

Claude: I'll write entries for this competition.

[Reads issue #42]

Competition: Win a $500 Coles Gift Card
Prompt: "Tell us in 25 words or less what you'd buy"

First, a few questions to find your authentic angle:

1. What do you typically buy at Coles?
2. Any specific situation where $500 would help?
3. Tone preference: practical/sincere or humorous?

User: We do our weekly shop there. Always buying for the kids. Would love to
just buy nice things for once instead of bulk snacks and school lunch stuff.

Claude: That's a great angle - the "finally treating yourself" vs endless kid supplies.

## Entry Drafts

### Option 1: Self-Deprecating List (24 words) ⭐⭐⭐⭐⭐
> "Tiny teddies. Zooper doopers. Le Snaks. Cheese stringers. For once, I'd
> fill a trolley with things that aren't in a lunchbox."

Arc: List of kid stuff → pivot to self
Landing: 5/5 - "aren't in a lunchbox" is specific and relatable

### Option 2: Confession (25 words) ⭐⭐⭐⭐
> "I know every lunchbox snack by heart but forgot what cheese I actually
> like. Five hundred dollars of rediscovering my own taste buds."

Arc: Confession → resolution
Landing: 4/5 - "own taste buds" works but slightly abstract

### Option 3: Practical Humour (23 words) ⭐⭐⭐
> "School lunches sorted for a term. Then with whatever's left—maybe
> $4.50—something from the fancy cheese section. Just for me."

Arc: Practical → undercut → treat
Landing: 3/5 - Good but "$4.50" joke might not land for everyone

**Recommendation:** Option 1 - The specific snack names are immediately
recognisable to any parent, and the landing is both relatable and punchy.

[Runs: gh issue comment 42 --body "..."]
[Runs: gh issue edit 42 --add-label "entry-drafted"]

✅ Entries saved to issue #42!
- Added 3 entry options as comment
- Added `entry-drafted` label

Which option do you want to submit?
```

## Integration

This skill:
- Uses strategy from `comp-scout-analyze` (optional but recommended)
- Auto-saves entries to GitHub issue
- Adds `entry-drafted` label for tracking
- Can be followed by submission confirmation (add `entry-submitted` label)
