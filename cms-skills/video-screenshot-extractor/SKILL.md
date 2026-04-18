---
name: video-screenshot-extractor
version: "1.1"
description: >
  Extracts SEO-optimized still frames from a source video and injects them into an existing blog
  post with timestamp-deeplinked anchor text, EXIF metadata, and section-matched placements.
  **Use this skill whenever a user provides BOTH a video source (YouTube, Vimeo, Loom, direct
  MP4 — any video URL or file) AND a blog post (markdown, HTML, or URL), and wants frames from
  the video placed into the article.** Always trigger when the prompt mentions: "screenshots
  from the video", "frames from the recording", "proof images from the video", "stills from
  the video", "add images from the video/loom/youtube", "pull images out of the recording",
  "replace the embedded video with screenshots", or any variation of the video-to-blog image
  pipeline — even if the user doesn't literally say "screenshot". Do NOT trigger when the user
  wants screenshots of a live webpage or dashboard (no video involved), AI-generated
  illustration images, video trimming or editing, audio extraction, or transcription without
  image output. Platform-agnostic: runs anywhere with a Unix-like shell, Python 3.8+, and ffmpeg.

inputs:
  required:
    - type: text
      label: "video-url"
      description: "URL of the source video. Any yt-dlp-supported source (YouTube, Vimeo, Loom exports, direct MP4)."
    - type: text
      label: "blog-post"
      description: "The blog post that will receive screenshots. Accepts a markdown file path, an HTML file path, or a public URL."
  optional:
    - type: text
      label: "work-dir"
      description: "Working directory for all outputs. Defaults to the current working directory."
    - type: text
      label: "timestamps"
      description: "Comma-separated timestamps (HH:MM:SS or MM:SS) to use instead of auto-detection. Overrides scene detection entirely."
    - type: text
      label: "keyword"
      description: "Primary target keyword for the blog post. If omitted, inferred from the blog's H1 and repeated terms."
    - type: text
      label: "creator"
      description: "Name written to the Artist/Creator EXIF field. Defaults to inferring from the blog's author metadata, then to empty."

outputs:
  - type: png
    label: "screenshots"
    description: "Full-quality PNG frames saved to ./screenshots/, named section-slug-NN.png with EXIF metadata written."
  - type: markdown
    label: "modified-blog-post"
    description: "A copy of the blog post with image blocks inserted at matched sections, saved as ./<blog-filename>.with-images.md. The original file is never overwritten."
  - type: markdown
    label: "manifest"
    description: "./screenshots/manifest.md — per-image review doc listing filename, section, timestamp, alt text, caption, and frame-selection reasoning."

tools_used:
  - yt-dlp
  - ffmpeg
  - exiftool
  - piexif
  - Pillow
  - python3
chains_from:
  - transcript-to-blog-post
chains_to:
  - cms-wordpress
  - cms-webflow
  - cms-shopify
tags:
  - seo
  - video
  - screenshots
  - content-pipeline
  - exif
  - youtube
  - vimeo
  - cms
---

# Video Screenshot Extractor

## What This Skill Does

Takes a video URL and an existing blog post, identifies every section in the post that references a specific visual artifact, extracts the matching clean frame from the video at full quality, writes SEO-optimized EXIF metadata, and hands back a modified blog post with each screenshot wrapped in a timestamp-deeplinked link back to the exact second of the video.

---

## Context the Agent Needs

This skill is a pipeline step, not a content generator. The blog post has already been written (typically by `transcript-to-blog-post`). The skill does not decide what the post should say or whether it needs images — it identifies where the existing prose is making a visual claim and supplies the matching proof frame.

**Why clean frames matter.** Screenshots that contain pause icons, progress bars, or player overlays look like screen-grabs from a YouTube tab, which tells readers (and Google) that the image is a lazy capture rather than a first-party asset. Extracting directly from the downloaded video file with ffmpeg gives pure frames with zero player chrome.

**Why timestamp deeplinks matter.** Each screenshot is wrapped in a link of the form `https://youtube.com/watch?v=VIDEO_ID&t=145s`. A reader who clicks the image lands on the exact moment of the video where the claim is demonstrated. This is the killer feature — it turns static images into proof checkpoints, signals the video as the source document to search engines, and dramatically improves dwell time.

