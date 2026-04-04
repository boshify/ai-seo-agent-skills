---
name: verbalization-generator
version: "1.0"
description: >
  Generates all search query verbalizations for an entity-attribute pair by
  producing connector variants, question formats, and pulling from Google
  autosuggest, People Also Ask, and related searches. Use this skill whenever
  an entity-attribute pair needs to be expanded into the full set of ways
  someone might search for it, or when someone says "generate verbalizations",
  "what else would they search", "expand this pair", "find all the ways people
  search for this", or "get autosuggest for this". Always trigger when
  verbalization expansion is needed — even if phrased casually.

inputs:
  required:
    - type: text
      label: entity-attribute-pair
      description: >
        A validated entity-attribute pair from the entity-extractor skill
        (e.g., "red light therapy + dry eyes").
  optional:
    - type: text
      label: business-context
      description: >
        What the business sells or does — used for scope filtering
        to discard verbalizations outside the business's lane.
    - type: text
      label: member-suggestions
      description: >
        Any search behavior shortcuts or alternative phrasings the member
        has flagged from their knowledge of their customers.

outputs:
  - type: text
    label: verbalization-set
    description: >
      The complete set of verbalizations grouped by source, with
      out-of-scope and triple-combination items filtered out.

tools_used:
  - web_search

chains_from:
  - entity-extractor
chains_to:
  - volume-checker

tags:
  - seo
  - query-derivation
  - verbalization
  - stories-to-queries
---

# Verbalization Generator

## What This Skill Does

Takes a validated entity-attribute pair and generates the full set of ways a
real person might search for that combination. The output is every meaningful
verbalization — ready for volume checking and SERP validation downstream.

---

## Context the Agent Needs

A verbalization is any way someone might type the same entity-attribute pair
into a search bar. "Red light therapy dry eyes" and "does red light therapy
work for dry eyes" and "red light therapy for dry eyes at home" are all
verbalizations of the same pair. They all mean the same thing — the searcher
just phrases it differently.

Verbalizations come from four sources: obvious mechanical variants (adding
connector words, question formats), Google autosuggest, People Also Ask, and
related searches. No single source catches everything.

Every verbalization must stay within the entity-attribute pair boundary. If a
verbalization introduces a new entity or creates a triple combination
(entity + entity + attribute, or entity + attribute + attribute), it's out of
scope for this pair — though it might be a valid new pair to capture separately.

Verbalizations that fall outside what the business can credibly cover get
discarded regardless of how interesting they are.

**Key constraint:** Never leave the entity-attribute pair. Every verbalization
must be a rewording of the same pair, not an expansion into adjacent topics.

---

## Workflow — Execute In This Order

### STEP 1: Generate Mechanical Variants

Produce the obvious verbalizations without any tool calls.

**Input:** The entity-attribute pair.

**Process:**
1. Raw pair — entity + attribute with no connecting words (e.g., "red light therapy dry eyes")
2. Connector variants — add "for", "and", "with" between entity and attribute (e.g., "red light therapy for dry eyes")
3. Reversed order — attribute + entity if it reads naturally (e.g., "dry eyes red light therapy")
4. Question formats:
   - "does [entity] work for [attribute]"
   - "is [entity] good for [attribute]"
   - "how does [entity] help [attribute]"
   - "what are the benefits of [entity] for [attribute]"
   - "can [entity] help with [attribute]"
5. Evaluation formats:
   - "[entity] for [attribute] reviews"
   - "[entity] for [attribute] cost"
   - "[entity] for [attribute] results"
   - "best [entity] for [attribute]"

**Output:** A list of mechanical verbalizations.

