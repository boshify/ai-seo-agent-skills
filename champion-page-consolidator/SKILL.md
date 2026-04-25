---
name: champion-page-consolidator
version: "1.0"
description: >
  Identifies cannibalization on a website by walking the user through Google Search Console
  exports, working backward from money pages to find pages bleeding authority. Produces a
  consolidation playbook with SERP-verified evidence and clear next steps.
  Use this skill whenever the user says "find cannibalization", "audit my money pages",
  "champion page audit", "consolidate my pages", "kill cannibalizing pages", "which pages
  are competing", "consolidation plan", "fix cannibalization", "PageRank consolidation",
  "find pages stealing my rankings", or provides a domain along with any intent to find
  competing pages, consolidate authority, identify champions, or build a redirect plan.
  Also trigger when the user asks "why isn't my SEO working" alongside a site that
  publishes lots of long-tail variants, mentions champion pages, authority hoarding, or
  splitting rankings across pages. Always trigger when consolidation, cannibalization, or
  champion page intent is present — even if phrased casually.

inputs:
  required:
    - type: text
      label: "site-url"
      description: "Root domain of the site to audit (e.g., https://example.com)"
    - type: file
      label: "gsc-exports"
      description: "Google Search Console Excel exports — uploaded across multiple stages of the audit (site-wide, per-money-page, per-query, per-suspect)"
  optional:
    - type: text
      label: "money-pages"
      description: "Optional list of known money page URLs. If omitted, skill scrapes nav and confirms with user."

outputs:
  - type: markdown
    label: "consolidation-playbook"
    description: "Money-page-anchored audit with cannibalization clusters, GSC and SERP evidence, first-pass calls, and verification next steps"

tools_used:
  - web_fetch
  - web_search

chains_from: []
chains_to: []

tags:
  - seo
  - ai-seo
  - cannibalization
  - pagerank
  - consolidation
  - champion-pages
---

# Champion Page Consolidator

## What This Skill Does

Walks the user through a guided cannibalization audit using Google Search Console exports they pull themselves. Outputs a money-page-anchored consolidation playbook with GSC evidence, SERP verification, and explicit next steps before any redirect decision.

---

## Context the Agent Needs

The skill operates on one belief: **PageRank is the most underrated ranking factor in AI search**, and most sites bleed it across long-tail variants competing with their highest-revenue pages. The fix is consolidation — but only where it actually matters. Cannibalization between two zero-traffic pages is noise. Cannibalization siphoning queries off a money page is the business problem.

The skill runs Jonathan's IRL diagnostic process, encoded as a guided audit:

1. Site-wide overview first — spot URL pattern clusters at a glance before going deep.
2. Money pages anchor priority. Revenue defines what's worth investigating.
3. Top queries per money page reveal what's at risk.
4. Site-wide query filter shows every page on the site competing for those queries.
5. Each suspect gets the same depth as the money page (top 3 queries pulled).
6. SERP evidence is the verdict layer. The SERP itself reveals whether the search engine treats this query as deserving a separate page or as a sub-topic.

The skill never says "redirect this." It says "this is the situation, this is the SERP evidence, verify and decide."

