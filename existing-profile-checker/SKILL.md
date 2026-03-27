---
name: existing-profile-checker
version: "1.0"
description: >
  Check whether a brand already has a profile on a specific platform before creating one.
  Use this skill whenever preparing to create a new profile, claiming a listing, or auditing
  a brand's multi-surface presence. Always trigger before profile-creator to prevent duplicates.

inputs:
  required:
    - type: text
      label: "brand-name"
      description: "The brand or business name to search for"
    - type: text
      label: "brand-url"
      description: "The brand's primary website URL, used to confirm ownership of found profiles"
    - type: text
      label: "platform-url"
      description: "The platform domain to check (e.g., yelp.com, linkedin.com, crunchbase.com)"
  optional:
    - type: text
      label: "platform-name"
      description: "Human-readable platform name (e.g., Yelp, LinkedIn). Inferred from platform-url if not provided"
    - type: text
      label: "brand-category"
      description: "Industry or business category to help disambiguate common brand names"

outputs:
  - type: markdown
    label: "profile-check-verdict"
    description: "One of three verdicts: no existing profile, confirmed existing profile (with URL), or possible match needing member verification"

tools_used: [brave-search, page-scraper]
chains_from: [sheet-manager, competitor-profile-researcher]
chains_to: [profile-creator, sheet-manager]
tags: [profile-detection, duplicate-check, entity-signals, profile-creation]
---

## What This Skill Does

Searches a specified platform for existing profiles matching a brand, cross-references found profiles against the brand's website URL, and returns a definitive verdict on whether a profile already exists. This prevents duplicate profile creation, which fragments entity signals and weakens the brand's search presence.

## Context the Agent Needs

Creating a duplicate profile on a platform where the brand already has one is worse than having no profile at all — it splits entity signals, confuses search engines, and can trigger platform penalties. The ruling is always to claim and update the existing profile rather than create a new one. Existing profiles with outdated information are higher priority than net-new profiles because they already carry accumulated authority that would be lost if abandoned in favor of a duplicate.

Common brand names (e.g., "Summit", "Atlas", "Apex") will return many false positives. The brand URL is the primary disambiguation signal: if a found profile lists a website URL that matches the brand URL, that is a confirmed match. If a found profile has no website listed or a different one, it requires member verification.

## Workflow Steps

### STEP 1: Build search queries

Multiple search strategies increase the chance of finding an existing profile, especially on platforms without robust internal search.

**Input:** brand-name, platform-url, platform-name (if provided)
**Process:**
1. Construct query A: `"{brand-name}" site:{platform-url}`
2. Construct query B: `"{brand-name}" {platform-name or inferred name from platform-url}`
3. If brand-category is provided, construct query C: `"{brand-name}" {brand-category} site:{platform-url}`
**Output:** Two or three search queries ready to execute
**Decision gate:**
- Always proceed to Step 2

### STEP 2: Execute searches

Cast a wide net to surface all potential matches before filtering.

**Input:** Search queries from Step 1
**Process:**
1. Run query A using brave-search
2. Scan results for URLs on the platform domain (match against platform-url)
3. If query A returned zero platform-domain results, run query B
4. If brand-category was provided and results are ambiguous (3+ potential matches), run query C
5. Collect all unique URLs on the platform domain from search results
**Output:** List of candidate profile URLs on the target platform (may be empty)
**Decision gate:**
- If zero candidate URLs found → skip to Step 4 with "no existing profile found" verdict
- If one or more candidate URLs found → proceed to Step 3

### STEP 3: Verify candidates against brand URL

Cross-referencing the brand URL is the only reliable way to confirm ownership when brand names are ambiguous.

**Input:** Candidate profile URLs from Step 2, brand-url
**Process:**
1. For each candidate URL, scrape the profile page using page-scraper
2. Look for a website URL field on the profile page (common labels: "Website", "Homepage", "URL", "Visit website")
3. Compare the listed website URL against brand-url (normalize both: strip protocol, www, trailing slashes)
4. Check the business name on the profile for an exact or near-exact match to brand-name
5. If brand-category is provided, check whether the profile's listed category or description aligns
**Output:** Each candidate classified as "confirmed match", "possible match", or "not a match"
**Decision gate:**
- If any candidate is a confirmed match → proceed to Step 4 with "existing profile confirmed" verdict
- If candidates exist but none confirmed → proceed to Step 4 with "possible match" verdict for the closest candidate(s)
- If all candidates are "not a match" → proceed to Step 4 with "no existing profile found" verdict

