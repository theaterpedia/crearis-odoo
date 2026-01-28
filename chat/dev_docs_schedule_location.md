# Schedule & Location System

> Developer documentation for the crearis schedule parsing and location management system.
> 
> **Module:** `crearis` (core)  
> **Status:** Implemented (parser), Partially Implemented (config), TBD (views)  
> **Last Updated:** 2026-01-28

---

## Overview

The schedule system provides structured parsing of free-text event schedules into JSONB format, enabling:

- **Hybrid event detection** - Identify events with both online and venue sessions
- **Online session tracking** - Hours, dates, and conference provider integration
- **Location management** - Map shortcodes to venues, support per-company configuration
- **Reporting** - Stored computed fields for filtering and aggregation

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      event.event                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              event.schedule.mixin                    │   │
│  │  • schedule_data (JSONB)                            │   │
│  │  • schedule_raw (Text)                              │   │
│  │  • has_online_sessions, total_hours, etc.          │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     res.company                             │
│  • schedule_shortcodes (JSONB)                             │
│  • schedule_locale ('de' | 'en')                           │
│  • online_provider ('msteams' | 'zoom' | 'jitsi')          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   ScheduleParser                            │
│  Pure Python class for parsing schedule text               │
│  • Weekday codes (DE: MO-SO, EN: MON-SUN)                  │
│  • Time ranges (HH:MM-HH:MM)                               │
│  • Shortcodes (_online_, _VENUE_, _VENUE:ROOM_)            │
│  • Section headers (online:, München:)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### 1. Parse a Schedule (Shell Example)

```python
from crearis.models.schedule_mixin import ScheduleParser

# Basic parsing with defaults
parser = ScheduleParser()
result = parser.parse("""
online:
FR 18:00-20:00
München:
SA 09:30-18:30
SO 09:00-15:00
online:
DI 18:00-21:00
""")

print(result['summary'])
# {'total_hours': 18.5, 'online_hours': 5.0, 'venue_hours': 13.5, 
#  'has_online': True, 'session_count': 4, 'online_session_count': 2}
```

### 2. Use Shortcodes

```python
# DASEi company shortcodes
shortcodes = {
    '_online_': {'type': 'online', 'name': 'Online'},
    '_TANZEREI_': {'type': 'venue', 'raum_id': 8, 'name': 'Tanzerei Fürth'},
    '_KINEO_': {'type': 'venue', 'raum_id': 17, 'name': 'Kineo München'},
    '_KHG_': {'type': 'venue', 'raum_id': 4, 'name': 'KHG München'},
}

parser = ScheduleParser(locale='de', shortcodes=shortcodes)
result = parser.parse("SA 09:00-18:00 _TANZEREI_")

print(result['sessions'][0])
# {'day': 'SAT', 'start': '09:00', 'end': '18:00', 
#  'type': 'venue', 'location_hint': 'Tanzerei Fürth', ...}
```

### 3. Parse with Date Context

```python
from datetime import date

# When event dates are known, weekdays resolve to specific dates
result = parser.parse(
    "FR 18:00-20:00 _online_\nSA 09:00-18:00 _TANZEREI_",
    date_begin=date(2026, 3, 13),  # Friday
    date_end=date(2026, 3, 15)     # Sunday
)

print(result['sessions'][0]['date'])  # '2026-03-13'
print(result['sessions'][1]['date'])  # '2026-03-14'
```

---

## Schedule Text Format

### Supported Patterns

| Pattern | Example | Description |
|---------|---------|-------------|
| Weekday + Time | `FR 18:00-20:00` | Basic time slot |
| Weekday + Date + Time | `FR 24.6 18:00-20:00` | With explicit date |
| Time + Shortcode | `SA 09:00-18:00 _TANZEREI_` | Venue shortcode |
| Time + online | `DI 18:00-21:00 online` | Online marker |
| Section header | `online:` or `München:` | Sets context for following lines |

### Weekday Codes

| German (default) | English | Normalized |
|-----------------|---------|------------|
| MO | MON | MON |
| DI | TUE | TUE |
| MI | WED | WED |
| DO | THU | THU |
| FR | FRI | FRI |
| SA | SAT | SAT |
| SO | SUN | SUN |

### Date Formats

| Locale | Format | Example |
|--------|--------|---------|
| `de` (default) | DD.MM or DD.MM.YY | `24.6` or `24.6.26` |
| `en` | MM/DD or MM/DD/YY | `6/24` or `6/24/26` (TBD) |

