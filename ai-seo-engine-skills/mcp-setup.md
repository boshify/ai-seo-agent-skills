# MCP Server Setup

AI SEO Engine provides a remote MCP (Model Context Protocol) server so you can manage SEO projects, content, and jobs directly from Claude, Cursor, or any MCP-compatible AI tool — no CLI installation required.

**MCP Server URL:** `https://aiseoengine.studio/api/mcp`

## Prerequisites

- An AI SEO Engine account
- For **Claude.ai / ChatGPT**: just the MCP URL (OAuth sign-in is automatic)
- For **CLI / Cursor / Desktop**: an API key (generate at [Profile → API Keys](https://aiseoengine.studio/app/profile))

## Authentication

The MCP server supports two authentication methods:

| Method | Used by | How it works |
|--------|---------|-------------|
| **OAuth 2.1** | Claude.ai, ChatGPT, web connectors | Automatic — paste the MCP URL, sign in when prompted |
| **API Key** | CLI, Cursor, Claude Desktop, scripts | Set `Authorization: Bearer aiseo_your_key_here` header |

Both methods provide the same access to all 27 tools.

## Setup by Client

### Claude.ai (OAuth — recommended)

1. Go to **Settings → Integrations** (or **Settings → MCP Servers**)
2. Click **Add custom integration** (or **Add MCP Server**)
3. Enter the MCP server URL: `https://aiseoengine.studio/api/mcp`
4. Click **Connect** — you'll be redirected to sign in with your AI SEO Engine account
5. Approve access on the consent screen
6. Done. The 27 AI SEO Engine tools will appear in your conversation.

No API key is needed — OAuth handles authentication automatically.

### ChatGPT (OAuth)

1. Go to **Settings → Connected Apps** (or your MCP configuration)
2. Add a new MCP server with URL: `https://aiseoengine.studio/api/mcp`
3. Sign in when prompted — OAuth flow is automatic
4. Approve access and start using tools

### Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ai-seo-engine": {
      "url": "https://aiseoengine.studio/api/mcp",
      "headers": {
        "Authorization": "Bearer aiseo_your_key_here"
      }
    }
  }
}
```

Config file locations:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Restart Claude Desktop after saving.

### Cursor

1. Open **Settings → MCP**
2. Click **Add MCP Server**
3. Set type to **Remote (Streamable HTTP)**
4. Enter URL: `https://aiseoengine.studio/api/mcp`
5. Add header: `Authorization: Bearer aiseo_your_key_here`
6. Save and restart Cursor.

### Windsurf / Other MCP Clients

Any client supporting remote MCP servers via Streamable HTTP can connect:
- **URL**: `https://aiseoengine.studio/api/mcp`
- **Auth**: Bearer token via `Authorization` header
- **Transport**: Streamable HTTP (stateless)

## Available Tools

The MCP server exposes 27 tools — everything the CLI can do:

### Project Management

| Tool | Description |
|------|-------------|
| `auth_status` | Check authentication status and plan details |
| `projects_list` | List all projects in your account |
| `projects_create` | Create a new project |
| `projects_update` | Update an existing project |
| `projects_delete` | Delete a project |

### Content Management

| Tool | Description |
|------|-------------|
| `content_list` | List content items in a project. `limit` is a positive integer capped at 1000 (numeric — strings fail validation). |
| `content_create` | Create a new content item. In addition to the basics (`projectId`, `name`, `status`, `contentType`, `slug`, `notes`), accepts the per-stage URLs and stage flag — see param notes below. After the API returns an ID, the tool re-queries the row to confirm it exists; a missing row throws "possible silent write failure, retry" rather than returning a phantom ID. |
| `content_update` | Update a content item. Same expanded param set as `content_create`. Same post-write existence check on the supplied ID. |
| `content_delete` | Delete content items |
| `content_bulk_delete` | Delete multiple content items at once |
| `content_bulk_import` | Bulk import content items from a list |

**`content_create` / `content_update` — expanded params**

In addition to the basic fields, both tools accept:

| Param | Type | Description |
|-------|------|-------------|
| `newOrExisting` | `"Existing"` \| `"New"` | Defaults to `"New"` on create when omitted |
| `clearscopeLink` | URL | Clearscope report URL |
| `fourPLink` | URL | 4P doc URL |
| `contentBriefLink` | URL | Content Brief sheet URL |
| `contentDocUrl` | URL | Generated content Google Doc URL |
| `finalArticleUrl` | URL | Final article URL — the "Recommended URL" |
| `driveFolderUrl` | URL | Drive folder URL for this item |
| `recommendedUrl` | URL | **Alias for `finalArticleUrl`.** "Recommended URL" in Asana IS the Final Article URL — mapped to `finalArticleUrl` server-side before forwarding. Explicit `finalArticleUrl` wins if both are supplied. |

Use these when ingesting from an external system (Asana, Notion, etc.) that already has these per-stage URLs populated, instead of dumping them into `notes`.

### Job Management

| Tool | Description |
|------|-------------|
| `jobs_start` | Start a content generation job |
| `jobs_status` | Get the status of a job |
| `jobs_wait` | Wait for a job to complete (polls until done or timeout) |
| `jobs_cancel` | Cancel a running job |
| `jobs_list` | List jobs for a project |

### Configuration & Discovery