**Portability is a hard constraint.** The skill runs as shell commands on whatever machine executes it — OpenClaw, Claude Code, a local terminal, CI — with no assumptions about OS, container, or path layout. Every path is relative to `--work-dir`. Every dependency is verified or installed at Step 0. Never hard-code `/tmp`, `/data`, `/mnt/user-data`, or any environment-specific path.

**Frame matching uses the transcript when available.** Jonathan's proof videos are screen recordings of dashboards, SERPs, and page layouts with narration. The video transcript (pulled via `yt-dlp --write-auto-subs`) tells us *when* the narrator references each artifact, and scene-change detection tells us *where* the visual content actually changed. Intersecting those two signals produces the best frame per section. User-provided timestamps override everything.

---

## Workflow — Execute In This Order

Do not skip Step 0. Do not assume dependencies are present. Do not overwrite the source blog file.

---

### STEP 0: Environment Preflight

Verify dependencies and install what can be installed without system privileges.

**Input:** None.

**Process:**
1. Run `bash scripts/preflight.sh`. The script checks for `ffmpeg`, `yt-dlp`, `exiftool`, and the Python libraries `Pillow` and `piexif`. It auto-installs `yt-dlp`, `Pillow`, and `piexif` via `pip install --user`. It never tries to install `ffmpeg` — that requires platform-specific instructions.
2. If `ffmpeg` is missing, stop with a clear install instruction per OS (`brew install ffmpeg` / `apt-get install ffmpeg` / `choco install ffmpeg`). Do not attempt to proceed without it.
3. If `exiftool` is missing, continue silently — the skill falls back to `piexif` + `Pillow` for EXIF writing.

**Output:** All required dependencies confirmed available.

**Decision gate:**
- If `ffmpeg` absent → stop and surface install instructions.
- If `yt-dlp` / `Pillow` / `piexif` installation fails → stop and report the pip error.
- If `exiftool` absent → continue (fallback path is fully supported).

---

### STEP 1: Normalize Inputs

Resolve the video URL and the blog post into consistent internal formats.

**Input:** `--video <url>`, `--blog <path|url>`, optional `--timestamps`, `--keyword`, `--creator`, `--work-dir`.

**Process:**
1. Resolve `--work-dir`. If not provided, use the current working directory. Create `./screenshots/` relative to it.
2. Normalize the blog post to markdown text:
   - If the input ends in `.md`, read it as-is.
   - If the input ends in `.html` or `.htm`, convert to markdown via `pandoc` if available, otherwise strip tags with a minimal HTML-to-markdown conversion.
   - If the input is a URL, fetch it with the `page-scraper` skill or a simple `curl` + HTML-to-markdown conversion.
3. Capture the blog filename stem for the output file. A blog at `./pillar-post.md` produces `./pillar-post.with-images.md`.
4. Parse the video URL. Extract the canonical video ID for timestamp-deeplink construction. For YouTube: `v=VIDEO_ID`. For Vimeo and others: preserve the URL and append `#t=145s` since `&t=` isn't universally supported.
5. If `--timestamps` provided, validate each as HH:MM:SS or MM:SS and convert to seconds.

**Output:** Clean markdown blog text, canonical video URL, video ID, parsed timestamp list (or null), resolved work-dir paths.

**Decision gate:**
- If the blog input cannot be resolved (404, unreadable file, binary) → stop and report.
- If the video URL is clearly invalid → stop.

---

### STEP 2: Identify Visual-Artifact Sections

Read the blog and list every section that makes a specific visual claim the screenshot should prove.

**Input:** Normalized blog markdown.

**Process:**
1. Walk the blog's heading tree (H2, H3, H4) and the prose under each.
2. For each section, ask: *does this section reference a specific visual artifact that the reader is expected to see?* Examples of what qualifies:
   - "The Ahrefs chart for Edia shows a 40% traffic collapse"
   - "Here's the SERP for [keyword]"
   - "The SEMrush dashboard looks like this"
   - "This is the layout of [page]"
   - Language cues: "as you can see", "looks like this", "the screenshot below", "here's the chart", "the dashboard shows", embedded image placeholders like `![...]()` with no src filled in
3. Skip sections that are purely narrative, opinion, FAQ, or conceptual. A section titled "Why Mass AI Content Strategies Collapse" that opens with prose and then injects the Edia case study H3 gets one screenshot (the Edia chart) — not one for the parent H2.
4. For each qualifying section, record: section heading, the sentence/phrase that anchors the visual claim, and 3-5 transcript-search terms likely to match the moment in the video narration.
5. Respect the hard cap. If more than 10 visual-artifact sections exist, stop and surface the list to the user for them to pick the top 10.

