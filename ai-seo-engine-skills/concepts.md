# Concepts

What AI SEO Engine is, how its pieces fit together, and what each feature actually does. Read this before the CLI reference — it explains the *why* behind every command.

---

## The Big Picture

AI SEO Engine automates the end-to-end SEO content workflow: discover what to write, generate optimized content, and deliver it ready for publishing.

The system follows this lifecycle:

```
Project → Configure → Topical Map → Content Items → Jobs → Deliverables → CMS
```

Each stage builds on the last. An agent can run the entire pipeline programmatically, or enter at any stage with existing data.

---

## Projects

A **project** represents one website or content property. Everything in the system is scoped to a project — content items, jobs, categories, configuration, and Drive folders.

```
Project
├── Config (language, style, topical map settings)
├── Categories (topic clusters, each with its own Drive subfolder)
├── Content Items (individual pieces to write)
├── Jobs (AI generation tasks)
└── Google Drive Folder (all deliverables, organized by category)
```

When you create a project, the system automatically:
- Creates a Google Drive folder and shares it with you
- Runs an onboarding agent that attempts to fill out your project configuration (central entity, writing style, categories, etc.)
- Creates initial categories based on your site

A project's `rootUrl` (e.g., `https://techblog.com`) is used to auto-generate full URLs for every content item. If you set a root URL, each content item gets a `fullUrl` like `https://techblog.com/seo-tips/keyword-research-guide`.

**CLI:** `aiseo projects create --name "Tech Blog" --url "https://techblog.com"`

---

## Project Configuration

Configuration controls **how** AI generates content for your project. These settings are passed to the AI during every generation job.

| Setting | What It Controls | Example |
|---------|-----------------|---------|
| `language` | Language content is written in. Also affects SERP research language. | "English", "Spanish", "German" |
| `country` | Target country. Affects cultural references, spelling, and SERP research region. | "US", "UK", "DE" |
| `writingStyle` | Tone and voice of generated content | "Professional and authoritative", "Casual and conversational" |
| `writingSamples` | Example text the AI uses as a style reference | A paragraph from your best-performing article |
| `imageStyleGuide` | Detailed instructions for AI image generation. Auto-generated based on your site's visual style — logo placement, shadows, color palette, illustration style. You can customize it. | "Flat illustration style, purple brand colors, no text overlays" |
| `sourceContext` | Brand context, company info, domain expertise | "We're a B2B SaaS company focused on enterprise security" |

The system is **multilingual out of the box** — changing language and country automatically updates content language and SERP research settings.

**Topical map settings** (also part of config):

| Setting | What It Controls |
|---------|-----------------|
| `centralEntity` | The main topic your site covers (e.g., "AI SEO") |
| `centralSearchIntent` | The primary search intent (e.g., "People searching for AI-powered SEO tools") |
| `coreSectionOfTopicalMap` | Pillar topics — the broad categories |
| `outerSectionOfTopicalMap` | Supporting topics — the long-tail clusters |
| `writeToCore` / `writeToOuter` | Controls whether the backlog agent generates topics for core or outer sections |

**Automation settings** control which stages progress automatically:

```json
{
  "backlog": true,
  "backlog-review": true,
  "production": true,
  "edit": true,
  "add-images": true,
  "upload": false,
  "refresh": true,
  "refresh-review": true,
  "refreshed": true
}
```

- **All on:** Content flows through every stage without stopping — fully autonomous.
- **All off:** Every stage requires manual approval before progressing.
- **Selective:** For example, turn off `add-images` to review the edited content before image generation.

**Why it matters:** Configuration is the difference between generic AI content and content that sounds like your brand. An agent should set these before generating anything.

**CLI:** `aiseo config set --project <id> --language "English" --country "US" --writing-style "Professional"`

---

## Topical Maps

A **topical map** is an AI-generated content strategy for your project. It analyzes your central entity, core topics, and outer topics to produce:

1. **Categories** — topic clusters that organize your content (auto-created in the system)
2. **Keyword suggestions** — specific keywords to target within each category
3. **Content structure** — how topics relate to each other

Think of it as the AI answering: *"If I were building this site from scratch to dominate search, what would I write and how would I organize it?"*

