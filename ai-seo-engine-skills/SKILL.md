---
name: ai-seo-engine
version: "1.0"
description: >
  Programmatic access to AI SEO Engine via the `aiseo` CLI. Use this skill to manage SEO projects,
  generate AI content, retrieve deliverables from Google Drive, and publish to CMS platforms.
  Trigger when the task involves AI SEO Engine, the `aiseo` CLI, or SEO content automation.

inputs:
  required:
    - type: text
      label: "aiseo-api-key"
      description: "API key starting with aiseo_ (get at https://aiseoengine.studio/app/profile)"
  optional:
    - type: text
      label: "project-id"
      description: "Target project ID (discover via `aiseo projects list`)"
    - type: text
      label: "google-workspace-cli"
      description: "Google Workspace CLI (`gws`) for Drive file access"

outputs:
  - type: json
    label: "cli-output"
    description: "JSON responses from aiseo CLI commands"

tools_used: [aiseo-cli, mcp-server, gws-cli, curl, jq]
chains_from: []
chains_to: [cms-wordpress, cms-webflow, cms-shopify]
tags: [seo, content-generation, ai, cli, mcp, google-drive]
---

# AI SEO Engine — Agent Skills

AI SEO Engine is an AI-powered SEO content platform. This skills library teaches agents how to use it programmatically via the `aiseo` CLI.

## Quick Start

### Option A: MCP (for AI chat interfaces)

Connect directly from Claude, Cursor, or any MCP-compatible tool — no installation needed.

- **MCP URL**: `https://aiseoengine.studio/api/mcp`
- **Auth**: Bearer token with your `AISEO_API_KEY`
- **Setup guide**: [mcp-setup.md](./mcp-setup.md)

### Option B: CLI (for scripts and automation)

```bash
# 1. Install
npm install -g @aiseo/cli

# 2. Configure (get your key at https://aiseoengine.studio/app/profile)
export AISEO_API_KEY=aiseo_your_key_here
export AISEO_BASE_URL=https://aiseoengine.studio

# 3. Verify
aiseo auth status
```

## Capabilities

| Command Group | Description |
|--------------|-------------|
| `aiseo auth status` | Check authentication and account info |
| `aiseo projects list\|create\|update\|delete` | Manage SEO projects |
| `aiseo content list\|create\|update\|delete\|import` | Manage content items and bulk import |
| `aiseo jobs start\|status\|wait\|cancel\|list` | Run AI content generation jobs |
| `aiseo categories list\|create` | Organize content by category |
| `aiseo config get\|set` | Configure project settings (language, style, etc.) |
| `aiseo topical-map` | Generate a topical map for a project |
| `aiseo content-types list` | List available content type templates |
| `aiseo statuses` | List workflow statuses |
| `aiseo usage` | View usage analytics |
| `aiseo drive folder` | Get Google Drive folder ID for a project |

All commands output JSON by default. Add `--pretty` for formatted output.

## Documentation

| Doc | Purpose |
|-----|---------|
| [setup.md](./setup.md) | Installation, API key setup, environment variables |
| [concepts.md](./concepts.md) | What each feature does, how the pipeline works, status behaviors |
| [cli-reference.md](./cli-reference.md) | Complete command reference with examples |
| [workflows.md](./workflows.md) | Step-by-step workflow recipes |
| [google-workspace.md](./google-workspace.md) | Google Drive/Docs/Sheets integration via `gws` |
| [mcp-setup.md](./mcp-setup.md) | MCP server setup for Claude, Cursor, and other AI tools |
| [troubleshooting.md](./troubleshooting.md) | Common errors and fixes |

## CMS Publishing

After generating content, publish it to your CMS using the [CMS Skills](../cms-skills/):
- [WordPress](../cms-skills/wordpress/SKILL.md) — WP-CLI and REST API
- [Webflow](../cms-skills/webflow/SKILL.md) — Webflow CMS API
- [Shopify](../cms-skills/shopify/SKILL.md) — Admin REST API

## Links

- **Web App**: https://aiseoengine.studio
- **MCP Server**: https://aiseoengine.studio/api/mcp
- **MCP Landing Page**: https://aiseoengine.studio/mcp
- **CLI Landing Page**: https://aiseoengine.studio/cli
- **API Key Management**: https://aiseoengine.studio/app/profile
