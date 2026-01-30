# Crearis Agenda Whitepaper

**Version**: 0.1.0 (task)  
**Created**: 2026-01-30  
**Status**: Building structure from extended agenda prompt

---

## Chapters

| # | Chapter | Description | Stage |
|---|---------|-------------|-------|
| 0 | [chapter_conventions](chapter_conventions.md) | Document types, staging, linking rules | task |
| 1 | [chapter_philosophy](chapter_philosophy.md) | Crearis vision, opinionated decisions, why Odoo | task |
| 2 | [chapter_agenda_model](chapter_agenda_model.md) | Agenda lines, session lines, line-types, providers | task |
| 3 | [chapter_customer_journey](chapter_customer_journey.md) | 6 journeys: Karo, Ida, Jolanda, issue-driver, service-worker, instructor | task |
| 4 | [chapter_ui_design](chapter_ui_design.md) | 3-tab sidebar, responsive breakpoints, odoo integration | task |
| 5 | [chapter_workflows](chapter_workflows.md) | Monthly cycles, email flows, chatter integration | task |
| 6 | [chapter_onboarding](chapter_onboarding.md) | 3 transitions, checkout stepper, contract states | task |
| 7 | [chapter_architecture](chapter_architecture.md) | Module boundaries, crearis vs agenda_dasei vs sharepoint | task |

---

## Module Architecture

| Module | Scope | Notes |
|--------|-------|-------|
| **crearis** | Core: agenda-lines, session-lines, events, partners | Everything fundamental |
| **crearis_event_package** | Event packages, package lines | Good isolation example |
| **crearis_sharepoint** | SharePoint sync (renamed from crearis_agenda) | Sync-specific code |
| **agenda_dasei** | DASEi-specific: UI colors, product configs, M18 web-experience | Domain-specific extensions |

**Principle**: Don't struggle with dependencies early — assume 'crearis' for most things. Extensions can import from crearis.

---

## Implementation Rounds

| Round | Name | Focus | Status |
|-------|------|-------|--------|
| 1 | **Essentials** | Blocking tasks, whitepaper-driven | planned |
| 2 | **Unlock DASEi** | Full A,B,C,D business cycle | planned |
| 3 | **Build Details** | Refinements after production testing | future |

---

## Document Conventions

- **chapter_*.md**: Index files only (title + abstract + master docs table)
- **Master docs**: Actual content, no date prefix, no 'devdocs'/'chapter' prefix
- **Stages**: task → draft → dev → spec → user
- **Devdocs**: Intermediary, created on-the-fly, `devdocs_*.md`
- **Sprint docs**: Date-prefixed `YYYY-MM-DD-*.md`
- **Files**: Source examples in `chat/files/` subfolders

---

## Master Documents Created

| Document | Chapter | Content |
|----------|---------|---------|
| [onboarding_checkout_stepper](onboarding_checkout_stepper.md) | 6 | Inside-out architecture, mdc_generator |
| [onboarding_three_transitions](onboarding_three_transitions.md) | 6 | Discovery→Interest→Commitment |
| [workflow_email_templates](workflow_email_templates.md) | 5 | Confirmation, contract, newsletter |
| [ui_vue_components](ui_vue_components.md) | 4 | DataView, Cards, stepper flow |
| [architecture_module_boundaries](architecture_module_boundaries.md) | 7 | crearis vs agenda_dasei |

---

## Quick Links

- [Input: Intro](2026-01-30-agenda_extended_intro.md) — Session lines architecture, naming decisions
- [Input: Meta](2026-01-30-agenda_extended_meta.md) — This whitepaper's structure guide
- [Input: Core](2026-01-30-agenda_extended_core.md) — Role of Odoo, 3 tabs, design specs
- [Input: Journeys](2026-01-30-agenda_extended_journeys.md) — 6 customer stories
- [Input: Emails](2026-01-30-agenda_extended_emails.md) — Email templates and examples
- [Input: Images](2026-01-30-agenda_extended_images.md) — UI reference images
- [Input: URLs & Code](2026-01-30-agenda_extended_urls_and_code.md) — Vue components, checkout stepper
