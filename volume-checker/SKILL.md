---
name: volume-checker
version: "1.0"
description: >
  Checks search volume and keyword difficulty for an entity-attribute pair
  and its verbalizations using Ahrefs, identifies the highest-volume
  verbalization as the Target Keyword, and applies the skip threshold for
  zero-volume pairs. Use this skill whenever volume data is needed for
  queries, or when someone says "check volume", "what's the search volume",
  "pull keyword data", "check Ahrefs", or "validate this keyword". Always
  trigger when volume or keyword difficulty data is needed — even if phrased
  casually.

inputs:
  required:
    - type: text
      label: entity-attribute-pair
      description: >
        The entity-attribute pair to check (e.g., "red light therapy + dry eyes").
    - type: text
      label: verbalizations
      description: >
        The list of verbalizations from the verbalization-generator skill.
  optional:
    - type: text
      label: country
      description: >
        Target country for volume data. Defaults to "us" if not specified.
    - type: text
      label: market-context
      description: >
        Industry context for zero-volume assessment — market size, trends,
        competitive landscape. Used to evaluate the emerging market argument.

outputs:
  - type: text
    label: volume-report
    description: >
      Volume and KD data for all verbalizations, identified Target Keyword,
      and skip/keep recommendation for zero-volume pairs.

tools_used:
  - Ahrefs:keywords-explorer-overview

chains_from:
  - verbalization-generator
chains_to:
  - serp-validator

tags:
  - seo
  - volume
  - keyword-research
  - stories-to-queries
---

# Volume Checker

## What This Skill Does

Takes an entity-attribute pair and its verbalizations, pulls search volume and
keyword difficulty from Ahrefs, identifies the highest-volume verbalization as
the Target Keyword, and recommends skip or keep for zero-volume pairs. The
output is volume-validated data ready for SERP validation and topical map entry.

---

## Context the Agent Needs

The highest-volume verbalization of an entity-attribute pair is usually the
shortest spelling — fewest words, least context. This is search behavior, not
strategy. The Target Keyword is whichever verbalization has the most volume,
because that's what will drive the most organic traffic to the page.

Volume data from keyword tools is directional, not absolute. A tool showing
zero volume doesn't mean nobody searches for it — it means the tool can't
measure it. In emerging markets (especially AI-related topics), zero-volume
pairs can still be valuable if the market is large, the trend is upward, and
impression data can validate later.

The skip threshold requires ALL three conditions to be true before skipping:
zero volume in tools, no meaningful SERP results, and no emerging market
argument. If even one signal exists, keep the pair.

Ahrefs requires explicit country filtering for accurate local data. Always
specify the target country. Default to "us" if none is specified.

**Key constraint:** Always use `keywords-explorer-overview` with explicit
country and field selection. Never estimate volume — pull real data.

---

## Workflow — Execute In This Order

### STEP 1: Prepare the Query List

Build the list of queries to check in Ahrefs.

**Input:** Entity-attribute pair and its verbalizations.

**Process:**
1. Compile the full list: raw pair + all core, question, evaluation, and long-tail verbalizations
2. Prioritize: check the raw pair and core verbalizations first (these are most likely to have volume)
3. If the list exceeds 20 queries, prioritize by likely volume (shorter queries first, core before long-tail) and batch the rest for a second check if needed
4. Determine the target country — use the member's specified country, or default to "us"

**Output:** Ordered query list ready for Ahrefs lookup.

---

### STEP 2: Pull Volume and KD from Ahrefs

Call Ahrefs for volume data on all queries.

**Input:** Query list from Step 1.

**Process:**
1. Use `Ahrefs:keywords-explorer-overview` with:
   - `keywords`: comma-separated list of queries
   - `country`: target country code
   - `select`: "keyword,volume,difficulty,cpc,traffic_potential"
2. Parse the response — extract volume, KD, CPC, and traffic potential for each query
3. If Ahrefs returns no data for a query, record it as volume = 0, KD = 0
4. If the Ahrefs call fails entirely, retry once. If still failing, note the failure and proceed to Step 4 with volume data marked as unavailable.

**Output:** Volume data table for all queries.

**Decision gate:**
- If all queries have volume data → proceed to Step 3
- If Ahrefs is unavailable → skip to Step 4 with all queries marked as "volume unavailable — needs manual check"

---

### STEP 3: Identify the Target Keyword

Determine which verbalization should be the primary keyword target.

**Input:** Volume data from Step 2.

