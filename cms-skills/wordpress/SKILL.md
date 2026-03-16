---
name: cms-wordpress
version: "1.0"
description: >
  Publish content to WordPress via WP-CLI (server access) or REST API (remote access).
  Trigger when the task involves publishing, updating, or managing posts on a WordPress site,
  including setting featured images, categories, tags, and SEO metadata (Yoast or RankMath).

inputs:
  required:
    - type: text
      label: "wordpress-url"
      description: "WordPress site URL (e.g., https://example.com)"
    - type: text
      label: "wordpress-credentials"
      description: "WP-CLI: server/SSH access. REST API: Application Password as 'username:xxxx xxxx xxxx xxxx'"
  optional:
    - type: text
      label: "html-content"
      description: "HTML content to publish (from file or AI SEO Engine deliverable)"
    - type: file
      label: "featured-image"
      description: "Image file path or URL for the post's featured image"
    - type: object
      label: "seo-metadata"
      description: "SEO title, meta description, and focus keyword for Yoast or RankMath"
    - type: text
      label: "target-keyword"
      description: "Primary keyword for the post (used in SEO plugin fields)"

outputs:
  - type: json
    label: "published-post"
    description: "Published WordPress post with URL, post ID, and status confirmation"

tools_used: [curl, wp-cli, jq]
chains_from: [ai-seo-engine]
chains_to: []
tags: [cms, wordpress, publishing, seo]
---

# WordPress Publishing — Agent Skill

Publish AI-generated content to WordPress sites using WP-CLI (server access) or REST API (remote access). Handles the full pipeline: media upload, category/tag assignment, post creation, and SEO metadata configuration.

## What This Skill Does

Publishes content to WordPress including featured images, taxonomy terms, and SEO plugin metadata. Supports both WP-CLI for direct server access and the WP REST API for remote publishing.

## Context the Agent Needs

- **Which access method?** Use WP-CLI when you have server/SSH access (faster, simpler). Use REST API when publishing remotely or WP-CLI is unavailable.
- **Which SEO plugin?** Check for Yoast (`_yoast_wpseo_*` meta keys) or RankMath (`rank_math_*` meta keys). These use different field names for the same purpose.
- **Draft vs publish?** Default to `--post_status=draft` for review unless the user explicitly requests `publish`. This prevents accidental live posts.
- **Image format support:** WordPress accepts JPG, PNG, GIF. WebP requires WP 5.8+. AVIF requires WP 6.5+. Google Drive exports may need format conversion.
- **Internal links:** If a spreadsheet of internal links is provided, inject those links into the HTML content BEFORE publishing — they cannot be reliably added after.

## Workflow Steps

### Step 1: Authenticate and Verify Access

**Input:** WordPress URL, credentials (WP-CLI access or Application Password)

**Process:**

Determine which access method is available, then verify connectivity.

*WP-CLI method:*
```bash
# Verify WP-CLI is available and connected
wp cli info
wp user list --format=json | jq '.[0].user_login'
```

*REST API method:*
```bash
# Test authentication with Application Password
curl -s https://yoursite.com/wp-json/wp/v2/users/me \
  -u "$WP_USER:$WP_APP_PASSWORD" | jq .name
```

**Output:** Confirmed authentication — username and access level.

**Decision gate:** If authentication fails, STOP. Check credentials, Application Password format (spaces between groups), and that the REST API is not disabled by a security plugin.

---

### Step 2: Prepare Taxonomy Terms (Categories and Tags)

**Input:** Target categories and tags for the post.

**Process:**

Look up existing terms. Create any that are missing.

*WP-CLI method:*
```bash
# List existing categories
wp term list category --format=json

# Create a new category if needed
wp term create category "SEO Tips"

# List existing tags (same pattern)
wp term list post_tag --format=json
```

*REST API method:*
```bash
# List existing categories
curl -s https://yoursite.com/wp-json/wp/v2/categories \
  -u "$WP_USER:$WP_APP_PASSWORD" | jq '.[] | {id, name}'

# Create a new category
curl -s -X POST https://yoursite.com/wp-json/wp/v2/categories \
  -u "$WP_USER:$WP_APP_PASSWORD" \
  -H "Content-Type: application/json" \
  -d '{"name": "SEO Tips"}' | jq '{id, name}'
```

**Output:** Category IDs and tag IDs (or names for WP-CLI) ready for post creation.

**Decision gate:** If a category name is ambiguous or has near-duplicates, ask the user which one to use rather than creating a duplicate.

---

### Step 3: Upload Featured Image (if provided)

**Input:** Image file path or URL.

**Process:**

Upload the image to the WordPress media library and capture the attachment ID.

