# Workflow Recipes

Step-by-step workflows for common agent tasks. Each workflow is a sequence of CLI commands you can run directly.

---

## 1. Full Content Pipeline

Create a project, generate content, and deliver it.

```bash
# Create a project
PROJECT_ID=$(aise projects create --name "Tech Blog" --url "https://techblog.com" | jq -r '.id')

# Generate topical map
TMAP_JOB=$(aise topical-map --project $PROJECT_ID | jq -r '.jobId')
aise jobs wait --id $TMAP_JOB

# Create content items from your keyword list
aise content create --project $PROJECT_ID --keyword "best seo tools 2026" --category "Reviews"
aise content create --project $PROJECT_ID --keyword "how to do keyword research" --category "Guides"
aise content create --project $PROJECT_ID --keyword "on-page seo checklist" --category "Resources"

# List content to get IDs
ITEMS=$(aise content list --project $PROJECT_ID)
echo $ITEMS | jq '.[].id'

# Start generation jobs
ITEM_ID=$(echo $ITEMS | jq -r '.[0].id')
JOB_ID=$(aise jobs start --project $PROJECT_ID --content $ITEM_ID | jq -r '.jobId')

# Wait for completion
aise jobs wait --id $JOB_ID --timeout 600

# Get deliverables from Drive
FOLDER_ID=$(aise drive folder --project $PROJECT_ID | jq -r '.folderId')
gws drive files list --params "{\"q\": \"'${FOLDER_ID}' in parents\"}"
```

---

## 2. Bulk Import and Generate

Import keywords from CSV and batch-generate content.

```bash
# Prepare a CSV file: keywords.csv
# keyword,category,contentType
# best seo tools 2026,Reviews,Blog Post
# keyword research guide,Guides,Tutorial
# technical seo audit,Guides,Checklist

# Import all keywords
aise content import --project proj_abc --file keywords.csv

# List imported items
ITEMS=$(aise content list --project proj_abc --status "backlog")

# Start jobs for each item
for ITEM_ID in $(echo $ITEMS | jq -r '.[].id'); do
  JOB=$(aise jobs start --project proj_abc --content $ITEM_ID)
  echo "Started job for $ITEM_ID: $(echo $JOB | jq -r '.jobId')"
  sleep 2  # respect rate limits
done

# Monitor all running jobs
aise jobs list --project proj_abc --status running --pretty
```

---

## 3. Content Refresh

Find and refresh stale content.

```bash
# List all live content
LIVE=$(aise content list --project proj_abc --status "Live")

# Identify items to refresh (e.g., older than 6 months — filter by date in your agent logic)
echo $LIVE | jq '.[] | select(.updatedAt < "2025-09-01") | {id, keyword, updatedAt}'

# Move items to Refresh status
ITEM_ID="ci_stale_123"
aise content update --id $ITEM_ID --status "Refresh"

# Start refresh job
JOB_ID=$(aise jobs start --project proj_abc --content $ITEM_ID | jq -r '.jobId')
aise jobs wait --id $JOB_ID
```

---

## 4. Drive-to-CMS Pipeline

Download content from Google Drive and publish to a CMS.

```bash
# Get folder ID
FOLDER_ID=$(aise drive folder --project proj_abc | jq -r '.folderId')

# List Google Docs (articles)
gws drive files list --params "{
  \"q\": \"'${FOLDER_ID}' in parents and mimeType = 'application/vnd.google-apps.document'\",
  \"fields\": \"files(id,name)\"
}"

# Download article as HTML
gws drive files export --params '{"fileId": "doc_123"}' --download text/html > article.html

# Download featured image
gws drive files get --params '{"fileId": "img_456"}' --download > featured.jpg

# Publish to WordPress (see ../cms-skills/wordpress.md for full details)
MEDIA_ID=$(curl -s -X POST https://yoursite.com/wp-json/wp/v2/media \
  -u "user:app_pass" \
  -H "Content-Disposition: attachment; filename=featured.jpg" \
  -H "Content-Type: image/jpeg" \
  --data-binary @featured.jpg | jq '.id')

curl -X POST https://yoursite.com/wp-json/wp/v2/posts \
  -u "user:app_pass" \
  -H "Content-Type: application/json" \
  -d "{
    \"title\": \"Article Title\",
    \"content\": $(jq -Rs . < article.html),
    \"status\": \"publish\",
    \"featured_media\": ${MEDIA_ID}
  }"
```

