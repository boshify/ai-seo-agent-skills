# Page Scraper API Reference

**Base URL**: `https://read.aiseoengine.studio`

---

## Endpoint: POST /read

### Request Body (JSON)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | **required** | Target page URL. Must start with `http://` or `https://`. |
| `max_chars` | int | `5000` | Truncation limit applied to `flat_outline`, `html`, `tables[].markdown`, and `tables[].html`. Increase for long-form content (e.g., `15000` for full articles). |
| `return_html` | bool | `false` | When `true`, includes an `html` field in the response. |
| `clean_html` | bool | `true` | When `true` + `return_html: true`: returns stripped HTML (content tags only, no scripts/styles/chrome). When `false`: returns the raw `<body>` HTML. |
| `is_sitemap` | bool | `false` | Sitemap mode — returns only `{"ok": true, "urls": [...]}`. Works with XML sitemaps (`<loc>` elements) and HTML pages (all `<a href>` links). |
| `fast_mode` | bool | `true` | **`true`** (default): ~4s fetch timeout, 1 retry, ~8s hard wall-clock limit. Good for automation/n8n. **`false`**: ~15s fetch timeout, 3 retries, ~25s hard limit. Use for slow or complex sites. |

**Parameter aliases**: `Clean HTML` is accepted for `clean_html`. `Is Sitemap` is accepted for `is_sitemap`.

### Minimal Example

```json
POST https://read.aiseoengine.studio/read
Content-Type: application/json

{
  "url": "https://example.com/article"
}
```

---

## Response Structure

### Success (`ok: true`)

```json
{
  "ok": true,
  "title": "Page Title",
  "meta_description": "Meta description text",
  "url": "https://example.com/article",
  "canonical": "https://example.com/article",
  "robots": null,
  "lang": "en",
  "h1": "Main Heading",
  "length": 3421,
  "lengths": {
    "main_text": 3421,
    "flat_outline": 4102
  },
  "flat_outline": "# Main Heading\n\nFirst paragraph...\n\n## Section Two\n\n...",
  "outline_sections": [
    {
      "title": "Main Heading",
      "level": "H1",
      "paragraphs": ["First paragraph text..."]
    },
    {
      "title": "Section Two",
      "level": "H2",
      "paragraphs": ["Paragraph one.", "Paragraph two."]
    }
  ],
  "tables": [
    {
      "markdown": "| Col 1 | Col 2 |\n|---|---|\n| A | B |",
      "html": "<table><tr><th>Col 1</th>...",
      "caption": "Table caption if present"
    }
  ],
  "schema_markup": ["{\"@type\": \"Article\", ...}"],
  "html": "..."
}
```

**Key fields for agents**:
- **`flat_outline`** — The primary content field. Markdown-formatted readable text with headings preserved. This is what you should use for reading/researching page content.
- **`outline_sections`** — Same content as `flat_outline` but structured as an array of sections, each with `title`, `level` (H1-H6), and `paragraphs` array. Useful for targeted section extraction.
- **`tables`** — Extracted tables as both Markdown and cleaned HTML. Check this when researching data, comparisons, pricing, or specifications.
- **`schema_markup`** — JSON-LD structured data blocks. Useful for extracting entity data, FAQs, reviews, products, etc.
- **`html`** — Only present when `return_html: true`. Cleaned or raw HTML depending on `clean_html`.
- **`length`** / **`lengths`** — Character counts. Use `lengths.flat_outline` to know if content was truncated by `max_chars`.

### Failure (`ok: false`)

```json
{
  "ok": false,
  "reason": "TIMEOUT",
  "message": "Timeout fetching page",
  "http_status": null,
  "url": "https://example.com/slow-page",
  "length": 0
}
```

### Failure Reasons

| Reason | Meaning | Recommended Action |
|--------|---------|-------------------|
| `INPUT` | Missing or invalid URL (not http/https) | Fix the URL and retry |
| `TIMEOUT` | Fetch or processing exceeded time limit | Retry with `fast_mode: false`, or use Jina Reader backup |
| `NETWORK` | Connection failure or non-200 HTTP status | Retry once, then use Jina Reader backup |
| `BLOCKED` | HTTP 401/403/429/451/503 and internal Jina fallback also failed | Use Jina Reader backup directly, or skip this URL |
| `UNSUPPORTED_MIME` | Response was not HTML/XML (e.g., PDF, image) | URL points to a non-HTML resource — handle differently |
| `EXTRACT_FAIL` | Page fetched but no readable content could be extracted | Try with `fast_mode: false` and higher `max_chars`, or use Jina Reader |
| `EMPTY` | Page returned empty or suspiciously short content | Site may require JavaScript rendering — use Jina Reader or browser-based scraper |
| `BANNED` | Rate limited by abuse detection | Wait for `retry_after` seconds, then retry. Diversify target domains. |
| `GLOBAL_LIMIT` | Server-wide rate limit reached | Wait for `retry_after` seconds, then retry |

---

## Rate Limiting (429 responses)

When rate limited, the response includes:
```json
{
  "ok": false,
  "reason": "BANNED",
  "message": "Rate limited: DOMAIN_SCRAPING:example.com",
  "retry_after": 60
}
```

The `Retry-After` header is also set. The abuse detector flags:
- **Domain scraping**: 80%+ of your recent requests target the same domain (20+ hits in 5 minutes)
- **Extreme volume**: 120+ requests per minute from one IP
- **Global limit**: 200+ requests per minute across all callers

Normal research workflows hitting diverse URLs at high throughput are **not** affected.

---

## Sitemap Mode

```json
{
  "url": "https://example.com/sitemap.xml",
  "is_sitemap": true
}
```

