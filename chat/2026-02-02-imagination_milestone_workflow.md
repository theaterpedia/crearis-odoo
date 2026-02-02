# Imagination: Complete Milestone Workflow

**Type**: imagination  
**Date**: 2026-02-02  
**Status**: Example scenario

---

## Scenario: A1 Kreisanimation Event Lifecycle

This imagination walks through a complete event lifecycle showing all three gated milestone transitions.

### Setup

- **Event**: "A1 Kreisanimation März 2026"
- **Event Type**: A1 Block (4-day format)
- **Date Begin**: Friday, March 6, 2026
- **Instructor**: Maria Schmidt
- **Domain**: dasei2 (use_milestones=True)
- **Company Labels**: Aktivierung, Meldefrist, Abschluss (German)

---

## Timeline

### January 5, 2026: Event Created

Maria creates the event from event type "A1 Block":

```
EVENT: A1 Kreisanimation März 2026
├── Stage: DRAFT (64)
├── Date Begin: 2026-03-06
├── Domain: dasei2
└── use_milestones: True (from domain)

AGENDA LINES (auto-generated from template):
├── [session] Fri 14:00-18:00 "Block 1" (4 UE) — mode: venue
├── [session] Sat 09:00-18:00 "Block 2" (8 UE) — mode: venue
├── [session] Sun 09:00-18:00 "Block 3" (8 UE) — mode: venue
├── [session] Sun 13:00-17:00 "Block 4" (4 UE) — mode: venue
└── [milestone] "Meldefrist" — gate_state: pending
                              milestone_key: deadline
                              milestone_days_before: 60
                              trigger_date: 2026-01-05
```

---

### January 5, 2026 (same day): Cron Runs

The daily cron `_cron_check_milestone_dates()` runs at 06:00:

```python
# Cron logic
today = 2026-01-05
event.date_begin = 2026-03-06
milestone.milestone_days_before = 60
trigger_date = 2026-03-06 - 60 days = 2026-01-05

today >= trigger_date? YES!
→ milestone.gate_state = 'ready'
→ Create activity for Maria
```

**Result**:
```
MILESTONE: Meldefrist
├── gate_state: READY (was: pending)
└── Activity created: "Meldefrist: A1 Kreisanimation März 2026"
                     assigned to: Maria Schmidt
                     deadline: 2026-01-05
```

---

### January 6, 2026: Maria Confirms Milestone

Maria sees the activity in her dashboard. She opens the event and clicks **"Confirm & Send"** on the Meldefrist milestone:

```python
# action_confirm_and_send()
1. Send email using milestone_template_id
   → Recipients: all registered participants
   → Subject: "Meldefrist: A1 Kreisanimation März 2026"
   → Body: "Hallo! Die Meldefrist für Deinen A1-Kurs rückt
            näher. Bitte gib uns bis zum 15. Januar Bescheid,
            ob Du dabei bist. Wir brauchen das, um den Kurs
            gut vorzubereiten — für Dich und alle anderen,
            die mit Dir zusammen starten werden."

2. milestone.gate_state = 'sent'

3. _maybe_advance_event_stage()
   → Event stage: DRAFT → CONFIRMED (512)
```

**Result**:
```
EVENT: A1 Kreisanimation März 2026
├── Stage: CONFIRMED (512) ✓
└── Registration: OPEN

MILESTONE: Meldefrist
└── gate_state: SENT ✓
```

---

### February 20, 2026: Schedule Finalized

Registration deadline approaches. Maria finalizes the schedule and creates the "Aktivierung" milestone for schedule release:

```
AGENDA LINES (updated):
├── [session] Fri 14:00-18:00 "Block 1" — conference_url: https://teams.microsoft.com/...
├── [session] Sat 09:00-18:00 "Block 2" — location_hint: Tanzerei Stuttgart
├── [session] Sun 09:00-18:00 "Block 3" — location_hint: Tanzerei Stuttgart
├── [session] Sun 13:00-17:00 "Block 4" — location_hint: Tanzerei Stuttgart
├── [milestone] "Meldefrist" — gate_state: sent ✓
└── [milestone] "Aktivierung" — gate_state: ready (manual)
                                milestone_key: activation
```

Maria clicks **"Confirm & Send"** on Aktivierung:

```
EVENT: A1 Kreisanimation März 2026
├── Stage: RELEASED (4096) ✓
└── Schedule: LOCKED (locked_edits=True)

MILESTONE: Aktivierung
└── gate_state: SENT ✓
```

