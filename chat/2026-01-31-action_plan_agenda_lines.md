# Action Plan: agenda.line Implementation

**Date**: 2026-01-31  
**Updated**: 2026-02-02 (afternoon)  
**Status**: ✅ Phase 1 IMPLEMENTED, ✅ Phase 4A IMPLEMENTED, ✅ Phase 6A IMPLEMENTED  
**Blocking**: ~~Domain codes task (Monday)~~ RESOLVED

---

## ⚡ February 2 Afternoon: crearis_milestones Module

### New Module Created: `crearis_milestones` v16.0.1.0.0

```
crearis_milestones/
├── __init__.py
├── __manifest__.py              # depends: crearis, account
├── data/
│   └── mail_template_data.xml   # 3 email templates (ready, triage, reminder)
├── models/
│   ├── __init__.py
│   ├── agenda_line.py           # Extended cron + helper methods
│   ├── agenda_line_blocker.py   # NEW model: blocker tracking
│   └── event_registration.py    # Check fields + actions
├── security/
│   └── ir.model.access.csv      # Blocker model access rights
└── views/
    ├── agenda_line_blocker_views.xml    # Blocker CRUD views
    ├── controlling_views.xml             # Main Controlling dashboard
    └── event_registration_views.xml      # Check form extension
```

### Key Features

| Feature | Description |
|---------|-------------|
| **Check States** | `pending` → `ready` → `confirmed` (+ `issue` for problems) |
| **Blocker Detection** | Automatic: payment_overdue, event_unresolved, confirmation_pending |
| **Controlling Dashboard** | Tree view grouped by Event (= Milestone) |
| **Bulk Confirmation** | Server action to confirm all BEREIT checks at once |
| **Override Flow** | Explicit manager override for checks with blockers |

### Next Steps

1. **Install test**: `./odoo/odoo-bin -d testdb -u crearis_milestones --stop-after-init`
2. **Add translations**: German (de) and Czech (cz) .po files (4A.3, 4A.4)
3. **Phase 3**: Product-driven agenda.lines (crearis_event_package)

---

## ⚡ February 2 Morning: crearis Phase 1 Summary

### Files Changed

| File | Change |
|------|--------|
| `crearis/models/agenda_line.py` | NEW — Renamed from event_session_line.py, added all new fields |
| `crearis/models/event.py` | Updated O2M, added use_milestones, _sync_agenda_lines |
| `crearis/models/website.py` | Added use_milestones field |
| `crearis/models/res_company.py` | Added use_milestones + milestone_label_* fields |
| `crearis/models/schedule_mixin.py` | Updated to call _sync_agenda_lines |
| `crearis/views/agenda_line_views.xml` | NEW — Renamed, added gate_state columns |
| `crearis/views/event_schedule_views.xml` | Updated to use agenda_line_ids |
| `crearis/data/ir_cron_data.xml` | NEW — Daily milestone check cron |
| `crearis/security/ir.model.access.csv` | Updated model references |
| `crearis/migrations/16.0.1.3.0/pre-migrate.py` | NEW — Table rename migration |
| `crearis/__manifest__.py` | Version bump to 16.0.1.3.0 |
| `agenda_dasei/data/milestone_defaults.xml` | NEW — German labels and defaults |
| `agenda_dasei/__manifest__.py` | Added milestone_defaults.xml |

### Files Removed

| File | Reason |
|------|--------|
| `crearis/models/event_session_line.py` | Replaced by agenda_line.py |
| `crearis/views/event_session_line_views.xml` | Replaced by agenda_line_views.xml |

---

## ⚡ February 2 Updates

### Terminology Changes

| Old (Jan 31) | New (Feb 2) | Reason |
|--------------|-------------|--------|
| `meldefrist_days_before` | `milestone_days_before` | Generic, not German-specific |
| `use_meldefrist` | `use_milestones` | Broader concept |

### New Decisions

| Decision | Choice | Notes |
|----------|--------|-------|
| **Gate Pattern** | All 3 stage transitions are GATED | Not automatic |
| **gate_state field** | `pending` → `ready` → `sent` / `issue` | On milestone lines only |
| **Trigger mechanism** | Daily cron | Checks milestone dates |
| **use_milestones location** | Website (domain_code) + Company fallback | Existing pattern |
| **Company labels** | `milestone_label_activation/deadline/completion` | Configurable per company |
| **English defaults** | "Activation", "Deadline", "Completion" | German in agenda_dasei |

### Three Milestone Types

| Key | Default Label | Stage Transition |
|-----|---------------|------------------|
| `activation` | "Activation" | draft → confirmed |
| `deadline` | "Deadline" | confirmed → released |
| `completion` | "Completion" | released → completed |

### Master Documents Created

- [architecture_agenda_lines.md](../_meta/Whitepaper/architecture_agenda_lines.md) — Model, providers, views
- [architecture_milestones_and_actions.md](../_meta/Whitepaper/architecture_milestones_and_actions.md) — Full gate pattern
- [architecture_agenda_lines_negative_spec.md](../_meta/Whitepaper/architecture_agenda_lines_negative_spec.md) — What is NOT in essentials

### Phase Updates

| Phase | Update |
|-------|--------|
| Phase 1 | Add `gate_state` field (milestone lines only) |
| Phase 4 | Rename `meldefrist_*` → `milestone_*`, add cron |
| Phase 7 | Views use company labels |

---

## Decision Points Summary

Collected from today's documents: core_draft, imagination scenarios A/F/G, investigation report.

### D1. Model Naming ⚡ DECIDED

| Question | Options | Recommendation |
|----------|---------|----------------|
| Rename `event.session.line` → `agenda.line`? | Keep / Rename | **RENAME** — broader scope (5 types) justifies it |

**Rationale**: The 5 types (session, meeting, milestone, info, action) go beyond "sessions". OCA's `event.session` is heavyweight; we stay lightweight with `.line` suffix.

---

### D2. Provider Relations ⚡ DECIDED

| Question | Options | Recommendation |
|----------|---------|----------------|
| How to link agenda.line to providers? | Single ref field / Multiple M2O | **Multiple M2O** — explicit, typed relations |

