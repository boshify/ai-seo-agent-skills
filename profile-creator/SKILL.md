---
name: profile-creator
version: "1.0"
description: >
  Create a business profile on a target platform using a headless browser, filling all available
  text fields and uploading a logo if the mechanism is straightforward. Use this skill whenever
  a new profile needs to be created on a directory, citation site, social platform, or review
  platform. This skill produces a result object with profile URL, credentials, status, and notes.

inputs:
  required:
    - type: text
      label: "platform_url"
      description: "Sign-up or registration page URL for the target platform"
    - type: object
      label: "brand_info"
      description: "Brand info package: name, website_url, category, platform_description (unique to this platform), email, password"
  optional:
    - type: text
      label: "logo_path"
      description: "Local file path or Drive URL to the brand logo/image for upload"
    - type: text
      label: "phone"
      description: "Business phone number if the platform requests one"
    - type: text
      label: "address"
      description: "Business address if the platform requests one"

outputs:
  - type: json
    label: "profile-result"
    description: "Object with: profile_url, credentials (email, password), status (created | paywall | captcha_required | verification_needed | other_blocker), notes"

tools_used: [browser, curl]
chains_from: [existing-profile-checker, brand-info-assembler, sheet-manager]
chains_to: [sheet-manager]
tags: [profile-creation, automation, entity-signals, headless-browser]
---

## What This Skill Does

Navigates to a target platform via headless browser, creates a new account with provided credentials, and fills every available text-based profile field with brand information. Returns the profile URL on success or a structured status report describing the blocker encountered.

## Context the Agent Needs

Every platform has a different registration flow — some require email verification before profile editing, some gate features behind a paywall after account creation, and some present CAPTCHAs mid-flow. The agent must attempt the fullest possible profile completion in a single session but gracefully exit and report when it hits an unautomatable wall. Each platform invocation gets a unique `platform_description` from the brand info package — never reuse the same description across platforms, as duplicate content across citation profiles damages entity signal quality.

## Workflow Steps

### STEP 1: Navigate to the platform and locate the registration flow

Understanding the registration entry point determines whether the platform is automatable at all.

**Input:** `platform_url` from inputs
**Process:**
1. Launch headless browser and navigate to `platform_url`
2. Wait for the page to fully load (network idle or DOM stable)
3. Identify the sign-up or registration form — look for "Sign Up", "Create Account", "Register", or "Claim Your Listing" CTAs
4. If no registration form is visible, check for a link to a separate sign-up page and navigate there
5. If the page redirects to a login-only flow, check for a "Create Account" or "New User" link
**Output:** Browser positioned on the registration form, or a blocker identified
**Decision gate:**
- If registration form is found → proceed to Step 2
- If paywall blocks registration → return status `paywall` with notes describing the paywall
- If no registration path exists → return status `other_blocker` with notes

### STEP 2: Create the account

Account creation is the prerequisite for all profile field population.

**Input:** `brand_info.email`, `brand_info.password`, and the registration form from Step 1
**Process:**
1. Fill the email field with `brand_info.email`
2. Fill the password field with `brand_info.password` (and confirm-password if present)
3. Fill any other required fields (first name, last name, business name) using brand info
4. Accept terms of service checkbox if present
5. Submit the registration form
**Output:** Account created confirmation, or a blocker encountered
**Decision gate:**
- If account is created and redirected to profile/dashboard → proceed to Step 3
- If CAPTCHA appears → return status `captcha_required` with notes
- If email verification is required before proceeding → return status `verification_needed` with notes including what verification method is required
- If phone verification or 2FA is required → return status `verification_needed` with notes specifying phone/2FA requirement
- If "email already registered" → return status `other_blocker` with notes

### STEP 3: Fill all available profile fields

Maximizing field completion strengthens the entity signal from this profile.

**Input:** `brand_info` package, optional `phone`, optional `address`, profile editing interface from Step 2
**Process:**
1. Navigate to the profile editing section if not already there (look for "Edit Profile", "Business Info", "Settings")
2. Fill business name with `brand_info.name`
3. Fill description/about/bio with `brand_info.platform_description` — this text is unique to this platform
4. Fill website URL with `brand_info.website_url`
5. Fill category/industry with `brand_info.category` — use the closest match from any dropdown, or type it if free-text
6. Fill every other visible text field that is relevant: phone, address, hours, tagline, social links
**Output:** All automatable text fields populated
**Decision gate:**
- If all fields are filled and saveable → proceed to Step 4
- If profile form requires fields not in the brand info package → fill what is available, note missing fields, proceed to Step 4

