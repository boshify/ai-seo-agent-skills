# Google Workspace Integration

AI SEO Engine delivers content to Google Drive folders. Use the [Google Workspace CLI (`gws`)](https://github.com/googleworkspace/cli) to access files — docs, images, spreadsheets — from those folders.

## Setup

```bash
# Install
npm install -g @googleworkspace/cli

# Authenticate (interactive)
gws auth setup

# Verify
gws drive about get --params '{"fields": "user"}'
```

## Workflow

1. Get the project's Drive folder ID with `aiseo`
2. Use `gws` for all file operations

```bash
# Step 1: Get folder ID
FOLDER_ID=$(aiseo drive folder --project proj_abc | jq -r '.folderId')

# Step 2: List files in the folder
gws drive files list --params "{
  \"q\": \"'${FOLDER_ID}' in parents and trashed = false\",
  \"fields\": \"files(id,name,mimeType,modifiedTime)\"
}"
```

## Common Recipes

### List all files in a project folder

```bash
FOLDER_ID=$(aiseo drive folder --project proj_abc | jq -r '.folderId')

gws drive files list --params "{
  \"q\": \"'${FOLDER_ID}' in parents and trashed = false\",
  \"fields\": \"files(id,name,mimeType,modifiedTime,size)\"
}" | jq '.files[]'
```

### Download a Google Doc as HTML

```bash
# Get the file ID from the list above
gws drive files export \
  --params '{"fileId": "YOUR_DOC_ID"}' \
  --download text/html > article.html
```

### Download a Google Doc as plain text

```bash
gws drive files export \
  --params '{"fileId": "YOUR_DOC_ID"}' \
  --download text/plain > article.txt
```

### Download an image

```bash
# Images are regular files, not Google Docs — use get, not export
gws drive files get \
  --params '{"fileId": "YOUR_IMAGE_ID"}' \
  --download > image.jpg
```

### Read a spreadsheet (internal linking recommendations)

```bash
# Get spreadsheet ID from the file list (mimeType: application/vnd.google-apps.spreadsheet)
gws sheets +read \
  --spreadsheet-id "YOUR_SHEET_ID" \
  --range "Sheet1!A1:Z"
```

Output is JSON with rows and columns. Parse with `jq`:

```bash
gws sheets +read \
  --spreadsheet-id "YOUR_SHEET_ID" \
  --range "Sheet1!A1:D100" | jq '.values[]'
```

### Export a spreadsheet as CSV

```bash
gws drive files export \
  --params '{"fileId": "YOUR_SHEET_ID"}' \
  --download text/csv > data.csv
```

### Upload a file to the project folder

```bash
FOLDER_ID=$(aiseo drive folder --project proj_abc | jq -r '.folderId')

gws drive +upload \
  --file ./image.jpg \
  --parent "${FOLDER_ID}"
```

### List only Google Docs (articles)

```bash
gws drive files list --params "{
  \"q\": \"'${FOLDER_ID}' in parents and mimeType = 'application/vnd.google-apps.document' and trashed = false\",
  \"fields\": \"files(id,name,modifiedTime)\"
}"
```

### List only images

```bash
gws drive files list --params "{
  \"q\": \"'${FOLDER_ID}' in parents and (mimeType contains 'image/') and trashed = false\",
  \"fields\": \"files(id,name,mimeType)\"
}"
```

### List only spreadsheets

```bash
gws drive files list --params "{
  \"q\": \"'${FOLDER_ID}' in parents and mimeType = 'application/vnd.google-apps.spreadsheet' and trashed = false\",
  \"fields\": \"files(id,name)\"
}"
```

## Full Pipeline: Content Generation → Drive → CMS

```bash
# 1. Create content and generate
aiseo content create --project proj_abc --keyword "best seo tools 2026"
# Returns: { "id": "ci_123", ... }

aiseo jobs start --project proj_abc --content ci_123
# Returns: { "jobId": "job_xyz", "status": "queued" }

aiseo jobs wait --id job_xyz
# Blocks until complete

# 2. Get files from Drive
FOLDER_ID=$(aiseo drive folder --project proj_abc | jq -r '.folderId')

# Find the generated article
gws drive files list --params "{
  \"q\": \"'${FOLDER_ID}' in parents and mimeType = 'application/vnd.google-apps.document'\",
  \"fields\": \"files(id,name)\"
}"

# Download as HTML
gws drive files export --params '{"fileId": "doc_id"}' --download text/html > article.html

# Download images
gws drive files get --params '{"fileId": "img_id"}' --download > featured.jpg

# 3. Publish to CMS (see ../cms-skills/)
# WordPress example:
curl -X POST https://yoursite.com/wp-json/wp/v2/posts \
  -u "$WP_USER:$WP_APP_PASSWORD" \
  -H "Content-Type: application/json" \
  -d "{\"title\": \"Best SEO Tools 2026\", \"content\": $(jq -Rs . < article.html), \"status\": \"publish\"}"
```

## Internal Linking from Spreadsheets

```bash
# 1. Find the internal linking spreadsheet
gws drive files list --params "{
  \"q\": \"'${FOLDER_ID}' in parents and mimeType = 'application/vnd.google-apps.spreadsheet'\",
  \"fields\": \"files(id,name)\"
}"

# 2. Read linking recommendations
gws sheets +read --spreadsheet-id "sheet_id" --range "Sheet1!A1:D100"

# Output typically contains: Source URL, Target URL, Anchor Text, Context
# 3. Parse and apply links to your content before publishing
```

## Authentication Options

| Method | Use Case | Setup |
|--------|----------|-------|
| Interactive | Local development | `gws auth setup` |
| Service Account | Automated pipelines | Set `GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE` env var |
| Access Token | Pre-authenticated | Set `GOOGLE_WORKSPACE_CLI_TOKEN` env var |

## Troubleshooting

**"No Drive folder configured"**: The project doesn't have a Google Drive folder. Create one in the web app first.

**Permission denied**: Your Google account needs access to the Shared Drive. Ask your workspace admin.

**Rate limits**: Google Drive API has per-user rate limits. Add delays between batch operations.