**Fields**:
```python
event_id = fields.Many2one('event.event', ondelete='cascade')
post_id = fields.Many2one('blog.post', ondelete='cascade')
product_id = fields.Many2one('product.template', ondelete='cascade')
provider_type = fields.Selection(compute='_compute_provider_type', store=True)
```

**Constraint**: Exactly one provider should be set (validated in `@api.constrains`).

---

### D3. Source of Truth (JSONB vs Table) ⚡ DECIDED

| Question | Options | Recommendation |
|----------|---------|----------------|
| Sync direction? | JSON→Table only / Bidirectional | **JSON→Table (readonly)** for source='json' |

**Rationale** (from 2026-01-28 "keep it simple"):
- JSONB serves GraphQL directly
- Enables SharePoint write-back
- Flexible schema evolution

**Implementation**:
```python
source = fields.Selection([
    ('json', 'From Schedule JSON'),      # Readonly, synced from JSONB
    ('template', 'From Template'),        # Readonly, generated on event create
    ('manual', 'Manual Entry'),           # Editable
    ('chatter', 'From Chatter'),          # Editable
])
locked_edits = fields.Boolean(default=False)  # True for json/template sources
```

---

### D4. Two Distinct agenda.line Sources ⚡ DECIDED

| Source | Trigger | Lines Created | Key Deadline |
|--------|---------|---------------|--------------|
| **Product** (Module) | `sale.order.line.create()` | Multiple (6-9 per module) | Stornierungsfrist |
| **Event** (Offenes Programm) | `event.registration.create()` | One per registration | Meldefrist |

**Product-driven**: Extends `product.package.event.line` with `agenda_line_id`.
**Event-driven**: Extends `event.registration` to create agenda.line on direct registration.

---

### D4A. Milestone vs Check Architecture ⚡ DECIDED (2026-02-02)

**Reference**: [architecture_milestones_and_actions.md](../_meta/Whitepaper/architecture_milestones_and_actions.md) Section "Für Anwender"

**Problem**: The Controlling UI needs two levels:
1. **Milestone** = Event-level (e.g., "A3 — Meldefrist 14.11")
2. **Check** = Participant-level (e.g., "Max ✓", "Selma ⚠️")

**Decision**: Registration IS the Check

| Level | Model | Key Fields |
|-------|-------|------------|
| **Milestone** | `agenda.line` (type='milestone') | `event_id`, `gate_state`, `milestone_days_before` |
| **Check** | `event.registration` | `check_state`, `check_comment`, `has_blockers` |

**Why not separate `agenda.line` per registration?**
- Registration already has `partner_id` (for blocker detection)
- Registration already has `event_id` (for grouping)
- Avoids N×M explosion of records
- Odoo tree views naturally group by `event_id`

**Controlling View Pattern**:
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Model: event.registration                                                  │
│  Group by: event_id (= Milestone)                                          │
│  Filters: BEREIT (check_state=ready, has_blockers=False)                   │
│           TRIAGE (check_state=issue OR has_blockers=True)                  │
│  Bulk action: action_confirm_all (on filtered selection)                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Terminology** (German UI):
| English | German | Model |
|---------|--------|-------|
| Milestone | Meilenstein | agenda.line |
| Check | Prüfpunkt / TN | event.registration |
| Blocker | Blocker | agenda.line.blocker (linked via partner) |

---

### D5. Unresolved Event Slots (CRM Workflow) ⚡ DECIDED

| Question | Options | Recommendation |
|----------|---------|----------------|
| Handle `event_id=False` package lines? | Ignore / CRM workflow | **CRM workflow** — critical for retention |

**Features**:
- Color-coded UI: 🟢 resolved, 🟡 pending, 🔴 overdue, ⚫ cancelled
- "Ambiguous Agendas Report" (6-month horizon)
- Automated reminder workflow
- Dashboard widget: "Resolution Queue"

---

### D6. Preserve Existing Fields ⚡ DECIDED

From CONSIDERATION 3 (Hybrid Event Problem):

| Field | Keep? | Reason |
|-------|-------|--------|
| `location_hint` | ✅ | Hybrid reporting ("which sessions at Tanzerei?") |
| `room` | ✅ | Room-level filtering |
| `conference_url` | ✅ | Online session links |
| `conference_id` | ✅ | External meeting IDs |
| `conference_provider` | ✅ | msteams/zoom/jitsi/other |

---

### D7. Type + Mode Fields ⚡ DECIDED

| Type | Modes | Description |
|------|-------|-------------|
| `session` | online/venue/individual/tbd | Time slot within event |
| `meeting` | online/venue | Outside event, prep/planning |
| `milestone` | — | Status check, deadline |
| `info` | — | Announcement, newsletter |
| `action` | — | Task, decision, document |

---

### D8. Template Inheritance ⚡ DECIDED (Consecutive Days)

**Approach**: Consecutive days pattern with in-presence anchor.

**Key Insight**: `date_begin`/`date_end` = first/last **in-presence** day, not first/last session overall.
- Online sessions may fall **before** `date_begin` or **after** `date_end`
- This is intentional: if online session shifts, event display dates stay stable

**Date Resolution Algorithm**:

1. **Anchor**: First in-presence slot in template → anchored to `date_begin`
2. **In-presence block**: Consecutive days from `date_begin` (Fri→Sat→Sun)
3. **Pre-event online**: If no explicit date inline, find first matching weekday **before** `date_begin`
4. **Post-event online**: Find **next** matching weekday after last resolved slot (simple consecutive logic)

*Note: Future validation could detect if `date_end` falls too early/late compared to template schedule.*

**Example** (Grundlagenkurs, `date_begin` = Friday March 13):
```
Template slot          | Resolved date      | Notes
-----------------------|--------------------|-------
online (Thu 19:00)     | Thu March 5        | Week before, matching weekday
venue (Fri 17:00)      | Fri March 13       | = date_begin (anchor)
venue (Sat 09:00)      | Sat March 14       | Consecutive
venue (Sun 09:00)      | Sun March 15       | = date_end
online (Thu 19:00)     | Thu March 19       | Week after, matching weekday
```

**Module**: `crearis` (algorithm), `agenda_dasei` (Grundlagenkurs template data)

---

### D9. Attendance Tracking ⚡ DECIDED (Simple First)

**Core Insight**: Attendance tracking is an **automation feature** — but `completed`/`partial` can be manually altered after automation sets it on the event.registration level.

