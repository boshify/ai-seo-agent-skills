---
name: sheet-manager
version: "1.0"
description: >
  Create, read, update, and manage Google Sheets for tracking processes like profile creation,
  content pipelines, or any row-based workflow. Use this skill whenever the agent needs to
  create a tracking spreadsheet, add or update rows in a sheet, check for duplicates, read
  sheet data, or manage tabs within a workbook. Always trigger when a process requires
  persistent tabular tracking via Google Sheets.

inputs:
  required:
    - type: text
      label: "operation"
      description: "The sheet operation: create-sheet, read-rows, update-row, add-row, add-tab"
  optional:
    - type: text
      label: "sheet-id"
      description: "Google Sheet ID (omit to create a new sheet)"
    - type: text
      label: "sheet-name"
      description: "Name for a new sheet or the tab/sheet name to target within a workbook"
    - type: json
      label: "columns"
      description: "Column structure definition including headers and optional data validation (dropdowns)"
    - type: json
      label: "row-data"
      description: "Key-value pairs mapping column headers to cell values"
    - type: text
      label: "filter-column"
      description: "Column header to filter or match on when reading or checking duplicates"
    - type: text
      label: "filter-value"
      description: "Value to match against filter-column"

outputs:
  - type: json
    label: "sheet-result"
    description: "Operation result containing sheet ID, row data, update confirmation, or matched rows"
  - type: text
    label: "sheet-url"
    description: "Google Sheets URL for newly created or existing sheets"

tools_used: [gws-cli, curl]
chains_from: []
chains_to: [competitor-profile-researcher, profile-creator, brand-info-assembler, existing-profile-checker]
tags: [google-sheets, tracking, data-management, automation]
---

## What This Skill Does

Creates and manages Google Sheets as structured tracking systems for multi-step processes, handling column setup with data validation, row CRUD operations, and duplicate prevention. Returns sheet URLs, row data, and operation confirmations that downstream skills use to track their work.

## Context the Agent Needs

All sheet operations go through the AI SEO Engine's Google Workspace integration (`gws-cli` or the equivalent API). The agent must have a valid Google Workspace connection configured in the AI SEO Engine project before using this skill. Sheet IDs are the alphanumeric string from the Google Sheets URL (`https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit`). When creating sheets, the API returns the new sheet ID — store it for all subsequent operations on that sheet. Tabs (individual sheets within a workbook) are referenced by name, not index.

## Workflow Steps

### STEP 1: Resolve the target sheet

Determine whether to create a new sheet or operate on an existing one.

**Input:** User request with optional `sheet-id`
**Process:**
1. If `sheet-id` is provided, verify the sheet exists and is accessible by reading row 1 (headers)
2. If no `sheet-id` and operation is `create-sheet`, proceed to Step 2
3. If no `sheet-id` and operation requires an existing sheet, ask the user for the sheet ID or URL
**Output:** Confirmed sheet ID and current header row (if existing sheet)
**Decision gate:**
- If `create-sheet` operation → proceed to Step 2
- If existing sheet confirmed → proceed to Step 3

### STEP 2: Create and configure a new sheet

Set up the sheet with the correct column structure and data validation.

**Input:** `sheet-name` and `columns` definition
**Process:**
1. Create a new Google Sheet with the specified name via `gws-cli`
2. Write the header row using the column names from `columns`
3. For any column with a `dropdown` field, apply data validation restricting that column to the specified values (e.g., Status: ["Not Started", "In Progress", "Complete", "Error"])
4. Freeze the header row
5. Store and return the new sheet ID and URL
**Output:** Sheet ID, sheet URL, and confirmation of column structure
**Decision gate:**
- If sheet created successfully → return result or proceed to Step 3 if additional operations were requested
- If creation fails (permissions, quota) → report error with the API response

### STEP 3: Execute the requested operation

Perform the read, add, or update operation on the target sheet.

**Input:** Operation type, sheet ID, and operation-specific parameters
**Process:**
1. **read-rows:** Fetch all rows, or filter to rows where `filter-column` matches `filter-value`
2. **add-row:** First check for duplicates by matching `filter-column` against existing rows. If no duplicate found, append the new row. If duplicate exists, report it and skip the add.
3. **update-row:** Locate the target row by matching `filter-column` = `filter-value`, then update only the specified cells in `row-data`
4. **add-tab:** Create a new tab within the existing workbook, optionally with its own column structure
**Output:** Operation result (row data for reads, row number for adds, confirmation for updates)
**Decision gate:**
- If operation succeeds → return result
- If duplicate detected on add → return the existing row data and skip
- If target row not found on update → report "row not found" with the filter criteria used

### STEP 4: Return structured result

Format the operation result for the calling agent or user.

**Input:** Raw operation result from Step 3
**Process:**
1. Include the sheet URL in every response
2. For reads, format rows as a list of key-value objects (header → value)
3. For adds and updates, confirm the row number and final cell values
4. For creates, include the sheet ID prominently so the caller can store it
**Output:** Structured result per the Output Format below
**Decision gate:**
- If caller is another skill (chained) → return JSON result
- If caller is the user directly → return formatted markdown

