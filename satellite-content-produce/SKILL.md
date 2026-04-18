---
name: satellite-content-produce
version: "1.0"
description: >
  Writes ready-to-paste satellite content targeted at a specific sub-query,
  formatted for a specific format class (Content / UGC / Video-long /
  Video-short / Social / Technical / Document), with a link back to the hub
  page baked in plus bracket-token placeholders for sibling satellites. Use
  this skill whenever an ASN deployment process needs to produce satellite
  content. This skill outputs platform-ready content plus metadata. Always
  trigger when satellite content production is needed for any off-site
  platform deployment — even if phrased casually.

# === CROSS-AGENT METADATA ===

inputs:
  required:
    - type: text
      label: "sub-query"
      description: "The H2 sub-query this satellite targets (e.g., 'how much AI content is safe to publish')"
    - type: text
      label: "format-class"
      description: "One of: Content, UGC, Video-long, Video-short, Social, Technical, Document"
    - type: text
      label: "target-platform"
      description: "Specific platform the content is being written for (e.g., Medium, Reddit, YouTube Shorts)"
    - type: text
      label: "hub-url"
      description: "The hub page URL the satellite must link back to"
    - type: text
      label: "hub-summary"
      description: "Short description of what the hub page covers — lets the satellite reference it naturally"
  optional:
    - type: array
      label: "sibling-satellites"
      description: >
        List of other satellites being deployed alongside this one for the same hub.
        Each sibling: {sub_query, platform, token}. Tokens are used as bracket
        placeholders the publish step swaps with real URLs once siblings go live.
    - type: text
      label: "brand-context"
      description: "Voice, tone, positioning notes from the member's brand profile"

outputs:
  - type: json
    label: "satellite-content-package"
    description: >
      Structured package with platform-ready content, hub link placement info,
      sibling link tokens used, and publish metadata (title, tags, description)

tools_used: []

chains_from:
  - serp-fetch-and-classify
chains_to:
  - satellite-publish

tags:
  - content-production
  - asn
  - satellite-network
  - off-site-content
---

# Satellite Content Produce

## What This Skill Does

Takes a sub-query, a format class, a target platform, and the hub page it supports, then writes ready-to-paste satellite content with a hub link baked in and bracket-token placeholders where sibling satellites will be linked after publish. The caller gets a content package that can be pasted directly onto the platform or passed to the `satellite-publish` skill.

---

## Context the Agent Needs

This skill sits inside the ASN deployment process. The methodology is in Synapse at `methodology/expansion/authority-satellite-network-deployment.md`. Two beliefs from that methodology shape every decision this skill makes:

1. **A satellite without a link back to the hub is not a satellite.** Every piece of content this skill produces must include a hub link. The link is non-negotiable and must be placed in a way that feels natural for the platform's format.

2. **Participation is the win condition, not position.** The content doesn't need to outrank the top result. It needs to be genuinely useful for the platform's audience, match the platform's native format, and link back to the hub. A satellite that reads like generic SEO content will underperform; one that feels native will rank and get engagement.

**Lateral linking rule:** When the `sibling-satellites` input is provided, the content must include bracket-token placeholders for relevant siblings. Tokens look like `[related-on-reddit]` or `[more-on-medium]`. The `satellite-publish` skill replaces these with real URLs once siblings are live. Never invent sibling URLs. Never produce placeholder text that says "link will be added later" — use the bracket tokens only.

**Hub link placement is format-dependent** (see per-format rules below). In-context for long-form content where the reference flows naturally. End-of-piece CTA for UGC and Social where a mid-content link would feel pushy.

**Key constraint:** Content must be indistinguishable from something a thoughtful human wrote for that specific platform. No AI tells. No generic framings. No "In this article, we will explore…" openings. No stuffed keywords.

---

## Format-Class Rules

### Content (Medium, Substack, LinkedIn Articles, Dev.to)

- **Length:** 600-1200 words
- **Structure:** Compelling opening hook → 2-4 subheadings breaking down the answer → closing insight or takeaway
- **Hub link placement:** In-context, woven naturally where the full hub page becomes the obvious next read. Typical spot: near the end of the piece where the reader wants to go deeper.
- **Sibling links:** In-context, using bracket tokens like `[more-on-[platform]]` where the topic they cover would add value. Max 2 sibling links per piece.
- **Voice:** First-person where natural. Specific examples. No hedging ("maybe," "perhaps," "some say").
- **Title format:** Strong standalone title that would make someone click from a feed. Not SEO-optimized title tag format.

