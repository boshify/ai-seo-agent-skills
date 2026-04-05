---
name: profile-creator
version: "2.0"
description: >
  Create a business profile on a target platform using a stealth headless browser, filling all available
  text fields and uploading a logo if the mechanism is straightforward. Uses playwright-stealth to bypass
  bot detection and CapSolver to resolve CAPTCHAs inline. Use this skill whenever a new profile needs to
  be created on a directory, citation site, social platform, or review platform. This skill produces a
  result object with profile URL, credentials, status, and notes.

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
      description: "Local file path to the brand logo/image for upload"
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

tools_used: [exec, curl]
chains_from: [existing-profile-checker, brand-info-assembler, sheet-manager]
chains_to: [sheet-manager]
tags: [profile-creation, automation, entity-signals, stealth-browser, capsolver]
---

## What This Skill Does

Navigates to a target platform via stealth headless browser, creates a new account with provided credentials, and fills every available text-based profile field with brand information. Uses `playwright-stealth` to remove bot detection signals and `capsolver` to solve CAPTCHAs (reCAPTCHA v2/v3, hCaptcha, Cloudflare Turnstile) automatically. Returns the profile URL on success or a structured status report describing the blocker encountered.

## Execution Model

This skill uses **exec** (not the browser tool) to run a Python stealth script. The agent writes the script for the specific platform's registration flow, then runs it via exec.

**Never use the `browser` tool for profile creation. Always use exec with the stealth script pattern below.**

## Stealth Script Pattern

Every profile creation script must start with this boilerplate. The agent adapts the `# --- Registration flow ---` section for each platform:

```python
#!/usr/bin/env python3
import asyncio, json, os, sys
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import capsolver

capsolver.api_key = os.environ.get("CAPSOLVER_API_KEY", "")

async def solve_captcha_if_present(page, url):
    """Detect and solve any CAPTCHA on the current page. Returns True if one was solved."""
    try:
        # hCaptcha
        hcaptcha_key = await page.evaluate("""
            () => {
                const el = document.querySelector('[data-sitekey]');
                if (!el) return null;
                const parent = el.closest('.h-captcha, [class*="hcaptcha"]');
                return parent ? el.getAttribute('data-sitekey') : null;
            }
        """)
        if hcaptcha_key:
            sol = capsolver.solve({
                "type": "HCaptchaTaskProxyLess",
                "websiteURL": url,
                "websiteKey": hcaptcha_key
            })
            await page.evaluate(
                f"(() => {{ const r = document.querySelector('[name=\"h-captcha-response\"]'); if (r) r.value = '{sol[\"gRecaptchaResponse\"]}'; }})()"
            )
            return True

        # reCAPTCHA v2
        recaptcha_el = await page.query_selector('.g-recaptcha')
        if recaptcha_el:
            recaptcha_key = await recaptcha_el.get_attribute('data-sitekey')
            if recaptcha_key:
                sol = capsolver.solve({
                    "type": "ReCaptchaV2TaskProxyLess",
                    "websiteURL": url,
                    "websiteKey": recaptcha_key
                })
                await page.evaluate(
                    f"(() => {{ const r = document.getElementById('g-recaptcha-response'); if (r) r.value = '{sol[\"gRecaptchaResponse\"]}'; }})()"
                )
                return True

        # Cloudflare Turnstile
        turnstile_el = await page.query_selector('.cf-turnstile')
        if turnstile_el:
            turnstile_key = await turnstile_el.get_attribute('data-sitekey')
            if turnstile_key:
                sol = capsolver.solve({
                    "type": "AntiTurnstileTaskProxyLess",
                    "websiteURL": url,
                    "websiteKey": turnstile_key
                })
                await page.evaluate(
                    f"(() => {{ const r = document.querySelector('[name=\"cf-turnstile-response\"]'); if (r) r.value = '{sol[\"token\"]}'; }})()"
                )
                return True

    except Exception as e:
        # CapSolver failed (unknown type, API error, insufficient balance) — log and continue
        print(json.dumps({"status": "captcha_required", "error": str(e)}), file=sys.stderr)

    return False

async def main():
    chromium_path = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH", "/usr/bin/chromium")
    result = {"status": "other_blocker", "profile_url": None, "notes": ""}

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                executable_path=chromium_path,
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
                      "--window-size=1280,800"]
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                locale="en-US",
                timezone_id="America/New_York"
            )
            page = await context.new_page()
            await stealth_async(page)  # MUST be called before any navigation

            # --- Registration flow (agent writes this section per platform) ---
            # Example structure:
            #
            # await page.goto("https://example.com/signup", wait_until="networkidle")
            # await solve_captcha_if_present(page, page.url)
            #
            # await page.fill('[name="email"]', brand_info["email"])
            # await page.fill('[name="password"]', brand_info["password"])
            # await page.click('button[type="submit"]')
            # await page.wait_for_load_state("networkidle")
            # await solve_captcha_if_present(page, page.url)
            #
            # ... fill profile fields ...
            #
            # result = {"status": "created", "profile_url": page.url, "notes": ""}

            await browser.close()

    except Exception as e:
        result["notes"] = str(e)

    print(json.dumps(result))

asyncio.run(main())
```

