# Imagination: Participant Journey Milestones

**Date**: 2026-01-31  
**Scenario**: F — Participant Journey Milestones  
**Stage**: imagination

---

## Abstract

Each participant has a personal agenda view combining event sessions with their individual milestones, actions, and meetings. This imagination doc shows 3 examples of how the personal agenda works for different journeys.

**Two Deadline Types** (clarified 2026-01-31):
| Deadline | Level | When | Visible to |
|----------|-------|------|------------|
| **Meldefrist** | Event | 2-4 months before each event | Participant, Team |
| **Stornierungsfrist** | Module/Product | 10 days after first event attendance | Participant, Accounting |

---

## Example 1: Ida's Module Journey — Concrete Input

**Context**: From Ida's journey (aged 37, Nürnberg). She purchased Module A "Einstiege ins Theaterspiel" and has attended A0, A1, A2, A3. Her **Stornierungsfrist** (module cancellation deadline) passed after A0. Now she sees upcoming Meldefristen for remaining events.

### Ida's Personal Agenda View

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 👤 Ida Müller — Agenda                                          [🔄 Refresh]│
├─────────────────────────────────────────────────────────────────────────────┤
│ Module: Einstiege ins Theaterspiel (A) — Nürnberg Herbst 2025               │
│ Status: In Progress (4 of 7 events completed: A0, A1, A2, A3)               │
│ Stornierungsfrist: ✅ 2025-09-22 (passed — module purchase binding)         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ ═══════════════════════════════════════════════════════════════════════════ │
│  MODULE MILESTONES                                                          │
│ ═══════════════════════════════════════════════════════════════════════════ │
│                                                                             │
│  ✅ 2025-09-22  ⏰ Stornierungsfrist                         passed         │
│     └─ 10 days after A0 attendance. Module purchase now binding.            │
│  🔶 2025-10-09  👤 Beratungsgespräch mit Hans               ⏱️ in 4 days    │
│     └─ Required before upgrade to Module B                                  │
│  ⬜ TBD         🎓 Modul A Zertifikat                        after A5       │
│                                                                             │
│ ═══════════════════════════════════════════════════════════════════════════ │
│  COMPLETED EVENTS                                                           │
│ ═══════════════════════════════════════════════════════════════════════════ │
│                                                                             │
│  ✅ 2025-09-12  📍 A0 Basistag (Tanzerei, Nürnberg)           8h completed  │
│  ✅ 2025-09-13  📍 A1 Kreisanimation Block                   22h completed  │
│     └─ DO-SO + Online Nachbereitung DI                                      │
│  ✅ 2025-10-04  📍 A2 Zwei-Kreise Block                      22h completed  │
│     └─ DO-SO + Online Nachbereitung DI                                      │
│  ✅ 2025-10-18  📍 A3 Drei-Kreise Block                      22h completed  │
│                                                                             │
│ ═══════════════════════════════════════════════════════════════════════════ │
│  UPCOMING EVENTS + MELDEFRISTEN                                             │
│ ═══════════════════════════════════════════════════════════════════════════ │
│                                                                             │
│  ⏰ 2025-11-01  Meldefrist A4 Vier-Kreise                    ⏱️ in 23 days  │
│     └─ [✅ Bestätigen] [❌ Abmelden]                                         │
│  📋 2025-11-04  🌐 A4 Online Nachbereitung                   2h scheduled   │
│     └─ Part of A4 Block, protocol task assigned: Ida                        │
│  📍 2025-12-05  📍 A4 Vier-Kreise Block                      22h scheduled  │
│                                                                             │
│ ═══════════════════════════════════════════════════════════════════════════ │
│  ACTIONS (open)                                                             │
│ ═══════════════════════════════════════════════════════════════════════════ │
│                                                                             │
│  ⚡ Invoice Split Request                                    created 10-06  │
│     │  Status: Pending (assigned to: Buchhaltung)                           │
│     │  Amount: 400€ Arbeitgeberzuschuss                                     │
│     └─ [View Details]                                                       │
│                                                                             │
│  ⚡ Protocol Task: A3 Drei-Kreise                             due: 10-25    │
│     │  Status: In Progress                                                  │
│     │  [📎 Upload Protocol]                                                 │
│     └─ [Mark Complete]                                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Model Behind the View

