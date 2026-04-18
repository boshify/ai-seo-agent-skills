---
name: serp-fetch-and-classify
version: "1.0"
description: >
  Fetches page 1 of Google for a given sub-query and classifies each result as
  owned-website or non-owned-platform, identifying the format class when non-owned.
  Use this skill whenever you need to know whether off-site content can rank for
  a specific query. This skill outputs a structured JSON report with per-result
  classification plus a satellite-worthy verdict. Always trigger when a process
  needs SERP composition analysis — especially for ASN deployment, competitive
  analysis, or sub-query viability checks.

# === CROSS-AGENT METADATA ===

inputs:
  required:
    - type: text
      label: "sub-query"
      description: "The search query to analyze (e.g., 'how much AI content is safe for SEO')"
  optional:
    - type: text
      label: "brand-domain"
      description: "Member's own domain, so it can be flagged separately in the results"

outputs:
  - type: json
    label: "serp-classification-report"
    description: >
      Structured report with sub-query, classified results per position,
      satellite-worthy verdict, and list of format classes found on the SERP

tools_used:
  - brave_search      # Primary SERP source
  - web_search        # Fallback if Brave unavailable or returns empty
  - web_fetch         # Only if needed to disambiguate a result's nature

chains_from: []
chains_to:
  - satellite-content-produce

tags:
  - serp
  - classification
  - asn
  - satellite-network
---

# SERP Fetch and Classify

## What This Skill Does

Takes a sub-query and returns page 1 of Google classified into owned-website vs non-owned-platform results, with a format class label on every non-owned result. The caller gets a satellite-worthy verdict plus the format classes found, which is everything needed to route a satellite to the right platform.

---

## Context the Agent Needs

This skill serves the ASN deployment decision framework. The methodology that governs this decision lives in Synapse at `methodology/expansion/authority-satellite-network-deployment.md` — specifically Stage 3 (SERP Evaluation) and the format-class taxonomy.

The rule the skill implements: page 1 contains at least one non-owned-website result → satellite-worthy. Otherwise, hub-only.

Position on the SERP is irrelevant. A non-owned result at position 10 counts the same as one at position 2. The presence signal matters, not the ranking dominance.

The format-class taxonomy below is a **heuristic starting list** — not exhaustive. When a domain doesn't match anything in the list, use judgment based on what the platform *does*, not what it's called. Most real-world classification cases are obvious. Edge cases are rare and can fall back to the "non-owned, unclassified" bucket without breaking the downstream process.

**Key constraint:** Do not over-engineer classification. If a domain clearly isn't a business's own website and clearly isn't a news publisher, classify it to the best-matching format class and move on.

---

## Format-Class Heuristic

| Format Class | Common domains |
|---|---|
| Content (medium-to-long publishing) | medium.com, substack.com, linkedin.com/pulse, dev.to, hashnode.com |
| UGC (user-generated / forum / community) | reddit.com, quora.com, stackexchange.com, stackoverflow.com, any URL containing `/forum/` or `/community/`, niche forums |
| Video (long-form) | youtube.com/watch, vimeo.com |
| Video (short-form) | youtube.com/shorts, tiktok.com, instagram.com/reels |
| Social (posts, not profiles) | linkedin.com/posts, x.com/[user]/status, twitter.com/[user]/status, facebook.com/[page]/posts |
| Technical / Code | github.com, gitlab.com, npmjs.com (package pages, not docs) |
| Document / Slide | slideshare.net, scribd.com, speakerdeck.com |

**Does NOT count as non-owned (classify as owned-website):**
- Any business domain that isn't one of the above platforms
- News publishers and editorial sites (nytimes.com, techcrunch.com, forbes.com/articles, theverge.com, etc.)
- Wikipedia (wikipedia.org)
- Profile pages on any platform (linkedin.com/in/[user], x.com/[user] without `/status`, youtube.com/@channel without `/watch`)
- Contributor-gated publisher content (forbes.com/sites/[contributor], huffpost.com/entry written by contributors, inc.com/contributor)