## Output Format

### For sheet creation:
```
Sheet created: {sheet-name}
URL: https://docs.google.com/spreadsheets/d/{sheet-id}/edit
Sheet ID: {sheet-id}
Columns: {column-1} | {column-2} | ... | {column-n}
Data validation applied: {column-name} → [{value-1}, {value-2}, ...]
```

### For reading rows:
```
## {sheet-name} — {n} rows found

| {col-1} | {col-2} | ... | {col-n} |
|---------|---------|-----|---------|
| {val}   | {val}   | ... | {val}   |
```

### For adding a row:
```
Row added to {sheet-name} (row {row-number}):
- {column-1}: {value-1}
- {column-2}: {value-2}
...
```

### For duplicate detected:
```
Duplicate found — skipped add.
Existing row {row-number} matches on {filter-column} = "{filter-value}":
- {column-1}: {value-1}
- {column-2}: {value-2}
...
```

### For updating a row:
```
Row {row-number} updated in {sheet-name}:
- {column-1}: {old-value} → {new-value}
...
```

## Edge Cases & Judgment Calls

**Incomplete input — no column structure provided for create:**
Use a sensible default for the process context. For profile tracking, default to: Platform | URL | Status | Date Created | Notes. Ask the user to confirm or adjust before writing.

**Ambiguous target — multiple rows match the filter:**
Return all matching rows and ask the caller which one to update. Never silently update all matches — that risks corrupting tracked data.

**Failed tool call — Google Workspace API error:**
Report the exact error from `gws-cli`. Common causes: expired auth token (re-authenticate), sheet not shared with the service account (share it), rate limit (wait and retry once). Do not retry more than once automatically.

**Oversized read — sheet has hundreds of rows:**
Return only the first 50 rows with a count of total rows. Offer to filter by column value or return a specific range. Never dump hundreds of rows into the conversation context.

**Duplicate check column not specified on add:**
Default to the first non-status, non-date column (typically the URL or name column). Log which column was used for the duplicate check so the caller can verify it was appropriate.

**Sheet ID extracted from URL instead of provided directly:**
Accept full Google Sheets URLs and extract the sheet ID from the path. Do not require the user to manually parse the URL.

## What This Skill Does NOT Do

- Does not create charts, graphs, or conditional formatting beyond dropdown validation
- Does not manage Google Sheets permissions or sharing settings
- Does not perform formulas or calculations within cells
- Does not handle sheet-to-sheet references or cross-workbook operations
- Does not sync sheet data to external databases or APIs
- Does not monitor sheets for changes or trigger automations on update

## Examples

### Example 1: Create a profile tracking sheet (happy path)

**User:** "Create a Google Sheet to track profile creation for RankBuilders across directories."

**Agent action:**
1. Calls `gws-cli` to create a new sheet named "RankBuilders — Profile Tracking"
2. Writes header row: Platform | Profile URL | Status | Date Created | Claimed | Notes
3. Applies dropdown validation on Status: ["Not Started", "In Progress", "Live", "Error", "Blocked"]
4. Applies dropdown validation on Claimed: ["Yes", "No", "N/A"]
5. Freezes header row

**Agent output:**
```
Sheet created: RankBuilders — Profile Tracking
URL: https://docs.google.com/spreadsheets/d/1aBcDeFgHiJkL/edit
Sheet ID: 1aBcDeFgHiJkL
Columns: Platform | Profile URL | Status | Date Created | Claimed | Notes
Data validation applied: Status → [Not Started, In Progress, Live, Error, Blocked]
Data validation applied: Claimed → [Yes, No, N/A]
```

### Example 2: Add a row with duplicate detection (edge case)

**User:** "Add Yelp to the tracking sheet. URL is https://yelp.com/biz/rankbuilders"

**Agent action:**
1. Reads all rows from the sheet, checking the "Profile URL" column for `https://yelp.com/biz/rankbuilders`
2. Finds an existing row (row 5) with that URL

**Agent output:**
```
Duplicate found — skipped add.
Existing row 5 matches on Profile URL = "https://yelp.com/biz/rankbuilders":
- Platform: Yelp
- Profile URL: https://yelp.com/biz/rankbuilders
- Status: Live
- Date Created: 2026-03-15
- Claimed: Yes
- Notes: Verified listing

No new row added. Update the existing row instead?
```

### Example 3: Filtered read for status check (happy path)

**User:** "Which profiles are still in progress?"

**Agent action:**
1. Reads all rows from the sheet, filtering where Status = "In Progress"
2. Returns 3 matching rows

**Agent output:**
```
## RankBuilders — Profile Tracking — 3 rows found

| Platform     | Profile URL                          | Status      | Date Created | Claimed | Notes              |
|-------------|--------------------------------------|-------------|--------------|---------|---------------------|
| Foursquare  | https://foursquare.com/rankbuilders  | In Progress | 2026-03-20   | No      | Awaiting approval   |
| Hotfrog     | https://hotfrog.com/rb               | In Progress | 2026-03-21   | N/A     | Email verification  |
| Manta       | https://manta.com/rankbuilders       | In Progress | 2026-03-22   | No      | Profile under review|
```
