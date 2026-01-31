# Core Draft: agenda.line Architecture

**Date**: 2026-01-31  
**Stage**: draft  
**Target**: agenda_lines_architecture.md (Chapter 2)

---

## ==TASKS== research findings, open questions **Agenda Lines Specification**

- [x] #kw05 Research existing `event.session.line` model
- [x] #kw05 Battle-test against session-line research (2026-01-28)
- [ ] #kw05 Decide: rename vs extend model
- [ ] #kw05 Define provider relations (events, posts, products)
- [ ] #kw05 Sync direction: JSON → Table or bidirectional?
- [ ] #kw06 Template inheritance scenarios
- [ ] #kw06 Create imagination docs for 3 selected scenarios

---

## ==DEV== current state findings **Research Summary**

### Existing Model: `event.session.line`

**Location**: `crearis/models/event_session_line.py` (160 lines)

**Purpose** (from docstring):
> Lightweight session line model for schedule display and filtering.
> These records are synced from schedule_data.sessions[] JSONB.

**Current Fields**:
| Field | Type | Notes |
|-------|------|-------|
| `event_id` | Many2one | Required, cascade delete |
| `sequence` | Integer | Order within event |
| `day` | Char(3) | MON, TUE, etc. |
| `date` | Date | Indexed |
| `start` / `end` | Char(5) | HH:MM format |
| `duration_h` | Float | Hours |
| `type` | Selection | online/venue/individual/tbd |
| `location_hint` | Char | Parsed location name |
| `room` | Char | Room identifier |
| `notes` | Text | Additional notes |
| `conference_url` | Char | Video meeting URL |
| `conference_id` | Char | External meeting ID |
| `conference_provider` | Selection | msteams/zoom/jitsi/other |

**Related fields** (stored for filtering):
- `event_name`, `company_id`, `event_date_begin`, `address_id`, `event_type_id`, `user_id`

### Supporting Infrastructure

**`schedule_mixin.py`** (628 lines):
- Parses text schedules into JSONB (`schedule_data_v1` schema)
- German/English weekday codes
- Shortcodes: `_online_`, `_TANZEREI_`, `_VENUE:ROOM_`

**OCA `event.session`** (538 lines):
- Heavy model with own registrations
- Inherits `event.event` — NOT what we want
- We stay lightweight

---

## ==DEV== battle-test against prior research **Considerations & Warnings**

### ⚠️ CONSIDERATION 1: Naming Decision (from 2026-01-28 naming analysis)

The naming analysis concluded `event.session.line` is correct because:
- "Session" is natural language users use
- `.line` follows Odoo pattern for child records
- Distinguishes from heavy OCA `event.session`

**Warning**: Renaming to `agenda.line` breaks this alignment. However, the broader scope (meetings, milestones, info, actions) justifies it — these aren't "sessions".

**Decision factor**: If we keep only schedule-type lines → stay `event.session.line`. If we expand to 5 types → rename to `agenda.line`.

### ⚠️ CONSIDERATION 2: JSONB as Source (from 2026-01-28 revisiting_keep_it_simple)

The "keep it simple" analysis established:
> JSONB serves GraphQL directly, enables SharePoint write-back, flexible schema evolution

**Warning**: The proposed bidirectional sync (Option C) adds complexity. The original decision was:
- JSONB = source of truth
- `event.session.line` = display layer only (synced FROM JSONB)

**Recommendation**: Keep `source='json'` lines as **readonly**. Only `source='manual'|'chatter'` lines are editable. No reverse sync to JSONB.

### ⚠️ CONSIDERATION 3: Hybrid Event Problem (from 2026-01-28 research_event_tracks)

Key finding: ~50% of DASEi events are hybrid (online + venue sessions).

**Current architecture handles this** via `type` field (online/venue per session). The proposed `mode` field preserves this.

**Warning**: Don't lose the `location_hint` and `room` fields — they're essential for hybrid reporting ("which sessions are at Tanzerei?").

### ⚠️ CONSIDERATION 4: Eleanora's View Requirement

From triage doc:
> **Special view: "All online sessions" line-by-line**

This requires searchable records — JSONB alone can't do `WHERE type='online' AND date BETWEEN...`