### STEP 4: Compile verdict

A clear, actionable verdict prevents the agent from making a wrong call on profile creation.

**Input:** Classification results from Step 3 (or empty results from Step 2)
**Process:**
1. Select the appropriate verdict template from the Output Format section
2. If multiple profiles were found for the same brand on one platform, flag all of them
3. If the confirmed profile has outdated information (wrong address, old branding, missing details), note this as high priority for update
**Output:** Formatted verdict per the Output Format templates below
**Decision gate:**
- If verdict is "existing profile confirmed" → chain to sheet-manager to log the existing profile, then to profile-creator with instructions to claim/update (not create new)
- If verdict is "possible match" → halt automated profile creation, present to member for verification
- If verdict is "no existing profile found" → chain to profile-creator to proceed with new profile creation

## Output Format

### Verdict: No existing profile found

```
## Profile Check: {brand-name} on {platform-name}

**Verdict:** No existing profile found
**Platform:** {platform-url}
**Searches run:** {number of queries executed}
**Results reviewed:** {number of candidate URLs checked}

No matching profile was found for {brand-name} on {platform-name}. Safe to proceed with new profile creation.
```

### Verdict: Existing profile confirmed

```
## Profile Check: {brand-name} on {platform-name}

**Verdict:** Existing profile confirmed
**Profile URL:** {confirmed-profile-url}
**Website listed on profile:** {website-url-on-profile}
**Match confidence:** High — website URL matches brand URL
**Profile status:** {Active / Outdated — describe what needs updating}

Do NOT create a new profile. Claim and update this existing profile instead.
{If outdated: "Priority: HIGH — this profile has accumulated authority but contains outdated information."}
```

### Verdict: Possible match — needs member verification

```
## Profile Check: {brand-name} on {platform-name}

**Verdict:** Possible match — needs member verification
**Candidate URL(s):**
- {candidate-url-1} — {reason it might match, reason it's uncertain}
- {candidate-url-2} — {reason it might match, reason it's uncertain}

**Why verification is needed:** {explanation — e.g., "Brand name matches but no website URL listed on profile" or "Multiple businesses with this name exist on the platform"}

**Action required:** Member must confirm whether any of the above profiles belong to them before proceeding.
```

### Verdict: Multiple profiles detected

```
## Profile Check: {brand-name} on {platform-name}

**Verdict:** Multiple profiles detected
**Profiles found:**
- {profile-url-1} — {status: confirmed/possible, details}
- {profile-url-2} — {status: confirmed/possible, details}

**Warning:** Multiple profiles for the same brand on one platform fragment entity signals. Recommend consolidating into a single authoritative profile.
**Action required:** Member must identify which profile is authoritative. Remaining duplicates should be flagged for removal or merger.
```

## Edge Cases & Judgment Calls

**Incomplete input — brand-url not provided:**
Do not proceed without brand-url. It is the primary signal for confirming ownership. Ask the member to provide it before running the check.

**Ambiguous brand name — common name with many matches:**
If searches return more than 5 candidate profiles on the platform, narrow results using brand-category (if available) and brand-url matching. If still ambiguous after filtering, present the top 3 closest matches as "possible match" and request member verification. Never guess.

**Failed tool call — brave-search or page-scraper unavailable:**
If brave-search fails, report that the check could not be completed and recommend the member manually search the platform. Do not issue a "no existing profile found" verdict based on a failed search — absence of evidence is not evidence of absence.

**Platform blocks scraping — profile page cannot be read:**
If page-scraper cannot extract the profile page content, the candidate cannot be confirmed or ruled out. Classify it as "possible match" and include the URL for manual verification. Note the scraping failure in the verdict.

