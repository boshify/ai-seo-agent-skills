---
name: landscape-report-generator
version: "1.0"
description: >
  Assembles market research, competitive landscape data, differentiation analysis,
  and proof inventory into a branded Target Market Landscape Report Google Doc. Use
  this skill whenever the target-market-landscape-analysis process reaches Step 8
  (compile report), or whenever a completed landscape analysis needs to be formatted
  into the final deliverable. This skill produces a completed branded Google Doc using
  the Omnipresence report template. Always trigger when landscape report generation,
  report compilation, or deliverable assembly intent is present.

inputs:
  required:
    - type: markdown
      label: "market-overview"
      description: "Structured market overview from the market-research skill"
    - type: json
      label: "competitor-profiles"
      description: "Array of up to 10 competitor profile objects from competitor-landscape-research skill"
    - type: markdown
      label: "differentiation-analysis"
      description: "Underserved need extraction results and differentiation validation from process Steps 5-6"
    - type: markdown
      label: "proof-inventory"
      description: "Ranked proof inventory with gap analysis from the proof-catalog skill"
  optional:
    - type: text
      label: "member-brand-name"
      description: "The member's brand name for the report header"
    - type: text
      label: "report-date"
      description: "The date for the report header (defaults to today)"

outputs:
  - type: docx
    label: "landscape-report"
    description: "Completed branded Google Doc — Target Market Landscape Report"

tools_used: []

chains_from:
  - market-research
  - competitor-landscape-research
  - proof-catalog
chains_to: []

tags:
  - report-generation
  - foundation
  - deliverable
  - google-docs
---

# Landscape Report Generator

## What This Skill Does

Takes the outputs from market research, competitor analysis, differentiation work, and proof cataloging and assembles them into a branded Target Market Landscape Report using the Omnipresence doc template. The member gets a polished, one-page-per-section deliverable they can reference throughout their Omnipresence journey.

---

## Context the Agent Needs

This is an assembly skill, not a research skill. All the thinking and analysis happened upstream. This skill's job is to take finalized outputs and place them correctly into the branded template without adding, removing, or editorially changing any content.

The report template is a .docx file with five sections (pages), each with a dark header banner, gold accent divider, and light working area. Placeholder fields use `{curly_brace}` naming. The skill replaces placeholders with actual content.

The template structure:
- **Page 1 — Market Overview:** Market definition, TAM metric cards, market context
- **Page 2 — Competitive Landscape:** 10-row competitor table + landscape patterns
- **Page 3 — Underserved Need:** Specialization lens table + positioning statement
- **Page 4 — Differentiation:** Competitive analysis + strategic recommendation
- **Page 5 — Proof Inventory:** Ranked proof table + gap analysis

Each page must fit on one page. Content must be concise. No fluff.

The template file is located in the Omnipresence templates directory. The agent clones the template, replaces placeholders, and delivers the completed doc to the member.

**Key constraint:** Assembly only. Do not add analysis, commentary, or recommendations that weren't produced by the upstream skills and process steps. The report reflects what was found and decided — nothing more.

---

## Workflow — Execute In This Order

Do not skip steps. Do not summarize. Produce every section in full.

---

### STEP 1: Validate All Inputs

Confirm all required data is present before starting assembly.

**Input:** All four required inputs (market overview, competitor profiles, differentiation analysis, proof inventory).

**Process:**
1. Check that market overview contains: market definition, TAM, growth trajectory, demand signals
2. Check that competitor profiles array contains at least 3 profiles (process may have found fewer than 10)
3. Check that differentiation analysis contains either an identified underserved need with positioning statement OR a documented decision to stay broad
4. Check that proof inventory contains the ranked inventory and gap analysis
5. Set report date to today if not provided
6. Set brand name from member context if not provided

**Output:** Validation confirmation — all inputs present and complete.

**Decision gate:**
- If any required input is missing → do not generate the report. Notify the primary agent which input is missing and suggest returning to the relevant process step.
- If an input is partially complete (e.g., only 3 competitors instead of 10) → proceed with what's available. Note gaps in the report.

---

### STEP 2: Populate Market Overview (Page 1)

Fill in the market overview section of the template.

**Input:** Market overview from market-research skill.

**Process:**
1. Replace `{brand_name}` in the header with the member's brand name
2. Replace `{date}` with the report date
3. Replace `{market_definition}` with the market definition paragraph
4. Replace `{TAM}` with the TAM figure
5. Replace `{trend}` with the growth classification (Growing/Stable/Shrinking + CAGR if available)
6. Replace `{signal}` with the primary demand signal (one word or short phrase)
7. Replace `{market_context}` with the growth trajectory details and key drivers

**Output:** Completed Market Overview page.

---

### STEP 3: Populate Competitive Landscape (Page 2)

Fill in the competitor table and patterns section.

**Input:** Array of competitor profile objects from competitor-landscape-research skill.

**Process:**
1. Replace header placeholders (`{brand_name}`, `{date}`)
2. For each competitor profile (up to 10), populate one table row:
   - `{competitor}` → domain
   - `{dr}` → domain rating
   - `{traffic}` → organic traffic (formatted with commas)
   - `{keywords}` → organic keywords (formatted with commas)
   - `{backlinks}` → total backlinks (formatted with commas)
   - `{ref_domains}` → referring domains (formatted with commas)
   - `{ai_mentions}` → total AI mentions across all surfaces
3. Sort competitors by organic traffic (highest first) unless the process specified a different sort order
4. If fewer than 10 competitors: remove unused rows from the table
5. Replace `{patterns}` with a synthesis of positioning observations across all competitors — common themes, shared approaches, notable gaps. Derive this from the individual competitor positioning summaries. Keep to 2-3 sentences.

