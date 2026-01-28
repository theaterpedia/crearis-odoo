# Research: Event Tracks, Seminarzeiten & Hybrid Events

*Created: 2026-01-28*  
*Context: Location Management Action Plan*

---

## 1. User Context: Eleanora Allerdings

```
User ID: 72
Partner ID: 1078
Login: eleanora.allerdings@dasei.eu
Name: Eleanora Allerdings
City: Nürnberg
```

**Role:** Location & Room Manager for DASEi  
**Workflow:** Sends booking overviews every 4 months to location partners:
- München: Institut Kineo (Eva Nikolait), Eine-Welt-Haus (Nelly Usaceva)
- Nürnberg: Tanzerei (Alexander Blanke), Burgstallmühle (Britta)

---

## 2. Module Architecture

```
crearis (base)
  └── crearis_agenda (SP sync engine)
        └── agenda_dasei (DASEi-specific extensions)
              └── crearis_event_package (event packages/products)
```

### crearis (base module)

**Purpose:** Core event management + website infrastructure  
**Key features:**
- Extended `event.track.location` with provider_id, type, MS Teams fields
- Extended `res.partner` with `is_location_provider`, version tracking
- Event stages, event types
- Website/domain management

**Depends:** website_event_track, event_session, partner_event, etc.

### crearis_agenda

**Purpose:** SharePoint sync engine  
**Key features:**
- Sync event types from `plan_veranstaltungscodes`
- Sync events from `plan_veranstaltungen`
- Three sync levels: init, slave, master
- Template application on event creation

**Depends:** crearis, event

### agenda_dasei

**Purpose:** DASEi-specific extensions  
**Key features:**
- Partner status → domaincode mapping
- Course sync (plan_kursteilnehmer)
- Event registration sync (plan_veranstaltungsteilnehmer)
- DASEi websites (dasei0/1/2/3)
- Location tags (just added!)

**Depends:** crearis_agenda, crearis_event_package

---

## 3. SharePoint plan_seminarzeiten

**List GUID:** `6BBE92C5-82C5-40E7-8C5F-D6CB3018EC23`

**Known columns:**
| SP Field | Description |
|----------|-------------|
| `Title` | Schedule template name |
| `Feld1` | Short schedule description |
| `Feld12` | Detailed schedule text (multiline) |

**Usage in sync:**
```python
# In _map_event_from_sp():
schedule_text = sp_fields.get('oschedule') or ''
if not schedule_text:
    schedule_text = sp_fields.get('Feld11') or ''  # Event's custom memo
if not schedule_text:
    seminarplan_id = sp_fields.get('SeminarplanLookupId')
    if seminarplan_id and str(seminarplan_id) != '1':
        schedule_text = self._fetch_seminarplan_text(company, seminarplan_id)
```

