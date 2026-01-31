# Imagination: Event Type Template → agenda.lines

**Date**: 2026-01-31  
**Scenario**: A — Event Type Template  
**Stage**: imagination

---

## Abstract

When an event is created from an event type, the type's schedule template automatically generates `agenda.line` records. This is at the **event level** (e.g., A1 Kreisanimation), not the module level (Einstiege ins Theaterspiel).

**Hierarchy**:
- COURSE: M18 Grundkurs Theaterpädagogik (full 2-year program)
- MODULE/PRODUCT: A = Einstiege ins Theaterspiel, B, C, D
- EVENT: A0 Basistag, A1 Kreisanimation, A2 Zwei-Kreise... (each separate)
- SESSION LINES: Time slots within one event (DO 19:00, FR 09:00, etc.)

**Two Deadline Types** (clarified 2026-01-31):
| Deadline | Level | What it controls |
|----------|-------|------------------|
| **Meldefrist** | Event | Confirmation deadline per event (e.g., A1). Typically 2-4 months before event start. |
| **Stornierungsfrist** | Module/Product | Cancellation deadline for module purchase. 10 days after first event attendance. |

---

## Example 1: A1 Kreisanimation Block — Concrete Input

**Context**: Admin creates event "A1 Kreisanimation - München März 2026" from the event type template. The system generates session lines AND the Meldefrist milestone.

### Event Type: A1 Kreisanimation (Block)

```yaml
# schedule_template on event.type
name: "A1 Kreisanimation (Block)"
meldefrist_days_before: 60  # Confirmation deadline 2 months before

sessions:
  - day: DO
    start: "19:00"
    end: "21:00"
    mode: venue
    label: "Anreise/Einführung"
  - day: FR
    start: "09:00"
    end: "12:30"
    mode: venue
    label: "Praxis Vormittag"
  - day: FR
    start: "14:00"
    end: "18:00"
    mode: venue
    label: "Praxis Nachmittag"
  - day: SA
    start: "09:00"
    end: "12:30"
    mode: venue
    label: "Praxis Vormittag"
  - day: SA
    start: "14:00"
    end: "18:00"
    mode: venue
    label: "Praxis Nachmittag"
  - day: SO
    start: "09:00"
    end: "15:00"
    mode: venue
    label: "Abschluss"
  - day: DI
    start: "19:00"
    end: "21:00"
    mode: online
    offset_weeks: 1
    label: "Online Nachbereitung"
```

### View: Event Form — Schedule Tab

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Event: A1 Kreisanimation — München März 2026                                │
│ Type: A1 Kreisanimation (Block)                                             │
│ Module: Einstiege ins Theaterspiel (A)                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ [Details] [Schedule] [Registrations] [Communication]                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─ Generated from Template ──────────────────────────────────────────────┐ │
│  │ ℹ️ 7 sessions + 1 milestone auto-generated from type template          │ │
│  │    [🔄 Regenerate] [✏️ Unlock for Editing]                              │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ═══════════════════════════════════════════════════════════════════════   │
│  MILESTONES                                                                 │
│  ═══════════════════════════════════════════════════════════════════════   │
│                                                                             │
│  │ ⏰ │ 2026-01-12 │ Meldefrist │ Confirm by this date or opt-out     │    │
│                                                                             │
│  ═══════════════════════════════════════════════════════════════════════   │
│  SESSIONS (Block: DO 12.03 — SO 15.03 + Online DI 24.03)                   │
│  ═══════════════════════════════════════════════════════════════════════   │
│                                                                             │
│  ┌────┬────────────┬─────────────┬────────┬──────────────┬────────────────┐ │
│  │ #  │ Date       │ Time        │ Mode   │ Label        │ Location       │ │
│  ├────┼────────────┼─────────────┼────────┼──────────────┼────────────────┤ │
│  │ 📍 │ 2026-03-12 │ 19:00-21:00 │ venue  │ Anreise      │ Burgstallmühle │ │
│  │ 📍 │ 2026-03-13 │ 09:00-12:30 │ venue  │ Praxis VM    │ Burgstallmühle │ │
│  │ 📍 │ 2026-03-13 │ 14:00-18:00 │ venue  │ Praxis NM    │ Burgstallmühle │ │
│  │ 📍 │ 2026-03-14 │ 09:00-12:30 │ venue  │ Praxis VM    │ Burgstallmühle │ │
│  │ 📍 │ 2026-03-14 │ 14:00-18:00 │ venue  │ Praxis NM    │ Burgstallmühle │ │
│  │ 📍 │ 2026-03-15 │ 09:00-15:00 │ venue  │ Abschluss    │ Burgstallmühle │ │
│  │ 🌐 │ 2026-03-24 │ 19:00-21:00 │ online │ Nachber.     │ [🔗 Teams]     │ │
│  └────┴────────────┴─────────────┴────────┴──────────────┴────────────────┘ │
│                                                                             │
│  Total: 22 UE (20h venue, 2h online) • Location: Burgstallmühle            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Meldefrist Logic