### Shortcode Format

```
_SHORTCODE_           → Maps to venue/online config
_SHORTCODE:ROOM_      → Maps to venue + specific room (TBD)
```

**Reserved shortcodes:**
- `_online_` - Always maps to online session type

**Special shortcodes (generate sessions programmatically):**
- `_anfrage_` - Times on request (generates placeholder sessions)
- `_individuell_` - Individual appointments (single placeholder + notes)
- `_reihe_` - Weekly series (parses series info, full generation TBD)

---

## Special Shortcodes

These shortcodes have special behavior - they generate sessions programmatically rather than parsing text patterns.

### `_anfrage_` - Times on Request

For events where times are "auf Anfrage" (on request).

**Input:** `_anfrage_`  
**Behavior:**
- Generates one session per day in event date range
- Each session: 09:00-18:00 (9 hours placeholder)
- Adds `issue_schedule` flag for follow-up
- **Validation:** Errors if date range > 14 days

**Example:**
```python
parser.parse('_anfrage_', date_begin=date(2026, 3, 15), date_end=date(2026, 3, 17))
# Result: 3 sessions (15th, 16th, 17th), each 09:00-18:00
# Flags: ['issue_schedule']
```

**Use cases:** "Zeiten auf Anfrage", "auf AnFRage", "times on request"

---

### `_individuell_` - Individual Appointments

For events with individual/flexible appointment scheduling.

**Input:** `_individuell_ | <description>`  
**Behavior:**
- Creates single placeholder session on first day: 09:00-09:00 (0 hours)
- Preserves original description in `schedule_data.notes`
- Session type: `individual`

**Example:**
```python
parser.parse('_individuell_ | individueller (Telefon-) Termin', 
             date_begin=date(2026, 4, 1), date_end=date(2026, 4, 30))
# Result: 1 session on 2026-04-01, 09:00-09:00
# Notes: "individueller (Telefon-) Termin"
```

**Use cases:** "individueller Prozess", "individueller Termin", "Eigenleistung", "Coaching-Kleingruppen"

---

### `_reihe_` - Weekly Series (Terminreihe)

For recurring weekly sessions (evening courses, etc.).

**Input:** `_reihe_ N Termine WD HH:MM-HH:MM [_online_]`  
**Behavior:**
- Parses series info (count, weekday, times, type)
- Creates single placeholder session for first occurrence
- Stores `series_info` in schedule_data for future expansion
- Adds `series_pending` flag

**Example:**
```python
parser.parse('_reihe_ 6 Termine DI 18:00-21:00 _online_',
             date_begin=date(2026, 2, 3), date_end=date(2026, 3, 10))
# Result: 1 session on 2026-02-03, 18:00-21:00, type=online
# series_info: {num_sessions: 6, weekday: 'DI', start: '18:00', end: '21:00', type: 'online'}
# Flags: ['series_pending']
```

**Note:** Full series generation (creating N weekly sessions) is planned for next sprint. Current implementation only parses and stores the series info.

**Use cases:** "4 aus 6 Abende a 3h online", "5 Abende a 3h online"

---

## JSONB Schema: schedule_data

```json
{
  "$schema": "schedule_data_v1",
  "source": "parsed",
  "raw_text": "FR 18:00-20:00 _online_\nSA 09:00-18:00...",
  
  "sessions": [
    {
      "day": "FRI",
      "date": "2026-03-13",
      "start": "18:00",
      "end": "20:00",
      "duration_h": 2.0,
      "type": "online",
      "location_hint": null,
      "room": null,
      "notes": null
    },
    {
      "day": "SAT",
      "date": "2026-03-14",
      "start": "09:00",
      "end": "18:00",
      "duration_h": 9.0,
      "type": "venue",
      "location_hint": "Tanzerei Fürth",
      "room": null,
      "notes": null
    }
  ],
  
  "summary": {
    "total_hours": 11.0,
    "online_hours": 2.0,
    "venue_hours": 9.0,
    "has_online": true,
    "session_count": 2,
    "online_session_count": 1
  },
  
  "unparsed_notes": []
}
```

### Session Types

| Type | Description | Example |
|------|-------------|---------|
| `online` | Video conference session | `_online_` shortcode or `online` keyword |
| `venue` | Physical location | Venue shortcode or section header |
| `individual` | Individual appointment | `_individuell_` shortcode |
| `tbd` | Location to be determined | (TBD - future) |

