# Imagination: 3-Month Cycle Batch Processing

**Date**: 2026-01-31  
**Scenario**: G — 3-Month Cycle Batch Processing  
**Stage**: imagination

---

## Abstract

DASEi operates on 3 main cycles per year. Each cycle involves batch operations that create agenda.lines for status updates, payment checks, and confirmations. This imagination doc shows how the system automates the "monthly workflow" at scale.

**Two Deadline Types in Cycle Context**:
| Deadline | Level | Batch Processing |
|----------|-------|------------------|
| **Meldefrist** | Event | 2-4 events per cycle reach their confirmation deadline (2-4 months before event). Batch reminder emails to participants. |
| **Stornierungsfrist** | Module/Product | Tracked per participant. After first event attendance + 10 days, module purchase becomes binding. Accounting sync. |

---

## Example 1: Frühjahr 2026 Cycle — Concrete Input

**Context**: From agenda_extended_core — "accounting supervises payments 3 times per year + bigger website-updates 3 times per year + planning decisions on underbooked events".

### The 3-Month Cycle Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3-Month Cycle: Frühjahr 2026                                                │
│ Period: January 15 — April 15, 2026                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ ┌─ Cycle Overview ──────────────────────────────────────────────────────┐   │
│ │                                                                       │   │
│ │  Phase 1: Newsletter (Week 1-2)                     ✅ Completed      │   │
│ │    • Newsletter aggregated and published                             │   │
│ │    • 847 recipients, 312 opens, 45 clicks                            │   │
│ │                                                                       │   │
│ │  Phase 2: Reactions (Week 2-3)                      ✅ Completed      │   │
│ │    • 12 new inquiries processed                                      │   │
│ │    • 3 consulting calls scheduled                                    │   │
│ │                                                                       │   │
│ │  Phase 3: Planning Session (Week 3)                 🔶 In Progress   │   │
│ │    • Team meeting: 2026-02-12                                        │   │
│ │    • Decisions pending: 4 underbooked events                         │   │
│ │                                                                       │   │
│ │  Phase 4: Website Update (Week 4)                   ⬜ Upcoming      │   │
│ │    • Content refresh for spring events                               │   │
│ │    • New event announcements                                         │   │
│ │                                                                       │   │
│ └───────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│ ═══════════════════════════════════════════════════════════════════════════ │
│  BATCH OPERATIONS                                                           │
│ ═══════════════════════════════════════════════════════════════════════════ │
│                                                                             │
│  ┌────────────────────────────────────────────────┬──────────┬───────────┐  │
│  │ Operation                                      │ Status   │ Action    │  │
│  ├────────────────────────────────────────────────┼──────────┼───────────┤  │
│  │ ⏰ Meldefrist Reminders (EVENT-LEVEL)          │ Ready    │ [▶ Run]   │  │
│  │    Events with Meldefrist in this cycle: 4     │          │           │  │
│  │    A1 München: 2026-01-12                      │          │           │  │
│  │    A2 Nürnberg: 2026-01-18                     │          │           │  │
│  │    B1 München: 2026-02-05                      │          │           │  │
│  │    B2 Nürnberg: 2026-02-12                     │          │           │  │
│  ├────────────────────────────────────────────────┼──────────┼───────────┤  │
│  │ 📊 Update Event Statuses                       │ Ready    │ [▶ Run]   │  │
│  │    announced → current: 8 events               │          │           │  │
│  │    current → completed: 3 events               │          │           │  │
│  ├────────────────────────────────────────────────┼──────────┼───────────┤  │
│  │ 💰 Payment Check                               │ Ready    │ [▶ Run]   │  │
│  │    Active registrations: 156                   │          │           │  │
│  │    Expected: 23 overdue                        │          │           │  │
│  ├────────────────────────────────────────────────┼──────────┼───────────┤  │
│  │ ✉️ Confirmation Requests                       │ Pending  │ [Preview] │  │
│  │    Requires: Planning session decisions        │          │           │  │
│  │    Recipients: ~120 participants               │          │           │  │
│  ├────────────────────────────────────────────────┼──────────┼───────────┤  │
│  │ 📋 Instructor Schedules                        │ Ready    │ [▶ Run]   │  │
│  │    Events needing confirmation: 12             │          │           │  │
│  │    Instructors to notify: 8                    │          │           │  │
│  └────────────────────────────────────────────────┴──────────┴───────────┘  │
│                                                                             │
│ [📥 Export Cycle Report] [🔄 Refresh Data] [⚙️ Cycle Settings]              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Meldefrist Batch Processing