**How it works:**
1. You configure the project's central entity and topic sections
2. The topical map job sends this to the AI
3. The AI returns a structured content plan
4. Categories are auto-created in your project
5. Content items are created in "Backlog" status with recommended keywords

**The topical map view** in the web UI provides a visual representation of all your content organized by category. Topics within each category are sorted from highest to lowest search volume. Color-coded dots indicate the workflow status of each topic, and green/red bars show search volume vs keyword difficulty.

**CLI:** `aiseo topical-map --project <id>` → returns a jobId (this is a long-running job — use `aiseo jobs wait`)

---

## Categories

**Categories** are topic clusters that organize content items within a project. They serve three purposes:

1. **Content organization** — group related keywords together (e.g., "Technical SEO", "Content Strategy")
2. **URL structure** — category slugs become URL path segments (`/technical-seo/core-web-vitals-guide`). Slugs are optional — without one, content URLs are just `rootUrl/content-slug`.
3. **Drive organization** — each category gets its own Google Drive subfolder for deliverables

Categories can be:
- **Auto-generated** by the onboarding agent when a project is created
- **Auto-generated** by a topical map job
- **Manually created** via the CLI or web UI
- **Imported** from a CSV during bulk content import

Deleting a category gives you the option to leave content items uncategorized or migrate them to a different category.

**CLI:** `aiseo categories create --project <id> --name "Technical SEO"`

---

## Content Items

A **content item** is a single piece of content you want to create — one keyword, one article. It tracks the entire lifecycle from idea to published page.

**Key fields:**

| Field | Purpose |
|-------|---------|
| `keyword` | The target search keyword (e.g., "best seo tools 2026") |
| `name` | Display name (defaults to keyword if not set) |
| `slug` | URL slug, auto-generated from keyword (e.g., "best-seo-tools-2026") |
| `workflowStatus` | Current stage in the pipeline (see Workflow Statuses below) |
| `category` | Topic cluster this belongs to |
| `contentType` | Template to use for generation (see Content Types below) |
| `fullUrl` | Auto-generated: `rootUrl` + category slug + content slug |
| `searchVolume` | Monthly search volume (auto-populated by DataForSEO) |
| `keywordDifficulty` | Keyword difficulty score 0-100 (auto-populated by DataForSEO) |
| `searchIntent` | Search intent classification (auto-populated) |
| `pageTitle` | SEO page title (auto-populated during generation) |

**The minimum required fields** to create a content item are: `name`, `keyword`, and `slug`. The CLI auto-generates `name` and `slug` from the keyword if you don't provide them.

**What happens when you create one:** The content item starts in "Backlog" status. It doesn't generate anything yet — it's a placeholder in your content plan. To generate content, you start a **job** for it.

**Importing content:** You can import from CSV, Excel, or use the web UI field mapper. You can upload keyword research directly from tools like Ahrefs, SEMrush, etc. and map the columns to content item fields.

**Exporting content:** Export all content or just the current filtered view as CSV, Excel, or XML.

**CLI:** `aiseo content create --project <id> --keyword "best seo tools 2026" --category "Reviews"`

---

## Content Types

A **content type** is a template that tells the AI *how* to structure a piece of content. Each content type has an **outline in markdown** that defines the sections, headings, and structure the AI should follow.

Examples of built-in content types:
- **Blog Post** — intro, main sections with H2s, conclusion, FAQ
- **Tutorial** — step-by-step guide with numbered sections
- **Listicle** — ranked list format with individual item sections
- **Product Review** — pros/cons, features, comparison, verdict
- **Checklist** — actionable checklist format
- And more (the system ships with ~15 content types out of the box)

**How they work:**
- Content types have an `outlineMarkdown` field — a markdown template the AI follows during generation
- **Global types** are available to all projects (system defaults). You can modify them per project (creates a project-specific override), and reset to default anytime.
- **Custom types** can be created for project-specific content structures
- When a job runs, the selected content type's outline is sent to the AI along with the keyword and config

**Why it matters:** Content types ensure consistency across your content. Every "Tutorial" follows the same structure, every "Product Review" has the same sections. This is especially important for agents running bulk generation — the output is predictable.

**CLI:** `aiseo content-types list --project <id>` → see available templates

---

## Workflow Statuses

