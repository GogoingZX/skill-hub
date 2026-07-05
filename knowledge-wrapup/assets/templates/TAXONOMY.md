# TAXONOMY — knowledge base classification

Maintained by knowledge-wrapup; edit freely. Naming: lowercase kebab-case English.
Machine contract: `## <slug>` = domain, `- <slug>` under it = subdomain; inside
the `## Tags` section, `- <slug>` = registered tag. Everything else is prose.

## finance
- risk-management
- portfolio-management

## algo

## technology
- ai-engineering
- tools

## Tags

### Nature
- best-practice
- conventions
- internals
- recovery

### Topic
- workflow

### Tooling
- cli
- automation

## Rules

1. Every note belongs to exactly one domain (its folder location). Cross-cutting
   topics are expressed with tags and wikilinks, not duplicate files.
2. Two levels maximum. Finer distinctions use tags.
3. A level-2 subdomain is split out only when a subtopic accumulates ~8–10 notes,
   or when the user directs it.
4. New domains are allowed, but each one must be added here and announced in the
   run report — no silent vocabulary drift.
5. Tags come from the `## Tags` registry above. Reuse first (check the registry
   and `obsidian tags`); a genuinely new tag is registered here in the same run
   and announced in the report.
6. 2–4 tags per note is the target (1–5 is the hard limit). Never tag what the
   domain already says — no `git` tag on a note living in `technology/git`.