**Phase 1 (Simple)**:
| Config | Level | Description |
|--------|-------|-------------|
| `attendance_completion_mode` | Company | Selection: `manual`, `threshold`, `full_attendance` |
| `attendance_threshold` | Company | Integer (default 80%) — only used if mode=`threshold` |

**Phase 2 (Extension, non-breaking)**:
| Config | Level | Description |
|--------|-------|-------------|
| Override rules | Company | Can override + set defaults |
| `attendance_completion_mode` | Event Type | Optional override of company default |

**Status Field** (on `event.registration`):
```python
completion_status = fields.Selection([
    ('pending', 'Pending'),      # Event not yet finished
    ('completed', 'Completed'),  # Met threshold (auto or manual)
    ('partial', 'Partial'),      # Below threshold (auto or manual)
], default='pending')
completion_status_manual = fields.Boolean(default=False)  # True if manually overridden
```

**Module**: `crearis` (field + automation), company config in base settings.

---

### D10. Posts as Provider 🔴 INVESTIGATION NEEDED

| Question | Status |
|----------|--------|
| How do blog.post records link to agenda.lines? | Not investigated |
| What triggers post→agenda.line creation? | Unknown |

**Task**: Investigation needed on posts model (bottom of plan).

---

## Decision → Module Correlation Matrix

This matrix shows how each decision point affects module implementation:

| Decision | crearis | crearis_event_package | agenda_dasei | Notes |
|----------|---------|----------------------|--------------|-------|
| D1. Model Name | ✓ | — | — | Rename in core |
| D2. Provider Fields | ✓ | — | — | Generic relation pattern |
| D3. Source of Truth | ✓ | — | — | JSONB sync in core |
| D4. Two Sources | ✓ (event-driven) | ✓ (product-driven) | — | Split implementation |
| D5. CRM Workflow | — | ✓ | ✓ (templates) | Infrastructure + content |
| D6. Existing Fields | ✓ | — | — | Keep in core model |
| D7. Type + Mode | ✓ | — | — | Core selection fields |
| D8. Template Inheritance | ✓ | — | ✓ (data) | Engine + defaults |
| D9. Attendance | ✓ | — | — | Future: core model |
| D10. Posts Provider | ? | — | — | Investigation needed |

### Key Correlations

1. **D4 + D5 Correlation**: The two sources (Product/Event) create different CRM needs:
   - Product-driven → needs Resolution Queue (in `crearis_event_package`)
   - Event-driven → simpler (just Meldefrist milestone in `crearis`)

2. **D3 + D8 Correlation**: Both involve JSONB storage:
   - D3 (schedule_json) lives on `event.event` 
   - D8 (schedule_template) lives on `event.type`
   - Both managed in `crearis`, template content from `agenda_dasei`

3. **D5 + D6.6 Correlation**: CRM workflow email templates:
   - Infrastructure (cron, mail.template record) → `crearis_event_package`
   - German content (body_html) → `agenda_dasei` data files

---

## Implementation Phases

---

### Module Location Legend

| Module | Purpose | Key Models |
|--------|---------|------------|
| **crearis** | Core agenda.line model, generic relations | agenda.line, event extensions |
| **crearis_event_package** | Product/package-driven functionality | product.package.event.line, stornierungsfrist |
| **agenda_dasei** | DASEi-specific defaults and templates | Data files, German email templates |

---

### Phase 0: Field Rename (Prerequisite)

**Module**: `crearis`, `crearis_agenda`
**Goal**: Rename `template_units` → `teaching_units` for semantic clarity