**Output:** Completed Competitive Landscape page.

---

### STEP 4: Populate Underserved Need (Page 3)

Fill in the specialization analysis and positioning statement.

**Input:** Differentiation analysis from process Steps 5-6.

**Process:**
1. Replace header placeholders
2. For each specialization lens row in the table:
   - `{finding}` → what was discovered when applying this lens (or "No signal" if the lens didn't surface anything)
   - `{signal}` → strength indicator: "Strong," "Moderate," "Weak," or "None"
3. Replace `{underserved_need}` with the identified underserved need description, or the documented decision to stay broad with reasoning
4. Replace `{positioning_statement}` with the draft positioning statement, or "Broad positioning — no specialization selected" if the member chose to stay broad

**Output:** Completed Underserved Need page.

---

### STEP 5: Populate Differentiation (Page 4)

Fill in the competitive differentiation analysis.

**Input:** Differentiation analysis from process Step 6 + competitive landscape data.

**Process:**
1. Replace header placeholders
2. Replace `{differentiation_analysis}` with the validated differentiation angle — how the underserved need differentiates against the competitive landscape, or justification for broad positioning
3. Replace `{overlap}` with competitive overlap analysis — how many of the top 10 position similarly
4. Replace `{recommendation}` with the strategic recommendation — what slice to focus on first

**Output:** Completed Differentiation page.

---

### STEP 6: Populate Proof Inventory (Page 5)

Fill in the proof table and gap analysis.

**Input:** Proof inventory from proof-catalog skill.

**Process:**
1. Replace header placeholders
2. For each proof asset (up to 8 in the table), populate one row:
   - `{proof_asset}` → specific proof asset description
   - `{type}` → proof type (Review, Case Study, Certification, etc.)
   - `{proximity}` → outcome-proximity ranking (High, Medium, Low)
   - `{location}` → where it currently lives (on-site, off-site, unpublished)
3. Sort by outcome-proximity: High first, then Medium, then Low
4. If fewer than 8 proof assets: remove unused rows
5. If more than 8: include the top 8 by proximity and note additional assets exist
6. Replace `{gap_analysis}` with the gap analysis and top 3 proof actions

**Output:** Completed Proof Inventory page.

---

### STEP 7: Deliver the Report

Finalize and deliver the completed document.

**Input:** Completed template with all sections populated.

**Process:**
1. Review the complete document for any remaining unfilled placeholders — replace any found with "Not available"
2. Save the completed document
3. Present to the member with a brief summary: "Your Target Market Landscape Report is ready. It covers your market position, top 10 competitors, differentiation angle, and proof inventory."

**Output:** Completed Target Market Landscape Report — branded Google Doc delivered to the member.

---

## Output Format

The output is a completed .docx file based on the Omnipresence report template. No structural changes to the template — only placeholder replacement.

**Formatting rules:**
- Numbers in the competitor table use comma formatting (12,500 not 12500)
- Percentages include the % symbol
- "Unavailable" is used for any data point that couldn't be retrieved
- Each page must fit on one page — if content runs long, trim the least important details
- No orphaned placeholder text should remain in the final document

---

## Edge Cases & Judgment Calls

**When there are fewer than 10 competitors:**
Remove empty rows from the competitor table. A report with 5 well-researched competitors is better than one padded with irrelevant entries.

**When the member skipped differentiation:**
Page 3 (Underserved Need) shows all lenses as "No signal" or with findings but no selection. Page 4 (Differentiation) documents the broad positioning decision. The positioning statement box shows "Broad positioning — no specialization selected." Do not leave these pages blank.

**When proof inventory is empty:**
Page 5 still gets populated — with an empty table and a prominent gap analysis stating that no proof was found and listing the top 3 proof types to develop. An empty proof page is one of the most valuable pages in the report.

**When the report won't fit one page per section:**
Prioritize by trimming in this order: (1) reduce market context to 2 sentences, (2) remove the reminder box, (3) shorten landscape patterns to 1 sentence, (4) reduce gap analysis to top 2 actions. Never remove the data tables or metric cards — those are the core value.

---

## What This Skill Does NOT Do

- Does NOT perform any research — all data comes from upstream skills
- Does NOT add analysis or recommendations beyond what the process produced
- Does NOT modify the template structure — only replaces placeholders
- Does NOT create the Google Doc template — the template already exists as a .docx file
- If additional analysis is needed, route back to the relevant process step, don't generate it in the report skill

---

## Examples

**Example 1: Complete Report Assembly**

Input:
- Market overview: "Residential plumbing, Auckland, NZ$420M TAM, growing 3.2% CAGR"
- 8 competitor profiles with full metrics
- Differentiation: "Hot water cylinder specialist"
- Proof: 12 assets ranked, 2 gaps identified

Output: Completed 5-page branded report with all placeholders filled, competitors sorted by traffic, proof sorted by outcome-proximity, positioning statement highlighted in gold box.

Why this is correct: Pure assembly — no added commentary. Every placeholder filled. Competitors and proof sorted per the skill's rules.

---

**Example 2: Partial Data Assembly**

Input:
- Market overview: complete
- 4 competitor profiles (6 failed during research)
- Differentiation: member chose broad positioning
- Proof: 2 assets found, significant gaps

Output: Completed report with 4-row competitor table (6 empty rows removed), underserved need page showing lens findings but "Broad positioning — no specialization selected" in the positioning box, proof page with 2 entries and prominent gap analysis.

Why this is correct: The skill handles incomplete data gracefully — removing empty rows, honestly reflecting the broad positioning decision, and making the sparse proof inventory visible rather than hiding it.
