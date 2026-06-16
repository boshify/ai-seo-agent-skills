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
| `--name <name>` | No | Content name (defaults to keyword) |
| `--status <status>` | No | Workflow status (default: "Backlog") |
| `--category <name>` | No | Category name |
| `--content-type <type>` | No | Content type name |
| `--slug <slug>` | No | URL slug |
| `--notes <notes>` | No | Notes |
| `--new-or-existing <value>` | No | `Existing` or `New` (defaults to `New` when omitted) |
| `--clearscope-link <url>` | No | Clearscope report URL |
| `--four-p-link <url>` | No | 4P doc URL |
| `--content-brief-link <url>` | No | Content Brief sheet URL |
| `--content-doc-url <url>` | No | Generated content Google Doc URL |
| `--final-article-url <url>` | No | Final article URL (the "Recommended URL") |
| `--drive-folder-url <url>` | No | Drive folder URL for this item |
| `--recommended-url <url>` | No | Alias for `--final-article-url`. "Recommended URL" in Asana IS the Final Article URL — mapped to `finalArticleUrl` before forwarding. Explicit `--final-article-url` wins if both are set. |

```bash
aiseo content create --project proj_abc --keyword "best seo tools 2026" --category "Reviews"
```

Ingesting from an external system (e.g. Asana) with the per-stage URLs already populated:

```bash
aiseo content create \
  --project proj_abc \
  --keyword "online poker real money" \
  --new-or-existing Existing \
  --clearscope-link "https://app.clearscope.io/.../report/..." \
  --recommended-url "https://example.com/online-poker-real-money/"
```

### `aiseo content update`

| Flag | Required | Description |
|------|----------|-------------|
| `--id <id>` | Yes | Content item ID |
| `--status <status>` | No | New workflow status |
| `--category <name>` | No | New category |
| `--keyword <keyword>` | No | New keyword |
| `--name <name>` | No | New name |
| `--slug <slug>` | No | New slug |
| `--notes <notes>` | No | New notes |
| `--new-or-existing <value>` | No | `Existing` or `New` |
| `--clearscope-link <url>` | No | Clearscope report URL |
| `--four-p-link <url>` | No | 4P doc URL |
| `--content-brief-link <url>` | No | Content Brief sheet URL |
| `--content-doc-url <url>` | No | Generated content Google Doc URL |
| `--final-article-url <url>` | No | Final article URL (the "Recommended URL") |
| `--drive-folder-url <url>` | No | Drive folder URL for this item |
| `--recommended-url <url>` | No | Alias for `--final-article-url`. Maps to `finalArticleUrl` before forwarding. |

```bash
aiseo content update --id ci_123 --status "Production"
aiseo content update --id ci_123 --new-or-existing Existing --clearscope-link "https://app.clearscope.io/..."
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
| `--industry <industry>` | Industry name (must match a row in /app/industry-style-guides) |
| `--writing-style <style>` | Writing style/tone instructions |
| `--writing-samples <samples>` | Voice / style rules the writers and editors apply throughout the article |
| `--global-problem <text>` | **(4Ps: Problem)** Project-wide pain points the brand addresses |
| `--global-promise <text>` | **(4Ps: Promise)** Project-wide benefits, offers, and CTAs |
| `--global-proof <text>` | **(4Ps: Proof)** Project-wide trust signals (awards, certifications, social proof) |
| `--global-proposition <text>` | **(4Ps: Proposition)** Project-wide proposition / positioning statement |
| `--global-pain-points <text>` | DEPRECATED alias for `--global-problem`. Server still accepts it; prefer the new name. |
| `--global-benefits-offers-ctas <text>` | DEPRECATED alias for `--global-promise`. |
| `--global-trust-elements <text>` | DEPRECATED alias for `--global-proof`. |
| `--image-style-guide <guide>` | Guidelines for AI image generation |
| `--source-context <context>` | Background info about the brand/product |
| `--central-entity <entity>` | Central entity/brand name for topical authority |
| `--central-search-intent <intent>` | Core search intent the strategy targets |
| `--core-section <section>` | Core section of the topical map |
| `--outer-section <section>` | Outer section of the topical map |
| `--write-to-core <bool>` | Enable writing to core section (true/false) |
| `--write-to-outer <bool>` | Enable writing to outer section (true/false) |
| `--word-count-minimum <n>` | Per-client minimum article word count (overrides the global floor) |
| `--word-count-maximum <n>` | Per-client maximum article word count (overrides the global ceiling) |
| `--automation-settings <json>` | Automation settings as JSON string |

**4Ps order is Problem → Promise → Proof → Proposition.** That's the order the operator-facing /app/config UI displays the fields, and the order they appear in the agent context blocks. The old `--global-trust-elements` / `--global-benefits-offers-ctas` / `--global-pain-points` flags map transparently to their new names server-side for one release; new automations should use the canonical names.

**Examples:**
```bash
# Set 4Ps for a project
aiseo config set --project proj_abc \
  --global-problem "Players hate slow withdrawals and unclear bonus terms" \
  --global-promise "Same-day crypto payouts; bonus terms shown before opt-in" \
  --global-proof "Trustpilot 4.2 / 11,891 reviews; 35+ years of operation; segregated player funds" \
  --global-proposition "The fastest, most transparent online casino for US players"

