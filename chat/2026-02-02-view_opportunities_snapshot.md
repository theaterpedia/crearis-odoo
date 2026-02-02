# View Opportunities Snapshot

**Date**: 2026-02-02 (evening)  
**Status**: Post Phase 5+7+8 Implementation  
**Modules Tested**: crearis v16.0.1.4.0, crearis_event_package v16.0.1.1.0  
**Updated**: Cross-checked against origin documents (additions, details, origin, dayprompt)

---

## Views Implemented Today

### Phase 5: Template System
| View | Model | Type | Description |
|------|-------|------|-------------|
| Schedule Template in Event Type | `event.type` | Form extension | `schedule_template` JSONB + `schedule_template_note` |
| Regenerate from Template button | `event.event` | Action button | `action_regenerate_from_template()` |
| Unlock for Editing button | `event.event` | Action button | `action_unlock_for_editing()` |

### Phase 7: Event Views (already existed, enhanced)
| View | Model | Type | Description |
|------|-------|------|-------------|
| Online Sessions tree | `event.event` | List | `has_online_sessions`, `online_hours`, `venue_hours` |
| Schedule Tab in Event Form | `event.event` | Tab | Agenda lines with parse + template actions |
| Agenda Line Tree | `agenda.line` | List | All types, modes, gate states |
| Agenda Line Form | `agenda.line` | Form | Provider, schedule, milestone details |
| Agenda Line Calendar | `agenda.line` | Calendar | Date-based planning view |
| Online Sessions action | `agenda.line` | Action | Filtered by mode=online |
| Sessions by Venue action | `agenda.line` | Action | Grouped by address_id |
| Milestones Ready action | `agenda.line` | Action | Filtered by gate_state=ready |

### Phase 8: Product Views (enhanced today)
| View | Model | Type | Description |
|------|-------|------|-------------|
| Event Package Tab | `product.template` | Tab | Cancellation, milestones, requirements |
| Package Event Line Tree | `product.package.event.line` | List | State, attendance tracking |
| Package Event Line Form | `product.package.event.line` | Form | Full workflow with buttons |
| Sale Order Line Form | `sale.order.line` | Form | **NEW** Milestone tracking, completion status |

---

## Remaining View Opportunities

### A. Agenda Line Model (`agenda.line`)

| # | View | Purpose | Complexity | Notes |
|---|------|---------|------------|-------|
| A1 | **Kanban by Gate State** | Visual milestone workflow | Medium | 4 columns: pending → ready → sent / issue |
| A2 | **Product Milestone Tree** | Milestones linked to products | Low | Filter: `provider_type='product'` |
| A3 | **Customer Agenda View** | Partner's personal timeline | Medium | All agenda.lines for one partner_id |
| A4 | **Pivot: Hours by Venue** | Booking analysis | Low | Measure: duration_h, venue grouped |
| A5 | **Graph: Sessions/Month** | Trend visualization | Low | Date:month x count |

#### A1 Enhanced Filters (from origin docs)

| Filter | Domain | Source |
|--------|--------|--------|
| `My Lines` | `[('user_id', '=', uid)]` | origin.md: "only my lines" |
| `Next 3 Days` | `[('date', '<=', today+3)]` | origin.md: urgent items |
| `Next 14 Days` | `[('date', '<=', today+14)]` | origin.md: planning horizon |
| `Info Lines` | `[('type', '=', 'info')]` | origin.md: info-mail, announcements |
| `Milestones Only` | `[('type', '=', 'milestone')]` | additions.md: decision points |
| `1-3 Weeks Horizon` | `[('date', '>=', today+7), ('date', '<=', today+21)]` | additions.md: bi_weekly window |

#### A4 Enhanced Measures (from origin docs)

| Measure | Field | Source |
|---------|-------|--------|
| `Online Hours` | `duration_h where mode='online'` | origin.md: always itemized |
| `Venue Hours` | `duration_h where mode='venue'` | origin.md: can be blocked |
| `Block Days` | Count of consecutive venue dates | details.md: shows intensity |

