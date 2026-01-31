# Action Plan: agenda.line Implementation

**Date**: 2026-01-31  
**Status**: Planning  
**Blocking**: Domain codes task (Monday)

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
4. **Post-event online**: Find first matching weekday **after** `date_end`

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

### Phase 1: Model Refactoring (Foundation)

**Module**: `crearis`
**Rationale**: `event.session.line` already lives in crearis, natural home for agenda.line

**Goal**: Rename and extend `event.session.line` → `agenda.line`

| # | Task | Module | Depends On | Estimate |
|---|------|--------|------------|----------|
| 1.1 | Create migration script for model rename | crearis | — | 2h |
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

### Phase 2: Provider Relations

**Module**: `crearis`
**Rationale**: Generic relation pattern belongs in core, not package-specific

**Goal**: Add multi-provider support (event, post, product)

| # | Task | Module | Depends On | Estimate |
|---|------|--------|------------|----------|
| 2.1 | Keep `event_id` as primary provider (existing) | crearis | Phase 1 | — |
| 2.2 | Add `post_id` Many2one field | crearis | Phase 1 | 0.5h |
| 2.3 | Add `product_id` Many2one field | crearis | Phase 1 | 0.5h |
| 2.4 | Add `provider_type` computed field | crearis | 2.1-2.3 | 1h |
| 2.5 | Add constraint: exactly one provider set | crearis | 2.4 | 0.5h |
| 2.6 | Update JSONB sync to use event_id provider | crearis | 2.1 | 1h |

**Deliverable**: agenda.line can be linked to event, post, or product.

---

### Phase 3: Product-Driven agenda.lines (Option A)

**Module**: `crearis_event_package`
**Rationale**: Extends `product.package.event.line` which already lives there

**Goal**: Extend `product.package.event.line` to create agenda.lines

| # | Task | Module | Depends On | Estimate |
|---|------|--------|------------|----------|
| 3.1 | Add `agenda_line_id` M2O on `product.package.event.line` | crearis_event_package | Phase 2 | 0.5h |
| 3.2 | Override `create()` to auto-create agenda.line | crearis_event_package | 3.1 | 2h |
| 3.3 | Override `write()` to sync event_id changes | crearis_event_package | 3.2 | 1h |
| 3.4 | Add `stornierungsfrist_days` on `product.template` | crearis_event_package | Phase 2 | 0.5h |
| 3.5 | Add `stornierungsfrist_date` computed on `sale.order.line` | crearis_event_package | 3.4 | 1h |
| 3.6 | Add `is_stornierungsfrist_passed` computed | crearis_event_package | 3.5 | 0.5h |
| 3.7 | Create Stornierungsfrist milestone agenda.line on purchase | crearis_event_package | 3.2, 3.5 | 2h |

**Deliverable**: Module purchase creates agenda.lines with Stornierungsfrist tracking.

---

### Phase 4: Event-Driven agenda.lines

**Module**: `crearis` (base), `agenda_dasei` (defaults)
**Rationale**: Event registration extension is generic; Meldefrist defaults are DASEi-specific

**Goal**: Extend `event.registration` for Offenes Programm

| # | Task | Module | Depends On | Estimate |
|---|------|--------|------------|----------|
| 4.1 | Add `agenda_line_ids` O2M on `event.registration` | crearis | Phase 2 | 0.5h |
| 4.2 | Override `create()` to auto-create agenda.line for direct registration | crearis | 4.1 | 2h |
| 4.3 | Add `meldefrist_days_before` on `event.type` | crearis | Phase 2 | 0.5h |
| 4.4 | Add `meldefrist_date` computed on `event.event` | crearis | 4.3 | 1h |
| 4.5 | Create Meldefrist milestone agenda.line on event create | crearis | 4.4 | 2h |
| 4.6 | Extend `event.mail` with `interval_type='before_meldefrist'` | crearis | 4.4 | 2h |
| 4.7 | Add `use_meldefrist` boolean on domain-code (default=False) | crearis | 4.3 | 0.5h |
| 4.8 | Set `use_meldefrist=True` + `meldefrist_days_before=60` for DASEi | agenda_dasei | 4.7 | 0.5h |

**Deliverable**: Event registration creates agenda.line with Meldefrist tracking (opt-in per domain).

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
Phase 1 (Foundation)     ████████████████████  MUST HAVE     [crearis]
    ↓
Phase 2 (Providers)      ████████████████      MUST HAVE     [crearis]
    ↓
Phase 3 (Product)        ████████████████      MUST HAVE     [crearis_event_package]
    ↓
Phase 4 (Event)          ████████████████      MUST HAVE     [crearis + agenda_dasei]
    ↓
Phase 5 (Templates)      ████████████          SHOULD HAVE   [crearis + agenda_dasei]
    ↓
Phase 6 (CRM)            ████████████          SHOULD HAVE   [crearis_event_package + agenda_dasei]
    ↓
Phase 7 (Event Views)    ████████              SHOULD HAVE   [crearis]
    ↓
Phase 8 (Product Views)  ████████              SHOULD HAVE   [crearis_event_package]
    ↓
Phase 9 (Investigation)  ████                  COULD HAVE    [TBD]
```

---

## Module Distribution Summary

| Module | Phases | % of Work |
|--------|--------|-----------|
| **crearis** | 1, 2, 4 (base), 5 (engine), 7, 9 (placeholders) | ~60% |
| **crearis_event_package** | 3, 6, 8 | ~30% |
| **agenda_dasei** | 4 (defaults), 5 (templates), 6 (email) | ~10% |

### Dependency Flow

```
crearis (core agenda.line)
    ├─► crearis_event_package (package-driven logic)
    │       └─► agenda_dasei (German email templates)
    └─► agenda_dasei (Meldefrist defaults, schedule templates)
```

---

## Open Questions for Decision

| # | Question | Blocking Phase | Status |
|---|----------|----------------|--------|
| ~~Q1~~ | ~~Confirm 80% attendance threshold~~ | ~~Phase 9.4~~ | ⚡ DECIDED (D9) |
| Q2 | How to handle event type hierarchy inheritance? | Phase 5.6 | Before Phase 5 |
| Q3 | What triggers post→agenda.line creation? | Phase 9.2 | Before Phase 9 |
| ~~Q4~~ | ~~Meldefrist field location~~ | ~~Phase 4.3~~ | ⚡ DECIDED |
| ~~Q5~~ | ~~Email template infrastructure location~~ | ~~Phase 6.6~~ | ⚡ DECIDED |

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
