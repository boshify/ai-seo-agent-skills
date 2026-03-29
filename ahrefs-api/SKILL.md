---
name: ahrefs-api
version: "1.0"
description: >
  Reference index for the Ahrefs v3 REST API. Use this skill whenever you need
  to know which Ahrefs endpoint to call, what parameters it accepts, what fields
  it returns, or how to handle API-specific behaviour (unit costs, rate limits,
  monetary value formatting, Brand Radar source restrictions). Fetch this skill
  before making any Ahrefs API call you haven't made before, or when debugging
  an unexpected response.

inputs:
  required: []
  optional:
    - type: text
      label: "endpoint-category"
      description: "Narrow the reference to a specific category (site-explorer, brand-radar, keywords-explorer, etc.)"

outputs:
  - type: markdown
    label: "api-reference"
    description: "Endpoint index, parameter reference, and usage notes for the requested category"

tools_used: []

chains_from: []
chains_to: []

tags:
  - ahrefs
  - reference
  - api
  - seo-data
---

# Ahrefs API — Reference Index

## What This Skill Does

Acts as a structured index to the Ahrefs v3 REST API. Covers every endpoint category, the fields you'll actually use in practice, gotchas that trip up integrations, and the exact curl patterns for the most common calls.

Full official documentation: https://docs.ahrefs.com/api/docs/introduction

---

## Authentication & Base URL

**Base URL:** `https://api.ahrefs.com/v3/`

**Auth header:** `-H "Authorization: Bearer $AHREFS_API_KEY"`

The API key is pre-configured as `$AHREFS_API_KEY` in the exec environment. Never ask the member for it. Never display it in output.

**Verify connectivity / quota:**
```bash
curl -s "https://api.ahrefs.com/v3/subscription-info/limits-and-usage" \
  -H "Authorization: Bearer $AHREFS_API_KEY" | jq '.'
```

---

## Critical Gotchas

Read these before making any call:

1. **Monetary values are in USD cents, not dollars.** `org_cost`, `traffic_value`, `paid_cost` — divide by 100 to display in dollars.
2. **Brand Radar: Google and non-Google sources cannot be mixed in one call.** `google_ai_overviews` / `google_ai_mode` must be called separately from `chatgpt` / `perplexity` / `gemini` / `copilot`.
3. **`mode=subdomains` is the right default for domain analysis.** `mode=domain` excludes www and subdomains. `mode=subdomains` captures everything.
4. **Minimum 50 API units per request.** Calls are not free — batch only what you need, don't call speculatively.
5. **Rate limit: 60 requests/minute.** When running parallel sub-agents, stagger calls slightly. On 429, back off and retry.
6. **`select` parameter controls which columns are returned.** Only request what you need — some columns (like `response`) cost 10 units.
7. **`date` format is `YYYY-MM-DD`.** Use today's date for current metrics.

---

## Endpoint Categories

### Site Explorer

Base path: `/v3/site-explorer/`

All site explorer endpoints accept:
- `target` (required) — domain or URL
- `date` (required) — `YYYY-MM-DD`
- `mode` — `subdomains` (default), `domain`, `prefix`, `exact`

| Endpoint | Path | Key fields returned | Primary use |
|---|---|---|---|
| Metrics | `metrics` | `org_keywords`, `org_traffic`, `paid_keywords`, `paid_traffic`, `org_cost` | Domain-level SEO snapshot |
| Domain Rating | `domain-rating` | `domain_rating`, `ahrefs_rank` | Authority score |
| Backlinks Stats | `backlinks-stats` | `live`, `all_time`, `live_refdomains`, `all_time_refdomains` | Link profile volume |
| Organic Keywords | `organic-keywords` | Full keyword list with positions, volume, traffic | Keyword rankings |
| Organic Competitors | `organic-competitors` | Competitor domains + overlap metrics | Find competitors |
| Top Pages | `top-pages` | Pages ranked by organic traffic | Traffic-driving pages |
| Referring Domains | `referring-domains` | Domain list with DR, traffic | Backlink sources |
| All Backlinks | `all-backlinks` | Full backlink list | Link-level data |
| Broken Backlinks | `broken-backlinks` | Links pointing to 404/redirected pages | Link reclamation |
| Anchors | `anchors` | Anchor text distribution | Link profile quality |
| Linked Domains | `linked-domains` | Outbound domain targets | Site relationship map |
| Pages by Traffic | `pages-by-traffic` | Page-level traffic ranking | Content performance |
| Pages by Backlinks | `pages-by-backlinks` | Pages with most links | Link equity |
| Metrics History | `metrics-history` | Time series for org_keywords, org_traffic | Trend analysis |
| Domain Rating History | `domain-rating-history` | DR over time | Authority growth |
| Refdomains History | `refdomains-history` | Referring domain count over time | Link growth |
| Metrics by Country | `metrics-by-country` | Traffic/keywords broken down by country | Geo performance |
| Paid Pages | `paid-pages` | Pages running paid ads | PPC intelligence |