### UGC (Reddit, Quora, Stack Exchange, niche forums)

- **Length:** 200-500 words
- **Structure:** Direct answer to the sub-query in the first 1-2 sentences, then reasoning, then optional expansion or example
- **Hub link placement:** End of piece, framed as "If you want the full breakdown, I wrote about this here: [hub-url]" or similar platform-native phrasing. Reddit and Quora penalize aggressive linking — one clean end-link.
- **Sibling links:** Only if genuinely relevant. Max 1 sibling link, end of piece. Often skip entirely on UGC.
- **Voice:** Conversational, first-person, match the register of the platform. Reddit = slightly casual, Quora = more authoritative. Avoid corporate voice.
- **Title format:** Question-phrased for Quora. For Reddit, match subreddit norms (title is the post title, which may be a claim or a question).

### Video-long (YouTube long-form)

- **Length:** 3-5 minute script (roughly 450-750 spoken words)
- **Structure:** Hook in the first 15 seconds → context in 30-45 seconds → core answer → example or demonstration → closing CTA
- **Hub link placement:** Called out verbally near the end ("I broke the full framework down at [hub-url] if you want to dig deeper") AND placed in the video description with a clear label.
- **Sibling links:** In the description, organized under a "Related" heading. Use bracket tokens.
- **Voice:** Direct, spoken cadence. Short sentences. No reading-off-the-page phrases.
- **Output includes:** Script, suggested title, description (with hub link + sibling tokens), tag suggestions.

### Video-short (YouTube Shorts, TikTok)

- **Length:** 30-60 second script (roughly 75-150 spoken words)
- **Structure:** Hook in first 3 seconds → answer in one punchy beat → close with tease
- **Hub link placement:** In the caption/description only ("Full breakdown: [hub-url]"). Not verbal — shorts don't have time.
- **Sibling links:** Typically skip. Description space is minimal. Only include one sibling if the short explicitly sets up a reference the viewer wants next.
- **Voice:** Punchy. Declarative. No throat-clearing. Every second earns its place.
- **Output includes:** Script, hook variants (2-3 alternatives), caption, hashtag suggestions.

### Social (LinkedIn Posts, X threads, Facebook posts)

- **Length:** Under 300 words. LinkedIn = 150-250 words sweet spot. X thread = 3-7 tweets.
- **Structure:** Strong opening line (first-line hook) → body that delivers the sub-query answer → closing line that either invites engagement or teases the hub
- **Hub link placement:** End of piece, formatted per platform. LinkedIn = first comment or end of post. X = final tweet in thread.
- **Sibling links:** Rare. Social is a low-link environment. Skip unless a sibling is directly referenced.
- **Voice:** Platform-native. LinkedIn = professional, first-person, specific. X = tight, declarative, punchy.
- **Output includes:** Post body (or thread as numbered tweets), suggested first-comment link (LinkedIn), hook variants.

### Technical (GitHub, Dev.to, dedicated technical platforms)

- **Length:** 500-1000 words
- **Structure:** Problem statement → solution → code example or step-by-step → edge cases or gotchas → links to more
- **Hub link placement:** In the "Further reading" or "Related" section at the end, with a short description of what's on the hub page.
- **Sibling links:** In the same Further reading section, using bracket tokens.
- **Voice:** Technical, precise, no marketing speak. Show code. Show output. Assume the reader is technical.
- **Title format:** Problem-oriented or solution-oriented ("How to X without Y" or "Fixing the common X bug in Z").

### Document (SlideShare, Scribd, SpeakerDeck)

- **Length:** 5-10 slide outline
- **Structure:** Cover slide → problem/context → core framework or breakdown (3-5 slides) → example or case → takeaway → source/CTA slide
- **Hub link placement:** Final slide, as a clear CTA linking to the hub with a brief description of what's there.
- **Sibling links:** On the CTA slide or as a "Related resources" slide before the CTA.
- **Voice:** Visual-first. Each slide supports one idea. Minimal text per slide — the deck should be skimmable.
- **Output includes:** Slide-by-slide outline with slide title, key points per slide, speaker notes where helpful.

---

## Workflow — Execute In This Order

### STEP 1: Validate Inputs

**Input:** All inputs passed to the skill.

**Process:**
1. Confirm required inputs are present: sub-query, format-class, target-platform, hub-url, hub-summary.
2. Confirm format-class is one of the seven valid classes. If invalid → return error status.
3. If sibling-satellites is provided, confirm each sibling has a `sub_query`, `platform`, and `token`.