```python
# Event type defines offset
event_type.meldefrist_days_before = 60

# Event computes deadline from date_begin
event.date_begin = 2026-03-12
event.meldefrist_date = 2026-03-12 - 60 days = 2026-01-12

# System creates agenda.line
agenda_line = {
    'type': 'milestone',
    'event_id': event.id,
    'name': 'Meldefrist A1 Kreisanimation',
    'date': event.meldefrist_date,  # 2026-01-12
    'source': 'template',
    'notes': 'Participants must confirm attendance or opt-out by this date.'
}
```

### Email Reference: Meldefrist Reminder

```
Betreff: Bitte bestätigen — A1 Kreisanimation März 2026

Liebe/r {participant.name},

die Meldefrist für A1 Kreisanimation (12.-15. März) 
läuft am 12. Januar 2026 ab.

Bitte bestätigen Sie Ihre Teilnahme oder melden Sie sich ab:

  [✅ Ich nehme teil]  [❌ Ich melde mich ab]

Nach der Meldefrist ist eine Abmeldung nur noch bei 
Stellung eines Ersatzteilnehmers möglich.

Herzliche Grüße,
Das DASEi Team
```

---

## Example 2: Small Detail — Block Date Resolution Algorithm

**Context**: When event "A1 Kreisanimation" is created with `date_begin = 2026-03-12`, how does the system resolve DO-FR-SA-SO as consecutive days?

### The Problem

```
Template (A1 Block): 
  DO 19:00-21:00      (Anreise/Einführung)
  FR 09:00-12:30      (Slot 1)
  FR 14:00-18:00      (Slot 2)
  SA 09:00-12:30      (Slot 1)
  SA 14:00-18:00      (Slot 2)
  SO 09:00-15:00      (Abschluss)
  DI 19:00-21:00      (Online Nachbereitung, offset: +1 week)

Event: date_begin = 2026-03-12 (Thursday)

Expected resolution:
  DO = 2026-03-12     (Block start)
  FR = 2026-03-13     (consecutive)
  SA = 2026-03-14     (consecutive)
  SO = 2026-03-15     (Block end)
  DI = 2026-03-24     (Online follow-up, +1 week offset)
```

### The Solution: Consecutive Day Resolution

```python
def _resolve_block_dates(self, template_sessions, date_begin):
    """
    Resolve Block format: consecutive days starting from date_begin.
    
    Algorithm:
    1. date_begin is the first session's date
    2. Walk through days consecutively (DO→FR→SA→SO)
    3. Handle offset_weeks for post-block online sessions
    """
    from datetime import timedelta
    
    # Map weekday codes to Python weekday (0=Monday)
    WEEKDAY_MAP = {'MO': 0, 'DI': 1, 'MI': 2, 'DO': 3, 'FR': 4, 'SA': 5, 'SO': 6}
    
    current_date = date_begin
    resolved = []
    
    for session in template_sessions:
        offset_weeks = session.get('offset_weeks', 0)
        
        if offset_weeks > 0:
            # Jump forward for post-block sessions
            target_weekday = WEEKDAY_MAP[session['day']]
            # Find next occurrence of this weekday after offset
            days_ahead = target_weekday - current_date.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            session['resolved_date'] = current_date + timedelta(days=days_ahead + (offset_weeks - 1) * 7)
        else:
            # Consecutive day within block
            session['resolved_date'] = current_date
            # Move to next day for next session (unless same day)
            if resolved and resolved[-1]['day'] != session['day']:
                current_date += timedelta(days=1)
        
        resolved.append(session)
    
    return resolved
```

### Result