*WP-CLI method:*
```bash
# Upload from local file and set as featured image for a post
wp media import ./featured-image.jpg --post_id=123 --featured_image

# Upload from a remote URL
wp media import https://example.com/image.jpg --post_id=123 --featured_image
```

*REST API method:*
```bash
# Upload image file
curl -s -X POST https://yoursite.com/wp-json/wp/v2/media \
  -u "$WP_USER:$WP_APP_PASSWORD" \
  -H "Content-Disposition: attachment; filename=featured-image.jpg" \
  -H "Content-Type: image/jpeg" \
  --data-binary @featured-image.jpg | jq '{id, source_url}'
```

Save the returned media ID (`id` field) for use as `featured_media` in Step 5.

**Output:** Media attachment ID and URL.

**Decision gate:** If upload fails, check file size limits (WordPress default 2MB–64MB depending on server config) and supported formats (JPG, PNG, GIF, WebP 5.8+, AVIF 6.5+). Google Drive exports may produce formats that need conversion first.

---

### Step 4: Prepare Content and Internal Links

**Input:** HTML content, optional internal links spreadsheet.

**Process:**

If an internal links spreadsheet is provided (from Google Sheets via `gws`), inject links into the HTML content before publishing.

```bash
# Read links from a Google Sheet
gws sheets read SPREADSHEET_ID "Sheet1!A:C" --format=json

# Parse the JSON to get anchor text + target URL pairs
# Inject <a href="target-url">anchor text</a> into matching phrases in the HTML
```

If content comes from AI SEO Engine via Google Drive:
```bash
# Get the Drive folder for the project
aise drive folder --project-id PROJECT_ID

# Export the Google Doc as HTML
gws docs export DOC_ID --format=html --output=article.html
```

**Output:** Final HTML content ready for publishing, with internal links applied.

**Decision gate:** If the content contains existing internal links that conflict with the spreadsheet, preserve the existing links and skip duplicates.

---

### Step 5: Create or Update the Post

**Input:** HTML content, category IDs, tag IDs/names, featured media ID, post status.

**Process:**

Create a new post or update an existing one.

*WP-CLI — Create:*
```bash
wp post create \
  --post_title="Your SEO-Optimized Title" \
  --post_content="$(cat article.html)" \
  --post_status=publish
```

*WP-CLI — Update:*
```bash
wp post update 123 --post_content="$(cat updated.html)"
```

*WP-CLI — Assign taxonomy terms:*
```bash
# Set categories (by name or ID)
wp post term set 123 category "SEO Tips"

# Set tags
wp post term set 123 post_tag "seo" "content-marketing"
```

*REST API — Create:*
```bash
curl -s -X POST https://yoursite.com/wp-json/wp/v2/posts \
  -u "$WP_USER:$WP_APP_PASSWORD" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Your SEO-Optimized Title",
    "content": "<p>HTML content here...</p>",
    "status": "publish",
    "categories": [5, 12],
    "tags": [8, 15],
    "featured_media": 456
  }' | jq '{id, link, status}'
```

*REST API — Update:*
```bash
curl -s -X PUT https://yoursite.com/wp-json/wp/v2/posts/123 \
  -u "$WP_USER:$WP_APP_PASSWORD" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "<p>Updated HTML content...</p>"
  }' | jq '{id, link, status}'
```

**Output:** Post ID, permalink URL, and publish status.

**Decision gate:** If the post title already exists on the site, confirm with the user whether to create a duplicate or update the existing post.

---

### Step 6: Set SEO Plugin Metadata

**Input:** SEO title, meta description, focus keyword. Post ID from Step 5.

**Process:**

Detect which SEO plugin is active, then set the appropriate meta fields.

*WP-CLI — Yoast SEO:*
```bash
wp post meta update 123 _yoast_wpseo_title "Your SEO Title"
wp post meta update 123 _yoast_wpseo_metadesc "Your meta description under 160 chars."
wp post meta update 123 _yoast_wpseo_focuskw "target keyword"
```

*WP-CLI — RankMath SEO:*
```bash
wp post meta update 123 rank_math_title "Your SEO Title"
wp post meta update 123 rank_math_description "Your meta description under 160 chars."
wp post meta update 123 rank_math_focus_keyword "target keyword"
```

*REST API — Yoast SEO (via post meta):*
```bash
curl -s -X PUT https://yoursite.com/wp-json/wp/v2/posts/123 \
  -u "$WP_USER:$WP_APP_PASSWORD" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {
      "_yoast_wpseo_title": "Your SEO Title",
      "_yoast_wpseo_metadesc": "Your meta description under 160 chars.",
      "_yoast_wpseo_focuskw": "target keyword"
    }
  }'
```