---

## Workflow — Execute In This Order

### STEP 1: Fetch the SERP

**Input:** The sub-query string.

**Process:**
1. Call Brave Search API with the sub-query. Request top 10 results from page 1.
2. If Brave returns fewer than 5 results, flag a warning and fall back to `web_search` for the same query.
3. If both sources return fewer than 3 results, return an error result with status `serp_fetch_failed` — do not guess.

**Output:** A list of up to 10 result objects, each with `position`, `url`, `title`, and `domain`.

---

### STEP 2: Classify Each Result

**Input:** The list from Step 1.

**Process:**
1. For each result, extract the root domain and relevant URL path.
2. Compare against the format-class heuristic table above.
3. Classify as one of:
   - `non-owned` with a `format_class` label (Content / UGC / Video-long / Video-short / Social / Technical / Document)
   - `owned-website` (default for anything not matching the heuristic AND not a news publisher/profile/Wikipedia)
   - `news-publisher` (matches known publishers — treat as owned-website for satellite purposes)
   - `profile-page` (matches profile-page patterns — treat as owned-website for satellite purposes)
   - `contributor-gated` (matches contributor paths — treat as owned-website for satellite purposes)
4. If a result clearly isn't a business website but doesn't match any format class cleanly, classify as `non-owned` with `format_class: unclassified` and include the domain. The caller handles unclassified results separately.

**Output:** Each result now has `type` and optionally `format_class`.

**Decision gate:**
- If the brand-domain input was provided and matches a result → flag that result with `is_brand_domain: true` so the caller knows the member's own site ranks here. Do not exclude it from the classification.

---

### STEP 3: Determine Satellite-Worthiness

**Input:** Classified results from Step 2.

**Process:**
1. Count results with `type: non-owned`.
2. If count ≥ 1 → `satellite_worthy: true`.
3. If count = 0 → `satellite_worthy: false`.
4. Build a list of unique format classes found among non-owned results.

**Output:** Top-level `satellite_worthy` boolean plus `format_classes_found` array.

---

### STEP 4: Return the Report

Return a single JSON object in this exact structure:

```json
{
  "sub_query": "how much AI content is safe for SEO",
  "source": "brave | web_search | fallback",
  "results": [
    {
      "position": 1,
      "url": "https://www.reddit.com/r/SEO/comments/...",
      "domain": "reddit.com",
      "title": "...",
      "type": "non-owned",
      "format_class": "UGC",
      "is_brand_domain": false
    },
    {
      "position": 2,
      "url": "https://example.com/ai-content-guide",
      "domain": "example.com",
      "title": "...",
      "type": "owned-website",
      "is_brand_domain": false
    }
  ],
  "satellite_worthy": true,
  "format_classes_found": ["UGC", "Content"],
  "status": "ok"
}
```

**On failure:**

```json
{
  "sub_query": "...",
  "results": [],
  "satellite_worthy": null,
  "format_classes_found": [],
  "status": "serp_fetch_failed",
  "error": "Brave returned 0 results; web_search returned 2 results — below 3-result threshold"
}
```

---

## Output Format

Always return JSON. No prose. No markdown. No commentary. A downstream process consumes the output — it expects structured data.

**Required fields:**
- `sub_query` (string)
- `source` (string: brave / web_search / fallback)
- `results` (array of result objects)
- `satellite_worthy` (boolean or null)
- `format_classes_found` (array of strings)
- `status` (string: ok / serp_fetch_failed / partial)

**Per-result fields:**
- `position` (integer, 1-indexed)
- `url` (string)
- `domain` (string)
- `title` (string)
- `type` (string: non-owned / owned-website / news-publisher / profile-page / contributor-gated)
- `format_class` (string, only present if type is non-owned)
- `is_brand_domain` (boolean)