**Profile exists but under a different name variation:**
Brand names often appear differently on profiles (e.g., "Joe's Pizza" vs "Joes Pizza" vs "Joe's Pizza & Pasta"). Treat near-matches in brand name as candidates worth verifying. The website URL is the definitive signal, not the name.

**Multiple profiles for the same brand on one platform:**
Flag all of them. This is a consolidation opportunity, not a reason to create yet another profile. Use the "Multiple profiles detected" verdict template.

## What This Skill Does NOT Do

- Does not create, claim, or update profiles — that is profile-creator's job
- Does not check multiple platforms in one run — run the skill once per platform
- Does not log in to platforms or access authenticated profile management dashboards
- Does not determine which of multiple duplicate profiles should be the authoritative one — that decision requires the member
- Does not assess profile quality or completeness beyond noting obviously outdated information

## Examples

### Example 1: Confirmed existing profile (happy path)

**Input:**
- brand-name: "Riverstone Dental"
- brand-url: "https://riverstonedental.com"
- platform-url: "yelp.com"

**Agent action:**
1. Searches `"Riverstone Dental" site:yelp.com` via brave-search
2. Finds one result: `https://www.yelp.com/biz/riverstone-dental-austin`
3. Scrapes the Yelp profile page using page-scraper
4. Finds website field: `riverstonedental.com` — matches brand-url

**Agent output:**
```
## Profile Check: Riverstone Dental on Yelp

**Verdict:** Existing profile confirmed
**Profile URL:** https://www.yelp.com/biz/riverstone-dental-austin
**Website listed on profile:** riverstonedental.com
**Match confidence:** High — website URL matches brand URL
**Profile status:** Outdated — listed address is 412 Congress Ave but brand website shows 900 E 6th St

Do NOT create a new profile. Claim and update this existing profile instead.
Priority: HIGH — this profile has accumulated authority but contains outdated information.
```

### Example 2: Ambiguous brand name (edge case — common name)

**Input:**
- brand-name: "Summit"
- brand-url: "https://summitfinancial.com"
- platform-url: "linkedin.com"
- brand-category: "financial advisory"

**Agent action:**
1. Searches `"Summit" site:linkedin.com` — returns 50+ results across many industries
2. Narrows with `"Summit" "financial advisory" site:linkedin.com` — returns 4 company pages
3. Scrapes all 4 LinkedIn company pages:
   - Summit Financial Group (summitfg.com) — not a match
   - Summit Financial Strategies (summitfinancialstrategies.com) — not a match
   - Summit (summitfinancial.com) — website matches brand-url
   - Summit Financial Advisors (summitfa.com) — not a match

**Agent output:**
```
## Profile Check: Summit on LinkedIn

**Verdict:** Existing profile confirmed
**Profile URL:** https://www.linkedin.com/company/summit-financial
**Website listed on profile:** summitfinancial.com
**Match confidence:** High — website URL matches brand URL
**Profile status:** Active — company name, description, and logo present

Do NOT create a new profile. Claim and update this existing profile instead.
```

### Example 3: No profile found with scraping failure (edge case — partial tool failure)

**Input:**
- brand-name: "Oakwood Therapy"
- brand-url: "https://oakwoodtherapy.co.uk"
- platform-url: "healthgrades.com"

**Agent action:**
1. Searches `"Oakwood Therapy" site:healthgrades.com` — returns zero results
2. Searches `"Oakwood Therapy" Healthgrades` — returns one result that links to healthgrades.com
3. Attempts to scrape the candidate URL — page-scraper returns failure (blocked)

**Agent output:**
```
## Profile Check: Oakwood Therapy on Healthgrades

**Verdict:** Possible match — needs member verification
**Candidate URL(s):**
- https://www.healthgrades.com/group-directory/oakwood-therapy — found via search but profile page could not be scraped to verify website URL

**Why verification is needed:** A potential profile was found in search results but the profile page could not be read to confirm ownership via website URL matching. The scraping failure means this candidate cannot be automatically confirmed or ruled out.

**Action required:** Member must visit the candidate URL and confirm whether this profile belongs to them before proceeding.
```
