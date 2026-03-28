# Troubleshooting

Common errors and how to fix them.

---

## Authentication Errors

### 401 Unauthorized

```json
{ "error": "Unauthorized" }
```

**Causes:**
- `AISEO_API_KEY` environment variable not set
- API key is invalid or typo in the key
- Key has been revoked

**Fix:**
```bash
# Verify the variable is set
echo $AISEO_API_KEY

# Test authentication
aiseo auth status

# If revoked, generate a new key at:
# https://aiseoengine.studio/app/profile
```

### 403 Forbidden

```json
{ "error": "Forbidden" }
```

**Causes:**
- API key doesn't have access to the requested tenant/project
- Trying to access another tenant's resources

**Fix:**
- Verify the project belongs to your tenant: `aiseo projects list`
- Check which tenant your key is scoped to: `aiseo auth status`

---

## Rate Limiting

### 429 Too Many Requests

```json
{ "error": "Rate limit exceeded" }
```

**Limits:**
- STARTER plan: 60 requests per minute
- TEAM plan: 120 requests per minute

**Fix:**
- Add delays between requests in batch operations
- Use `sleep 1` between API calls in shell scripts
- For bulk operations, use the bulk endpoints (`content import`) instead of individual calls

---

## Job Errors

### Job stuck in "queued" status

**Causes:**
- Concurrent job limit reached (check with `aiseo jobs list --project <id> --status running`)
- Backlog jobs: only 1 runs at a time per project

**Fix:**
- Wait for running jobs to complete, or cancel them: `aiseo jobs cancel --id <jobId>`
- Check job list: `aiseo jobs list --project <id> --pretty`

### Job failed

```json
{ "status": "failed", "error": "..." }
```

**Fix:**
- Check the error message in the job status response
- Common causes: invalid content type, missing project config, API quota exceeded
- Retry: create a new job for the same content item

### Jobs wait timeout

```json
{ "error": "Timeout waiting for job" }
```

**Fix:**
- Increase timeout: `aiseo jobs wait --id <id> --timeout 900`
- Content generation can take 3-5 minutes; topical maps can take longer
- Check job status manually: `aiseo jobs status --id <id>`

---

## Google Drive Errors

### "No Google Drive folder configured for this project"

The project doesn't have a Drive folder linked.

**Fix:**
1. Open the project in the web app
2. The Drive folder is created automatically when the project is created
3. If missing, contact your workspace admin

### Permission denied on Drive files

**Fix:**
- Ensure your Google account has access to the Shared Drive
- Run `gws auth setup` to re-authenticate
- Check `GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE` if using service account

---

## Content Errors

### "Project not found"

**Fix:**
- Verify the project ID: `aiseo projects list`
- Check you're using the correct `AISEO_BASE_URL`

### "Content item not found"

**Fix:**
- Verify the content item ID: `aiseo content list --project <id>`
- Content items are scoped to projects — make sure you're looking in the right project

### Duplicate content items

The API doesn't prevent duplicate keywords. Before creating, check:

```bash
# Search for existing items with the same keyword
aiseo content list --project proj_abc | jq '.[] | select(.keyword == "your keyword")'
```

---

## MCP Connection Issues

### Claude Desktop: "Some MCP servers could not be loaded"

**Cause:** Your version of Claude Desktop doesn't support remote MCP servers (Streamable HTTP). The `url` config field is only recognized in recent versions.

**Fix:**
1. Update Claude Desktop to the latest version (Help → Check for Updates, or re-download from https://claude.ai/download)
2. Restart Claude Desktop after updating
3. Your config is likely correct — older versions just don't recognize the `url` field

**Alternative:** Use Claude.ai (web) instead — go to Settings → Integrations, paste `https://aiseoengine.studio/api/mcp`, and sign in with OAuth. No API key needed.

### MCP tools not appearing after connecting

**Fix:**
- Verify the URL is exactly `https://aiseoengine.studio/api/mcp`
- Try disconnecting and reconnecting the server
- Restart your client (Claude Desktop, Cursor, etc.)

---

## CLI Installation Issues

### "aiseo: command not found"

**Fix:**
```bash
# Verify installation
npm list -g @aiseo/cli

# Reinstall
npm install -g @aiseo/cli

# Check npm global bin is in PATH
npm config get prefix
# Add <prefix>/bin to your PATH
```

### Node.js version error

**Fix:**
- Requires Node.js 18+
- Check version: `node --version`
- Update: `nvm install 18` or download from https://nodejs.org

---

## Webhook Callback Issues

### Callback not received

**Causes:**
- `callbackUrl` not reachable from the server
- Firewall blocking incoming requests
- URL typo

**Fix:**
- Test the URL is reachable: `curl -X POST <your-callback-url>`
- Check server logs for incoming requests
- Callbacks have a 10-second timeout — ensure your endpoint responds quickly

### HMAC signature verification failing

**Fix:**
```bash
# The signature is in the X-Signature-256 header: sha256=<hex>
# Verify with:
echo -n '<request-body>' | openssl dgst -sha256 -hmac '<your-secret>'

# Compare the hex output with the header value (without the sha256= prefix)
```

- Ensure you're using the raw request body (not parsed JSON) for verification
- The secret must match exactly what you passed in `--callback-secret`

---

## Getting Help

- **Web App**: https://aiseoengine.studio
- **CLI Docs**: https://aiseoengine.studio/cli
- **API Key Management**: https://aiseoengine.studio/app/profile
