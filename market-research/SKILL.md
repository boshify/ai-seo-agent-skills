---
name: market-research
version: "1.0"
description: >
  Researches and sizes a member's target market using business metrics, not search
  volume. Use this skill whenever the target-market-landscape-analysis process reaches
  Step 2, or whenever a member asks about their market size, TAM, or industry landscape.
  This skill produces a structured market overview with TAM estimate, growth trajectory,
  and demand signals. Always trigger when market sizing, TAM, industry analysis, or
  market research intent is present — even if phrased casually.

inputs:
  required:
    - type: text
      label: "industry-description"
      description: "The member's industry or market as confirmed in the process scope step"
  optional:
    - type: text
      label: "business-context"
      description: "Additional context from brand assessment — services offered, audience served, geography"
    - type: text
      label: "core-keywords"
      description: "1-3 core keywords the member identified for their business"

outputs:
  - type: markdown
    label: "market-overview"
    description: "Structured market overview with TAM estimate, growth trajectory, and demand signals"

tools_used:
  - web_search
  - web_fetch

chains_from: []
chains_to:
  - competitor-landscape-research

tags:
  - market-research
  - foundation
  - business-strategy
  - TAM
---

# Market Research

## What This Skill Does

Researches and sizes a member's target market using industry data, business logic, and market reports — not search volume. The member gets a structured market overview that frames their opportunity in business terms and feeds into the Target Market Landscape Report.

---

## Context the Agent Needs

This skill exists because most SEO practitioners size markets by keyword volume, which dramatically underestimates the true opportunity — especially for new niches, complex B2B purchases, and AI-driven businesses where search behavior hasn't caught up to demand.

The target-market-landscape methodology mandates sizing the business market: total addressable customers, industry revenue, growth trajectory. Search volume is one demand signal among many — not the primary sizing metric.

For new or AI-driven niches, every new market is a remix of an existing one. "AI-powered sales interview simulation" is new — "pre-hire sales assessments" is the existing market with decades of data. The skill must identify the existing market being remixed and size that.

Market research uses public sources: industry reports, analyst estimates, trade publications, government data, and reputable market research firms. The output doesn't need to be precise to the dollar — a defensible range with clear sourcing is more valuable than false precision.

**Key constraint:** Size the business market, never the search market. A huge market with low search volume means people don't know what to search for yet — that's an opportunity, not a limitation.

---

## Workflow — Execute In This Order

Do not skip steps. Do not summarize. Produce every section in full.

---

### STEP 1: Confirm the Market Definition

Establish exactly what market is being sized.

**Input:** Industry description from the process scope step + any business context from brand assessment memory.

**Process:**
1. State the market being researched in plain language: "I'm sizing the market for [X]."
2. If the business is in a new or AI-driven niche, identify the existing market it remixes. State both: "Your business operates in [new niche], which remixes the existing [traditional market] market."
3. Confirm geographic scope — is this global, national, or regional? Default to the member's primary operating geography unless the business is clearly global.

**Output:** One-sentence market definition with geographic scope and, if applicable, the traditional market being remixed.

**Decision gate:**
- If the market definition is too broad (e.g., "technology") → narrow to the specific segment the member operates in
- If the market definition is too narrow (e.g., "hot water cylinder repair in Christchurch") → size the broader market first, then estimate the member's addressable slice

---

### STEP 2: Research Market Size and TAM

Find credible data on total addressable market.

**Input:** Market definition from Step 1.

**Process:**
1. Search for industry reports and market sizing data using queries like:
   - "[industry] market size [year]"
   - "[industry] TAM total addressable market"
   - "[industry] industry report revenue"
   - "[industry] market growth forecast"
2. Prioritize sources in this order: government data (Census, BLS, IBIS), major research firms (Gartner, Statista, Grand View Research, Mordor Intelligence), trade associations, reputable business publications
3. Look for: total market revenue, number of businesses or customers in the space, average deal size or customer value if available
4. If the niche is new/AI-driven: search for the traditional market's TAM and note that the new niche is capturing a slice of this existing demand
5. If no credible TAM data exists: estimate from bottom-up. Calculate: (number of potential customers) × (average annual spend on this service/product). State the estimation method clearly.

**Output:** TAM figure or range with source attribution. If estimated, show the calculation method.

**Decision gate:**
- If multiple sources conflict → present the range and note the spread
- If no data exists at all → use bottom-up estimation and flag confidence as low

---

### STEP 3: Assess Growth Trajectory and Demand Signals

Determine whether this market is growing, stable, or shrinking — and why.

**Input:** Market definition and TAM from Steps 1-2.

**Process:**
1. Search for growth rate data:
   - "[industry] market growth rate CAGR"
   - "[industry] industry trends [current year]"
   - "[industry] market forecast"
2. Identify tailwinds (factors accelerating growth): regulatory changes, technology shifts, demographic trends, behavioral changes
3. Identify headwinds (factors slowing growth): market saturation, disruption, declining demand
4. Assess demand signals beyond search volume: trade show attendance, job postings in the space, venture capital investment, new entrants, legislative activity

