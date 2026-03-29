---
name: proof-catalog
version: "1.0"
description: >
  Scrapes a member's website and public presence for existing proof assets, then
  catalogs and ranks them by outcome-proximity. Use this skill whenever the
  target-market-landscape-analysis process reaches Step 7 (proof catalog), or whenever
  a member asks to audit their proof, review their credibility assets, or assess their
  trust signals. This skill produces a ranked proof inventory with gap analysis. Always
  trigger when proof, trust signals, testimonials, case studies, credibility, or social
  proof intent is present — even if phrased casually.

inputs:
  required:
    - type: text
      label: "member-domain"
      description: "The member's website domain URL"
  optional:
    - type: text
      label: "brand-name"
      description: "The member's brand or business name (for Google review lookup)"
    - type: text
      label: "primary-outcome"
      description: "The primary result/outcome the member sells (for outcome-proximity ranking)"
    - type: text
      label: "differentiation-angle"
      description: "The member's differentiation angle if identified (shapes what proof matters most)"

outputs:
  - type: markdown
    label: "proof-inventory"
    description: "Ranked proof inventory with gap analysis, organized by outcome-proximity"

tools_used:
  - web_fetch
  - web_search

chains_from:
  - competitor-landscape-research
chains_to:
  - landscape-report-generator

tags:
  - proof
  - trust-signals
  - foundation
  - credibility
---

# Proof Catalog

## What This Skill Does

Scrapes a member's website and public presence for every proof asset it can find, then ranks them by how close each proof is to the actual outcome the member sells. The member gets a ranked inventory that shows their strongest proof, weakest gaps, and what to develop next.

---

## Context the Agent Needs

Proof is the single most important conversion factor on a website. Without it, every other optimization is cosmetic. The target-market-landscape methodology treats proof as a strategic asset to be hoarded and deployed — not a nice-to-have to add later.

The ranking principle is outcome-proximity: proof that demonstrates the actual result the customer is buying ranks highest. A kitchen renovator's before-and-after photos outrank their Google reviews. A SaaS company's documented revenue impact outranks their team bios. The hierarchy isn't fixed by proof type — it's governed by how close the proof is to the outcome being sold.

