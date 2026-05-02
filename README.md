# AI SEO Agent Skills

A small, focused public collection of agent skills for AI SEO — built by [Jonathan Boshoff](https://jonathanboshoff.com).

This repo hosts:

- **CMS publishing skills** — `cms-skills/wordpress`, `cms-skills/webflow`, `cms-skills/shopify`, plus `cms-skills/video-screenshot-extractor`
- **AI SEO Engine reference skills** — `ai-seo-engine-skills/` (frozen; kept for legacy reference)

Each skill is a self-contained instruction set any AI agent can fetch, read, and execute. No setup required. No API keys beyond the platform you're targeting (e.g., your CMS).

---

## What changed (May 2026)

The bulk of the operator skill library — page scrapers, sheet managers, market research, ASN deployment, profile creation, the stories-to-queries pipeline, and ~15 others — has moved.

These skills are now the foundation of **[Omnipresence](https://getomnipresence.com)** — the AI SEO operating system Jonathan built around the same methodology. Members get the full skill library plus the methodology and processes that compose them into actual SEO outcomes, all served through MCP into Claude, ChatGPT, Cursor, or any AI tool that speaks the protocol.

**Public access to the moved skills:** [join the Omnipresence community on Skool](https://www.skool.com/ai-seo) for membership info.

What stays free here: CMS publishing helpers + the AI SEO Engine reference. They're useful standalone, and they don't change much.

---

## Using what's here

```
skill-name/
├── SKILL.md          ← The entire skill. The only file an agent needs.
├── scripts/          ← Optional helper code referenced by SKILL.md
├── references/       ← Optional docs loaded into context as needed
└── assets/           ← Optional files used in output (templates, etc.)
```

**SKILL.md is the source of truth** for each skill. It contains description, inputs, outputs, workflow steps, edge cases, and examples — everything an agent needs to discover, evaluate, and execute the skill.

### For agents

Fetch `registry.yaml` first to discover what's available without scanning the tree, then fetch the matched `SKILL.md`.

```
https://raw.githubusercontent.com/boshify/ai-seo-agent-skills/main/registry.yaml
https://raw.githubusercontent.com/boshify/ai-seo-agent-skills/main/{skill-path}
```

### For humans

```bash
git clone https://github.com/boshify/ai-seo-agent-skills.git
```

Browse, copy what you need into your AI tool's context, modify freely. MIT-licensed.

---

## Skill standard

Want to write your own skills using the same architecture? See [`SKILL-STANDARD.md`](SKILL-STANDARD.md). The standard is portable — works for any agent runtime.

---

## License

MIT — see [LICENSE](LICENSE). Free to use, modify, and redistribute.
