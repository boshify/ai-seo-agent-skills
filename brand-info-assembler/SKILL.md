---
name: brand-info-assembler
version: "1.0"
description: >
  Assemble a reusable brand info package with multiple unique descriptions for profile creation.
  Use this skill whenever creating profiles, listings, or directory submissions that need brand
  descriptions. Always trigger when a brand needs unique copy across multiple platforms.

inputs:
  required:
    - type: text
      label: "brand-name"
      description: "The official business or brand name"
    - type: text
      label: "brand-url"
      description: "The brand's primary website URL (must start with http:// or https://)"
  optional:
    - type: text
      label: "brand-category"
      description: "Industry or business category (e.g., 'Digital Marketing Agency', 'SaaS - Project Management')"
    - type: text
      label: "existing-descriptions"
      description: "Any existing brand descriptions the agent can use as source material"
    - type: text
      label: "logo-drive-folder"
      description: "Google Drive folder URL or path containing brand logos and images"
    - type: text
      label: "platform-name"
      description: "Specific platform to generate tailored copy for (e.g., 'LinkedIn', 'Yelp', 'G2')"

outputs:
  - type: json
    label: "brand-info-package"
    description: "Complete brand info package: name, URL, category, tagline, descriptions array (5-10 unique), logo locations, source material"
  - type: text
    label: "platform-description"
    description: "Single platform-tailored description when platform-name is provided"

tools_used: [page-scraper]
chains_from: [sheet-manager]
chains_to: [profile-creator, existing-profile-checker]
tags: [brand-info, content-generation, entity-signals, profile-creation]
---

## What This Skill Does

Scrapes a brand's website and assembles a reusable brand info package containing multiple unique descriptions written in distinct language, ready for use across different profiles and directories. When called with a specific platform name, generates additional platform-tailored copy on demand.

## Context the Agent Needs

Every profile created for a brand MUST have unique text. Copy-pasting the same description across profiles is a common mistake that weakens entity signals and can trigger duplicate content flags on platforms. This skill exists to solve that problem at the source: generate the descriptions once, use them everywhere, and never repeat the same wording twice.

Descriptions must accurately reflect the business using distinct language each time. They are factual restatements, not marketing fluff. The source material comes from the brand's own website (scraped via page-scraper) and any existing descriptions provided. The agent does not invent services or capabilities the brand does not actually offer.

Platform tone matters. A LinkedIn company description reads differently from a Yelp business description or a G2 product listing. When generating per-platform copy, adapt length, vocabulary, and emphasis to match what performs well on that platform.

## Workflow Steps

### STEP 1: Gather existing brand information

Collect everything available before scraping so the agent knows what gaps to fill.

**Input:** brand-name, brand-url, and any optional inputs (brand-category, existing-descriptions, logo-drive-folder)
**Process:**
1. Record brand-name and brand-url as the canonical identifiers
2. If brand-category is provided, record it; otherwise mark it for extraction in Step 2
3. If existing-descriptions are provided, parse them as source material for rewriting
4. If logo-drive-folder is provided, record the location for inclusion in the package
**Output:** Partial brand info record with known fields populated and gaps identified
**Decision gate:**
- If brand-url is valid → proceed to Step 2
- If brand-url is missing or malformed → ask the user for a corrected URL before continuing

### STEP 2: Scrape the brand's website

Extract source material directly from the brand's homepage to ground all descriptions in reality.

**Input:** brand-url from Step 1
**Process:**
1. Use page-scraper to scrape brand-url with `max_chars: 10000` to capture sufficient content
2. Extract from the response: meta description, h1, tagline (if identifiable), about/company text, service or product descriptions
3. If brand-category was not provided, infer it from the page content (industry, product type, service area)
4. If the homepage is thin on content, scrape the About page (try `/about`, `/about-us`, `/company`) as a secondary source
5. Compile all extracted text as raw source material
**Output:** Structured source material: tagline, about text, services/products list, meta description, inferred category
**Decision gate:**
- If sufficient source material extracted (tagline or about text + at least a service/product description) → proceed to Step 3
- If scrape failed or page is too thin → use existing-descriptions as primary source; if none exist, ask the user to provide a brief business description

### STEP 3: Generate unique brand descriptions

Create multiple descriptions that say the same things in genuinely different ways.

**Input:** Source material from Step 2, existing-descriptions from Step 1 if any
**Process:**
1. Write 5-10 unique brand descriptions, each between 50 and 200 words
2. Vary sentence structure, opening words, vocabulary, and emphasis across descriptions — no two should start the same way or share phrasing
3. Every description must be factually accurate to the source material; do not invent services, awards, or claims
4. Mix description lengths: 2-3 short (50-80 words) for social profiles, 3-4 medium (80-150 words) for directories, 2-3 long (150-200 words) for detailed listings
5. If existing-descriptions were provided, rewrite them as additional variants rather than including them verbatim
**Output:** Array of 5-10 unique descriptions, each tagged with approximate word count and suggested use (short/social, medium/directory, long/detailed)
**Decision gate:**
- If all descriptions are factually grounded and linguistically distinct → proceed to Step 4
- If source material was too thin to produce 5 distinct descriptions → produce as many as the material supports (minimum 3) and note the limitation