### Schedule Sources

| Source | Description |
|--------|-------------|
| `parsed` | Standard text parsing |
| `shortcode:anfrage` | Generated by `_anfrage_` |
| `shortcode:individuell` | Generated by `_individuell_` |
| `shortcode:reihe` | Generated by `_reihe_` |

### Flags

| Flag | Description |
|------|-------------|
| `issue_schedule` | Needs manual follow-up (from `_anfrage_`) |
| `series_pending` | Series expansion not yet implemented (from `_reihe_`) |
| `range_exceeded` | Date range validation failed |

---

## Per-Company Configuration

### Company Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `schedule_shortcodes` | JSON | `{'_online_': {...}}` | Shortcode → config mapping |
| `schedule_locale` | Selection | `'de'` | Parsing locale (weekdays, dates) |
| `online_provider` | Selection | `'msteams'` | Default video conference provider |

### Setting Up Shortcodes

**Via Shell:**
```python
company = env['res.company'].browse(11)  # DASEi
company.schedule_shortcodes = {
    '_online_': {'type': 'online', 'name': 'Online'},
    '_TANZEREI_': {'type': 'venue', 'raum_id': 8, 'name': 'Tanzerei Fürth'},
    '_KINEO_': {'type': 'venue', 'raum_id': 17, 'name': 'Kineo München'},
    '_KHG_': {'type': 'venue', 'raum_id': 4, 'name': 'KHG München'},
    '_KOFFERFABRIK_': {'type': 'venue', 'raum_id': 9, 'name': 'Kofferfabrik Fürth'},
    '_BURGSTALLMUEHLE_': {'type': 'venue', 'raum_id': 6, 'name': 'Burgstallmühle'},
}
company.schedule_locale = 'de'
company.online_provider = 'msteams'
env.cr.commit()
```

**Via Config View (TBD):**