Response:
```json
{
  "ok": true,
  "urls": [
    "https://example.com/page-1",
    "https://example.com/page-2"
  ]
}
```

Works with:
- XML sitemaps (parses `<loc>` elements)
- HTML pages (extracts all `<a href>` as absolute URLs)
- Sitemap indexes (returns the child sitemap URLs)

---

## Internal Fallback Behavior

The scraper automatically tries Jina Reader (`r.jina.ai`) internally when:
1. Direct fetch returns no response
2. HTTP status is 401, 403, 429, 451, or 503
3. Soft block detected (Cloudflare challenge, captcha, "enable JavaScript", etc.)
4. HTML body is suspiciously short (< 200 characters)

This means when you get `ok: false`, **both** the direct fetch and the internal Jina fallback have already failed. Only then should you try an external backup.

---

## Backup: Jina Reader (External)

Use when the page scraper returns `ok: false` with TIMEOUT, BLOCKED, NETWORK, EXTRACT_FAIL, or EMPTY.

### Usage

```
GET https://r.jina.ai/{target_url}
```

Example: `GET https://r.jina.ai/https://example.com/article`

### Optional Headers

| Header | Value | Purpose |
|--------|-------|---------|
| `Authorization` | `Bearer {JINA_API_KEY}` | Higher rate limits |
| `X-Return-Format` | `markdown` / `html` / `text` | Response format |

### Optional Query Parameters

- `x-wait-for` — CSS selector to wait for (JS-heavy pages)
- `x-timeout` — Timeout in seconds (default ~30)
- `tokenBudget` — Max tokens in response

### Response Format

Returns plain text or Markdown:
```
title: Article Title
url source: https://example.com/article

markdown content
---
# Article Title
Content here...
```

### Mapping Jina Response to Page Scraper Format

```python
def parse_jina_response(text):
    title, source_url, content = None, None, text
    lines = text.splitlines()
    for line in lines[:10]:
        low = line.lower()
        if low.startswith("title:"):
            title = line.split(":", 1)[1].strip()
        elif "url source" in low or "source url" in low:
            source_url = line.split(":", 1)[1].strip()
    for i, line in enumerate(lines):
        if "markdown content" in line.lower():
            content = "\n".join(lines[i+1:]).strip()
            break
    return {"title": title, "url": source_url, "flat_outline": content}
```

---

## Backup: Other Options

- **Firecrawl** / **ScrapingBee** — Paid APIs with JS rendering. Use when Jina Reader and page scraper both fail on JS-heavy or protected sites.
- **Direct fetch + trafilatura** — Manual HTML fetch + trafilatura extraction for local scripts.
- **Browser automation** (Playwright/Puppeteer) — For sites that require full browser execution or bypass aggressive bot protection.

---

## Recommended Patterns

### For AI Agent Research Workflows (n8n, etc.)

1. Call `POST /read` with default settings (`fast_mode: true`, `max_chars: 5000`)
2. Check `ok` field in response
3. If `ok: true` — use `flat_outline` for content, `tables` for structured data
4. If `ok: false` — route to Jina Reader HTTP Request node as fallback
5. Keep `max_chars` reasonable (5000-10000) to avoid bloating agent context

### For Full Content Extraction

```json
{
  "url": "https://example.com/long-article",
  "max_chars": 20000,
  "fast_mode": false
}
```

### For SEO Analysis

```json
{
  "url": "https://example.com/page",
  "max_chars": 15000,
  "return_html": true,
  "clean_html": true
}
```

Use `title`, `meta_description`, `canonical`, `robots`, `h1`, `lang` for on-page SEO data. Use `schema_markup` for structured data analysis. Use `html` for tag-level inspection.

### For Sitemap Crawling

```json
{
  "url": "https://example.com/sitemap.xml",
  "is_sitemap": true
}
```

Then loop through the returned `urls` array and scrape each page individually.

### For Slow or Protected Sites

```json
{
  "url": "https://heavy-js-site.com/page",
  "fast_mode": false
}
```

This gives ~15s fetch timeout with 3 retries and ~25s hard limit. If this still fails, the site likely requires browser-based scraping (Playwright/Puppeteer).

---

## Common Failure Patterns and Solutions

| Symptom | Likely Cause | Solution |
|---------|-------------|----------|
| TIMEOUT on specific sites | Site is slow or JS-heavy | Set `fast_mode: false` |
| TIMEOUT on all sites | Service under load | Wait and retry; check global rate limit |
| BLOCKED consistently | Site has aggressive bot protection | Use Jina Reader backup; site may not be scrapable |
| EXTRACT_FAIL | Content is dynamically rendered (SPA) | Try `fast_mode: false`; use Jina with `x-wait-for` selector |
| EMPTY response | Page requires cookies/auth | Likely not scrapable without authentication |
| `flat_outline` seems truncated | `max_chars` too low | Increase `max_chars` (check `lengths.flat_outline` vs `max_chars`) |
| 429 rate limited | Abuse detection triggered | Diversify target domains; wait for `retry_after` period |
| Missing tables | Tables outside main content area | Try `return_html: true` with `clean_html: false` for raw body |

---

## What the Scraper Extracts

The scraper focuses content using this priority:
1. `<main>` element (if present)
2. `<article>` element (if present)
3. Element with the most `<p>` descendants (heuristic)

It strips navigation, headers, footers, sidebars, cookie banners, modals, ads, and other chrome. Tables within the content area are extracted separately and returned in both Markdown and HTML format.

Schema markup (JSON-LD `<script type="application/ld+json">`) is extracted from the full page, not just the content area.
