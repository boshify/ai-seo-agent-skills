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
| **API Key** | CLI, Cursor, Claude Desktop, scripts | Set `Authorization: Bearer aise_your_key_here` header |

Both methods provide the same access to all 23 tools.

## Setup by Client

### Claude.ai (OAuth — recommended)

1. Go to **Settings → Integrations** (or **Settings → MCP Servers**)
2. Click **Add custom integration** (or **Add MCP Server**)
3. Enter the MCP server URL: `https://aiseoengine.studio/api/mcp`
4. Click **Connect** — you'll be redirected to sign in with your AI SEO Engine account
5. Approve access on the consent screen
6. Done. The 23 AI SEO Engine tools will appear in your conversation.

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
        "Authorization": "Bearer aise_your_key_here"
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
5. Add header: `Authorization: Bearer aise_your_key_here`
6. Save and restart Cursor.

### Windsurf / Other MCP Clients

Any client supporting remote MCP servers via Streamable HTTP can connect:
- **URL**: `https://aiseoengine.studio/api/mcp`
- **Auth**: Bearer token via `Authorization` header
- **Transport**: Streamable HTTP (stateless)

## Available Tools

The MCP server exposes 23 tools — everything the CLI can do:

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
| `content_list` | List content items in a project |
| `content_create` | Create a new content item |
| `content_update` | Update a content item |
| `content_delete` | Delete content items |
| `content_bulk_import` | Bulk import content items from a list |

### Job Management

| Tool | Description |
|------|-------------|
| `jobs_start` | Start a content generation job |
| `jobs_status` | Get the status of a job |
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

## Troubleshooting

### "Authorization required" (401)
- **OAuth users (Claude.ai/ChatGPT)**: Try disconnecting and reconnecting. The OAuth token may have expired — reconnecting triggers a fresh sign-in.
- **API key users**: Verify your key starts with `aise_` and hasn't been revoked.

### "Rate limit exceeded" (429)
API keys are rate-limited (60 req/min on Starter, 120 on Team). Wait and retry.

### Tools not appearing
- Verify the URL is exactly `https://aiseoengine.studio/api/mcp`
- Check that your client supports remote MCP servers
- Try disconnecting and reconnecting

### Slow responses
MCP tools call the API internally. Most respond in under 2 seconds. Job generation (`jobs_start`, `topical_map_generate`) returns immediately with a job ID — the actual work runs in the background.

## MCP vs CLI

| Feature | MCP | CLI |
|---------|-----|-----|
| Installation | None | `npm install -g @aise/cli` |
| Auth | OAuth (web) or API key (desktop) | `AISE_API_KEY` env var |
| Interface | Natural language via AI tools | Command line |
| Best for | Chat-based workflows | Scripts and automation |
| Tools/Commands | 23 tools | 12 command groups |

Both use the same API endpoints and API key. You can use both interchangeably.

## Next Steps

- [concepts.md](./concepts.md) — Understand what each feature does
- [workflows.md](./workflows.md) — Step-by-step workflow recipes
- [CMS Publishing](../cms-skills/) — Publish generated content to WordPress, Webflow, Shopify