**Optimally**: 2-4 events hit their Meldefrist within the same 3-month cycle. This allows batch coordination of:
- Customer confirmation reminders
- Accounting payment status sync
- Team planning for underbooked events

```python
# Find events with Meldefrist in this cycle
cycle_start = '2026-01-15'
cycle_end = '2026-04-15'

events_with_meldefrist = Event.search([
    ('meldefrist_date', '>=', cycle_start),
    ('meldefrist_date', '<=', cycle_end),
])

# Group by week for coordinated reminders
for event in events_with_meldefrist:
    # Create reminder agenda.line for each participant
    for reg in event.registration_ids:
        AgendaLine.create({
            'type': 'action',
            'event_id': event.id,
            'registration_id': reg.id,
            'name': f'Meldefrist: {event.name}',
            'date': event.meldefrist_date - timedelta(days=14),  # 2 weeks before
            'notes': 'Bitte bestätigen oder abmelden.',
        })
```

### Email Text Reference: Meldefrist Reminder

```
Betreff: Bitte bestätigen — Meldefrist {event.name}

Liebe/r {participant.name},

die Meldefrist für {event.name} ({event.date_begin}) läuft 
am {event.meldefrist_date} ab.

Bitte bestätigen Sie Ihre Teilnahme:

  [✅ Ich nehme teil]  [❌ Ich melde mich ab]

Nach der Meldefrist ist eine Abmeldung nur noch bei 
Stellung eines Ersatzteilnehmers möglich.

Ihre weiteren Termine in diesem Zyklus:
{upcoming_events_list}

Herzliche Grüße,
Das DASEi Team
```

### Email Text Reference: Payment Reminder

From workflow patterns, the batch creates personalized emails:

```
Subject: Zahlungserinnerung — Frühjahr 2026

Liebe/r {participant.name},

Im Rahmen unserer Quartalsabrechnung haben wir festgestellt, dass 
folgende Zahlung noch aussteht:

  Kurs: {event.name}
  Betrag: {amount_due} €
  Fällig seit: {due_date}

Bitte überweisen Sie den Betrag bis zum {reminder_deadline} auf 
unser Konto:

  IBAN: DE89 3704 0044 0532 0130 00
  Verwendungszweck: {registration.reference}

Falls Sie bereits überwiesen haben, ignorieren Sie diese Nachricht.
Bei Fragen zur Rechnung kontaktieren Sie uns gerne.

Herzliche Grüße,
Das DASEi Team

---
Diese Nachricht wurde automatisch erstellt (Zyklus Frühjahr 2026).
```

### Generated Agenda Lines

After running "Payment Check" batch:

```python
# For each overdue registration, create action line
for registration in overdue_registrations:
    agenda_line = {
        'type': 'action',
        'event_id': registration.event_id.id,
        'registration_id': registration.id,
        'name': f'Zahlungserinnerung ({cycle_name})',
        'date': fields.Date.today(),
        'source': 'template',
        'locked_edits': True,
        'notes': f'Betrag: {registration.amount_due}€, Fällig: {registration.due_date}',
        'state': 'pending',
    }
```

---

## Example 2: Small Detail — Underbooked Event Decision Flow

**Context**: 4 events have <50% registrations. The planning session must decide: cancel, merge, or proceed.

### The Problem

```
Event: B1 Rollen-Ich (Teil von Modul B "Szenische Themenarbeit")
Location: München
Date: April 2026
Capacity: 16
Registered: 5 (31%)
Status: announced
Decision needed: Cancel / Merge / Proceed with discount

How does this flow through agenda.lines?
```