Every content item has a **workflow status** that tracks where it is in the pipeline. Each status has its own AI agent with a specific purpose. **The behavior of "generate" changes completely based on the current status.**

### Primary Flow (New Content)

```
Backlog → Backlog Review → Production → Edit → Add Images → Upload → Live
```

| Status | What the AI Does When You Generate | Deliverables |
|--------|-----------------------------------|-------------|
| **Backlog** | **Keyword research.** Rewrites the item's fields (name, keyword, slug, notes) based on research. Use this for unconfirmed topic ideas. **Warning:** Generating in Backlog will overwrite your fields — don't use it for content you've already decided on. | Updated fields |
| **Backlog Review** | **Cannibalization check.** Checks your sitemaps and existing content for conflicts. If it finds a cannibalization issue, it automatically changes the topic and fields to avoid conflict. **Warning:** Same as Backlog — fields may be rewritten. | Updated fields, conflict report |
| **Production** | **Content generation.** Creates the content brief (outline), first draft, and internal linking sheet. This is the main generation stage. The first draft is comprehensive but tends to be wordy. | Content brief, Draft, Internal linking sheet |
| **Edit** | **Content refinement.** Cleans up the draft into a polished edited version. Better formatting, more concise, lower word count. Also adds `[IMAGE: description]` placement markers for the Add Images stage. | Edited document |
| **Add Images** | **Image generation.** Creates a featured image, custom charts, infographics, and in-page images based on the content brief. Images are on-brand using your image style guide. | Featured image, in-page images, charts, infographics |
| **Upload** | No generation. Holding stage for content ready to be uploaded to your website. | — |
| **Live** | **Full rewrite.** Sends the item back to Production for a complete rewrite. Use this for existing content you want to regenerate from scratch. | Same as Production |

### Refresh Flow (Updating Existing Content)

```
Refresh → Refresh Review → Refreshed
```

| Status | What the AI Does When You Generate | Deliverables |
|--------|-----------------------------------|-------------|
| **Refresh** | **New section generation.** Does SERP research for your keyword, compares top-ranking pages against your existing content, and generates new sections for topics you're missing. Does NOT modify existing sections — only adds new ones. New sections are labeled `[NEW SECTION]` in the document. | Refresh report with existing content + new sections, updated metadata |
| **Refresh Review** | **Content editor for refreshed content.** Edits ALL content (existing + new sections). Use this if you want the editor to clean up everything. Skip this if you want existing content to remain word-for-word. | Edited refreshed document |
| **Refreshed** | **Another refresh cycle** if you generate again. This is a completed state for refreshed content, separate from "Live" for tracking purposes. | Same as Refresh |

### How Refresh Finds Your Content

The refresh agent looks for content in this order:
1. The edited document in your Drive folder
2. The draft document
3. The content brief
4. **Crawls the live page URL** to extract content

Because it can crawl live pages, you can import existing URLs, set them to "Refresh" status, and refresh content without needing any documents in Drive.

### Key Rules for Agents

- **Importing decided keywords?** Set status to `"Production"` — never `"Backlog"` or `"Backlog Review"` (they will rewrite your fields)
- **Importing for review?** Set status to `"Backlog"` — the AI will research and refine them
- **Refreshing existing content?** Set status to `"Refresh"` and generate
- **Full rewrite of existing content?** Set status to `"Live"` and generate (sends it back through Production)
- **Moving backward:** You can move a content item back to any stage and regenerate (e.g., move back to "Add Images" to regenerate images)

**CLI:** `aiseo statuses` → see all available statuses

---

## Jobs

A **job** is a background AI task. When you start a job for a content item, the system:

1. Creates a job record with status `queued`
2. Checks rate limits (see below)
3. If a slot is available, dispatches the job to the AI processing system
4. The AI generates content based on the keyword, config, content type, and current workflow status
5. Deliverables are saved to Google Drive
6. The job status updates to `completed` or `failed`
7. If automation is enabled, the content item automatically moves to the next status and a new job starts

### Two-Track System

Jobs run on two parallel tracks to balance throughput:

**Backlog Track** — For content items in "Backlog" status:
- **1 job at a time per project** (serialized)
- Exempt from the tenant's concurrent job limit
- Designed for slow, exploratory keyword research tasks

