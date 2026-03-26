# CLI Reference

Complete command reference for the AI SEO Engine CLI. All commands output JSON by default. Add `--pretty` for formatted output.

## Global Options

| Flag | Description |
|------|-------------|
| `--pretty` | Pretty-print JSON output |
| `-V, --version` | Show version number |
| `-h, --help` | Show help |

---

## auth

### `aiseo auth status`

Check current authentication and account info.

```bash
aiseo auth status --pretty
```

```json
{
  "id": "user_abc",
  "email": "you@example.com",
  "name": "Your Name",
  "tenants": [{ "id": "t_1", "name": "My Workspace", "tier": "TEAM", "role": "OWNER" }]
}
```

---

## projects

### `aiseo projects list`

List all projects you have access to.

```bash
aiseo projects list --pretty
```

### `aiseo projects create`

| Flag | Required | Description |
|------|----------|-------------|
| `--name <name>` | Yes | Project name |
| `--url <url>` | No | Root URL of the project website |
| `--tenant-id <id>` | No | Tenant ID (uses default if omitted) |

```bash
aiseo projects create --name "Tech Blog" --url "https://techblog.com"
```

### `aiseo projects update`

| Flag | Required | Description |
|------|----------|-------------|
| `--id <id>` | Yes | Project ID |
| `--name <name>` | No | New name |
| `--url <url>` | No | New root URL |

```bash
aiseo projects update --id proj_abc --name "Tech Blog v2"
```

### `aiseo projects delete`

| Flag | Required | Description |
|------|----------|-------------|
| `--id <id>` | Yes | Project ID |

```bash
aiseo projects delete --id proj_abc
```

---

## content

### `aiseo content list`

| Flag | Required | Description |
|------|----------|-------------|
| `--project <id>` | Yes | Project ID |
| `--status <status>` | No | Filter by workflow status |
| `--category <name>` | No | Filter by category |
| `--page <n>` | No | Page number (default: 1) |
| `--limit <n>` | No | Items per page (default: 50) |

```bash
aiseo content list --project proj_abc --status "Backlog" --pretty
```

### `aiseo content create`

| Flag | Required | Description |
|------|----------|-------------|
| `--project <id>` | Yes | Project ID |
| `--keyword <keyword>` | Yes | Target keyword |
| `--status <status>` | No | Workflow status (default: "backlog") |
| `--category <name>` | No | Category name |
| `--content-type <type>` | No | Content type name |
| `--slug <slug>` | No | URL slug |
| `--notes <notes>` | No | Notes |

```bash
aiseo content create --project proj_abc --keyword "best seo tools 2026" --category "Reviews"
```

### `aiseo content update`

| Flag | Required | Description |
|------|----------|-------------|
| `--id <id>` | Yes | Content item ID |
| `--status <status>` | No | New workflow status |
| `--category <name>` | No | New category |
| `--keyword <keyword>` | No | New keyword |
| `--slug <slug>` | No | New slug |
| `--notes <notes>` | No | New notes |

```bash
aiseo content update --id ci_123 --status "Production"
```

### `aiseo content delete`

| Flag | Required | Description |
|------|----------|-------------|
| `--id <id>` | Yes | Content item ID |

```bash
aiseo content delete --id ci_123
```

### `aiseo content import`

Bulk import content from a CSV file. CSV must have headers matching content fields (e.g., `keyword,category,contentType,workflowStatus`).

| Flag | Required | Description |
|------|----------|-------------|
| `--project <id>` | Yes | Project ID |
| `--file <path>` | Yes | Path to CSV file |

```bash
aiseo content import --project proj_abc --file keywords.csv
```

Example CSV:
```csv
keyword,category,contentType
best seo tools,Reviews,Blog Post
how to do keyword research,Guides,Tutorial
seo checklist 2026,Resources,Checklist
```

---

## jobs

### `aiseo jobs start`

Start an AI content generation job.

| Flag | Required | Description |
|------|----------|-------------|
| `--project <id>` | Yes | Project ID |
| `--content <id>` | Yes | Content item ID |
| `--type <type>` | No | Job type (default: "content-generation") |
| `--callback-url <url>` | No | Webhook URL for completion notification |
| `--callback-secret <secret>` | No | HMAC secret for webhook signature |

```bash
aiseo jobs start --project proj_abc --content ci_123
```

```json
{ "jobId": "job_xyz", "status": "queued" }
```

### `aiseo jobs status`

Get current status of a job.

| Flag | Required | Description |
|------|----------|-------------|
| `--id <id>` | Yes | Job ID |

```bash
aiseo jobs status --id job_xyz --pretty
```

```json
{
  "id": "job_xyz",
  "status": "running",
  "displayText": "Generating outline...",
  "type": "content-generation",
  "startedAt": "2026-03-16T10:00:00Z"
}
```

### `aiseo jobs wait`

Block until a job completes or fails. Progress is printed to stderr, final result to stdout.

| Flag | Required | Description |
|------|----------|-------------|
| `--id <id>` | Yes | Job ID |
| `--timeout <seconds>` | No | Timeout (default: 300) |
| `--interval <seconds>` | No | Poll interval (default: 5) |

