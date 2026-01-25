# Sprint Plan: Agenda DASEi

**Sprint Start**: 2026-01-26  
**Status**: 🟡 In Progress  
**Estimated Duration**: Multi-day sprint  

---

## Referenced Action Plans

| Action Plan | Module | Focus |
|-------------|--------|-------|
| [2026-01-24-action_plan_event_package_integration.md](./2026-01-24-action_plan_event_package_integration.md) | `crearis` | Event packages, GraphQL, feature flags |
| [2026-01-24-action_plan_dasei_event_packages.md](./2026-01-24-action_plan_dasei_event_packages.md) | `agenda_dasei` | SharePoint sync, DASEi-specific mappings |
| [2026-01-28-action_plan_graphql.md](./2026-01-28-action_plan_graphql.md) | `graphql_theaterpedia` | GraphQL schema updates (future) |

---

## Sprint Tasks

### Phase 1: Planning & Blocking Questions

- [x] **S1**: Update both action plans with new tasks from sprint kickoff
- [x] **S2**: Resolve blocking question from yesterday (T0 / D0: `use_event_packages` scope)
  - **Decision**: Option B — Company-primary + product filtering
  - Cross-domain display concerns documented for GraphQL layer
- [ ] **S3**: Explore and resolve blocking tasks for module `crearis`:
  - [ ] S3.1: cid / xmlid alignment for events, posts
  - [ ] S3.2: Event-stages deduplication (repurpose existing xml-ids)
  - [ ] S3.3: Registration status-IDs (repurpose existing xml-ids)

### Phase 2: First Implementation Batch — `crearis`

> **Tasks from action plan**: A1-A5 in implementation sequence

- [ ] **S4**: Git commit (after blocking questions resolved)
- [ ] **S5.1**: DB cleanup — stage deduplication (delete seq 7,8,9,10 if duplicates exist)
- [ ] **S5.2**: T-CID-1 to T-CID-6: cid/slug architecture
- [ ] **S5.3**: Registration states R1-R8 (from impl plan)
- [ ] **S5.4**: T-UI-1: Template code visualization
- [ ] **S5.5**: T11-T14: Feature flag hierarchy
- [ ] **S6**: Git commit (after crearis batch 1)

### Phase 3: First Implementation Batch — `agenda_dasei`

> **Tasks from action plan**: B1-B5 in implementation sequence

- [ ] **S7.1**: DB1 — Remove duplicate stage definitions from agenda_dasei
- [ ] **S7.2**: Update sync_engine.py: map StatusLookupId → stage_id
- [ ] **S7.3**: DA1: Menu restructuring
- [ ] **S7.4**: D1-D8: SharePoint list infrastructure
- [ ] **S7.5**: DB2: event.user_id mapping investigation
- [ ] **S8**: Write dev-docs
- [ ] **S9**: Git commit (after agenda_dasei batch 1 + docs)

### Phase 4: Testing & Fixes

- [ ] **S10**: Debug, test, fix issues

### Phase 5: Prod A — First Production Deployment

- [ ] **S11**: First production deployment (enables website-coding project to start)
- [ ] **S12**: Run Prod A tasks (DPa1: extract product-templates)
- [ ] **S13**: Git commit (post Prod A)

### Phase 6: Remaining Tasks & Finalization

- [ ] **S14**: Run remaining tasks from both action-plans
- [ ] **S15**: Update dev-docs
- [ ] **S16**: Git commit (final sprint commit)

---

## Dev-Docs Tasks (Gather During Sprint)

> Add documentation tasks here as they arise. Write docs in Phase 3 (S8) and update in Phase 6 (S15).

| ID | Topic | Source | Status |
|----|-------|--------|--------|
| DOC-1 | T0/D0 decision: use_event_packages scope | T0 resolution | 📝 To write |
| DOC-2 | Cross-domain display concerns for GraphQL/VueJS | T0 discussion | 📝 To write |
| DOC-3 | package_only field behavior | T0 discussion | 📝 To write |
| DOC-4 | cid/slug/cidSlug architecture | B1 resolution | 📝 To write |
| DOC-5 | Sysreg bitmask system (generic) | B2 resolution | 📝 To write |
| DOC-6 | Event stages sysreg mapping | B2 resolution | 📝 To write |
| DOC-7 | SharePoint plan_planungsstatus full table | B2 discussion | 📝 To write |
| DOC-8 | Registration states sysreg mapping | B3 resolution | 📝 To write |
| DOC-9 | SharePoint plan_teilnahmestatus full table | B3 discussion | 📝 To write |
| | | | |

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
| | | | |

---

## Blocking Questions Status

| ID | Question | Status | Decision |
|----|----------|--------|----------|
| T0/D0 | `use_event_packages` scope (company vs website) | ✅ Resolved | Option B: Company-primary + product filtering |
| S3.1/B1 | cid/xmlid/slug alignment | ✅ Resolved | cid=stable id-based, slug=SEO editable, cidSlug=combined |
| S3.2/B2 | Event-stages sysreg mapping | ✅ Resolved | 7 stages (1,8,64,512,4096,8192,12288), i18n via .po files |
| S3.3/B3 | Registration states sysreg | ✅ Resolved | 8 states, impl plan created |

---

## Notes

- Sprint designed for iterative development with frequent commits
- Action plans contain the detailed task breakdowns
- This sprint plan serves as the coordination meta-layer