**Non-Backlog Track** — For everything else (Production, Edit, Add Images, etc.):
- Uses the tenant's `concurrentJobLimit` (default 3, up to 10 on Team plan)
- Multiple jobs can run simultaneously across the tenant
- Designed for faster generation tasks

**Why two tracks?** This prevents a large backlog import from blocking your production pipeline. You can have 50 backlog items processing one-by-one while simultaneously generating 3 production articles.

### Job Types

| Type | What It Does |
|------|-------------|
| `content-generation` | Generates content for a content item based on its current workflow status |
| `new-topical-map` | Generates a topical map for the project (no content item required) |

### Webhook Callbacks

Jobs support optional webhook callbacks for async workflows:

```bash
aiseo jobs start --project <id> --content <id> \
  --callback-url "https://your-server.com/webhook" \
  --callback-secret "your_hmac_secret"
```

When the job completes, a POST is sent to your URL with the job result and an HMAC signature for verification.

**CLI:**
```bash
aiseo jobs start --project <id> --content <id>    # Start generation
aiseo jobs status --id <jobId>                     # Check progress
aiseo jobs wait --id <jobId> --timeout 600         # Block until done
aiseo jobs list --project <id> --status running    # List active jobs
aiseo jobs cancel --id <jobId>                     # Cancel a job
```

---

## Google Drive Deliverables

Every project has a **Google Drive folder** where AI-generated deliverables are stored. The folder is organized by category subfolders, and every content item gets its own subfolder within its category.

### Folder Structure

```
Project Drive Folder/
├── Technical SEO/                    (category subfolder)
│   ├── core-web-vitals-guide/       (content item subfolder)
│   │   ├── Content Brief            (Google Doc — outline)
│   │   ├── Draft                    (Google Doc — first draft)
│   │   ├── Edited                   (Google Doc — refined final)
│   │   ├── Internal Linking Sheet   (Google Spreadsheet)
│   │   ├── Featured Image           (PNG/JPG)
│   │   ├── Chart - Performance...   (PNG — data visualization)
│   │   └── Infographic - ...        (PNG — visual summary)
│   └── schema-markup-guide/
│       └── ...
└── Content Strategy/
    └── ...
```

### What Each Deliverable Is

| Deliverable | Format | Stage | Purpose |
|-------------|--------|-------|---------|
| **Content Brief** | Google Doc | Production | Outline of what goes into the page — sections, headings, CTAs, FAQs, recommended visual assets. Referenced by other stages. |
| **Draft** | Google Doc | Production | First attempt at the full article. Comprehensive but tends to be wordy with loose formatting. Contains all essential information from the brief. |
| **Edited** | Google Doc | Edit | Refined version of the draft. Better formatting, more concise, lower word count. Includes `[IMAGE: description]` markers showing where to place images. |
| **Internal Linking Sheet** | Google Spreadsheet | Production | Recommendations for adding internal links from existing pages to this new content. Sorted by relevance with "text before" and "text after" context. |
| **Featured Image** | Image file | Add Images | Hero/thumbnail image, on-brand with your site's style guide. |
| **Charts & Infographics** | Image files | Add Images | Data visualizations and visual summaries generated from the content brief's recommended visual assets. |
| **Refresh Report** | Google Doc | Refresh | Existing content + new sections labeled `[NEW SECTION]`, plus updated metadata (titles, descriptions, FAQs, schema). |

### How to Access

