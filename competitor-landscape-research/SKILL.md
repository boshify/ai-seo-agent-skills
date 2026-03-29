---
name: competitor-landscape-research
version: "1.0"
description: >
  Researches a single competitor's SEO metrics, AI visibility, positioning, and proof
  using Ahrefs MCP and web scraping. Use this skill whenever the target-market-landscape-
  analysis process reaches Step 3 (competitor research), or whenever a member asks to
  research a specific competitor. This skill produces a structured competitor profile.
  Designed to run as a sub-agent skill — one instance per competitor, parallelized.
  Always trigger when competitor research, competitor analysis, or competitive intelligence
  intent is present — even if phrased casually.

inputs:
  required:
    - type: text
      label: "competitor-domain"
      description: "The competitor's domain URL (e.g., competitor.com)"
    - type: text
      label: "competitor-brand-name"
      description: "The competitor's brand/company name (needed for Brand Radar AI visibility)"
  optional:
    - type: text
      label: "industry-context"
      description: "One-sentence description of the industry for contextualizing positioning analysis"

outputs:
  - type: json
    label: "competitor-profile"
    description: "Structured competitor profile with SEO metrics, AI visibility, positioning, and proof observations"

tools_used:
  - Ahrefs:site-explorer-metrics
  - Ahrefs:site-explorer-backlinks-stats
  - Ahrefs:site-explorer-domain-rating
  - Ahrefs:brand-radar-mentions-overview
  - web_fetch

chains_from: []
chains_to:
  - landscape-report-generator

tags:
  - competitor-research
  - foundation
  - ahrefs
  - competitive-intelligence
---

# Competitor Landscape Research

## What This Skill Does

Pulls SEO metrics, AI visibility data, and qualitative positioning analysis for a single competitor domain. The agent gets a structured competitor profile that feeds into the competitive landscape section of the Target Market Landscape Report.

---

## Context the Agent Needs

This skill is designed to run as a sub-agent task — one instance per competitor, up to 10 running in parallel. The primary agent handles competitor discovery (identifying the top 10 via SERP analysis and member input), then delegates individual research to sub-agents running this skill.

Each sub-agent operates in isolation with zero shared context. It receives one competitor domain, one brand name, and optional industry context. It returns a structured profile. The primary agent aggregates all profiles into the competitive landscape.

Metrics are intentionally high-level — this is orientation, not a deep competitive audit. The purpose is to understand who owns the market, how big they are, and how they position themselves. Deep content gap analysis and keyword overlap come later in content strategy.

The Ahrefs MCP provides all needed data. SEO metrics come from Site Explorer endpoints. AI visibility comes from Brand Radar. No additional tools are needed for the quantitative analysis. Web fetch handles the qualitative site scraping.

**Key constraint:** This is orientation research, not a competitive playbook. Keep metrics high-level. The member needs to know who's running and roughly how big they are — not a detailed breakdown of every keyword.

---

## Workflow — Execute In This Order

Do not skip steps. Do not summarize. Produce every field in the output.

---

### STEP 1: Pull SEO Metrics

Retrieve core SEO metrics from Ahrefs.

**Input:** Competitor domain URL.

**Process:**
1. Call `Ahrefs:site-explorer-metrics` with:
   - `target`: competitor domain
   - `date`: today's date (YYYY-MM-DD)
   - `mode`: "subdomains"
   - Extract: `org_keywords` (organic keywords), `org_traffic` (organic traffic)

2. Call `Ahrefs:site-explorer-backlinks-stats` with:
   - `target`: competitor domain
   - `date`: today's date (YYYY-MM-DD)
   - `mode`: "subdomains"
   - Extract: `live` (total backlinks), `live_refdomains` (referring domains)

3. Call `Ahrefs:site-explorer-domain-rating` with:
   - `target`: competitor domain
   - `date`: today's date (YYYY-MM-DD)
   - Extract: `domain_rating`

**Output:** SEO metrics object: { dr, organic_keywords, organic_traffic, total_backlinks, referring_domains }

