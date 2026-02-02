# Milestones and Actions Architecture

**Type**: snapshot (pre-master)  
**Stage**: draft  
**Date**: 2026-02-02  
**Origin**: Chat session consolidating details.md, additions.md, origin.md

---

## Abstract

This document captures the architecture for **gated stage transitions** in the event lifecycle. All three major transitions (draft→confirmed, confirmed→current, current→completed) are **gated** — requiring human confirmation before proceeding.

The implementation is split:
- **crearis** (essential): Gate infrastructure, basic states, instructor-only workflow
- **crearis_milestones**: Manager review layer, transient controlling model, frontrunner scheduling

---

## ==TASKS==

### Decisions Confirmed
- [x] All 3 stage transitions are gated (not automatic)
- [x] Variant 2 (Concluding) for milestone semantics
- [x] `use_milestones` adds manager layer, without it instructor is the gate
- [x] Reuse `mail.mail.scheduled_date` for queue preview (no custom queue model)
- [x] Wrap-up is gated: creates action, instructor completes, THEN stage advances

### Open Questions
- [ ] Exact field names for agenda.line states
- [ ] How does crearis-vue interact with gate states via GraphQL?
- [ ] Default offset values (configurable or hardcoded?)

---

## ==DRAFT==

### The "Hot Phase" Model

Three non-session agenda.lines frame an event's active lifecycle:

| Line | Timing | Gates Transition To |
|------|--------|---------------------|
| **milestone** (confirmation) | ~60 days before date_begin | confirmed/announced |
| **info-mail** | 10-30 days before date_begin | current/released |
| **wrap-up** | 7+ days after date_end | completed |

**Key insight**: These are not automatic triggers — they are **gates** requiring human confirmation.

### Event Stages (Main Lifecycle)

| Sysreg | Stage EN | Stage DE | Entry Gate |
|--------|----------|----------|------------|
| 64 | booked/draft | geplant | (sync from planning) |
| 512 | announced/confirmed | angekündigt | milestone decision |
| 4096 | current/released | aktuell | info-mail confirmed |
| 8192 | completed | vollständig | wrap-up confirmed |

### The Gate Pattern

```
EVERY TRANSITION:
  
  1. Date approaches → agenda.line created (type=info/milestone/action)
  2. Instructor sees pending work
  3. Instructor confirms "ready" (ticks checkbox)
  4. Gate satisfied → stage advances
  
  OR (negative path):
  
  3. Instructor doesn't confirm
  4. Reminder sent ("3 days left")
  5. Due date: Issue flag raised
  6. Manager intervention (with use_milestones) or manual resolution
```

### Role Split

| Mode | Gate Role | Manager Layer |
|------|-----------|---------------|
| `use_milestones=False` | Instructor only | ❌ |
| `use_milestones=True` | Instructor prepares → Manager approves | ✅ |

---

## ==SPEC== (Partial)

### Module: crearis (Essential)

#### agenda.line States

```python
class AgendaLine(models.Model):
    _name = 'agenda.line'
    
    # Existing fields from current implementation...
    
    # NEW: Gate workflow states
    gate_state = fields.Selection([
        ('pending', 'Pending'),      # Needs work
        ('ready', 'Ready'),          # Instructor confirmed
        ('sent', 'Sent'),            # Executed (email sent, action done)
        ('issue', 'Issue'),          # Overdue, not confirmed
    ], default='pending')
    
    confirmed_by = fields.Many2one('res.users', string='Confirmed By')
    confirmed_date = fields.Datetime()
    
    # Gate to stage transition
    gates_stage = fields.Selection([
        ('confirmed', 'Gates → Confirmed'),
        ('released', 'Gates → Released/Current'),
        ('completed', 'Gates → Completed'),
    ], help="Which stage transition this line gates")
```

#### Stage Transition Logic

```python
class EventEvent(models.Model):
    _inherit = 'event.event'
    
    def _check_gate_and_advance(self, target_stage):
        """Check if gate is satisfied, advance stage if so."""
        gate_line = self.agenda_line_ids.filtered(
            lambda l: l.gates_stage == target_stage
        )
        if not gate_line:
            # No gate defined, allow manual advance
            return True
        if gate_line.gate_state == 'ready':
            self.stage = target_stage
            gate_line.gate_state = 'sent'
            return True
        return False
```

#### Cron: Daily Gate Check

```python
def _cron_check_gates(self):
    """Daily: flag overdue gates, send reminders."""
    today = fields.Date.today()
    
    # Find pending gates within reminder window
    upcoming = self.env['agenda.line'].search([
        ('gate_state', '=', 'pending'),
        ('date', '<=', today + timedelta(days=3)),
        ('date', '>', today),
    ])
    for line in upcoming:
        line._send_reminder()
    
    # Flag overdue as issues
    overdue = self.env['agenda.line'].search([
        ('gate_state', '=', 'pending'),
        ('date', '<=', today),
    ])
    overdue.write({'gate_state': 'issue'})
```

#### Mail Queue Pattern

```python
def _prepare_gate_mail(self):
    """Create mail.mail with scheduled_date for preview window."""
    # Create 4 hours before execution
    mail = self.env['mail.mail'].create({
        'subject': self._get_mail_subject(),
        'body_html': self._render_merged_content(),
        'scheduled_date': self.date + timedelta(hours=17),  # 17:00 send
        'state': 'outgoing',
        'recipient_ids': [(6, 0, self._get_recipients().ids)],
    })
    self.mail_id = mail.id
    return mail
```

---

### Module: crearis_milestones (Enhanced)

