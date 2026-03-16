---
name: cms-shopify
version: "1.0"
description: >
  Publish HTML content to Shopify as blog articles or pages via the Admin REST API.
  Use this skill when the destination CMS is Shopify, when publishing SEO content to a
  Shopify store, or when managing blog articles and pages on Shopify programmatically.
  Always trigger when the user mentions Shopify publishing, Shopify blog, or Shopify pages.

inputs:
  required:
    - type: text
      label: "shopify-store-url"
      description: "Shopify store URL in the format https://your-store.myshopify.com"
    - type: text
      label: "shopify-access-token"
      description: "Admin API access token from a Shopify Custom App with write_content scope"
  optional:
    - type: text
      label: "html-content"
      description: "HTML body to publish (from Google Docs export, AI SEO Engine, or raw HTML)"
    - type: text
      label: "blog-id"
      description: "Numeric blog ID to publish articles to (discover via list blogs step)"
    - type: json
      label: "seo-metadata"
      description: "Object with title_tag and description_tag for SEO metafields"
    - type: text
      label: "featured-image-url"
      description: "Public URL for the article featured image"

outputs:
  - type: json
    label: "published-resource"
    description: "Shopify article or page object with id, handle, and full public URL"

tools_used: [curl, jq]
chains_from: [ai-seo-engine]
chains_to: []
tags: [cms, shopify, publishing, seo, ecommerce]
---

# Shopify Publishing

## What This Skill Does

Publishes HTML content to a Shopify store as blog articles or static pages, with SEO metafields and optional featured images. It handles authentication, blog discovery, article/page creation and updates, image uploads, and rate limit management.

## Context the Agent Needs

- Shopify REST Admin API uses version-dated endpoints (use `2024-01` as the stable version).
- Authentication is a single header: `X-Shopify-Access-Token: TOKEN` -- no OAuth flow needed for Custom Apps.
- Blog articles live under a specific blog ID; a store can have multiple blogs. Pages are top-level and have no parent blog.
- SEO title and meta description are set via metafields with namespace `global` and keys `title_tag` / `description_tag`, not via dedicated fields.
- Rate limit is 2 requests per second using a leaky bucket algorithm. The `X-Shopify-Shop-Api-Call-Limit` header (e.g., `2/40`) shows current usage. Slow down when the numerator approaches the denominator.
- Tags in Shopify are a single comma-separated string, not a JSON array.

## Workflow Steps

### STEP 1: Validate Credentials

Confirm the access token and store URL are valid before attempting any writes.

**Input:** `shopify-store-url`, `shopify-access-token`
**Process:**
1. Run the auth test request:
   ```bash
   curl -s "https://YOUR-STORE.myshopify.com/admin/api/2024-01/shop.json" \
     -H "X-Shopify-Access-Token: YOUR_TOKEN" | jq '.shop.name'
   ```
2. Confirm the response returns a shop name (not an error object).
**Output:** Confirmed store name and valid credentials.
**Decision gate:**
- If shop name is returned -> proceed to Step 2
- If 401/403 error -> stop and report: token is invalid or missing `write_content` scope
- If connection error -> stop and report: store URL is incorrect

### STEP 2: Determine Content Type

Decide whether to create a blog article or a page based on the content and user intent.

**Input:** User request, content metadata
**Process:**
1. If user specifies "page" or content is a landing page / about page / policy -> target is a Page.
2. If user specifies "blog post" or "article", or content has a date/author -> target is a Blog Article.
3. If ambiguous, default to Blog Article (most common SEO publishing target).
**Output:** Decision: `article` or `page`.
**Decision gate:**
- If `article` -> proceed to Step 3
- If `page` -> skip to Step 4

### STEP 3: Discover Blog ID

Retrieve the target blog ID. Required for article creation.

**Input:** `shopify-store-url`, `shopify-access-token`, optional `blog-id`
**Process:**
1. If `blog-id` is already provided, use it directly.
2. Otherwise, list all blogs:
   ```bash
   curl -s "https://YOUR-STORE.myshopify.com/admin/api/2024-01/blogs.json" \
     -H "X-Shopify-Access-Token: YOUR_TOKEN" | jq '.blogs[] | {id, title, handle}'
   ```
3. If the user named a specific blog, match by title or handle.
4. If only one blog exists, use it. If multiple exist and none specified, ask the user.
**Output:** Numeric `blog-id` to target.
**Decision gate:**
- If blog ID resolved -> proceed to Step 4
- If no blogs exist -> stop and report: store has no blogs configured
- If multiple blogs and no match -> ask user which blog to target

