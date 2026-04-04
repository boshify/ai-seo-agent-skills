---
name: entity-extractor
version: "1.0"
description: >
  Extracts entity-attribute pairs from User Stories by identifying the entity,
  validating it against Google's Knowledge Graph, and pairing it with the
  narrowing attribute. Use this skill whenever a User Story needs to be
  converted into a searchable entity-attribute pair, or when someone says
  "extract the entity", "what's the entity-attribute pair", "what would they
  search", or "derive the pair from this story". Always trigger when an
  entity-attribute extraction is needed — even if phrased casually.

inputs:
  required:
    - type: text
      label: user-story
      description: >
        A validated User Story in the format "As a [ICP], I want to [action],
        so that [outcome]."
  optional:
    - type: text
      label: business-context
      description: >
        What the business sells or does — used for scope filtering and
        disambiguation when the Knowledge Graph returns multiple entities.

outputs:
  - type: text
    label: entity-attribute-pair
    description: >
      The raw entity-attribute pair, the validated Knowledge Graph entity,
      the attribute, and confidence notes.

tools_used:
  - knowledge-graph-mcp

chains_from:
  - user-stories
chains_to:
  - verbalization-generator

tags:
  - seo
  - entity
  - query-derivation
  - stories-to-queries
---

# Entity Extractor

## What This Skill Does

Takes a single User Story and extracts the entity-attribute pair — the shortest
searchable combination of a Knowledge Graph-validated entity and its narrowing
attribute. The output is the atomic building block for query generation.

---

## Context the Agent Needs

The entity is whatever Google recognizes as a real entity in the Knowledge Graph.
This is not a grammatical exercise — it's a database lookup. The attribute is the
narrowing lens: a condition, feature, evaluation angle, desired action, or qualifier.
Together they form the raw pair that a real user would type into a search bar.

The entity usually comes from the "I want to" portion of the User Story. The
attribute comes from the intersection of what the person wants and their specific
situation. The ICP and "so that" portions provide context but rarely contain the
entity or attribute directly.

Users don't always search the way the story reads. "Solopreneur CRM" becomes
"free CRM" in real search behavior. This skill flags uncertain derivations
for human review rather than guessing.

**Key constraint:** The entity MUST be validated against the Knowledge Graph.
If it's not a recognized entity, try the broader concept. Never guess — look it up.

---

## Workflow — Execute In This Order

### STEP 1: Parse the User Story

Read the User Story and identify the three components: ICP ("As a..."),
action ("I want to..."), and outcome ("so that...").

**Input:** The User Story text.

**Process:**
1. Extract the ICP descriptor (who they are)
2. Extract the action (what they want to do or find)
3. Extract the outcome (why they want it)

**Output:** The three components separated and labeled.

**Decision gate:**
- If the story is malformed or missing components → ask the member to complete it
- If the story is too vague ("I want to improve my business") → flag it as too broad for entity extraction

---

### STEP 2: Identify the Entity Candidate

From the action component, identify what the person is looking for — the core
subject of their search.

**Input:** The parsed User Story from Step 1.

**Process:**
1. Read the "I want to" portion — the entity is usually the noun or noun phrase representing what they're seeking
2. Consider the "so that" portion for additional context but don't extract the entity from it
3. Form an entity candidate — the broadest recognizable concept that captures what they'd search for
4. If multiple candidates exist, pick the one most likely to be searched as a standalone term

**Output:** One entity candidate, with reasoning for why it was selected.

---

### STEP 3: Validate Against Knowledge Graph

Confirm the entity candidate is a recognized entity in Google's Knowledge Graph.

**Input:** Entity candidate from Step 2.

**Process:**
1. Search the Knowledge Graph for the entity candidate
2. If one clear result matches → confirmed entity
3. If multiple results return (e.g., "Mercury" returns planet, element, mythology):
   a. Use the User Story context (ICP, action, outcome) to disambiguate
   b. Select the entity whose description aligns with the story's domain
   c. If still ambiguous even with story context → flag for member review
4. If no results return:
   a. Try a broader version of the candidate (e.g., "solopreneur CRM" → "CRM")
   b. If the broader concept is found → use that as the entity, note the specificity gap
   c. If still nothing → the entity may be too new or too niche. Note it and proceed with uncertainty flagged
5. Record the Knowledge Graph MID, entity name, and type for the confirmed entity

**Output:** Confirmed entity with Knowledge Graph validation, or flagged uncertainty.

**Decision gate:**
- If entity confirmed → proceed to Step 4
- If entity ambiguous → flag for member review with the Knowledge Graph options presented
- If entity not found even at broader level → proceed but flag as unvalidated

---

### STEP 4: Identify the Attribute

From the User Story, identify the specific lens that narrows the entity.

**Input:** Confirmed entity from Step 3, full User Story from Step 1.

**Process:**
1. The attribute is the qualifier that narrows the entity to the searcher's specific situation
2. It can be: a condition (dry eyes), a feature (client approvals), an evaluation angle (cost), a desired action (reduction), a generic qualifier (best)
3. The attribute usually comes from the intersection of the action and the ICP's situation
4. Strip connecting words — the raw attribute is the shortest meaningful qualifier
5. Check: does the entity + attribute pair make sense as a search? Would someone actually type this?

