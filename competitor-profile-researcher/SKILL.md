---
name: competitor-profile-researcher
version: "1.0"
description: >
  Discover which platforms a competitor has profiles on by searching the web for their brand name and
  cross-referencing results against their website URL. Use this skill whenever building a list of
  profile platforms a competitor appears on, researching competitor entity signals, or identifying
  directories and review sites in a niche. Always trigger when given a competitor brand name + URL
  and asked to find their online profiles.

inputs:
  required:
    - type: text
      label: "competitor_name"
      description: "The competitor's brand name (e.g., 'Acme Plumbing')"
    - type: text
      label: "competitor_url"
      description: "The competitor's website URL for entity verification (e.g., 'https://acmeplumbing.com')"
  optional:
    - type: text
      label: "industry"
      description: "Industry or niche for disambiguation (e.g., 'plumbing contractor'). Strongly recommended for common brand names."

outputs:
  - type: json
    label: "discovered-profiles"
    description: "Structured list of platforms where the competitor has profiles, with platform name, URL, and website type"

tools_used: [brave-search, page-scraper]
chains_from: [sheet-manager]
chains_to: [sheet-manager, existing-profile-checker]
tags: [competitor-research, profile-discovery, entity-signals, seo]
---

## What This Skill Does

Searches the web for a single competitor's brand name, scans search results to identify profile platforms (directories, review sites, social profiles, startup listings, industry-specific platforms), and returns a structured list of discovered profiles after verifying entity correctness against the competitor's website URL.

## Context the Agent Needs

This skill runs as a sub-agent — one competitor per invocation. The caller (typically sheet-manager) provides one competitor at a time and collects results across multiple invocations.

Entity verification is critical. Many brand names are common words or shared across industries. Always cross-reference the competitor URL against profile pages to confirm you have the right entity before including a platform in the results. A profile that mentions "acmeplumbing.com" is confirmed; a profile for "Acme Plumbing" in a different city with no URL match is not.

This skill does NOT use Ahrefs, Moz, or any domain authority tools. Discovery relies entirely on web search results and page content analysis.

## Workflow Steps

### STEP 1: Search for competitor profiles

Cast a wide net across search results to find every platform where the competitor appears.

