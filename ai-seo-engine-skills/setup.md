# Setup Guide

## Prerequisites

- Node.js 18 or later
- npm (comes with Node.js)
- An active AI SEO Engine subscription

## Installation

```bash
npm install -g @aise/cli
```

Verify the installation:

```bash
aise --version
# 0.1.0
```

## Get Your API Key

1. Log in to https://aiseoengine.studio
2. Go to **Profile** → **API Keys** section (https://aiseoengine.studio/app/profile)
3. Click **Generate New Key**
4. Give it a name (e.g., "Claude Code agent")
5. Copy the key immediately — it's shown only once
6. The key starts with `aise_`

## Environment Variables

Set these in your shell profile or agent configuration:

```bash
# Required — your API key
export AISE_API_KEY=aise_your_key_here

# Optional — defaults to https://aiseoengine.studio
export AISE_BASE_URL=https://aiseoengine.studio
```

## Verify Authentication

```bash
aise auth status --pretty
```

Expected output:

```json
{
  "id": "user_abc123",
  "email": "you@company.com",
  "name": "Your Name",
  "tenants": [
    {
      "id": "tenant_xyz",
      "name": "Your Workspace",
      "tier": "TEAM",
      "role": "OWNER"
    }
  ]
}
```

## Rate Limits

- **STARTER plan**: 60 requests per minute per API key
- **TEAM plan**: 120 requests per minute per API key
- Rate limit headers are included in API responses
- Exceeding the limit returns HTTP 429

## Key Management

```bash
# List your keys (via the web UI — API keys can only be managed through the profile page)
# Revoke a key if compromised — revocation is immediate
```

API keys:
- Are scoped to a single tenant
- Can be revoked at any time from the profile page
- Show last-used timestamp
- Support optional expiration dates

## Google Workspace CLI (Optional)

For accessing Google Drive files (docs, images, spreadsheets), install the Google Workspace CLI:

```bash
npm install -g @googleworkspace/cli
gws auth setup
```

See [google-workspace.md](./google-workspace.md) for integration details.

## Next Steps

- [Concepts](./concepts.md) — what each feature does and how the pipeline works
- [CLI Reference](./cli-reference.md) — full command syntax and examples
- [Workflows](./workflows.md) — step-by-step recipes
- [CMS Skills](../cms-skills/) — publishing to WordPress, Webflow, Shopify