### STEP 4: Assemble the brand info package

Package everything into a structured, reusable format that downstream skills consume.

**Input:** All data from Steps 1-3
**Process:**
1. Compile the final brand info package with all fields populated
2. Include the raw source material so downstream skills can generate additional copy if needed
3. If platform-name was provided, proceed to Step 5 before finalizing
4. Validate: every description in the array is unique (no duplicate sentences across descriptions)
**Output:** Complete brand-info-package (see Output Format below)
**Decision gate:**
- If platform-name was provided → proceed to Step 5
- If no platform-name → package is complete, return it

### STEP 5: Generate platform-specific copy

Tailor a description for the specific platform's tone and format expectations.

**Input:** Brand info package from Step 4, platform-name
**Process:**
1. Identify platform conventions: LinkedIn (professional, capability-focused, 1-2 paragraphs), Yelp (service-focused, local, conversational), G2 (product-focused, feature-benefit pairs), Crunchbase (factual, founding story, metrics), social profiles (single punchy sentence or tagline)
2. Write one platform-specific description that matches the platform's typical tone and length
3. Do not reuse any description verbatim from the existing array — this must be net-new copy
4. Include platform-specific elements where relevant (e.g., "Visit us at..." for Yelp, product categories for G2)
**Output:** Platform-tailored description appended to the package and returned separately
**Decision gate:**
- If description matches platform conventions → done
- If platform is unknown → write a medium-length general-purpose description and note that the agent did not have platform-specific guidance

## Output Format

### Brand Info Package:
```
## Brand Info Package: {brand-name}

**Name:** {brand-name}
**URL:** {brand-url}
**Category:** {brand-category}
**Tagline:** {tagline extracted from website, or "Not found"}
**Logo Location:** {logo-drive-folder, or "Not provided"}

### Source Material
- **Meta Description:** {meta description from website}
- **About Text:** {about/company text, summarized if lengthy}
- **Services/Products:** {comma-separated list}

### Unique Descriptions

**Description 1** (short / social — ~{n} words)
{description text}

**Description 2** (medium / directory — ~{n} words)
{description text}

**Description 3** (long / detailed — ~{n} words)
{description text}

...

### Platform-Specific Copy
**{platform-name}:** {platform-tailored description}
(Only included when platform-name was provided)
```

### Platform-specific description (standalone):
```
## {platform-name} Description for {brand-name}

{platform-tailored description}

**Tone:** {tone used, e.g., "Professional/capability-focused"}
**Word Count:** ~{n}
```

## Edge Cases & Judgment Calls

**Incomplete input — brand-url not provided or unreachable:**
If the URL is missing, ask for it. If the scrape fails completely (page-scraper returns failure even after fallback), rely on existing-descriptions and brand-category to generate descriptions. Clearly note in the output that descriptions are based on provided text only, not verified against the live website.

**Ambiguous category — cannot determine industry from website:**
If the homepage does not clearly indicate the business type and no brand-category was provided, ask the user. Do not guess an industry — an incorrect category leads to wrong tone and vocabulary in every downstream profile.

**Oversized source material — website has extensive content:**
Do not dump the entire scrape into the package. Summarize the about text to 2-3 sentences, list services/products as a concise comma-separated list, and keep the meta description as-is. The source material section exists for reference, not as a content dump.

**Thin website — single-page site or under-construction page:**
If the website yields fewer than 3 usable sentences of source material, combine whatever was scraped with existing-descriptions. If the total is still insufficient, produce 3 descriptions (the minimum viable set) and flag that the user should provide more context about their business to improve output quality.

**Existing descriptions are marketing fluff:**
Rewrite them into factual language. Strip superlatives ("world's best", "industry-leading") unless they are verifiable claims. The goal is accurate descriptions, not advertising copy.

**Unknown platform requested:**
Generate a medium-length, neutral-tone description. Note in the output that no platform-specific guidance was available, so the copy may need manual adjustment for that platform's conventions.

## What This Skill Does NOT Do

- Does not create or submit profiles on any platform — that is profile-creator's job
- Does not check whether profiles already exist — that is existing-profile-checker's job
- Does not generate visual brand assets (logos, banners, images)
- Does not verify business information (address, phone, hours) — only works with brand identity and descriptions
- Does not write full website copy, landing pages, or marketing campaigns
- Does not translate descriptions into other languages

## Examples

### Example 1: Full brand info package for a digital agency (happy path)