**Script execution:**
```bash
python3 /tmp/profile_creator_{platform}.py
```

Write the script to `/tmp/`, run it via exec, parse the JSON from stdout.

**CAPTCHA calling convention:**
- Call `await solve_captcha_if_present(page, page.url)` after every `page.goto()` and after every form submit
- CapSolver handles reCAPTCHA v2, hCaptcha, and Cloudflare Turnstile automatically
- If CapSolver raises (unknown type, API error), the script logs to stderr and continues — the caller catches `captcha_required` from the result if the flow couldn't proceed
- reCAPTCHA v3 (invisible, score-based) does not need solving — stealth alone is sufficient for most v3 gates

## Context the Agent Needs

Every platform has a different registration flow. The agent must inspect the platform's signup page structure (via `web_fetch` or a quick page snapshot before writing the script) to understand the form fields and submit flow. Each platform invocation gets a unique `platform_description` from the brand info package — never reuse the same description across platforms.

## Workflow Steps

### STEP 1: Inspect the registration flow

Before writing the script, understand the form structure.

**Process:**
1. Use `web_fetch` on `platform_url` to read the page HTML/structure
2. Identify: form field names/selectors, submit button selector, multi-step vs single-page flow, any visible CAPTCHA widget
3. Note any redirects after registration (dashboard URL pattern, profile edit URL)
**Output:** Enough information to write targeted selectors in the script
**Decision gate:**
- If registration path is clear → proceed to write and run the script (Steps 2–5)
- If page is completely inaccessible (connection refused, 403 before any interaction) → return status `other_blocker`
- If paywall is evident from the page content → return status `paywall`

### STEP 2: Write and run the account creation script

**Process:**
1. Write a Python script using the stealth pattern above, filling in the registration form selectors from Step 1
2. Include `await solve_captcha_if_present(page, page.url)` after the submit click
3. Run the script via exec: `python3 /tmp/profile_creator_{platform_domain}.py`
4. Parse the JSON result from stdout
**Output:** Account created and logged in, or a blocker status
**Decision gate:**
- If `status: created` or session shows logged-in dashboard → proceed to Step 3
- If result contains `status: captcha_required` (CapSolver failed or unsupported type) → return that status with manual assist package
- If `status: verification_needed` → return that status with notes
- If script errors or times out → retry once; if still failing, return `other_blocker`

### STEP 3: Fill all available profile fields

**Process:**
1. Extend the script (or write a follow-up script) to navigate to the profile editing section
2. Fill: business name, description (`platform_description`), website URL, category, phone (if provided), address (if provided)
3. Fill any other visible text fields relevant to the brand
4. Run via exec
**Output:** All automatable text fields populated

### STEP 4: Upload logo if applicable

**Process:**
1. If `logo_path` is not provided → skip to Step 5
2. Add logo upload to the script: locate `<input type="file">`, call `page.set_input_files(selector, logo_path)`
3. Run via exec, confirm success (check for thumbnail or success message)
**Output:** Logo uploaded, or note explaining skip

### STEP 5: Save and capture the profile URL

**Process:**
1. Click Save/Submit in the script
2. Navigate to the public profile page
3. Capture the URL
4. Return the final result JSON
**Output:** Profile result object with `status: created` and `profile_url`

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
- `captcha_required` — CAPTCHA type not supported by CapSolver, or CapSolver API failed; notes must include manual assist package
- `verification_needed` — Email, phone, or 2FA verification required to continue
- `other_blocker` — Any other issue (account exists, platform down, form broken, stealth still detected, etc.)