**Row Grouping Options:** By `address_id` (venue), by `event_id`, by `date:week`

### B. Package Event Line (`product.package.event.line`)

| # | View | Purpose | Complexity | Notes |
|---|------|---------|------------|-------|
| B1 | **Kanban by State** | Visual selection workflow | Medium | 5 states: pending → selected → registered → attended |
| B2 | **Unresolved Events Dashboard** | CRM: event_id=False | High | Phase 6 CRM workflow |
| B3 | **By Event Type Tree** | Which events need selection | Low | Group by event_type_id |
| B4 | **Customer Package Progress** | All selections for partner | Medium | Tree grouped by sale_order_id |

#### B2 Enhanced Filters (from origin docs)

| Filter | Domain | Source |
|--------|--------|--------|
| `Unresolved` | `[('event_id', '=', False)]` | Original requirement |
| `Confirmation Phase` | Event milestone within 14 days | details.md: "7-14 days prior to milestone" |
| `My Customers` | `[('partner_id.user_id', '=', uid)]` | CRM ownership |

**New Insight:** Unresolved package events ARE part of confirmation phase — dashboard should show both unresolved selections AND lines where event's milestone is within 14 days but registration not yet confirmed.

### C. Sale Order Line (`sale.order.line`)

| # | View | Purpose | Complexity | Notes |
|---|------|---------|------------|-------|
| C1 | **Package Lines Dashboard** | All event packages sold | Low | Filter: is_event_package=True |
| C2 | **Cancellation Period Tracker** | Lines in cancellation window | Medium | Filter: cancellation_state='in_period' |
| C3 | **Completion Tracker** | Packages near completion | Low | Filter: is_completed=False + high attendance |

#### C2 Enhanced Filters (from origin docs)

| Filter | Domain | Source |
|--------|--------|--------|
| `In Cancellation Period` | `[('cancellation_state', '=', 'in_period')]` | Original |
| `Needs Reverification` | 7 days before first_attendance + milestone | additions.md: "reverification-link 7 days before" |
| `Period Ending Soon` | `[('cancellation_deadline', '<=', today+3)]` | Urgent items |

**New Insight:** Cancellation period overlaps with "frontrunner" logic — tracker should show lines needing reverification (7 days before milestone).

### D. Event Type (`event.type`)

| # | View | Purpose | Complexity | Notes |
|---|------|---------|------------|-------|
| D1 | **Template Hierarchy Tree** | Parent/child visualization | Medium | Tree with parent_id folding |
| D2 | **Template Codes Kanban** | Quick template overview | Low | Cards showing schedule_template_note |

### E. Event Event (`event.event`)

| # | View | Purpose | Complexity | Notes |
|---|------|---------|------------|-------|
| E1 | **Events with Milestones** | milestone-enabled events | Low | Filter: use_milestones=True |
| E2 | **Milestone Status Column** | Add gate_state summary | Low | Inherit tree, add computed field |

#### E2 Enhanced: `current_milestone_key` Computed Field

From details.md, the column should show the **current milestone type** based on stage:

| Stage | Current Milestone | Computed Logic |
|-------|-------------------|----------------|
| `draft` | `deadline` (Meldefrist) | Waiting for confirmation gate |
| `confirmed` | `info_mail` | Waiting for info-mail send |
| `released` | `wrap_up` | In hot phase, wrap-up pending |
| `completed` | — | All milestones passed |

**New Field:** `current_milestone_key` on `event.event` (computed from stage_id.sysreg)

### F. Cross-Model Dashboards

| # | View | Purpose | Complexity | Notes |
|---|------|---------|------------|-------|
| F1 | **Coordinator Dashboard** | Milestones ready + issues | High | Multi-model with graphs |
| F2 | **Customer Journey View** | Timeline of partner's items | High | agenda.lines + registrations |
| F3 | **Resolution Queue** | Unresolved package events | Medium | Phase 6 CRM requirement |

