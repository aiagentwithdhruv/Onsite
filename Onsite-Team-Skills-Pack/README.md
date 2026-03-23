# Onsite Team Skills Pack

> Skills and Cursor rules for Engineering, Sales, Marketing, and every department. Use with Claude (Code/Desktop) and Cursor so the whole team gets consistent Onsite context and best practices.

---

## What's Inside

| Folder | Contents | Use In |
|--------|----------|--------|
| **claude-skills/** | One folder per skill, each with `SKILL.md` | Cursor: copy to `.cursor/skills/`. Claude Code: copy to project or `~/.claude/skills/` |
| **cursor-rules/** | `.mdc` rule files | Cursor: copy to `.cursor/rules/` |

---

## Installation

### Cursor

1. **Skills (optional but recommended)**  
   Copy each folder from `claude-skills/` into your project’s `.cursor/skills/` (or `~/.cursor/skills/` for global):
   ```bash
   cp -r claude-skills/* .cursor/skills/
   ```

2. **Rules**  
   Copy all `.mdc` files from `cursor-rules/` into `.cursor/rules/`:
   ```bash
   cp cursor-rules/*.mdc .cursor/rules/
   ```

### Claude Code / Claude Desktop

Copy the contents of `claude-skills/` into your project’s `.claude/skills/` or your user skills directory so the agent can load them by name.

---

## Skills Overview

| Skill | For | Triggers |
|------|-----|----------|
| **onsite-context** | Everyone | Company, product, pricing, who does what |
| **onsite-engineering** | Engineering | Codebase, BOQ formats, APIs, stack |
| **onsite-sales** | Sales | Reps, pipeline, demos, revenue, deal tracking |
| **onsite-marketing** | Marketing | Campaigns, ads, CAC, channel ROI |
| **onsite-pre-sales** | Pre-Sales | Demo booking, Jyoti/Shruti/Chadni, ME capacity |
| **onsite-product** | Product | Features, roadmap, app metrics, benchmarks |
| **onsite-support** | Support | Tickets, Gallabox, onboarding, renewals |
| **onsite-finance** | Finance | Revenue, pricing, forecasting, deal sizes |
| **onsite-data-analytics** | Data/Analytics | CSV fields, date parsing, report patterns |
| **onsite-boq-data** | Ops/Implementation | BOQ/CSV upload formats, fix rules |
| **onsite-coding-standards** | Engineering | TypeScript, React, Python, testing |

---

## Cursor Rules Overview

| Rule | When it applies |
|------|------------------|
| **onsite-context.mdc** | Always (company/product context) |
| **onsite-engineering.mdc** | When editing `.ts`, `.tsx`, `.py`, `.js` in Onsite repos |
| **onsite-sales.mdc** | Sales analysis, pipeline, CRM, demos |
| **onsite-marketing.mdc** | Campaigns, ads, lead sources, ROI |
| **onsite-coding-standards.mdc** | Any code (TypeScript, React, Python, testing) |

---

## What the Onsite team uses (if needed)

When working with the main Onsite repo, these are the things the team actually uses. The skills in this pack reference them; for full detail, use the live repo:

| What | Where in Onsite repo |
|------|----------------------|
| **CRM & data** | Zoho CRM → CSV export. Primary CSV: `Last_Touched_Query` (sales-intelligence). |
| **Support / WA** | Gallabox (WhatsApp). Channel ID, API in support context. |
| **Quotations** | `quotation-generator.html` + `QuotationGenerator.gs` (Google Apps Script). PDF to Drive, email to client. |
| **Sales Intelligence** | `sales-intelligence/` — Next.js frontend, FastAPI backend, Supabase. Agents, dashboards, alerts. |
| **BOQ / uploads** | `knowledge/boq-fix/SKILL.md`, `knowledge/boq-fix/ONSITE_BOQ_FORMAT_GUIDE.md`, `knowledge/onsite-platform-knowledge-base.md`. |
| **Runbooks** | `runbooks/` — deploy sales-intelligence, add quotation feature, Zoho credentials. |
| **Department context** | `departments/` — Sales, Marketing, Pre-Sales, Support, Product, Finance, Data-Analytics (CONTEXT.md + SKILL.md each). |
| **Master context** | `.claude/CLAUDE.md` — company, product, pricing, tech, credentials. |
| **Loadout** | `LOADOUT.md` — full agent loadout, self-update schedule, sales ops context. |

Use the matching skill from this pack for AI assistance; use the paths above when you need the full docs or code.

---

## Departments Mapping

- **Engineering** → onsite-context, onsite-engineering, onsite-boq-data, onsite-coding-standards  
- **Sales** → onsite-context, onsite-sales  
- **Marketing** → onsite-context, onsite-marketing  
- **Pre-Sales** → onsite-context, onsite-pre-sales  
- **Product** → onsite-context, onsite-product  
- **Support** → onsite-context, onsite-support  
- **Finance** → onsite-context, onsite-finance  
- **Data / Analytics** → onsite-context, onsite-data-analytics  

---

*Pack generated for Onsite Teams. Update skills from `Onsite/knowledge/` and `Onsite/departments/` as needed.*
