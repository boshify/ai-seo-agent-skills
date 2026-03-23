---
name: page-scraper
version: "1.0"
description: >
  Extract text, metadata, and structured data from web pages using the hosted page scraper API.
  Use this skill whenever scraping web pages, extracting content from URLs, reading articles,
  parsing sitemaps, analyzing on-page SEO elements, or when the user mentions page scraping,
  web scraping, or content extraction. Falls back to Jina Reader when primary scraping fails.

inputs:
  required:
    - type: text
      label: "url"
      description: "Target page URL (must start with http:// or https://)"
  optional:
    - type: number
      label: "max_chars"
      description: "Truncation limit for content fields (default 5000, increase for long-form content)"
    - type: boolean
      label: "return_html"
      description: "Include cleaned HTML in response (default false)"
    - type: boolean
      label: "is_sitemap"
      description: "Sitemap mode — extract URLs from XML sitemaps or HTML pages"
    - type: boolean
      label: "fast_mode"
      description: "Fast mode (default true, ~8s limit). Set false for slow/protected sites (~25s limit)"

outputs:
  - type: markdown
    label: "page-content"
    description: "Extracted page content as structured Markdown with metadata, tables, and schema markup"
  - type: json
    label: "seo-metadata"
    description: "Title, meta description, canonical, robots, h1, lang, and schema markup"
  - type: json
    label: "sitemap-urls"
    description: "List of URLs extracted from sitemap (sitemap mode only)"

tools_used: [curl, jina-reader]
chains_from: [ai-seo-engine]
chains_to: [ai-seo-engine, cms-wordpress, cms-webflow, cms-shopify]
tags: [scraping, content-extraction, seo, research, sitemap]
---

## What This Skill Does

Extracts readable content, SEO metadata, tables, and schema markup from any web page URL using a hosted scraper API. When direct scraping fails, automatically falls back to Jina Reader to maximize extraction success.

## Context the Agent Needs

The page scraper at `https://read.aiseoengine.studio` handles bot protection bypass (Cloudflare, captchas) internally. It also tries Jina Reader as an internal fallback before returning failure — so when you get `ok: false`, both methods have already failed. Only then should you try the external Jina Reader backup described in the reference docs.

For full API details, parameters, rate limiting, and backup options, see [references/reference.md](references/reference.md).

## Workflow Steps

### STEP 1: Determine scraping requirements

Identify what the user needs extracted and configure the request accordingly.

**Input:** User request containing one or more URLs
**Process:**
1. Identify whether the user needs content, SEO metadata, HTML, or sitemap URLs
2. Set `max_chars` based on need: 5000 for summaries, 10000–15000 for full articles, 20000 for comprehensive extraction
3. Set `is_sitemap: true` if the URL points to a sitemap or the user wants URL extraction
4. Set `fast_mode: false` if the site is known to be slow or heavily protected
5. Set `return_html: true` only if the user needs HTML-level analysis
**Output:** Configured request parameters
**Decision gate:**
- If single URL → proceed to Step 2
- If multiple URLs → batch them, proceeding to Step 2 for each

### STEP 2: Scrape the page

Send the request to the page scraper API.

**Input:** URL and configured parameters from Step 1
**Process:**
1. Send `POST https://read.aiseoengine.studio/read` with JSON body containing `url` and any optional parameters
2. Parse the JSON response
3. Check the `ok` field
**Output:** Raw API response
**Decision gate:**
- If `ok: true` → proceed to Step 3
- If `ok: false` → proceed to Step 4 (fallback)

### STEP 3: Extract and present results

Process the successful response into the format the user needs.

**Input:** Successful API response
**Process:**
1. Use `flat_outline` as the primary content (Markdown with headings preserved)
2. Use `outline_sections` when the user needs specific sections extracted
3. Check `tables` array for any structured data (comparisons, pricing, specs)
4. Check `schema_markup` for entity data, FAQs, reviews, products
5. Report SEO metadata: `title`, `meta_description`, `canonical`, `robots`, `h1`, `lang`
6. If `lengths.flat_outline` equals `max_chars`, content was truncated — re-scrape with higher `max_chars` if completeness matters
**Output:** Extracted content in the format the user requested
**Decision gate:**
- If content is complete and user is satisfied → done
- If content was truncated and user needs more → re-scrape with higher `max_chars`

### STEP 4: Handle failure and fallback

When the scraper returns `ok: false`, attempt recovery.