```python
# Ida's module purchase (product.template)
module_purchase = {
    'product_id': 101,        # "Einstiege ins Theaterspiel" (Modul A)
    'partner_id': 1234,       # Ida
    'purchase_date': '2025-08-15',
    'first_event_date': '2025-09-12',  # A0 attendance
    'stornierungsfrist': '2025-09-22', # +10 days after first event
    'stornierung_passed': True,
}

# Module-level agenda.lines (from product template)
module_agenda_lines = [
    {
        'type': 'milestone',
        'product_id': 101,
        'registration_id': 4521,
        'name': 'Stornierungsfrist',
        'date': '2025-09-22',  # first_event + 10 days
        'source': 'template',
        'notes': 'Nach diesem Datum ist der Modulkauf verbindlich. Nur 1. Rate wird einbehalten.',
    },
    {
        'type': 'meeting',
        'product_id': 101,
        'registration_id': 4521,
        'name': 'Beratungsgespräch',
        'date': '2025-10-09',  # scheduled after 2+ events
        'source': 'template',
        'notes': 'Required before upgrade to Module B',
    },
    {
        'type': 'milestone',
        'product_id': 101,
        'registration_id': 4521,
        'name': 'Modul A Zertifikat',
        'date': None,  # computed after A5 completion
        'source': 'template',
    },
]

# Event-level agenda.lines (from event.type templates)
# Each event A0, A1, A2... has its own Meldefrist + session lines
event_agenda_lines = [
    # A0 Basistag
    {'type': 'milestone', 'event_id': 890, 'name': 'Meldefrist A0', 'date': '2025-07-12'},
    {'type': 'session', 'event_id': 890, 'date': '2025-09-12', 'label': 'A0 Basistag', 'mode': 'venue'},
    
    # A1 Kreisanimation - Block format (DO-SO + Online)
    {'type': 'milestone', 'event_id': 891, 'name': 'Meldefrist A1', 'date': '2025-07-13'},
    {'type': 'session', 'event_id': 891, 'date': '2025-09-12', 'label': 'A1 DO Anreise', 'mode': 'venue'},
    {'type': 'session', 'event_id': 891, 'date': '2025-09-13', 'label': 'A1 FR', 'mode': 'venue'},
    {'type': 'session', 'event_id': 891, 'date': '2025-09-14', 'label': 'A1 SA', 'mode': 'venue'},
    {'type': 'session', 'event_id': 891, 'date': '2025-09-15', 'label': 'A1 SO', 'mode': 'venue'},
    {'type': 'session', 'event_id': 891, 'date': '2025-09-23', 'label': 'A1 Online', 'mode': 'online'},
    
    # A4 Vier-Kreise (upcoming, Meldefrist visible)
    {'type': 'milestone', 'event_id': 894, 'name': 'Meldefrist A4', 'date': '2025-11-01'},
    {'type': 'session', 'event_id': 894, 'date': '2025-12-05', 'label': 'A4 DO', 'mode': 'venue'},
    # ... more A4 sessions ...
]

# Ida's personal agenda.lines (only visible to her)
personal_agenda_lines = [
    {
        'type': 'action',
        'date': '2025-10-06',
        'label': 'Invoice Split Request',
        'registration_id': 4521,
        'state': 'pending',
    },
    {
        'type': 'action',
        'date': '2025-10-15',
        'label': 'Protocol Task: A3 Drei-Kreise',
        'registration_id': 4521,
        'state': 'in_progress',
    },
]
```

### Stornierungsfrist Logic