| # | Task | Module | Depends On | Estimate |
|---|------|--------|------------|----------|
| 0.1 | Rename field in `event.py`: `template_units` → `teaching_units` | crearis | — | 0.5h |
| 0.2 | Update view reference in `event_type_views.xml` | crearis | 0.1 | 0.5h |
| 0.3 | Update sync_engine.py references (3 occurrences) | crearis_agenda | 0.1 | 0.5h |
| 0.4 | Create migration script for column rename | crearis | 0.1 | 1h |
| 0.5 | Update documentation references in chat/*.md | — | 0.4 | 0.5h |

**Files affected**:
- `crearis/models/event.py` (field definition)
- `crearis/views/event_type_views.xml` (view)
- `crearis_agenda/models/sync_engine.py` (sync logic)

**Deliverable**: Field renamed with data preserved, clearer semantics (UE = Unterrichtseinheiten).

---

### Phase 1: Model Refactoring (Foundation)

**Module**: `crearis`
**Rationale**: `event.session.line` already lives in crearis, natural home for agenda.line

**Goal**: Rename and extend `event.session.line` → `agenda.line`

| # | Task | Module | Depends On | Estimate |
|---|------|--------|------------|----------|
| 1.1 | Create migration script for model rename | crearis | Phase 0 | 2h |
| 1.2 | Update model file: `event_session_line.py` → `agenda_line.py` | crearis | 1.1 | 1h |
| 1.3 | Add `type` field with 5 types (session, meeting, milestone, info, action) | crearis | 1.2 | 1h |
| 1.4 | Add `mode` field (online/venue/individual/tbd) | crearis | 1.2 | 0.5h |
| 1.5 | Add `source` field (json/template/manual/chatter) | crearis | 1.2 | 0.5h |
| 1.6 | Add `locked_edits` boolean | crearis | 1.5 | 0.5h |
| 1.7 | Update all view references (`event_session_line` → `agenda_line`) | crearis | 1.2 | 2h |
| 1.8 | Update security rules (ir.model.access.csv) | crearis | 1.2 | 0.5h |
| 1.9 | Run tests, fix breakages | crearis | 1.7, 1.8 | 2h |

**Deliverable**: `agenda.line` model with backward-compatible fields.

---

### Phase 2: Provider Relations ✅ COMPLETE (2026-02-02)

**Module**: `crearis`
**Status**: Implemented in Phase 1 commit (433c9b4)

**Deliverable**: ✅ agenda.line can be linked to event, post, or product.

---

### Phase 3: Product-Driven agenda.lines (Cancellation Period)

**Module**: `crearis_event_package`
**Rationale**: Extends `product.package.event.line` which already lives there

**Terminology** (German → English):
| German | English Field | Description |
|--------|---------------|-------------|
| Stornierungsfrist | `cancellation_period_days` | Days after first attendance (default: 10) |
| Stornierungsfrist-Datum | `cancellation_deadline_date` | Computed deadline per sale |
| Stornierungsfrist verstrichen | `is_cancellation_deadline_passed` | Boolean check |

**Goal**: Extend `product.package.event.line` to create agenda.lines

| # | Task | Module | Depends On | Estimate |
|---|------|--------|------------|----------|
| 3.1 | Add `agenda_line_id` M2O on `product.package.event.line` | crearis_event_package | Phase 2 | 0.5h |
| 3.2 | Override `create()` to auto-create agenda.line | crearis_event_package | 3.1 | 2h |
| 3.3 | Override `write()` to sync event_id changes | crearis_event_package | 3.2 | 1h |
| 3.4 | Add `cancellation_period_days` on `product.template` | crearis_event_package | Phase 2 | 0.5h |
| 3.5 | Add `cancellation_deadline_date` computed on `sale.order.line` | crearis_event_package | 3.4 | 1h |
| 3.6 | Add `is_cancellation_deadline_passed` computed | crearis_event_package | 3.5 | 0.5h |
| 3.7 | Create Cancellation Period milestone agenda.line on purchase | crearis_event_package | 3.2, 3.5 | 2h |

**Deliverable**: Module purchase creates agenda.lines with Cancellation Period tracking.

---

### Phase 4: Event-Driven agenda.lines ✅ MOSTLY COMPLETE (2026-02-02)

**Module**: `crearis` (base), `agenda_dasei` (defaults)
**Rationale**: Event registration extension is generic; Milestone defaults are DASEi-specific

**Status**: Core milestone infrastructure implemented in Phase 1. Remaining: registration-level agenda lines (deferred - not needed for event milestones).

**Goal**: ~~Extend `event.registration` for Offenes Programm~~ Event-level milestones

| # | Task | Module | Depends On | Estimate | Status |
|---|------|--------|------------|----------|--------|
| ~~4.1~~ | ~~Add `agenda_line_ids` O2M on `event.registration`~~ | — | — | — | ❌ Deferred |
| ~~4.2~~ | ~~Override `create()` to auto-create agenda.line for direct registration~~ | — | — | — | ❌ Deferred |
| 4.3 | Add `milestone_days_before` on `event.type` | crearis | Phase 2 | 0.5h | ✅ Done |
| 4.4 | Add computed milestone trigger date on `event.event` | crearis | 4.3 | 1h | ✅ Done |
| 4.5 | Create Milestone agenda.line on event create | crearis | 4.4 | 2h | ✅ Done |
| 4.6 | ~~Extend `event.mail` with `interval_type='before_milestone'`~~ | — | — | — | ❌ Not needed |
| 4.7 | Add `use_milestones` boolean on domain-code (default=False) | crearis | 4.3 | 0.5h | ✅ Done |
| 4.8 | Set `use_milestones=True` + defaults for DASEi | agenda_dasei | 4.7 | 0.5h | ✅ Done |

**Note on 4.1-4.2**: Event milestones are on `event.event`, not per-registration. For product/post providers, individual agenda.lines will be created at sale/post level (Phase 3). Meeting lines (`type='meeting'`) can be attached to any provider for individual/small-group sessions.

**Deliverable**: ✅ Event creation generates milestone agenda.lines (opt-in per domain).

---

### Phase 4B: German Customer Journeys (Documentation)

**Module**: Documentation only (`_meta/Whitepaper/`)
**Rationale**: Before implementing crearis_milestones, document complete customer journeys with German text

**Goal**: Create detailed journey documents with example interactions (Du/Ihr tone)

| # | Task | Location | Depends On | Estimate |
|---|------|----------|------------|----------|
| 4B.1 | Create master doc: `journey_karo_first_contact.md` | Whitepaper | — | 1.5h |
| 4B.2 | Create master doc: `journey_ida_basistag_to_module.md` | Whitepaper | — | 1.5h |
| 4B.3 | Create master doc: `journey_jolanda_full_grundlagenbildung.md` | Whitepaper | — | 2h |
| 4B.4 | Create master doc: `journey_selma_issue_driver.md` | Whitepaper | — | 1.5h |

**Personas**:
| Name | Journey | Description |
|------|---------|-------------|
| **Karo** | First contact → INFO-Teaser | Discovery, not yet committed |
| **Ida** | Basistag → Module A | Entry via taster day |
| **Jolanda** | Module A → full Grundlagenbildung | Long-term A,B,C,D path |
| **Selma** | Issue-driver | 41, Bamberg, problem-focused entry |

**Deliverable**: 4 journey master docs with German example interactions, email texts, portal views.

---

### Phase 4A: crearis_milestones Module (Gate Business Logic) ✅ IMPLEMENTED

**Module**: `crearis_milestones` (NEW)
**Status**: ✅ All tasks implemented (2026-02-02 afternoon)
**Rationale**: Separates enhanced milestone workflow from core agenda.line model
**Dependencies**: `agenda_dasei` will depend on `crearis_milestones` (not the other way around)

**Architecture Reference**: [architecture_milestones_and_actions.md](../_meta/Whitepaper/architecture_milestones_and_actions.md)
- Section 10: Blocker Pattern
- Section "Für Anwender": UI mockups and terminology

**Key Terminology** (from architecture doc):
| Term | Model | Description |
|------|-------|-------------|
| **Meilenstein** | `agenda.line` (type='milestone') | Event-level decision point |
| **Check** | `event.registration` + milestone fields | Participant-level within milestone |

**Goal**: Implement gate pattern business logic for milestone transitions

| # | Task | Module | Depends On | Estimate | Status |
|---|------|--------|------------|----------|--------|
| 4A.1 | Create `crearis_milestones` module scaffold | crearis_milestones | Phase 4 | 0.5h | ✅ Done |
| 4A.2 | Create English `mail.template` records for 3 milestone types | crearis_milestones | 4A.1 | 2h | ✅ Done |
| 4A.3 | Add German (de) translations for templates | crearis_milestones | 4A.2 | 1h | 🔜 Next |
| 4A.4 | Add Czech (cz) translations for templates | crearis_milestones | 4A.2 | 1h | 🔜 Next |
| 4A.5 | Implement `action_confirm_and_send()` business logic | crearis_milestones | 4A.2 | 2h | ✅ Done |
| 4A.6 | Implement `action_flag_issue()` method | crearis_milestones | 4A.1 | 1h | ✅ Done |
| 4A.7 | Implement `_maybe_advance_event_stage()` | crearis_milestones | 4A.5 | 2h | ⏸️ Deferred |
| 4A.8 | Add activity creation to cron (when gate_state → ready) | crearis_milestones | 4A.1 | 1h | ✅ Done |
| 4A.9 | Add "Confirm & Send" / "Flag Issue" buttons to views | crearis_milestones | 4A.5, 4A.6 | 1h | ✅ Done |
| 4A.10 | Create "Milestones Ready" dashboard/action | crearis_milestones | 4A.8 | 1.5h | ✅ Done |

**Check-Level Implementation** (UI from architecture doc Section "Für Anwender") ✅ IMPLEMENTED:

| # | Task | Module | Depends On | Estimate | Status |
|---|------|--------|------------|----------|--------|
| 4A.11 | Add `check_state` field on `event.registration` | crearis_milestones | 4A.1 | 0.5h | ✅ Done |
| 4A.12 | Add `check_comment` field on `event.registration` | crearis_milestones | 4A.11 | 0.5h | ✅ Done |
| 4A.13 | Add `has_blockers` computed on registration | crearis_milestones | 4A.11, 6A.4 | 1h | ✅ Done |
| 4A.14 | Create Controlling tree view (registrations grouped by event) | crearis_milestones | 4A.11 | 2h | ✅ Done |
| 4A.15 | Add BEREIT/TRIAGE sections via domain filters | crearis_milestones | 4A.14 | 1h | ✅ Done |
| 4A.16 | Add bulk "Alle bestätigen" server action | crearis_milestones | 4A.14 | 1h | ✅ Done |
| 4A.17 | Add milestone summary line per event group | crearis_milestones | 4A.14 | 1.5h | ⏸️ Deferred |

**View Implementation Pattern** (Odoo-native):

```xml
<!-- Controlling: Registration list grouped by event (=milestone) -->
<record id="view_registration_controlling_tree" model="ir.ui.view">
    <field name="model">event.registration</field>
    <field name="arch" type="xml">
        <tree default_group_by="event_id">
            <field name="event_id" invisible="1"/>
            <field name="partner_id"/>
            <field name="check_state" widget="badge"/>
            <field name="check_comment" optional="show"/>
            <field name="has_blockers" invisible="1"/>
            <button name="action_confirm_check" type="object" 
                    string="✓" attrs="{'invisible': [('has_blockers', '=', True)]}"/>
            <button name="action_show_blockers" type="object"
                    string="⚠️" attrs="{'invisible': [('has_blockers', '=', False)]}"/>
        </tree>
    </field>
</record>

<!-- Filters for BEREIT / TRIAGE -->
<filter name="bereit" string="✓ Bereit" 
        domain="[('check_state', '=', 'ready'), ('has_blockers', '=', False)]"/>
<filter name="triage" string="⚠️ Triage" 
        domain="['|', ('check_state', '=', 'issue'), ('has_blockers', '=', True)]"/>
```

**Dashboard Header** (custom widget or action with context):
```python
# In action definition
'context': {
    'search_default_group_by_event': True,
    'search_default_bereit': True,  # Default to BEREIT filter
}
```

**Template Language Strategy**:
- English base templates in `crearis_milestones/data/mail_template_data.xml`
- German/Czech as Odoo translations (`.po` files or inline `<field name="body_html" lang="de">...</field>`)
- `agenda_dasei` depends on `crearis_milestones` and can override templates if needed

**Email Tone**: Du/Ihr pattern (individual reader = Du, group references = Ihr)

**Deliverable**: Full gate workflow — cron triggers ready state, human confirms via button, email sent, stage advances.

---

### Phase 5: Template System

**Module**: `crearis` (template engine), `agenda_dasei` (DASEi templates)
**Rationale**: Template engine is generic; DASEi schedule patterns are specific

**Goal**: Event types generate agenda.lines from schedule templates

| # | Task | Module | Depends On | Estimate |
|---|------|--------|------------|----------|
| 5.1 | Add `schedule_template` JSONB on `event.type` | crearis | Phase 1 | 1h |
| 5.2 | Implement block date resolution algorithm | crearis | 5.1 | 3h |
| 5.3 | Override `event.event.create()` to generate session lines | crearis | 5.2 | 2h |
| 5.4 | Add "Regenerate from Template" action button | crearis | 5.3 | 1h |
| 5.5 | Add "Unlock for Editing" action (sets locked_edits=False) | crearis | 5.3 | 0.5h |
| 5.6 | [PLACEHOLDER] Event type hierarchy inheritance | crearis | 5.1 | TBD |
| 5.7 | **[NEW]** Define Grundlagenkurs schedule template (Fri+Sat+Sun pattern) | agenda_dasei | 5.1 | 1h |

**Deliverable**: Creating event from type auto-generates session agenda.lines.

---

### Phase 6: CRM Workflow (Unresolved Slots)

**Module**: `crearis_event_package` (workflow), `agenda_dasei` (German templates)
**Rationale**: Unresolved slots are package-specific; email content is DASEi-specific

**Goal**: Help resolve `event_id=False` package lines

| # | Task | Module | Depends On | Estimate |
|---|------|--------|------------|----------|
| 6.1 | Add color state field (resolved/pending/overdue/cancelled) | crearis_event_package | Phase 3 | 1h |
| 6.2 | Create "Ambiguous Agendas Report" wizard | crearis_event_package | 6.1 | 3h |
| 6.3 | Add `resolution_reminder_count` tracking | crearis_event_package | 6.1 | 0.5h |
| 6.4 | Create automated reminder cron job | crearis_event_package | 6.3 | 2h |
| 6.5 | Create "Resolution Queue" dashboard widget | crearis_event_package | 6.1 | 2h |
| 6.6 | Define reminder email template (German) | agenda_dasei | 6.4 | 1h |

**Deliverable**: CRM tools to track and resolve unresolved event selections.

---

### Phase 6A: Blocker Detection (Issue-Driver Support) ✅ IMPLEMENTED

**Module**: `crearis_milestones`
**Status**: ✅ All core tasks implemented (2026-02-02 afternoon)
**Rationale**: Blocker detection is milestone-specific, extends gate pattern

**Architecture References**:
- [architecture_milestones_and_actions.md](../_meta/Whitepaper/architecture_milestones_and_actions.md) Section 10: Blocker Pattern (code examples)
- [journey_selma_issue_driver.md](../_meta/Whitepaper/journey_selma_issue_driver.md): Full issue-driver scenario with all 3 blocker types

**Goal**: Detect and track blockers that prevent milestone completion

| # | Task | Module | Depends On | Estimate | Status |
|---|------|--------|------------|----------|--------|
| 6A.1 | Create `agenda.line.blocker` model (type, severity, resolved) | crearis_milestones | Phase 4 | 2h | ✅ Done |
| 6A.2 | Add `blocker_ids` One2many on registration (via partner) | crearis_milestones | 6A.1 | 0.5h | ✅ Done |
| 6A.3 | Add `has_blockers` computed field | crearis_milestones | 6A.2 | 0.5h | ✅ Done |
| 6A.4 | Implement `_check_blockers()` method | crearis_milestones | 6A.2 | 3h | ✅ Done |
| 6A.5 | Add payment_overdue detection (invoice lookup) | crearis_milestones | 6A.4 | 1h | ✅ Done |
| 6A.6 | Add event_unresolved detection (pending package selections) | crearis_milestones | 6A.4, Phase 3 | 1h | ⏸️ Needs Phase 3 |
| 6A.7 | Add confirmation_pending detection (overdue activities) | crearis_milestones | 6A.4 | 1h | ✅ Done |
| 6A.8 | Extend cron to call _check_blockers when setting ready | crearis_milestones | 6A.4, Phase 4 | 1h | ✅ Done |
| 6A.9 | Create blocker resolution action (sets resolved, resets gate) | crearis_milestones | 6A.1 | 1h | ✅ Done |
| 6A.10 | Add "Issues" filter to Controlling view | crearis_milestones | 6A.3, 4A.14 | 0.5h | ✅ Done |
| 6A.11 | Add blocker badges to tree/kanban (severity color-coded) | crearis_milestones | 6A.10 | 1h | ✅ Done |
| 6A.12 | Create activity on blocker creation (for coordinator) | crearis_milestones | 6A.8 | 1h | ⏸️ Deferred |

**Three Blocker Types** (from journey_selma_issue_driver.md):

| Type | Severity | Detection | Selma Example |
|------|----------|-----------|---------------|
| `payment_overdue` | High | Partner has overdue invoices | EUR 660, 3 invoices |
| `event_unresolved` | Medium | Pending event selections in package | A4 not chosen |
| `confirmation_pending` | Low | Overdue confirmation request activities | Employer letter 3x requested |

**Blocker → Check Integration**:

The `_check_blockers()` method is called on the **registration** (not agenda.line) because:
- Registration has `partner_id` → needed for invoice/activity lookup
- Registration has `event_id` → needed for package event lookup

```python
# On event.registration (in crearis_milestones)
def _check_blockers(self):
    """Check blockers for this registration's partner."""
    blockers = []
    partner = self.partner_id
    
    # 1. payment_overdue (see arch doc 10.3)
    # 2. event_unresolved (see arch doc 10.3)  
    # 3. confirmation_pending (see arch doc 10.3)
    
    return blockers
```

**View: TRIAGE Section** (from arch doc "Für Anwender"):

```xml
<!-- TRIAGE: 3 rows per blocked registration -->
<record id="view_registration_triage_form" model="ir.ui.view">
    <field name="model">event.registration</field>
    <field name="arch" type="xml">
        <form>
            <header>
                <button name="action_resolve_and_confirm" string="⚡ Freigeben"/>
                <button name="action_show_partner" string="📞 Kontaktieren"/>
            </header>
            <group>
                <field name="partner_id"/>
                <field name="event_id"/>
                <field name="check_comment"/>
            </group>
            <notebook>
                <page string="Blocker">
                    <field name="blocker_ids">
                        <tree>
                            <field name="blocker_type"/>
                            <field name="severity" widget="badge"/>
                            <field name="data_display"/>
                            <button name="action_resolve" string="✓"/>
                        </tree>
                    </field>
                </page>
            </notebook>
        </form>
    </field>
</record>
```

**Deliverable**: Gates can detect and refuse to open when blockers exist; coordinators see issues in Controlling view with actionable TRIAGE cards.

---

### Phase 7: Core Views (Events)

**Module**: `crearis`
**Rationale**: Event views are part of core agenda functionality

**Goal**: Event form shows agenda.lines

| # | Task | Module | Depends On | Estimate |
|---|------|--------|------------|----------|
| 7.1 | Create agenda.line tree view (for event form embed) | crearis | Phase 1 | 1h |
| 7.2 | Create agenda.line form view | crearis | 7.1 | 1h |
| 7.3 | Add "Schedule" tab to event form with agenda.lines | crearis | 7.1, 7.2 | 1h |
| 7.4 | Add Meldefrist milestone display in form header | crearis | Phase 4 | 1h |
| 7.5 | Add color-coding for session modes (online/venue icons) | crearis | 7.1 | 1h |
| 7.6 | Create "All Online Sessions" filtered view (Eleanora requirement) | crearis | 7.1 | 1h |

**Deliverable**: Event form with embedded agenda.line schedule view.

---

### Phase 8: Core Views (Products/Modules)

**Module**: `crearis_event_package`
**Rationale**: Product/package views extend existing package functionality

**Goal**: Product form shows module milestones

| # | Task | Module | Depends On | Estimate |
|---|------|--------|------------|----------|
| 8.1 | Add "Module Milestones" tab to product form | crearis_event_package | Phase 3 | 1h |
| 8.2 | Show Stornierungsfrist configuration | crearis_event_package | 8.1 | 0.5h |
| 8.3 | Create sale.order.line view with package event selections | crearis_event_package | Phase 3 | 2h |
| 8.4 | Add color-coded resolution status on package lines | crearis_event_package | Phase 6 | 1h |
| 8.5 | Link "Configure Events" button to configurator wizard | crearis_event_package | 8.3 | 0.5h |

**Deliverable**: Product/Module form with milestone and package configuration views.

---

### Phase 9: Investigation & Future

**Module**: TBD per investigation
**Rationale**: Future scope depends on findings

| # | Task | Module | Depends On | Estimate |
|---|------|--------|------------|----------|
| 9.1 | **Investigation: posts model as agenda.line provider** | TBD | — | TBD |
| 9.2 | [PLACEHOLDER] Post-driven info lines implementation | crearis | 9.1 | TBD |
| 9.3 | [PLACEHOLDER] Chatter → Action lines wizard | crearis | Phase 2 | TBD |
| 9.4 | [PLACEHOLDER] Attendance tracking model | crearis | Phase 4 | TBD |
| 9.5 | [PLACEHOLDER] Participant personal agenda view | crearis | Phase 7 | TBD |

---

## Priority Order

```
Phase 1 (Foundation)     ████████████████████  ✅ DONE       [crearis]
    ↓
Phase 2 (Providers)      ████████████████      ✅ DONE       [crearis]
    ↓
Phase 3 (Product)        ████████████████      MUST HAVE     [crearis_event_package]
    ↓
Phase 4 (Event)          ████████████████      ✅ DONE       [crearis + agenda_dasei]
    ↓
Phase 4A (Milestones)    ████████████████      ✅ DONE       [crearis_milestones]
    ↓
Phase 5 (Templates)      ████████████          SHOULD HAVE   [crearis + agenda_dasei]
    ↓
Phase 6 (CRM)            ████████████          SHOULD HAVE   [crearis_event_package + agenda_dasei]
    ↓
Phase 6A (Blockers)      ████████████          ✅ DONE       [crearis_milestones]
    ↓
Phase 7 (Event Views)    ████████              SHOULD HAVE   [crearis]
    ↓
Phase 8 (Product Views)  ████████              SHOULD HAVE   [crearis_event_package]
    ↓
Phase 9 (Investigation)  ████                  COULD HAVE    [TBD]
```

---

## Module Distribution Summary

| Module | Phases | % of Work | Status |
|--------|--------|-----------|--------|
| **crearis** | 1, 2, 4 (base), 5 (engine), 7, 9 (placeholders) | ~45% | ✅ Core done |
| **crearis_event_package** | 3, 6, 8 | ~20% | 🔜 Next |
| **crearis_milestones** | 4A (templates + Check fields), 6A (blockers) | ~25% | ✅ Implemented |
| **agenda_dasei** | 4 (defaults), 5 (templates), 6 (email) | ~10% | ✅ Defaults done |

### Dependency Flow

```
crearis (core agenda.line, gate_state)
    ├─► crearis_milestones (Check fields on registration, blockers, Controlling UI)
    │       └─► agenda_dasei (German/Czech translations)
    ├─► crearis_event_package (package-driven logic)
    │       └─► agenda_dasei (German email templates)
    └─► agenda_dasei (Meldefrist defaults, schedule templates)
```

### crearis_milestones Scope (NEW)

**Models extended**:
- `event.registration`: `check_state`, `check_comment`, `has_blockers`
- `agenda.line`: Business logic methods (already has `gate_state` from crearis)

**New models**:
- `agenda.line.blocker`: Blocker tracking per partner

**Views**:
- Controlling tree: Registrations grouped by event
- BEREIT filter: Ready to confirm
- TRIAGE filter: Has blockers
- Blocker resolution form

**Reference docs**:
- [architecture_milestones_and_actions.md](../_meta/Whitepaper/architecture_milestones_and_actions.md) — Full spec
- [journey_selma_issue_driver.md](../_meta/Whitepaper/journey_selma_issue_driver.md) — Issue-driver scenario

---

## Open Questions for Decision

| # | Question | Blocking Phase | Status |
|---|----------|----------------|--------|
| ~~Q1~~ | ~~Confirm 80% attendance threshold~~ | ~~Phase 9.4~~ | ⚡ DECIDED (D9) |
| ~~Q2~~ | ~~Event type hierarchy inheritance~~ | ~~Phase 5.6~~ | ⚡ DECIDED (C4) |
| Q3 | What triggers post→agenda.line creation? | Phase 9.2 | Before Phase 9 |
| ~~Q4~~ | ~~Meldefrist field location~~ | ~~Phase 4.3~~ | ⚡ DECIDED |
| ~~Q5~~ | ~~Email template infrastructure location~~ | ~~Phase 6.6~~ | ⚡ DECIDED |

---

### Q2 Detail: Event Type Hierarchy Inheritance ⚡ DECIDED (C4 Hybrid)

**Decision**: C4 Hybrid pattern confirmed.
- **Mandatory inherit** → pure `related` (e.g., `product_template_id`)
- **Optional override** → editable field with fallback compute (e.g., `template_units`)
- **Child-only** → regular field, no inheritance (e.g., `schedule_template`)

**Current State** (already in `crearis/models/event.py`):
```python
is_template_code = fields.Boolean(default=False)  # True = shortcode variant
template_parent_id = fields.Many2one('event.type', domain=[('is_template_code', '=', False)])
```

**Hierarchy Example**:
```
event.type: "A1 Kreisanimation" (abstract parent, is_template_code=False)
    │       Linked to: Module "Einstiege ins Theaterspiel" (product.template)
    │       schedule_template: None (abstract)
    │
    ├── event.type: "A1 Block" (is_template_code=True, template_parent_id → parent)
    │       schedule_template: DO-FR-SA-SO + Online pattern
    │
    └── event.type: "A1 Tageskurs" (is_template_code=True, template_parent_id → parent)
            schedule_template: SA 10:00-17:00 (single day)
```

**Question**: When creating an event from "A1 Block", what inherits from the parent?

| Field | Inherit from Parent? | Override in Child? | Notes |
|-------|---------------------|-------------------|-------|
| `product_template_id` | ✅ Yes | ❌ No | Module link comes from parent |
| `template_units` | ✅ Yes | ✅ Yes | Child can have reduced UE |
| `schedule_template` | ❌ No | ✅ Required | Child defines own schedule |
| `template_cimg` | ✅ Yes | ✅ Yes | Child can override image |
| `template_teasertext` | ✅ Yes | ✅ Yes | Child can override text |
| `meldefrist_days_before` | ✅ Yes | ✅ Yes | Usually same across variants |

**Options**:

| Option | Description | Complexity |
|--------|-------------|------------|
| **A. Explicit Copy** | On child create, copy inherited fields from parent | Simple, explicit |
| **B. Computed Fallback** | Child fields compute `self.value or parent.value` | DRY, but magic |
| **C. Related Fields** | Use `related='template_parent_id.field'` with store=True | Odoo-native, auto-sync |

---

#### Option C Variants with Data Examples

**Sample Data** (3 event.type records):

| id | name | is_template_code | template_parent_id | product_template_id | template_units | template_cimg |
|----|------|------------------|-------------------|---------------------|----------------|---------------|
| 1 | A1 Kreisanimation | False | — | 42 (Module A) | 22 | hero_a1.jpg |
| 2 | A1 Block | True | 1 | ? | ? | ? |
| 3 | A1 Tageskurs | True | 1 | ? | 10 | tageskurs.jpg |

---

**C1. Pure Related (no override possible)**

```python
# Child ALWAYS shows parent value, cannot override
product_template_id = fields.Many2one(
    related='template_parent_id.product_template_id',
    store=True, readonly=True
)
template_units = fields.Float(
    related='template_parent_id.template_units',
    store=True, readonly=True
)
```

**Resulting Data**:
| id | name | product_template_id | template_units | template_cimg |
|----|------|---------------------|----------------|---------------|
| 1 | A1 Kreisanimation | 42 | 22 | hero_a1.jpg |
| 2 | A1 Block | 42 *(from parent)* | 22 *(from parent)* | hero_a1.jpg *(from parent)* |
| 3 | A1 Tageskurs | 42 *(from parent)* | 22 *(WRONG! wanted 10)* | hero_a1.jpg *(WRONG! wanted tageskurs.jpg)* |

❌ **Problem**: Cannot override `template_units` or `template_cimg` on Tageskurs.

---

**C2. Related with Local Override Field**

```python
# Separate "own" field + computed "effective" field
template_units_own = fields.Float(string="Own Units (override)")
template_units = fields.Float(
    compute='_compute_template_units', store=True
)

@api.depends('template_units_own', 'template_parent_id.template_units')
def _compute_template_units(self):
    for rec in self:
        if rec.template_units_own:
            rec.template_units = rec.template_units_own
        elif rec.template_parent_id:
            rec.template_units = rec.template_parent_id.template_units
        else:
            rec.template_units = rec.template_units  # keep own
```

**Resulting Data**:
| id | name | template_units_own | template_units (computed) |
|----|------|--------------------|---------------------------|
| 1 | A1 Kreisanimation | 22 | 22 |
| 2 | A1 Block | — | 22 *(from parent)* |
| 3 | A1 Tageskurs | 10 | 10 *(own override)* |

✅ **Works**: Child inherits by default, can override with `_own` field.
⚠️ **Downside**: Two fields per inheritable value (verbose).

---

**C3. Computed with Fallback (single field, editable)**

```python
# Single field, editable, falls back to parent if empty
template_units = fields.Float()
template_units_effective = fields.Float(
    compute='_compute_effective_fields', store=True
)

@api.depends('template_units', 'template_parent_id.template_units')
def _compute_effective_fields(self):
    for rec in self:
        rec.template_units_effective = rec.template_units or (
            rec.template_parent_id.template_units if rec.template_parent_id else 0
        )
```

**Resulting Data**:
| id | name | template_units (editable) | template_units_effective |
|----|------|---------------------------|--------------------------|
| 1 | A1 Kreisanimation | 22 | 22 |
| 2 | A1 Block | 0 (empty) | 22 *(from parent)* |
| 3 | A1 Tageskurs | 10 | 10 |

✅ **Works**: Single editable field, separate computed for display/logic.
⚠️ **Downside**: Must use `_effective` in business logic, not raw field.

---

**C4. Hybrid: Related for mandatory, Computed for optional**

```python
# product_template_id: ALWAYS from parent (no override)
product_template_id = fields.Many2one(
    related='template_parent_id.product_template_id',
    store=True, readonly=True
)

# template_units: own field with fallback
template_units = fields.Float()

@api.depends('template_units', 'template_parent_id.template_units')
def _compute_display_units(self):
    for rec in self:
        rec.display_units = rec.template_units or (
            rec.template_parent_id.template_units if rec.template_parent_id else 0
        )
```

**Resulting Data**:
| id | name | product_template_id | template_units | display_units |
|----|------|---------------------|----------------|---------------|
| 1 | A1 Kreisanimation | 42 | 22 | 22 |
| 2 | A1 Block | 42 *(related)* | — | 22 *(fallback)* |
| 3 | A1 Tageskurs | 42 *(related)* | 10 | 10 |

✅ **Recommended**: Clean separation — mandatory fields use `related`, optional use fallback.

---

**Recommendation Summary**:

| Field Type | Pattern | Example Fields |
|------------|---------|----------------|
| **Mandatory inherit** | C1 (pure related) | `product_template_id` |
| **Optional override** | C4 (fallback) | `template_units`, `template_cimg`, `meldefrist_days_before` |
| **Child-only** | Regular field | `schedule_template` |

**Decision Needed**: Confirm Option C pattern, or choose A/B?

---

### Q4/Q5 Decisions (Confirmed)

**Pattern**: Infrastructure in generic module, Content in specific module.

- **Q4**: Field `meldefrist_days_before` in `crearis` + `use_meldefrist` boolean (default=False) at domain-code level. Enabled + default (60 days) set in `agenda_dasei` data files.
- **Q5**: Cron + mail.template base in `crearis_event_package`, German content in `agenda_dasei` data files.

---

## Source References

- [core_draft_agenda_lines.md](2026-01-31-core_draft_agenda_lines.md) — Architecture decisions
- [investigation_odoo_workflows.md](2026-01-31-investigation_odoo_workflows.md) — Odoo patterns + CRM workflow
- [imagination_scenario_a](2026-01-31-imagination_scenario_a_event_type_template.md) — Template system
- [imagination_scenario_f](2026-01-31-imagination_scenario_f_participant_journey.md) — Participant journey
- [imagination_scenario_g](2026-01-31-imagination_scenario_g_3month_cycle.md) — Batch processing
- [crearis_event_package](../crearis_event_package/) — Existing product.package.event.line