### STEP 4: Prepare Payload

Build the JSON payload for the article or page.

**Input:** `html-content`, `seo-metadata`, `featured-image-url`, content type decision
**Process:**
1. Build the base object with `title`, `body_html`, `published: true`.
2. If SEO metadata is provided, add metafields array:
   ```json
   "metafields": [
     {
       "namespace": "global",
       "key": "title_tag",
       "value": "SEO Title Here",
       "type": "single_line_text_field"
     },
     {
       "namespace": "global",
       "key": "description_tag",
       "value": "Meta description here",
       "type": "single_line_text_field"
     }
   ]
   ```
3. For articles: add `author`, `tags` (comma-separated string), and `summary_html` if excerpt is available.
4. For articles with a featured image: add `"image": {"src": "https://cdn.com/image.jpg"}` to the article object.
5. For scheduled publishing: set `published_at` to an ISO 8601 datetime (e.g., `"2026-04-01T09:00:00-05:00"`).
6. For custom URL slugs: set `handle` to the desired slug.
**Output:** Complete JSON payload ready for the API call.
**Decision gate:**
- If payload is valid JSON -> proceed to Step 5
- If required fields are missing (title or body_html) -> stop and ask user for missing content

### STEP 5: Publish to Shopify

Send the create or update request to the Shopify Admin API.

**Input:** JSON payload, `blog-id` (for articles), content type
**Process:**
1. For a **new article**:
   ```bash
   curl -s -X POST \
     "https://YOUR-STORE.myshopify.com/admin/api/2024-01/blogs/BLOG_ID/articles.json" \
     -H "X-Shopify-Access-Token: YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"article": { ...payload... }}'
   ```
2. For a **new page**:
   ```bash
   curl -s -X POST \
     "https://YOUR-STORE.myshopify.com/admin/api/2024-01/pages.json" \
     -H "X-Shopify-Access-Token: YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"page": { ...payload... }}'
   ```
3. For an **update to an existing article**:
   ```bash
   curl -s -X PUT \
     "https://YOUR-STORE.myshopify.com/admin/api/2024-01/blogs/BLOG_ID/articles/ARTICLE_ID.json" \
     -H "X-Shopify-Access-Token: YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"article": { ...payload... }}'
   ```
4. For an **update to an existing page**:
   ```bash
   curl -s -X PUT \
     "https://YOUR-STORE.myshopify.com/admin/api/2024-01/pages/PAGE_ID.json" \
     -H "X-Shopify-Access-Token: YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"page": { ...payload... }}'
   ```
5. Check the `X-Shopify-Shop-Api-Call-Limit` header. If approaching the limit, add a 500ms delay before the next request.
6. Parse the response to extract the created/updated resource ID and handle.
**Output:** Shopify API response with resource ID, handle, and confirmation of publish status.
**Decision gate:**
- If 201 Created or 200 OK -> proceed to Step 6
- If 422 Unprocessable Entity -> inspect `errors` object, fix payload, and retry once
- If 429 Too Many Requests -> wait 1 second and retry
- If 401/403 -> stop and report credentials or scope issue

### STEP 6: Upload Image to Shopify Files (Optional)

Upload an image to Shopify's file storage via GraphQL when needed for non-article images.

**Input:** Image URL to upload
**Process:**
1. Send the GraphQL mutation:
   ```bash
   curl -s -X POST \
     "https://YOUR-STORE.myshopify.com/admin/api/2024-01/graphql.json" \
     -H "X-Shopify-Access-Token: YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "mutation fileCreate($files: [FileCreateInput!]!) { fileCreate(files: $files) { files { alt url } userErrors { field message } } }",
       "variables": {
         "files": [{
           "alt": "Image description",
           "contentType": "IMAGE",
           "originalSource": "https://cdn.com/image.jpg"
         }]
       }
     }'
   ```
2. Check `userErrors` for failures.
3. Extract the Shopify-hosted URL from the response.
**Output:** Shopify CDN URL for the uploaded image.
**Decision gate:**
- If `userErrors` is empty -> use the returned URL
- If `userErrors` present -> report the error; fall back to inline `<img>` with the original URL

### STEP 7: Verify and Report

Confirm the publish was successful and provide the public URL.

