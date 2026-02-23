---
name: onsite-sales-intelligence
version: 1.0.0
description: AI loadout for construction SaaS sales intelligence & quotation automation
author: AiwithDhruv
license: proprietary
tier: premium
last_verified: 2026-02-23
refresh_cadence: monthly
dependencies: []
platforms: [claude-code, cursor]
---

# Onsite — Agent Loadout

> Equip any AI agent with complete domain expertise for Onsite Teams (construction management SaaS). Covers company context, market research, competitor analysis, sales playbook, codebase knowledge, and automation recipes.

---

## What's Included

| File | Type | Purpose |
|------|------|---------|
| `.claude/CLAUDE.md` | Context | Auto-loaded master context (~500 lines) — company, pricing, market, sales, architecture |
| `sales-intelligence-system/SKILL.md` | Skill | Sales Intelligence System — codebase map, competitor intel, technical recipes |
| `knowledge/construction-market.md` | Knowledge | Market size, growth rates, government spending, India construction drivers |
| `knowledge/competitors.md` | Knowledge | 7 India + 5 global competitors with pricing and differentiators |
| `knowledge/sales-intelligence-tools.md` | Knowledge | 12 sales intelligence tools analyzed — what to steal from each |
| `knowledge/glossary.md` | Knowledge | Construction + regulatory terms (DPR, RA Bills, BOQ, RERA, GST) |
| `runbooks/deploy-sales-intelligence.md` | Runbook | Step-by-step deployment to Railway + Vercel |
| `runbooks/add-quotation-feature.md` | Runbook | How to add features to the quotation generator |
| `runbooks/zoho-credential-setup.md` | Runbook | Zoho CRM OAuth setup and webhook configuration |
| `tests/quotation-tests.md` | Tests | Quotation generator math validation (3 scenarios) |
| `tests/sales-intelligence-tests.md` | Tests | Sales intelligence system validation (5 scenarios) |

---

## Quick Start

### For Claude Code
1. Open `Onsite/` as project root — `.claude/CLAUDE.md` auto-loads
2. Agent immediately knows: company, pricing, market, codebase, credentials
3. For sales intelligence work: agent reads `SKILL.md` for deep technical context
4. For deployment: agent follows `runbooks/deploy-sales-intelligence.md`
5. For math verification: agent checks `tests/quotation-tests.md`

### For Cursor
1. Copy `.claude/CLAUDE.md` content into `.cursor/rules/onsite-context.mdc`
2. Add `SKILL.md` as additional context for sales-intelligence work

### For Any AI Agent
1. Feed `CLAUDE.md` as system prompt or context
2. Feed relevant `knowledge/*.md` files for domain expertise
3. Feed `SKILL.md` for technical codebase understanding

---

## Self-Update Schedule

| Component | Refresh | Trigger |
|-----------|---------|---------|
| Pricing tables | Monthly | Check onsiteteams.com/onsite-pricing |
| Competitor data | Quarterly | Web search for construction SaaS India |
| Market size numbers | Yearly | Check Fortune/Mordor Intelligence reports |
| Codebase map (SKILL.md) | Every coding session | Auto-update after changes |
| Credentials | On failure | Test, update if expired |
| Sales playbook | Quarterly | Review win/loss data |

---

## Changelog

### v1.0.0 (2026-02-23)
- Initial loadout creation
- CLAUDE.md: Complete company profile, pricing, market research, sales playbook, architecture, credentials
- SKILL.md: Full codebase map, 12 competitor analyses, lead scoring model, technical recipes
- Knowledge files: market, competitors, tools, glossary
- Runbooks: deployment, quotation features, Zoho setup
- Test cases: quotation math, sales intelligence validation
- Self-update rules added to CLAUDE.md and SKILL.md
