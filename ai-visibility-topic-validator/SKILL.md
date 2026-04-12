---
name: ai-visibility-topic-validator
version: "1.0"
description: >
  Validates whether a content topic is worth creating by checking SERP fit,
  brand lane alignment, AI replaceability, and uniqueness. Use this skill
  whenever someone says "should I make this page", "validate this topic",
  "is this worth writing about", "content validation", "will this rank",
  "stay in my lane check", "lane check", "SERP check this topic",
  "is this in my lane", or provides a topic + site URL and asks whether to
  create content about it. Also trigger when someone provides a list of topics
  and asks which ones are worth pursuing. Always trigger when content validation,
  topic fit, or "should I write this" intent is present — even if phrased casually.

inputs:
  required:
    - type: text
      label: "site-url"
      description: "The member's site URL — used to determine brand lane and filter self-referential SERP results."
    - type: text
      label: "topic-or-query"
      description: "The proposed content topic or search query to validate (e.g., 'red light therapy for dry eyes', 'best CRM for small business')."
  optional:
    - type: text
      label: "site-lane"
      description: "Pre-determined site lane if already known from a prior validation or brand audit. Skips Step 1 if provided."
    - type: text
      label: "batch-topics"
      description: "Multiple topics to validate in sequence. If provided, run the full workflow for each topic and produce a summary table at the end."

outputs:
  - type: markdown
    label: "content-validation-report"
    description: "Per-topic validation report with SERP lane check, AI replaceability assessment, uniqueness check, and GO / CAUTION / NO-GO recommendation."

tools_used:
  - web_search
  - page-scraper

chains_from:
  - volume-checker
  - serp-validator
chains_to:
  - ai-seo-engine

tags:
  - seo
  - content-validation
  - ai-visibility
  - serp-analysis
  - topic-validation
  - lane-check
---

# AI Visibility Topic Validator

## What This Skill Does

Evaluates whether a proposed content topic is worth creating by running three checks: SERP lane fit (does this topic belong to sites like yours?), AI replaceability (can a chatbot answer this just as well?), and uniqueness (do you have something no one else can say?). Produces a GO / CAUTION / NO-GO recommendation with reasoning.

---

## Context the Agent Needs

Not every topic a brand *could* write about is a topic they *should* write about. Three failure modes kill content before it ranks:

1. **Out of lane.** The SERP is dominated by a different site type (e.g., medical journals for a supplement brand). Google has decided who belongs here — your site type isn't one of them.

2. **AI-replaceable.** The query has a factual, self-contained answer that AI chat handles perfectly. Zero reason for a user to click through to your page. These topics are losing strategies in an AI-search world.

3. **Generic.** Your page would say exactly what every other page says. No proprietary data, no first-party experience, no product tie-in, no community angle. Google has no reason to prefer your version.

A topic needs to clear all three checks. One failure is enough to kill it — or at minimum push it to CAUTION with a specific angle that might save it.

**Site lane** is determined once per site and reused across all topics in a session. It answers: "What type of site is this, and what topical territory does it credibly occupy?" The SERP lane check then asks: "Do sites like this one rank for this query?"

---

## Workflow Steps

### STEP 1: Determine Site Lane

Establish what kind of site this is so you can evaluate SERP fit for any topic.

**Input:** `site-url` (or `site-lane` if pre-provided — skip this step)
**Process:**
1. Fetch the site's homepage and 2-3 key pages using page-scraper
2. Identify: site type (SaaS, agency, e-commerce, publisher, local business, etc.), core topical territory, and the audience it serves
3. Write a one-sentence Site Lane: "[Site type] serving [audience] in [topical territory]"

**Output:** Site Lane statement (e.g., "B2B SaaS company serving marketing teams in the email automation space")
**Decision gate:**
- If `site-lane` was provided as input → skip to Step 2
- If site is too ambiguous to categorize → ask the member to clarify their core offering before proceeding

---

### STEP 2: SERP Lane Check

Determine whether sites like the member's site rank for this topic.

**Input:** `topic-or-query`, Site Lane from Step 1
**Process:**
1. Search the topic/query using web search
2. Examine the top 10 results. For each result, record:
   - Domain
   - Site type (same categories as Step 1: SaaS, agency, publisher, etc.)
   - Whether it's "in-lane" — same site type as the member's site
