---
name: sitemap-diff
version: "1.0"
description: >
  Pulls a hub site's sitemap, diffs it against the ASN Tracker sheet, and
  returns the list of published pages that don't yet have satellites deployed.
  Use this skill whenever a process or cron job needs to discover which hub
  pages are eligible for new ASN deployment. This skill outputs a JSON array
  of candidate hub URLs ordered oldest-first by last-modified date. Always
  trigger when sitemap detection, new-page discovery, or ASN cron eligibility
  checks are needed — even if phrased casually.

# === CROSS-AGENT METADATA ===

inputs:
  required:
    - type: text
      label: "site-root"
      description: "Root domain of the hub site (e.g., 'jonathanboshoff.com') OR an explicit sitemap URL"
    - type: text
      label: "tracker-sheet-id"
      description: "Google Sheets ID of the ASN Roster + Tracker sheet"
  optional:
    - type: text
      label: "tracker-tab-name"
      description: "Tab name where deployed hub URLs are tracked (default: 'Tracker')"
    - type: text
      label: "hub-url-column"
      description: "Column letter in the Tracker tab containing hub URLs (default: 'A')"

outputs:
  - type: json
    label: "eligible-hub-urls"
    description: >
      JSON array of hub URLs present in sitemap but not in tracker,
      ordered oldest-first by lastmod when available. Each entry includes
      the URL, lastmod (if found), and a discovery source note.

tools_used:
  - page_scraper     # Custom scraper at github.com/boshify/page_scraper
  - web_fetch        # Fallback for raw sitemap XML when lastmod extraction is needed

chains_from: []
chains_to:
  - satellite-content-produce

tags:
  - sitemap
  - asn
  - discovery
  - cron
---

# Sitemap Diff

## What This Skill Does

Given a hub site and the ASN Tracker sheet, returns which published pages haven't been satellited yet — ordered oldest-first so cron runs pick up older content before newer content. The caller gets a clean eligible-pages list without any further filtering or checking needed.

---

## Context the Agent Needs

This skill serves the ASN Deployment cron. Every daily run needs to answer: "Which of this member's published pages should I build satellites for today?" The answer is: pages that exist in the sitemap AND aren't already in the tracker.

QDP reports are not checked by this skill. QDP lives in chat history, not in any structured store. The deployment process handles the missing-QDP gate per-page at runtime (asks the member to provide, or offers to run `query-deserves-page`). This skill stays scoped to sitemap vs tracker.

Sitemap discovery follows a standard fallback chain. Most modern CMSs expose `/sitemap.xml` or `/sitemap_index.xml`. Some require reading `robots.txt` to find the sitemap reference. The skill tries each in order.

**Key constraint:** Return an empty array when no new pages exist. Do not fabricate candidates. Do not return pages that have any row in the tracker regardless of status — a Deferred page is still "in the tracker" and not eligible for a new deployment run.

---

## Workflow — Execute In This Order

### STEP 1: Resolve the Sitemap URL

**Input:** site-root string from caller.

**Process:**
1. If input already ends in `.xml` or contains `sitemap` in the path → treat as explicit sitemap URL, skip to Step 2.
2. Otherwise, try these URLs in order:
   - `https://{site-root}/sitemap.xml`
   - `https://{site-root}/sitemap_index.xml`
   - Fetch `https://{site-root}/robots.txt` and parse for `Sitemap: <url>` directive
3. Use the first one that returns a 200 response with sitemap-like content.

**Output:** Resolved sitemap URL.

**Decision gate:**
- If none of the three patterns work → return error status `sitemap_not_found` with the URLs attempted.

---

### STEP 2: Fetch the Sitemap

**Input:** Resolved sitemap URL from Step 1.

**Process:**
1. Call `page_scraper` with `is_sitemap: true`. Returns `{"ok": true, "urls": [...]}`.
2. If the URL list is empty or the call fails → try one retry.
3. If still empty, flag `sitemap_empty` and return empty eligible list — not an error, but surfaced to the caller.

**Output:** Array of URLs from the sitemap.

---

### STEP 3: Extract Last-Modified Dates (Best Effort)

**Input:** Sitemap URL from Step 1, URL list from Step 2.

**Process:**
1. Fetch the raw sitemap XML with `web_fetch` (not the extracted URL list — the full XML).
2. Parse for `<url><loc>...</loc><lastmod>...</lastmod></url>` blocks.
3. Build a map of `url → lastmod` for every URL that has a `lastmod` tag.
4. URLs without `lastmod` get `null` for their date.
5. If the sitemap is a sitemap index (contains `<sitemap>` elements rather than `<url>`), this step skips lastmod extraction and returns `null` for all URLs. The diff still works — ordering just defaults to sitemap order.