**Most common calls:**
```bash
# Domain metrics snapshot
curl -s "https://api.ahrefs.com/v3/site-explorer/metrics?target=DOMAIN&date=DATE&mode=subdomains" \
  -H "Authorization: Bearer $AHREFS_API_KEY" | jq '.metrics | {org_keywords, org_traffic, org_cost}'

# Domain rating
curl -s "https://api.ahrefs.com/v3/site-explorer/domain-rating?target=DOMAIN&date=DATE" \
  -H "Authorization: Bearer $AHREFS_API_KEY" | jq '.domain_rating.domain_rating'

# Backlink volume
curl -s "https://api.ahrefs.com/v3/site-explorer/backlinks-stats?target=DOMAIN&date=DATE&mode=subdomains" \
  -H "Authorization: Bearer $AHREFS_API_KEY" | jq '.metrics | {live, live_refdomains}'

# Find organic competitors
curl -s "https://api.ahrefs.com/v3/site-explorer/organic-competitors?target=DOMAIN&date=DATE&mode=subdomains&limit=10" \
  -H "Authorization: Bearer $AHREFS_API_KEY" | jq '.competitors'
```

---

### Brand Radar

Base path: `/v3/brand-radar/`

Tracks brand mentions in AI-generated responses across chatbots and Google AI surfaces.

**CRITICAL:** Google sources (`google_ai_overviews`, `google_ai_mode`) and non-Google sources (`chatgpt`, `perplexity`, `gemini`, `copilot`) **cannot be mixed in a single call**. Always make two separate calls.

| Endpoint | Path | Key fields | Primary use |
|---|---|---|---|
| Mentions Overview | `mentions-overview` | `total`, `only_target_brand`, `target_and_competitors_brands` | Total AI mention volume |
| Impressions Overview | `impressions-overview` | `total`, `only_target_brand` | Estimated impressions |
| Share of Voice | `sov-overview` | Share of voice vs competitors | Competitive AI visibility |
| Mentions History | `mentions-history` | Time series of mentions | Trend tracking |
| Impressions History | `impressions-history` | Impressions over time | Trend tracking |
| SOV History | `sov-history` | Share of voice over time | Competitive trend |
| Cited Domains | `cited-domains` | Domains cited alongside brand | Authority context |
| Cited Pages | `cited-pages` | Specific pages cited | Content that drives AI mentions |
| AI Responses | `ai-responses` | Full AI response text | Qualitative analysis |

**`data_source` values:**
- Non-Google: `chatgpt`, `perplexity`, `gemini`, `copilot`
- Google: `google_ai_overviews`, `google_ai_mode`

**Most common calls:**
```bash
# Non-Google AI mentions
curl -s "https://api.ahrefs.com/v3/brand-radar/mentions-overview?brand=BRAND&select=brand,total,only_target_brand&data_source=chatgpt,perplexity,gemini,copilot" \
  -H "Authorization: Bearer $AHREFS_API_KEY" | jq '.metrics[0] | {total, only_target_brand}'

# Google AI mentions (separate call — cannot mix with above)
curl -s "https://api.ahrefs.com/v3/brand-radar/mentions-overview?brand=BRAND&select=brand,total,only_target_brand&data_source=google_ai_overviews,google_ai_mode" \
  -H "Authorization: Bearer $AHREFS_API_KEY" | jq '.metrics[0] | {total, only_target_brand}'
```

**Zero mentions is valid data, not an error.** Many brands have zero AI visibility — record it as zero, don't treat it as a failed call.

---

### Keywords Explorer

Base path: `/v3/keywords-explorer/`

Keyword research and volume data.

| Endpoint | Path | Key fields | Primary use |
|---|---|---|---|
| Overview | `overview` | `volume`, `difficulty`, `cpc`, `clicks`, `serp_features` | Keyword metrics |
| Matching Terms | `matching-terms` | Keyword list with metrics | Keyword discovery |
| Search Suggestions | `search-suggestions` | Autocomplete-style suggestions | Content ideation |
| Related Terms | `related-terms` | Semantically related keywords | Topic mapping |
| Volume by Country | `volume-by-country` | Country-level search volume breakdown | Geo targeting |
| Volume History | `volume-history` | Monthly volume over time | Trend analysis |

**Common call:**
```bash
# Keyword overview
curl -s "https://api.ahrefs.com/v3/keywords-explorer/overview?keywords=KEYWORD&country=us" \
  -H "Authorization: Bearer $AHREFS_API_KEY" | jq '.'
```

---

### SERP Overview

Base path: `/v3/serp-overview/`

Top 100 organic results for a keyword.