#### Config

```python
class ResCompany(models.Model):
    _inherit = 'res.company'
    
    use_milestones = fields.Boolean(
        string='Use Milestones Workflow',
        help='Enables manager review layer and bi-weekly controlling'
    )
```

#### Extended agenda.line

```python
class AgendaLine(models.Model):
    _inherit = 'agenda.line'
    
    # Manager review layer
    manager_reviewed = fields.Boolean()
    manager_id = fields.Many2one('res.users', string='Reviewed By')
    merged_content = fields.Html(
        string='Merged Content',
        help='Editable merged output, manager can edit before send'
    )
    manager_notes = fields.Text()
    
    # Frontrunner scheduling
    frontrunner_ids = fields.One2many(
        'agenda.line', 'parent_milestone_id',
        string='Frontrunner Actions'
    )
    parent_milestone_id = fields.Many2one(
        'agenda.line', string='Parent Milestone',
        help='This line is a frontrunner to this milestone'
    )
    offset_days = fields.Integer(
        string='Offset Days',
        help='Days before (-) or after (+) the milestone date'
    )
```

#### Transient Controlling Model

```python
class ControllingLine(models.TransientModel):
    _name = 'controlling.line'
    _description = 'Controlling View Line'
    
    agenda_line_id = fields.Many2one('agenda.line')
    event_id = fields.Many2one('event.event')
    instructor_id = fields.Many2one('res.partner')
    
    # Computed from agenda.line
    gate_state = fields.Selection(related='agenda_line_id.gate_state')
    date = fields.Date(related='agenda_line_id.date')
    days_until = fields.Integer(compute='_compute_days_until')
    
    # For manager editing
    merged_content = fields.Html(related='agenda_line_id.merged_content', readonly=False)
    
    @api.model
    def get_controlling_view(self, date_from=None, date_to=None, instructor_id=None):
        """Aggregate all due agenda.lines for controlling meeting."""
        domain = [
            ('gate_state', 'in', ['pending', 'ready', 'issue']),
            ('gates_stage', '!=', False),
        ]
        if date_from:
            domain.append(('date', '>=', date_from))
        if date_to:
            domain.append(('date', '<=', date_to))
        if instructor_id:
            domain.append(('event_id.user_id', '=', instructor_id))
        
        lines = self.env['agenda.line'].search(domain)
        return self.create([{
            'agenda_line_id': line.id,
            'event_id': line.event_id.id,
            'instructor_id': line.event_id.user_id.partner_id.id,
        } for line in lines])
```

#### Bi-Weekly Controlling Cron

```python
def _cron_biweekly_controlling(self):
    """Every 2 weeks: prepare controlling session for managers."""
    companies = self.env['res.company'].search([
        ('use_milestones', '=', True)
    ])
    for company in companies:
        # Find all gates in next 3 weeks
        date_to = fields.Date.today() + timedelta(weeks=3)
        lines = self.env['controlling.line'].with_company(company).get_controlling_view(
            date_to=date_to
        )
        # Create controlling session record or notification
        # ... implementation
```

---

## Implementation Split Summary

| Feature | crearis | crearis_milestones |
|---------|---------|-------------------|
| agenda.line `gate_state` field | ✅ | — |
| Instructor "confirm ready" action | ✅ | — |
| Date-based reminders ("3 days left") | ✅ | — |
| Issue flagging (overdue) | ✅ | — |
| `mail.mail.scheduled_date` queue | ✅ | — |
| Stage transition on gate satisfied | ✅ | — |
| `use_milestones` config | — | ✅ |
| Transient controlling model | — | ✅ |
| Manager aggregated view | — | ✅ |
| Merged content editing | — | ✅ |
| Bi-weekly controlling rhythm | — | ✅ |
| Frontrunner scheduling (offset_days) | — | ✅ |

---

## Timeline Example: A1 Grundlagenkurs Block

```
2026-01-15  Event created (stage: draft)
            └── milestone agenda.line created (date: 2026-02-01, gates: confirmed)

2026-01-25  Frontrunner: inquiry email (offset: -7 from milestone)
            Instructor sends registration confirmation requests

2026-02-01  MILESTONE DATE
            Manager reviews registrations, decides GO
            Instructor confirms milestone → gate_state = ready
            Stage advances → confirmed/announced

2026-02-20  info-mail agenda.line (date: 2026-02-20, gates: released)
            Instructor confirms event details are current
            → gate_state = ready
            Stage advances → current/released

2026-03-06  EVENT: date_begin (Fri)
2026-03-08  EVENT: date_end (Sun)

2026-03-15  wrap-up agenda.line (date: 2026-03-15, gates: completed)
            Instructor writes summary, confirms
            → gate_state = ready
            Stage advances → completed
```

---

## Next Steps

1. **Cross-check** against existing action plan (2026-01-31-action_plan_agenda_lines.md)
2. **Identify conflicts** with previous terminology/decisions
3. **Split into master docs**:
   - `agenda-lines.md` (core model, types, providers)
   - `milestones-and-actions.md` (this content, refined)
4. **Define negative spec**: What is NOT in essentials

---

## Source References

- [2026-02-02-details.md](2026-02-02-details.md) — Hot phase, event stages, milestone definition
- [2026-02-02-additions.md](2026-02-02-additions.md) — use_milestones config, frontrunners/followers
- [2026-02-02-origin.md](2026-02-02-origin.md) — Original transient model thinking
- [2026-01-31-action_plan_agenda_lines.md](2026-01-31-action_plan_agenda_lines.md) — Previous action plan