**Input:** API response from Step 5
**Process:**
1. Extract the resource `id` and `handle` from the response.
2. Construct the public URL:
   - Articles: `https://your-store.myshopify.com/blogs/BLOG_HANDLE/ARTICLE_HANDLE`
   - Pages: `https://your-store.myshopify.com/pages/PAGE_HANDLE`
3. Report the result in the output format below.
**Output:** Structured confirmation with ID, handle, URL, and publish status.
**Decision gate:**
- If URL is accessible -> done
- If custom domain is configured -> note that the `.myshopify.com` URL redirects to the custom domain

## Output Format

```
SHOPIFY PUBLISH RESULT
======================
Status:    [Created | Updated]
Type:      [Article | Page]
ID:        [numeric ID]
Handle:    [url-slug]
Blog:      [blog title] (articles only)
URL:       https://your-store.myshopify.com/[blogs/handle/article-handle | pages/page-handle]
SEO Title: [title_tag value or "not set"]
SEO Desc:  [description_tag value or "not set"]
Image:     [featured image URL or "none"]
Published: [true | false | scheduled for YYYY-MM-DD]
```

## Edge Cases & Judgment Calls

1. **Missing HTML content:** If only a title is provided with no body, create the resource with an empty `body_html` and warn the user that the published page/article has no content. Do not refuse to publish.

2. **Blog does not exist:** If the user references a blog by name that does not exist, list available blogs and ask for clarification. Do not create a new blog -- that requires separate store configuration.

3. **Rate limit hit during bulk publishing:** When publishing multiple articles in sequence, check `X-Shopify-Shop-Api-Call-Limit` after each request. If the numerator exceeds 75% of the denominator (e.g., 30/40), insert a 1-second delay before the next call. If a 429 response is received, wait 2 seconds and retry.

4. **Duplicate article title:** Shopify allows duplicate titles (it auto-generates unique handles). Warn the user if an article with the same title already exists in the target blog, but proceed with creation unless explicitly told to update instead.

5. **Image URL is not publicly accessible:** If the featured image `src` returns a non-200 status, Shopify will silently ignore it. Warn the user that the image may not appear. Suggest uploading to Shopify Files via GraphQL as a fallback.

6. **Metafields on update:** When updating an existing article or page, metafields must be sent with their existing `id` to update them, or omitted entirely to leave them unchanged. Sending metafields without an `id` on an update creates duplicates. If updating, first GET the resource to retrieve existing metafield IDs.

7. **HTML contains inline styles or scripts:** Shopify strips `<script>` tags and certain inline styles from `body_html`. Do not attempt to include JavaScript. Warn the user if the HTML contains scripts that will be stripped.

8. **Large body_html (over 512KB):** Shopify has undocumented size limits on `body_html`. If the content is very large, warn the user and suggest breaking it into multiple pages or trimming.

## What This Skill Does NOT Do

- **Create or configure Shopify Custom Apps** -- the user must create the app and provide the access token.
- **Manage Shopify products, collections, or inventory** -- this skill is limited to content publishing (articles and pages).
- **Create new blogs** -- only publishes to existing blogs. Blog creation is a store administration task.
- **Handle Shopify theme/template editing** -- no Liquid template modifications.
- **Manage redirects or URL routing** -- use Shopify admin for URL redirects.
- **Generate content** -- this skill publishes content; use the `ai-seo-engine` skill to generate it.
- **Manage Shopify webhooks or app subscriptions** -- out of scope.

## Recipes

### List Existing Articles

```bash
# Count articles in a blog
curl -s "https://YOUR-STORE.myshopify.com/admin/api/2024-01/blogs/BLOG_ID/articles/count.json" \
  -H "X-Shopify-Access-Token: YOUR_TOKEN" | jq '.count'

# List articles (paginated, 50 per page)
curl -s "https://YOUR-STORE.myshopify.com/admin/api/2024-01/blogs/BLOG_ID/articles.json?limit=50" \
  -H "X-Shopify-Access-Token: YOUR_TOKEN" | jq '.articles[] | {id, title, handle, published_at}'
```

### Delete an Article

```bash
curl -s -X DELETE \
  "https://YOUR-STORE.myshopify.com/admin/api/2024-01/blogs/BLOG_ID/articles/ARTICLE_ID.json" \
  -H "X-Shopify-Access-Token: YOUR_TOKEN"
```

### Schedule a Future Publish