```bash
curl -s "https://api.ahrefs.com/v3/serp-overview?keyword=KEYWORD&country=us" \
  -H "Authorization: Bearer $AHREFS_API_KEY" | jq '.organic'
```

Key fields per result: `url`, `domain`, `position`, `traffic`, `keywords`, `ahrefs_rank`

---

### Rank Tracker

Base path: `/v3/rank-tracker/`

**These endpoints are free (no API units consumed).**

| Endpoint | Path | Primary use |
|---|---|---|
| Overview | `overview` | Project keyword rankings snapshot |
| SERP Overview | `serp-overview` | SERP data for tracked keywords |
| Competitors Overview | `competitors-overview` | Competitor rankings for same keywords |
| Competitors Pages | `competitors-pages` | Competitor page-level data |
| Competitors Stats | `competitors-stats` | Aggregate competitor stats |

---

### Site Audit

Base path: `/v3/site-audit/`

| Endpoint | Path | Primary use |
|---|---|---|
| Projects | `projects` | Crawl project health scores |
| Issues | `issues` | SEO issues by type and severity |
| Page Explorer | `page-explorer` | Per-page crawl data |
| Page Content | `page-content` | HTML and text content for a crawled page |

---

### Batch Analysis

Base path: `/v3/batch-analysis`

Analyze up to 100 targets (URLs or domains) in a single call — more efficient than looping individual site-explorer calls.

```bash
curl -s -X POST "https://api.ahrefs.com/v3/batch-analysis" \
  -H "Authorization: Bearer $AHREFS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"targets":["domain1.com","domain2.com"],"select":"url_from,domain_rating,org_traffic","date":"DATE","mode":"subdomains"}' \
  | jq '.results'
```

---

### GSC Insights

Base path: `/v3/gsc/`

Google Search Console data synced through Ahrefs. Requires GSC connected in the Ahrefs account.

| Endpoint | Path | Primary use |
|---|---|---|
| Keywords | `keywords` | GSC keyword impressions, clicks, CTR, position |
| Pages | `pages` | GSC page performance |
| Keyword History | `keyword-history` | Single keyword over time |
| Page History | `page-history` | Single page over time |
| Performance History | `performance-history` | Overall GSC performance trend |
| Performance by Device | `performance-by-device` | Desktop vs mobile vs tablet |
| Performance by Position | `performance-by-position` | CTR/clicks by SERP position |
| CTR by Position | `ctr-by-position` | CTR curve |
| Positions History | `positions-history` | Position tracking over time |
| Anonymous Queries | `anonymous-queries` | Queries hidden by GSC |
| Metrics by Country | `metrics-by-country` | Performance by country |
| Pages History | `pages-history` | Page performance over time |

---

### Web Analytics

Base path: `/v3/web-analytics/`

First-party analytics data (requires Ahrefs tracking script installed).

Main endpoints: `stats`, `chart`, `top-pages`, `countries`, `devices`, `browsers`, `operating-systems`, `source-channels`, `sources`, `referrers`, `utm-params`, `entry-pages`, `exit-pages`

Each has a corresponding `-chart` variant for time-series output.

---

### Management (Free — no units)

Base path: `/v3/management/`

| Endpoint | Path | Primary use |
|---|---|---|
| Projects | `projects` | List Rank Tracker projects |
| Project Keywords | `project-keywords` | Keywords in a project |
| Project Competitors | `project-competitors` | Competitors in a project |
| Keyword Lists | `keyword-list-keywords` | Keywords in a keyword list |
| Locations | `locations` | Supported geo locations |
| Brand Radar Prompts | `brand-radar-prompts` | Custom Brand Radar prompts |

---

### Subscription Info (Free — no units)

```bash
curl -s "https://api.ahrefs.com/v3/subscription-info/limits-and-usage" \
  -H "Authorization: Bearer $AHREFS_API_KEY" | jq '.'
```

Returns current plan limits, units used, and units remaining. Use this to diagnose quota issues before concluding a call failed.

---

## Response Format

All endpoints default to JSON. Add `&output=json` explicitly if needed. Other formats available: `csv`, `xml`, `php`.

Paginated endpoints support `limit` and `offset` parameters. Default `limit` varies by endpoint — check if results seem truncated.

---

## Rate Limiting

- **60 requests/minute** default
- HTTP 429 = rate limit hit
- On 429: wait and retry with exponential backoff
- When running 10 parallel sub-agents each making 5 calls = 50 calls near-simultaneously — stagger spawning slightly to avoid bursting the limit

---

## What This Skill Does NOT Do

- Does NOT make any API calls itself — it's a reference only
- Does NOT store or cache API results — each call fetches fresh data
- Does NOT handle authentication setup — the key is pre-configured in the environment
- For endpoint parameters not listed here, fetch the full docs at https://docs.ahrefs.com/api/docs/introduction