**Output:** Growth classification (growing / stable / shrinking) with CAGR if available, plus 2-4 key tailwinds or headwinds.

**Decision gate:**
- If the market is clearly shrinking → note it but don't editorialize. The member may have a differentiation angle that works in a contracting market.

---

### STEP 4: Compile Market Overview

Assemble findings into a structured output ready for the report.

**Input:** All findings from Steps 1-3.

**Process:**
1. Write a 2-3 sentence market definition paragraph
2. State the TAM with source
3. State the growth trajectory with key drivers
4. List 2-3 demand signals
5. If AI/new niche: explain why the TAM is larger than search volume suggests, referencing the traditional market

**Output:** Structured market overview in this format:

```
## Market Overview

**Market definition:** [2-3 sentences describing the market]

**Total Addressable Market:** [figure or range] ([source])

**Growth trajectory:** [Growing/Stable/Shrinking] — [CAGR if available]

**Key drivers:**
- [Tailwind or headwind 1]
- [Tailwind or headwind 2]
- [Tailwind or headwind 3]

**Demand signals:** [2-3 signals beyond search volume]

**Note:** [Only if AI/new niche — explain the traditional market being remixed]
```

---

## Output Format

The market overview follows the structure in Step 4. Keep it concise — this is one page of a larger report. No fluff, no filler paragraphs. Data and sourcing only.

**Formatting rules:**
- TAM should be a dollar figure or range, not a vague qualifier like "large"
- Sources must be named — "according to Statista" not "according to industry research"
- Growth trajectory needs a number (CAGR) when available
- Total length: 150-300 words maximum

---

## Edge Cases & Judgment Calls

**When no credible market data exists:**
Use bottom-up estimation. (Potential customers) × (average spend) = estimated TAM. State the method explicitly and flag confidence as low. A rough estimate with transparent math is more useful than "data unavailable."

**When the member operates in multiple markets:**
Size the primary market first — the one that drives the majority of revenue. Note adjacent markets as expansion opportunity but don't size them unless asked.

**When market data is outdated (3+ years old):**
Use it as a baseline and apply the most recent growth rate to project forward. Note: "Based on [year] data from [source], projected at [X]% CAGR."

**When the market seems too small to be interesting:**
Report it honestly. A small TAM with low competition can be more valuable than a massive TAM with entrenched players. Don't editorialize — present the data and let the differentiation analysis determine strategy.

---

## What This Skill Does NOT Do

- Does NOT size the market by search volume — that's the opposite of the methodology
- Does NOT identify competitors — that's the competitor-landscape-research skill
- Does NOT evaluate the member's position in the market — that happens in the differentiation steps of the process
- Does NOT produce the final report — that's the landscape-report-generator skill
- If the member asks "who are my competitors," direct to the competitor-landscape-research skill

---

## Examples

**Example 1: Traditional Service Business**

Input: Industry: "residential plumbing," Geography: "Auckland, New Zealand"

Output (abbreviated):
```
## Market Overview

**Market definition:** The residential plumbing services market in Auckland encompasses
installation, repair, and maintenance of plumbing systems in homes. Auckland's housing
stock of ~580,000 dwellings drives consistent demand for both new build and maintenance work.

**Total Addressable Market:** NZ$420M–$480M annually (IBIS World, NZ plumbing services 2025)

**Growth trajectory:** Growing — 3.2% CAGR driven by Auckland housing development pipeline

**Key drivers:**
- Healthy Homes legislation driving mandatory compliance upgrades
- Auckland's housing growth pipeline (~15,000 consents/year)
- Aging housing stock requiring system replacements
```

Why this is correct: The market is sized by industry revenue (business metric), not by searches for "plumber Auckland." The TAM reflects total market opportunity, not the member's current share.

---

**Example 2: New AI Niche**

Input: Industry: "AI-powered sales assessment platform," Geography: "United States"

Output (abbreviated):
```
## Market Overview

**Market definition:** AI-powered sales assessment replaces traditional pre-hire sales
evaluation (psychometric tests, role-play simulations, behavioral assessments) with
AI-driven live interaction and scoring. The existing market being remixed is pre-hire
assessment and talent evaluation.

**Total Addressable Market:** $3.4B (US talent assessment market, Grand View Research 2024).
The AI-powered segment is estimated at $180-250M and growing rapidly within this.

**Growth trajectory:** Growing — 14.2% CAGR for AI in HR tech (Mordor Intelligence)

**Note:** Search volume for "AI sales assessment" is minimal (~200/month), but the
underlying market of companies hiring sales reps and wanting pre-hire validation is
massive. Low search volume reflects a market that hasn't adopted new search terminology,
not a small market.
```

Why this is correct: The skill identified the traditional market being remixed (pre-hire assessment), sized that, then estimated the AI segment within it. The note explicitly addresses the search volume vs. TAM gap per the methodology.
