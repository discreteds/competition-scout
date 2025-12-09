---
name: comp-scout-compose
description: Generate authentic, memorable competition entries (25 words or less). Creates multiple variations with different arcs and tones, then refines based on feedback.
---

# Competition Entry Composer

Generate authentic, memorable "25 words or less" competition entries.

## Input

- Strategy from `comp-scout-analyze` (recommended)
- OR competition details (prompt, word_limit, brand)
- User context (personal connection, preferences)

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

**Example output:**

```
## Entry Variations

### 1. Self-Deprecating (24 words) ⭐⭐⭐⭐
"Every summer barbecue I'm the one who forgot to refill ice trays.
This year, I finally become the prepared host. Gas bottle pending."

Arc: Self-deprecating confession → resolution → undercut
Landing: 4/5 - "Gas bottle pending" callback adds personality

### 2. Sincere (23 words) ⭐⭐⭐⭐⭐
"Summer entertaining means hauling bags of servo ice in 40-degree heat.
My dignity melts faster than the ice. This would change everything."

Arc: Problem → consequence → resolution
Landing: 5/5 - "dignity melts" is memorable and specific

### 3. Comedic (25 words) ⭐⭐⭐
"I've mastered pavlova, perfected my burger technique, and memorised everyone's
drink orders. Yet 'did anyone refill the ice?' remains my nemesis."

Arc: List credentials → pivot to weakness
Landing: 3/5 - Solid but "nemesis" feels slightly forced

**Recommendation:** Entry #2 - strongest landing, relatable specificity,
good word economy.
```

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
```

## Example Session

```
User: Write entries for this competition

Competition:
- Brand: Coles
- Prompt: "Tell us in 25 words or less what you'd buy with a $500 gift card"
- Word limit: 25

Claude: I'll help you write entries for the Coles gift card competition.

First, a few questions to find your authentic angle:

1. What do you typically buy at Coles? (groceries, specific products, household items)
2. Any specific situation where $500 would help? (hosting, family, specific need)
3. Tone preference: practical/sincere or humorous?

User: We do our weekly shop there. Always buying for the kids. Would love to
just buy nice things for once instead of bulk snacks and school lunch stuff.

Claude: That's a great angle - the "finally treating yourself" vs endless kid supplies.
Here are some variations:

## Entry Variations

### 1. Self-Deprecating List (24 words) ⭐⭐⭐⭐⭐
"Tiny teddies. Zooper doopers. Le Snaks. Cheese stringers. For once, I'd
fill a trolley with things that aren't in a lunchbox."

Arc: List of kid stuff → pivot to self
Landing: 5/5 - "aren't in a lunchbox" is specific and relatable

### 2. Confession (25 words) ⭐⭐⭐⭐
"I know every lunchbox snack by heart but forgot what cheese I actually
like. Five hundred dollars of rediscovering my own taste buds."

Arc: Confession → resolution
Landing: 4/5 - "own taste buds" works but slightly abstract

### 3. Practical Humour (23 words) ⭐⭐⭐
"School lunches sorted for a term. Then with whatever's left—maybe
$4.50—something from the fancy cheese section. Just for me."

Arc: Practical → undercut → treat
Landing: 3/5 - Good but "$4.50" joke might not land for everyone

**Recommendation:** Entry #1 - The specific snack names are immediately
recognisable to any parent, and the landing is both relatable and punchy.

Want me to refine any of these, or try a different angle?
```

## Integration

Entries can be:
1. Added as a comment on the competition's GitHub issue
2. Refined through multiple iterations
3. Tracked with status labels (entry-drafted, entry-submitted)