---

## Edge Cases & Judgment Calls

**When Brave returns thin results (under 5):**
Fall back to `web_search` silently. Flag the source used in the output. If both sources are thin, return status `serp_fetch_failed`.

**When a domain doesn't match any format class but clearly isn't a business website:**
Classify as `non-owned` with `format_class: unclassified`. Include the domain. The caller decides how to handle it.

**When two platforms blur the line (e.g., a Substack post on a custom domain):**
Check if the URL structure matches the platform pattern (e.g., `substack.com/subdomain` or `/p/` path). If yes, classify as the platform. If the platform has been fully white-labeled on a custom domain with no platform fingerprint, classify as `owned-website` — the member would have no access to post there as a satellite.

**When a result is a news article written by a contributor:**
Classify as `contributor-gated`. Do not count it as non-owned. Velocity belief rules this out as a satellite opportunity.

**When the SERP contains featured snippets, People Also Ask, or shopping results:**
Ignore non-organic elements. Classify only the 10 organic results. If fewer than 10 organic results exist, classify what's available.

**When the same domain appears multiple times on page 1:**
Classify each occurrence independently. Do not deduplicate — position matters for the caller's records even if the classification is irrelevant to the satellite-worthy check.

---

## What This Skill Does NOT Do

- Does NOT decide whether to deploy a satellite — that's the methodology's job
- Does NOT route to a platform — that's the methodology's job (Stage 4)
- Does NOT write satellite content — that's the `satellite-content-produce` skill
- Does NOT fetch SERP data for multiple queries in one call — one query per invocation
- Does NOT return prose or analysis — output is JSON only
- If the caller wants analysis, they should parse the JSON and apply the methodology

---

## Examples

**Example 1: Satellite-worthy SERP**

Input:
```
sub_query: "how much AI content is safe to publish for SEO"
brand_domain: "jonathanboshoff.com"
```

Output (abbreviated):
```json
{
  "sub_query": "how much AI content is safe to publish for SEO",
  "source": "brave",
  "results": [
    {"position": 1, "url": "https://reddit.com/r/SEO/...", "domain": "reddit.com", "type": "non-owned", "format_class": "UGC"},
    {"position": 2, "url": "https://backlinko.com/ai-content", "domain": "backlinko.com", "type": "owned-website"},
    {"position": 3, "url": "https://medium.com/@author/...", "domain": "medium.com", "type": "non-owned", "format_class": "Content"},
    {"position": 4, "url": "https://semrush.com/blog/...", "domain": "semrush.com", "type": "owned-website"}
  ],
  "satellite_worthy": true,
  "format_classes_found": ["UGC", "Content"],
  "status": "ok"
}
```

Why this is correct: Two non-owned results on page 1 (Reddit and Medium) trigger satellite-worthy. Two format classes identified (UGC, Content). Caller now has everything needed to check against the member's roster.

---

**Example 2: Hub-only SERP**

Input:
```
sub_query: "best enterprise SEO platform comparison"
```

Output (abbreviated):
```json
{
  "sub_query": "best enterprise SEO platform comparison",
  "source": "brave",
  "results": [
    {"position": 1, "url": "https://botify.com/...", "domain": "botify.com", "type": "owned-website"},
    {"position": 2, "url": "https://conductor.com/...", "domain": "conductor.com", "type": "owned-website"},
    {"position": 3, "url": "https://brightedge.com/...", "domain": "brightedge.com", "type": "owned-website"},
    {"position": 4, "url": "https://searchenginejournal.com/...", "domain": "searchenginejournal.com", "type": "news-publisher"}
  ],
  "satellite_worthy": false,
  "format_classes_found": [],
  "status": "ok"
}
```

Why this is correct: All results are either owned websites (tool vendors) or a news publisher. Zero non-owned platform results. Satellite-worthy is false. Downstream process will classify this sub-query as HUB-ONLY.