```bash
aiseo jobs wait --id job_xyz --timeout 600
```

Exit code 0 if completed, 1 if failed or timed out.

### `aiseo jobs cancel`

Cancel a running or queued job.

| Flag | Required | Description |
|------|----------|-------------|
| `--id <id>` | Yes | Job ID |

```bash
aiseo jobs cancel --id job_xyz
```

### `aiseo jobs list`

List jobs for a project.

| Flag | Required | Description |
|------|----------|-------------|
| `--project <id>` | Yes | Project ID |
| `--status <status>` | No | Filter by status (queued/running/completed/failed) |

```bash
aiseo jobs list --project proj_abc --status running --pretty
```

```json
{
  "jobs": [
    {
      "id": "job_xyz",
      "type": "content-generation",
      "status": "running",
      "displayText": "Generating outline...",
      "contentItemId": "ci_123",
      "startedAt": "2026-03-16T10:00:00Z",
      "createdAt": "2026-03-16T09:59:55Z"
    }
  ]
}
```

---

## categories

### `aiseo categories list`

| Flag | Required | Description |
|------|----------|-------------|
| `--project <id>` | Yes | Project ID |

```bash
aiseo categories list --project proj_abc --pretty
```

### `aiseo categories create`

| Flag | Required | Description |
|------|----------|-------------|
| `--project <id>` | Yes | Project ID |
| `--name <name>` | Yes | Category name |
| `--slug <slug>` | No | Category slug |

```bash
aiseo categories create --project proj_abc --name "Technical SEO" --slug "technical-seo"
```

---

## config

### `aiseo config get`

Get project configuration (language, writing style, etc.).

| Flag | Required | Description |
|------|----------|-------------|
| `--project <id>` | Yes | Project ID |

```bash
aiseo config get --project proj_abc --pretty
```

### `aiseo config set`

Update project configuration. Only pass fields you want to change.

| Option | Description |
|--------|-------------|
| `--project <projectId>` | **(required)** Project ID |
| `--language <language>` | Content language (e.g. "English") |
| `--country <country>` | Target country (e.g. "United States") |
| `--writing-style <style>` | Writing style/tone instructions |
| `--writing-samples <samples>` | Example text to match writing style |
| `--image-style-guide <guide>` | Guidelines for AI image generation |
| `--source-context <context>` | Background info about the brand/product |
| `--central-entity <entity>` | Central entity/brand name for topical authority |
| `--central-search-intent <intent>` | Core search intent the strategy targets |
| `--core-section <section>` | Core section of the topical map |
| `--outer-section <section>` | Outer section of the topical map |
| `--write-to-core <bool>` | Enable writing to core section (true/false) |
| `--write-to-outer <bool>` | Enable writing to outer section (true/false) |
| `--automation-settings <json>` | Automation settings as JSON string |

**Examples:**
```bash
# Set brand context
aiseo config set --project proj_abc --central-entity "Acme Corp" --source-context "Leading provider of widgets since 1990"

# Set writing style with samples
aiseo config set --project proj_abc --writing-style "Professional, authoritative" --writing-samples "We believe in quality..."

# Set topical map sections
aiseo config set --project proj_abc --core-section "Widgets" --outer-section "Industrial Equipment"
```

---

## topical-map

### `aiseo topical-map`

Generate a topical map (keyword cluster analysis) for a project.

| Flag | Required | Description |
|------|----------|-------------|
| `--project <id>` | Yes | Project ID |

```bash
aiseo topical-map --project proj_abc --pretty
```

Returns a job that generates the topical map. Use `aiseo jobs wait` to block until complete.

---

## content-types

### `aiseo content-types list`

List available content type templates.

| Flag | Required | Description |
|------|----------|-------------|
| `--project <id>` | Yes | Project ID |

```bash
aiseo content-types list --project proj_abc --pretty
```

---

## statuses

### `aiseo statuses`

List all available workflow statuses.

```bash
aiseo statuses --pretty
```

```json
[
  { "name": "Backlog", "order": 1 },
  { "name": "Production", "order": 3 },
  { "name": "Live", "order": 10 }
]
```

---

## usage

### `aiseo usage`

Show usage analytics for your tenant.

```bash
aiseo usage --pretty
```

---

## drive

### `aiseo drive folder`

Get the Google Drive folder ID for a project. Use with the [Google Workspace CLI](./google-workspace.md) for file operations.

| Flag | Required | Description |
|------|----------|-------------|
| `--project <id>` | Yes | Project ID |

```bash
aiseo drive folder --project proj_abc --pretty
```

```json
{
  "projectId": "proj_abc",
  "projectName": "Tech Blog",
  "folderId": "1ABC_drivefolderid",
  "folderUrl": "https://drive.google.com/drive/folders/1ABC_drivefolderid"
}
```

Then use `gws` for file operations:
```bash
gws drive files list --params '{"q": "\"1ABC_drivefolderid\" in parents"}'
```
