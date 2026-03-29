---
name: doc-manager
version: "1.0"
description: >
  Create, read, update, and template-fill Google Docs via the Google Docs and
  Drive REST APIs. Use this skill whenever the agent needs to create a new
  document, clone a template and fill its placeholders, read the text content
  of a doc, or append/insert content into an existing doc. Always trigger when
  a process requires producing or editing a Google Doc deliverable — reports,
  briefs, content drafts, or any structured document.

inputs:
  required:
    - type: text
      label: "operation"
      description: "The doc operation: create, clone-template, replace-placeholders, read, append"
  optional:
    - type: text
      label: "doc-id"
      description: "Google Doc ID (from the URL — omit to create a new doc)"
    - type: text
      label: "doc-title"
      description: "Title for a new or cloned document"
    - type: text
      label: "folder-id"
      description: "Google Drive folder ID to place the document in"
    - type: json
      label: "placeholders"
      description: "Key-value pairs of {placeholder} → replacement text, for clone-template and replace-placeholders operations"
    - type: text
      label: "content"
      description: "Text content to append to an existing doc"

outputs:
  - type: json
    label: "doc-result"
    description: "Operation result containing doc ID, URL, and confirmation details"
  - type: text
    label: "doc-url"
    description: "Google Docs URL of the created or modified document"

tools_used: [gws-cli, curl]

chains_from: []
chains_to:
  - landscape-report-generator

tags:
  - google-docs
  - documents
  - templates
  - deliverables
---

# Doc Manager

## What This Skill Does

Creates and manages Google Docs as deliverables and working documents. The primary use case is cloning a branded template and filling its `{placeholder}` fields with real content — the pattern used to produce the Target Market Landscape Report and other Omnipresence deliverables. Also handles creating blank docs, reading doc content, and appending text.

---

## Context the Agent Needs

All doc operations use the Google Docs API v1 and Drive API v3 via `curl`. Authentication uses the same `gws` service account as all other Google Workspace operations — get a token with `gws auth print-access-token`, then pass it as a Bearer token in every API call.

**Doc IDs** are the alphanumeric string from the Google Docs URL:
`https://docs.google.com/document/d/{DOC_ID}/edit`

**Template cloning** is the correct pattern for producing branded reports. Clone first, then fill placeholders — never edit the original template. The `replaceAllText` request in the Docs API is the most reliable way to fill `{placeholder}` fields: it replaces every occurrence throughout the entire document (headers, body, tables, footers) in a single call.

**Service account access:** The service account must have access to any template document and any target Drive folder. If a template or folder is in a shared drive, share it with the service account email. If the doc is in My Drive, share it with the service account directly.

---

## Workflow — Execute In This Order

---

### STEP 1: Verify Access

Confirm Google Workspace authentication is working before any operation.

**Process:**
```bash
gws drive about get --params '{"fields": "user"}'
```
If this returns a user object, proceed. If it errors, stop — report auth failure to the member and ask them to contact support. Never attempt to fix credentials.

---

### STEP 2: Execute the Requested Operation

#### `create` — Create a blank document

**Process:**
```bash
TOKEN=$(gws auth print-access-token)

# Create the document
DOC=$(curl -s -X POST "https://docs.googleapis.com/v1/documents" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "TITLE"}')

DOC_ID=$(echo $DOC | jq -r '.documentId')
echo "Created: https://docs.google.com/document/d/$DOC_ID/edit"
```

If a `folder-id` is provided, move the doc into that folder after creation:
```bash
# Move into folder (Drive API)
curl -s -X PATCH "https://www.googleapis.com/drive/v3/files/$DOC_ID?addParents=FOLDER_ID&removeParents=root&supportsAllDrives=true" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Output:** Doc ID and URL.

---

#### `clone-template` — Copy a template and fill placeholders

This is the standard pattern for producing branded reports. Clone the template, then replace all `{placeholder}` fields in one batch.

**Process:**
```bash
TOKEN=$(gws auth print-access-token)

# 1. Clone the template
CLONE=$(curl -s -X POST "https://www.googleapis.com/drive/v3/files/TEMPLATE_DOC_ID/copy?supportsAllDrives=true" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "TITLE", "parents": ["FOLDER_ID"]}')

DOC_ID=$(echo $CLONE | jq -r '.id')

# 2. Replace all placeholders in one batchUpdate call
# Build the requests array — one replaceAllText per placeholder
curl -s -X POST "https://docs.googleapis.com/v1/documents/$DOC_ID:batchUpdate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "requests": [
      {
        "replaceAllText": {
          "containsText": {"text": "{placeholder_name}", "matchCase": false},
          "replaceText": "replacement value"
        }
      }
    ]
  }'

