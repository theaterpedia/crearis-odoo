# Naming Analysis: Session vs Track vs Timeslot vs Block

*Created: 2026-01-28*  
*Context: Q2 - Learning from existing implementations and choosing terminology*

---

## Existing Implementations Analysis

### 1. OCA `event_session` Module (Heavy Framework)

**Source:** `.external/event/event_session/`

**Architecture:**
```python
class EventSession(models.Model):
    _name = "event.session"
    _inherits = {"event.event": "event_id"}  # ← Delegation inheritance!
```

**Key Insight:** Sessions **inherit** from events via `_inherits`. A session IS a mini-event.

**Features:**
- Full event lifecycle (`date_begin`, `date_end`, `stage_id`, `kanban_state`)
- Own registrations (`registration_ids` with `session_id`)
- Own seat tracking (`seats_reserved`, `seats_available`, `seats_used`)
- Mail scheduling per session (`event.mail.session`)
- Session update propagation (`session_update` = this/subsequent/all)
- ICS calendar export per session

**Usage Pattern:**
```
event.event (parent)
  └── event.session (child, inherits event.event)
        └── event.registration (links to session)
```

**Verdict:** This is a **heavyweight framework** for events with independent sessions that have:
- Separate registration/ticketing
- Separate capacity management
- Separate mail campaigns
- Separate stages/workflows

**Example Use Case:** "Summer Workshop Series" with 8 independent sessions, each bookable separately.

---

### 2. OCA `event_session_timeslot` Model

**Source:** `.external/event/event_session/models/event_session_timeslot.py`

**Architecture:**
```python
class EventSessionTimeslot(models.Model):
    _name = "event.session.timeslot"
    _description = "Event Session Timeslot"
    _order = "time"
    
    time = fields.Float(required=True)  # 0.0 to 24.0
```

**Purpose:** Pre-defined time slots for quick session creation.

**Example:** "18:00", "09:30", "14:00" - reusable across events.

**Verdict:** This is a **configuration helper**, not a session model. It defines available time slots, not actual sessions.

---

### 3. Odoo Core `event.track` Model

**Source:** `odoo/addons/website_event_track/`

**Architecture:**
```python
class Track(models.Model):
    _name = "event.track"
    
    event_id = fields.Many2one('event.event', required=True)
    location_id = fields.Many2one('event.track.location')
    partner_id = fields.Many2one('res.partner')  # Speaker
    stage_id = fields.Many2one('event.track.stage')
    date = fields.Datetime('Track Date')
    duration = fields.Float('Duration', default=0.5)
```

**Key Insight:** Tracks are for **conference-style events** with:
- Multiple speakers
- Multiple rooms/locations
- Talk proposals & review workflow
- Website agenda display

**Features:**
- Speaker management (`partner_id`)
- Location per track (`location_id` → `event.track.location`)
- Tags for categorization
- Stage workflow (proposal → confirmed → presented)
- Website integration (agenda, track detail pages)

**Verdict:** This is for **conferences** where each track is a talk/presentation with a speaker.

---

## Comparison Table

| Aspect | `event.session` | `event.track` | Our Need |
|--------|----------------|---------------|----------|
| **Inheritance** | `_inherits` event.event | Standalone model | Standalone |
| **Registrations** | Per-session | Per-event | Per-event |
| **Speakers** | No | Yes (`partner_id`) | No |
| **Locations** | Via parent event | Per-track | Per-session |
| **Capacity** | Per-session | Per-event | Per-event |
| **Workflow** | Yes (stages) | Yes (stages) | No (display only) |
| **Website** | No | Yes (agenda) | Future |
| **Primary Use** | Multi-session courses | Conferences | Hybrid schedule display |

---

## Our Requirements (Eleanora + GraphQL)

What we actually need:

1. **Display parsed schedule** as rows in form view
2. **List all online sessions** across events (searchable)
3. **Store conference URLs** per session
4. **GraphQL exposure** of session details
5. **No separate registration** per session
6. **No separate capacity** per session
7. **No workflow/stages** per session

**Verdict:** Neither `event.session` nor `event.track` fits perfectly.

---

## Naming Options Analysis

### Option A: `event.session.line`

**Rationale:** "Session" is the natural word for a time slot within an event. "Line" indicates it's a child record (like `sale.order.line`).

**Pros:**
- Intuitive naming
- Follows Odoo patterns (`*.line` for child records)
- "Session" is what users say: "the Friday session", "online sessions"

**Cons:**
- Conflicts with OCA `event.session` (heavyweight)
- Might confuse developers familiar with OCA module

