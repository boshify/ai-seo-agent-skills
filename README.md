# AI SEO Agent Skills

Free, open-source agent skills for AI SEO — built by [Jonathan Boshoff](https://jonathanboshoff.com) and maintained by the [AI SEO Academy](https://www.skool.com/ai-seo) community.

Each skill is a self-contained instruction set that any AI agent can fetch, read, and execute. No setup required. No API keys. No dependencies beyond the agent itself.

---

## What's in Here

Every skill follows the same architecture:

```
skill-name/
├── SKILL.md          ← The entire skill. This is the only file an agent needs.
└── scripts/          ← Optional helper code referenced by SKILL.md
└── references/       ← Optional docs loaded into context as needed
└── assets/           ← Optional files used in output (templates, etc.)
```

**SKILL.md is the source of truth.** It contains the skill description, inputs, outputs, workflow steps, edge cases, and examples — everything an agent needs to discover, evaluate, and execute the skill. Supplementary files only exist when SKILL.md explicitly references them.

---

## For Agents: Programmatic Discovery

Read [`registry.yaml`](registry.yaml) to find the right skill without scanning every directory.

```
1. Fetch registry.yaml
2. Match your task to a skill (by description, tags, or inputs)
3. Fetch the matched skill's SKILL.md
4. Execute the workflow steps in order
```

**Raw URL pattern:**
```
https://raw.githubusercontent.com/boshify/ai-seo-agent-skills/main/registry.yaml
https://raw.githubusercontent.com/boshify/ai-seo-agent-skills/main/{skill-path}
```

The registry is intentionally denormalized — each entry contains enough information to make a selection decision without fetching any SKILL.md files. One read, one decision, one fetch.

---

## For Humans: Browse, Clone, Modify

```bash
git clone https://github.com/boshify/ai-seo-agent-skills.git
```

Every skill works standalone. Clone the whole repo or just grab the SKILL.md for the one you need. Modify freely — these are MIT licensed.

**Using a skill manually:**
1. Open the SKILL.md for the skill you want
2. Copy the full contents into your AI agent's context (Claude, ChatGPT, etc.)
3. Provide the required inputs described in the skill
4. The agent executes the workflow and produces the output

---

## Available Skills

<!-- This section updates as skills are added. See registry.yaml for the programmatic version. -->

| Skill | What It Does |
|-------|-------------|
| [ai-seo-engine](ai-seo-engine-skills/SKILL.md) | Programmatic access to AI SEO Engine — manage projects, generate content, retrieve deliverables from Google Drive |
| [cms-wordpress](cms-skills/wordpress/SKILL.md) | Publish content to WordPress via WP-CLI or REST API with SEO metadata |
| [cms-webflow](cms-skills/webflow/SKILL.md) | Publish content to Webflow CMS collections via API v2 |
| [cms-shopify](cms-skills/shopify/SKILL.md) | Publish blog articles and pages to Shopify via Admin REST API |

---

## How These Skills Are Built

Every skill in this repo follows the [AI SEO Agent Skill Standard](SKILL-STANDARD.md) — a structured format designed for reliable agent execution across any runtime.

Key conventions:
- **YAML frontmatter** with machine-readable metadata (inputs, outputs, tags, chaining info)
- **Step-by-step workflows** with explicit Input → Process → Output → Decision Gate per step
- **Edge cases documented** so agents handle ambiguity instead of hallucinating
- **Examples included** so agents see what correct execution looks like

Want to contribute a skill? Follow the standard and open a PR.

---

## The Bigger Picture

These skills are the **component layer** of a larger AI SEO system. They work on their own, but they're designed to chain together — each skill's output can feed another skill's input.

- **Free skills** (this repo) → Manual or single-agent execution
- **[AI SEO Engine](https://aiseoengine.studio)** → Automated orchestration across your SEO workflow
- **[AI SEO Academy](https://www.skool.com/ai-seo)** → Free community of 3k+ AI SEOs building with these tools

The skills are free. The orchestration that chains them together and runs them autonomously — that's [AI SEO Engine](https://aiseoengine.studio).

---

## License

[MIT](LICENSE) — use freely, modify freely, no attribution required.

---

Built by [Jonathan Boshoff](https://jonathanboshoff.com) · [AI SEO Academy](https://www.skool.com/ai-seo) · [AI SEO Engine](https://aiseoengine.studio) · [Rank Builders](https://rankbuilders.co)