**Input:** `competitor_name`, `competitor_url`, optional `industry`
**Process:**
1. Run primary search: `"[competitor_name]"` (exact match, quoted)
2. If fewer than 10 results or results look ambiguous (other entities with the same name dominate), run a refined search: `"[competitor_name]" [industry]` or `"[competitor_name]" site:[competitor_url domain]`
3. For common/ambiguous names, also try: `"[competitor_name]" "[competitor_url domain]"` to surface profiles that link back to the competitor's site
4. Collect all unique non-competitor-owned URLs from the search results (skip the competitor's own site pages)
5. Deduplicate by root domain — keep only the most relevant page per platform
**Output:** Raw list of candidate platform URLs (typically 10-30)
**Decision gate:**
- If 5+ candidate URLs found → proceed to Step 2
- If fewer than 5 candidates → run additional searches with industry terms, location, or product keywords, then proceed to Step 2

### STEP 2: Classify platform types

Determine what kind of platform each candidate URL represents to categorize the profile.

**Input:** List of candidate URLs from Step 1
**Process:**
1. For each URL, classify the platform into one of these types based on the domain and page path: `directory`, `review-site`, `social`, `startup-listing`, `industry-specific`, `map-listing`, `news-mention`, `other`
2. Use domain knowledge for well-known platforms (e.g., yelp.com = review-site, linkedin.com = social, crunchbase.com = startup-listing, bbb.org = directory)
3. For unfamiliar domains, use page-scraper to load the page and determine the platform type from its content and structure
4. Discard URLs that are clearly not profiles (e.g., news articles that merely mention the competitor, generic search aggregator pages, the competitor's own blog posts on other sites)
**Output:** Classified list of candidate platforms with types assigned
**Decision gate:**
- If all candidates are classified → proceed to Step 3
- If any candidate is ambiguous → scrape the page for more context, then classify

### STEP 3: Verify entity correctness

Confirm each discovered profile actually belongs to the target competitor, not a different entity with the same name.

**Input:** Classified candidate list from Step 2, `competitor_url`
**Process:**
1. For each candidate, check if the search result snippet or page content contains the competitor's URL, domain name, phone number, or address
2. For high-confidence platforms (profile page URL contains the competitor name and the snippet references their domain), mark as verified
3. For uncertain matches, use page-scraper to load the profile page and scan for the competitor's website URL, matching contact details, or other identifying information
4. Mark each profile as `verified` (URL/contact match found) or `unverified` (name match only, no corroborating details)
5. Include both verified and unverified profiles in the output, but flag the confidence level
**Output:** Final list of profiles with verification status
**Decision gate:**
- If at least 1 verified profile found → proceed to Step 4
- If zero verified profiles → report that no confirmed profiles were found, include unverified candidates with a warning

### STEP 4: Compile and return results

Assemble the structured output for the caller.

**Input:** Verified and classified profiles from Step 3
**Process:**
1. Sort profiles: verified first, then unverified, alphabetical within each group
2. Format each profile according to the output template
3. Include a summary count by platform type
**Output:** Structured JSON result (see Output Format)
**Decision gate:**
- Output ready → return to caller

## Output Format

Return results as structured data with this exact shape:

```json
{
  "competitor_name": "Acme Plumbing",
  "competitor_url": "https://acmeplumbing.com",
  "profiles_found": 12,
  "profiles": [
    {
      "platform_name": "Yelp",
      "platform_url": "https://www.yelp.com/biz/acme-plumbing-dallas",
      "website_type": "review-site",
      "verified": true
    },
    {
      "platform_name": "LinkedIn",
      "platform_url": "https://www.linkedin.com/company/acme-plumbing",
      "website_type": "social",
      "verified": true
    },
    {
      "platform_name": "Houzz",
      "platform_url": "https://www.houzz.com/pro/acme-plumbing",
      "website_type": "industry-specific",
      "verified": false
    }
  ],
  "summary_by_type": {
    "review-site": 3,
    "directory": 4,
    "social": 2,
    "industry-specific": 2,
    "startup-listing": 1
  }
}
```

**Formatting rules:**
- `platform_url` must be the direct profile page URL, not a search results page
- `website_type` must be one of: `directory`, `review-site`, `social`, `startup-listing`, `industry-specific`, `map-listing`, `other`
- `verified` is `true` only when the competitor's URL or matching contact info was confirmed on the profile page
- Do not include the competitor's own website pages in the profiles list

## Edge Cases & Judgment Calls

**Incomplete input — competitor name provided but no URL:**
Ask the caller for the competitor URL before proceeding. The URL is required for entity verification. Without it, results cannot be reliably attributed to the correct entity.

**Ambiguous entity — common brand name returns mixed results:**
Escalate search specificity progressively: add industry terms, add the URL domain to the search query, add location if known. If results still mix entities, use page-scraper on each candidate to verify. Flag any profiles where entity confidence is low as `verified: false` rather than discarding them.

**Oversized output — competitor has 50+ profiles:**
Return all discovered profiles. Do not truncate. The downstream skill (sheet-manager) handles aggregation and filtering. If search results span many pages, focus on the first 3-4 pages of results — diminishing returns beyond that.

**Failed tool call — Brave Search returns an error or no results:**
Retry once. If the search still fails, report the failure to the caller with the reason. Do not fabricate results. Suggest the caller verify the competitor name spelling or try an alternate name/DBA.

**Competitor website is dead or redirects:**
Proceed with the search using the brand name. Note in the output that the competitor URL was unreachable. Verification will rely on name matching and any cached references to the original URL.

**Profile page requires login to view:**
Include the platform in results with the profile URL as discovered from search results. Mark `verified: false` since the page content could not be checked. Note that the platform requires authentication.

## What This Skill Does NOT Do

- Does not check if the member's own site has profiles on these platforms (that is existing-profile-checker)
- Does not assess domain authority, backlink value, or SEO metrics of discovered platforms
- Does not create or claim profiles on any platform
- Does not scrape competitor reviews, ratings, or detailed profile content beyond what is needed for verification
- Does not handle multiple competitors in one invocation — call once per competitor
- Does not deduplicate across competitors — the caller manages cross-competitor aggregation

## Examples

### Example 1: Clear brand name with strong web presence (happy path)

**Input:**
```json
{
  "competitor_name": "BrightLocal",
  "competitor_url": "https://www.brightlocal.com"
}
```

**Agent action:**
1. Brave Search: `"BrightLocal"` — returns 20+ results across G2, Capterra, LinkedIn, Twitter/X, Crunchbase, Product Hunt, TrustPilot, etc.
2. Classify each: G2 = review-site, Capterra = review-site, LinkedIn = social, Crunchbase = startup-listing, etc.
3. Verify: G2 profile page links to brightlocal.com — verified. LinkedIn company page lists brightlocal.com — verified. All major profiles confirmed.
4. Return 14 profiles, 12 verified, 2 unverified.

**Why this works:** Distinctive brand name produces clean search results. Entity verification is straightforward because the URL appears on most profile pages.

### Example 2: Common brand name requiring disambiguation (edge case)

**Input:**
```json
{
  "competitor_name": "Summit Dental",
  "competitor_url": "https://summitdentalcolorado.com",
  "industry": "dentist"
}
```

**Agent action:**
1. Brave Search: `"Summit Dental"` — returns results for Summit Dental practices in 8 different states.
2. Refined search: `"Summit Dental" "summitdentalcolorado.com"` — narrows to the Colorado practice. Also try: `"Summit Dental" dentist Colorado`.
3. Classify: Yelp = review-site, Healthgrades = industry-specific, Google Business = map-listing, Facebook = social, Zocdoc = industry-specific.
4. Verify: Yelp profile for "Summit Dental" in Denver lists summitdentalcolorado.com — verified. Healthgrades profile lists matching phone number — verified. A Zocdoc listing for "Summit Dental" in Ohio has no URL match — excluded.
5. Return 8 profiles, 6 verified, 2 unverified (flagged as name-match only).

**Why this matters:** Without URL cross-referencing, the agent would have returned profiles for the wrong Summit Dental. The disambiguation queries and per-profile verification prevented false positives.