**Key constraint:** Every cannibalization call must cite specific GSC evidence (shared queries, click distribution) AND SERP evidence (page types ranking for the suspect's top query). No verdict without both.

The skill works with GSC primarily, but accepts Ahrefs or SEMrush as fallbacks if the user does not have GSC access.

---

## How GSC Exports Work

The skill auto-detects what each uploaded file represents by reading the Filters tab.

**Every GSC export has these tabs:**
- `Filters` — what's filtered (Search type, Date range, Page, Query, etc.)
- `Chart` — daily metrics over the date range
- `Queries` — top 1000 queries (capped by GSC)
- `Pages` — top pages
- `Countries`, `Devices`, `Search appearance` — secondary breakdowns

**Filter signatures the skill recognizes:**

| Filters tab content | What it is | Used in |
|---|---|---|
| Search type + Date only | Site-wide overview | Stage 1 |
| Search type + Date + **Page** | Per-page deep dive | Stages 3, 4 |
| Search type + Date + **Query** | Per-query suspect discovery | Stage 3 |

**Validation rules per upload:**
- Page-filtered exports must have exactly 1 row in the Pages tab matching the filter URL
- Query-filtered exports show every page ranking for that query in the Pages tab
- Site-wide exports have no Page or Query filter

**Date range expectations:**
- Strongly recommend Last 12 months
- If user provides a shorter range, warn but proceed
- Always read date range from the Filters tab and note it in output

**Data format notes:**
- CTR is stored as a decimal (0.008 = 0.8%) — multiply by 100 for display
- Position is the average ranking position across the date range
- Queries tab caps at 1000 rows — note this when the cap is hit

---

## Workflow Steps

### STEP 1: Confirm GSC access and request site-wide export

Set expectations. Get the foundational data.

**Input:** User-provided site URL.

**Process:**
1. Confirm the user has GSC access for the site they want audited.
2. If yes → request the site-wide export. If no → ask whether they have Ahrefs or SEMrush; if neither, tell them GSC is required and link to https://search.google.com/search-console/about.
3. Provide step-by-step instructions for the site-wide export:
   ```
   1. Open Google Search Console at https://search.google.com/search-console
   2. Select the property for [site URL]
   3. Click "Performance" in the left sidebar → "Search results"
   4. Set Date range to "Last 12 months" (top of the page)
   5. Do NOT apply any Page or Query filters
   6. Click "EXPORT" (top right) → "Download Excel"
   7. Upload the file here
   ```
4. Wait for the user to upload.

**Output:** User uploads the site-wide GSC export.

**Decision gate:**
- If user has GSC → proceed to Step 2 after upload.
- If user has only Ahrefs/SEMrush → adapt instructions (request a domain-level Top Pages and Top Keywords export instead) and adjust analysis. The core workflow stays the same; only the data source changes.
- If user has nothing → halt and explain GSC is required.

---

### STEP 2: Validate site-wide upload and scan for URL pattern clusters

The site-wide overview reveals the obvious cannibalization patterns at a glance — before any deep analysis.

**Input:** Site-wide GSC export from Step 1.

**Process:**
1. Read the Filters tab. Confirm signature is "Search type + Date only" (no Page or Query filter). If a filter exists, halt and ask user to re-export without filters.
2. Read the date range from Filters. If shorter than 12 months, warn the user that recommendations may be weaker but proceed.
3. Read the Pages tab. Extract every URL.
4. Group URLs by **path stem** — the URL path with the trailing variable removed. Examples:
   - `/best-project-management-software/` and `/best-free-project-management-software/` share stem `/best-*-project-management-software/`
   - `/software/asana/` and `/software/monday/` share stem `/software/*`
5. Identify clusters where 2+ URLs share a path stem. Sort clusters by total clicks (highest impact first).
6. Read the Queries tab. Note the top 20 queries by clicks for context — these are the queries the site as a whole is competing for.

**Output:** Internal URL cluster map: `{path_stem: [URLs in cluster, total clicks]}` plus site-wide top queries.

**Decision gate:**
- If 0 URL pattern clusters detected → site may not have URL-pattern cannibalization, but money page deep dive may still reveal query-level issues. Proceed to Step 3 with a note.
- If 10+ clusters detected → flag as "site-wide cannibalization pattern" — likely a structural strategy issue. Continue but note this in the final output.
- If Pages tab has fewer than 10 rows → the site may be too small for meaningful pattern analysis. Note and continue.

---

### STEP 3: Identify money pages

Money pages anchor the audit priority.

**Input:** Site URL + URL cluster map from Step 2.

**Process:**
1. If user supplied money pages in the initial input, skip to confirmation in step 4.
2. Use `web_fetch` to load the site's homepage.
3. Extract main navigation links and footer links from the HTML.
4. Filter to URLs on the same domain. Exclude obvious non-money paths: `/blog/*`, `/about`, `/contact`, `/login`, `/signup`, `/privacy`, `/terms`, `/careers`, `/help`, `/support`, `/docs/*` (unless docs IS the product).
5. Categorize candidates by inferred type: feature page, product/service page, category page, listicle/review page, pricing page.
6. Cross-reference with the URL cluster map: flag any candidate that sits inside a cluster identified in Step 2.
7. Present the candidate list to the user. For each candidate flagged in a cluster, note "this page is in a cluster with N other URLs — likely high cannibalization risk."
8. Ask user to confirm, remove, or add money pages.

**Output:** Confirmed money page list, with cluster membership noted.

**Decision gate:**
- If user confirms 3+ money pages → proceed to Step 4.
- If site has no clear money pages in nav → ask user to manually identify 3-5 URLs that drive revenue or capture leads.
- If money pages are flagged across many clusters → prioritize the money pages in the largest clusters first.

---

### STEP 4: Request per-money-page exports

Each money page needs its own filtered export to reveal its top queries.

**Input:** Confirmed money pages from Step 3.

**Process:**
1. For each money page, instruct the user:
   ```
   1. In GSC, click "+ NEW" filter → "Page" → "URL is exactly" → paste [money page URL]
   2. Confirm the Pages tab will show exactly that one URL
   3. Click EXPORT → Download Excel
   4. Upload here, named after the page (e.g., money-page-1-best-pm-software.xlsx)
   ```
2. Front-load all instructions at once — give the user the full list of pages they need to export and ask them to upload all files together.
3. Wait for uploads.
4. As each file arrives, validate:
   - Filters tab shows Page filter applied
   - Pages tab has exactly 1 row matching the filtered URL
   - Date range matches the site-wide export
5. Read the Queries tab from each. Extract top 3 queries by clicks.

**Output:** Per money page: `{money_page_url, top_3_queries: [{query, clicks, impressions, position}]}`.

**Decision gate:**
- If a money page returns fewer than 3 queries with meaningful clicks (under 10 each) → flag as low-signal in output, audit it but lower confidence on findings.
- If validation fails on any upload → tell user which file is wrong and how to re-export.
- If user uploads files for only some money pages → audit what's available, note skipped pages in output.

---

### STEP 5: Request per-query exports (suspect discovery)

For each top query across all money pages, find every page on the site competing for it.

**Input:** Top queries from Step 4 (deduplicated across money pages).

**Process:**
1. Build the deduplicated query list. If two money pages share a top query, that's already a strong cannibalization signal — flag it.
2. Cap the query list at 12 to keep the upload burden reasonable. If more than 12 unique top queries exist, prioritize by total clicks across money pages.
3. Instruct the user:
   ```
   For each query below, do this in GSC:
   1. Click "+ NEW" filter → "Query" → "Query is exactly" → paste the query
   2. Click EXPORT → Download Excel
   3. Name the file after the query (e.g., query-best-pm-software.xlsx)

   Queries to export:
   1. [query 1]
   2. [query 2]
   ...
   ```
4. Wait for uploads.
5. For each file, validate:
   - Filters tab shows Query filter applied with exact query
6. Read the Pages tab from each. Every URL with impressions on that query is a potential suspect.
7. Aggregate: build the suspect map `{money_page → [suspects with shared queries and metrics]}`.
8. Score severity per suspect on each shared query:
   - HIGH: suspect has >100 impressions or >10 clicks on the query
   - MEDIUM: suspect has 20–100 impressions
   - LOW: suspect has under 20 impressions (early warning)
9. A suspect appearing on multiple top queries from the same money page gets escalated severity.

**Output:** Suspect map per money page with severity scoring.

**Decision gate:**
- If a money page has no suspects across any of its top queries → record "no cannibalization detected" and skip Step 6 for that money page.
- If a suspect appears across 3+ money pages → flag as "site-wide cannibalization pattern."
- If query-filtered export shows only the money page itself (no other pages with impressions) → that query is clean, no cannibalization on it.

---

### STEP 6: Request per-suspect exports (deep dive)

Each suspect gets the same depth of analysis as the money page. This reveals whether the suspect has independent demand or is a parasitic variant.

**Input:** Deduplicated suspect list from Step 5.

**Process:**
1. Cap suspect deep-dives at 8 to keep analysis manageable. If more suspects exist, prioritize by aggregated severity (HIGH first, most money pages affected first).
2. Instruct the user to export each suspect using the same Page filter pattern from Step 4. Front-load all instructions.
3. Wait for uploads.
4. Validate each file (Page filter, exactly 1 row in Pages tab).
5. Read each suspect's top 3 queries by clicks.
6. Compare suspect's top 3 to the money page's top 3:
   - 2+ queries overlap → high overlap, strong cannibalization signal
   - 1 query overlaps → medium overlap, partial independent demand
   - 0 overlap (suspect ranks for queries the money page doesn't) → suspect may serve distinct intent — bias toward leaving alone, but still SERP-check
7. Identify each suspect's **top query** (highest click count) — this is the query Step 7 SERP-checks.

**Output:** Per suspect: `{suspect_url, top_3_queries, overlap_with_money_page, query_for_serp_check}`.

**Decision gate:**
- If a suspect has no GSC data (new page, deindexed, blocked) → flag as "low confidence — no query data on suspect" and skip SERP check.
- If overlap is 0 AND suspect has >100 clicks on its own top query → mark as "likely distinct intent, verify before flagging" but still SERP-check.

---

### STEP 7: SERP-check each suspect's top query

The SERP itself is the verdict. It reveals whether the search engine treats the query as deserving a separate page or as a sub-topic of the parent money page.

**Input:** Each suspect's top query from Step 6.

**Process:**
1. For each suspect's top query, use `web_search` to retrieve the top 10 organic results.
2. For each result, use `web_fetch` to identify page type from title, H1, and intro paragraph. Classify as:
   - Dedicated page (a page focused on this specific query)
   - Parent listicle (a broader category page that handles this as a sub-section)
   - Blog post / guide
   - Directory / aggregator
3. Classify the SERP overall:
   - **Dedicated sub-topic SERP** — most top results are dedicated pages on the suspect's specific query. The suspect page is justified. Flag as "intent justifies separate page."
   - **Parent-page SERP** — most top results are parent listicle/category pages handling the suspect's query inline. Strong signal the suspect should fold into the money page. Flag as "SERP indicates consolidation."
   - **Mixed SERP** — roughly even split. Flag as "SERP mixed — manual review required."
4. Assign first-pass confidence per suspect:
   - **HIGH consolidation:** GSC overlap ≥ 2/3 AND parent-page SERP
   - **MEDIUM consolidation:** GSC overlap ≥ 1/3 AND parent-page SERP, OR overlap ≥ 2/3 AND mixed SERP
   - **LOW consolidation:** weaker signal but some evidence
   - **DO NOT CONSOLIDATE:** dedicated sub-topic SERP regardless of GSC overlap

**Output:** Per suspect: `{serp_classification, top_3_serp_examples, confidence}`.

**Decision gate:**
- If `web_search` or `web_fetch` is unavailable → mark every suspect "GSC evidence only — manual SERP check required" and produce output without SERP layer.
- If SERP returns mostly forum/Reddit results → flag as "non-commercial SERP, may not need consolidation."
- If multiple `web_fetch` calls fail (>50%) → note SERP analysis is partial in output.

---

### STEP 8: Build the consolidation playbook

Assemble the final output. One section per money page. Suspects sorted by confidence within each section.

**Input:** All findings from Steps 1–7.

**Process:**
1. Write summary header with site URL, date range, money pages audited, suspect count by confidence level.
2. Note any URL pattern clusters detected in Step 2 that the audit covered (and any that were skipped).
3. For each money page, write a section using the Output Format template.
4. Within each money page section, sort suspects: HIGH → MEDIUM → LOW → DO NOT CONSOLIDATE.
5. For each suspect, include GSC evidence, SERP evidence, first-pass confidence, and explicit verification steps.
6. Add closing notes that flag this as evidence and recommendations, not a verdict.

**Output:** Full markdown playbook per Output Format below.

---

## Output Format

ALWAYS use this exact template:

```markdown
# Champion Page Consolidation Audit: [Site URL]

**Date range analyzed:** [from Filters tab — e.g., "Last 12 months"]
**Money pages audited:** [N]
**Suspects identified:** [N total — X HIGH, Y MEDIUM, Z LOW, W DO NOT CONSOLIDATE]
**URL pattern clusters detected:** [N]

---

## Summary

[2–3 sentences: where the biggest cannibalization risks are, the pattern across the site, the most urgent money page to address.]

[If site-wide pattern detected: "This site shows structural cannibalization — [N] URL clusters were identified beyond the audited money pages. Consider a content strategy review beyond individual page consolidations."]

---

## Money Page: [URL]

**Top queries (last [date range]):**
- [query 1] — [clicks] clicks, position [X]
- [query 2] — [clicks] clicks, position [X]
- [query 3] — [clicks] clicks, position [X]

**Cannibalization status:** [N suspects identified / no cannibalization detected]

---

### Suspect: [URL] — Confidence: [HIGH / MEDIUM / LOW / DO NOT CONSOLIDATE]

**GSC evidence:**
- Shared queries with money page: [N of 3]
- Shared query examples: [list with click counts on suspect]
- Suspect's top 3 queries: [list with click counts]

**SERP evidence (query: "[suspect top query]"):**
- SERP classification: [Dedicated sub-topic / Parent-page / Mixed / Non-commercial]
- Top 3 results page types: [brief description of each]

**First-pass call:** [HIGH/MEDIUM/LOW indication of cannibalization with reasoning, or "intent justifies separate page"]

**Verify before acting:**
1. [Specific manual check the user should run]
2. [Second check if needed]

---

[Repeat suspect block for each suspect under this money page]

---

## Money Page: [Next URL]

[Repeat]

---

## Closing Notes

This audit surfaces evidence and first-pass calls. It does not redirect anything automatically. Before redirecting any page:
- Confirm the suspect doesn't serve a meaningfully different audience or intent
- Check the suspect for backlinks worth preserving
- Plan the redirect target carefully — the URL receiving the redirect should be the money page, and internal links to the redirected URL should be updated where practical
```

**Formatting rules:**
- One H2 per money page. Suspects under each money page are H3.
- No tables for suspects — section structure is the readable form.
- "Verify before acting" is always present, never skipped, even on HIGH confidence.
- If a money page has zero suspects, render the section with "Cannibalization status: no cannibalization detected" and no suspect blocks.
- Closing notes block is fixed text — do not modify per audit.

---

## Edge Cases & Judgment Calls

**When the input is incomplete (no GSC and no Ahrefs/SEMrush):**
Halt at Step 1. Tell the user GSC is the required minimum data source. Link to https://search.google.com/search-console/about and offer to resume the audit when they have it set up.

**When two classifications seem equally valid (suspect has both partial query overlap and dedicated-intent SERP):**
Default to "DO NOT CONSOLIDATE" with a note explaining the tension. False positives that destroy traffic are worse than false negatives leaving a small consolidation opportunity on the table.

**When the output would be unusually large (10+ money pages, 50+ suspects):**
Cap output at the top 5 money pages by total click volume. List remaining money pages with suspect counts only ("Money page X: 4 suspects identified — full analysis omitted, run a focused audit on this page next"). Never truncate suspect details for a money page that is included.

**When a tool call returns unexpected results (uploaded file isn't a valid GSC export):**
Confirm the file came from the GSC EXPORT button and was downloaded as Excel (not CSV — CSV exports lose the multi-tab structure the skill needs). If the file is missing the Filters tab entirely, the export is malformed — ask user to re-export.

**When the suspect outperforms the money page on the shared query:**
The "money page" framing may be wrong — the suspect might be the de facto champion. Flag this explicitly: "Suspect outperforms money page on this query — verify whether the suspect should be the champion instead." Do not auto-recommend redirecting the higher-performing page into the lower-performing one.

**When the user provides Ahrefs or SEMrush data instead of GSC:**
Accept as a fallback. Adapt instructions: ask for a Top Pages export and a Top Keywords export at the domain level, then per-page Organic Keywords exports. The workflow stays the same, only the data source changes. Note in the output that analysis used third-party data, not first-party GSC, which may show different rankings.

**When the date range is shorter than 12 months:**
Warn at Step 2. Proceed but note in the final output: "Analysis based on [actual range] — recommendations may be weaker than a 12-month view." Don't refuse the audit.

**When the SERP check returns geographically inconsistent results:**
Note that the SERP was checked in the agent's default locale. If the site targets a specific country, recommend re-running the SERP check from that location for any HIGH confidence flag before redirecting.

**When a query-filtered export reveals 10+ pages competing for the same query:**
Flag as a structural problem. The fix is not consolidating each page individually — it's a strategy review. Note in output that this query has site-wide spread and needs a unified approach.

---

## What This Skill Does NOT Do

- Does NOT execute redirects. Produces evidence and recommendations only.
- Does NOT include on-page optimization for the surviving champion (e.g., outlink strategy, internal linking, content updates). That's downstream work covered in Omnipresence methodology.
- Does NOT detect cannibalization between non-money pages. Two competing blog posts that don't bleed a money page are out of scope.
- Does NOT analyze backlink profiles. The user must check backlinks before redirecting any page with significant link equity.
- Does NOT replace human judgment on intent. The SERP check is a first-pass call, not a verdict.
- Does NOT pull GSC data automatically. The user runs every export — the skill walks them through it.
- If the user asks for a full content strategy or topical map, suggest the `query-deserves-page` or `content-funnel-architect` skills instead.
- If the user asks how to optimize the surviving champion page after consolidation, point them to AI SEO Operators (free) or Omnipresence (premium) — the post-consolidation methodology is not encoded in this skill.

---

## Examples

### Example 1: Happy path — clear cannibalization on an affiliate site

**Input:**
- Site: `https://example.com` (project management software affiliate)
- User confirms money pages: `/best-project-management-software/`, `/best-crm-software/`, `/best-time-tracking-software/`

**Process abbreviated:**
- Site-wide export reveals URL clusters: `/best-*-project-management-software/` cluster has 6 URLs
- Money page `/best-project-management-software/` top queries: "best project management software" (3,420 clicks), "project management software" (1,840), "project management tools" (920)
- Query-filtered export on "best project management software" returns money page AND `/best-free-project-management-software/` (340 impressions) and `/best-construction-project-management-software/` (180 impressions)
- Suspect `/best-free-project-management-software/` top queries: "best free project management software" (220), "free project management software" (110), "best project management software" (45) — overlap 1/3
- SERP check on "best free project management software": 8/10 results are parent listicle pages handling free options inline, not dedicated free-only pages

**Output (abbreviated):**

```markdown
### Suspect: /best-free-project-management-software/ — Confidence: HIGH

**GSC evidence:**
- Shared queries with money page: 1 of 3 (suspect ranks for "best project management software" with 45 clicks)
- Suspect's top 3 queries: "best free project management software" (220), "free project management software" (110), "best project management software" (45)

**SERP evidence (query: "best free project management software"):**
- SERP classification: Parent-page SERP
- Top 3 results page types: parent listicle handling free inline, parent listicle handling free inline, dedicated free-only page

**First-pass call:** HIGH indication of cannibalization. The SERP rewards parent listicles, not dedicated "free" pages.

**Verify before acting:**
1. Confirm the suspect page has no significant backlink profile worth preserving
2. Verify the money page covers free options (or plan to add coverage before redirecting)
```

**Why this is correct:** The skill cited GSC evidence (overlap), ran the SERP check, and made a first-pass call without claiming verdict. The verification steps protect the user from acting blindly.

---

### Example 2: Edge case — suspect outperforms money page

**Input:**
- Site: `https://example.com` (B2B SaaS)
- User confirms money page: `/features/integrations/` (intended pillar page)

**Process abbreviated:**
- Money page `/features/integrations/` top query: "saas integrations" — 80 clicks, position 14
- Query-filtered export on "saas integrations" returns money page (80 clicks) AND `/blog/integrations-guide/` (640 clicks, position 4)

**Output:**

```markdown
### Suspect: /blog/integrations-guide/ — Confidence: DO NOT CONSOLIDATE

**GSC evidence:**
- Shared queries with money page: 3 of 3
- Suspect's top 3 queries: "saas integrations" (640), "integration platform" (180), "best saas integrations" (90)

**SERP evidence (query: "saas integrations"):**
- SERP classification: Mixed (40% blog/guide content, 40% product feature pages, 20% directory listings)

**First-pass call:** Suspect outperforms intended money page on the same queries. The "money page" framing may be wrong — the blog post is the de facto champion. Verify whether the blog post should be the champion instead, or whether the feature page needs significant rework before any consolidation.

**Verify before acting:**
1. Compare on-page intent: does the blog post serve top-of-funnel research and the feature page serve buying intent? If yes, both can coexist with proper internal linking.
2. If both pages target the same intent, consider redirecting the feature page into the blog post — not the other way around.
3. Review whether the feature page needs a different positioning entirely.
```

**Why this is correct:** The skill caught the inversion — the assumed money page is being outranked by a blog post on the same queries. Auto-redirecting the higher-performing page into the lower-performing one would have destroyed traffic. The skill flags this and refuses to make a confident call.