See [Schedule Config View](#schedule-config-view-tbd) below.

### Shortcode Config Structure

```json
{
  "_VENUE_": {
    "type": "online|venue",
    "name": "Display name for UI",
    "raum_id": 8,              // Optional: SharePoint plan_raeume ID
    "partner_id": 123,         // Optional: Odoo res.partner ID (TBD)
    "default_room": "R1"       // Optional: Default room code (TBD)
  }
}
```

---

## Event Integration

### Mixin Usage

Events inherit `event.schedule.mixin` to gain schedule capabilities:

```python
class Event(models.Model):
    _name = 'event.event'
    _inherit = ['event.event', 'event.schedule.mixin']
```

### Computed Fields

| Field | Type | Stored | Description |
|-------|------|--------|-------------|
| `schedule_data` | JSON | Yes | Full parsed schedule |
| `schedule_raw` | Text | Yes | Original text input |
| `has_online_sessions` | Boolean | Yes | Has any online sessions |
| `total_hours` | Float | Yes | Sum of all session hours |
| `online_hours` | Float | Yes | Sum of online session hours |
| `venue_hours` | Float | Yes | Sum of venue session hours |
| `session_count` | Integer | Yes | Number of sessions |

### Example: Filter Hybrid Events

```python
# Find all events with online sessions
hybrid_events = env['event.event'].search([
    ('has_online_sessions', '=', True),
    ('company_id', '=', 11),
])

# Find events with more than 4 hours online
heavy_online = env['event.event'].search([
    ('online_hours', '>', 4.0),
])
```

### Example: Parse on Sync

```python
# In sync_engine.py - after fetching sp_textinfo
for event in events:
    if event.sp_textinfo:
        schedule_data = event.parse_schedule_text(
            event.sp_textinfo,
            date_begin=event.date_begin,
            date_end=event.date_end,
            company=event.company_id
        )
        if schedule_data:
            event.schedule_data = schedule_data
            event.schedule_raw = event.sp_textinfo
```

---

## Recommended Strategies

### Strategy 1: Shortcode Migration

For existing data with legacy format (section headers), migrate incrementally:

1. **Keep legacy parsing** - Parser handles both `online:` headers and `_online_` shortcodes
2. **Update new entries** - Use shortcodes for new schedule text
3. **Batch update** - Export → regex replace → re-import (SharePoint bulk update)

### Strategy 2: Venue Standardization

Map all physical venues to shortcodes:

```python
# Step 1: Export plan_raeume
raeume = sync.export_raeume_full(company)

# Step 2: Create shortcode for each venue (Type A)
shortcodes = {'_online_': {'type': 'online'}}
for r in raeume:
    if r['type'] == 'A':  # Physical venue
        code = r['name'].upper().replace(' ', '').replace('-', '')[:12]
        shortcodes[f'_{code}_'] = {
            'type': 'venue',
            'raum_id': r['id'],
            'name': r['name'],
        }

company.schedule_shortcodes = shortcodes
```

### Strategy 3: Multi-Week Event Handling

Events spanning > 28 days or with "N Termine" pattern should be excluded:

```python
# In sync logic
if event.is_multi_week_event():
    _logger.info("Skipping multi-week event %s - needs sessions feature", event.name)
    continue
```

---

## Views & UI (TBD)

### Schedule Config View (TBD)

**Location:** Settings → Technical → Schedule Configuration

**Features:**
- Edit shortcodes as key-value table
- Test parser with sample text
- Preview parsed result

**Wireframe:**
```
┌─────────────────────────────────────────────────────────────┐
│ Schedule Configuration                    [Company: DASEi]  │
├─────────────────────────────────────────────────────────────┤
│ Locale: [German ▼]     Online Provider: [MS Teams ▼]       │
├─────────────────────────────────────────────────────────────┤
│ Shortcodes:                                                 │
│ ┌──────────────┬────────┬────────────────────┬───────────┐ │
│ │ Code         │ Type   │ Name               │ Raum ID   │ │
│ ├──────────────┼────────┼────────────────────┼───────────┤ │
│ │ _online_     │ online │ Online             │           │ │
│ │ _TANZEREI_   │ venue  │ Tanzerei Fürth     │ 8         │ │
│ │ _KINEO_      │ venue  │ Kineo München      │ 17        │ │
│ │ _KHG_        │ venue  │ KHG München        │ 4         │ │
│ │ [+ Add]      │        │                    │           │ │
│ └──────────────┴────────┴────────────────────┴───────────┘ │
├─────────────────────────────────────────────────────────────┤
│ Test Parser:                                                │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ FR 18:00-20:00 _online_                                 │ │
│ │ SA 09:00-18:00 _TANZEREI_                               │ │
│ └─────────────────────────────────────────────────────────┘ │
│ [Parse]                                                     │
│                                                             │
│ Result: 2 sessions, 11h total (2h online, 9h venue) ✓      │
└─────────────────────────────────────────────────────────────┘
```

### Event Schedule Tab (TBD)

**Location:** Event form → "Schedule" tab

**Features:**
- Display parsed sessions in table
- Edit schedule_raw with live preview
- "Re-parse" button
- Online session highlighting

**Wireframe:**
```
┌─────────────────────────────────────────────────────────────┐
│ Event: D2 Werkstatt Regie                                   │
│ [General] [Schedule] [Registrations] [...]                  │
├─────────────────────────────────────────────────────────────┤
│ Schedule Text:                          [Re-parse]          │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ FR 18:00-20:00 _online_                                 │ │
│ │ SA 09:00-18:00 _TANZEREI_                               │ │
│ │ SO 09:00-15:00 _TANZEREI_                               │ │
│ │ DI 18:00-21:00 _online_                                 │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ Parsed Sessions:                                            │
│ ┌─────┬────────────┬─────────────┬────────┬───────────────┐ │
│ │ Day │ Date       │ Time        │ Hours  │ Location      │ │
│ ├─────┼────────────┼─────────────┼────────┼───────────────┤ │
│ │ 🌐 FRI │ 2026-03-13 │ 18:00-20:00 │ 2.0  │ Online       │ │
│ │ 📍 SAT │ 2026-03-14 │ 09:00-18:00 │ 9.0  │ Tanzerei     │ │
│ │ 📍 SUN │ 2026-03-15 │ 09:00-15:00 │ 6.0  │ Tanzerei     │ │
│ │ 🌐 TUE │ 2026-03-17 │ 18:00-21:00 │ 3.0  │ Online       │ │
│ └─────┴────────────┴─────────────┴────────┴───────────────┘ │
│                                                             │
│ Summary: 20h total | 5h online | 15h venue | 4 sessions    │
└─────────────────────────────────────────────────────────────┘
```

### Online Sessions View (TBD)

**Location:** Events → Online Sessions

**Features:**
- List all online sessions across events
- Group by date/week
- Filter by company, date range
- Action: "Create conference link" (future)

**Wireframe:**
```
┌─────────────────────────────────────────────────────────────┐
│ Online Sessions                           [This Week ▼]     │
├─────────────────────────────────────────────────────────────┤
│ ┌────────────┬──────────────┬─────────────┬───────────────┐ │
│ │ Date       │ Time         │ Event       │ Status        │ │
│ ├────────────┼──────────────┼─────────────┼───────────────┤ │
│ │ 2026-03-13 │ 18:00-20:00  │ D2 Werkst.  │ No link       │ │
│ │ 2026-03-17 │ 18:00-21:00  │ D2 Werkst.  │ No link       │ │
│ │ 2026-03-20 │ 18:00-20:00  │ A0 Einführ. │ Teams ✓       │ │
│ └────────────┴──────────────┴─────────────┴───────────────┘ │
│                                                             │
│ This week: 3 online sessions, 7 hours                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Utilities

### Shell Commands

```python
# Parse all events with sp_textinfo
company = env['res.company'].browse(11)
from crearis.models.schedule_mixin import ScheduleParser

parser = ScheduleParser(
    locale=company.schedule_locale or 'de',
    shortcodes=company.schedule_shortcodes or {}
)

events = env['event.event'].search([
    ('company_id', '=', company.id),
    ('sp_textinfo', '!=', False),
])

for event in events:
    if event.is_multi_week_event():
        continue
    result = parser.parse(event.sp_textinfo, event.date_begin, event.date_end)
    if result:
        event.schedule_data = result
        event.schedule_raw = event.sp_textinfo

env.cr.commit()
```

### Diagnostic: Online Hours Report

```python
# Get online hours summary per month
from collections import defaultdict

events = env['event.event'].search([
    ('company_id', '=', 11),
    ('has_online_sessions', '=', True),
])

by_month = defaultdict(lambda: {'events': 0, 'online_hours': 0})
for e in events:
    if e.date_begin:
        key = e.date_begin.strftime('%Y-%m')
        by_month[key]['events'] += 1
        by_month[key]['online_hours'] += e.online_hours

for month, data in sorted(by_month.items()):
    print(f"{month}: {data['events']} events, {data['online_hours']:.1f}h online")
```

---

## Testing

### Run Standalone Tests

```bash
cd /home/persona/crearis/odoo/dev/crearis-odoo
python3 crearis/tests/test_schedule_parser.py
```

### Test in Odoo Shell

```python
from crearis.models.schedule_mixin import ScheduleParser

# Test company config
company = env['res.company'].browse(11)
print(f"Locale: {company.schedule_locale}")
print(f"Shortcodes: {company.schedule_shortcodes}")

# Test parsing
parser = ScheduleParser(
    locale=company.schedule_locale or 'de',
    shortcodes=company.schedule_shortcodes or {}
)

test_text = """
FR 18:00-20:00 _online_
SA 09:00-18:00 _TANZEREI_
"""
result = parser.parse(test_text)
print(f"Sessions: {len(result['sessions'])}")
print(f"Summary: {result['summary']}")
```

---

## Related Files

| File | Description |
|------|-------------|
| [crearis/models/schedule_mixin.py](../crearis/models/schedule_mixin.py) | Core mixin and parser |
| [crearis/models/res_company.py](../crearis/models/res_company.py) | Company config fields |
| [crearis/tests/test_schedule_parser.py](../crearis/tests/test_schedule_parser.py) | Standalone tests |
| [chat/2026-01-28_research_event_tracks_hybrid.md](2026-01-28_research_event_tracks_hybrid.md) | Research & JSONB schema |
| [chat/ref_sharepoint_raeume.md](ref_sharepoint_raeume.md) | Location reference data |

---

## TBD Items

| Item | Priority | Sprint |
|------|----------|--------|
| Schedule Config View | Medium | Next |
| Event Schedule Tab | Medium | Next |
| Online Sessions View | Medium | Next |
| `_reihe_` full series generation | Medium | Next |
| Videocall tracks for `_individuell_` | Low | Wishlist |
| Room support (_VENUE:ROOM_) | Low | Future |
| English date format (MM/DD) | Low | Future |
| Conference link creation | Low | Future |
| SharePoint write-back (oschedule_data) | Medium | L19 |

---

## Changelog

- **2026-01-28**: Initial implementation
  - ScheduleParser class with DE/EN weekday support
  - Company config fields (shortcodes, locale, online_provider)
  - event.schedule.mixin with computed summary fields
  - Standalone test suite
