---
name: cms-webflow
version: "1.0"
description: >
  Publish content to Webflow CMS collections via the Webflow v2 API. Use this skill whenever
  the task involves creating, updating, or managing Webflow CMS items programmatically.
  Trigger when the destination is a Webflow site or the user mentions Webflow publishing.

inputs:
  required:
    - type: text
      label: "webflow-api-token"
      description: "Webflow API token (Site Settings > Apps & Integrations)"
    - type: text
      label: "collection-id"
      description: "Target Webflow CMS collection ID"
  optional:
    - type: text
      label: "html-content"
      description: "HTML body content for the CMS item's rich text field"
    - type: text
      label: "seo-metadata"
      description: "SEO title, meta description, and slug for the item"
    - type: text
      label: "site-id"
      description: "Webflow site ID (required only for discovery; not needed if collection-id is known)"

outputs:
  - type: json
    label: "published-item"
    description: "Published Webflow collection item including item ID and live URL"

tools_used: [curl, jq]
chains_from: [ai-seo-engine]
chains_to: []
tags: [cms, webflow, publishing, seo]
---

# Webflow CMS Publishing

## What This Skill Does

Takes HTML content and SEO metadata and publishes it as a live item in a Webflow CMS collection via the v2 API. The agent discovers the collection schema, creates a draft item with the correct field slugs, and explicitly publishes it.

## Context the Agent Needs

- Webflow v2 API base URL is `https://api.webflow.com/v2`. All requests use `Authorization: Bearer TOKEN` and `Content-Type: application/json`.
- Items created via the API are **drafts by default** -- they are not live until an explicit publish call is made.
- Field slugs are **collection-specific** and cannot be guessed. The agent must fetch the collection schema before constructing the fieldData payload.
- Rate limit is **60 requests per minute per site**. Check `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers. Add a 1-second delay between requests during bulk operations.
- Webflow v2 has **no native asset upload**. Images must be hosted on an external CDN (S3, Cloudflare R2, etc.) and referenced by URL.
- Field type mapping: PlainText (string), RichText (HTML string), Image (URL object), DateTime (ISO 8601), Switch (boolean), Option (enum value), Link (URL string).

## Workflow Steps

### STEP 1: Validate Authentication

Confirm the API token works before attempting any data operations.

**Input:** `webflow-api-token`
**Process:**
1. Run: `curl -s -o /dev/null -w "%{http_code}" https://api.webflow.com/v2/sites -H "Authorization: Bearer $TOKEN"`
2. Check HTTP status code.
**Output:** HTTP 200 confirming valid credentials, or an error message.
**Decision gate:**
- If 200 -> proceed to Step 2
- If 401/403 -> stop and report: "Webflow API token is invalid or lacks permissions. Get a new token at Site Settings > Apps & Integrations."

### STEP 2: Discover Site and Collection (if needed)

Resolve human-readable names to IDs when the user provides a site name or collection name instead of IDs.

**Input:** `site-id` (optional), `collection-id` (may need discovery)
**Process:**
1. If `site-id` is missing, list all sites:
   `curl -s https://api.webflow.com/v2/sites -H "Authorization: Bearer $TOKEN" | jq '.sites[] | {id, displayName}'`
2. If `collection-id` is missing, list collections for the site:
   `curl -s https://api.webflow.com/v2/sites/$SITE_ID/collections -H "Authorization: Bearer $TOKEN" | jq '.collections[] | {id, displayName, slug}'`
3. Match the user's target by name or slug.
**Output:** Confirmed `site-id` and `collection-id`.
**Decision gate:**
- If both IDs resolved -> proceed to Step 3
- If no matching collection found -> stop and report available collections, ask user to clarify

### STEP 3: Fetch Collection Schema

Get the exact field slugs and types so the payload can be constructed correctly.

**Input:** `collection-id`
**Process:**
1. Run: `curl -s https://api.webflow.com/v2/collections/$COLLECTION_ID -H "Authorization: Bearer $TOKEN" | jq '.fields[] | {slug, type, isRequired}'`
2. Record all required fields and their types.
3. Map the content inputs to the correct field slugs (e.g., body HTML -> the RichText field slug, SEO title -> the PlainText field for meta-title).
**Output:** Field mapping: `{ content_field: "post-body", title_field: "name", slug_field: "slug", meta_title_field: "meta-title", meta_desc_field: "meta-description", ... }`
**Decision gate:**
- If all required fields can be populated -> proceed to Step 4
- If a required field has no matching input data -> stop and report which required fields are missing

### STEP 4: Create Draft Item

Create the CMS item as a draft using the mapped field slugs.

**Input:** Field mapping from Step 3, content inputs (`html-content`, `seo-metadata`)
**Process:**
1. Construct the JSON payload using the exact field slugs from the schema:
   ```bash
   curl -s -X POST "https://api.webflow.com/v2/collections/$COLLECTION_ID/items" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "fieldData": {
         "name": "Article Title",
         "slug": "article-title",
         "post-body": "<p>HTML content here</p>",
         "meta-title": "SEO Title | Site Name",
         "meta-description": "155 chars max meta description",
         "author": "Author Name",
         "publish-date": "2026-03-16T00:00:00Z"
       }
     }'
   ```