**Decision gate:**
- If any Ahrefs call fails → record the metric as "unavailable" and proceed with remaining calls. Do not abort.
- If domain returns zero across all metrics → the domain may be incorrect. Note it and proceed.

---

### STEP 2: Pull AI Visibility

Retrieve AI mention data from Ahrefs Brand Radar.

**Input:** Competitor brand name.

**Process:**
1. Call `Ahrefs:brand-radar-mentions-overview` for non-Google sources:
   - `brand`: competitor brand name
   - `data_source`: ["chatgpt", "perplexity", "gemini", "copilot"]
   - `select`: "brand,total,only_target_brand"
   - Extract: total mentions per source

2. Call `Ahrefs:brand-radar-mentions-overview` for Google sources:
   - `brand`: competitor brand name
   - `data_source`: ["google_ai_overviews", "google_ai_mode"]
   - `select`: "brand,total,only_target_brand"
   - Extract: total mentions per source

3. Note: Google sources and non-Google sources CANNOT be mixed in a single call. Always make two separate calls.

**Output:** AI visibility object: { google_ai_overviews, google_ai_mode, chatgpt, perplexity, gemini, copilot, total }

**Decision gate:**
- If Brand Radar returns zero mentions → this is valid data, not an error. The competitor has no AI visibility. Record as zero.
- If Brand Radar call fails → record AI visibility as "unavailable" and proceed. Do not abort.

---

### STEP 3: Scrape Positioning and Proof

Analyze the competitor's website for qualitative signals.

**Input:** Competitor domain URL + industry context.

**Process:**
1. Web fetch the competitor's homepage. Extract:
   - Primary headline / value proposition
   - How they describe what they do (first 2-3 sentences or hero section)
   - Any specific niche, audience, or specialization claims
   - Proof signals visible above the fold: logos, review counts, awards, certifications

2. Web fetch the competitor's about page (try /about, /about-us, /company). Extract:
   - Team size or experience claims
   - Years in business
   - Certifications, awards, or notable clients mentioned
   - Any specialization or positioning statements

3. Synthesize into:
   - **Positioning summary:** 1-2 sentences on how they present themselves and who they target
   - **Proof observed:** List of proof types visible on the site (reviews, case studies, logos, certifications, team credentials)
   - **Content notes:** High-level observation on content strategy (blog present? resource center? how many pages roughly?)

**Output:** Qualitative analysis: { positioning, proof_observed, content_notes }

**Decision gate:**
- If homepage fetch fails → try www. prefix or https variant. If still fails, note "site unreachable" and proceed with metrics only.
- If about page doesn't exist → skip about page analysis, work from homepage only.

---

### STEP 4: Compile Competitor Profile

Assemble all data into the output structure.

**Input:** All outputs from Steps 1-3.

**Process:**
1. Merge all data into a single structured profile
2. Format numbers for readability (e.g., 12500 → "12,500")
3. Ensure all fields are present — use "unavailable" for any failed data points, "0" for confirmed zeros

**Output:** Complete competitor profile in this format:

```json
{
  "domain": "competitor.com",
  "brand_name": "Competitor Inc",
  "metrics": {
    "dr": 45,
    "organic_keywords": 12500,
    "organic_traffic": 8400,
    "total_backlinks": 34000,
    "referring_domains": 890
  },
  "ai_visibility": {
    "google_ai_overviews": 12,
    "google_ai_mode": 3,
    "chatgpt": 8,
    "perplexity": 5,
    "gemini": 4,
    "copilot": 2,
    "total": 34
  },
  "positioning": "Brief summary of how they position themselves and who they target",
  "proof_observed": "Reviews (4.8 stars, 200+ on Google), 5 case studies, SOC 2 certified, client logos (Microsoft, Salesforce)",
  "content_notes": "Active blog (~150 posts), resource center with whitepapers, no video content visible"
}
```

---

## Output Format

The output is a JSON-structured competitor profile as shown in Step 4. Every field must be present. Use "unavailable" for failed data pulls, "0" for confirmed zeros, and "none observed" for qualitative fields where nothing was found.

