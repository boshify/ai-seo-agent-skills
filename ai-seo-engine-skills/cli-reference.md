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

### `aise auth status`

Check current authentication and account info.

```bash
aise auth status --pretty
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

### `aise projects list`

List all projects you have access to.

```bash
aise projects list --pretty
```

### `aise projects create`

| Flag | Required | Description |
|------|----------|-------------|
| `--name <name>` | Yes | Project name |
| `--url <url>` | No | Root URL of the project website |
| `--tenant-id <id>` | No | Tenant ID (uses default if omitted) |

```bash
aise projects create --name "Tech Blog" --url "https://techblog.com"
```

### `aise projects update`

| Flag | Required | Description |
|------|----------|-------------|
| `--id <id>` | Yes | Project ID |
| `--name <name>` | No | New name |
| `--url <url>` | No | New root URL |

```bash
aise projects update --id proj_abc --name "Tech Blog v2"
```

### `aise projects delete`

| Flag | Required | Description |
|------|----------|-------------|
| `--id <id>` | Yes | Project ID |

```bash
aise projects delete --id proj_abc
```

---

## content

### `aise content list`

| Flag | Required | Description |
|------|----------|-------------|
| `--project <id>` | Yes | Project ID |
| `--status <status>` | No | Filter by workflow status |
| `--category <name>` | No | Filter by category |
| `--page <n>` | No | Page number (default: 1) |
| `--limit <n>` | No | Items per page (default: 50) |

```bash
aise content list --project proj_abc --status "Backlog" --pretty
```

### `aise content create`

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
aise content create --project proj_abc --keyword "best seo tools 2026" --category "Reviews"
```

### `aise content update`

| Flag | Required | Description |
|------|----------|-------------|
| `--id <id>` | Yes | Content item ID |
| `--status <status>` | No | New workflow status |
| `--category <name>` | No | New category |
| `--keyword <keyword>` | No | New keyword |
| `--slug <slug>` | No | New slug |
| `--notes <notes>` | No | New notes |

```bash
aise content update --id ci_123 --status "Production"
```

### `aise content delete`

| Flag | Required | Description |
|------|----------|-------------|
| `--id <id>` | Yes | Content item ID |

```bash
aise content delete --id ci_123
```

### `aise content import`

Bulk import content from a CSV file. CSV must have headers matching content fields (e.g., `keyword,category,contentType,workflowStatus`).

| Flag | Required | Description |
|------|----------|-------------|
| `--project <id>` | Yes | Project ID |
| `--file <path>` | Yes | Path to CSV file |

```bash
aise content import --project proj_abc --file keywords.csv
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

### `aise jobs start`

Start an AI content generation job.

| Flag | Required | Description |
|------|----------|-------------|
| `--project <id>` | Yes | Project ID |
| `--content <id>` | Yes | Content item ID |
| `--type <type>` | No | Job type (default: "content-generation") |
| `--callback-url <url>` | No | Webhook URL for completion notification |
| `--callback-secret <secret>` | No | HMAC secret for webhook signature |

```bash
aise jobs start --project proj_abc --content ci_123
```

```json
{ "jobId": "job_xyz", "status": "queued" }
```

### `aise jobs status`

Get current status of a job.

| Flag | Required | Description |
|------|----------|-------------|
| `--id <id>` | Yes | Job ID |

```bash
aise jobs status --id job_xyz --pretty
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

### `aise jobs wait`

Block until a job completes or fails. Progress is printed to stderr, final result to stdout.

| Flag | Required | Description |
|------|----------|-------------|
| `--id <id>` | Yes | Job ID |
| `--timeout <seconds>` | No | Timeout (default: 300) |
| `--interval <seconds>` | No | Poll interval (default: 5) |

```bash
aise jobs wait --id job_xyz --timeout 600
```

Exit code 0 if completed, 1 if failed or timed out.

### `aise jobs cancel`

Cancel a running or queued job.

| Flag | Required | Description |
|------|----------|-------------|
| `--id <id>` | Yes | Job ID |

```bash
aise jobs cancel --id job_xyz
```

### `aise jobs list`

List jobs for a project.

| Flag | Required | Description |
|------|----------|-------------|
| `--project <id>` | Yes | Project ID |
| `--status <status>` | No | Filter by status (queued/running/completed/failed) |

```bash
aise jobs list --project proj_abc --status running --pretty
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

### `aise categories list`

| Flag | Required | Description |
|------|----------|-------------|
| `--project <id>` | Yes | Project ID |

```bash
aise categories list --project proj_abc --pretty
```

### `aise categories create`

| Flag | Required | Description |
|------|----------|-------------|
| `--project <id>` | Yes | Project ID |
| `--name <name>` | Yes | Category name |
| `--slug <slug>` | No | Category slug |

```bash
aise categories create --project proj_abc --name "Technical SEO" --slug "technical-seo"
```

---

## config

### `aise config get`

Get project configuration (language, writing style, etc.).

| Flag | Required | Description |
|------|----------|-------------|
| `--project <id>` | Yes | Project ID |

```bash
aise config get --project proj_abc --pretty
```

### `aise config set`

Update project configuration.

| Flag | Required | Description |
|------|----------|-------------|
| `--project <id>` | Yes | Project ID |
| `--language <lang>` | No | Content language |
| `--country <country>` | No | Target country |
| `--writing-style <style>` | No | Writing style description |

```bash
aise config set --project proj_abc --language "English" --country "US" --writing-style "Professional, authoritative"
```

---

## topical-map

### `aise topical-map`

Generate a topical map (keyword cluster analysis) for a project.

| Flag | Required | Description |
|------|----------|-------------|
| `--project <id>` | Yes | Project ID |

```bash
aise topical-map --project proj_abc --pretty
```

Returns a job that generates the topical map. Use `aise jobs wait` to block until complete.

---

## content-types

### `aise content-types list`

List available content type templates.

| Flag | Required | Description |
|------|----------|-------------|
| `--project <id>` | Yes | Project ID |

```bash
aise content-types list --project proj_abc --pretty
```

---

## statuses

### `aise statuses`

List all available workflow statuses.

```bash
aise statuses --pretty
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

### `aise usage`

Show usage analytics for your tenant.

```bash
aise usage --pretty
```

---

## drive

### `aise drive folder`

Get the Google Drive folder ID for a project. Use with the [Google Workspace CLI](./google-workspace.md) for file operations.

| Flag | Required | Description |
|------|----------|-------------|
| `--project <id>` | Yes | Project ID |

```bash
aise drive folder --project proj_abc --pretty
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
