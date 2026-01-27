# Sprint Plan: Agenda DASEi + Website Templates

**Sprint Start**: 2026-01-26  
**Sprint End**: 2026-02-07  
**Status**: 🟡 In Progress  
**Production Target**: 2026-01-30 (THU) — technically running  
**Next Sprint**: 2026-02-08 (Design Sprint for FEB 10 demo)

---

## Referenced Action Plans

| Action Plan | Module | Focus | Priority |
|-------------|--------|-------|----------|
| [2026-01-24-action_plan_event_package_integration.md](./2026-01-24-action_plan_event_package_integration.md) | `crearis` | Event packages, feature flags | ✅ Phase 1 Done |
| [2026-01-24-action_plan_dasei_event_packages.md](./2026-01-24-action_plan_dasei_event_packages.md) | `agenda_dasei` | SharePoint sync, DASEi mappings | 🟡 In Progress |
| [2026-01-26-action_plan_website_templates.md](./2026-01-26-action_plan_website_templates.md) | `website templates` | Customer portal UI (DASEi) | 🟡 In Progress |
| [2026-01-28-action_plan_graphql.md](./2026-01-28-action_plan_graphql.md) | `graphql_theaterpedia` | GraphQL schema updates | 🟠 Fork A (FEB 3-7) |

---

## Sprint Timeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  WEEK 1: JAN 27-31                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  MON 27: ✅ Event packages demo                                             │
│  TUE 28: Event locations sync, SharePoint-drives-updates mode               │
│  WED 29: Website templates foundation                                       │
│  THU 30: 🎯 PRODUCTION DEPLOY - technically running                         │
│  FRI 31: Fork start preparation                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  WEEK 2: FEB 3-7 (Two Parallel Forks)                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  FORK A: GraphQL → VueJS exploration                                        │
│  FORK B: Content work (meaningful interactions)                             │
│                                                                              │
│  Decision: full-odoo vs partly-vuejs vs major-vuejs                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Next Sprint**: [2026-02-08_sprint_dasei_launch.md](./2026-02-08_sprint_dasei_launch.md) — Design Sprint (SUN-TUE)

---

## Sprint Tasks

### Phase 1: Planning & Blocking Questions

- [x] **S1**: Update both action plans with new tasks from sprint kickoff
- [x] **S2**: Resolve blocking question from yesterday (T0 / D0: `use_event_packages` scope)
  - **Decision**: Option B — Company-primary + product filtering
  - Cross-domain display concerns documented for GraphQL layer
- [x] **S3**: Explore and resolve blocking tasks for module `crearis`:
  - [x] S3.1: cid / xmlid alignment for events, posts
  - [x] S3.2: Event-stages deduplication (repurpose existing xml-ids)
  - [x] S3.3: Registration status-IDs (repurpose existing xml-ids)

### Phase 2: First Implementation Batch — `crearis`

> **Tasks from action plan**: A1-A5 in implementation sequence

- [x] **S4**: Git commit (after blocking questions resolved)
- [x] **S5.1**: DB cleanup — stage deduplication (delete seq 7,8,9,10 if duplicates exist)
- [x] **S5.2**: T-CID-1 to T-CID-6: cid/slug architecture
- [x] **S5.3**: Registration states R1-R8 (from impl plan)
- [x] **S5.4**: T-UI-1: Template code visualization
- [x] **S5.5**: T11-T14: Feature flag hierarchy
- [x] **S6**: Git commit (after crearis batch 1)

### Phase 3: First Implementation Batch — `agenda_dasei`

> **Tasks from action plan**: B1-B5 in implementation sequence

- [x] **S7.1**: DB1 — Remove duplicate stage definitions from agenda_dasei
- [x] **S7.2**: Update sync_engine.py: map StatusLookupId → stage_id
- [x] **S7.3**: DA1: Menu restructuring
- [x] **S7.4**: D1-D8: SharePoint list infrastructure
- [x] **S7.5**: DB2: event.user_id mapping investigation
- [x] **S8**: Write dev-docs
- [x] **S9**: Git commit (after agenda_dasei batch 1 + docs)

### Phase 3b: Pre-Deployment Checklist (2026-01-27 morning)

> **Priority**: Production deployment before 08:00

- [x] **S9b.1**: Update manifest versions (dependencies)
- [ ] **S9b.2**: Git commit (pre-deployment)
- [ ] **S9b.3**: Update external modules (partner-contact, rest-framework)
- [ ] **S9b.4**: Domain codes → events/event_types (dasei1/dasei2/dasei3 foundation)
- [ ] **S9b.5**: Verify 'slave' sync mode (SharePoint drives sync)
- [ ] **S9b.6**: Sync-down event locations (one-way SP → Odoo)
- [ ] **S9b.7**: Deploy to production

### Phase 4: Website Templates — Demo Prep

> **Tasks from action plan**: W1-W4 for demo target