**Confirmation**: The `agenda.line` table approach is correct for this use case.

### ⚠️ CONSIDERATION 5: Monthly Workflow Focus (from agenda_extended_core)

Key insight:
> The big focus of the system is a **monthly workflow**! Not 10-30 tasks per day, but >1 interaction per week.

**Warning**: Don't over-engineer agenda.lines for real-time tracking. They should support:
- Monthly newsletter aggregation (type='info')
- 3-monthly cycle checkpoints (type='milestone')
- Planning sessions (type='meeting')

**Not**: minute-by-minute task management.

### ⚠️ CONSIDERATION 6: 3-Tab UI Definition (from agenda_extended_core)

The UI defines 3 perspectives:
| Tab | Shows |
|-----|-------|
| **Agenda** | Timeline of future activities, infos, tasks, events |
| **Curriculum** | Portfolio view, A1-A14, B1-B14 progress per product |
| **Service/Contract** | Agreements, payments, opt-out dates |

**Warning**: `agenda.line` primarily serves the **Agenda tab**. The **Curriculum tab** needs different aggregation (by product milestone, not by date). Consider whether `type='milestone'` lines should be filterable by product.

### ⚠️ CONSIDERATION 7: Provider Scope (from chapter_agenda_model decisions)

Decided exclusions:
> ~~Companies~~ — They "have" agendas, not "are" agendas
> ~~Users/Partners~~ — They are actors, not providers

**Confirmation**: The 3 providers (event, post, product) are correct. Don't add `partner_id` as provider.

### ✅ VALIDATED: Conference Per Session (from implementation_scenarios)

Scenario B (JSONB-driven) was chosen:
> Conference URLs stored inside `schedule_data.sessions[]` JSONB

The current `event.session.line` already has `conference_url`, `conference_id`, `conference_provider`. This is correct and should be preserved in `agenda.line`.

---

## ==DRAFT== proposed architecture **Rename + Extend to agenda.line**

### 1. Model Rename

| Current | Proposed | Rationale |
|---------|----------|-----------|
| `event.session.line` | `agenda.line` | Distinguishes from OCA, reflects broader scope |

**Migration**: Rename model, update all references in views/controllers.

### 2. Extended Type Field

Current types only cover schedule entries. Expand for full agenda capability:

| Type | Mode | Description | Provider |
|------|------|-------------|----------|
| `session` | online/venue | In-presence slot (current default) | Events |
| `meeting` | online/venue | Outside event, prep/planning | Events, Posts |
| `milestone` | — | Status documentation, stats/checks | Events, Products |
| `info` | — | Email sent, portal news | Posts |
| `action` | — | Text, document, decision, Q&A | Any |

```python
type = fields.Selection([
    ('session', 'Session'),      # Was: online/venue/individual/tbd
    ('meeting', 'Meeting'),
    ('milestone', 'Milestone'),
    ('info', 'Info'),
    ('action', 'Action'),
], string='Type', default='session', required=True, index=True)

mode = fields.Selection([
    ('online', 'Online'),
    ('venue', 'Venue'),
    ('individual', 'Individual'),
    ('tbd', 'TBD'),
], string='Mode', help="For session/meeting types")
```

### 3. Provider Relations

**Design**: Multiple optional Many2one fields, exactly one should be set.

```python
# Providers (exactly one should be populated)
event_id = fields.Many2one('event.event', ondelete='cascade', index=True)
post_id = fields.Many2one('blog.post', ondelete='cascade', index=True)
product_id = fields.Many2one('product.template', ondelete='cascade', index=True)

# Computed provider reference
provider_type = fields.Selection([
    ('event', 'Event'),
    ('post', 'Blog Post'),
    ('product', 'Product'),
], compute='_compute_provider_type', store=True)

@api.depends('event_id', 'post_id', 'product_id')
def _compute_provider_type(self):
    for rec in self:
        if rec.event_id:
            rec.provider_type = 'event'
        elif rec.post_id:
            rec.provider_type = 'post'
        elif rec.product_id:
            rec.provider_type = 'product'
        else:
            rec.provider_type = False
```

### 4. Source of Truth Decision