echo "Doc ready: https://docs.google.com/document/d/$DOC_ID/edit"
```

**Building the requests array:** For each key-value pair in `placeholders`, add one `replaceAllText` object to the requests array. Use `jq` to build the payload cleanly:

```bash
# Example: build requests from a JSON object of placeholders
PLACEHOLDERS='{
  "{brand_name}": "Acme Plumbing",
  "{date}": "2026-03-29",
  "{market_definition}": "Residential plumbing services in Auckland..."
}'

REQUESTS=$(echo $PLACEHOLDERS | jq '[to_entries[] | {
  "replaceAllText": {
    "containsText": {"text": .key, "matchCase": false},
    "replaceText": .value
  }
}]')

curl -s -X POST "https://docs.googleapis.com/v1/documents/$DOC_ID:batchUpdate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"requests\": $REQUESTS}"
```

**Output:** Cloned doc ID and URL, confirmation of placeholder count replaced.

---

#### `replace-placeholders` — Fill placeholders in an existing doc

Same as the placeholder replacement step above, but on an existing doc (no cloning):

```bash
TOKEN=$(gws auth print-access-token)

REQUESTS=$(echo $PLACEHOLDERS | jq '[to_entries[] | {
  "replaceAllText": {
    "containsText": {"text": .key, "matchCase": false},
    "replaceText": .value
  }
}]')

RESULT=$(curl -s -X POST "https://docs.googleapis.com/v1/documents/DOC_ID:batchUpdate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"requests\": $REQUESTS}")

# Count how many replacements were made
echo $RESULT | jq '[.replies[].replaceAllText.occurrencesChanged // 0] | add'
```

Check the `occurrencesChanged` field per reply — if zero for a placeholder that should exist, the placeholder text didn't match (check spelling, case, curly brace format).

**Output:** Count of replacements made per placeholder. Any with `occurrencesChanged: 0` are flagged as unfilled.

---

#### `read` — Get the text content of a document

Export as plain text via the Drive API (simpler than parsing the Docs JSON structure):

```bash
TOKEN=$(gws auth print-access-token)

curl -s "https://www.googleapis.com/drive/v3/files/DOC_ID/export?mimeType=text/plain&supportsAllDrives=true" \
  -H "Authorization: Bearer $TOKEN"
```

To get the raw Docs JSON (structure, formatting, table data):
```bash
curl -s "https://docs.googleapis.com/v1/documents/DOC_ID" \
  -H "Authorization: Bearer $TOKEN" | jq '.body.content'
```

**Output:** Plain text content of the document.

---

#### `append` — Add content at the end of a document

The Docs API requires knowing the end index to insert at. Read the doc first to find it:

```bash
TOKEN=$(gws auth print-access-token)

# 1. Get the current end index
END_INDEX=$(curl -s "https://docs.googleapis.com/v1/documents/DOC_ID" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.body.content[-1].endIndex - 1')

# 2. Insert text at that index
curl -s -X POST "https://docs.googleapis.com/v1/documents/DOC_ID:batchUpdate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"requests\": [{
      \"insertText\": {
        \"location\": {\"index\": $END_INDEX},
        \"text\": \"YOUR CONTENT HERE\n\"
      }
    }]
  }"