**Manual assist package (required for all non-`created` statuses):**
Notes must include a copy-paste-ready package: signup URL, business name, description, website, category, email, password — each clearly labeled.

## Edge Cases & Judgment Calls

**Stealth still detected (IP-level block):**
Some platforms block Railway/cloud datacenter IPs entirely regardless of browser stealth. This shows as an immediate redirect to a "suspicious activity" or "access denied" page before any form interaction. Return `other_blocker` with notes that it appears to be an IP-level block rather than fingerprint detection.

**CapSolver returns wrong token / CAPTCHA not submitted correctly:**
Some platforms use custom CAPTCHA submission (non-standard hidden input names). If the CAPTCHA solve succeeds but form still fails, add platform-specific token injection to the script before retrying.

**Multi-step registration wizard:**
Complete each step sequentially in the script, calling `solve_captcha_if_present` at each step transition. If a step blocks entirely (mandatory phone verification mid-wizard), return `verification_needed`.

**Incomplete brand info — missing optional fields:**
Fill every field you have data for. Leave missing fields empty. Note skipped fields in `fields_skipped`. Never invent a phone number, address, or hours.

**Ambiguous registration paths:**
Prefer "Business" or "Company" path over "Individual". Try "Create Account" before "Claim Your Listing".

**Platform requires a work email domain:**
Return `verification_needed` with notes specifying the business domain email requirement.

**Dropdown category has no exact match:**
Select the closest parent category. Note the substitution in `notes`.

**Script exec timeout:**
Default exec timeout is 5 minutes. If the platform is slow (lots of page loads), structure the script to complete each phase quickly. If it times out, return `other_blocker` with the last known state.

## What This Skill Does NOT Do

- Does not handle email verification clicks (reports requirement and exits)
- Does not complete phone verification, SMS, or 2FA flows
- Does not create profiles that require payment
- Does not handle complex image operations (cropping, drag-and-drop only uploads)
- Does not manage ongoing profile maintenance
- Does not create multiple profiles on the same platform in one invocation
- Does not reuse descriptions across platforms

## Examples

### Example 1: Successful profile creation with CAPTCHA solved automatically

**User:** Create a profile for "Acme Plumbing" on yellowpages.com

**Agent action:**
1. `web_fetch` on yellowpages.com/advertise — identifies form selectors
2. Writes stealth script with email/password fields + `solve_captcha_if_present` after submit
3. Runs script via exec — CapSolver resolves reCAPTCHA v2 on form submit automatically
4. Navigates to profile edit, fills all fields
5. Uploads logo via `page.set_input_files`

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
  "notes": "reCAPTCHA v2 on registration form solved automatically via CapSolver. Profile created successfully."
}
```

### Example 2: Email verification required

**User:** Create a profile for "Bloom Digital" on clutch.co

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
  "notes": "Account registered. Platform requires email verification at profiles@bloomdigital.io before profile editing is accessible.\n\n**Manual step:** Click verification link in email, then log in and complete the profile."
}
```

### Example 3: IP-level block (datacenter IP)

**User:** Create a profile for "Summit Legal" on linkedin.com

**Agent action:**
1. Writes stealth script, navigates to linkedin.com/signup
2. Page immediately shows "Unusual activity detected" before any form interaction

**Agent output:**
```json
{
  "platform": "linkedin.com",
  "profile_url": null,
  "credentials": {
    "email": "listings@summitlegal.com",
    "password": "Kp5#wN8mR!2v"
  },
  "status": "other_blocker",
  "fields_filled": [],
  "fields_skipped": ["business_name", "description", "website", "category", "logo"],
  "notes": "LinkedIn is blocking access at the IP level (datacenter IP detection) before any form interaction. Stealth browser fingerprint is not the issue — this requires a residential IP.\n\n**Manual signup — copy-paste ready:**\nSignup URL: https://www.linkedin.com/signup\nBusiness name: Summit Legal\nDescription: Summit Legal is a full-service law firm in Denver, CO offering business litigation, employment law, and contract negotiation.\nWebsite: https://summitlegal.com\nEmail: listings@summitlegal.com\nPassword: Kp5#wN8mR!2v"
}
```