```python
class ProductModulePurchase(models.Model):
    \"\"\"Tracks module purchase with cancellation deadline.\"\"\"
    
    first_event_attendance = fields.Date('First Event Attended')
    stornierungsfrist = fields.Date(
        compute='_compute_stornierungsfrist',
        store=True
    )
    stornierung_passed = fields.Boolean(
        compute='_compute_stornierung_passed'
    )
    
    @api.depends('first_event_attendance')
    def _compute_stornierungsfrist(self):
        for rec in self:
            if rec.first_event_attendance:
                rec.stornierungsfrist = rec.first_event_attendance + timedelta(days=10)
    
    @api.depends('stornierungsfrist')
    def _compute_stornierung_passed(self):
        for rec in self:
            rec.stornierung_passed = rec.stornierungsfrist and rec.stornierungsfrist < fields.Date.today()
```

---

## Example 2: Small Detail — Completion Status Sync

**Context**: When Ida attends the A4 Online Nachbereitung, how does the system know to mark it "completed"?

### The Problem

```
Session: A4 Online Nachbereitung (part of A4 Vier-Kreise Block)
Date: 2025-11-04, 19:00-21:00
Mode: online

Ida's status: ?
  - She joined the Teams call
  - She stayed for 1.8 of 2 hours
  - Should this count as "completed"?
```

### The Solution: Attendance-Based Completion

```python
class AgendaLine(models.Model):
    _inherit = 'agenda.line'
    
    # Per-participant completion tracking
    attendance_ids = fields.One2many(
        'agenda.line.attendance',
        'line_id',
        string='Attendance Records'
    )
    
    def get_completion_status(self, registration):
        """
        Get completion status for a specific participant.
        
        Returns: 'completed', 'partial', 'missed', 'upcoming'
        """
        if self.date > fields.Date.today():
            return 'upcoming'
        
        attendance = self.attendance_ids.filtered(
            lambda a: a.registration_id == registration
        )
        
        if not attendance:
            return 'missed'
        
        # Check minimum attendance threshold (e.g., 80%)
        if attendance.duration_attended >= self.duration_h * 0.8:
            return 'completed'
        else:
            return 'partial'


class AgendaLineAttendance(models.Model):
    _name = 'agenda.line.attendance'
    _description = 'Participant Attendance per Agenda Line'
    
    line_id = fields.Many2one('agenda.line', required=True, ondelete='cascade')
    registration_id = fields.Many2one('event.registration', required=True)
    
    attended = fields.Boolean(default=False)
    duration_attended = fields.Float('Hours Attended')
    notes = fields.Text('Attendance Notes')
    
    # Auto-populated from Teams/Zoom API (future)
    joined_at = fields.Datetime()
    left_at = fields.Datetime()
```

### Visual Indicator

| Status | Icon | Color | Meaning |
|--------|------|-------|---------|
| completed | ✅ | green | Attended ≥80% |
| partial | ⚠️ | yellow | Attended <80% |
| missed | ❌ | red | No attendance record |
| upcoming | 📋 | gray | Future date |

### Ida's A4 Online Session Status

```
2025-11-04: A4 Online Nachbereitung
  Duration: 2h
  Ida attended: 1.8h (90%)
  Status: ✅ completed
```

---

## Example 3: Meta-Level — Journey State Machine

**Context**: Each participant moves through states. The agenda view adapts based on journey phase.

### Journey States (from agenda_extended_journeys)

| Journey | Phase | Agenda Focus | Key Lines Visible |
|---------|-------|--------------|-------------------|
| Karo | Discovery | Light touch | INFO-Teaser session only |
| Ida | Participation | Full schedule | Sessions + consulting + actions |
| Jolanda | Transformation | Extended | D-module + instructor prep + crearis access |
| Issue-driver | Recovery | Simplified | Overdue payments, missed sessions, reschedules |