This skill has two phases: autonomous research (scraping the site and searching for public proof) and conversational follow-up (asking the member what else they have that isn't published). The autonomous phase runs first so the agent can present findings and ask targeted questions about gaps.

**Key constraint:** Catalog everything. The more proof the better. Rank by outcome-proximity, but never discard low-ranking proof — it all gets deployed somewhere across site, content, profiles, and ASN.

---

## Workflow — Execute In This Order

Do not skip steps. Do not summarize. Produce every section in full.

---

### STEP 1: Scrape the Member's Website for Proof

Search the member's site for every visible proof asset.

**Input:** Member's domain URL.

**Process:**
1. Web fetch the homepage. Look for:
   - Client/partner logos
   - Review scores or testimonial quotes
   - Stats or metrics displayed (customers served, years in business, projects completed)
   - Award badges or certification marks
   - Trust badges (BBB, industry associations, security certifications)

2. Web fetch common proof pages — try each of these paths:
   - /testimonials, /reviews, /case-studies, /case-study, /portfolio, /results, /success-stories
   - /about, /about-us, /our-team, /company
   - /press, /media, /news, /awards
   - Not all will exist. Skip 404s silently.

3. For each page found, extract:
   - Proof type (testimonial, case study, certification, credential, award, metric, logo, portfolio item)
   - Specific details (star rating, number of reviews, names of certifying bodies, specific results mentioned)
   - Where it lives (URL path)

4. Compile a raw list of every proof asset found on-site.

**Output:** Raw proof inventory from website scraping.

**Decision gate:**
- If the site is very small (< 5 pages) → still check all standard proof paths. Small sites often have proof buried on the homepage.
- If the site has no discoverable proof → this is a critical finding. Record it clearly.

---

### STEP 2: Search for Public Proof

Look for proof assets that exist off-site.

**Input:** Member's brand name + domain.

**Process:**
1. Web search for "[brand name] reviews" — check for Google Business Profile, Trustpilot, G2, Capterra, Yelp, industry-specific review sites
2. Web search for "[brand name] testimonials" or "[brand name] case study" — check for third-party features
3. Web search for "[brand name] award" or "[brand name] certification" — check for external recognition
4. Record: platform, rating, number of reviews, any standout quotes or metrics visible in search results

**Output:** Off-site proof inventory.

**Decision gate:**
- If no public reviews exist → record as a gap. This is actionable intelligence.
- If reviews exist but are poor (below 4.0) → record honestly. The member needs to know.

---

### STEP 3: Rank by Outcome-Proximity

Organize all proof by how close it is to the result the member sells.

**Input:** Combined proof from Steps 1-2 + the member's primary outcome (from brand assessment memory or process context) + differentiation angle if available.

**Process:**
1. Identify the primary outcome the member's customers are buying. Examples: "beautiful kitchen renovation," "more organic traffic," "faster hiring," "reliable plumbing repair"
2. For each proof asset, assess outcome-proximity:
   - **High proximity:** Directly demonstrates the outcome. Before/after photos for a renovator. Revenue graphs for a marketing agency. Documented time savings for a SaaS tool.
   - **Medium proximity:** Related to the outcome but indirect. Google reviews mentioning satisfaction. Client logos implying trust. Years of experience suggesting reliability.
   - **Low proximity:** Supports credibility but doesn't demonstrate the outcome. Certifications. Team bios. Industry association memberships. Generic awards.
3. Rank the full inventory: high proximity first, then medium, then low.
4. If a differentiation angle exists, weight proof that supports the specific niche higher. A plumber specializing in hot water cylinders values hot-water-specific reviews more than general plumbing reviews.

**Output:** Ranked proof inventory with proximity classification per asset.

---

### STEP 4: Identify Gaps and Compile

Analyze what's missing and assemble the final output.

**Input:** Ranked proof inventory from Step 3.

**Process:**
1. Check for gaps across proof types:
   - Documented outcomes with numbers? (case studies, before/after, metrics)
   - Social proof with volume? (reviews, ratings, testimonial count)
   - Authority signals? (certifications, awards, media mentions)
   - Trust signals? (years in business, team credentials, partnerships)
2. Identify the single most impactful proof gap — the one that, if filled, would most improve the member's credibility
3. Identify the top 3 proof assets to develop or surface
4. Compile everything into the output format

**Output:** Complete proof inventory with gap analysis.

---

## Output Format

```
## Proof Inventory

### High Outcome-Proximity
| Proof Asset | Type | Location |
|---|---|---|
| [specific asset] | [type] | [on-site/off-site/unpublished] |

### Medium Outcome-Proximity
| Proof Asset | Type | Location |
|---|---|---|
| [specific asset] | [type] | [on-site/off-site/unpublished] |

### Low Outcome-Proximity
| Proof Asset | Type | Location |
|---|---|---|
| [specific asset] | [type] | [on-site/off-site/unpublished] |

### Gap Analysis

**Biggest gap:** [The single most impactful missing proof type]

**Missing proof types:**
- [Type 1 — why it matters]
- [Type 2 — why it matters]

### Top 3 Proof Actions

1. [Most impactful proof to develop or surface]
2. [Second priority]
3. [Third priority]
```

**Formatting rules:**
- Each proof asset is specific, not generic. "4.8 stars on Google (127 reviews)" not "has Google reviews"
- Location states where the proof currently lives: on-site (with URL path), off-site (platform name), or unpublished (member mentioned it but it's not visible anywhere)
- Gap analysis is actionable — what to do, not just what's missing
- Total length: fits on one page of the report

---

## Edge Cases & Judgment Calls

**When the member has zero proof of any kind:**
This is the most important finding in the entire landscape analysis. State it clearly: "No proof assets found on-site or publicly. This is the highest-priority gap — without proof, traffic doesn't convert." Recommend starting with the easiest proof to obtain (usually Google reviews or documenting existing outcomes).

**When proof exists but is poorly presented:**
Catalog what exists and note the presentation issue. "3 case studies exist at /case-studies but contain no specific metrics or outcomes — they read as project descriptions, not proof." This shapes content strategy recommendations.

**When the member has great proof that isn't on their website:**
Mark location as "unpublished" and flag it as a quick win. Getting existing proof onto the site is higher ROI than creating new proof from scratch.

**When reviews are negative or mixed:**
Report honestly. If the overall rating is below 4.0, note it. If specific negative patterns emerge (slow response time, quality issues), note those too. The member needs the truth, not flattery.

---

## What This Skill Does NOT Do

- Does NOT evaluate competitor proof — that's handled in competitor-landscape-research
- Does NOT create proof for the member — it catalogs what exists and identifies gaps
- Does NOT determine the differentiation angle — it uses the angle (if available) to weight proof relevance
- Does NOT publish or deploy proof — deployment happens in content strategy and ASN processes
- If the member asks to create case studies or develop proof, suggest that as a follow-up action after the landscape report is complete

---

## Examples

**Example 1: Service Business With Strong Proof**

Input: Domain: "acmerenovations.com", Brand: "Acme Renovations", Outcome: "beautiful kitchen and bathroom renovations"

Output (abbreviated):
```
### High Outcome-Proximity
| Proof Asset | Type | Location |
|---|---|---|
| 42 before/after photo galleries | Portfolio | on-site /gallery |
| Case study: "Johnson Kitchen — $85k renovation, 3-week timeline" | Case study | on-site /case-studies |
| "Increased our home value by $120k" — Sarah M. | Testimonial | on-site /testimonials |

### Medium Outcome-Proximity
| Proof Asset | Type | Location |
|---|---|---|
| 4.9 stars on Google (312 reviews) | Reviews | off-site (Google) |
| Houzz Best of Service 2024 | Award | on-site /about |

### Gap Analysis
**Biggest gap:** No video walkthroughs of completed projects — video proof is highest-converting for renovation businesses.
```

Why this is correct: Before/after photos rank highest because they directly demonstrate the outcome (beautiful renovation). Google reviews rank medium because they're related but indirect. The gap analysis is specific and actionable.

---

**Example 2: New SaaS With Almost No Proof**

Input: Domain: "newaisaas.com", Brand: "NewAI", Outcome: "faster sales hiring decisions"

Output (abbreviated):
```
### High Outcome-Proximity
(none found)

### Medium Outcome-Proximity
| Proof Asset | Type | Location |
|---|---|---|
| "Cut our hiring time by 40%" — beta user quote on homepage | Testimonial | on-site / (homepage) |

### Low Outcome-Proximity
| Proof Asset | Type | Location |
|---|---|---|
| Founder has 12 years in HR tech (About page) | Credential | on-site /about |
| SOC 2 Type II certified | Certification | on-site /security |

### Gap Analysis
**Biggest gap:** No documented outcomes with specific numbers. The single beta quote is promising but isolated. Need 3-5 case studies with measurable hiring metrics (time-to-hire reduction, quality-of-hire improvement, cost savings).

### Top 3 Proof Actions
1. Convert 3 beta users into documented case studies with specific hiring metrics
2. Collect 10+ reviews on G2 or Capterra
3. Create a "Results" page with aggregated metrics across all users
```

Why this is correct: The skill correctly identifies that one beta testimonial is the only meaningful proof, and it's medium-proximity at best. The gap analysis is specific about what kind of proof matters most (hiring metrics, not generic satisfaction).