**Options**:
| Option | Source | Table | Use Case |
|--------|--------|-------|----------|
| A | JSONB | Readonly | Text-based schedule entry |
| B | Table | Primary | UI-driven entry, chatter integration |
| C | Bidirectional | Both | Sync with `locked_edits` flag |

**Proposed: Option C (Bidirectional)**

```python
source = fields.Selection([
    ('json', 'From Schedule JSON'),
    ('manual', 'Manual Entry'),
    ('chatter', 'From Chatter'),
    ('template', 'From Template'),
], default='manual')

locked_edits = fields.Boolean(
    default=False,
    help="If True, record is controlled by source and should not be manually edited"
)
```

---

## ==DRAFT== template scenarios **How Templates Generate agenda.lines**

### Scenario A: Event Type Template

**Context**: Event types define default schedules. When creating an event from a type, agenda.lines are pre-populated.

**Hierarchy reminder**:
- COURSE: M18 Grundkurs Theaterpädagogik (full 2-year program)
- MODULE/PRODUCT: A = Einstiege ins Theaterspiel, B = Szenische Themenarbeit, etc.
- EVENT: A1 Kreisanimation, A2 Zwei-Kreise, etc. (each a separate event)
- SESSION LINES: Time slots within an event (DO 19:00, FR 09:00, etc.)

```
event.type (A1 Kreisanimation - Block)
    └── schedule_template (JSONB)
            └── default sessions: DO 19:00 - SO 15:00 + online

event.event (A1 Kreisanimation - München März 2026)
    └── agenda.line[] (5-6 records, source='template')
```

**Implementation**:
```python
class EventType(models.Model):
    _inherit = 'event.type'
    
    schedule_template = fields.Json(
        string='Schedule Template',
        help="Default sessions for events of this type"
    )

class EventEvent(models.Model):
    _inherit = 'event.event'
    
    def _create_from_type(self):
        """Override to generate agenda.lines from template."""
        super()._create_from_type()
        if self.event_type_id.schedule_template:
            self._generate_agenda_lines_from_template(
                self.event_type_id.schedule_template
            )
```

**Q: How does date resolution work?**
- Template has: `DO 19:00-21:00, FR 09:00-18:00, SA 09:00-18:00, SO 09:00-15:00` (weekdays + times)
- Event has: `date_begin = 2026-03-13` (Thursday)
- System resolves: Find consecutive DO-FR-SA-SO starting from date_begin

**Variant: Tageskurs** (single-day events, different unit count):
- Template has: `SA 10:00-17:00` (one day)
- Different event type, fewer teaching units per event

**Meldefrist (Event-level confirmation deadline)**:
```python
class EventType(models.Model):
    _inherit = 'event.type'
    
    meldefrist_days_before = fields.Integer(
        string='Meldefrist (days before start)',
        default=60,  # Typically 2-4 months before event
        help="Confirmation deadline offset from event date_begin"
    )

class EventEvent(models.Model):
    _inherit = 'event.event'
    
    meldefrist_date = fields.Date(
        compute='_compute_meldefrist_date',
        store=True,
        string='Confirmation Deadline'
    )
    
    @api.depends('date_begin', 'event_type_id.meldefrist_days_before')
    def _compute_meldefrist_date(self):
        for event in self:
            if event.date_begin and event.event_type_id.meldefrist_days_before:
                event.meldefrist_date = event.date_begin - timedelta(
                    days=event.event_type_id.meldefrist_days_before
                )
```

**Meldefrist creates agenda.line**:
- Type: `milestone`
- Name: "Meldefrist A1" (confirmation required)
- Date: computed from event.date_begin - offset
- Participants must confirm or opt-out before this date
- Ties into 3-month cycle batch processing (Scenario G)

---

### Scenario B: Product/Module Template (DASEi Modules A,B,C,D)

**Context**: Products represent modules (A = Einstiege ins Theaterspiel, B = Szenische Themenarbeit, etc.). They define **module-level milestones** that exist alongside event-level session lines.