### Option B: `event.schedule.line`

**Rationale:** These are "schedule" entries, not independent sessions.

**Pros:**
- Matches our field name `schedule_data`
- No conflict with OCA
- Clear it's about scheduling, not booking

**Cons:**
- "Schedule line" sounds odd in English
- Users say "session", not "schedule entry"

### Option C: `event.track.line`

**Rationale:** Align with Odoo's `event.track` terminology.

**Pros:**
- Aligns with existing Odoo vocabulary
- Could integrate with `event.track.location`

**Cons:**
- `event.track` implies speakers/talks
- Confusing: why "track line" instead of "track"?

### Option D: `event.timeslot`

**Rationale:** Borrowed from OCA's `event.session.timeslot`.

**Pros:**
- Clear meaning: a time slot within an event
- No conflict with existing models

**Cons:**
- Sounds like configuration, not data
- OCA uses it for templates, not actual sessions

### Option E: `event.block`

**Rationale:** A "block" of time - neutral term.

**Pros:**
- Fresh terminology, no conflicts
- Clear it's a time segment

**Cons:**
- Not intuitive ("what's a block?")
- No precedent in Odoo/OCA

---

## Recommendation: `event.session.line`

**Reasoning:**

1. **Natural language:** "Session" is what everyone calls it
2. **Odoo pattern:** `*.line` for child records of a parent
3. **Differentiation:** Adding `.line` distinguishes from OCA's `event.session`
4. **Future-proof:** If we later need full OCA sessions, they coexist

**Model Naming:**
```python
class EventSessionLine(models.Model):
    _name = 'event.session.line'
    _description = 'Event Session Line'
```

**Related Naming:**
- `session_line_ids` on event.event
- `action_online_session_lines` for menu action
- `view_event_session_line_tree` for views

---

## Alignment Strategy

### Don't: Extend OCA `event.session`

**Why not:**
- We don't need per-session registration
- We don't need per-session capacity
- The `_inherits` pattern is overkill
- Would require installing the module

### Don't: Extend `event.track`

**Why not:**
- We don't need speakers
- We don't need proposal workflow
- Track implies conference structure

### Do: Create Lightweight `event.session.line`

**Characteristics:**
- Simple O2M child of `event.event`
- No separate registration
- No separate workflow
- Synced from `schedule_data` JSONB
- Display + search purpose only

### Do: Keep Promotion Path Open

**Future option:**
```python
def action_create_tracks(self):
    """Promote session lines to full event.track records"""
    for line in self.session_line_ids:
        self.env['event.track'].create({
            'event_id': self.id,
            'name': f"{line.day} {line.start}-{line.end}",
            'date': line.date,
            'duration': line.duration_h,
            'location_id': self._resolve_track_location(line),
        })
```

This allows progressive enhancement without committing to heavy frameworks.

---

## Coexistence Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         event.event                                 │
├─────────────────────────────────────────────────────────────────────┤
│                              │                                      │
│    ┌─────────────────────────┼─────────────────────────┐           │
│    │                         │                         │           │
│    ▼                         ▼                         ▼           │
│ schedule_data           session_line_ids          track_ids       │
│   (JSONB)               (O2M lightweight)        (O2M standard)   │
│                                                                     │
│ ┌─────────────┐        ┌──────────────────┐    ┌────────────────┐ │
│ │ sessions: [ │        │ event.session.   │    │ event.track    │ │
│ │   {date,    │  sync  │ line             │    │ (speakers,     │ │
│ │    start,   │ ─────▶ │ (display only)   │    │  proposals,    │ │
│ │    type,    │        │                  │    │  website)      │ │
│ │    url}     │        │                  │    │                │ │
│ │ ]           │        │                  │    │                │ │
│ └─────────────┘        └──────────────────┘    └────────────────┘ │
│                               │                        ▲           │
│                               │ promote               │           │
│                               └────────────────────────┘           │
└─────────────────────────────────────────────────────────────────────┘

OCA event.session (NOT USED)
┌─────────────────────────────────────────────────────────────────────┐
│ _inherits event.event - heavy framework for independent sessions   │
│ (separate registrations, separate capacity, separate mail)         │
│ → NOT what we need                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Summary Decision

| Question | Answer |
|----------|--------|
| **Model name** | `event.session.line` |
| **Align with OCA event.session?** | No - too heavy |
| **Align with event.track?** | No - different purpose |
| **Alter existing concepts?** | No - keep separate |
| **Coexist?** | Yes - promotion path to tracks |

---

*Ready for discussion.*