**Process:**
1. Sort all verbalizations by volume (descending)
2. The highest-volume verbalization becomes the Target Keyword
3. If multiple verbalizations share the same volume, prefer the shorter one (it's more versatile as a page target)
4. If the raw entity-attribute pair has the highest volume, it's the Target Keyword (this is the most common case)
5. Record CPC and traffic potential for the Target Keyword — these go into the Notes field downstream

**Output:** Identified Target Keyword with its volume, KD, CPC, and traffic potential.

---

### STEP 4: Apply Skip Threshold

For pairs where the Target Keyword has zero volume, evaluate whether to keep or skip.

**Input:** Volume data from Step 2, market context if available.

**Process:**
1. If the Target Keyword has volume > 0 → keep. No further evaluation needed.
2. If volume = 0, check condition 1: are there meaningful SERP results? (This will be confirmed downstream by the serp-validator, but a preliminary check can be done by looking at whether Ahrefs shows any traffic potential or related keywords.)
3. If volume = 0, check condition 2: is there an emerging market argument?
   a. Is this an AI-related or new technology topic? → likely emerging
   b. Is the broader market large? (multi-billion dollar, hundreds of thousands of potential searchers) → supports keeping
   c. Is the trend direction upward? (growing industry, increasing interest) → supports keeping
   d. Can impression data validate later? → always yes for any indexed page
4. If ALL three are absent (no volume, no SERP signal, no emerging market) → recommend Skip
5. If at least one signal exists → recommend Keep with rationale

**Output:** Skip or Keep recommendation with reasoning.

---

## Output Format

```
**Entity-Attribute Pair:** [entity] + [attribute]
**Target Country:** [country code]

**Target Keyword:** [highest-volume verbalization]
**Volume:** [number]
**Keyword Difficulty:** [number]
**CPC:** $[number]
**Traffic Potential:** [number]

**All Verbalizations by Volume:**
| Verbalization | Volume | KD | CPC |
|---|---|---|---|
| [query 1] | [vol] | [kd] | [cpc] |
| [query 2] | [vol] | [kd] | [cpc] |
| [query 3] | [vol] | [kd] | [cpc] |
| ... | ... | ... | ... |

**Recommendation:** [Keep / Skip]
**Rationale:** [Why — volume confirmed / emerging market argument / no signal]

**Notes for Topical Map:**
Vol: [X] | KD: [X] | CPC: $[X] | TP: [X] — [strategic context]
```

**Formatting rules:**
- Sort the volume table descending by volume
- Target Keyword is always the first row in the table
- Zero-volume queries show "0" not blank
- The Notes for Topical Map line is pre-formatted to paste directly into the Notes field of the topical map
- If Ahrefs was unavailable, replace the table with: "Volume data unavailable — Ahrefs connection failed. Needs manual check."

---

## Edge Cases & Judgment Calls

**When all verbalizations have zero volume:**
Don't skip automatically. Check the emerging market conditions. If the broader entity has volume (e.g., "red light therapy" has volume but "red light therapy + [niche attribute]" doesn't), the pair may still be worth keeping — the entity's authority lifts the niche page.

**When volume data seems wrong:**
Ahrefs occasionally shows zero for queries that clearly have traffic (especially newer or rapidly growing queries). If the entity is well-known and the attribute is common, note the discrepancy. The pair is likely worth keeping.

**When the country matters:**
A pair targeting a local audience (e.g., "plumber + emergency" in Australia) must use the correct country code. US volume for a local Australian business is meaningless. Always confirm the target country.

**When a tool call to Ahrefs fails:**
Retry once. If still failing, proceed without volume data. Flag every query as "volume unavailable — needs manual check." The pair can still be SERP-validated and kept as an Idea pending volume confirmation.

---

## What This Skill Does NOT Do

- Does NOT extract entity-attribute pairs — that's the entity-extractor skill
- Does NOT generate verbalizations — that's the verbalization-generator skill
- Does NOT validate SERP intent or page split decisions — that's the serp-validator skill
- Does NOT decide page architecture — that's QDP downstream
- If the member asks "should this be its own page?" → this skill provides volume data, QDP makes the page decision

---

## Examples

**Example 1: Clear winner with volume**

Input:
Entity-attribute pair: red light therapy + dry eyes
Verbalizations: [red light therapy dry eyes, red light therapy for dry eyes, does red light therapy work for dry eyes, red light therapy for dry eyes at home, best red light therapy for dry eyes]

Output (abbreviated):
```
**Target Keyword:** red light therapy for dry eyes
**Volume:** 1,300
**KD:** 15
**CPC:** $2.40
**Traffic Potential:** 2,100

**All Verbalizations by Volume:**
| Verbalization | Volume | KD | CPC |
|---|---|---|---|
| red light therapy for dry eyes | 1,300 | 15 | $2.40 |
| red light therapy dry eyes | 880 | 12 | $2.10 |
| best red light therapy for dry eyes | 320 | 18 | $3.50 |
| does red light therapy work for dry eyes | 210 | 8 | $1.80 |
| red light therapy for dry eyes at home | 90 | 6 | $1.50 |

**Recommendation:** Keep
**Rationale:** Strong volume confirmed across multiple verbalizations.

**Notes for Topical Map:**
Vol: 1.3K | KD: 15 | CPC: $2.40 | TP: 2.1K — Strong demand, low difficulty, multiple high-volume verbalizations
```

Why this is correct: The connector variant "for dry eyes" outperformed the raw pair, which is common. All verbalizations have volume, confirming this is a solid content item.

---

**Example 2: Zero volume with emerging market argument**

Input:
Entity-attribute pair: AI prospecting tools + sales
Verbalizations: [AI prospecting tools sales, AI prospecting tools for sales, best AI prospecting tools for sales teams]
Market context: Sales technology is a multi-billion dollar market. AI tools are trending rapidly.

Output (abbreviated):
```
**Target Keyword:** AI prospecting tools for sales
**Volume:** 0
**KD:** 0

**Recommendation:** Keep
**Rationale:** Zero volume in Ahrefs, but: (1) sales technology is a multi-billion dollar market with hundreds of thousands of practitioners, (2) AI tools are trending with rapid adoption across all sales functions, (3) page can collect impression data to validate demand within 30-60 days. Strong emerging market argument.

**Notes for Topical Map:**
Vol: 0 | KD: 0 | Emerging market — multi-billion dollar sales tech market, AI trending, validate with impression data
```

Why this is correct: The skip threshold was not met because the emerging market argument is strong. The pair is kept with clear rationale documented.