**Output:** The identified attribute with its type (condition, feature, angle, action, qualifier).

**Decision gate:**
- If the attribute is obvious → proceed to Step 5
- If multiple attributes could apply → extract all of them as separate pairs (each gets its own output)
- If no clear attribute exists → the story may be too broad. Flag for member review.

---

### STEP 5: Form and Validate the Pair

Combine entity and attribute into the raw entity-attribute pair.

**Input:** Confirmed entity from Step 3, attribute(s) from Step 4.

**Process:**
1. Form the raw pair: [entity] + [attribute] with no connecting words
2. Apply the shortest-pair test: is this the shortest combination that would still return relevant results if searched?
3. Check for search behavior shortcuts: would a real user search this differently than how the story reads? If yes, flag it with the alternative phrasing.
4. Check scope: does this pair fall within what the business can credibly cover? If not, note it as out of scope.
5. Check for triple combinations: does this pair contain two entities or two attributes? If yes, it's too complex — simplify or split.

**Output:** The final entity-attribute pair(s) with confidence level and any flags.

---

## Output Format

For each User Story processed, output:

```
**User Story:** [full story text]

**Entity:** [entity name] (Knowledge Graph: [MID] / [type] / [validated|unvalidated|ambiguous])
**Attribute:** [attribute] ([type: condition|feature|angle|action|qualifier])
**Raw Pair:** [entity] + [attribute]

**Confidence:** [high|medium|low]
**Flags:**
- [any search behavior shortcut concerns]
- [any scope concerns]
- [any disambiguation notes]

**Additional Pairs:** (if multiple attributes extracted)
- [entity] + [attribute 2] — [reasoning]
```

**Formatting rules:**
- One output block per User Story
- If multiple attributes exist, each gets its own pair listed under Additional Pairs
- Flags section is omitted if there are no flags (don't include an empty flags section)
- Confidence is high if entity is Knowledge Graph validated and attribute is clear; medium if entity required broader concept fallback; low if entity is unvalidated or search behavior divergence is suspected

---

## Edge Cases & Judgment Calls

**When the story has no clear product or solution entity:**
Top-of-funnel stories point to problems, not products. The entity candidate will be the problem concept itself ("information silos", "context loss"). These are valid entities — check the Knowledge Graph for the concept. Multiple pairs may emerge from one story.

**When the entity candidate is a compound term:**
"Invoice automation" — is the entity "invoice" or "invoice automation"? Check the Knowledge Graph for both. Use whichever is recognized. If both are recognized, use the more specific one that matches the story's intent.

**When the attribute is "best" or another generic qualifier:**
Accept it. "Best baby monitor" is a real search pattern. Generic qualifiers are valid attributes when they reflect actual search behavior.

**When a tool call to the Knowledge Graph fails:**
Proceed with the entity candidate unvalidated. Flag it clearly in the output. The entity is likely still correct — the Knowledge Graph is a validation tool, not the only source of truth.

---

## What This Skill Does NOT Do

- Does NOT generate verbalizations — that's the verbalization-generator skill
- Does NOT check search volume — that's the volume-checker skill
- Does NOT validate against SERPs — that's the serp-validator skill
- Does NOT create or update the topical map — that's handled by the process using doc-manager
- If the member asks "what keywords should I target?" → this skill extracts the pair, downstream skills handle keywords

---

## Examples

**Example 1: Straightforward extraction**

Input:
"As a dry eye sufferer, I want to find out if red light therapy works for MGD specifically, so that I can determine if this is worth trying before spending money."

Output:
```
**User Story:** As a dry eye sufferer, I want to find out if red light therapy works for MGD specifically, so that I can determine if this is worth trying before spending money.

**Entity:** Red light therapy (Knowledge Graph: /m/0xyz123 / Thing / validated)
**Attribute:** MGD (condition)
**Raw Pair:** red light therapy + MGD

**Confidence:** high

**Additional Pairs:**
- red light therapy + dry eyes — ICP is "dry eye sufferer", many won't know the term MGD
```

Why this is correct: The entity is the product/solution being evaluated. The attribute is the specific condition. A second pair is extracted because the ICP descriptor suggests an alternate attribute that non-clinical searchers would use.

---

**Example 2: Search behavior divergence**

Input:
"As a solopreneur, I want to find a CRM that doesn't require a sales team to be useful, so that I can manage leads without hiring."

Output:
```
**User Story:** As a solopreneur, I want to find a CRM that doesn't require a sales team to be useful, so that I can manage leads without hiring.

**Entity:** CRM (Knowledge Graph: /m/0abc456 / Thing / validated)
**Attribute:** solopreneur (qualifier)
**Raw Pair:** CRM + solopreneur

**Confidence:** low
**Flags:**
- ⚠️ Search behavior divergence: real users likely search "free CRM", "simple CRM", or "CRM for one person" rather than "solopreneur CRM". Recommend member review.
```

Why this is correct: The skill flagged the divergence rather than silently accepting a pair that doesn't match real search behavior. The low confidence triggers member review in the process.