Set `published_at` to a future ISO 8601 datetime and `published` to `true`:
```json
{
  "article": {
    "title": "Scheduled Post",
    "body_html": "<p>Content here</p>",
    "published": true,
    "published_at": "2026-04-01T09:00:00-05:00"
  }
}
```

### Set a Custom URL Slug

Use the `handle` field to control the URL path:
```json
{
  "article": {
    "title": "My Article Title",
    "handle": "custom-url-slug",
    "body_html": "<p>Content</p>"
  }
}
```

## Examples

### Example 1: Happy Path -- Publish a Blog Article with SEO Metadata

**Scenario:** User has HTML content from AI SEO Engine and wants to publish it to their Shopify blog.

**Inputs provided:**
- Store URL: `https://acme-store.myshopify.com`
- Access token: `shpat_xxxxx`
- HTML content: `<h2>Best Running Shoes 2026</h2><p>Our top picks...</p>`
- SEO title: `Best Running Shoes 2026 | Acme Store`
- SEO description: `Discover the top running shoes for 2026 with expert reviews and comparisons.`
- Featured image: `https://cdn.example.com/running-shoes.jpg`

**Agent execution:**
1. Validates credentials -- `shop.name` returns "Acme Store".
2. Content type: article (blog post with SEO intent).
3. Lists blogs -- finds one blog: `{id: 82471234, title: "News", handle: "news"}`.
4. Builds payload with title, body_html, metafields for SEO, featured image, and tags.
5. POSTs to `/admin/api/2024-01/blogs/82471234/articles.json`.
6. Gets 201 response with `{id: 991234567, handle: "best-running-shoes-2026"}`.

**Output:**
```
SHOPIFY PUBLISH RESULT
======================
Status:    Created
Type:      Article
ID:        991234567
Handle:    best-running-shoes-2026
Blog:      News
URL:       https://acme-store.myshopify.com/blogs/news/best-running-shoes-2026
SEO Title: Best Running Shoes 2026 | Acme Store
SEO Desc:  Discover the top running shoes for 2026 with expert reviews and comparisons.
Image:     https://cdn.example.com/running-shoes.jpg
Published: true
```

### Example 2: Edge Case -- Multiple Blogs, No Blog Specified

**Scenario:** User says "publish this article to Shopify" but the store has 3 blogs.

**Inputs provided:**
- Store URL: `https://acme-store.myshopify.com`
- Access token: `shpat_xxxxx`
- HTML content: `<p>Article body</p>`
- No blog ID or blog name specified

**Agent execution:**
1. Validates credentials -- success.
2. Content type: article.
3. Lists blogs -- finds three:
   ```
   {id: 82471234, title: "News", handle: "news"}
   {id: 82471235, title: "Guides", handle: "guides"}
   {id: 82471236, title: "Updates", handle: "updates"}
   ```
4. Multiple blogs found and none specified -- **stops and asks the user:**

   > "Your store has 3 blogs: **News**, **Guides**, and **Updates**. Which blog should I publish this article to?"

5. User responds "Guides".
6. Proceeds with blog ID `82471235` and completes the publish.

**Judgment call:** The agent does not guess or default to the first blog when multiple exist. Picking the wrong blog means the article shows up in the wrong section of the store. Always ask.

### Example 3: Edge Case -- Publishing a Static Page

**Scenario:** User wants to publish an "About Us" page to Shopify, not a blog article.

**Inputs provided:**
- Store URL: `https://acme-store.myshopify.com`
- Access token: `shpat_xxxxx`
- HTML content: `<h1>About Acme</h1><p>Founded in 2020...</p>`
- Title: "About Us"

**Agent execution:**
1. Validates credentials -- success.
2. Content type: **page** (user said "page" and content is an about page).
3. Skips blog discovery (pages have no parent blog).
4. Builds payload with title and body_html.
5. POSTs to `/admin/api/2024-01/pages.json`.
6. Gets 201 response with `{id: 112345, handle: "about-us"}`.

**Output:**
```
SHOPIFY PUBLISH RESULT
======================
Status:    Created
Type:      Page
ID:        112345
Handle:    about-us
Blog:      n/a
URL:       https://acme-store.myshopify.com/pages/about-us
SEO Title: not set
SEO Desc:  not set
Image:     none
Published: true
```

**Judgment call:** No SEO metafields were provided, so the agent publishes without them and notes "not set" in the output rather than fabricating metadata.