3. **Exclude Reddit and Wikipedia from the in-lane count** — these are universal rankers, not lane signals
4. Count in-lane results out of the remaining results
5. Apply thresholds:
   - **5+ in-lane** → STRONG FIT (this SERP welcomes your site type)
   - **3-4 in-lane** → POSSIBLE FIT (your site type appears but doesn't dominate)
   - **0-2 in-lane** → OUT OF LANE (Google prefers a different site type here)
6. Note what site types *do* dominate if the member is out of lane

**Output:** SERP lane check table + verdict + key observation
**Decision gate:**
- If OUT OF LANE → this alone is enough for a NO-GO, but continue checks for completeness
- If STRONG FIT or POSSIBLE FIT → proceed to Step 3

---

### STEP 3: AI Replaceability Check

Evaluate whether AI chat makes this content unnecessary.

**Input:** `topic-or-query`
**Process:**
1. Ask yourself: "If someone typed this into ChatGPT or Claude, would the AI response fully satisfy their need?"
2. Evaluate along three dimensions:
   - **Factual completeness:** Can AI give a correct, complete answer from training data alone?
   - **Freshness requirement:** Does this topic require current data, recent events, or live market conditions that AI can't access?
   - **Decision complexity:** Does the user need to compare options, see examples, or make a judgment that benefits from curated human perspective?
3. Apply thresholds:
   - **AI fully answers it** → LOSING STRATEGY (no click-through incentive)
   - **AI partially answers but misses nuance** → VULNERABLE (defensible only with unique angle)
   - **AI can't answer well** (needs freshness, locality, experience, visual examples, proprietary data) → DEFENSIBLE

**Output:** AI replaceability verdict + reasoning
**Decision gate:**
- If LOSING STRATEGY and no unique angle exists → strong signal toward NO-GO
- If VULNERABLE → proceed, but the uniqueness check in Step 4 becomes critical
- If DEFENSIBLE → proceed to Step 4

---

### STEP 4: Uniqueness Check

Evaluate whether the member can say something no one else can.

**Input:** `topic-or-query`, Site Lane from Step 1
**Process:**
1. Check four uniqueness signals:
   - **Proprietary data:** Does the member have data, benchmarks, or metrics no one else publishes? (e.g., "We analyzed 10,000 campaigns and found...")
   - **First-party experience:** Has the member done, built, or tested the thing the topic is about? (e.g., hands-on product reviews, case studies from real work)
   - **Product tie-in:** Does the topic naturally connect to the member's product/service without being forced? (e.g., a CRM company writing about sales pipeline management)
   - **Community/UGC:** Does the member have user-generated content, community discussions, or customer stories that enrich the topic?
2. Apply thresholds:
   - **2+ signals present** → UNIQUE
   - **1 signal present** → POSSIBLE (could work if the signal is strong)
   - **0 signals** → GENERIC (your page adds nothing new to the internet)

**Output:** Uniqueness verdict with specific signals identified
**Decision gate:**
- If GENERIC and AI replaceability is VULNERABLE or worse → NO-GO
- If POSSIBLE → CAUTION with specific angle suggestion
- If UNIQUE → strong signal toward GO

---

### STEP 5: Final Recommendation

Synthesize all three checks into a single recommendation.

**Input:** Results from Steps 2, 3, and 4
**Process:**
1. Apply the recommendation matrix:
   - **GO** — SERP is STRONG FIT or POSSIBLE FIT, AND not a LOSING STRATEGY for AI, AND at least POSSIBLE on uniqueness
   - **CAUTION** — one check is marginal but the other two are strong, OR SERP is POSSIBLE FIT with strong uniqueness that could compensate
   - **NO-GO** — OUT OF LANE on SERP, OR LOSING STRATEGY on AI with no uniqueness to compensate, OR GENERIC with no defensible angle
2. Write 2-3 sentence reasoning that references the specific check results
3. If CAUTION, suggest a specific angle that would make it work (e.g., "Add your proprietary benchmark data to differentiate from the generic guides that dominate this SERP")

**Output:** Final recommendation in the output format below

---

## Output Format

```markdown
# Content Validation Report

## Site: [site URL]
**Lane:** [One-sentence Site Lane from Step 1]

---

## Topic: [Proposed topic or query]

### 1. SERP Lane Check

**Query searched:** [exact query used]

**Top 10 Results:**
| # | Site | Type | In-Lane? |
|---|---|---|---|
| 1 | [domain] | [site type] | [check] / [x] / skip |
| 2 | ... | ... | ... |
| ... | ... | ... | ... |

**In-lane count:** [X] / [Y counted] (excluding Reddit/Wikipedia)
**Verdict:** STRONG FIT / POSSIBLE FIT / OUT OF LANE
**Key observation:** [1-2 sentences on what types of sites dominate this SERP]

---

### 2. AI Replaceability Check

**Can AI chat answer this well?** [Yes / Partially / No]
**Why:** [1-2 sentences]
**Verdict:** DEFENSIBLE / VULNERABLE / LOSING STRATEGY

---

### 3. Uniqueness Check

**Proprietary data:** [Yes/No — what data?]
**First-party experience:** [Yes/No — what experience?]
**Product tie-in:** [Yes/No — what connection?]
**Community/UGC:** [Yes/No — what content?]
**Verdict:** UNIQUE / POSSIBLE / GENERIC

---

### RECOMMENDATION: GO / CAUTION / NO-GO

**Reasoning:** [2-3 sentences]

**If CAUTION — suggested angle:** [What would make this work]
```

**Batch mode:** When validating multiple topics, produce the full report for each topic, then append a summary table:

```markdown
## Batch Summary

| Topic | SERP | AI Risk | Uniqueness | Recommendation |
|---|---|---|---|---|
| [topic 1] | STRONG FIT | DEFENSIBLE | UNIQUE | GO |
| [topic 2] | OUT OF LANE | VULNERABLE | GENERIC | NO-GO |
| ... | ... | ... | ... | ... |
```

---

## Edge Cases & Judgment Calls

### Incomplete input — no site URL provided
If the member provides topics but no site URL, you cannot run the SERP lane check or uniqueness assessment. Ask: "I need your site URL to check whether this topic fits your brand lane. What's your domain?" Do not skip the lane check — it's the most important signal.

### Ambiguous site lane — member's site spans multiple verticals
Some sites genuinely serve multiple audiences (e.g., a SaaS company that's also a publisher). Pick the primary lane based on what the majority of their content targets. Note the ambiguity in the report: "Lane is ambiguous — site has both [type A] and [type B] content. Evaluating against [type A] as the primary lane." If the member disagrees, re-run with their corrected lane.

### Topic is too broad to SERP-check
If the topic is something like "marketing" or "SEO" — too broad for a meaningful SERP check — ask the member to narrow it: "That's too broad to validate against SERPs. Can you give me the specific angle or query someone would search? For example, 'SEO for dentists' or 'how to do keyword research for local businesses'."

### SERP returns mostly aggregators (Reddit, Quora, forums)
If the SERP is dominated by forums and aggregators after excluding Reddit/Wikipedia, this signals a gap — no one has authored definitive content for this query yet. This is actually a positive signal for POSSIBLE FIT if the member's site type is plausible for the topic. Note: "SERP is forum-dominated, which signals a content gap. Your site could fill this if the topic is in your lane."

### All three checks pass but volume is zero
This skill does not check search volume — that's volume-checker's job. If the member asks about volume, point them there. A topic can be a GO for lane fit, AI defensibility, and uniqueness while still having no search demand. This skill validates *fit*, not *demand*.

### Member insists on a NO-GO topic
Present the data clearly but respect the member's decision. Add a note: "This topic scored NO-GO on [check], but you know your business better than any SERP analysis. If you proceed, consider [specific angle] to maximize your chances."

---

## What This Skill Does NOT Do

- **Search volume or keyword difficulty** — use volume-checker for demand data
- **Content brief generation** — use ai-seo-engine after validation confirms GO
- **Competitor deep-dive** — use competitor-landscape-research for full competitive analysis
- **Full topical map building** — use stories-to-queries for systematic query derivation
- **Page architecture decisions** — use serp-validator for one-page-or-split analysis
- **Content creation** — this skill decides *whether* to create, not *what* to write

---

## Examples

### Example 1: Happy path — clear GO

**Input:** site-url: `thermlight.com` (red light therapy device manufacturer), topic: "red light therapy for dry eyes"

**Step 1:** Site Lane — "E-commerce / health device manufacturer serving consumers in the red light therapy space"

**Step 2:** SERP check for "red light therapy for dry eyes" — 6 of 8 counted results are health device brands, wellness publishers, and condition-specific health sites. In-lane count: 5/8. **STRONG FIT.**

**Step 3:** AI replaceability — AI can explain the mechanism, but users want to see specific device recommendations, clinical study links, and real user results. **DEFENSIBLE** (needs specificity AI can't provide).

**Step 4:** Uniqueness — product tie-in (they sell the device), first-party experience (can demonstrate usage and results). **UNIQUE.**

**Recommendation: GO.** SERP welcomes device manufacturers, AI can't replace specific product guidance with real-world evidence, and the brand has a natural product tie-in plus first-party usage data.

---

### Example 2: Edge case — out of lane despite relevance

**Input:** site-url: `acmecrm.com` (B2B SaaS CRM), topic: "how to write a cold email"

**Step 1:** Site Lane — "B2B SaaS company serving sales teams in the CRM / sales enablement space"

**Step 2:** SERP check for "how to write a cold email" — top 10 dominated by email marketing platforms (Mailchimp, HubSpot), sales methodology blogs (Gong, Salesloft), and general business publishers (HBR, Forbes). Only 1 CRM company appears. In-lane count: 1/8. **OUT OF LANE.**

**Step 3:** AI replaceability — AI can generate a solid cold email framework with templates. **VULNERABLE.**

**Step 4:** Uniqueness — the CRM has email send data they could leverage (proprietary data signal). **POSSIBLE.**

**Recommendation: CAUTION.** The SERP doesn't currently favor CRM companies for this query — it's owned by email platforms and sales methodology publishers. However, if Acme CRM publishes with their proprietary send/reply rate data from their platform, that could differentiate enough to break in. **Suggested angle:** "We analyzed 50,000 cold emails sent through Acme CRM — here's what the top 1% do differently." Without the data angle, this is a NO-GO.