### Wizard: Underbooked Event Decision

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Underbooked Event Decision                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Event: B1 Rollen-Ich — München April 2026                                   │
│ Current: 5/16 registered (31%)                                              │
│ Threshold: 50% (8 participants)                                             │
│ Days until start: 45                                                        │
│                                                                             │
│ ┌─ Decision Options ────────────────────────────────────────────────────┐   │
│ │                                                                       │   │
│ │  ○ Cancel Event                                                      │   │
│ │    Creates for each participant:                                      │   │
│ │    • agenda.line(type='info'): "Event cancelled"                     │   │
│ │    • agenda.line(type='action'): "Refund/Transfer"                   │   │
│ │    • Email: Cancellation notification                                │   │
│ │                                                                       │   │
│ │  ○ Merge with Nürnberg B1 Event                                       │   │
│ │    Creates for each participant:                                      │   │
│ │    • agenda.line(type='info'): "Event merged"                        │   │
│ │    • agenda.line(type='action'): "Confirm new dates"                 │   │
│ │    • Updates: registration.event_id → merged event                   │   │
│ │                                                                       │   │
│ │  ● Proceed (extend deadline + discount)                              │   │
│ │    Creates:                                                           │   │
│ │    • agenda.line(type='milestone'): "Extended registration"          │   │
│ │    • Marketing push (newsletter mention)                             │   │
│ │    • Discount: 15% for new registrations                             │   │
│ │                                                                       │   │
│ └───────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│ Decision Notes:                                                             │
│ ┌───────────────────────────────────────────────────────────────────────┐   │
│ │ Team decision 2026-02-12: Proceed with discount.                     │   │
│ │ Reason: Strong instructor availability, good venue slot.             │   │
│ │ Review again in Cycle 2 if <8 registrations.                         │   │
│ └───────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│ [Cancel] [Apply Decision]                                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Resulting Agenda Lines

Decision: "Proceed with discount"

```python
# On the event itself
event_milestone = {
    'type': 'milestone',
    'event_id': event.id,
    'name': 'Extended Registration (Frühjahr 2026)',
    'date': '2026-02-12',
    'source': 'template',
    'notes': 'Decision: Proceed with 15% discount. Review in Cycle 2.',
}

# For marketing/website team
marketing_action = {
    'type': 'action',
    'event_id': event.id,
    'name': 'Add to newsletter + website highlight',
    'date': '2026-02-15',
    'source': 'template',
    'assigned_to': 'marketing@dasei.eu',
}
```

---

## Example 3: Meta-Level — The 3-Cycle Calendar

**Context**: DASEi's year is structured around 3 cycles. How do batch operations align with the business calendar?

### Annual Cycle Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ DASEi Annual Cycles — 2026                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│     JAN    FEB    MAR    APR    MAY    JUN    JUL    AUG    SEP    OCT  ...│
│     ├──────────────┤      ├──────────────┤      ├──────────────┤           │
│     │   FRÜHJAHR   │      │    SOMMER    │      │    HERBST    │           │
│     │   Cycle 1    │      │   Cycle 2    │      │   Cycle 3    │           │
│     └──────────────┘      └──────────────┘      └──────────────┘           │
│                                                                             │
│  Cycle Phases:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Week 1-2: Newsletter + Reactions                                    │   │
│  │ Week 3:   Planning Session (team)                                   │   │
│  │ Week 4:   Website Update                                            │   │
│  │ Week 5-8: Execution (events, follow-ups)                            │   │
│  │ Week 9-12: Normal operations                                        │   │
│  │ Week 13:  Cycle handover                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Batch Operations per Cycle:                                                │
│  ┌─────────────┬──────────────────────────────────────────────────────┐    │
│  │ Operation   │ What it creates                                      │    │
│  ├─────────────┼──────────────────────────────────────────────────────┤    │
│  │ Status      │ milestone: "Status: announced→current"               │    │
│  │ Update      │ info: Status change notification to participants     │    │
│  ├─────────────┼──────────────────────────────────────────────────────┤    │
│  │ Payment     │ action: "Payment overdue" for each overdue           │    │
│  │ Check       │ info: Payment reminder email                         │    │
│  ├─────────────┼──────────────────────────────────────────────────────┤    │
│  │ Confirm     │ action: "Confirm participation" for each active      │    │
│  │ Requests    │ info: Confirmation request email                     │    │
│  ├─────────────┼──────────────────────────────────────────────────────┤    │
│  │ Instructor  │ action: "Confirm availability" per instructor        │    │
│  │ Schedules   │ meeting: Planning call if conflicts                  │    │
│  └─────────────┴──────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Implementation: Cycle Configuration