2. Parse the response to extract the `id` of the created item.
3. Check for field validation errors in the response.
**Output:** Draft item ID (e.g., `"id": "64a..."`).
**Decision gate:**
- If item created successfully (HTTP 200/201) -> proceed to Step 5
- If 400 with field errors -> fix the payload based on the error message and retry once
- If 429 rate limited -> wait until `X-RateLimit-Reset` and retry

### STEP 5: Publish Item

Move the draft item to live status on the Webflow site.

**Input:** `collection-id`, item ID from Step 4
**Process:**
1. Run:
   ```bash
   curl -s -X POST "https://api.webflow.com/v2/collections/$COLLECTION_ID/items/publish" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{ "itemIds": ["ITEM_ID"] }'
   ```
2. Confirm the response indicates success.
**Output:** Published item confirmation.
**Decision gate:**
- If publish succeeds -> proceed to Step 6
- If publish fails -> report error; the item remains as a draft and can be retried

### STEP 6: Verify and Report

Confirm the item is live and return the result.

**Input:** Item ID, site display name
**Process:**
1. Fetch the item to confirm its status:
   `curl -s https://api.webflow.com/v2/collections/$COLLECTION_ID/items/$ITEM_ID -H "Authorization: Bearer $TOKEN"`
2. Construct the result summary.
**Output:** Final JSON result with item ID, slug, and confirmation of published status.
**Decision gate:**
- If item confirmed live -> report success
- If item still in draft state -> report partial success and advise manual publish from Webflow dashboard

## Output Format

```json
{
  "status": "published",
  "platform": "webflow",
  "item_id": "64a1b2c3d4e5f6...",
  "collection_id": "63f...",
  "slug": "article-title",
  "fields_populated": ["name", "slug", "post-body", "meta-title", "meta-description"],
  "published_at": "2026-03-16T12:00:00Z",
  "notes": "Item is live. Images referenced via external CDN URLs."
}
```

## Supplementary Recipes

### Update an Existing Item

```bash
# PATCH to update fields, then republish
curl -s -X PATCH "https://api.webflow.com/v2/collections/$COLLECTION_ID/items/$ITEM_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "fieldData": { "post-body": "<p>Updated HTML</p>" } }'

# Must republish after update for changes to go live
curl -s -X POST "https://api.webflow.com/v2/collections/$COLLECTION_ID/items/publish" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "itemIds": ["ITEM_ID"] }'
```

### List Items with Pagination

```bash
# Default returns up to 100 items; use offset/limit for pagination
curl -s "https://api.webflow.com/v2/collections/$COLLECTION_ID/items?offset=0&limit=100" \
  -H "Authorization: Bearer $TOKEN" | jq '.items[] | {id, slug, name: .fieldData.name}'
```

### Delete an Item

```bash
curl -s -X DELETE "https://api.webflow.com/v2/collections/$COLLECTION_ID/items/$ITEM_ID" \
  -H "Authorization: Bearer $TOKEN"
```

### Bulk Publish Multiple Items

```bash
# Publish up to 100 items in one call
curl -s -X POST "https://api.webflow.com/v2/collections/$COLLECTION_ID/items/publish" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "itemIds": ["ITEM_ID_1", "ITEM_ID_2", "ITEM_ID_3"] }'
```

### Image Handling

Webflow v2 has no native asset upload API. Use one of these approaches:

1. **External URL in rich text:** Embed `<img src="https://cdn.example.com/image.jpg">` directly in the RichText field HTML.
2. **Image field type:** Pass a URL object matching the Image field schema from the collection.
3. **Recommended pipeline:** Upload images to an external CDN (S3, Cloudflare R2) first, then reference the CDN URLs in Webflow fields.

## Edge Cases & Judgment Calls

1. **Field slugs vary by collection.** Never hardcode field slugs like `post-body` or `meta-title`. Always fetch the schema in Step 3. A "Blog Posts" collection might use `body` while another uses `post-body` or `content`.

2. **Rate limit hit during bulk operations.** If `X-RateLimit-Remaining` reaches 0, pause until the timestamp in `X-RateLimit-Reset`. For bulk creates (10+ items), proactively add a 1-second delay between each request rather than waiting for a 429.

3. **Rich text field rejects raw text.** RichText fields require valid HTML. If the input is plain text, wrap it in `<p>` tags before submitting. Malformed HTML may be silently stripped by Webflow.

4. **Required fields missing from input.** If the collection schema has required fields (e.g., `author`, `category`) that the user did not provide, stop and ask rather than submitting with empty values -- the API will reject the request with a 400 error.

5. **Item created but publish fails.** The item exists as a draft. Do not re-create it. Retry the publish call with the existing item ID. Report the draft state to the user so they can manually publish from the Webflow dashboard if retries fail.