**Output:** Validated input set ready for content generation.

**Decision gate:**
- If validation fails → return error package with status `invalid_input` and the specific issue

---

### STEP 2: Produce Content Per Format Class

**Input:** Validated inputs.

**Process:**
1. Select the format-class rule block from this skill (Content / UGC / Video-long / Video-short / Social / Technical / Document).
2. Write the content following that block's length, structure, voice, and link rules.
3. Embed the hub URL exactly where the format-class rule says (in-context or end-CTA).
4. If sibling-satellites was provided, weave in bracket tokens where relevant. Use `[<token>]` format — e.g., if a sibling has `token: "related-on-reddit"`, insert `[related-on-reddit]` as the link anchor. Respect the format's max sibling link count.
5. If no sibling-satellites was provided, skip lateral linking — do not invent tokens.

**Output:** Content body in the format's native structure (prose, script, slide outline, etc.).

---

### STEP 3: Generate Publish Metadata

**Input:** The content body from Step 2.

**Process:**
1. Generate a title appropriate for the platform (not SEO title tag format — feed-ready title).
2. Generate a description/caption/summary appropriate for the platform, if the platform uses one.
3. Generate tag or hashtag suggestions (3-5) if the platform uses them.
4. Generate 2 alternate title or hook variants for platforms where the opening line is critical (Video-short, Social).

**Output:** Metadata package attached to the content.

---

### STEP 4: Return the Content Package

Return a single JSON object:

```json
{
  "sub_query": "...",
  "format_class": "Content",
  "target_platform": "Medium",
  "hub_url": "...",
  "status": "ok",
  "content": {
    "title": "...",
    "body": "... full platform-ready content ...",
    "description": "...",
    "tags": ["tag1", "tag2", "tag3"],
    "alt_titles": ["alternate 1", "alternate 2"]
  },
  "hub_link_location": "in-context | end-cta | description",
  "sibling_tokens_used": ["related-on-reddit", "more-on-youtube"],
  "platform_notes": "Any platform-specific gotchas the publisher should know about"
}
```

---

## Output Format

Always return JSON. The body field contains the platform-ready content as a string (with markdown formatting where appropriate for Content/Technical, or plain text for UGC/Social, or structured script for Video).

**Required fields:**
- `sub_query` (string)
- `format_class` (string)
- `target_platform` (string)
- `hub_url` (string)
- `status` (string: ok / invalid_input / generation_failed)
- `content` (object with title, body, description, tags, alt_titles)
- `hub_link_location` (string: in-context / end-cta / description)
- `sibling_tokens_used` (array of strings — empty if no siblings were passed)
- `platform_notes` (string)

**On failure:**
```json
{
  "status": "invalid_input | generation_failed",
  "error": "specific issue",
  "sub_query": "...",
  "target_platform": "..."
}
```

---

## Edge Cases & Judgment Calls

**When the sub-query is anxiety-driven or negative ("is my AI content hurting my rankings"):**
Match the emotional register. Don't gaslight the reader with aggressive reassurance — acknowledge the concern, give the real answer, link to the hub for the full breakdown.

**When the target platform is in a format class but has strict cultural rules (Reddit, especially niche subreddits):**
Default to the UGC rules but flag in `platform_notes` that the content may need manual softening for specific subreddit cultures. Never assume the author can post to r/SEO the same way they'd post to r/learnprogramming.

**When the hub summary is thin or missing detail:**
Work with what's there. Don't fabricate hub content. If the hub summary is clearly inadequate (one sentence, no context), flag in `platform_notes`: "Hub summary was thin — content references hub generically. Consider providing a richer hub summary for better integration."

**When the sibling list has 5+ siblings:**
Use max 2 sibling tokens total (or fewer per format-class rules). Do not try to reference every sibling — it reads like a link dump. Pick the most topically relevant siblings.

**When the format is Video-long or Video-short and the sub-query doesn't lend itself to video:**
Produce the script anyway — the caller has already decided the format. Flag in `platform_notes` that the sub-query may perform better in a different format, for future iterations.

**When brand-context is missing:**
Default to the member's general AI SEO voice (direct, first-person, specific examples). Do not invent a persona. Keep the voice neutral but confident.

**When a sibling's platform overlaps with the current target platform (unusual but possible):**
Skip the sibling token. Linking within the same platform isn't a lateral link — it's just internal navigation and doesn't serve ASN goals.