**Priority:**
1. `oschedule` (Odoo write-back)
2. `Feld11` (event's Seminarplan_Memo - custom override)
3. `plan_seminarzeiten` template via `SeminarplanLookupId`

---

## 4. Event Schedule Fields

On SharePoint `plan_veranstaltungen`:
| Field | Internal Name | Description |
|-------|---------------|-------------|
| Seminarplan | `SeminarplanLookupId` | Lookup to plan_seminarzeiten |
| Seminarplan_Memo | `Feld11` | Custom schedule text override |
| Start | `Feld17` | Event start datetime |
| Ende | `Feld18` | Event end datetime |

**Key insight:** When `SeminarplanLookupId = 1`, it means "use custom memo" (Feld11).

---

## 5. The Hybrid Event Problem

### Pattern: ~50% of DASEi events are hybrid

Typical structure:
```
FR evening: Online session (intro)
SA full day: In-presence at venue
SO morning: In-presence at venue  
DI evening: Online session (follow-up)
```

### Current Data Model Pain Points

1. **Single location per event:** Event has `address_id` but hybrid needs both online + venue
2. **Text-based schedule:** `Seminarplan_Memo` is free-form text - parsing nightmare
3. **No track breakdown:** Multi-day event stored as one record with date_begin → date_end
4. **Hidden online sessions:** Get overlooked in booking reports

### Example (hypothetical):

```
Event: "Grundkurs Modul A - März 2026"
Date: 2026-03-13 to 2026-03-17
Location: Nbg: Tanzerei (raum_id=8)

Seminarplan_Memo:
  FR 13.03. 18:00-20:00 online (MS Teams)
  SA 14.03. 09:00-18:00 Tanzerei
  SO 15.03. 09:00-14:00 Tanzerei
  DI 17.03. 18:00-20:00 online (MS Teams)
```

**Problems:**
- Report says "Tanzerei" but 2 sessions are actually online
- Instructor may have conflicts on Tue if not tracked
- Participants need different join links for different days

---

## 6. Odoo event.track Model

Standard Odoo `event.track` (website_event_track module):

```python
class Track(models.Model):
    _name = "event.track"
    
    name = fields.Char('Title', required=True, translate=True)
    event_id = fields.Many2one('event.event', 'Event', required=True)
    location_id = fields.Many2one('event.track.location', 'Location')
    date = fields.Datetime('Track Date')
    date_end = fields.Datetime('Track End Date', compute='_compute_end_date')
    duration = fields.Float('Duration', default=0.5)
    partner_id = fields.Many2one('res.partner', 'Contact')  # Speaker
    description = fields.Html(translate=html_translate)
    stage_id = fields.Many2one('event.track.stage', 'Stage')
    tag_ids = fields.Many2many('event.track.tag', 'Tags')
```

**Key features:**
- Each track has its own `location_id`
- Own datetime (date, date_end, duration)
- Can have different speaker/contact
- Has stage workflow

### crearis extension to event.track.location

```python
class Location(models.Model):
    _inherit = "event.track.location"
    
    provider_id = fields.Many2one('res.partner', 'Address/Provider',
        domain=[('is_location_provider','=',True)])
    type = fields.Selection([
        ("location.venue", "venue"),
        ("location.office", "office"),
        ("location.nature", "nature"),
        ("location.street", "street"),
        ("space.msteams", "online (teams)"),
        ("space.jitsi", "online (jitsi)")
    ])
    is_default = fields.Boolean("Default Space?")
    site_id = fields.Char('MS Site ID')
    company_ids = fields.Many2many('res.company')
```

**This is already quite sophisticated!**
- Location can be physical venue OR online space type
- Links to res.partner (provider)
- Can configure MS Teams integration

---

## 7. Solution Architecture Options

### Option A: Parse text → tracks on sync

**Flow:**
1. SP sync brings event with `Seminarplan_Memo` text
2. Parsing logic extracts sessions: `{date, time, location_type, notes}`
3. Auto-create `event.track` records for each session
4. Each track gets appropriate `location_id` (venue or online space)

**Pros:** Structured data in Odoo  
**Cons:** Complex parsing, breaks on edge cases, SP remains unstructured

### Option B: GraphQL-driven parsing at display time

**Flow:**
1. SP sync brings event with raw `Seminarplan_Memo` as-is
2. Store in Odoo `schedule` field (text/JSONB)
3. GraphQL endpoint parses text → structured tracks JSON
4. VueJS client renders track cards with location icons

**Pros:** No destructive transformation, flexible parsing  
**Cons:** Doesn't help Eleanora's Odoo list view

### Option C: Hybrid - defaults + optional tracks

**Flow:**
1. Event sync stores `sp_raum_id`, `schedule` (text)
2. Default: No tracks created, event uses `address_id` 
3. On demand: "Break into tracks" wizard parses schedule → creates tracks
4. GraphQL serves both: simple events + track-based events

**Pros:** Progressive enhancement, works for legacy  
**Cons:** Two code paths to maintain

### Option D: JSONB-native schedule field

**Flow:**
1. Define `schedule_data` as JSONB on event
2. SP sync or parsing fills structured JSON:
   ```json
   {
     "tracks": [
       {"date": "2026-03-13", "time": "18:00", "duration": 2, "type": "online", "notes": "Intro"},
       {"date": "2026-03-14", "time": "09:00", "duration": 9, "type": "venue", "location_id": 8},
       ...
     ]
   }
   ```
3. Odoo displays from JSONB
4. GraphQL serves directly
5. Optional: hydrate to `event.track` records when needed

**Pros:** Best of both worlds, GraphQL-native  
**Cons:** Custom implementation, diverges from standard Odoo patterns

---

## 8. Questions for Hans → ANSWERED

### Q1: Parsing complexity
**A:** Reasonably structured. Better: define crearis-wide conventions!
- `_online_` marker convention
- Per-company config for online provider (MS Teams, Zoom, Jitsi)
- ~300 entries to standardize (1-2h work)
- Team + channel already known via product → adapter can auto-acquire conference

### Q2: Run diagnostics
**A:** Yes

### Q3: JSONB appetite
**A:** Full commitment!
- `schedule_data` JSONB stores parsed tracks
- Write-back to SharePoint as `oschedule_data`
- MS Access reads into details table
- Power Automate triggers actions from JSON

### Q4: Eleanora's view
**A:** Event-level with expand option
- Main: events with tags/flags ("has online sessions")
- Click-open-inspect for session details
- Special: "All online sessions" view (line-by-line across events)

### Q5: event.track.location status
**A:** Half-dormant
- Shows early thinking (1.5 years ago)
- Will refactor against event_package product concept
- Product already has team/channel info

---

## 9. Diagnostic Commands Added

```python
# Query plan_seminarzeiten templates
company = env['res.company'].browse(11)
data = env['crearis.agenda.sync'].export_seminarzeiten_full(company)

# Find hybrid events (online mentions in schedule)
hybrids = env['crearis.agenda.sync'].diagnose_hybrid_events(company, limit=100)
```

**Results (2026-01-28):**
- 9 schedule templates, 5 are hybrid (B, C, D1, D2, E)
- 288 hybrid events out of 960 scanned (30%)

---

## 11. JSONB Schema Draft: `schedule_data`

```json
{
  "$schema": "schedule_data_v1",
  "source": "parsed|manual|template",
  "template_id": 5,
  "raw_text": "FR 18:00-20:00 online\nSA 09:00-18:00...",
  
  "sessions": [
    {
      "day": "FR",
      "date": "2026-03-13",
      "start": "18:00",
      "end": "20:00",
      "duration_h": 2.0,
      "type": "online",
      "location_hint": null,
      "notes": null
    },
    {
      "day": "SA",
      "date": "2026-03-14",
      "start": "09:00",
      "end": "18:00",
      "duration_h": 9.0,
      "type": "venue",
      "location_hint": "Tanzerei",
      "notes": null
    },
    {
      "day": "SO",
      "date": "2026-03-15",
      "start": "09:00",
      "end": "15:00",
      "duration_h": 6.0,
      "type": "venue",
      "location_hint": null,
      "notes": null
    },
    {
      "day": "DI",
      "date": "2026-03-17",
      "start": "18:00",
      "end": "21:00",
      "duration_h": 3.0,
      "type": "online",
      "location_hint": null,
      "notes": null
    }
  ],
  
  "summary": {
    "total_hours": 20.0,
    "online_hours": 5.0,
    "venue_hours": 15.0,
    "has_online": true,
    "session_count": 4,
    "online_session_count": 2
  },
  
  "unparsed_notes": [
    "*Fr. Regie-Team A (2-3 Personen) schon ab 09:00 Uhr"
  ]
}
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `$schema` | string | Schema version for migrations |
| `source` | enum | `parsed` (auto), `manual` (user edited), `template` (from seminarzeiten) |
| `template_id` | int | SeminarplanLookupId if from template |
| `raw_text` | string | Original text for reference/debugging |
| `sessions[]` | array | Parsed session slots |
| `sessions[].day` | string | Day code: MO, DI, MI, DO, FR, SA, SO |
| `sessions[].date` | date | Resolved date (YYYY-MM-DD) |
| `sessions[].start` | time | Start time (HH:MM) |
| `sessions[].end` | time | End time (HH:MM) |
| `sessions[].duration_h` | float | Duration in hours |
| `sessions[].type` | enum | `online`, `venue`, `tbd` |
| `sessions[].location_hint` | string | Parsed location name if found |
| `sessions[].notes` | string | Attached notes for this session |
| `summary` | object | Computed aggregates |
| `unparsed_notes` | array | Lines that couldn't be parsed as sessions |

### Parsing Rules

1. **Section headers:** `online:`, `München:`, `NÜRNBERG:` → set context for following lines
2. **Time pattern:** `{DAY} [{DD.MM}] {HH:MM}-{HH:MM} [online|location]`
3. **Day codes:** MO, DI, MI, DO, FR, SA, SO (German)
4. **Online markers:** `online`, `ONLINE`, `Teams`, `Zoom`, `Web`
5. **Venue markers:** City names, venue codes (KHG, Kineo, Tanzerei, etc.)
6. **Notes:** Lines starting with `*` or not matching time pattern

### Date Resolution

Given event `date_begin` and `date_end`:
1. If session has explicit date (DD.MM) → use it
2. Else resolve by day code within event date range
3. If day appears multiple times → distribute across weeks

---

## 12. Shortcode Convention (Refined)

### Format Rule
Shortcodes are **only valid in time-slot format:**
```
{DAY} {HH:MM}-{HH:MM} _SHORTCODE_
```

**NOT automated:** Section headers like `online:`, `München:` (legacy, kept for display)

### Supported Shortcodes

| Shortcode | Type | Maps To | Example |
|-----------|------|---------|--------|
| `_online_` | online | Company's online_provider | `FR 18:00-20:00 _online_` |
| `_TANZEREI_` | venue | plan_raeume ID 8 | `SA 09:00-18:00 _TANZEREI_` |
| `_KINEO_` | venue | plan_raeume ID 17 | `SO 09:30-18:30 _KINEO_` |
| `_KHG_` | venue | plan_raeume ID 4 | `SA 09:00-18:00 _KHG_` |
| `_KOFFERFABRIK_` | venue | plan_raeume ID 9 | `MI 16:00-21:00 _KOFFERFABRIK_` |

### Room Extension (Future)
```
{DAY} {HH:MM}-{HH:MM} _VENUE:ROOM_
```
Example: `SA 09:00-18:00 _WELTHAUS:R1_`

Maps to:
- Venue → plan_raeume entry
- Room → tracks.location within venue (like Welthaus R1, R2, R3)

### Legacy Handling

| Legacy Format | Action |
|---------------|--------|
| `online:` section header | Display only, not parsed as shortcode |
| `München:` section header | → Tag "München (auf Anfrage)" + action required |
| `NÜRNBERG:` section header | → Tag "Nürnberg (auf Anfrage)" + action required |

### SharePoint Update Strategy
1. Export current Feld12 (Zeiten) values
2. Run regex replacement: `online\n{DAY}` → `{DAY} ... _online_`
3. Bulk update via Power Automate or direct API
4. Validate with `diagnose_hybrid_events()` before/after

---

## 13. Multi-Week Events (Out of Scope)

### Problem
Some events span multiple weeks with enumerated sessions:
```
8 Termine online je 3h DI 18:00-21:00
17.9.24, 24.9.24, 1.10.24, 15.10.24, 5.11.24, 19.11.24, 26.11.24, 17.12.24
```

### Current Decision
**Exclude from sync** - detect pattern and skip:
- `{N} Termine` or `{N} Abende` patterns
- Date ranges > 4 weeks with recurring day codes

### Detection Logic
```python
def is_multi_week_event(memo, date_begin, date_end):
    # Check for "N Termine/Abende" pattern
    if re.search(r'\d+\s+(Termine|Abende)', memo):
        return True
    # Check date span > 28 days
    if (date_end - date_begin).days > 28:
        return True
    return False
```

### Sprint Task (2026-02-11)
**Sessions Feature** - needed for:
- Multi-week events with enumerated dates
- Weekly courses (common in other organizations)
- Recurring workshops

See: [Action Plan L25](2026-01-28_action_plan_location_management.md)

---

## 14. JSONB Patterns in crearis

### Pattern 1: weboptions (crearis/models/weboptions.py)

**Architecture:**
- `fields.Json()` for storage (page_options, aside_options, header_options, footer_options)
- Computed fields with `inverse` for typed key access
- Helper methods: `get_option()`, `set_option()`, `remove_option()`
- Button actions for create/delete entire sections

**Key insight:** Abstract model `web.options.abstract` - inherited by any entity needing web theming.

```python
class WebOptionsAbstract(models.AbstractModel):
    _name = 'web.options.abstract'
    
    page_options = fields.Json(string='Page Options', default=False)
    
    # Computed accessor for single key
    page_background = fields.Selection(
        selection=[...],
        compute='_compute_page_background',
        inverse='_inverse_page_background',
        store=False
    )
    
    def get_option(self, section, option_name, default=None):
        section_field = f'{section}_options'
        options = getattr(self, section_field, None) or {}
        return options.get(option_name, default)
```

**Criticism (from VueJS review):** Monolithic approach - should break into smaller pieces.

### Pattern 2: sysreg System

**Concept:** System registry for:
- Status variables
- Roles (creator, participant, ...) as integers
- Capabilities and transitions

**Integration with tags:**
- Extend odoo-per-entity-tag-systems with `sysreg_key` field
- Convention for xmlid naming per entity
- GraphQL interface maps odoo tags → JSON fields

---

## 15. schedule_data Architecture

### Module Placement: `crearis` (not crearis_agenda)

**Rationale:** Schedule parsing is crearis-wide, not DASEi-specific.

**Structure:**
```
crearis/
  models/
    schedule_mixin.py      # Abstract mixin for schedule_data
    schedule_config.py     # Per-company shortcode config
```

### Per-Company Configuration

```python
class ResCompany(models.Model):
    _inherit = 'res.company'
    
    schedule_shortcodes = fields.Json(
        string='Schedule Shortcodes',
        help='Mapping of shortcodes to location IDs',
        default=lambda self: {
            '_online_': {'type': 'online'},
        }
    )
    
    schedule_locale = fields.Selection([
        ('de', 'German'),
        ('en', 'English'),
    ], default='de', string='Schedule Locale')
    
    online_provider = fields.Selection([
        ('msteams', 'Microsoft Teams'),
        ('zoom', 'Zoom'),
        ('jitsi', 'Jitsi Meet'),
        ('other', 'Other'),
    ], default='msteams', string='Online Provider')
```

**Example shortcodes config (DASEi, company_id=11):**
```json
{
  "_online_": {"type": "online"},
  "_TANZEREI_": {"type": "venue", "raum_id": 8, "name": "Tanzerei"},
  "_KINEO_": {"type": "venue", "raum_id": 17, "name": "Kineo"},
  "_KHG_": {"type": "venue", "raum_id": 4, "name": "KHG München"},
  "_KOFFERFABRIK_": {"type": "venue", "raum_id": 9, "name": "Kofferfabrik"}
}
```

### i18n Strategy

**VueJS Pattern (reference):**
| Field | Language | Purpose |
|-------|----------|---------|
| `name` | English | Technical identifier, code-safe |
| `label` | i18n | UI display label |
| `description` | i18n | Extended description |

**For schedule parsing:**
- Support both `de` and `en` weekday codes
- Default to `de` (German-speaking area is crearis origin)
- Normalize to English internally for consistency

**Weekday Mapping:**
```python
WEEKDAYS = {
    # German (default)
    'MO': 0, 'DI': 1, 'MI': 2, 'DO': 3, 'FR': 4, 'SA': 5, 'SO': 6,
    # English (fallback)
    'MON': 0, 'TUE': 1, 'WED': 2, 'THU': 3, 'FRI': 4, 'SAT': 5, 'SUN': 6,
}

# Internal storage uses English 3-letter codes
WEEKDAY_NAMES = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
```

**Date Parsing:**
```python
# German: DD.MM or DD.MM.YY
# English: MM/DD or MM/DD/YY (future, lower priority)
DATE_PATTERNS = {
    'de': r'(\d{1,2})\.(\d{1,2})(?:\.(\d{2,4}))?',  # 17.9 or 17.9.24
    'en': r'(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?',    # 9/17 or 9/17/24
}
```

**GraphQL Integration:**
- GraphQL resolver provides i18n via `Accept-Language` header
- Composable on Vue side handles static localStorage fallbacks
- schedule_data stored with English `name` keys, labels resolved at query time

### Abstract Mixin Design

```python
class EventScheduleMixin(models.AbstractModel):
    _name = 'event.schedule.mixin'
    _description = 'Event Schedule Mixin'
    
    schedule_data = fields.Json(
        string='Schedule Data',
        help='Parsed session schedule in JSONB format',
        default=False
    )
    
    schedule_raw = fields.Text(
        string='Schedule Raw Text',
        help='Original text before parsing'
    )
    
    # Computed summary fields (stored for filtering/reporting)
    has_online_sessions = fields.Boolean(
        compute='_compute_schedule_summary',
        store=True
    )
    total_hours = fields.Float(
        compute='_compute_schedule_summary',
        store=True
    )
    online_hours = fields.Float(
        compute='_compute_schedule_summary',
        store=True
    )
    session_count = fields.Integer(
        compute='_compute_schedule_summary',
        store=True
    )
    
    @api.depends('schedule_data')
    def _compute_schedule_summary(self):
        for record in self:
            data = record.schedule_data or {}
            summary = data.get('summary', {})
            record.has_online_sessions = summary.get('has_online', False)
            record.total_hours = summary.get('total_hours', 0.0)
            record.online_hours = summary.get('online_hours', 0.0)
            record.session_count = summary.get('session_count', 0)
    
    def parse_schedule_text(self, text, company=None):
        """Parse schedule text into schedule_data JSONB."""
        company = company or self.env.company
        locale = company.schedule_locale or 'de'
        shortcodes = company.schedule_shortcodes or {}
        # ... parsing logic ...
        return schedule_data
    
    def get_online_sessions(self):
        """Get all online sessions."""
        sessions = (self.schedule_data or {}).get('sessions', [])
        return [s for s in sessions if s.get('type') == 'online']
    
    def get_venue_sessions(self):
        """Get all venue sessions."""
        sessions = (self.schedule_data or {}).get('sessions', [])
        return [s for s in sessions if s.get('type') == 'venue']
```

---

## 10. Architecture Insight: The Broker Pattern

From earlier sprint planning:

```
┌──────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│   SharePoint     │────▶│      Odoo       │────▶│    GraphQL API   │
│  (heterogeneous) │     │   (normalizes)  │     │  (standardizes)  │
└──────────────────┘     └─────────────────┘     └──────────────────┘
                                 │
                                 ▼
                         ┌──────────────────┐
                         │  Eleanora's List │
                         │   (Odoo native)  │
                         └──────────────────┘
```

**Key insight:** Odoo acts as broker - normalizes heterogeneous SP data AND provides native UX for internal users (Eleanora) AND serves GraphQL for external clients (VueJS).

The location-management + track-breakdown feature should showcase this:
- SP: raw text schedule
- Odoo: parsed JSONB + optional tracks
- GraphQL: nested structure with location details
- Eleanora: filterable list with issue tags

---

*Next: Run diagnostic commands, review seminarzeiten patterns, synthesize with Hans' vision*