### STEP 4: Upload logo if applicable

A logo strengthens visual entity recognition across platforms.

**Input:** `logo_path` (optional), the profile editing interface
**Process:**
1. If `logo_path` is not provided → skip to Step 5
2. Locate the logo/avatar/image upload element on the profile page
3. If the upload mechanism is a standard file input (`<input type="file">`) → set the file path and trigger upload
4. If the upload requires cropping, drag-and-drop only, or a complex modal workflow → skip and note in output
5. Confirm the image uploaded successfully (check for preview thumbnail or success message)
**Output:** Logo uploaded, or note explaining why it was skipped
**Decision gate:**
- If upload succeeded or was skipped → proceed to Step 5
- If upload caused an error → note the error, proceed to Step 5

### STEP 5: Save and capture the profile URL

The profile URL is the primary deliverable that proves the profile exists.

**Input:** Completed profile form from Steps 3-4
**Process:**
1. Click "Save", "Update Profile", "Submit", or equivalent button
2. Wait for save confirmation
3. Navigate to the public-facing profile page (look for "View Profile", "Public Profile", or construct from username/slug)
4. Capture the profile URL from the browser address bar
5. If no public profile URL is discoverable, note this and use the dashboard URL
**Output:** Profile result object
**Decision gate:**
- If profile URL captured → return result with status `created`
- If save failed → return status `other_blocker` with error details

## Output Format

```json
{
  "platform": "{platform domain}",
  "profile_url": "{public profile URL or null}",
  "credentials": {
    "email": "{email used}",
    "password": "{password used}"
  },
  "status": "created | paywall | captcha_required | verification_needed | other_blocker",
  "fields_filled": ["business_name", "description", "website", "category", "phone", "logo"],
  "fields_skipped": ["hours", "social_links"],
  "notes": "{Human-readable explanation of any issues, blockers, or partial completion details}"
}
```

**Status values:**
- `created` — Profile is live and accessible at `profile_url`
- `paywall` — Platform requires payment before profile creation or completion
- `captcha_required` — CAPTCHA blocked progress; manual intervention needed
- `verification_needed` — Email, phone, or 2FA verification required to continue
- `other_blocker` — Any other issue (account exists, platform down, form broken, etc.)

## Edge Cases & Judgment Calls

**Incomplete input — brand info package missing optional fields:**
Fill every field you have data for. Leave missing fields empty rather than fabricating data. Note which fields were skipped in `fields_skipped`. Never invent a phone number, address, or hours of operation.

**Ambiguous classification — platform has multiple registration paths:**
Prefer the "Business" or "Company" registration path over "Individual" or "Personal". If the platform offers "Claim Your Listing" alongside "Create Account", try "Create Account" first — claiming often requires verification of an existing listing.

**Oversized output — platform has dozens of profile fields:**
Fill all text-based fields that accept brand-relevant information. Skip fields that require external data not in the brand info package (e.g., license numbers, tax IDs, employee count). Report skipped fields in the output.

**Failed tool call — browser crashes or page fails to load:**
Retry navigation once. If the page still fails, return status `other_blocker` with the error. Do not retry more than once — the platform may be down or blocking headless browsers entirely.

**Platform requires a work email domain (not Gmail/Outlook):**
Return status `verification_needed` with notes specifying that the platform requires a business domain email. Do not attempt to use a personal email if the form explicitly rejects it.

**Dropdown category has no exact match:**
Select the closest parent category available. If "Digital Marketing Agency" is not listed but "Marketing" or "Advertising" is, use the broader category. Note the substitution in `notes`.

**Registration form is a multi-step wizard:**
Complete each step sequentially. If a step requires information not available in the brand info package, fill what you can and proceed. If a step blocks entirely (e.g., mandatory phone verification mid-wizard), report the step number and blocker.

**Platform detects headless browser and blocks access:**
Return status `other_blocker` with notes indicating bot detection. Do not attempt to bypass bot detection mechanisms — this is outside the skill's scope.

## What This Skill Does NOT Do