| Template Entry | Resolved Date | Logic |
|----------------|---------------|-------|
| DO 19:00-21:00 | 2026-03-12 | date_begin (Thursday) |
| FR 09:00-12:30 | 2026-03-13 | +1 day (consecutive) |
| FR 14:00-18:00 | 2026-03-13 | Same day (FR) |
| SA 09:00-12:30 | 2026-03-14 | +1 day (consecutive) |
| SA 14:00-18:00 | 2026-03-14 | Same day (SA) |
| SO 09:00-15:00 | 2026-03-15 | +1 day (Block end) |
| DI 19:00-21:00 | 2026-03-24 | offset_weeks=1 → Online follow-up |

---

## Example 3: Meta-Level — Event Type Template Hierarchy

**Context**: DASEi offers different formats for the same event (Block vs Tageskurs). How do templates inherit and specialize?

### Event Type Hierarchy (A1 Kreisanimation)

```
event.type: "A1 Kreisanimation" (abstract parent)
    │       Inherits from: Module "Einstiege ins Theaterspiel"
    │       unit_count: 22 UE (default)
    │
    ├── event.type: "A1 Kreisanimation (Block)"
    │       schedule_template: DO-SO + Online Nachbereitung
    │       unit_count: 22 UE
    │       location_hint: "Burgstallmühle or Kineo"
    │
    └── event.type: "A1 Kreisanimation (Tageskurs)"
            schedule_template: SA 10:00-17:00 (single day)
            unit_count: 10 UE (reduced)
            location_hint: "Tanzerei Nürnberg"
```

### View: Event Type Configuration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Event Type: A1 Kreisanimation (Block)                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Template Hierarchy:                                                         │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │ Parent: A1 Kreisanimation (abstract)                                 │  │
│   │   Module: Einstiege ins Theaterspiel (A)                             │  │
│   │   └── Inherits: product_template_id, curriculum_refs                 │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│ Schedule Template:                                                          │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │ Pattern: Block (DO-SO + Online)                                      │  │
│   │ Total Hours: 22 UE                                                   │  │
│   │ Online Hours: 2 UE                                                   │  │
│   │ Venue Hours: 20 UE                                                   │  │
│   │                                                                      │  │
│   │ Session Preview:                                                     │  │
│   │   DO 19:00-21:00  Anreise/Einführung                                │  │
│   │   FR 09:00-18:00  Praxistag 1                                       │  │
│   │   SA 09:00-18:00  Praxistag 2                                       │  │
│   │   SO 09:00-15:00  Abschluss                                         │  │
│   │   DI 19:00-21:00  Online Nachbereitung (+1 Woche)                   │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│ Variant Settings:                                                           │
│   ☑️ Is bookable variant (not abstract)                                     │
│   ☐ Requires instructor assignment                                         │
│   ☑️ Auto-generate sessions on event create                                │
│   ☐ Allow manual session edits                                             │
│                                                                             │
│ [📋 Copy Template] [🔗 Create Event from This Type]                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### How Inheritance Works

```python
class EventType(models.Model):
    _inherit = 'event.type'
    
    template_parent_id = fields.Many2one(
        'event.type',
        string='Parent Template',
        help="Inherit base settings from parent"
    )
    
    schedule_template = fields.Json(
        string='Schedule Template'
    )
    
    @api.model
    def _get_effective_schedule_template(self):
        """Get schedule, falling back to parent if not set."""
        if self.schedule_template:
            return self.schedule_template
        elif self.template_parent_id:
            return self.template_parent_id._get_effective_schedule_template()
        return None
```

### Business Rule

| Variant | Inherits From | Overrides |
|---------|---------------|-----------|
| A1 Block | A1 Kreisanimation | schedule_template (DO-SO), unit_count=22 |
| A1 Tageskurs | A1 Kreisanimation | schedule_template (SA only), unit_count=10 |

All variants inherit `product_template_id`, `curriculum_structure` from the abstract parent. The module "Einstiege ins Theaterspiel" provides module-level milestones (certificate, consulting call).

---

## Source References

- ⚙️ `crearis/models/schedule_mixin.py` — Parser that will consume templates
- [workflow_email_templates](../_meta/Whitepaper/workflow_email_templates.md) — Email patterns
- [grundkurs_pricing_report](grundkurs_pricing_report.md) — Course/Module/Event structure
- Karo's journey: `agenda_extended_journeys.md`