**Key distinction from Event-level**:
| Level | Deadline Type | Description | Example |
|-------|---------------|-------------|--------|
| **Event** | Meldefrist | Confirmation deadline per event | "A1 Kreisanimation: confirm by Jan 15" (2-4 months before) |
| **Module** | Stornierungsfrist | Cancellation deadline for module purchase | "10 days after first event attendance" |

```
product.template (Einstiege ins Theaterspiel - Modul A)
    └── module_milestones (JSONB)
            └── Stornierungsfrist (cancellation deadline)
            └── consulting call, certificate, QM check

When participant buys Module A:
    └── Creates agenda.lines from module template:
        • milestone: "Stornierungsfrist" (10 days after first event)
        • milestone: "Beratungsgespräch" (consulting call)
        • milestone: "Modul A Zertifikat" (certificate)
        • milestone: "QM Rückmeldung" (quality feedback)
    └── PLUS: agenda.lines from each event they register for (A0, A1, A2...)
        • Including: Meldefrist per event (from event_type config)
```

**Stornierungsfrist Logic**:
```python
# Date is driven by event, but belongs to module
stornierungsfrist_date = first_event_attendance_date + timedelta(days=10)

# Before this date: Customer can cancel, loses only first Kursrate (EUR ~220)
# After this date: Full module fee applies, no cancellation
```
```

**Key insight**: Two sources of agenda.lines for participants:
1. **Module-level**: Stornierungsfrist, Certificate, consulting, QM — from product template
2. **Event-level**: Session times (DO 19:00, FR 09:00...) + Meldefrist — from event type template

**Two Critical Deadlines**:
| Deadline | Level | Drives | Consequence |
|----------|-------|--------|-------------|
| **Meldefrist** | Event | `event.date_begin - offset` | Must confirm attendance for each event |
| **Stornierungsfrist** | Module | `first_event_date + 10 days` | After this, module purchase is binding |

**Implementation**:
```python
class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    is_course_module = fields.Boolean('Is Course Module')
    module_milestones = fields.Json(
        string='Module Milestones',
        help="Module-level milestones (not event sessions)"
    )
    
    # Example milestones JSON for "Einstiege ins Theaterspiel" (Modul A):
    # [
    #   {"type": "meeting", "name": "Beratungsgespräch", "sequence": 50,
    #    "timing": "after_2_events", "duration_min": 30, "mode": "online"},
    #   {"type": "milestone", "name": "Modul A Zertifikat", "sequence": 90,
    #    "timing": "after_all_events"},
    #   {"type": "action", "name": "QM Rückmeldung Team", "sequence": 95,
    #    "timing": "after_all_events", "assigned_to": "team"}
    # ]
```

---

### Scenario C: Post-Driven Info Lines

**Context**: Blog posts (announcements, newsletters) create info-type agenda.lines for participants.

```
blog.post (Workshop Reminder: March Event)
    └── linked_events[] (M2M to events)
            └── On post publish → create agenda.line(type='info')
```

**Implementation**:
```python
class BlogPost(models.Model):
    _inherit = 'blog.post'
    
    linked_event_ids = fields.Many2many('event.event', string='Linked Events')
    
    def write(self, vals):
        res = super().write(vals)
        if 'is_published' in vals and vals['is_published']:
            self._create_info_agenda_lines()
        return res
    
    def _create_info_agenda_lines(self):
        for event in self.linked_event_ids:
            self.env['agenda.line'].create({
                'event_id': event.id,
                'post_id': self.id,
                'type': 'info',
                'name': self.name,
                'date': fields.Date.today(),
                'source': 'chatter',  # or 'auto'
            })
```

---

### Scenario D: Chatter → Action Lines

**Context**: Important chatter messages (decisions, documents, Q&A) become action-type agenda.lines.

```
event.event
    └── mail.message (Chatter: "Decision: we'll use Room B")
            └── User clicks "Add to Agenda"
                    └── agenda.line(type='action', source='chatter')
