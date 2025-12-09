---
name: comp-scout-analyze
description: Generate strategic analysis for competition entries. Identifies winning tone, themes, and angles based on sponsor type and brand voice.
---

# Competition Strategy Analyzer

Generate strategic analysis for "25 words or less" competition entries.

## Input

Competition data from `comp-scout-scrape`:
- url, title, brand
- prize_summary, prize_value
- prompt, word_limit
- closing_date

## Workflow

### Step 1: Identify Sponsor Category

Classify the brand/sponsor into one of these categories:

| Category | Examples | Indicators |
|----------|----------|------------|
| **Wellness/luxury** | Spas, skincare, premium travel, health retreats | Premium language, self-care themes, aspirational imagery |
| **Tech/gaming** | Electronics, gaming, apps, software | Features, specs, community, innovation |
| **Food/beverage** | Grocery, restaurants, drinks, snacks | Sensory language, recipes, family moments, occasions |
| **Travel** | Airlines, hotels, destinations, experiences | Adventure, discovery, escape, bucket-list |
| **Retail/general** | Department stores, homewares, fashion | Lifestyle, value, everyday convenience |
| **Rural/agricultural** | Farm supplies, outdoor equipment, regional brands | Practical language, weather, land, hard work |

### Step 2: Determine Winning Tone

Based on sponsor category, identify the likely winning tone:

| Sponsor Type | Likely Winning Tone |
|--------------|---------------------|
| Wellness/luxury | Sincere, aspirational, emotional honesty. Judges want to feel you genuinely need/deserve this. |
| Tech/gaming | Knowledgeable enthusiasm, self-aware humour. Show you understand the product without being a fanboy. |
| Food/beverage | Relatable moments, sensory details. Specific tastes, smells, family traditions. |
| Travel | Discovery, bucket-list energy, specific memories. What makes this destination special to YOU? |
| Retail/general | Personality, memorability, genuine need. Stand out from generic "I'd love to win" entries. |
| Rural/agricultural | Practical, financially savvy, honest about habits. Down-to-earth authenticity wins. |

### Step 3: Assess Brand Voice

Analyze how the brand communicates:

**Questions to answer:**
- Is the brand formal or casual?
- Do they use humour or stay serious?
- What values do they emphasize? (family, adventure, quality, value, sustainability)
- What language patterns appear in their marketing?
- Who is their target audience?

**Output example:**
> "Casual and friendly, emphasizes family moments and everyday joy. Uses warm, approachable language. Target audience is parents/families."

### Step 4: Analyze the Prompt

Break down what the prompt is really asking:

**Questions to answer:**
- What's the surface-level question?
- What's the emotional response they're hoping for?
- What generic answers will judges see hundreds of times?
- What would make an entry memorable?

**Example:**
> Prompt: "Tell us in 25 words or less why you love our coffee"
>
> Surface: Why do you like coffee?
> Real ask: What specific, personal moment makes our coffee special?
> Generic answers: "I love the taste", "It wakes me up", "Best coffee ever"
> Memorable: Specific sensory detail, unexpected moment, personal ritual

### Step 5: Generate Angle Ideas

Create 3-5 distinct approaches, each with:
- Different emotional hook
- Different arc structure (sincere, comedic, self-deprecating, list-pivot)
- Brief description of the strategy

**Format:**
```
1. **Sincere - The morning ritual**
   Focus on a specific moment when the product is part of your routine.
   Arc: Honest admission → Sensory detail → Warm landing

2. **Self-deprecating - The confession**
   Admit to a relatable "flaw" that the product addresses.
   Arc: Confession → Constraint → Resolution

3. **Comedic - The unexpected angle**
   Find an unusual perspective that subverts expectations.
   Arc: Setup → Pivot → Callback

4. **Sensory - The specific detail**
   Zero in on one vivid sensory moment.
   Arc: Scene-setting → Sensory detail → Emotional resonance

5. **List-pivot - The credentials**
   Quick list establishing context, then pivot to the real point.
   Arc: List → Gap → Aspiration
```

### Step 6: Identify What to Avoid

Common pitfalls for this type of competition:

**Always avoid:**
- Generic superlatives ("amazing", "best ever", "fantastic")
- Begging or desperation ("please pick me", "I really need this")
- Lies or fabricated stories
- Clichés the judges will see hundreds of times
- Empty enthusiasm without specificity

**Category-specific pitfalls:**

| Category | Avoid |
|----------|-------|
| Wellness/luxury | Sounding entitled, over-the-top drama |
| Tech/gaming | Being too technical, gatekeeping |
| Food/beverage | Generic taste descriptions, "yummy" |
| Travel | Bucket-list clichés, generic wanderlust |
| Retail/general | "I want free stuff" energy |
| Rural/agricultural | City-slicker posturing, romanticism |

## Output Format

```yaml
strategy:
  competition_url: "https://..."
  brand: "Example Brand"
  brand_voice: "Casual and friendly, emphasizes family moments"
  sponsor_category: "food/beverage"
  recommended_tone: "Relatable with sensory details, warm and specific"
  approach: |
    Focus on a specific moment when the product is part of your life.
    Avoid generic taste descriptions - instead, anchor to a memory,
    ritual, or unexpected moment. The best entries will make judges
    nod in recognition.
  themes_to_use:
    - "Family traditions"
    - "Sensory memories"
    - "Everyday rituals"
    - "Unexpected moments"
  words_to_consider:
    - "ritual"
    - "moment"
    - "discover"
    - "finally"
  angle_ideas:
    - "Sincere: The Sunday morning ritual that wouldn't be complete without it"
    - "Self-deprecating: Confessing to hiding the good stuff from the family"
    - "Sensory: The specific smell that triggers childhood memories"
    - "Comedic: The unexpected place/time you've enjoyed the product"
    - "List-pivot: All the things you've tried, but this is the one that stuck"
  avoid:
    - "I love [brand]"
    - "Best [product] ever"
    - "Please pick me"
    - "My family would love this"
    - "Delicious" / "Yummy" / "Amazing"
```

## Example Session

```
User: Analyze this competition for strategy

Competition:
- Brand: Nespresso
- Prompt: "Complete this sentence in 25 words or less: My morning coffee..."
- Prize: Year's supply of coffee ($1,200)

Claude:

## Strategy Analysis: Nespresso Competition

**Sponsor Category:** Food/beverage (premium)

**Brand Voice:** Sophisticated but accessible. Nespresso positions itself as
everyday luxury - not pretentious, but elevated. George Clooney campaigns
suggest self-aware humour is welcome.

**Recommended Tone:** Sensory and specific, with room for subtle wit.
The "morning coffee" framing invites ritual/routine angles.

**What they're really asking:** What specific, personal moment makes your
morning coffee ritual special? They want to see themselves as part of
meaningful moments, not just caffeine delivery.

**Themes to use:**
- Morning rituals and routines
- Sensory details (aroma, warmth, first sip)
- The pause before chaos begins
- Small luxuries

**Words to consider:**
- ritual, moment, pause, before
- aroma, warmth, first
- finally, only, mine

**Angle ideas:**

1. **The Pause** - Focus on the quiet moment before the day begins
   "...is the only five minutes that's truly mine before the school run chaos begins."

2. **Sensory Detail** - Zero in on one specific sensation
   "...starts when the aroma reaches the bedroom. By the time I reach the kitchen, I'm already half-awake."

3. **Self-Deprecating** - Admit to needing it more than you'd like
   "...is non-negotiable. I've tried being a morning person without it. My family has asked me to stop trying."

4. **The Ritual** - Describe the specific routine
   "...follows the same steps every day. Capsule, cup, first sip by the window. Then, and only then, I speak."

5. **Unexpected Angle** - Subvert the "morning" framing
   "...sometimes happens at 3pm when I've earned a quiet moment and nobody's watching."

**Avoid:**
- "I need coffee to function" (overdone)
- "Best coffee ever" (generic)
- "I'm not a morning person" (cliché)
- "Delicious" or taste descriptions without specificity
```

## Integration

This skill outputs a `strategy` object that can be:
1. Added as a comment on the competition's GitHub issue (via `comp-scout-persist`)
2. Passed to `comp-scout-compose` to generate actual entries