#### F1 Enhanced: 4-Section Layout (from origin docs)

| Section | Content | Filter | Source |
|---------|---------|--------|--------|
| **MILESTONES** | Events with milestone in 1-3 weeks | `type='milestone', date in [+7, +21]` | additions.md |
| **INFO-MAIL** | Events needing info-mail (10-30 days before) | `milestone_key='info_mail', gate_state='ready'` | details.md |
| **HOT PHASE** | Released events (stage=released) | `event.stage_id.sysreg=4096` | details.md |
| **WRAP-UP** | Completed events awaiting wrap-up | `milestone_key='wrap_up', gate_state='ready'` | details.md |

**New Field:** `forced_controlling` boolean on `event.event` to manually flag events for dashboard inclusion (from additions.md: "events with flag 'forced controlling' activated")

---

## Decision Matrix: Roles × Views

### Role Definitions

| Role | German | Description |
|------|--------|-------------|
| **Coordinator** | Koordinator:in | Manages events, milestones, registrations |
| **Educator** | Dozent:in | Teaches sessions, needs schedule overview |
| **Admin** | Verwaltung | Handles sales, invoices, CRM |
| **Customer** | Teilnehmer:in | Views own agenda, makes selections |
| **Manager** | Leitung | Reports, analytics, oversight |

### Scenario Definitions

| Code | Scenario | Description |
|------|----------|-------------|
| **S1** | Daily Ops | Regular daily operations |
| **S2** | Milestone Check | Processing milestone deadlines |
| **S3** | Event Planning | Setting up new events |
| **S4** | Customer Support | Helping customers with bookings |
| **S5** | Reporting | Periodic analysis and reports |
| **S6** | CRM Follow-up | Resolving unfinished selections |

---

### Decision Matrix

| View | Coordinator | Educator | Admin | Customer | Manager | Primary Scenario |
|------|:-----------:|:--------:|:-----:|:--------:|:-------:|-----------------|
| **A1** Kanban by Gate | ★★★ | ★ | ★★ | — | ★★ | S2 Milestone |
| **A2** Product Milestone Tree | ★★★ | — | ★★ | — | ★ | S2 Milestone |
| **A3** Customer Agenda | ★★ | ★ | ★★ | ★★★ | — | S4 Support |
| **A4** Pivot Hours/Venue | ★★ | ★★★ | — | — | ★★★ | S5 Reporting |
| **A5** Graph Sessions/Month | ★ | ★★ | — | — | ★★★ | S5 Reporting |
| **B1** Kanban Selection | ★★★ | — | ★★ | ★★ | — | S1 Daily |
| **B2** Unresolved Dashboard | ★★★ | — | ★★★ | — | ★★ | S6 CRM |
| **B3** By Event Type | ★★ | ★ | ★ | — | — | S3 Planning |
| **B4** Customer Progress | ★★★ | — | ★★ | ★★★ | — | S4 Support |
| **C1** Package Lines | ★★ | — | ★★★ | — | ★★ | S5 Reporting |
| **C2** Cancellation Tracker | ★★★ | — | ★★★ | — | ★★ | S1 Daily |
| **C3** Completion Tracker | ★★★ | — | ★★ | — | ★★ | S1 Daily |
| **D1** Template Hierarchy | ★★ | ★ | — | — | ★ | S3 Planning |
| **D2** Template Cards | ★★ | ★★ | — | — | — | S3 Planning |
| **E1** Events w/ Milestones | ★★★ | ★ | ★ | — | ★★ | S2 Milestone |
| **E2** Milestone Status Col | ★★★ | ★ | ★ | — | ★★ | S1 Daily |
| **F1** Coordinator Dashboard | ★★★ | — | ★★ | — | ★★★ | S1+S2 |
| **F2** Customer Journey | ★★ | — | ★★ | ★★★ | — | S4 Support |
| **F3** Resolution Queue | ★★★ | — | ★★★ | — | ★★ | S6 CRM |