- Does not solve CAPTCHAs — reports them as blockers for manual resolution
- Does not complete phone verification, SMS confirmation, or 2FA flows
- Does not handle email verification clicks — reports the requirement and exits
- Does not bypass bot detection or anti-automation measures
- Does not create profiles that require payment — reports paywalls as blockers
- Does not reuse descriptions across platforms — each platform gets unique text from `brand_info.platform_description`
- Does not handle complex image operations (cropping, resizing, drag-and-drop uploads)
- Does not manage ongoing profile maintenance (updates, responses to reviews, posting)
- Does not create multiple profiles on the same platform in one invocation

## Examples

### Example 1: Successful profile creation on a business directory (happy path)

**User:** Create a profile for "Acme Plumbing" on yellowpages.com

**Brand info provided:**
```json
{
  "name": "Acme Plumbing",
  "website_url": "https://acmeplumbing.com",
  "category": "Plumber",
  "platform_description": "Acme Plumbing provides residential and commercial plumbing services in Austin, TX. Licensed and insured with over 15 years of experience in pipe repair, water heater installation, and emergency plumbing.",
  "email": "listings@acmeplumbing.com",
  "password": "Xr9#mK2pL!4w"
}
```

**Agent action:**
1. Navigates to yellowpages.com, finds "Add Your Business" link
2. Fills email and password, submits registration — account created
3. Navigates to profile edit, fills: business name, description (unique platform text), website, category ("Plumber" matched from dropdown), phone, address
4. Uploads logo via standard file input — success
5. Saves profile, navigates to public listing

**Agent output:**
```json
{
  "platform": "yellowpages.com",
  "profile_url": "https://www.yellowpages.com/austin-tx/acme-plumbing-12345",
  "credentials": {
    "email": "listings@acmeplumbing.com",
    "password": "Xr9#mK2pL!4w"
  },
  "status": "created",
  "fields_filled": ["business_name", "description", "website", "category", "phone", "address", "logo"],
  "fields_skipped": ["hours", "payment_methods"],
  "notes": "Profile created successfully. Hours and payment methods were available fields but not provided in brand info. Category 'Plumber' matched exactly in dropdown."
}
```

### Example 2: Platform requires email verification (edge case — verification blocker)

**User:** Create a profile for "Bloom Digital" on clutch.co

**Brand info provided:**
```json
{
  "name": "Bloom Digital",
  "website_url": "https://bloomdigital.io",
  "category": "Digital Marketing Agency",
  "platform_description": "Bloom Digital is a performance marketing agency specializing in paid search and programmatic advertising for B2B SaaS companies.",
  "email": "profiles@bloomdigital.io",
  "password": "Tn7$bQ3rJ!9x"
}
```

**Agent action:**
1. Navigates to clutch.co, finds "Get Listed" registration form
2. Fills email, password, company name — submits form
3. Platform displays "Check your email to verify your account before continuing"
4. No profile editing is accessible without verification

**Agent output:**
```json
{
  "platform": "clutch.co",
  "profile_url": null,
  "credentials": {
    "email": "profiles@bloomdigital.io",
    "password": "Tn7$bQ3rJ!9x"
  },
  "status": "verification_needed",
  "fields_filled": ["business_name", "email"],
  "fields_skipped": ["description", "website", "category", "logo"],
  "notes": "Account registration submitted. Platform requires email verification at profiles@bloomdigital.io before profile editing is accessible. No profile fields could be filled beyond the registration form. Manual step: click verification link in email, then re-run or complete profile manually."
}
```

### Example 3: CAPTCHA blocks registration (edge case — unautomatable wall)

**User:** Create a profile for "Summit Legal" on avvo.com

**Agent action:**
1. Navigates to avvo.com, finds attorney registration form
2. Fills email and password fields
3. reCAPTCHA v2 challenge appears on form submission

**Agent output:**
```json
{
  "platform": "avvo.com",
  "profile_url": null,
  "credentials": {
    "email": "listings@summitlegal.com",
    "password": "Kp5#wN8mR!2v"
  },
  "status": "captcha_required",
  "fields_filled": ["email"],
  "fields_skipped": ["business_name", "description", "website", "category", "logo"],
  "notes": "Registration form presents a reCAPTCHA v2 challenge on submission. Account was not created. Manual step: complete CAPTCHA at https://www.avvo.com/registration, then profile fields can be filled in a follow-up invocation or manually."
}
```
