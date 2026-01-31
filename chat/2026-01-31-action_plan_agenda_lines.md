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

### D8. Template Inheritance 🔶 NEEDS DETAIL

| Question | Status |
|----------|--------|
| How do event types inherit schedule templates? | Conceptually decided, needs technical spec |
| Block date resolution algorithm? | Designed in imagination_scenario_a, needs implementation |

**Placeholder**: Technical spec for template inheritance in Phase 3.

---

### D9. Attendance Tracking 🔶 NEEDS DETAIL

| Question | Status |
|----------|--------|
| How to mark sessions completed? | Conceptually decided (attendance-based), needs model |
| Threshold for "completed" vs "partial"? | 80% proposed, needs confirmation |

**Placeholder**: `agenda.line.attendance` model in Phase 4.

---

### D10. Posts as Provider 🔴 INVESTIGATION NEEDED

| Question | Status |
|----------|--------|
| How do blog.post records link to agenda.lines? | Not investigated |
| What triggers post→agenda.line creation? | Unknown |

**Task**: Investigation needed on posts model (bottom of plan).

---

## Implementation Phases

### Phase 1: Model Refactoring (Foundation)

**Goal**: Rename and extend `event.session.line` → `agenda.line`

| # | Task | Depends On | Estimate |
|---|------|------------|----------|
| 1.1 | Create migration script for model rename | — | 2h |
| 1.2 | Update model file: `event_session_line.py` → `agenda_line.py` | 1.1 | 1h |
| 1.3 | Add `type` field with 5 types (session, meeting, milestone, info, action) | 1.2 | 1h |
| 1.4 | Add `mode` field (online/venue/individual/tbd) | 1.2 | 0.5h |
| 1.5 | Add `source` field (json/template/manual/chatter) | 1.2 | 0.5h |
| 1.6 | Add `locked_edits` boolean | 1.5 | 0.5h |
| 1.7 | Update all view references (`event_session_line` → `agenda_line`) | 1.2 | 2h |
| 1.8 | Update security rules (ir.model.access.csv) | 1.2 | 0.5h |
| 1.9 | Run tests, fix breakages | 1.7, 1.8 | 2h |

**Deliverable**: `agenda.line` model with backward-compatible fields.

---

### Phase 2: Provider Relations

**Goal**: Add multi-provider support (event, post, product)

| # | Task | Depends On | Estimate |
|---|------|------------|----------|
| 2.1 | Keep `event_id` as primary provider (existing) | Phase 1 | — |
| 2.2 | Add `post_id` Many2one field | Phase 1 | 0.5h |
| 2.3 | Add `product_id` Many2one field | Phase 1 | 0.5h |
| 2.4 | Add `provider_type` computed field | 2.1-2.3 | 1h |
| 2.5 | Add constraint: exactly one provider set | 2.4 | 0.5h |
| 2.6 | Update JSONB sync to use event_id provider | 2.1 | 1h |

**Deliverable**: agenda.line can be linked to event, post, or product.

---

### Phase 3: Product-Driven agenda.lines (Option A)

**Goal**: Extend `product.package.event.line` to create agenda.lines

| # | Task | Depends On | Estimate |
|---|------|------------|----------|
| 3.1 | Add `agenda_line_id` M2O on `product.package.event.line` | Phase 2 | 0.5h |
| 3.2 | Override `create()` to auto-create agenda.line | 3.1 | 2h |
| 3.3 | Override `write()` to sync event_id changes | 3.2 | 1h |
| 3.4 | Add `stornierungsfrist_days` on `product.template` | Phase 2 | 0.5h |
| 3.5 | Add `stornierungsfrist_date` computed on `sale.order.line` | 3.4 | 1h |
| 3.6 | Add `is_stornierungsfrist_passed` computed | 3.5 | 0.5h |
| 3.7 | Create Stornierungsfrist milestone agenda.line on purchase | 3.2, 3.5 | 2h |

**Deliverable**: Module purchase creates agenda.lines with Stornierungsfrist tracking.

---

### Phase 4: Event-Driven agenda.lines

**Goal**: Extend `event.registration` for Offenes Programm

| # | Task | Depends On | Estimate |
|---|------|------------|----------|
| 4.1 | Add `agenda_line_ids` O2M on `event.registration` | Phase 2 | 0.5h |
| 4.2 | Override `create()` to auto-create agenda.line for direct registration | 4.1 | 2h |
| 4.3 | Add `meldefrist_days_before` on `event.type` | Phase 2 | 0.5h |
| 4.4 | Add `meldefrist_date` computed on `event.event` | 4.3 | 1h |
| 4.5 | Create Meldefrist milestone agenda.line on event create | 4.4 | 2h |
| 4.6 | Extend `event.mail` with `interval_type='before_meldefrist'` | 4.4 | 2h |

**Deliverable**: Event registration creates agenda.line with Meldefrist tracking.

---

### Phase 5: Template System

**Goal**: Event types generate agenda.lines from schedule templates