- [x] **S10**: W1.1 — User mapping (SP Person → event.user_id)
- [ ] **S11**: W1.2-W1.3 — Verify headline/overline/teasertext sync
- [ ] **S12**: W2.1-W2.3 — Pre-production deployment + debug
- [ ] **S13**: W3.1-W3.4 — Event card templates
- [ ] **S14**: W4.1-W4.3 — Event detail page
- [ ] **S15**: Git commit (demo checkpoint)

### Phase 5: Testing & Fixes

- [ ] **S16**: Debug, test, fix issues

### Phase 6: Production Deploy (THU JAN 30)

> **Goal**: dasei1 + dasei2 technically running, customer transition from dasei.eu

- [ ] **S17**: First production deployment
- [ ] **S18**: Verify event listing works on dasei1/dasei2
- [ ] **S19**: Basic registration flow test
- [ ] **S20**: Git commit (production checkpoint)

### Phase 7: Fork Preparation (FRI JAN 31)

- [ ] **S21**: Document current state for fork work
- [ ] **S22**: Identify GraphQL schema gaps
- [ ] **S23**: List content work priorities
- [ ] **S24**: 🔴 **REVIEW & DEEPEN DOCS** — Before Fork starts!
  - Review [dev_docs_quick_reference.md](./dev_docs_quick_reference.md)
  - Add code snippets, edge cases
  - Validate against actual implementation
  - Fill in DOC-7, DOC-9, DOC-10 (SharePoint schemas)

### Phase 8: Fork A — GraphQL/VueJS Exploration (FEB 3-7)

> **Goal**: Evaluate full-odoo vs partly-vuejs vs major-vuejs

- [ ] **FA1**: Review graphql_theaterpedia current schema
- [ ] **FA2**: Add event package queries to schema
- [ ] **FA3**: Test with Vue client prototype
- [ ] **FA4**: Document complexity vs benefit analysis
- [ ] **FA5**: Architecture decision recommendation

### Phase 9: Fork B — Content Work (FEB 3-7)

> **Goal**: Make "technically running" deliver meaningful interactions

- [ ] **FB1**: Event descriptions/teasertext review
- [ ] **FB2**: Module A-D product descriptions
- [ ] **FB3**: Welcome/info pages content
- [ ] **FB4**: Email templates for registrations
- [ ] **FB5**: Git commit (content batch)

### Phase 10: Sprint Wrap-up (FEB 7)

- [ ] **S24**: Final dev-docs update
- [ ] **S25**: Prepare handoff to Design Sprint
- [ ] **S26**: Git commit (sprint final)

---

## Dev-Docs Tasks (Gather During Sprint)

> Quick reference docs created: [dev_docs_quick_reference.md](./dev_docs_quick_reference.md)  
> **Action S24**: REVIEW & DEEPEN before Fork A starts

| ID | Topic | Source | Status |
|----|-------|--------|--------|
| DOC-1 | T0/D0 decision: use_event_packages scope | T0 resolution | ✅ In action plan |
| DOC-2 | Cross-domain display concerns for GraphQL/VueJS | T0 discussion | 🔴 Defer to Fork A |
| DOC-3 | package_only field behavior | T0 discussion | ✅ Quick ref |
| DOC-4 | cid/slug/cidSlug architecture | B1 resolution | ✅ Quick ref |
| DOC-5 | Sysreg bitmask system (generic) | B2 resolution | ✅ Quick ref |
| DOC-6 | Event stages sysreg mapping | B2 resolution | ✅ Quick ref |
| DOC-7 | SharePoint plan_planungsstatus full table | B2 discussion | 🟡 Other chat |
| DOC-8 | Registration states sysreg mapping | B3 resolution | ✅ Quick ref |
| DOC-9 | SharePoint plan_teilnahmestatus full table | B3 discussion | 🟡 Other chat |
| DOC-10 | plan_veranstaltungen full schema | S10 discussion | 🟡 Other chat |
| DOC-11 | plan_referenten schema + user mapping | S10 discussion | ✅ Quick ref |

---

## Progress Log