**Output:** Ordered list of target sections, each with a heading, anchor phrase, and transcript search terms.

**Decision gate:**
- If zero visual-artifact sections → stop and report. The blog doesn't call for screenshots.
- If > 10 sections → stop and ask the user to pick 10.
- If 1-10 → proceed.

---

### STEP 3: Download the Video and Transcript

Pull the video file and its auto-captions in one pass.

**Input:** Canonical video URL.

**Process:**
1. Run `python3 scripts/download.py --url <video_url> --out <work-dir>/video.mp4`. This wraps `yt-dlp` with flags for the best-available MP4 (no re-encoding) and also requests auto-generated captions in VTT format.
2. The script produces `<work-dir>/video.mp4` and `<work-dir>/video.vtt` (if captions available).
3. If captions are unavailable (creator disabled them, or Vimeo/direct MP4 has no transcript), continue with the VTT file absent. The pipeline degrades gracefully — Step 5 will fall back to proximity-only matching.

**Output:** Local video file path, optional transcript VTT path.

**Decision gate:**
- If download fails due to geo-block, privacy, or removal → stop and report.
- If transcript is unavailable → log a warning and continue.

---

### STEP 4: Build the Candidate Frame Pool

Produce a list of candidate timestamps that represent distinct visual moments.

**Input:** Local video file, optional `--timestamps` override.

**Process:**
1. If `--timestamps` was provided, this is the candidate pool. Skip detection entirely and move to Step 5 with one candidate per provided timestamp.
2. Otherwise, run `python3 scripts/scenes.py --video <path> --threshold 0.3`. The script runs `ffmpeg -vf select='gt(scene,0.3)'` and prints a list of timestamps where the visual content changed meaningfully. For a 10-minute screen recording this typically yields 30-80 candidates.
3. `scenes.py` automatically retries at lower thresholds (0.2, then 0.15) if the initial pass yields fewer than `--min-candidates` (default 5). This catches softer transitions — fades, slow zooms, cross-dissolves — that a 0.3 threshold misses. The script writes the threshold actually used to stderr as `# threshold_used=<T>`. If you observe that the final matched frames keep landing in large no-change gaps, re-run with `--threshold 0.2` explicitly.
4. If scene detection still returns fewer than 3 candidates after the retry chain (rare — typically talking-head videos with a locked camera), fall back to evenly-spaced samples: one frame every `video_duration / (N + 1)` seconds, where N is the number of target sections from Step 2.

**Output:** Array of candidate timestamps in seconds.

**Decision gate:**
- If user-provided timestamps exist → use them verbatim, no detection.
- If scene detection produces < 3 candidates even after threshold retries → use evenly-spaced fallback.
- Otherwise → use the scene-detected pool.

---

### STEP 5: Match Sections to Frames

Assign one timestamp to each target section.

**Input:** Target sections from Step 2, candidate pool from Step 4, optional transcript VTT.

**Process:**
1. If user-provided timestamps exist, zip them with sections in order and skip the matching logic. The user explicitly chose these frames.
2. If a transcript exists:
   - For each target section, search the VTT for its anchor phrase and transcript search terms. Record the start-time of the matching caption block.
   - From the candidate pool, pick the nearest timestamp that is *at or after* the transcript match time (the visual usually appears a beat after the narrator mentions it, not before).
3. If no transcript exists:
   - Distribute candidates across sections proportionally to their position in the blog. Section 1 of 5 gets a candidate from the first fifth of the video, section 2 from the second fifth, etc.
4. Enforce a minimum spacing of 3 seconds between selected frames. If two sections would match the same candidate, pick the next nearest.

**Output:** A list of `(section, timestamp_seconds)` pairs, one per target section.

**Decision gate:**
- If a section has no plausible transcript match and the proportional fallback would produce a clearly unrelated frame → flag it in the manifest as "low-confidence match; please verify".

---

### STEP 6: Extract Final Frames

Produce the actual PNG files at full quality with no player overlays.

**Input:** Matched `(section, timestamp)` pairs.