See full CMS guides:
- [WordPress](../cms-skills/wordpress.md)
- [Webflow](../cms-skills/webflow.md)
- [Shopify](../cms-skills/shopify.md)

---

## 5. Image Workflow

Download images from Drive and upload to your CMS media library.

```bash
FOLDER_ID=$(aise drive folder --project proj_abc | jq -r '.folderId')

# List all images
IMAGES=$(gws drive files list --params "{
  \"q\": \"'${FOLDER_ID}' in parents and (mimeType contains 'image/') and trashed = false\",
  \"fields\": \"files(id,name,mimeType)\"
}")

# Download each image
for IMG in $(echo $IMAGES | jq -r '.files[] | @base64'); do
  ID=$(echo $IMG | base64 -d | jq -r '.id')
  NAME=$(echo $IMG | base64 -d | jq -r '.name')

  gws drive files get --params "{\"fileId\": \"${ID}\"}" --download > "$NAME"
  echo "Downloaded: $NAME"
done

# Upload to WordPress media library
for IMG_FILE in *.jpg *.png *.webp; do
  [ -f "$IMG_FILE" ] || continue
  MIME=$(file --mime-type -b "$IMG_FILE")

  curl -s -X POST https://yoursite.com/wp-json/wp/v2/media \
    -u "user:app_pass" \
    -H "Content-Disposition: attachment; filename=${IMG_FILE}" \
    -H "Content-Type: ${MIME}" \
    --data-binary @"$IMG_FILE" | jq '{id, source_url}'
done
```

---

## 6. Internal Linking from Spreadsheets

Read linking recommendations from a spreadsheet and apply them to content.

```bash
FOLDER_ID=$(aise drive folder --project proj_abc | jq -r '.folderId')

# Find spreadsheets
gws drive files list --params "{
  \"q\": \"'${FOLDER_ID}' in parents and mimeType = 'application/vnd.google-apps.spreadsheet'\",
  \"fields\": \"files(id,name)\"
}"

# Read the linking spreadsheet
# Columns typically: Source URL, Target URL, Anchor Text, Context
gws sheets +read --spreadsheet-id "sheet_id" --range "Sheet1!A1:D100"

# Export as CSV for easier parsing
gws drive files export --params '{"fileId": "sheet_id"}' --download text/csv > links.csv

# Parse and apply (agent logic):
# 1. Read the CSV
# 2. For each row, find the source content item
# 3. Download the source content from Drive
# 4. Insert the link at the appropriate location
# 5. Update the content on the CMS
```

---

## 7. Monitoring and Polling

### Synchronous: Use `jobs wait`

Best for single jobs where you need the result before proceeding.

```bash
JOB_ID=$(aise jobs start --project proj_abc --content ci_123 | jq -r '.jobId')
aise jobs wait --id $JOB_ID --timeout 600 --interval 10
# Blocks until done. Exit code 0 = success, 1 = failure/timeout.
```

### Asynchronous: Use webhook callbacks

Best for batch operations where you don't want to block.

```bash
# Start job with callback
aise jobs start \
  --project proj_abc \
  --content ci_123 \
  --callback-url "https://your-server.com/webhook" \
  --callback-secret "your_hmac_secret"
```

Your webhook receives a POST with:
```json
{
  "event": "job.completed",
  "jobId": "job_xyz",
  "status": "completed",
  "contentItemId": "ci_123",
  "timestamp": "2026-03-16T10:05:00Z"
}
```

With `X-Signature-256: sha256=<hmac>` header for verification.

### Polling: Use `jobs status`

For custom polling logic.

```bash
aise jobs status --id job_xyz
# { "id": "job_xyz", "status": "running", "displayText": "Writing section 3/5..." }
```

---

## Tips

- **JSON parsing**: All commands output JSON. Use `jq` to extract values.
- **Error handling**: Check exit codes. 0 = success, non-zero = error. Error details in JSON output.
- **Rate limits**: STARTER = 60 req/min, TEAM = 120 req/min. Add delays in batch loops.
- **Parallel jobs**: Tenant concurrent job limit applies (default 3). Queue extras and they'll run automatically.
- **Idempotency**: Content creation is not idempotent — check if an item exists before creating duplicates.