| Tool | Description |
|------|-------------|
| `categories_list` | List categories for a project |
| `categories_create` | Create a new category |
| `config_get` | Get project configuration |
| `config_set` | Update project configuration |
| `topical_map_generate` | Generate a topical authority map |
| `content_types_list` | List available content type definitions |
| `statuses_list` | List all workflow statuses |
| `usage_analytics` | View usage analytics and quotas |
| `drive_folder` | Get Google Drive folder ID for a project |
| `content_export_doc` | Export a Google Doc as clean markdown for CMS publishing |

### Prompt Database

Tenant-scoped editorial prompts the workflow runners load at runtime. Two row kinds: **core** (registry-wired, body-only editable, undeletable) and **custom** (user-added at named injection points, full CRUD).

| Tool | Description |
|------|-------------|
| `prompts_list` | List every prompt in the tenant (filter by `section` 4P\|CB\|CG\|Global, or by `kind` core\|custom). Returns slim metadata; use `prompts_get` for bodies. |
| `prompts_get` | Fetch one prompt's full body by `id` or by stable `key` (e.g. `cg.writer-hard-rules`). |
| `prompts_create` | Create a custom prompt. Requires `section`, `name`, `systemPrompt`, and `injectionPoint`. Always becomes `kind=custom` (core rows are seeded from the in-code registry, not via this tool). |
| `prompts_update` | Partial update by `id`. Core rows accept `systemPrompt` / `description` / `sortOrder` only; custom rows accept the full field set. Body changes are versioned (audit-trail). |
| `prompts_delete` | Delete a custom prompt. Core prompts reject delete — wipe `systemPrompt` to `""` to fall back to the registry default instead. |

**Valid `injectionPoint` values** per section:

| Section | Injection points |
|---------|------------------|
| 4P | `4p.all-agents` |
| CB | `cb.outline.extras`, `cb.qa.extras`, `cb.writer-instructions.extras`, `cb.brief-sections.extras` |
| CG | `cg.writer.extras`, `cg.section-editor.extras`, `cg.surgical-edit.extras` |

**Typical workflows:**

```
# Inspect what's wired
prompts_list({ kind: "core" })

# Read one body
prompts_get({ key: "cg.writer-hard-rules" })

# Add a custom rule the writer agent will see
prompts_create({
  section: "CG",
  name: "BetOnline domain casing",
  systemPrompt: "Always write 'BetOnline.ag' with that exact casing.",
  injectionPoint: "cg.writer.extras"
})

# Tweak a core rule's body (auto-captures a version)
prompts_update({ id: "cm...", systemPrompt: "...edited...", note: "Tightened the em-dash language" })

# Disable a core rule (runner falls back to registry default + logs a warning)
prompts_update({ id: "cm...", systemPrompt: "", note: "Disabled while tuning" })
```

## Example Conversations

### List projects
> "Show me all my SEO projects"

The AI will call `projects_list` and display your projects.

### Generate content
> "Create a blog post about 'best running shoes 2026' in my Tech Blog project and start generating it"

The AI will:
1. Call `projects_list` to find the project
2. Call `content_create` with the keyword
3. Call `jobs_start` to begin generation
4. Optionally call `jobs_status` to check progress

### Bulk workflow
> "Import these 10 keywords into my project and start generating all of them"

The AI will:
1. Call `content_bulk_import` with all keywords
2. Call `jobs_start` for each content item
3. Monitor with `jobs_list`

### Export content to CMS
> "Export the article for 'best widgets 2024' as markdown"

The AI will:
1. Call `drive_folder` to find the project's Google Drive folder
2. Find the doc ID for the content item
3. Call `content_export_doc` with the doc ID and user key to get clean markdown

## Troubleshooting

### "Authorization required" (401)
- **OAuth users (Claude.ai/ChatGPT)**: Try disconnecting and reconnecting. The OAuth token may have expired — reconnecting triggers a fresh sign-in.
- **API key users**: Verify your key starts with `aiseo_` and hasn't been revoked.

### "Rate limit exceeded" (429)
API keys are rate-limited (60 req/min on Starter, 120 on Team). Wait and retry.

### Claude Desktop: "Some MCP servers could not be loaded"
Claude Desktop requires a recent version to support remote MCP servers (Streamable HTTP). If you see this error:
1. Update Claude Desktop to the latest version (Help → Check for Updates, or re-download from [claude.ai/download](https://claude.ai/download))
2. Restart Claude Desktop after updating
3. Your config is likely correct — older versions just don't recognize the `url` field

If you can't update, use **Claude.ai** (web) instead — go to Settings → Integrations, paste the MCP URL, and OAuth handles auth automatically with no API key needed.

### Tools not appearing
- Verify the URL is exactly `https://aiseoengine.studio/api/mcp`
- Check that your client supports remote MCP servers
- Try disconnecting and reconnecting

### Slow responses
MCP tools call the API internally. Most respond in under 2 seconds. Job generation (`jobs_start`, `topical_map_generate`) returns immediately with a job ID — the actual work runs in the background.

## MCP vs CLI

| Feature | MCP | CLI |
|---------|-----|-----|
| Installation | None | `npm install -g @aiseo/cli` |
| Auth | OAuth (web) or API key (desktop) | `AISEO_API_KEY` env var |
| Interface | Natural language via AI tools | Command line |
| Best for | Chat-based workflows | Scripts and automation |
| Tools/Commands | 27 tools | 12 command groups |

Both use the same API endpoints and API key. You can use both interchangeably.

## Next Steps

- [concepts.md](./concepts.md) — Understand what each feature does
- [workflows.md](./workflows.md) — Step-by-step workflow recipes
- [CMS Publishing](../cms-skills/) — Publish generated content to WordPress, Webflow, Shopify