**Input:** Failed API response with `reason` field
**Process:**
1. Check the `reason` field to determine failure type
2. If `TIMEOUT` or `NETWORK` → retry once with `fast_mode: false`
3. If still failing or `BLOCKED` / `EXTRACT_FAIL` / `EMPTY` → try external Jina Reader: `GET https://r.jina.ai/{url}`
4. If Jina Reader also fails → inform the user the page cannot be scraped and suggest alternatives (manual visit, different URL, cached version)
5. If `BANNED` or `GLOBAL_LIMIT` → wait for `retry_after` seconds, then retry
**Output:** Extracted content from fallback, or failure report
**Decision gate:**
- If fallback succeeds → proceed to Step 3 with fallback data
- If all methods fail → report failure with reason and suggestions

## Output Format

### For content extraction:
```
## Page: {title}
**URL:** {url}
**Meta Description:** {meta_description}

{flat_outline content}

### Tables
{tables as markdown, if any}

### Schema Markup
{schema_markup summary, if any}
```

### For SEO analysis:
```
| Element | Value |
|---------|-------|
| Title | {title} |
| Meta Description | {meta_description} |
| H1 | {h1} |
| Canonical | {canonical} |
| Robots | {robots} |
| Language | {lang} |
| Content Length | {length} chars |
```

### For sitemap extraction:
```
Found {n} URLs in sitemap:
1. {url_1}
2. {url_2}
...
```

## Edge Cases & Judgment Calls

**Incomplete input — no URL provided:**
Ask the user for the URL. Do not guess or fabricate URLs.

**Ambiguous request — unclear what to extract:**
Default to content extraction with `max_chars: 5000`. Present `flat_outline` and key SEO metadata. Ask if the user needs more detail.

**Oversized output — very long pages:**
Start with default `max_chars: 5000`. If content appears truncated (check `lengths.flat_outline` vs `max_chars`), offer to re-scrape with higher limit. For multi-page research, summarize each page rather than dumping full content.

**Failed tool call — scraper and fallback both fail:**
Report the failure reason clearly. Suggest: (1) trying a different URL for the same content, (2) checking if the site requires authentication, (3) using a cached version (Google Cache, Wayback Machine). Never fabricate content that wasn't actually scraped.

**Rate limiting — 429 response:**
Respect `retry_after`. If scraping many URLs from the same domain, space requests out and diversify target domains between batches.

**Sitemap with thousands of URLs:**
Present the first 20-30 URLs and report the total count. Ask the user if they want to filter by pattern or see more.

## What This Skill Does NOT Do

- Does not scrape pages that require authentication (login-walled content)
- Does not execute JavaScript in a full browser environment (use Playwright/Puppeteer for SPAs that resist all scraping methods)
- Does not cache or store scraped content between sessions
- Does not modify or publish content — extraction only
- Does not scrape at scale without rate limit awareness (respect the abuse detection thresholds)
- Does not extract content from non-HTML resources (PDFs, images, videos) — only HTML and XML

## Examples

### Example 1: Research a competitor's blog post (happy path)

**User:** "Can you scrape this article and summarize it? https://competitor.com/blog/seo-guide"

**Agent action:**
```json
POST https://read.aiseoengine.studio/read
{"url": "https://competitor.com/blog/seo-guide", "max_chars": 10000}
```

**Response:** `ok: true`, `flat_outline` contains the full article in Markdown.

**Agent output:** Presents the article summary with key headings, extracts any tables (comparison charts, checklists), and notes SEO metadata (title tag, meta description, h1) for competitive analysis.

### Example 2: Scraping a protected site (edge case — fallback chain)

**User:** "Read this page for me: https://heavily-protected-site.com/pricing"

**Agent action:**
1. `POST /read` with default settings → returns `ok: false`, `reason: "BLOCKED"`
2. Retry with `fast_mode: false` → still `ok: false`, `reason: "BLOCKED"`
3. Try Jina Reader: `GET https://r.jina.ai/https://heavily-protected-site.com/pricing` → returns Markdown content

**Agent output:** Presents the content from Jina Reader, noting it was retrieved via fallback. Flags that this site has aggressive bot protection if the user plans to scrape it repeatedly.

### Example 3: Sitemap crawl for content audit

**User:** "Get me all the URLs from this sitemap: https://mysite.com/sitemap.xml"

**Agent action:**
```json
POST https://read.aiseoengine.studio/read
{"url": "https://mysite.com/sitemap.xml", "is_sitemap": true}
```

**Response:** `ok: true`, `urls: [...]` with 247 URLs.

**Agent output:** Reports 247 URLs found, presents the first 25, and asks if the user wants to filter by pattern (e.g., `/blog/`, `/products/`) or proceed to scrape specific pages.
