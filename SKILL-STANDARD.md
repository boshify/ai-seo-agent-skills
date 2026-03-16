# AI SEO Agent Skill Standard

Every skill in this repo follows this structure. If you're contributing a skill or building your own, use this as your blueprint.

---

## Skill Architecture

```
skill-name/
├── SKILL.md          ← Required. The entire skill in one self-describing file.
├── scripts/          ← Optional. Executable code for deterministic tasks.
├── references/       ← Optional. Docs loaded into context as needed.
└── assets/           ← Optional. Files used in output (templates, etc.)
```

**One file is the source of truth.** Everything an agent needs to discover, evaluate, and execute a skill lives in SKILL.md. Supplementary files exist only when SKILL.md explicitly references them.

---

## SKILL.md Structure

Every SKILL.md has these sections:

### 1. YAML Frontmatter

Two zones:

**Triggering zone** (top) — `name`, `version`, `description`. This is what agent runtimes read to decide whether to load the skill.

**Cross-agent metadata** (bottom) — `inputs`, `outputs`, `tools_used`, `chains_from`, `chains_to`, `tags`. For programmatic discovery by other agents and the registry.

```yaml
---
name: skill-name-here
version: "1.0"
description: >
  What this skill does in one sentence. Use this skill whenever [trigger conditions].
  This skill produces [specific deliverable]. Always trigger when [broadest safe condition].

inputs:
  required:
    - type: text
      label: "primary-input"
      description: "What the user must provide"
  optional:
    - type: text
      label: "secondary-input"
      description: "What improves output if present"

outputs:
  - type: markdown
    label: "primary-deliverable"
    description: "What the skill produces"

tools_used: []
chains_from: []
chains_to: []
tags: [seo, relevant-tag]
---
```

### 2. What This Skill Does

Two sentences max. What transformation happens, and what the user gets.

### 3. Context the Agent Needs

Decision-making context only. If removing a sentence wouldn't change how the agent executes, cut it.

### 4. Workflow Steps

Numbered steps, executed in order. Each step follows this skeleton:

```markdown
### STEP N: [Verb] + [Object]

[Why this step matters — one sentence.]

**Input:** [What this step reads]
**Process:**
1. [Concrete action — max 5 sub-steps]
2. [Concrete action]
**Output:** [What this step produces, including format]
**Decision gate:**
- If [condition A] → proceed to next step
- If [condition B] → [alternative action]
```

### 5. Output Format

Exact template for the final deliverable, with formatting rules.

### 6. Edge Cases & Judgment Calls

Minimum four: incomplete input, ambiguous classification, oversized output, failed tool call.

### 7. What This Skill Does NOT Do

Explicit boundaries. Prevents over-triggering and sets expectations.

### 8. Examples

At least two: one happy path, one edge case. Each demonstrates a judgment call, not just format.

---

## Chaining Skills

Skills are designed to chain. The `chains_from` and `chains_to` fields in the frontmatter define the pipeline:

```
skill-a (chains_to: [skill-b]) → skill-b (chains_from: [skill-a], chains_to: [skill-c]) → skill-c
```

An agent can read these fields to auto-suggest the next skill after completing one, or validate that prerequisites exist before running.

---

## Contributing

1. Follow this standard
2. Add your skill as a new directory: `your-skill-name/SKILL.md`
3. Add an entry to `registry.yaml`
4. Open a PR

Quality bar: the skill should produce reliable output across different agent runtimes (Claude, ChatGPT, etc.) without requiring runtime-specific instructions.
