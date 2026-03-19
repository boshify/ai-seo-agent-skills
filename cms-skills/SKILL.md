---
name: cms-skills
version: "1.0"
description: >
  Index of CMS publishing skills for AI agents. Use this to discover the right CMS skill
  for publishing content to WordPress, Webflow, or Shopify. Trigger when the task involves
  publishing HTML content to a CMS platform.

inputs:
  required:
    - type: text
      label: "cms-platform"
      description: "Target CMS: wordpress, webflow, or shopify"
    - type: text
      label: "html-content"
      description: "HTML content to publish (from Google Drive, file, or generated)"
  optional:
    - type: text
      label: "seo-metadata"
      description: "Title tag, meta description, focus keyword"

outputs:
  - type: text
    label: "published-url"
    description: "URL of the published content on the target CMS"

tools_used: [curl, jq]
chains_from: [ai-seo-engine]
chains_to: []
tags: [cms, publishing, seo, content]
---

## What This Skill Does

Routes content publishing tasks to the correct platform-specific CMS skill. Each sub-skill handles authentication, content creation, media upload, SEO metadata, and publishing for its platform.

## Typical Workflow

1. Generate content with AI SEO Engine (`aiseo jobs start`)
2. Wait for completion (`aiseo jobs wait --id <jobId>`)
3. Get project Drive folder (`aiseo drive folder --project <id>`)
4. Download deliverables from Google Drive (`gws drive files export`)
5. Publish to your CMS using the appropriate skill below

## Available Skills

| Platform | Skill | Auth Method | Best For |
|----------|-------|-------------|----------|
| WordPress | [wordpress/SKILL.md](./wordpress/SKILL.md) | Application Passwords or WP-CLI | Blogs, content sites, most common CMS |
| Webflow | [webflow/SKILL.md](./webflow/SKILL.md) | API Token (Bearer) | Designer-built sites, marketing sites |
| Shopify | [shopify/SKILL.md](./shopify/SKILL.md) | Admin API Access Token | E-commerce blogs, store pages |

## How to Choose

- **WordPress** — Default choice. Most flexible, supports WP-CLI (server access) and REST API (remote). Best plugin ecosystem for SEO (Yoast, RankMath).
- **Webflow** — When the site is built in Webflow Designer. Collection-based CMS with schema-first approach. No native image upload API — use external CDN.
- **Shopify** — When publishing to an e-commerce store's blog or pages. Simpler API but limited to articles and pages.

## Prerequisites

- Content ready (HTML or Markdown) — typically from AI SEO Engine via Google Drive
- CMS credentials configured (see individual skill docs)
- [AI SEO Engine CLI](../ai-seo-engine-skills/SKILL.md) installed for content generation
- [Google Workspace CLI](https://github.com/googleworkspace/cli) installed for downloading content from Drive