*REST API — RankMath SEO (via post meta):*
```bash
curl -s -X PUT https://yoursite.com/wp-json/wp/v2/posts/123 \
  -u "$WP_USER:$WP_APP_PASSWORD" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {
      "rank_math_title": "Your SEO Title",
      "rank_math_description": "Your meta description under 160 chars.",
      "rank_math_focus_keyword": "target keyword"
    }
  }'
```

**Output:** Confirmed SEO metadata set on the post.

**Decision gate:** If meta update returns an error (e.g., meta key not registered), the SEO plugin may not be installed or may not expose its fields to the REST API. Fall back to WP-CLI if available, or notify the user.

---

### Step 7: Verify and Report

**Input:** Post ID from Step 5.

**Process:**

Confirm the post is live and all fields are correctly set.

*WP-CLI:*
```bash
wp post list --post_type=post --format=json \
  --fields=ID,post_title,post_status,post_date | jq '.[] | select(.ID == 123)'

wp post meta get 123 _yoast_wpseo_title
```

*REST API:*
```bash
curl -s https://yoursite.com/wp-json/wp/v2/posts/123 \
  -u "$WP_USER:$WP_APP_PASSWORD" | jq '{id, title: .title.rendered, status, link, categories, tags, featured_media}'
```

*Search for posts:*
```bash
# List recent posts
curl -s "https://yoursite.com/wp-json/wp/v2/posts?per_page=20&status=publish" \
  -u "$WP_USER:$WP_APP_PASSWORD" | jq '.[] | {id, title: .title.rendered, link}'

# Search by keyword
curl -s "https://yoursite.com/wp-json/wp/v2/posts?search=keyword" \
  -u "$WP_USER:$WP_APP_PASSWORD" | jq '.[] | {id, title: .title.rendered, link}'
```

**Output:** Final confirmation with post URL and all metadata.

**Decision gate:** If any field is missing or incorrect, go back to the relevant step and fix it before reporting success.

## Output Format

```
## WordPress Publish Result

- **Post ID:** 123
- **URL:** https://yoursite.com/your-seo-optimized-title/
- **Status:** publish
- **Categories:** SEO Tips
- **Tags:** seo, content-marketing
- **Featured Image:** https://yoursite.com/wp-content/uploads/2026/03/featured-image.jpg
- **SEO Plugin:** Yoast
  - Title: "Your SEO Title"
  - Description: "Your meta description under 160 chars."
  - Focus Keyword: "target keyword"
- **Method:** REST API
```

## Edge Cases & Judgment Calls

1. **No SEO plugin installed.** Skip Step 6 entirely. Inform the user that no Yoast or RankMath metadata was set, and recommend installing one.

2. **REST API disabled by security plugin.** Some hosts or security plugins (Wordfence, iThemes) disable the WP REST API for unauthenticated or even authenticated users. If `/wp-json/` returns 403 or is unreachable, try WP-CLI. If neither works, report the blocker.

3. **Application Password contains special characters.** WordPress Application Passwords use spaces between 4-character groups (e.g., `xxxx xxxx xxxx xxxx`). The entire `user:password` string must be passed to `-u` in curl. URL-encoding is NOT needed when using `-u`.

4. **Content has shortcodes or Gutenberg blocks.** If the HTML content contains WordPress shortcodes (`[shortcode]`) or Gutenberg block comments (`<!-- wp:paragraph -->`), publish as-is. Do NOT strip them. If publishing raw HTML to a Gutenberg site, the content will appear in a single Classic block, which is acceptable.

5. **Large content exceeds POST body limits.** Some servers limit POST body size (default ~8MB in PHP). For very large articles, check `post_max_size` in PHP config. With WP-CLI, use `--post_content="$(cat file.html)"` to avoid shell argument limits on very large files.

6. **Featured image from Google Drive.** Drive exports images in specific formats. Download the image first via `gws`, ensure it is in a WordPress-supported format (JPG, PNG, GIF, WebP 5.8+, AVIF 6.5+), then upload to the media library before attaching to the post.

7. **Duplicate post titles.** WordPress allows duplicate titles (they get different slugs). If a post with the same title already exists, confirm with the user whether to update the existing post or create a new one.

## What This Skill Does NOT Do

- **Does NOT generate content.** Use the `ai-seo-engine` skill to generate articles. This skill only publishes them.
- **Does NOT manage WordPress plugins, themes, or site settings.** Only post-level operations.
- **Does NOT handle custom post types** beyond `post`. Pages and custom types may work but are not covered here.
- **Does NOT configure WordPress Application Passwords.** The user must create these in WP Admin > Users > Profile before using the REST API method.
- **Does NOT handle multisite network operations.** Single-site WordPress only.

## Examples

### Example 1: Happy Path — Full Pipeline via REST API

**Scenario:** Publish an AI SEO Engine article to WordPress with featured image and Yoast SEO metadata.