**Decision gate:**
- If any variant reads unnaturally (reversed order doesn't work for this pair) → discard it
- If any variant introduces a new attribute (e.g., "cost" becomes a separate pair) → flag it as a potential new pair, don't include it in this set

---

### STEP 2: Pull from Autosuggest

Search Google for the raw pair and capture autosuggest results.

**Input:** Raw entity-attribute pair from Step 1.

**Process:**
1. Use web_search with the raw pair as the query
2. Note any autosuggest completions visible in the results
3. Also search the primary connector variant (e.g., "red light therapy for dry eyes") to catch additional suggestions
4. For each suggestion:
   a. Does it stay within the entity-attribute pair? → keep
   b. Does it introduce a new entity or attribute? → flag as potential new pair, don't include
   c. Does it fall outside business scope? → discard

**Output:** Autosuggest verbalizations added to the set.

---

### STEP 3: Pull from People Also Ask and Related Searches

From the web_search results, extract PAA questions and related searches.

**Input:** Web search results from Step 2.

**Process:**
1. Identify any People Also Ask questions in the search results
2. Identify any related searches at the bottom of results
3. For each:
   a. Is it a verbalization of the same entity-attribute pair? → keep
   b. Is it a related but different topic? → flag as potential new pair
   c. Is it out of scope? → discard
4. PAA questions often reveal question formats that mechanical generation missed — capture these

**Output:** PAA and related search verbalizations added to the set.

---

### STEP 4: Filter and Classify

Clean the full verbalization set.

**Input:** All verbalizations from Steps 1-3.

**Process:**
1. Remove exact duplicates
2. Remove verbalizations that violate the pair boundary (triple combinations, new entities)
3. Remove verbalizations outside business scope
4. Classify remaining verbalizations:
   - **Core** — the raw pair and its direct connector variants
   - **Question** — question-format verbalizations
   - **Evaluation** — review/cost/comparison verbalizations
   - **Long-tail** — autosuggest/PAA verbalizations with additional context
5. Compile the list of potential new pairs flagged in earlier steps

**Output:** The filtered, classified verbalization set plus a list of potential new entity-attribute pairs discovered.

---

## Output Format

```
**Entity-Attribute Pair:** [entity] + [attribute]

**Core Verbalizations:**
- [raw pair]
- [connector variant 1]
- [connector variant 2]
- [reversed if applicable]

**Question Verbalizations:**
- [question 1]
- [question 2]
- [question 3]

**Evaluation Verbalizations:**
- [review variant]
- [cost variant]
- [best variant]

**Long-tail Verbalizations (from autosuggest/PAA):**
- [autosuggest 1]
- [autosuggest 2]
- [PAA question 1]
- [related search 1]

**Potential New Pairs Discovered:**
- [entity + new attribute] — source: [autosuggest/PAA/related]
- [entity + new attribute] — source: [autosuggest/PAA/related]

**Discarded (out of scope):**
- [verbalization] — reason: [outside business scope / triple combination]
```

**Formatting rules:**
- Group by verbalization type, not by source
- Include the Potential New Pairs section only if new pairs were discovered
- Include the Discarded section only if items were discarded (helps the member see what was filtered)
- No duplicates across groups — each verbalization appears once in the most specific group it fits

---

## Edge Cases & Judgment Calls

**When autosuggest returns very few results:**
The pair may be too niche or too new. This is fine — mechanical variants still provide a useful set. Note the low autosuggest count but don't treat it as a problem.

**When a verbalization could be its own pair OR a variant:**
Apply the pair boundary test: does it introduce a genuinely new attribute, or is it the same attribute with more context? "Red light therapy dry eyes at home" = same pair with context (variant). "Red light therapy dry eyes cost" = potentially new attribute (cost). Flag "cost" as a potential new pair.

**When the reversed order creates a different meaning:**
"Dry eyes red light therapy" means the same as "red light therapy dry eyes." But "cancer red light therapy" might imply red light therapy as a cancer treatment, while "red light therapy cancer" might imply cancer as a side effect. If reversing changes meaning, discard the reversed variant.

**When a web_search tool call fails:**
Return the mechanical variants only. Note that autosuggest/PAA/related searches could not be checked. The mechanical variants are still valuable — volume checking can proceed.

---

## What This Skill Does NOT Do

- Does NOT extract entity-attribute pairs from User Stories — that's the entity-extractor skill
- Does NOT check search volume or keyword difficulty — that's the volume-checker skill
- Does NOT validate whether verbalizations share SERP intent — that's the serp-validator skill
- Does NOT decide whether to create the pair (skip threshold) — that's decided by the process using volume data
- If the member asks "which verbalization should I target?" → this skill generates the options, volume-checker identifies the winner

---

## Examples

**Example 1: Rich autosuggest results**

Input:
Entity-attribute pair: red light therapy + dry eyes

Output (abbreviated):
```
**Entity-Attribute Pair:** red light therapy + dry eyes

**Core Verbalizations:**
- red light therapy dry eyes
- red light therapy for dry eyes
- dry eyes red light therapy

**Question Verbalizations:**
- does red light therapy work for dry eyes
- is red light therapy good for dry eyes
- can red light therapy help with dry eyes

**Evaluation Verbalizations:**
- red light therapy for dry eyes reviews
- best red light therapy for dry eyes

**Long-tail Verbalizations (from autosuggest/PAA):**
- red light therapy for dry eyes at home
- red light therapy for dry eyes before and after
- how long does red light therapy take for dry eyes

**Potential New Pairs Discovered:**
- red light therapy + dry eyes cost — source: autosuggest
- red light therapy + causing dry eyes — source: autosuggest (different intent — treating vs. causing)
```

Why this is correct: The skill stayed within the pair boundary, flagged "cost" and "causing dry eyes" as potential new pairs rather than including them as verbalizations, and classified outputs by type.

---

**Example 2: Niche pair with sparse autosuggest**

Input:
Entity-attribute pair: ACL + exercises

Output (abbreviated):
```
**Entity-Attribute Pair:** ACL + exercises

**Core Verbalizations:**
- ACL exercises
- exercises for ACL
- ACL recovery exercises

**Question Verbalizations:**
- what exercises help ACL recovery
- how to exercise with ACL injury

**Evaluation Verbalizations:**
- best ACL exercises

**Long-tail Verbalizations (from autosuggest/PAA):**
- ACL exercises at home
- ACL exercises without equipment

**Potential New Pairs Discovered:**
- ACL + surgery recovery — source: PAA
- ACL + rehab timeline — source: related searches
```

Why this is correct: Even with sparse autosuggest, mechanical variants produced a useful set. PAA surfaced adjacent topics correctly flagged as potential new pairs.