**Formatting rules:**
- Metrics are raw numbers (not formatted strings) in the JSON — formatting happens in the report generator
- Positioning summary: 1-2 sentences max
- Proof observed: comma-separated list of proof types with specifics where available
- Content notes: 1 sentence max
- Total output: the JSON object, nothing else. No preamble, no commentary.

---

## Edge Cases & Judgment Calls

**When the competitor domain redirects to a different domain:**
Follow the redirect and research the final destination domain. Note both domains in the profile.

**When the competitor is a large platform (e.g., Yelp, Thumbtack) rather than a direct competitor:**
Research it anyway — the member or primary agent identified it as a competitor. Platforms compete for the same search real estate. Note in positioning that this is a marketplace/platform, not a direct service provider.

**When AI visibility returns zero across all surfaces:**
This is valuable intelligence, not a failure. Many businesses have zero AI visibility. Record it accurately — it may represent an opportunity gap the member can exploit.

**When the competitor's site is behind a login or heavily JavaScript-rendered:**
Extract what you can from the initial HTML. If the homepage is completely empty without JS execution, note "site requires JavaScript rendering — limited qualitative analysis" and provide metrics only.

---

## What This Skill Does NOT Do

- Does NOT discover competitors — the primary agent handles discovery via SERP analysis and member input. This skill researches one competitor it's given.
- Does NOT compare competitors to each other — aggregation and comparison happens in the primary agent after all profiles are collected.
- Does NOT do deep content gap analysis — that belongs in content strategy skills.
- Does NOT evaluate backlink quality — total counts only at this stage.
- If asked for keyword overlap or content gap analysis, suggest those as separate downstream analyses.

---

## Examples

**Example 1: Established SaaS Competitor**

Input: Domain: "hubspot.com", Brand: "HubSpot", Industry: "CRM and marketing automation"

Output (abbreviated):
```json
{
  "domain": "hubspot.com",
  "brand_name": "HubSpot",
  "metrics": {
    "dr": 93,
    "organic_keywords": 5840000,
    "organic_traffic": 18200000,
    "total_backlinks": 395000000,
    "referring_domains": 742000
  },
  "ai_visibility": {
    "google_ai_overviews": 4820,
    "google_ai_mode": 1240,
    "chatgpt": 3100,
    "perplexity": 2800,
    "gemini": 1950,
    "copilot": 890,
    "total": 14800
  },
  "positioning": "All-in-one CRM platform for scaling businesses. Positions as the growth platform that connects marketing, sales, and service.",
  "proof_observed": "228,000+ customers in 135 countries, G2 leader badges, extensive case study library, partner ecosystem",
  "content_notes": "Massive content operation — blog, academy, certifications, free tools. Content-led growth model."
}
```

Why this is correct: High-level metrics captured cleanly. Positioning is a concise summary, not a full analysis. Proof lists what's visible, not an evaluation of quality.

---

**Example 2: Small Local Competitor With No AI Visibility**

Input: Domain: "smithplumbing.co.nz", Brand: "Smith Plumbing", Industry: "residential plumbing Auckland"

Output (abbreviated):
```json
{
  "domain": "smithplumbing.co.nz",
  "brand_name": "Smith Plumbing",
  "metrics": {
    "dr": 12,
    "organic_keywords": 340,
    "organic_traffic": 180,
    "total_backlinks": 890,
    "referring_domains": 45
  },
  "ai_visibility": {
    "google_ai_overviews": 0,
    "google_ai_mode": 0,
    "chatgpt": 0,
    "perplexity": 0,
    "gemini": 0,
    "copilot": 0,
    "total": 0
  },
  "positioning": "General residential plumber in Auckland. No clear specialization — positions on reliability and fast response times.",
  "proof_observed": "Google reviews (4.6 stars, 89 reviews), Master Plumber certified, 15 years experience claim",
  "content_notes": "5-page brochure site, no blog, no resources"
}
```

Why this is correct: Zero AI visibility is recorded as data, not treated as an error. The small site still gets the full profile treatment — the primary agent needs consistent data structures across all competitors to build the comparison table.