**Process:**
1. For each pair, run `python3 scripts/extract.py --video <path> --ts <HH:MM:SS> --out <work-dir>/screenshots/<filename>.png`.
2. The script invokes `ffmpeg -ss <ts> -i <video> -frames:v 1 -c:v png -compression_level 0 -q:v 1 <out>` — fast seek, single frame, lossless PNG, maximum quality.
3. Filenames are kebab-case, descriptive, SEO-friendly: derived from the section slug with a two-digit zero-padded index. Example: `edia-ahrefs-chart-01.png`, `serp-page-layout-02.png`.
4. Frames come from the raw video stream. They contain no pause icons, no progress bars, no player UI. Verify this visually by opening one before continuing.

**Output:** Full-quality PNG files in `<work-dir>/screenshots/`.

**Decision gate:**
- If any ffmpeg call fails (unreadable timestamp, codec mismatch) → retry once with a 500ms offset; if still failing, skip that section and note it in the manifest.

---

### STEP 7: Generate SEO Assets per Screenshot

For each image, produce the alt text, optional caption, filename, and EXIF payload.

**Input:** Matched sections + extracted frames + blog keyword.

**Process:**
1. Determine the primary target keyword. If `--keyword` was provided, use it. Otherwise, infer from the blog's H1, meta-title, and the most-repeated 2-3 word phrase excluding stop words.
2. For each screenshot, write:
   - **Alt text** (always): a descriptive sentence of what the image shows, with the target keyword or a natural variation included — never stuffed. Example: `Ahrefs organic traffic graph showing Edia's 42% decline from 2023 to 2024`.
   - **Caption** (conditional): only if the surrounding prose doesn't already describe what's in the image. Skip otherwise. Redundant captions hurt readability.
   - **Filename** (derived from section slug): already generated in Step 6.
   - **EXIF Title**: matches the filename without the extension, human-readable. Example: `Edia Ahrefs Chart`.
   - **EXIF Description**: one sentence, reuses or refines the alt text for the context of the blog topic.
   - **EXIF Keywords**: target keyword + 2-3 natural variations, comma-separated.
   - **EXIF Artist/Creator**: from `--creator` flag, or inferred from blog author metadata, or empty.
   - **EXIF Copyright**: `<creator> <current-year>` if creator present, else blank.
   - **EXIF Source**: the canonical YouTube URL (without `&t=` parameter). Keep it clean.

**Output:** A dict per screenshot containing filename, alt, caption-or-null, and the EXIF payload.

**Decision gate:**
- If alt text would repeat the target keyword more than once → rewrite with a natural variation.

---

### STEP 8: Write EXIF Metadata

Stamp each PNG with the metadata from Step 7 and strip anything that fingerprints automation.

**Input:** PNGs from Step 6 + EXIF payloads from Step 7.

**Process:**
1. For each PNG, run `python3 scripts/exif.py --file <png> --title <title> --description <desc> --keywords <kw> --artist <creator> --copyright <copyright> --source <url>`.
2. The script prefers `exiftool` if available — it writes all fields across EXIF, XMP, and IPTC so any downstream reader finds the value regardless of which schema it prefers.
3. When `exiftool` is absent, the fallback path writes the EXIF-compatible fields (Title, Artist, Copyright) to the PNG `eXIf` chunk via `piexif` + `Pillow`, AND writes the remaining SEO-critical fields (Description, Keywords, Source, Author) as PNG `tEXt` chunks. The tEXt chunks are a superset of what piexif alone produces and are readable by exiftool, ImageMagick, and most metadata-aware crawlers when the files are later re-ingested.
4. The script always strips: GPS data, camera make/model, software identifiers (`yt-dlp`, `ffmpeg`, `Pillow`), and any pre-existing EXIF from the source video's frame.
5. The script never writes: `Comments`, `UserComment`, or URL parameters in the Source field.

**Output:** PNGs with clean, SEO-optimized EXIF.

**Decision gate:**
- If neither `exiftool` nor `piexif+Pillow` can write metadata (extremely rare on modern systems) → produce the images without EXIF and flag it in the manifest for manual post-processing.

---

### STEP 9: Inject Images into the Blog + Write Manifest

Produce the two output markdown files.

**Input:** Target sections, matched frames, EXIF payloads, original blog markdown, video ID.

**Process:**
1. For each target section, compose the image block using the wrapped-link pattern:
   ```markdown
   [![<alt text>](screenshots/<filename>.png)](<video-url-with-timestamp>)
   ```
   - `<video-url-with-timestamp>` is `https://youtube.com/watch?v=VIDEO_ID&t=<seconds>s` for YouTube, or the canonical URL with `#t=<seconds>s` fragment for other sources.
   - If a caption was generated in Step 7, append it on the line below as `*Caption text here.*` (italic markdown).