**Output:** URL-to-lastmod map. Missing lastmods are acceptable.

**Decision gate:**
- If XML parse fails → continue with `null` lastmods for all URLs. Do not block the process.

---

### STEP 4: Read the Tracker

**Input:** tracker-sheet-id from caller, optional tab name and column letter.

**Process:**
1. Read the tracker tab (default `Tracker`, default column `A`).
2. Extract all non-empty hub URL values.
3. Normalize URLs (strip trailing slashes, lowercase the host, drop URL fragments) for consistent comparison.
4. Deduplicate the list.

**Output:** Set of hub URLs already in the tracker.

**Decision gate:**
- If the sheet read fails → return error status `tracker_read_failed`. Do not proceed with a partial diff — false positives would cause duplicate satellite deployments.

---

### STEP 5: Diff and Order

**Input:** Sitemap URL list (Step 2), lastmod map (Step 3), tracker URL set (Step 4).

**Process:**
1. Normalize sitemap URLs the same way tracker URLs were normalized (trailing slashes, lowercase host, no fragments).
2. Compute set difference: sitemap URLs NOT in tracker set.
3. For each eligible URL, attach its lastmod (or null).
4. Sort ascending by lastmod. URLs with `null` lastmod go to the end of the list.
5. If any two URLs have the same lastmod, preserve sitemap order as a stable tiebreaker.

**Output:** Ordered array of eligible candidates.

---

### STEP 6: Return the Report

Return a single JSON object:

```json
{
  "status": "ok",
  "site_root": "jonathanboshoff.com",
  "sitemap_url_used": "https://jonathanboshoff.com/sitemap.xml",
  "sitemap_urls_found": 47,
  "tracker_urls_found": 38,
  "eligible_count": 9,
  "eligible": [
    {
      "url": "https://jonathanboshoff.com/ai-content-seo-guide",
      "lastmod": "2026-01-15",
      "source": "sitemap"
    },
    {
      "url": "https://jonathanboshoff.com/pagerank-flow",
      "lastmod": "2026-02-03",
      "source": "sitemap"
    },
    {
      "url": "https://jonathanboshoff.com/thin-content-audit",
      "lastmod": null,
      "source": "sitemap"
    }
  ]
}
```

**On failure:**

```json
{
  "status": "sitemap_not_found | sitemap_empty | tracker_read_failed",
  "site_root": "...",
  "error": "Specific description of what failed",
  "urls_attempted": ["..."],
  "eligible": []
}
```

---

## Output Format

Always return JSON. No prose. No commentary.

**Required fields:**
- `status` (string: ok / sitemap_not_found / sitemap_empty / tracker_read_failed)
- `site_root` (string)
- `sitemap_url_used` (string, empty if status is sitemap_not_found)
- `sitemap_urls_found` (integer)
- `tracker_urls_found` (integer)
- `eligible_count` (integer)
- `eligible` (array of objects)

**Per-eligible-entry fields:**
- `url` (string, fully normalized)
- `lastmod` (string in YYYY-MM-DD format, or null)
- `source` (string: "sitemap" — reserved for future expansion)

---

## Edge Cases & Judgment Calls

**When the sitemap is a sitemap index (links to other sitemaps, not to pages):**
Follow one level of nesting. Fetch each child sitemap in the index and aggregate URLs. Do not recurse beyond one level — pathological sitemap structures would blow up the skill. Flag in output if nested fetches happened.

**When the site has no sitemap at all:**
Return status `sitemap_not_found`. Do not attempt to crawl the site to build one from scratch — that's out of scope and expensive. Suggest in the error message: "Consider adding a sitemap, or invoke ASN deployment manually per-page."

**When URL normalization causes collisions (trailing slash vs no trailing slash for the same page):**
The normalized form wins for diffing. Only one satellite deployment per canonical URL. If the tracker has the slash version and the sitemap has the non-slash version, they're the same page — not eligible.

**When the tracker contains a hub URL that's no longer in the sitemap (page was deleted/unpublished):**
Ignore it. Tracker-only URLs are not the skill's concern — they're historical deployments for pages that no longer exist. Future maintenance methodology handles stale-hub scenarios.

**When lastmod dates look invalid or in the future:**
Keep them as-is. The skill doesn't validate dates — it sorts by string comparison, and ISO 8601 dates sort correctly even if individual values are suspicious. Garbage lastmod in sitemap → garbage ordering, but the diff is still correct.