| # | Task | Depends On | Estimate |
|---|------|------------|----------|
| 5.1 | Add `schedule_template` JSONB on `event.type` | Phase 1 | 1h |
| 5.2 | Implement block date resolution algorithm | 5.1 | 3h |
| 5.3 | Override `event.event.create()` to generate session lines | 5.2 | 2h |
| 5.4 | Add "Regenerate from Template" action button | 5.3 | 1h |
| 5.5 | Add "Unlock for Editing" action (sets locked_edits=False) | 5.3 | 0.5h |
| 5.6 | [PLACEHOLDER] Event type hierarchy inheritance | 5.1 | TBD |

**Deliverable**: Creating event from type auto-generates session agenda.lines.

---

### Phase 6: CRM Workflow (Unresolved Slots)

**Goal**: Help resolve `event_id=False` package lines

| # | Task | Depends On | Estimate |
|---|------|------------|----------|
| 6.1 | Add color state field (resolved/pending/overdue/cancelled) | Phase 3 | 1h |
| 6.2 | Create "Ambiguous Agendas Report" wizard | 6.1 | 3h |
| 6.3 | Add `resolution_reminder_count` tracking | 6.1 | 0.5h |
| 6.4 | Create automated reminder cron job | 6.3 | 2h |
| 6.5 | Create "Resolution Queue" dashboard widget | 6.1 | 2h |
| 6.6 | Define reminder email template | 6.4 | 1h |

**Deliverable**: CRM tools to track and resolve unresolved event selections.

---

### Phase 7: Core Views (Events)

**Goal**: Event form shows agenda.lines

| # | Task | Depends On | Estimate |
|---|------|------------|----------|
| 7.1 | Create agenda.line tree view (for event form embed) | Phase 1 | 1h |
| 7.2 | Create agenda.line form view | 7.1 | 1h |
| 7.3 | Add "Schedule" tab to event form with agenda.lines | 7.1, 7.2 | 1h |
| 7.4 | Add Meldefrist milestone display in form header | Phase 4 | 1h |
| 7.5 | Add color-coding for session modes (online/venue icons) | 7.1 | 1h |
| 7.6 | Create "All Online Sessions" filtered view (Eleanora requirement) | 7.1 | 1h |

**Deliverable**: Event form with embedded agenda.line schedule view.

---

### Phase 8: Core Views (Products/Modules)

**Goal**: Product form shows module milestones

| # | Task | Depends On | Estimate |
|---|------|------------|----------|
| 8.1 | Add "Module Milestones" tab to product form | Phase 3 | 1h |
| 8.2 | Show Stornierungsfrist configuration | 8.1 | 0.5h |
| 8.3 | Create sale.order.line view with package event selections | Phase 3 | 2h |
| 8.4 | Add color-coded resolution status on package lines | Phase 6 | 1h |
| 8.5 | Link "Configure Events" button to configurator wizard | 8.3 | 0.5h |

**Deliverable**: Product/Module form with milestone and package configuration views.

---

### Phase 9: Investigation & Future

| # | Task | Depends On | Estimate |
|---|------|------------|----------|
| 9.1 | **Investigation: posts model as agenda.line provider** | — | TBD |
| 9.2 | [PLACEHOLDER] Post-driven info lines implementation | 9.1 | TBD |
| 9.3 | [PLACEHOLDER] Chatter → Action lines wizard | Phase 2 | TBD |
| 9.4 | [PLACEHOLDER] Attendance tracking model | Phase 4 | TBD |
| 9.5 | [PLACEHOLDER] Participant personal agenda view | Phase 7 | TBD |

---

## Priority Order

```
Phase 1 (Foundation)     ████████████████████  MUST HAVE
    ↓
Phase 2 (Providers)      ████████████████      MUST HAVE
    ↓
Phase 3 (Product)        ████████████████      MUST HAVE (enables CRM)
    ↓
Phase 4 (Event)          ████████████████      MUST HAVE (enables Meldefrist)
    ↓
Phase 5 (Templates)      ████████████          SHOULD HAVE
    ↓
Phase 6 (CRM)            ████████████          SHOULD HAVE (retention critical)
    ↓
Phase 7 (Event Views)    ████████              SHOULD HAVE
    ↓
Phase 8 (Product Views)  ████████              SHOULD HAVE
    ↓
Phase 9 (Investigation)  ████                  COULD HAVE
```

---

## Open Questions for Decision

| # | Question | Blocking Phase | Deadline |
|---|----------|----------------|----------|
| Q1 | Confirm 80% attendance threshold for "completed" | Phase 9.4 | Later |
| Q2 | How to handle event type hierarchy inheritance? | Phase 5.6 | Before Phase 5 |
| Q3 | What triggers post→agenda.line creation? | Phase 9.2 | Before Phase 9 |

---

## Source References

- [core_draft_agenda_lines.md](2026-01-31-core_draft_agenda_lines.md) — Architecture decisions
- [investigation_odoo_workflows.md](2026-01-31-investigation_odoo_workflows.md) — Odoo patterns + CRM workflow
- [imagination_scenario_a](2026-01-31-imagination_scenario_a_event_type_template.md) — Template system
- [imagination_scenario_f](2026-01-31-imagination_scenario_f_participant_journey.md) — Participant journey
- [imagination_scenario_g](2026-01-31-imagination_scenario_g_3month_cycle.md) — Batch processing
- [crearis_event_package](../crearis_event_package/) — Existing product.package.event.line