```python
class CycleConfig(models.Model):
    _name = 'cycle.config'
    _description = '3-Month Cycle Configuration'
    
    name = fields.Char(required=True)  # "Frühjahr 2026"
    date_start = fields.Date(required=True)
    date_end = fields.Date(required=True)
    
    # Phase dates
    newsletter_start = fields.Date()
    planning_session_date = fields.Date()
    website_update_deadline = fields.Date()
    
    # Thresholds
    underbooked_threshold = fields.Float(default=0.5)  # 50%
    payment_overdue_days = fields.Integer(default=30)
    
    # Generated lines tracking
    batch_line_ids = fields.One2many(
        'agenda.line',
        'cycle_id',
        string='Generated Agenda Lines'
    )
    
    # Operations log
    operation_ids = fields.One2many(
        'cycle.operation.log',
        'cycle_id',
        string='Operation History'
    )


class CycleOperationLog(models.Model):
    _name = 'cycle.operation.log'
    _description = 'Cycle Batch Operation Log'
    
    cycle_id = fields.Many2one('cycle.config', required=True)
    operation = fields.Selection([
        ('status_update', 'Status Update'),
        ('payment_check', 'Payment Check'),
        ('confirm_request', 'Confirmation Request'),
        ('instructor_schedule', 'Instructor Schedule'),
        ('underbooked_decision', 'Underbooked Decision'),
    ])
    
    executed_at = fields.Datetime()
    executed_by = fields.Many2one('res.users')
    
    # Statistics
    records_processed = fields.Integer()
    lines_created = fields.Integer()
    emails_sent = fields.Integer()
    
    notes = fields.Text()
```

### Agenda Line Tagging for Cycles

```python
class AgendaLine(models.Model):
    _inherit = 'agenda.line'
    
    cycle_id = fields.Many2one(
        'cycle.config',
        string='Generated by Cycle',
        help="If set, this line was batch-generated by a cycle operation"
    )
    
    cycle_operation = fields.Selection([
        ('status_update', 'Status Update'),
        ('payment_check', 'Payment Check'),
        ('confirm_request', 'Confirmation Request'),
        ('instructor_schedule', 'Instructor Schedule'),
    ], string='Cycle Operation')
```

### Report: Cycle Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Cycle Summary: Frühjahr 2026                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Agenda Lines Generated:                                                     │
│                                                                             │
│   By Operation:                                                             │
│   ├── Status Update:        11 milestones                                  │
│   ├── Payment Check:        23 actions (18 resolved, 5 pending)            │
│   ├── Confirm Request:     120 actions (98 confirmed, 15 pending, 7 issue) │
│   └── Instructor Schedule:  12 actions (12 confirmed)                      │
│                                                                             │
│   By Type:                                                                  │
│   ├── milestone:  11                                                        │
│   ├── action:    155                                                        │
│   ├── info:       89                                                        │
│   └── meeting:     8                                                        │
│                                                                             │
│   Total: 263 agenda lines                                                   │
│                                                                             │
│ Key Outcomes:                                                               │
│   • 8 events advanced: announced → current                                  │
│   • 3 events completed                                                      │
│   • €12,340 collected from payment reminders                               │
│   • 2 events merged (underbooked)                                          │
│   • 98% participant confirmation rate                                       │
│                                                                             │
│ [📊 Full Report] [📤 Export to Excel] [📧 Send to Team]                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Source References

- 3-month cycle concept: `agenda_extended_core.md`
- Monthly workflow focus: `agenda_extended_core.md`
- Service-worker journey: `agenda_extended_journeys.md`
- Email templates: `workflow_email_templates.md`