### Wizard: Journey Phase Transition

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Participant Journey Transition                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Participant: Ida Müller                                                     │
│ Current Phase: A-Module Participation                                       │
│                                                                             │
│ ┌─ Transition Options ──────────────────────────────────────────────────┐   │
│ │                                                                       │   │
│ │  ○ Continue to B-Module                                              │   │
│ │    → Creates: B-module event registration                            │   │
│ │    → Adds: 6 new session lines to agenda                             │   │
│ │    → Schedules: Consulting call for module transition                │   │
│ │                                                                       │   │
│ │  ○ Pause (Sabbatical)                                                │   │
│ │    → Freezes: Current progress                                       │   │
│ │    → Adds: "Reactivation reminder" milestone (6 months)              │   │
│ │    → Hides: Future sessions from agenda                              │   │
│ │                                                                       │   │
│ │  ○ Complete A-Module Only                                            │   │
│ │    → Adds: "A-Module Certificate" milestone                          │   │
│ │    → Archives: Completed sessions                                    │   │
│ │    → Shows: Alumni info lines                                        │   │
│ │                                                                       │   │
│ │  ○ Issue Resolution Required                                         │   │
│ │    → Adds: "Payment overdue" action                                  │   │
│ │    → Adds: "Reschedule missed sessions" action                       │   │
│ │    → Blocks: B-module registration until resolved                    │   │
│ │                                                                       │   │
│ └───────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│ Notes for this transition:                                                  │
│ ┌───────────────────────────────────────────────────────────────────────┐   │
│ │ Ida hat 2 Terminconflikte für B-Modul identifiziert.                 │   │
│ │ Consulting call scheduled to resolve via München alternatives.        │   │
│ └───────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│ [Cancel] [Save as Draft] [Execute Transition]                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Implementation: Journey-Aware Agenda Filtering

```python
class EventRegistration(models.Model):
    _inherit = 'event.registration'
    
    journey_phase = fields.Selection([
        ('discovery', 'Discovery'),      # Karo
        ('onboarding', 'Onboarding'),    # Karo → Ida
        ('participation', 'Active Participation'),  # Ida
        ('transformation', 'Transformation'),  # Jolanda
        ('alumni', 'Alumni'),
        ('issue', 'Issue Resolution'),   # Issue-driver
        ('paused', 'Paused'),
    ], default='discovery')
    
    def get_agenda_lines_for_phase(self):
        """
        Filter agenda lines based on journey phase.
        Different phases see different line types.
        """
        base_domain = [
            '|',
            ('event_id', '=', self.event_id.id),
            ('registration_id', '=', self.id),
        ]
        
        if self.journey_phase == 'discovery':
            # Minimal view: only upcoming sessions
            return self.env['agenda.line'].search(
                base_domain + [
                    ('type', '=', 'session'),
                    ('date', '>=', fields.Date.today()),
                ]
            )
        
        elif self.journey_phase == 'issue':
            # Focus on blockers: actions and overdue milestones
            return self.env['agenda.line'].search(
                base_domain + [
                    ('type', 'in', ['action', 'milestone']),
                    '|',
                    ('state', '=', 'overdue'),
                    ('state', '=', 'pending'),
                ]
            )
        
        else:
            # Full view for participation/transformation
            return self.env['agenda.line'].search(base_domain)
```

### Journey Transitions Create Agenda Lines

| Transition | Lines Created |
|------------|---------------|
| Discovery → Onboarding | `meeting`: "Onboarding call scheduled" |
| Onboarding → Participation | `milestone`: "First payment received" |
| A-Module → B-Module | `session[]`: All B-module sessions |
| Any → Issue | `action`: "Resolve payment", "Reschedule session" |
| Participation → Alumni | `milestone`: "Certificate issued" |

---

## Source References

- Ida's journey: `agenda_extended_journeys.md`
- Issue-driver journey: `agenda_extended_journeys.md`
- Jolanda's journey: `agenda_extended_journeys.md`
- 3-Tab UI definition: `agenda_extended_core.md`