```

**Note:** For large content blocks with formatting, prefer `clone-template` with a pre-structured template over appending raw text. The Docs API insert operations don't apply formatting — appended text inherits the style at the insertion point.

**Output:** Confirmation of insertion and updated doc URL.

---

### STEP 3: Return Result

Format the result for the caller.

**For create / clone-template:**
```
Doc created: {title}
URL: https://docs.google.com/document/d/{doc-id}/edit
Doc ID: {doc-id}
Placeholders filled: {n}
Unfilled placeholders: {list, or "none"}
```

**For replace-placeholders:**
```
Replacements made in {doc-title}:
- {placeholder}: {n} occurrence(s) replaced
- {placeholder}: 0 occurrences — CHECK: may not exist in doc
```

**For read:** Return the plain text content directly.

**For append:** Confirm insertion point and character count added.

---

## Output Format

Always include the doc URL in every response. Doc IDs should be surfaced for storage in memory. Flag any unfilled placeholders explicitly — don't silently leave `{curly_brace}` text in a delivered doc.

---

## Edge Cases & Judgment Calls

**Template not shared with service account:**
Drive API returns 404 (not 403) when the service account can't see a file. If clone fails with "File not found," the template hasn't been shared. Ask the member to share the template doc with the service account email (visible in `gws drive about get`).

**Placeholder not found in doc (`occurrencesChanged: 0`):**
Most common causes: wrong case, extra spaces inside the braces, slightly different spelling. Read the doc as plain text, search for the placeholder string, and report the exact text found near where the placeholder should be. Don't guess — show the member what's actually in the doc.

**Doc is in a shared drive, not My Drive:**
Always include `supportsAllDrives=true` in Drive API calls. Without it, shared drive files return 404 or are silently excluded. This applies to copy, move, export, and get operations.

**Content too long for a single insert:**
Split into multiple `insertText` requests in one `batchUpdate` call. The Docs API accepts up to 2MB per `batchUpdate` request. For very large content, split into multiple batchUpdate calls.

**Tables in the template:**
`replaceAllText` works inside table cells — it scans the full document including headers, footers, and tables. No special handling needed.

**Doc ID extracted from URL instead of provided directly:**
Accept full Google Docs URLs and extract the ID from the path segment after `/d/`. Do not require the user to manually parse the URL.

---

## What This Skill Does NOT Do

- Does not apply text formatting (bold, italic, font size, colour) — use a pre-formatted template instead
- Does not create or modify tables structurally (add/remove rows/columns) — only fills existing placeholder cells via replaceAllText
- Does not convert between formats (Docs → PDF → Sheets) — use Drive export for one-way format conversion
- Does not manage document sharing or permissions — handled separately via Drive API or manually
- Does not handle Google Slides or Forms — separate skills for those
- Does not sync doc content to external systems

---

## Examples

### Example 1: Clone and fill the landscape report template

**Context:** landscape-report-generator skill needs to produce a branded report doc.

```bash
TOKEN=$(gws auth print-access-token)

# Clone template
CLONE=$(curl -s -X POST "https://www.googleapis.com/drive/v3/files/TEMPLATE_ID/copy?supportsAllDrives=true" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme Plumbing — Target Market Landscape Report", "parents": ["MEMBER_FOLDER_ID"]}')
DOC_ID=$(echo $CLONE | jq -r '.id')

# Fill all placeholders in one call
PLACEHOLDERS=$(jq -n '{
  "{brand_name}": "Acme Plumbing",
  "{date}": "2026-03-29",
  "{market_definition}": "Residential plumbing services in Auckland, NZ.",
  "{TAM}": "NZ$420M–$480M",
  "{trend}": "Growing — 3.2% CAGR",
  "{signal}": "Rising",
  "{market_context}": "Auckland housing pipeline driving steady demand.",
  "{patterns}": "All competitors position as general plumbers — none specialise by service type.",
  "{underserved_need}": "Hot water cylinder specialists",
  "{positioning_statement}": "Auckland hot water cylinder repair, replacement and installation specialists.",
  "{gap_analysis}": "No before/after photos specific to hot water installations."
}')

REQUESTS=$(echo $PLACEHOLDERS | jq '[to_entries[] | {"replaceAllText": {"containsText": {"text": .key, "matchCase": false}, "replaceText": .value}}]')

RESULT=$(curl -s -X POST "https://docs.googleapis.com/v1/documents/$DOC_ID:batchUpdate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"requests\": $REQUESTS}")

echo "Report ready: https://docs.google.com/document/d/$DOC_ID/edit"
echo $RESULT | jq '[.replies[].replaceAllText.occurrencesChanged // 0] | add | "Replacements made: \(.)"'
```

**Output:**
```
Doc created: Acme Plumbing — Target Market Landscape Report
URL: https://docs.google.com/document/d/1xYz.../edit
Doc ID: 1xYz...
Placeholders filled: 11
Unfilled placeholders: none
```

---

### Example 2: Read a doc to verify content

**Context:** Agent needs to confirm no `{placeholder}` text remains in a delivered report.

```bash
TOKEN=$(gws auth print-access-token)

CONTENT=$(curl -s "https://www.googleapis.com/drive/v3/files/DOC_ID/export?mimeType=text/plain&supportsAllDrives=true" \
  -H "Authorization: Bearer $TOKEN")

# Check for any remaining unfilled placeholders
echo "$CONTENT" | grep -o '{[^}]*}' | sort -u
```

If the `grep` returns nothing, all placeholders were filled. If it returns strings like `{competitor}`, those rows still have unfilled template text — loop back and fill them.