| Date | Task | Status | Notes |
|------|------|--------|-------|
| 2026-01-26 | Sprint kickoff | ✅ | Created sprint plan, updated action plans |
| 2026-01-26 | S2: T0/D0 resolved | ✅ | Option B chosen, concerns documented |
| 2026-01-26 | S3.1/B1: cid architecture | ✅ | cid=id-based stable, slug=SEO, cidSlug=combined |
| 2026-01-26 | S3.2/B2: event stages | ✅ | Sysreg mapping, i18n files created |
| 2026-01-26 | S3.3/B3: registration states | ✅ | Impl plan created, mapping defined |
| 2026-01-26 | S5.1: DB cleanup | ✅ | Old stages deleted, sequences updated |
| 2026-01-26 | S5.1: Migration script | ✅ | crearis/migrations/16.0.1.1.0/pre-migrate.py |
| 2026-01-26 | S5.2: cid/slug architecture | ✅ | event.event + blog.post updated |
| 2026-01-26 | S5.3: Registration states | ✅ | event_registration.py with extended states |
| 2026-01-26 | S5.4: Template code viz | ✅ | Grey box in event form |
| 2026-01-26 | S5.5: Feature flags | ✅ | use_products computed, use_event_packages added |
| 2026-01-26 | S6: crearis batch 1 commit | ✅ | Commit 5f18552 |
| 2026-01-26 | S7.1: DB1 stage cleanup | ✅ | No duplicates in agenda_dasei |
| 2026-01-26 | S7.2: StatusLookupId mapping | ✅ | STATUS_TO_STAGE_SYSREG in sync_engine |
| 2026-01-26 | S7.3: DA1 menu restructure | ✅ | DASEi submenu under Crearis |
| 2026-01-26 | S7.4: D1-D8 SharePoint lists | ✅ | plan_kurse + plan_veranstaltungsteilnehmer |
| 2026-01-26 | S8: Dev docs | ✅ | Updated agenda_dasei + crearis_agenda docs |
| 2026-01-26 | S9: agenda_dasei batch 1 commit | ✅ | Commit f6fe324 |
| 2026-01-26 | Refactor: use_event_packages | ✅ | Moved to crearis_event_package (3ad660d) |
| 2026-01-26 | S10: User mapping | ✅ | Hauptreferent → user_id via dasei.referent.sync |
| 2026-01-27 | S9b.1: Update manifests | ✅ | Dependencies updated |
| 2026-01-27 | Fix: view inheritance errors | ✅ | XML IDs renamed, mode=extension (32097bf) |
| 2026-01-27 | Fix: image controller | ✅ | str2bool bypass in graphql_theaterpedia |
| 2026-01-27 | Event package products | ✅ | 4 Grundkurs modules (A, B, C, D) with XMLIds (6ee7930) |
| 2026-01-27 | Website creation hooks | ✅ | post_init_hook creates dasei0-3 websites |
| 2026-01-27 | View fixes | ✅ | Removed duplicate field causing empty tags |
| 2026-01-27 | Dev docs updated | ✅ | agenda_dasei + crearis_event_package (0415b13) |
| 2026-01-27 | Demo presentation | ✅ | Event packages shown to team |
| 2026-01-27 | Next sprint planned | ✅ | 2026-02-08_sprint_dasei_launch.md created |
| 2026-01-27 | DOC-12: Stage migration docs | ✅ | JSONB format, 5 issues documented |
| 2026-01-27 | DOC-5/6/8 verification | ✅ | Corrected sysreg tables, added SP mappings |
| 2026-01-27 | Asymmetric sync strategy | ✅ | Documented SP→Odoo filtering + Odoo→SP triggers |

---

## Blocking Questions Status

| ID | Question | Status | Decision |
|----|----------|--------|----------|
| T0/D0 | `use_event_packages` scope (company vs website) | ✅ Resolved | Option B: Company-primary + product filtering |
| S3.1/B1 | cid/xmlid/slug alignment | ✅ Resolved | cid=stable id-based, slug=SEO editable, cidSlug=combined |
| S3.2/B2 | Event-stages sysreg mapping | ✅ Resolved | 7 stages (1,8,64,512,4096,8192,12288), i18n via .po files |
| S3.3/B3 | Registration states sysreg | ✅ Resolved | 8 states, impl plan created |
| W1.1 | SP Person column → event.user_id | ✅ Resolved | dasei.referent.sync + ms_referenten_filter |

---

## Backlog / Next Week

| ID | Task | Module | Priority | Notes |
|----|------|--------|----------|-------|
| BL-1 | Fix missing website logo field in settings | `crearis` | 🟡 Medium | Logo field missing from Website Settings UI. Likely xpath issue in `res_config_settings_views.xml`. Check line 66 in odoo/addons/website/views/website_views.xml which replaces logo field. Investigate if crearis view inheritance breaks it. |
| BL-2 | Non-Hauptstatus → Odoo tags mapping | `agenda_dasei` | 🟡 Medium | When SP event status is not in Hauptstatus list (first ID in mapping), create Odoo tag to flag data issue. See DOC-6 notes. |
| BL-3 | Verify SP field name for event status | `agenda_dasei` | 🟡 Medium | Confirm `plan_veranstaltungen.status` is correct field name — may have obscure/automated name. |
| BL-4 | Bescheinigung (certificate_eligible) field | `crearis` | 🟢 PRIO 3 | Add `certificate_eligible` computed field to registration. Maps to SP `Bescheinigung` column. Only true for `done` and `partial` states. See DOC-8. |

---

## Notes

- Sprint designed for iterative development with frequent commits
- Action plans contain the detailed task breakdowns
- This sprint plan serves as the coordination meta-layer
- **Demo Target**: 2026-01-27 11:00 — Focus on visible customer-facing features
- **GraphQL Guard**: Must start by end of week to stay on core architecture path