**Email sent**: 
> "Hey! Der Ablaufplan für Deinen A1-Kurs steht.
> Hier findest Du alle Infos zu Zeiten und Orten.
> Schau Dir alles in Ruhe an — und wenn Du Fragen
> hast, melde Dich einfach. Wir freuen uns schon
> darauf, wenn Ihr alle zusammenkommt!"

---

### March 6-9, 2026: Event Runs

The event takes place as scheduled. Maria marks attendance.

---

### March 10, 2026: Wrap-Up

Day after event ends. The "Abschluss" milestone triggers:

```
MILESTONE: Abschluss
├── gate_state: READY (triggered by date_end + 1)
├── milestone_key: completion
└── Activity: "Abschluss: A1 Kreisanimation März 2026"
```

Maria reviews:
- Attendance: 18/20 participants (90%)
- No issues flagged

She clicks **"Confirm & Send"**:

```python
# action_confirm_and_send() for completion
1. Generate certificates for completed participants
2. Send wrap-up email:
   → "Das war's — Du hast es geschafft! 🎉
      Dein Zertifikat findest Du im Anhang.
      Es war schön zu sehen, wie Ihr als Gruppe
      zusammengewachsen seid. Bleib dran, bleib
      neugierig — und vielleicht sehen wir uns
      ja beim nächsten Kurs wieder!"
3. milestone.gate_state = 'sent'
4. Event stage: RELEASED → COMPLETED (8192)
```

**Final State**:
```
EVENT: A1 Kreisanimation März 2026
├── Stage: COMPLETED (8192) ✓
├── Participants: 18 completed, 2 partial
└── Certificates: Generated

AGENDA LINES:
├── [session] Block 1 — gate_state: n/a (sessions don't have gate)
├── [session] Block 2 — gate_state: n/a
├── [session] Block 3 — gate_state: n/a
├── [session] Block 4 — gate_state: n/a
├── [milestone] Meldefrist — gate_state: sent ✓
├── [milestone] Aktivierung — gate_state: sent ✓
└── [milestone] Abschluss — gate_state: sent ✓
```

---

## Exception Flow: Issue Flagged

What if Maria finds a problem at the Meldefrist milestone?

### January 6, 2026 (Alternative)

Maria reviews the milestone but notices the venue isn't confirmed yet. She clicks **"Flag Issue"**:

```python
# action_flag_issue()
milestone.gate_state = 'issue'
# Activity escalated to manager
```

**Result**:
```
MILESTONE: Meldefrist
├── gate_state: ISSUE ⚠️
└── Activity: Escalated to event manager
```

The event stays in DRAFT stage. Once venue is confirmed, manager can:
1. Resolve the issue
2. Reset gate_state to 'ready'
3. Maria confirms normally

---

## View: Milestones Ready Dashboard

Event managers see all ready milestones:

```
╔══════════════════════════════════════════════════════════════════════╗
║  MILESTONES: READY FOR ACTION                                        ║
╠══════════════════════════════════════════════════════════════════════╣
║  🎯 2026-01-05 | A1 Kreisanimation März 2026 | Meldefrist  | Maria   ║
║  🎯 2026-01-08 | LR Aufbaukurs April 2026    | Meldefrist  | Thomas  ║
║  🎯 2026-01-10 | AA Supervision Mai 2026     | Aktivierung | Sarah   ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

## Data Model Summary

```
agenda.line (type='milestone')
├── milestone_key: 'activation' | 'deadline' | 'completion'
├── milestone_days_before: Integer (60 for Meldefrist)
├── milestone_template_id: → mail.template
├── gate_state: 'pending' → 'ready' → 'sent' / 'issue'
└── event_id: → event.event

event.event
├── stage_id: draft(64) → confirmed(512) → released(4096) → completed(8192)
├── use_milestones: Boolean (from domain_code)
└── agenda_line_ids: One2many → agenda.line

res.company
├── milestone_label_activation: "Aktivierung"
├── milestone_label_deadline: "Meldefrist"
└── milestone_label_completion: "Abschluss"
```

---

## Key Insights

1. **All transitions are GATED** — milestones create decision points, not automatic advances
2. **Gate state flow**: pending → (cron) → ready → (human) → sent/issue
3. **Labels are configurable** — company sets German defaults, others can customize
4. **Issue handling** — problems can be flagged without blocking the system
5. **Daily cron** — ensures milestones become ready on the right day