```

**Implementation**: Wizard or chatter action button
```python
class MessageToAgendaWizard(models.TransientModel):
    _name = 'message.to.agenda.wizard'
    
    message_id = fields.Many2one('mail.message', required=True)
    line_type = fields.Selection([
        ('action', 'Action/Decision'),
        ('info', 'Info'),
        ('milestone', 'Milestone'),
    ], default='action')
    
    def action_create_agenda_line(self):
        msg = self.message_id
        # Determine parent model
        model = msg.model
        res_id = msg.res_id
        
        vals = {
            'type': self.line_type,
            'name': msg.subject or msg.preview[:50],
            'notes': msg.body,
            'date': msg.date.date(),
            'source': 'chatter',
        }
        
        if model == 'event.event':
            vals['event_id'] = res_id
        elif model == 'blog.post':
            vals['post_id'] = res_id
        
        self.env['agenda.line'].create(vals)
```

---

### Scenario E: Event Package (Multiple Events)

**Context**: `crearis_event_package` groups events. Package-level agenda shows aggregated view.

```
crearis.event.package (Grundlagenkurs Komplett A+B+C+D)
    └── event_ids[] (4 events, one per module)
            └── Each event has own agenda.line[]
    └── package_agenda_line_ids (computed: all child events' lines)
```

**Implementation**:
```python
class CreariEventPackage(models.Model):
    _name = 'crearis.event.package'
    
    event_ids = fields.Many2many('event.event')
    
    agenda_line_ids = fields.One2many(
        'agenda.line',
        compute='_compute_agenda_lines',
        string='Package Agenda'
    )
    
    @api.depends('event_ids.agenda_line_ids')
    def _compute_agenda_lines(self):
        for pkg in self:
            pkg.agenda_line_ids = pkg.event_ids.mapped('agenda_line_ids')
```

---

### Scenario F: Participant Journey Milestones (NEW)

**Context**: From Ida's journey — the consulting call is 4 days away. Her agenda shows milestones she's completed (A1/A2, A4/A5) and upcoming decisions.

```
event.registration (Ida → Grundlagenkurs A München)
    └── agenda.line[] (participant-specific view)
            ├── session: A1/A2 Block ✓ completed
            ├── session: A4/A5 Block ✓ completed  
            ├── milestone: Protocol task assigned
            ├── meeting: Consulting call (in 4 days)
            └── action: "Read curriculum" (self-assigned)
```

**Key insight**: The participant sees a **filtered view** of the event's agenda.lines, plus their own personal actions/milestones.

**Implementation**:
```python
class EventRegistration(models.Model):
    _inherit = 'event.registration'
    
    personal_agenda_line_ids = fields.One2many(
        'agenda.line',
        'registration_id',
        string='Personal Agenda Items'
    )
    
    all_agenda_line_ids = fields.Many2many(
        'agenda.line',
        compute='_compute_all_agenda_lines',
        string='Full Agenda View'
    )
    
    @api.depends('event_id.agenda_line_ids', 'personal_agenda_line_ids')
    def _compute_all_agenda_lines(self):
        for reg in self:
            event_lines = reg.event_id.agenda_line_ids
            personal_lines = reg.personal_agenda_line_ids
            reg.all_agenda_line_ids = event_lines | personal_lines

# Extend agenda.line with optional registration link
class AgendaLine(models.Model):
    _inherit = 'agenda.line'
    
    registration_id = fields.Many2one(
        'event.registration',
        ondelete='cascade',
        help="If set, this line is personal to one participant"
    )
```

**Warning**: This adds a 4th provider-like relation (`registration_id`). But registration isn't a "provider" — it's a **scope limiter**. Lines with `registration_id` are personal; lines without are shared.

---

### Scenario G: 3-Month Cycle Batch Processing (NEW)

**Context**: From agenda_extended_core — DASEi operates on 3 main cycles per year. Batch operations create agenda.lines for status updates, payment reminders, confirmations.

```
3-Month Cycle (e.g., "Frühjahr 2026")
    └── Batch: Update event statuses 'announced' → 'current'
            └── agenda.line(type='milestone') per event
    └── Batch: Payment check for all active registrations
            └── agenda.line(type='action') for overdue
    └── Batch: Confirmation request to all participants
            └── agenda.line(type='info') with email
```

**Implementation**:
```python
class CycleBatchWizard(models.TransientModel):
    _name = 'cycle.batch.wizard'
    _description = 'Run 3-Month Cycle Batch Operations'
    
    cycle_name = fields.Char(required=True)  # "Frühjahr 2026"
    operation = fields.Selection([
        ('status_update', 'Update Event Statuses'),
        ('payment_check', 'Check Payments'),
        ('confirm_request', 'Request Confirmations'),
    ])
    
    def action_run_batch(self):
        if self.operation == 'status_update':
            events = self.env['event.event'].search([
                ('stage_id.name', '=', 'announced'),
                ('date_begin', '<=', fields.Date.today() + timedelta(days=30))
            ])
            for event in events:
                event.stage_id = self.env.ref('event.event_stage_current')
                self.env['agenda.line'].create({
                    'event_id': event.id,
                    'type': 'milestone',
                    'name': f'Status: Current ({self.cycle_name})',
                    'date': fields.Date.today(),
                    'source': 'template',  # batch-generated
                })
        # ... similar for payment_check, confirm_request
```

**Key insight**: Batch-generated lines have `source='template'` and typically `locked_edits=True`. They document system actions, not manual entries.

---

## ==DEV== scenario selection **3 Favorable Scenarios**

After reviewing all 7 scenarios against DASEi needs and implementation effort:

### ⭐ Selected: Scenario A — Event Type Template
**Why**: Foundation for all schedule-based agenda.lines. Every event needs this.
- Enables: Grundlagenkurs A template → 6 sessions auto-generated
- Matches: Existing `schedule_mixin.py` infrastructure
- Journey fit: Karo, Ida, Jolanda all see session schedules

### ⭐ Selected: Scenario F — Participant Journey Milestones  
**Why**: Directly models the 6 customer journeys. Personal agenda is the core UX.
- Enables: Ida's consulting call, Jolanda's D-module progress
- Matches: Curriculum tab requirement (progress per participant)
- Journey fit: All 6 journeys, especially issue-driver edge cases

### ⭐ Selected: Scenario G — 3-Month Cycle Batch Processing
**Why**: Matches DASEi's operational rhythm. Automates the "monthly workflow" at scale.
- Enables: Status updates, payment checks, confirmation requests
- Matches: "Not 10-30 tasks/day, but monthly cycles"
- Journey fit: Service-worker, accounting, instructor coordination

### Not Selected (but valuable):

| Scenario | Status | Reason |
|----------|--------|--------|
| B: Product Template | Deferred | Products flow through events; covered by A |
| C: Post-Driven Info | Later | Nice-to-have after core is stable |
| D: Chatter → Action | Later | Manual process, can be added incrementally |
| E: Event Package | Covered | Aggregation view, not new line creation |
```

---

## ==DRAFT== open questions **Decisions Needed**

### Q1: Model Migration Strategy
- **Option A**: Rename `event.session.line` → `agenda.line` (breaking change)
- **Option B**: Create new `agenda.line`, deprecate old model
- **Option C**: Keep both, `agenda.line` extends `event.session.line`

### Q2: Provider Constraint
Should we enforce exactly-one-provider at DB level?
```python
@api.constrains('event_id', 'post_id', 'product_id')
def _check_single_provider(self):
    for rec in self:
        providers = bool(rec.event_id) + bool(rec.post_id) + bool(rec.product_id)
        if providers != 1:
            raise ValidationError("Exactly one provider must be set")
```
Or allow zero providers for standalone actions?

### Q3: Template Resolution Timing
When does template → agenda.line expansion happen?
- **On event create** (immediate)
- **On event confirm** (deferred)
- **Manual trigger** (explicit button)

### Q4: Reverse Sync (Table → JSON)
If user edits agenda.line in table view, should it update schedule_json?
- Pro: Single source of truth
- Con: Complexity, potential data loss for text-based schedules

---

## Source References

- ⚙️ `crearis/models/event_session_line.py` — Current model (160 lines)
- ⚙️ `crearis/models/schedule_mixin.py` — JSONB parser (628 lines)
- ⚙️ `event_session/models/event_session.py` — OCA heavy model (avoid)
- [chapter_agenda_model](../_meta/Whitepaper/chapter_agenda_model.md) — Parent chapter
- [products_dasei_abcd](../_meta/Whitepaper/products_dasei_abcd.md) — Product structure