**When the sitemap contains URL types that aren't blog posts (images, category pages, tag archives):**
Return them all. The skill does not filter by content type. The deployment process decides whether each candidate is a viable hub page (it'll check for QDP report, which is only expected on real content pages). False positives are cheap — the deployment process catches them.

**When tracker-tab-name or hub-url-column are non-default and the caller didn't pass them:**
Use the defaults (`Tracker`, column `A`). If the read returns zero URLs from a sheet that's known to have deployments, return status `tracker_read_failed` with a specific error — the sheet schema probably changed and the caller needs to pass the right tab/column.

---

## What This Skill Does NOT Do

- Does NOT verify QDP presence — QDP lives in chat history, not a queryable store; the deployment process handles QDP check per-page
- Does NOT filter by content type (blog posts only, exclude landing pages, etc.) — returns everything in the sitemap
- Does NOT pick which candidate to process — returns the full eligible list, caller picks (typically "oldest first, one per cron run")
- Does NOT write anything to the tracker — read-only against both sitemap and tracker
- Does NOT crawl the site — sitemap-only, no alternative discovery methods
- Does NOT check if a candidate URL is actually reachable / 200 / indexed — just that it's listed in the sitemap
- Does NOT deduplicate the tracker itself — if the tracker has duplicate rows, the skill's output is still correct because it only needs the *set* of URLs for the diff

---

## Examples

**Example 1: Happy path, mixed lastmods**

Input:
```
site_root: "jonathanboshoff.com"
tracker_sheet_id: "1AbC...xyz"
```

Output (abbreviated):
```json
{
  "status": "ok",
  "site_root": "jonathanboshoff.com",
  "sitemap_url_used": "https://jonathanboshoff.com/sitemap.xml",
  "sitemap_urls_found": 47,
  "tracker_urls_found": 38,
  "eligible_count": 9,
  "eligible": [
    {"url": "https://jonathanboshoff.com/content-decay-audit", "lastmod": "2025-11-22", "source": "sitemap"},
    {"url": "https://jonathanboshoff.com/ai-content-seo-guide", "lastmod": "2026-01-15", "source": "sitemap"},
    {"url": "https://jonathanboshoff.com/pagerank-flow", "lastmod": "2026-02-03", "source": "sitemap"},
    {"url": "https://jonathanboshoff.com/thin-content-audit", "lastmod": null, "source": "sitemap"}
  ]
}
```

Why this is correct: The oldest-lastmod URL is first. URLs without lastmod go to the end. Caller's cron picks `eligible[0]` — the page most likely to have matured search performance, making it the highest-value ASN target.

---

**Example 2: Sitemap not found**

Input:
```
site_root: "obscureclient.example"
tracker_sheet_id: "1AbC...xyz"
```

Output:
```json
{
  "status": "sitemap_not_found",
  "site_root": "obscureclient.example",
  "sitemap_url_used": "",
  "sitemap_urls_found": 0,
  "tracker_urls_found": 0,
  "eligible_count": 0,
  "eligible": [],
  "error": "Sitemap not found. Tried: https://obscureclient.example/sitemap.xml, https://obscureclient.example/sitemap_index.xml, https://obscureclient.example/robots.txt (no Sitemap directive). Consider adding a sitemap or invoking ASN deployment manually per-page.",
  "urls_attempted": [
    "https://obscureclient.example/sitemap.xml",
    "https://obscureclient.example/sitemap_index.xml",
    "https://obscureclient.example/robots.txt"
  ]
}
```

Why this is correct: The skill tried all three standard patterns, failed cleanly, and surfaced what was tried plus a specific remediation suggestion. The caller knows the skill did its job — the site just doesn't have sitemap infrastructure.

---

**Example 3: All pages already deployed**

Input:
```
site_root: "jonathanboshoff.com"
tracker_sheet_id: "1AbC...xyz"
```

Output:
```json
{
  "status": "ok",
  "site_root": "jonathanboshoff.com",
  "sitemap_url_used": "https://jonathanboshoff.com/sitemap.xml",
  "sitemap_urls_found": 47,
  "tracker_urls_found": 47,
  "eligible_count": 0,
  "eligible": []
}
```

Why this is correct: Every URL in the sitemap has at least one row in the tracker. Nothing eligible for a new deployment. The cron reads this and exits cleanly with "no work this run." No error — this is expected steady state for a fully-satellited site.