# Read current 4Ps
aiseo config get --project proj_abc --field globalProof
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

---

## prompts

Tenant-scoped editorial prompts the workflow runners load at runtime. Two row kinds:

- **Core prompts** (`isCore=true`, `kind=core`): wired into the runners by stable `key` (e.g. `cg.writer-hard-rules`). Body / description / sortOrder are editable. Name / key / section / kind / isCore / injectionPoint are immutable. Cannot be deleted — wipe the body to empty string (`--prompt ''`) to fall back to the registry default.
- **Custom prompts** (`isCore=false`, `kind=custom`): user-added. Full CRUD. Must declare an `injectionPoint` enum value naming where the runner appends the body.

### `aiseo prompts list`

| Flag | Required | Description |
|------|----------|-------------|
| `--section <section>` | No | Filter by section: `4P`, `CB`, `CG`, `Global` |
| `--kind <kind>` | No | Filter by kind: `core`, `custom` |
| `--slim` | No | Drop the `systemPrompt` body from each row (keep metadata only). Recommended for inspecting many rows at once. |

```bash
# All prompts, full bodies
aiseo prompts list --pretty

# Metadata only — see which prompts exist, their keys, and char counts
aiseo prompts list --slim --pretty

# Just the custom rows in CG
aiseo prompts list --section CG --kind custom --slim
```

### `aiseo prompts get`

Fetch one prompt's full body. Look up by `--id` OR `--key` (exactly one).

| Flag | Required | Description |
|------|----------|-------------|
| `--id <id>` | One of | Prompt cuid |
| `--key <key>` | One of | Stable slug (e.g. `cg.writer-hard-rules`) |

```bash
aiseo prompts get --key cg.writer-hard-rules --pretty

# Pipe just the body to a file
aiseo prompts get --key cg.writer-hard-rules --field systemPrompt > writer-hard-rules.txt
```

### `aiseo prompts create`

Create a custom prompt. The API enforces `kind=custom`; core prompts are seeded from the in-code registry, not via this tool.

| Flag | Required | Description |
|------|----------|-------------|
| `--section <section>` | Yes | `4P`, `CB`, `CG`, or `Global` |
| `--name <name>` | Yes | Display name shown in the UI |
| `--prompt <body>` | Yes | The body text the runner will append at the injection point |
| `--injection-point <point>` | Yes | One of: `4p.all-agents`, `cb.outline.extras`, `cb.qa.extras`, `cb.writer-instructions.extras`, `cb.brief-sections.extras`, `cg.writer.extras`, `cg.section-editor.extras`, `cg.surgical-edit.extras` |
| `--description <description>` | No | One-line operator hint |
| `--key <key>` | No | Override auto-derived slug. Immutable once set. |
| `--sort-order <n>` | No | UI ordering (integer; smaller numbers appear first) |

```bash
aiseo prompts create \
  --section CG \
  --name "BetOnline domain casing" \
  --prompt "Always write 'BetOnline.ag' with that exact casing, never 'betonline.ag' or 'BetOnline'." \
  --injection-point cg.writer.extras \
  --description "Brand-name casing rule for the BetOnline project"
```

### `aiseo prompts update`

Partial update by id. Send only the fields you want to change. Body changes are versioned (audit-trail) via the existing capture pipeline — pass `--note` to annotate.

| Flag | Required | Description |
|------|----------|-------------|
| `--id <id>` | Yes | Prompt cuid |
| `--prompt <body>` | No | New system prompt body |
| `--description <description>` | No | New one-line description (`""` clears) |
| `--sort-order <n>` | No | New UI sort order |
| `--name <name>` | No | New display name (rejected on core rows) |
| `--section <section>` | No | New section (rejected on core rows) |
| `--injection-point <point>` | No | New injection point (rejected on core rows) |
| `--note <note>` | No | Audit note attached to the version capture |

```bash
# Edit a core prompt's body
aiseo prompts update --id cm1234... --prompt "$(cat new-writer-hard-rules.txt)" \
  --note "Tightened the em-dash language after editorial feedback"

# Disable a core rule (runner falls back to registry default + logs a warning)
aiseo prompts update --id cm1234... --prompt "" --note "Disabled while tuning"

# Rename a custom prompt
aiseo prompts update --id cm5678... --name "Cleopatra slot variants"
```

### `aiseo prompts delete`

Delete a custom prompt. Core prompts reject delete — to disable a core prompt, `update --prompt ''` instead and the runner falls back to the registry default.

| Flag | Required | Description |
|------|----------|-------------|
| `--id <id>` | Yes | Prompt cuid |

```bash
aiseo prompts delete --id cm5678...
```