**Legend**: ★★★ = Critical, ★★ = Useful, ★ = Nice-to-have, — = Not relevant

---

### Priority Recommendations

**Tier 1: MUST HAVE (implement next)**
| View | Role Benefit | Effort |
|------|--------------|--------|
| A1 Kanban by Gate | Coordinator visual workflow | Medium |
| B2 Unresolved Dashboard | CRM workflow (Phase 6) | High |
| C2 Cancellation Tracker | Admin daily ops | Low |
| F1 Coordinator Dashboard | Multi-role visibility | High |

**Tier 2: SHOULD HAVE**
| View | Role Benefit | Effort |
|------|--------------|--------|
| A3 Customer Agenda | Customer + Support | Medium |
| B1 Kanban Selection | Coordinator workflow | Medium |
| B4 Customer Progress | Support + Customer | Medium |
| E2 Milestone Status Col | All roles daily view | Low |

**Tier 3: COULD HAVE**
| View | Role Benefit | Effort |
|------|--------------|--------|
| A4 Pivot Hours/Venue | Educator + Manager | Low |
| A5 Graph Sessions/Month | Manager reporting | Low |
| D1 Template Hierarchy | Planning clarity | Medium |
| F2 Customer Journey | Premium support | High |

---

## Implementation Notes

### Quick Wins (Low Effort, High Value)
1. **C2 Cancellation Tracker** — Simple filter action
2. **E2 Milestone Status Column** — Computed field + inherit
3. **A4 Pivot Hours/Venue** — Standard pivot view

### Requires Phase 6 (CRM Workflow)
- B2 Unresolved Dashboard
- F3 Resolution Queue

### Requires Portal Extension (Customer Views)
- A3 Customer Agenda (portal template)
- B4 Customer Progress (portal template)
- F2 Customer Journey (full portal redesign)

---

## Commit Reference

**Current**: `d3471b4` (Phase 3 complete)  
**Pending**: Phase 5+7+8 changes (not yet committed)

Files changed:
- `crearis/models/event.py` — schedule_template fields + generation methods
- `crearis/views/event_type_views.xml` — Schedule Template group
- `crearis/views/event_schedule_views.xml` — Template action buttons
- `crearis/__manifest__.py` — Version 16.0.1.4.0
- `crearis_event_package/views/sale_order_views.xml` — Sale line form + milestone view

---

## New Fields/Model Changes Discovered

From cross-checking origin documents, these additions are needed:

### New `milestone_key` Values

The "hot phase" requires 3 additional milestone keys (from details.md):

```python
milestone_key = fields.Selection([
    ('activation', 'Activation'),
    ('deadline', 'Deadline'),        # Meldefrist
    ('completion', 'Completion'),
    ('cancellation', 'Cancellation Period'),
    # NEW from details.md "3 interactions":
    ('info_mail', 'Info Mail'),      # 10-30 days before event
    ('opening', 'Opening Reminder'), # 1-3 days before event
    ('wrap_up', 'Wrap-Up'),          # 1-7 days after event
])
```

### New Fields on `event.event`

| Field | Type | Purpose | Source |
|-------|------|---------|--------|
| `current_milestone_key` | Computed Selection | Shows which milestone is current based on stage | details.md |
| `forced_controlling` | Boolean | Manual flag for dashboard inclusion | additions.md |

### Hot Phase Definition (from details.md)

> "The 'hot' phase typically only spans 3-5 weeks, it spans from 2-3 before the date_begin of an event until 1 week after date_end."

Stage transitions with offsets:
- `-14 days after 'milestone'` → event advances to `confirmed`
- `-14 days to date_begin` → event advances to `released` (current)
- `+7 days after date_end` → event advances to `completed`

### bi_weekly Controlling (from additions.md)

When `use_milestones=True`:
- Creates bi_weekly controlling-session
- Gathers events with milestone/info-mail/wrap-up within 1-3 weeks
- Plus events with `forced_controlling=True`
