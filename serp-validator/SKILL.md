---
name: serp-validator
version: "1.0"
description: >
  Validates whether verbalizations of an entity-attribute pair share SERP
  intent (one page opportunity) or diverge (separate page opportunities) by
  comparing ranking pages across verbalizations. Use this skill whenever
  SERP validation is needed to determine page splits, or when someone says
  "check the SERPs", "do these share intent", "should this be one page or
  two", "validate against SERPs", or "check if these overlap". Always trigger
  when SERP intent comparison is needed — even if phrased casually.

inputs:
  required:
    - type: text
      label: entity-attribute-pair
      description: >
        The entity-attribute pair being validated
        (e.g., "red light therapy + dry eyes").
    - type: text
      label: verbalizations-to-compare
      description: >
        Two or more verbalizations with significant volume that need
        SERP comparison (e.g., the top 2-3 by volume from volume-checker).
  optional:
    - type: text
      label: additional-attributes
      description: >
        Other attributes on the same entity that may share SERPs
        (e.g., "MGD" and "dry eyes" for entity "red light therapy").

outputs:
  - type: text
    label: serp-validation-report
    description: >
      Per-comparison SERP overlap analysis with one-page-or-split
      recommendation and any graduated verbalizations flagged as
      new content item Ideas.

tools_used:
  - web_search
  - web_fetch

chains_from:
  - volume-checker
chains_to: []

tags:
  - seo
  - serp-validation
  - content-architecture
  - stories-to-queries
---

# SERP Validator

## What This Skill Does

Takes an entity-attribute pair and its high-volume verbalizations, searches
each one, compares the ranking pages, and determines whether they share SERP
intent (serve with one page) or diverge (create separate content items). The
output is a definitive one-page-or-split recommendation for each comparison.

---

## Context the Agent Needs

Two verbalizations of the same entity-attribute pair can look identical but
serve different SERP intent. "Red light therapy for dry eyes" and "best red
light therapy for dry eyes" might rank the same informational guides — or
"best" might trigger product review listicles while the base query triggers
educational content. The SERP is the only way to know.

The same principle applies to different attributes on the same entity.
"Red light therapy + MGD" and "red light therapy + dry eyes" are two
different entity-attribute pairs, but they might share the same ranking
pages — meaning they can be served by one content item.

The SERP is the arbiter. Never assume. Always check.

When verbalizations diverge, the divergent verbalization graduates into its
own content item with Status = "Idea." It doesn't get fully validated here —
it re-enters the pipeline for its own volume check and SERP validation.

**Key constraint:** Compare ranking pages, not snippets. Two queries can
have different snippets but rank the same pages. The pages are what matter.

---

## Workflow — Execute In This Order

### STEP 1: Determine What to Compare

Identify which verbalizations and attributes need SERP comparison.

**Input:** The entity-attribute pair, verbalizations with volume data, and any additional attributes.

**Process:**
1. From the verbalizations, select the ones that need comparison:
   a. Any two verbalizations where both have significant volume (100+ searches/month)
   b. Any verbalization that uses a different format than the base query (question format vs. statement, "best" prefix, "how to" prefix)
   c. Any verbalization that adds substantial context beyond the raw pair (e.g., "at home", "without equipment", "reviews")
2. From additional attributes (if provided), pair each with the entity for cross-attribute comparison
3. Build a comparison list: pairs of queries to check against each other

**Output:** A list of query pairs to compare, with rationale for each comparison.

**Decision gate:**
- If only one verbalization has volume → no comparison needed, single content item confirmed
- If the list exceeds 5 comparisons → prioritize by volume differential and format differences

---

### STEP 2: Search and Compare SERPs

For each query pair, search both queries and compare ranking pages.

**Input:** Query pairs from Step 1.

**Process:**
1. For each query in the pair, run `web_search`
2. Extract the top 5 ranking domains and URLs from each search
3. Compare the two result sets:
   a. Count how many of the top 5 URLs appear in both SERPs
   b. Count how many of the top 5 domains appear in both SERPs (even if different URLs)
4. Apply the overlap rules:

| URL Overlap (top 5) | Domain Overlap (top 5) | Ruling |
|---|---|---|
| 3+ URLs match | — | Same intent → one content item |
| 1-2 URLs match | 3+ domains match | Likely same intent → one content item (verify with Step 3) |
| 1-2 URLs match | 1-2 domains match | Different intent → separate content items |
| 0 URLs match | — | Definitely different intent → separate content items |

5. If the ruling is "verify with Step 3," proceed to deeper analysis. Otherwise, record the ruling.

**Output:** Per-pair SERP overlap data and preliminary ruling.

**Decision gate:**
- If ruling is clear (3+ URL match or 0 URL match) → finalize without Step 3
- If ruling requires verification → proceed to Step 3

---

### STEP 3: Deep Verification (Ambiguous Cases Only)

For comparisons where the SERP overlap is ambiguous, fetch the top-ranking pages to check content treatment.

**Input:** Ambiguous query pairs from Step 2.

**Process:**
1. Take the top-ranking URL that appears for both queries (or the #1 result for each if no overlap)
2. Run `web_fetch` on one or both URLs
3. Check how each query is treated on the page:
   a. Are both queries addressed as the page's primary focus? → same intent
   b. Is one query the page's focus and the other addressed in a subsection? → same intent (the subsection query is an H2/H3, not its own page)
   c. Are they addressed on completely different pages with different structures? → different intent
4. If two pages are fetched and they cover the same ground with similar structure → same intent
5. If they cover substantively different angles → different intent

**Output:** Final ruling for ambiguous cases.

---

### STEP 4: Compile Results

Assemble the final validation report.

**Input:** All rulings from Steps 2 and 3.

**Process:**
1. For each comparison, record: the two queries compared, the overlap data, and the final ruling
2. For any verbalization ruled as "different intent," flag it as a graduated content item:
   - Content Name = the verbalization rephrased as an entity-attribute pair
   - Status = "Idea"
   - Source = the original pair it was derived from
3. For any cross-attribute comparison ruled as "same intent," note that the two attributes can be served by one content item — use the higher-volume attribute as the primary
4. Compile the list of graduated content items (new Ideas)

**Output:** Complete SERP validation report with rulings and new Ideas.

---

## Output Format

```
**Entity-Attribute Pair:** [entity] + [attribute]

**Comparisons:**

### [Query A] vs [Query B]
**URL Overlap:** [X] of 5 top URLs match
**Domain Overlap:** [X] of 5 top domains match
**Ruling:** [Same intent — one content item / Different intent — separate content items]
**Evidence:** [Brief description of what the SERPs show]

### [Query C] vs [Query D]
**URL Overlap:** [X] of 5
**Domain Overlap:** [X] of 5
**Ruling:** [Same / Different]
**Evidence:** [Brief description]

---

**Summary:**
- **One content item** serves: [list of verbalizations that share intent]
- **Graduated to new Ideas:**
  - [verbalization] → Content Name: [entity + new attribute], Source: [original pair]
  - [verbalization] → Content Name: [entity + new attribute], Source: [original pair]

**Cross-Attribute Findings:** (if applicable)
- [attribute A] and [attribute B] share SERPs → serve with one content item, primary keyword: [higher-volume variant]
```

**Formatting rules:**
- One comparison block per query pair
- Evidence is 1-2 sentences max — enough to justify the ruling, not a full SERP analysis
- Graduated content items use the entity-attribute pair format, not the raw verbalization
- Cross-attribute findings are only included when additional attributes were provided for comparison

---

## Edge Cases & Judgment Calls

**When the SERP is dominated by one mega-page (e.g., Wikipedia):**
A single authoritative page ranking for both queries doesn't necessarily mean same intent. Check whether other results also overlap. If only the mega-page overlaps and the remaining 4 results differ, treat as different intent — the mega-page is just authoritative enough to rank for everything.

**When the SERP shows mixed content formats:**
Query A shows informational guides, Query B shows product review listicles. Even if some domains overlap, the content format difference signals different intent. Treat as separate content items — they need different page structures.

**When the SERP is thin (few quality results):**
If a query returns mostly forum posts, Reddit threads, or thin content, that's a signal of unsaturated opportunity — not ambiguous intent. The query likely deserves its own content item. Default to treating it as separate unless there's clear overlap with another query's results.

**When a web_search or web_fetch call fails:**
For web_search failure: retry once. If still failing, note the comparison as "unvalidated — SERP check failed" and default to treating as same intent (conservative approach — better to consolidate than fragment without evidence).

For web_fetch failure (Step 3 only): make the ruling based on URL/domain overlap data from Step 2 alone. The deep verification is a tiebreaker, not a requirement.

---

## What This Skill Does NOT Do

- Does NOT extract entity-attribute pairs — that's the entity-extractor skill
- Does NOT generate verbalizations — that's the verbalization-generator skill
- Does NOT check search volume — that's the volume-checker skill
- Does NOT make page architecture decisions (H2 vs H3 vs page) — that's QDP downstream
- Does NOT create or update the topical map — that's handled by the process using doc-manager
- If the member asks "what heading level should this be?" → this skill determines page-or-not, QDP determines the full architecture

---

## Examples

**Example 1: Same intent confirmed**

Input:
Entity-attribute pair: red light therapy + dry eyes
Verbalizations to compare: "red light therapy for dry eyes" (vol: 1,300) vs "does red light therapy work for dry eyes" (vol: 210)

Output (abbreviated):
```
### "red light therapy for dry eyes" vs "does red light therapy work for dry eyes"
**URL Overlap:** 4 of 5 top URLs match
**Domain Overlap:** 5 of 5 top domains match
**Ruling:** Same intent — one content item
**Evidence:** Top results are identical informational guides. The question format surfaces the same pages — it's just a different way of phrasing the same query.

**Summary:**
- **One content item** serves: red light therapy for dry eyes, does red light therapy work for dry eyes, red light therapy dry eyes, all question variants
- **Graduated to new Ideas:** none
```

Why this is correct: 4/5 URL overlap is a clear signal of shared intent. No split needed.

---

**Example 2: Different intent — page split**

Input:
Entity-attribute pair: red light therapy + dry eyes
Verbalizations to compare: "red light therapy for dry eyes" (vol: 1,300) vs "best red light therapy for dry eyes" (vol: 320)

Output (abbreviated):
```
### "red light therapy for dry eyes" vs "best red light therapy for dry eyes"
**URL Overlap:** 1 of 5 top URLs match
**Domain Overlap:** 2 of 5 top domains match
**Ruling:** Different intent — separate content items
**Evidence:** "red light therapy for dry eyes" ranks informational guides explaining the science and benefits. "best red light therapy for dry eyes" ranks product review listicles comparing specific devices. Different content formats serving different search intent.

**Summary:**
- **One content item** serves: red light therapy for dry eyes, does red light therapy work for dry eyes
- **Graduated to new Ideas:**
  - "best red light therapy for dry eyes" → Content Name: red light therapy + best (dry eyes), Source: red light therapy + dry eyes
```

Why this is correct: Low overlap plus different content formats is a clear split signal. The "best" verbalization graduated into its own content item as an Idea.

---

**Example 3: Cross-attribute comparison**

Input:
Entity-attribute pair: red light therapy + MGD
Additional attributes: dry eyes

Output (abbreviated):
```
### "red light therapy for MGD" vs "red light therapy for dry eyes"
**URL Overlap:** 3 of 5 top URLs match
**Domain Overlap:** 4 of 5 top domains match
**Ruling:** Same intent — one content item
**Evidence:** Top results cover both MGD and dry eyes on the same pages. MGD is the clinical term for a type of dry eye — ranking pages address both terms within the same content.

**Cross-Attribute Findings:**
- MGD and dry eyes share SERPs → serve with one content item, primary keyword: red light therapy for dry eyes (higher volume)
```

Why this is correct: The cross-attribute comparison confirmed that the clinical term and the common term share SERP intent. One content item serves both, using the higher-volume attribute as the primary keyword.
