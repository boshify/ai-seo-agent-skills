---
name: ai-seo-engine
version: "1.0"
description: >
  Programmatic access to AI SEO Engine via the `aise` CLI. Use this skill to manage SEO projects,
  generate AI content, retrieve deliverables from Google Drive, and publish to CMS platforms.
  Trigger when the task involves AI SEO Engine, the `aise` CLI, or SEO content automation.

inputs:
  required:
    - type: text
      label: "aise-api-key"
      description: "API key starting with aise_ (get at https://aiseoengine.studio/app/profile)"
  optional:
    - type: text
      label: "project-id"
      description: "Target project ID (discover via `aise projects list`)"
    - type: text
      label: "google-workspace-cli"
      description: "Google Workspace CLI (`gws`) for Drive file access"

outputs:
  - type: json
    label: "cli-output"
    description: "JSON responses from aise CLI commands"

tools_used: [aise-cli, gws-cli, curl, jq]
chains_from: []
chains_to: [cms-wordpress, cms-webflow, cms-shopify]
tags: [seo, content-generation, ai, cli, google-drive]
---

# AI SEO Engine — Agent Skills

AI SEO Engine is an AI-powered SEO content platform. This skills library teaches agents how to use it programmatically via the `aise` CLI.

## Quick Start

```bash
# 1. Install
npm install -g @aise/cli

# 2. Configure (get your key at https://aiseoengine.studio/app/profile)
export AISE_API_KEY=aise_your_key_here
export AISE_BASE_URL=https://aiseoengine.studio

# 3. Verify
aise auth status
```

## Capabilities

| Command Group | Description |
|--------------|-------------|
| `aise auth status` | Check authentication and account info |
| `aise projects list\|create\|update\|delete` | Manage SEO projects |
| `aise content list\|create\|update\|delete\|import` | Manage content items and bulk import |
| `aise jobs start\|status\|wait\|cancel\|list` | Run AI content generation jobs |
| `aise categories list\|create` | Organize content by category |
| `aise config get\|set` | Configure project settings (language, style, etc.) |
| `aise topical-map` | Generate a topical map for a project |
| `aise content-types list` | List available content type templates |
| `aise statuses` | List workflow statuses |
| `aise usage` | View usage analytics |
| `aise drive folder` | Get Google Drive folder ID for a project |

All commands output JSON by default. Add `--pretty` for formatted output.

## Documentation

| Doc | Purpose |
|-----|---------|
| [setup.md](./setup.md) | Installation, API key setup, environment variables |
| [concepts.md](./concepts.md) | What each feature does, how the pipeline works, status behaviors |
| [cli-reference.md](./cli-reference.md) | Complete command reference with examples |
| [workflows.md](./workflows.md) | Step-by-step workflow recipes |
| [google-workspace.md](./google-workspace.md) | Google Drive/Docs/Sheets integration via `gws` |
| [troubleshooting.md](./troubleshooting.md) | Common errors and fixes |

## CMS Publishing

After generating content, publish it to your CMS using the [CMS Skills](../cms-skills/):
- [WordPress](../cms-skills/wordpress/SKILL.md) — WP-CLI and REST API
- [Webflow](../cms-skills/webflow/SKILL.md) — Webflow CMS API
- [Shopify](../cms-skills/shopify/SKILL.md) — Admin REST API

## Links

- **Web App**: https://aiseoengine.studio
- **CLI Landing Page**: https://aiseoengine.studio/cli
- **API Key Management**: https://aiseoengine.studio/app/profile