1. Get the project's Drive folder ID: `aiseo drive folder --project <id>`
2. Use the [Google Workspace CLI (`gws`)](https://github.com/googleworkspace/cli) for all file operations:
   ```bash
   # List files in the project folder
   gws drive files list --params '{"q": "\"FOLDER_ID\" in parents"}'

   # Download edited article as HTML
   gws drive files export --params '{"fileId": "DOC_ID"}' --download text/html > article.html

   # Download a generated image
   gws drive files get --params '{"fileId": "IMG_ID"}' --download > featured.jpg

   # Read internal linking spreadsheet
   gws sheets +read --spreadsheet-id "SHEET_ID" --range "Sheet1!A1:Z"
   ```

See [google-workspace.md](./google-workspace.md) for complete recipes.

---

## Tenants and Access

A **tenant** is a workspace — the top-level container for all projects, users, and billing. Every API key is scoped to one tenant.

| Tier | Projects | Seats | Concurrent Jobs | Rate Limit |
|------|----------|-------|----------------|------------|
| **Starter** | 1 | 1 | 3 | 60 req/min |
| **Team** | 10 | 5 | 10 | 120 req/min |

**Seats** give users access to the project and its Google Drive folders. Adding a seat automatically shares the Drive folder.

**Why it matters for agents:** The concurrent job limit determines how many generation jobs can run simultaneously. If you start 5 jobs on a Starter plan, 3 will run and 2 will queue. The system automatically dispatches queued jobs as slots open.

---

## Prompt Overrides

**Prompt overrides** let you customize the AI's system prompt for specific workflow statuses. For example, you might want:
- A research-focused prompt for "Backlog" processing
- A more creative prompt for "Production" writing
- A concise editing prompt for "Edit" refinement
- Additional instructions for image generation in "Add Images"

Each override specifies:
- A **name** (for your reference)
- A **system prompt** (the actual instructions)
- **Which stages** it applies to (one or more workflow statuses)

The override prompt is automatically injected into the AI's context for every job that runs in the specified stages. This allows deep customization of every step in the pipeline without modifying the core system.

---

## The Full Pipeline

Here's how everything fits together for an agent running the complete workflow:

```
1. Create project          → aiseo projects create --name "Tech Blog" --url "https://..."
                             (Drive folder auto-created, onboarding agent fills config)

2. Configure (optional)    → aiseo config set --project <id> --language "English" --writing-style "..."
                             (Customize language, style, image guide, topical map settings)

3. Generate topical map    → aiseo topical-map --project <id>
                           → aiseo jobs wait --id <jobId>
                             (Categories auto-created, content items created in Backlog)

4. Create content items    → aiseo content create --project <id> --keyword "..." --category "..."
   OR bulk import          → aiseo content import --project <id> --file keywords.csv
                             (Use status "Production" for decided keywords,
                              "Backlog" only if you want AI to research/refine them)

5. Start generation jobs   → aiseo jobs start --project <id> --content <id>
                           → aiseo jobs wait --id <jobId>
                             (If automation is on, it flows through all stages automatically.
                              If off, you start a job at each stage manually.)

6. Get deliverables        → aiseo drive folder --project <id>
                           → gws drive files export ... > article.html
                           → gws drive files get ... > featured.jpg
                           → gws sheets +read ... (internal linking data)

7. Publish to CMS          → (See CMS skills: WordPress, Webflow, Shopify)
```

Each step is independent — an agent can enter at any point. If you already have keywords, skip the topical map. If content is already generated, skip to step 6.

### Automation vs Manual Control

With **all automation on**, steps 3-5 are hands-free: generate a topical map → content flows through Backlog → Backlog Review → Production → Edit → Add Images → Upload automatically. You just wait and collect deliverables.

With **automation off**, you control each transition: generate at each stage, review the output, then move to the next stage and generate again.

---

## Key Relationships

```
Tenant (workspace)
└── Project (website)
    ├── ProjectConfig (1:1 — generation settings, automation flags)
    ├── Category[] (topic clusters, each with Drive subfolder)
    ├── ContentType[] (outline templates, project overrides global)
    ├── PromptOverride[] (custom AI prompts per status)
    ├── ContentItem[] (individual articles)
    │   ├── keyword, slug, fullUrl, searchVolume, keywordDifficulty
    │   ├── workflowStatus → determines what "generate" does
    │   ├── category → Category.name (affects URL + Drive folder)
    │   ├── contentType → ContentType.name (affects outline structure)
    │   └── Job[] (generation tasks, one per stage transition)
    └── Google Drive Folder
        ├── Category Subfolders/
        │   └── Content Item Subfolders/
        │       ├── Content Brief, Draft, Edited (Google Docs)
        │       ├── Internal Linking Sheet (Spreadsheet)
        │       └── Images (Featured, Charts, Infographics)
        └── (organized automatically by the system)
```

---

## Next Steps

- [setup.md](./setup.md) — Install the CLI and get your API key
- [cli-reference.md](./cli-reference.md) — Full command syntax and examples
- [workflows.md](./workflows.md) — Step-by-step recipes for common tasks
- [google-workspace.md](./google-workspace.md) — Accessing deliverables from Google Drive