```bash
# 1. Verify access
curl -s https://myblog.com/wp-json/wp/v2/users/me \
  -u "$WP_USER:$WP_APP_PASSWORD" | jq .name
# => "Editor User"

# 2. Get/create category
curl -s https://myblog.com/wp-json/wp/v2/categories \
  -u "$WP_USER:$WP_APP_PASSWORD" | jq '.[] | select(.name == "SEO Tips") | .id'
# => 5

# 3. Upload featured image
curl -s -X POST https://myblog.com/wp-json/wp/v2/media \
  -u "$WP_USER:$WP_APP_PASSWORD" \
  -H "Content-Disposition: attachment; filename=hero.jpg" \
  -H "Content-Type: image/jpeg" \
  --data-binary @hero.jpg | jq .id
# => 789

# 4. Create post
curl -s -X POST https://myblog.com/wp-json/wp/v2/posts \
  -u "$WP_USER:$WP_APP_PASSWORD" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "10 On-Page SEO Tips for 2026",
    "content": "<h2>Introduction</h2><p>On-page SEO remains critical...</p>",
    "status": "publish",
    "categories": [5],
    "tags": [8, 15],
    "featured_media": 789
  }' | jq '{id, link, status}'
# => {"id": 1234, "link": "https://myblog.com/10-on-page-seo-tips-2026/", "status": "publish"}

# 5. Set Yoast metadata
curl -s -X PUT https://myblog.com/wp-json/wp/v2/posts/1234 \
  -u "$WP_USER:$WP_APP_PASSWORD" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {
      "_yoast_wpseo_title": "10 On-Page SEO Tips for 2026 | MyBlog",
      "_yoast_wpseo_metadesc": "Learn the top 10 on-page SEO techniques to boost rankings in 2026.",
      "_yoast_wpseo_focuskw": "on-page seo tips"
    }
  }'
```

**Result:**
```
## WordPress Publish Result

- **Post ID:** 1234
- **URL:** https://myblog.com/10-on-page-seo-tips-2026/
- **Status:** publish
- **Categories:** SEO Tips
- **Tags:** seo, content-marketing
- **Featured Image:** https://myblog.com/wp-content/uploads/2026/03/hero.jpg
- **SEO Plugin:** Yoast
  - Title: "10 On-Page SEO Tips for 2026 | MyBlog"
  - Description: "Learn the top 10 on-page SEO techniques to boost rankings in 2026."
  - Focus Keyword: "on-page seo tips"
- **Method:** REST API
```

### Example 2: Edge Case — WP-CLI with RankMath and Internal Links from Spreadsheet

**Scenario:** Server access available. Content needs internal links injected from a Google Sheet before publishing. Site uses RankMath instead of Yoast.

```bash
# 1. Read internal links from Google Sheet
gws sheets read 1aBcDeFgHiJkLmNoPqRsT "Links!A:C" --format=json
# => [{"anchor": "SEO audit", "url": "/seo-audit-guide/", "target_post": "all"}, ...]

# 2. Download content from Drive
aise drive folder --project-id proj_abc123
gws docs export DOC_ID --format=html --output=article.html

# 3. Inject internal links into article.html (find anchor phrases, wrap in <a> tags)
# Agent processes the JSON and modifies article.html accordingly

# 4. Create post
wp post create \
  --post_title="Complete Guide to Technical SEO" \
  --post_content="$(cat article.html)" \
  --post_status=draft

# => Success: Created post 567.

# 5. Assign categories and tags
wp term create category "Technical SEO"
wp post term set 567 category "Technical SEO"
wp post term set 567 post_tag "technical-seo" "site-audit" "crawlability"

# 6. Upload and attach featured image
wp media import ./technical-seo-hero.png --post_id=567 --featured_image

# 7. Set RankMath metadata
wp post meta update 567 rank_math_title "Complete Guide to Technical SEO | MySite"
wp post meta update 567 rank_math_description "Master technical SEO with this comprehensive guide covering crawlability, indexing, and site architecture."
wp post meta update 567 rank_math_focus_keyword "technical seo"

# 8. Publish when ready
wp post update 567 --post_status=publish
```

**Result:**
```
## WordPress Publish Result

- **Post ID:** 567
- **URL:** https://mysite.com/complete-guide-technical-seo/
- **Status:** publish
- **Categories:** Technical SEO
- **Tags:** technical-seo, site-audit, crawlability
- **Featured Image:** https://mysite.com/wp-content/uploads/2026/03/technical-seo-hero.png
- **SEO Plugin:** RankMath
  - Title: "Complete Guide to Technical SEO | MySite"
  - Description: "Master technical SEO with this comprehensive guide covering crawlability, indexing, and site architecture."
  - Focus Keyword: "technical seo"
- **Method:** WP-CLI
- **Note:** 3 internal links injected from spreadsheet before publishing.
```