2. Insert each image block into the blog at the end of the first paragraph of its section. This keeps the visual close to the claim it proves without disrupting prose flow.
3. Write the modified blog to `<work-dir>/<blog-filename>.with-images.md`. The original file is never touched.
4. Write `<work-dir>/screenshots/manifest.md` — see Output Format below.

**Output:**
- `<work-dir>/<blog-filename>.with-images.md` — modified post ready for review and CMS publishing.
- `<work-dir>/screenshots/manifest.md` — per-image review doc.

**Decision gate:**
- After writing, spot-check that every image file referenced in the modified blog exists in `./screenshots/`. If any are missing, the pipeline has a bug — stop and surface it.

---

## Output Format

### manifest.md

```markdown
# Screenshot Manifest

Video: <canonical video URL>
Blog post: <blog filename>
Total screenshots: <N>

---

## <filename>.png

- **Section:** <section heading from blog>
- **Timestamp:** <HH:MM:SS> (<seconds>s)
- **Alt text:** <alt text>
- **Caption:** <caption if present, else "none">
- **Deeplink:** <video URL + timestamp>
- **Reasoning:** <one sentence: why this frame was chosen — e.g., "Scene change at 2:45 matching narrator mention of 'Edia Ahrefs traffic' at 2:43.">
- **Confidence:** high | medium | low

---
```

### <blog-filename>.with-images.md

Same content as the original blog, with image blocks inserted after the first paragraph of each target section:

```markdown
## Why Edia's Content Strategy Collapsed

Edia grew from 50k to 2M monthly visits in 18 months. The crash, when it came, was just as fast.

[![Ahrefs organic traffic graph showing Edia's 42% decline from 2023 to 2024](screenshots/edia-ahrefs-chart-01.png)](https://youtube.com/watch?v=abc123&t=163s)
*Edia's Ahrefs organic traffic timeline, showing the 42% collapse between March and September 2024.*

The pattern is visible across every site that tried to scale with pure AI-generated content...
```

**Formatting rules:**
- Image block is a wrapped link: `[![alt](path)](url-with-timestamp)`. Always.
- Path is relative (`screenshots/filename.png`), never absolute.
- Timestamp deeplink uses `&t=<seconds>s` for YouTube, `#t=<seconds>s` otherwise.
- Caption italicized on its own line, only if present.
- Single blank line before and after the image block.

---

## Edge Cases & Judgment Calls

**When the blog references zero visual artifacts:**
Stop and report. The skill doesn't exist to sprinkle decorative images into prose — it exists to supply proof frames for specific claims. If the blog doesn't make visual claims, the right action is to tell the user and let them decide whether to rewrite the post or skip the skill. Do not invent image spots.

**When the blog references more than 10 visual artifacts:**
Stop and surface the full list to the user with a prompt to pick their top 10. Ten is a deliberate cap — more screenshots past that point crowd the reader and dilute each image's proof value. Do not silently truncate.

**When the video has no transcript:**
Proceed with proximity-only matching (Step 5, branch 3). Flag every screenshot in the manifest as "low-confidence match; please verify" so the user knows to review them more carefully before publishing. This is common for Vimeo, Loom, and direct MP4 sources.

**When scene detection returns fewer than 3 candidates:**
Usually means the video is a static-camera talking head with no visual variation. Fall back to evenly-spaced samples across the video duration. This is the lowest-quality selection method — flag every screenshot as low-confidence in the manifest.

**When the video download fails (geo-block, private, removed):**
Stop and report with the exact `yt-dlp` error. Do not retry with a VPN or workaround — if the source isn't reachable from where the agent runs, the user needs to know so they can decide whether to re-run from a different location or pick a different video.

**When user-provided timestamps don't match section count:**
If `--timestamps` has a different count than target sections, honor the timestamps and drop excess sections (if fewer timestamps) or leave excess timestamps unused (if more timestamps). Report the mismatch clearly. Do not auto-fill from scene detection — the user explicitly chose manual control.

---

## What This Skill Does NOT Do