6. **Slug conflicts.** If the API returns a 409 or slug-conflict error, append a numeric suffix (e.g., `article-title-2`) and retry. Report the adjusted slug in the output.

7. **DateTime format rejection.** Webflow requires ISO 8601 format (`2026-03-16T00:00:00Z`). If the input date is in another format, convert it before submission. Omit the field entirely if no date is provided and it is not required.

## What This Skill Does NOT Do

- **Does not upload images to Webflow.** The v2 API has no asset upload endpoint. Images must be hosted externally and referenced by URL.
- **Does not manage Webflow site design, pages, or templates.** This skill only interacts with CMS collection items.
- **Does not generate content.** It publishes content that has already been created (e.g., by the `ai-seo-engine` skill).
- **Does not manage Webflow domains, hosting, or SSL.** Site configuration is out of scope.
- **Does not handle Webflow Memberships or Ecommerce APIs.** Only CMS collections are supported.

## Examples

### Example 1: Happy Path -- Publish a Blog Post

**Situation:** The agent has HTML content and SEO metadata from `ai-seo-engine` and needs to publish it to a Webflow blog collection.

**Execution:**
1. Validate token: `curl -s -o /dev/null -w "%{http_code}" https://api.webflow.com/v2/sites -H "Authorization: Bearer $TOKEN"` -> 200
2. Schema fetch for collection `63f_abc123` reveals fields: `name` (PlainText, required), `slug` (PlainText, required), `post-body` (RichText), `meta-title` (PlainText), `meta-description` (PlainText), `publish-date` (DateTime)
3. Create item:
   ```bash
   curl -s -X POST "https://api.webflow.com/v2/collections/63f_abc123/items" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "fieldData": {
         "name": "10 Technical SEO Fixes That Boost Rankings",
         "slug": "technical-seo-fixes-boost-rankings",
         "post-body": "<h2>Introduction</h2><p>Technical SEO is the foundation...</p>",
         "meta-title": "10 Technical SEO Fixes That Boost Rankings | ACME Blog",
         "meta-description": "Learn the 10 most impactful technical SEO fixes that can improve your search rankings and organic traffic.",
         "publish-date": "2026-03-16T00:00:00Z"
       }
     }'
   ```
   Response: `{ "id": "64a_item789", ... }`
4. Publish: `POST /v2/collections/63f_abc123/items/publish` with `{ "itemIds": ["64a_item789"] }`
5. Output:
   ```json
   {
     "status": "published",
     "platform": "webflow",
     "item_id": "64a_item789",
     "collection_id": "63f_abc123",
     "slug": "technical-seo-fixes-boost-rankings",
     "fields_populated": ["name", "slug", "post-body", "meta-title", "meta-description", "publish-date"],
     "published_at": "2026-03-16T12:00:00Z",
     "notes": ""
   }
   ```

### Example 2: Edge Case -- Required Field Missing, Schema Mismatch

**Situation:** The user says "publish this article to our Webflow blog" but the collection has a required `category` field (Option type) and a required `author` field (PlainText) that were not provided in the input.

**Execution:**
1. Validate token -> 200
2. Schema fetch reveals required fields: `name`, `slug`, `post-body`, `category` (Option, required), `author` (PlainText, required)
3. The agent has `name`, `slug`, and `post-body` from the input, but `category` and `author` are missing.
4. **Decision: Stop and ask.** Do not submit an incomplete payload.
5. Agent reports:
   > "The Webflow collection requires two additional fields that were not provided:
   > - **category** (Option type) -- available values: 'SEO', 'Content Marketing', 'Technical'
   > - **author** (PlainText)
   >
   > Please provide values for these fields so I can publish the item."
6. After the user provides values, the agent resumes from Step 4 (Create Draft Item) with the complete payload.

### Example 3: Edge Case -- Bulk Publish with Rate Limiting

**Situation:** The user wants to publish 25 articles from a batch export.

**Execution:**
1. Validate token -> 200
2. Fetch schema once (1 request).
3. Create items in a loop with a 1-second delay between each request (25 requests over ~25 seconds).
4. After all items are created, batch-publish all 25 item IDs in a single publish call.
5. Monitor `X-RateLimit-Remaining` throughout. If it drops below 5, pause until `X-RateLimit-Reset`.
6. Output includes all 25 item IDs and their slugs, plus a note on any that failed.

## Full Pipeline Reference

The end-to-end pipeline from AI SEO Engine to Webflow:

```
aiseo drive folder -> gws export HTML -> fetch collection schema -> create item -> publish
```

1. `aiseo drive folder --project-id $PID` -- get the Google Drive folder ID for the project
2. `gws` -- export the generated content as HTML from Google Docs
3. Fetch Webflow collection schema (Step 3 above)
4. Create Webflow CMS item with the HTML and SEO metadata (Step 4 above)
5. Publish the item (Step 5 above)