---

## What This Skill Does NOT Do

- Does NOT publish content to any platform — that's `satellite-publish`
- Does NOT decide which sub-query needs a satellite — that's the methodology
- Does NOT decide which platform to target — that's the methodology's routing
- Does NOT fetch SERP data — that's `serp-fetch-and-classify`
- Does NOT resolve sibling URLs — leaves bracket tokens, publish swaps them
- Does NOT optimize for keyword density, meta tags, schema, or other technical SEO factors — platforms handle those differently and the skill stays platform-native
- Does NOT write evergreen "pillar content" — satellites are targeted, sub-query-focused pieces
- Does NOT produce multiple format-class outputs from one call — one call = one satellite

---

## Examples

**Example 1: Content-class satellite (Medium)**

Input:
```
sub_query: "how much AI content is safe to publish for SEO"
format_class: "Content"
target_platform: "Medium"
hub_url: "https://jonathanboshoff.com/ai-content-seo-guide"
hub_summary: "Comprehensive guide to publishing AI-generated content without hurting SEO, covering quality thresholds, editorial workflows, and Google's 2024 stance."
sibling_satellites: [
  {"sub_query": "does AI content rank", "platform": "Reddit", "token": "reddit-discussion"},
  {"sub_query": "AI content editorial workflow", "platform": "YouTube", "token": "youtube-walkthrough"}
]
```

Output (abbreviated):
```json
{
  "sub_query": "how much AI content is safe to publish for SEO",
  "format_class": "Content",
  "target_platform": "Medium",
  "hub_url": "https://jonathanboshoff.com/ai-content-seo-guide",
  "status": "ok",
  "content": {
    "title": "The Real Answer to 'How Much AI Content Is Safe to Publish'",
    "body": "Three months ago a client asked me... [600-1000 word piece with hub link embedded in-context near the end, and two bracket tokens for siblings] ...for the full stance including Google's 2024 updates, I broke it down in detail here: https://jonathanboshoff.com/ai-content-seo-guide. If you're curious what the Reddit community thinks, there's an active thread [reddit-discussion], and I walked through the exact editorial workflow on video [youtube-walkthrough].",
    "description": "A practical answer to the AI content volume question, grounded in real client work.",
    "tags": ["ai content", "seo", "content strategy"],
    "alt_titles": ["'How Much AI Content' Is the Wrong Question", "The Volume Question Nobody Actually Answers"]
  },
  "hub_link_location": "in-context",
  "sibling_tokens_used": ["reddit-discussion", "youtube-walkthrough"],
  "platform_notes": "Piece is Medium-native length and voice. Hub link placed near end where reader naturally wants more."
}
```

Why this is correct: Content-class rules followed (length, in-context hub link, 2 sibling tokens, Medium-native voice). Title is feed-ready, not SEO-optimized. Bracket tokens embedded inline for publish to swap.

---

**Example 2: UGC-class satellite (Reddit)**

Input:
```
sub_query: "does AI content get penalized by Google"
format_class: "UGC"
target_platform: "Reddit"
hub_url: "https://jonathanboshoff.com/ai-content-seo-guide"
hub_summary: "Comprehensive guide covering AI content policies and what actually gets penalized vs what ranks."
sibling_satellites: []
```

Output (abbreviated):
```json
{
  "sub_query": "does AI content get penalized by Google",
  "format_class": "UGC",
  "target_platform": "Reddit",
  "hub_url": "https://jonathanboshoff.com/ai-content-seo-guide",
  "status": "ok",
  "content": {
    "title": "AI content doesn't get penalized. Low-quality content gets penalized. Here's the actual distinction.",
    "body": "Short version: Google's stance isn't 'AI content is bad.' It's 'unhelpful content is bad' — and most AI content is unhelpful because people publish first-draft slop... [250 word direct answer with real reasoning] ...If you want the full breakdown including what Google's 2024 updates actually changed, I wrote it up here: https://jonathanboshoff.com/ai-content-seo-guide",
    "description": null,
    "tags": ["ai content", "seo"],
    "alt_titles": []
  },
  "hub_link_location": "end-cta",
  "sibling_tokens_used": [],
  "platform_notes": "Reddit-native voice. Direct answer in first sentence. End-link framed as personal addition, not a promotion — reduces downvote risk. No siblings linked (none provided)."
}
```

Why this is correct: UGC rules followed (short length, direct answer first, end-CTA link, conversational voice, no lateral links since none were provided).