**User:** "Assemble brand info for Rank Builders, https://rankbuilders.com — they're a digital marketing agency."

**Agent action:**
1. Records brand-name: "Rank Builders", brand-url: "https://rankbuilders.com", brand-category: "Digital Marketing Agency"
2. Scrapes https://rankbuilders.com via page-scraper with `max_chars: 10000`
3. Extracts: meta description ("Rank Builders helps businesses grow through SEO, content marketing, and link building"), tagline ("Growth Through Search"), services list (SEO, Content Marketing, Link Building, Technical Audits)
4. Generates 7 unique descriptions

**Agent output:**
```
## Brand Info Package: Rank Builders

**Name:** Rank Builders
**URL:** https://rankbuilders.com
**Category:** Digital Marketing Agency
**Tagline:** Growth Through Search
**Logo Location:** Not provided

### Source Material
- **Meta Description:** Rank Builders helps businesses grow through SEO, content marketing, and link building
- **About Text:** Founded to help businesses compete in organic search, Rank Builders delivers SEO strategy, content production, and link acquisition for companies serious about long-term growth.
- **Services/Products:** SEO, Content Marketing, Link Building, Technical Audits

### Unique Descriptions

**Description 1** (short / social — ~55 words)
Rank Builders is a digital marketing agency focused on organic search growth. The team delivers SEO strategy, content marketing, and link building services for businesses that want to compete in search results over the long term.

**Description 2** (short / social — ~48 words)
A search-focused digital agency, Rank Builders works with businesses to improve their organic visibility through technical SEO audits, content production, and strategic link acquisition.

**Description 3** (medium / directory — ~90 words)
Rank Builders provides SEO and content marketing services designed to drive sustainable organic traffic. Their approach combines technical site audits with ongoing content production and link building, giving businesses a complete search strategy rather than isolated tactics. The agency works with companies that treat SEO as a long-term growth channel, not a one-time project.

...
```

### Example 2: Thin website with platform-specific request (edge case)

**User:** "I need brand info for NovaTech Solutions, https://novatech-solutions.io — also give me a LinkedIn description. The site is still being built."

**Agent action:**
1. Records brand-name: "NovaTech Solutions", brand-url: "https://novatech-solutions.io", platform-name: "LinkedIn"
2. Scrapes the URL — page-scraper returns minimal content: just a tagline ("Innovation Through Technology") and a single sentence about cloud consulting
3. No about page found; scrape of `/about` returns 404
4. Source material insufficient for 5 descriptions — generates 3 descriptions from available material
5. Generates LinkedIn-specific copy separately

**Agent output:**
```
## Brand Info Package: NovaTech Solutions

**Name:** NovaTech Solutions
**URL:** https://novatech-solutions.io
**Category:** Technology Consulting (inferred)
**Tagline:** Innovation Through Technology
**Logo Location:** Not provided

### Source Material
- **Meta Description:** Not found
- **About Text:** NovaTech Solutions provides cloud consulting services.
- **Services/Products:** Cloud Consulting

### Unique Descriptions

**Description 1** (short / social — ~35 words)
NovaTech Solutions is a technology consulting firm specializing in cloud services, helping organizations modernize their infrastructure and operations.

**Description 2** (medium / directory — ~60 words)
Focused on cloud consulting, NovaTech Solutions partners with businesses navigating the shift to cloud-based infrastructure. The company provides guidance on cloud strategy, migration, and ongoing management for organizations looking to modernize their technology stack.

**Description 3** (medium / directory — ~55 words)
NovaTech Solutions delivers cloud consulting services for businesses moving to or optimizing cloud environments. Their work spans strategy development, implementation planning, and infrastructure management.

> Note: The brand's website is under construction with minimal content. Only 3 descriptions could be generated. Provide additional details about NovaTech's services, differentiators, and target market to expand the description set.

### Platform-Specific Copy
**LinkedIn:** NovaTech Solutions helps businesses modernize through expert cloud consulting. From migration strategy to infrastructure optimization, the team works with organizations ready to move their operations to the cloud. Whether you are planning your first cloud deployment or refining an existing setup, NovaTech brings the technical depth to make it work.
```

### Example 3: Generating additional platform copy for an existing package

**User:** "I already have the brand info for Rank Builders. Now give me a Yelp description."

**Agent action:**
1. Retrieves existing brand info package from prior context
2. Generates Yelp-specific copy: service-focused, local-friendly tone, conversational

**Agent output:**
```
## Yelp Description for Rank Builders

Rank Builders is a digital marketing agency that focuses on getting businesses found in search results. They handle everything from SEO audits to content creation and link building — all geared toward helping companies show up when potential customers are searching online. If you are looking for a team to manage your organic search strategy, Rank Builders takes a hands-on, long-term approach rather than promising quick fixes.

**Tone:** Service-focused / conversational
**Word Count:** ~65
```