- **Does NOT write or edit the blog post content** — the prose is treated as input and preserved exactly. Only image blocks are inserted.
- **Does NOT make editorial decisions** about whether a section needs a screenshot beyond the visual-artifact check. If the user disagrees with a placement, they swap it in the manifest and re-run.
- **Does NOT upload images to a CMS** — that's handled by `cms-wordpress`, `cms-webflow`, or `cms-shopify` downstream.
- **Does NOT overwrite the original blog file** — output is always `<name>.with-images.md`.
- **Does NOT embed the YouTube player** — only still screenshots, each linked to its exact-second timestamp on YouTube. Players inside blog posts hurt Core Web Vitals and keep the reader on YouTube; timestamp deeplinks send them to the video only when they click proof.
- **Does NOT produce screenshots with pause icons, progress bars, or player UI** — frames come from the raw video stream, not from a browser screenshot.
- **Does NOT write to any environment-specific path** — everything is relative to `--work-dir`.
- **Does NOT fingerprint outputs with automation metadata** — EXIF strips `yt-dlp`, `ffmpeg`, and `Pillow` software tags.
- **Does NOT generate the blog post from the video** — that's the upstream `transcript-to-blog-post` skill. This skill picks up from its output.

---

## Examples

### Example 1: Happy Path — Edia Case Study Pillar

**Input:**
- `--video https://www.youtube.com/watch?v=abc123`
- `--blog ./edia-case-study.md`
- `--keyword "AI content strategy"`

**Blog structure (abbreviated):**
```
# Why Mass AI Content Strategies Collapse
## The Edia Case Study
[...prose referencing Ahrefs traffic graph...]
## The Traffic Collapse Timeline
[...prose referencing the month-by-month breakdown...]
## What Google's March 2024 Update Changed
[...prose referencing the SERP for AI-generated how-to queries...]
## The Contextual Connection
[...pure narrative, no visual claims...]
## FAQ
[...question/answer format, no visual claims...]
```

**Skill behavior:**
1. Identifies three visual-artifact sections: Edia Case Study (Ahrefs graph), Traffic Collapse Timeline (month breakdown), March 2024 SERP Change (SERP screenshot). Skips Contextual Connection and FAQ.
2. Downloads video + transcript. Transcript mentions "Edia" at 2:43, "month by month" at 4:18, "the SERP shows" at 6:55.
3. Scene detection returns 47 candidates. Matches: `edia-ahrefs-chart-01.png` at 2:45, `traffic-timeline-02.png` at 4:22, `serp-march-update-03.png` at 6:58.
4. Writes EXIF with creator "Jonathan Boshoff", keyword "AI content strategy", source URL.
5. Outputs `edia-case-study.with-images.md` with three wrapped-link image blocks and `manifest.md` with confidence "high" for all three.

Why this is correct: Only sections making a specific visual claim get an image. Transcript-matched timestamps land on the actual moment the artifact appears. Timestamp deeplinks point to the exact second of proof. EXIF is clean and SEO-optimized.

---

### Example 2: Edge Case — Manual Timestamps, No Transcript

**Input:**
- `--video https://vimeo.com/123456` (no auto-captions on Vimeo)
- `--blog ./dashboard-walkthrough.html`
- `--timestamps "0:15,1:40,3:25,5:10"`

**Skill behavior:**
1. Converts the HTML blog to markdown via pandoc fallback.
2. Identifies six visual-artifact sections.
3. User provided only four timestamps → honors all four, reports that the last two sections were dropped, asks user to re-run if they want coverage for those sections.
4. Skips scene detection entirely. Skips transcript matching entirely.
5. Extracts the four frames at the exact user-provided timestamps.
6. Generates image blocks with `#t=<seconds>s` fragment deeplinks (Vimeo syntax).
7. Manifest marks confidence "user-specified" for all four.

Why this is correct: User explicit control always wins. Skill degrades gracefully when Vimeo doesn't provide a transcript. Surface the section-count mismatch rather than silently auto-filling.

---

## Bundled Scripts

All scripts live in `./scripts/` and are referenced by the workflow steps above. Each does one thing:

| Script | Purpose |
|---|---|
| `preflight.sh` | Verify / install dependencies (ffmpeg check-only, others auto-install). |
| `download.py` | Wrap `yt-dlp` to fetch the best MP4 + auto-caption VTT. |
| `scenes.py` | Run ffmpeg scene detection, print candidate timestamps. |
| `extract.py` | Extract one full-quality PNG frame at a given timestamp. |
| `exif.py` | Write SEO EXIF with `exiftool` preferred, `piexif+Pillow` fallback. Strip GPS/camera/software tags. |

Call each via `python3 scripts/<name>.py --help` for exact CLI flags.
