# Action Plan: Location Management

*Created: 2026-01-28*  
*Status: Conception*

---

## Overview

Implement hybrid location sync from SharePoint `plan_raeume` to Odoo events:
- **Type A (Venues):** Sync to `res.partner` with full address data
- **Type B (Abstract):** Set location tag, no partner sync

---

## Data Foundation

### SharePoint plan_raeume

List GUID: `705952ee-bc5e-476f-88ea-31d21d5d3f7d`

See: [ref_sharepoint_raeume.md](ref_sharepoint_raeume.md)

### Location Classification

**Type A - Physical Venues (sync to res.partner):**
| ID | Title | City |
|----|-------|------|
| 1 | Nbg: KHG | Nürnberg |
| 3 | Mue: H-Lingg | München |
| 4 | Mue: Welt-Haus | München |
| 6 | Nbg: freie Szene | Nürnberg |
| 7 | Nbg: Büro | Nürnberg |
| 8 | Nbg: Tanzerei | Fürth |
| 13 | Burgstallmühle | Voggendorf |
| 16 | Mue: Stachus | München |
| 17 | Mue: Kineo | München |
| 18 | Mue: Viva la Danza | München |
| 19 | Mue: Biodanza | München |
| 20 | Mue: HochX | München |

**Type B - Abstract Placeholders (tag only, no partner):**
| ID | Title | → Tag XML ID |
|----|-------|--------------|
| 2 | Leer | `event_tag_tbd` |
| 5 | Web: Standard | `event_tag_online` |
| 9 | Nbg: Sonstige | `event_tag_on_request_nbg` |
| 10 | DEU: Nachfrage | `event_tag_on_request_deu` |
| 11 | BAY: Nachfrage | `event_tag_on_request_bay` |
| 12 | CZB: Nachfrage | `event_tag_on_request_czb` |
| 14 | - | `event_tag_tbd` |
| 15 | EU | `event_tag_on_request_eu` |

---

## Conception

### C1: Tag Category ✅

Created `event.tag.category` "Location Type" with tags:
- `event_tag_online` - Online
- `event_tag_on_request_nbg` - Nürnberg (auf Anfrage)
- `event_tag_on_request_mue` - München (auf Anfrage)
- `event_tag_on_request_bay` - Bayern (auf Anfrage)
- `event_tag_on_request_deu` - Deutschland (auf Anfrage)
- `event_tag_on_request_czb` - Bayern-Tschechien (auf Anfrage)
- `event_tag_on_request_eu` - Europa (auf Anfrage)
- `event_tag_tbd` - Ort wird bekannt gegeben

File: `agenda_dasei/data/event_tag_data.xml`

### C2: Event Model Extension

**Fields to add on `event.event`:**
```python
sp_raum_id = fields.Integer("SP Raum ID", help="SharePoint plan_raeume LookupId")
```

**Question:** Do we need `sp_location_type` computed field? Or is tag + address_id sufficient?

### C3: Partner Model Extension (Venue Locations)

**Fields to add on `res.partner`:**
```python
is_event_location = fields.Boolean("Is Event Location")
sp_raum_id = fields.Integer("SP Raum ID", help="SharePoint plan_raeume LookupId")
```

**Question:** Use existing `type='other'` for locations, or dedicated flag?

### C4: Sync Strategy

**Direction:** SharePoint → Odoo (READ-ONLY for locations)

**On event sync:**
```python
raum_id = sp_fields.get('raum1LookupId')

if raum_id in VENUE_IDS:
    # Find or create partner with sp_raum_id
    partner = find_or_create_location_partner(raum_id)
    vals['address_id'] = partner.id
    vals['sp_raum_id'] = raum_id
    # Remove location-type tags if any
    
elif raum_id in ABSTRACT_TO_TAG:
    tag_xmlid = ABSTRACT_TO_TAG[raum_id]
    tag = env.ref(f'agenda_dasei.{tag_xmlid}')
    vals['address_id'] = False
    vals['sp_raum_id'] = raum_id
    vals['tag_ids'] = [(4, tag.id)]  # Add tag
```

### C5: Location Partner Sync

**When to sync venue data to partner?**
- Option A: On first event sync (lazy create)
- Option B: Dedicated cron job for plan_raeume → res.partner
- Option C: Manual trigger only

**SP → Odoo Partner mapping:**
| SP Field | Odoo Field |
|----------|------------|
| Title | name |
| Feld1 (Beschreibung) | comment |
| Feld10 (Ort) | city |
| Feld11 (Adresse) | street |
| PLZ | zip |
| id | sp_raum_id |

### C6: Write-back

**After partner creation, write `oaddress_id` back to SP.**

---

## Tasks

### Phase 1: Data Model

- [ ] L1: Add `sp_raum_id` field to `event.event`
- [ ] L2: Add `is_event_location`, `sp_raum_id` to `res.partner`
- [ ] L3: Install tags (run module update)

### Phase 2: Sync Engine

- [ ] L4: Add `VENUE_IDS` and `ABSTRACT_TO_TAG` constants
- [ ] L5: Update `_map_event_from_sp()` to set `sp_raum_id`
- [ ] L6: Implement `_sync_event_location()` helper
- [ ] L7: Add location tag logic (add tag, remove conflicting tags)

### Phase 3: Venue Sync

- [ ] L8: Implement `sync_locations()` method for plan_raeume → res.partner
- [ ] L9: Write-back `oaddress_id` to SP after partner creation
- [ ] L10: Test full event sync with location data

### Phase 4: Schedule Data (JSONB)

- [ ] L11: Add `schedule_data` JSONB field to `event.event`
- [ ] L12: Add `online_provider` selection field to `res.company` (msteams, zoom, jitsi, etc.)
- [ ] L13: Define `_online_` convention parser
- [ ] L14: Implement schedule text → JSONB transformation
- [ ] L15: Write-back `schedule_data` to SP (new field `oschedule_data`)

### Phase 5: Online Sessions View

- [ ] L16: Add "All Online Sessions" list view (cross-event)
- [ ] L17: Add click-to-expand session details on event list
- [ ] L18: Add "has_online_sessions" computed field/tag

### Phase 6: Conference Adapter (Prototype)

- [ ] L19: Add `conference_adapter` field to `event.track.location` or product
- [ ] L20: Add MS Teams adapter fields (team_id, channel_id from product)
- [ ] L21: Stub conference acquisition method (no automation yet)

### Phase 7: Cleanup

- [ ] L22: Remove diagnostic methods from sync_engine.py
- [ ] L23: Update dev docs
- [ ] L24: Commit

### Phase 8: Sessions Feature (Sprint 2026-02-11)

**Context:** Multi-week events with enumerated sessions are out of scope for initial sync.
Detect and exclude, then implement full sessions support in next sprint.

- [ ] L25: Detect multi-week events (pattern: `N Termine/Abende` or span > 28 days)
- [ ] L26: Exclude multi-week from schedule_data sync (interim solution)
- [ ] L27: Design `event.session` model for recurring sessions
- [ ] L28: Parse enumerated dates into session records (`17.9.24, 24.9.24, ...`)
- [ ] L29: Sessions UI (calendar view for weekly/monthly course management)

**Use cases:**
- Weekly courses (common in other organizations)
- Multi-week workshops with specific dates
- Recurring seminars

### Phase 9: Schedule UI & Config Views

**Context:** Views for managing schedule configuration and visualizing parsed schedules.

- [ ] L30: Schedule Config View - Edit shortcodes, test parser (Settings → Technical)
- [ ] L31: Event Schedule Tab - Display/edit schedule_raw with parsed preview
- [ ] L32: Online Sessions View - List all online sessions across events
- [ ] L33: Room support in shortcodes (`_VENUE:ROOM_` format)
- [ ] L34: SharePoint write-back field `oschedule_data`

### Phase 10: Conference Integration (Future)

- [ ] L35: MS Teams adapter - acquire meeting links for online sessions
- [ ] L36: Store conference URLs in session data
- [ ] L37: Power Automate trigger on schedule changes

---

## Open Questions

1. **Partner type for venues:** Use `type='other'` or new `is_event_location` flag?
2. **Lazy vs eager sync:** Create partners on demand or sync all upfront?
3. **Koordination field:** Link venue partner to coordinator contact?
4. **Address formatting:** How to handle multiline `Adresse` field?

---

## Notes

- Migration script `migrate_raum_to_raum1()` already run successfully (699 events)
- Single-value `raum1LookupId` now available on all SP events
- Tags created in `agenda_dasei` module (pending install)

---

## Input Hans

*Raw input from user - to be synthesized with conception above*

### Tasks (DO)

- [ ] H1: Add tags-category `tasks_and_issues` for event-tags
- [ ] H2: Add tag `location issue` in that category

### Eleanora's Story

**User:** Eleanora Allerdings (`eleanora.allerdings@dasei.eu`)  
**Role:** Location & Room Manager for DASEi

**Workflow:**
- Every 4 months sends booking overview (6-18 months ahead) to location partners
- München: Institut Kineo (Eva Nikolait), Eine-Welt-Haus (Nelly Usaceva)
- Nürnberg: Tanzerei (Alexander Blanke), Burgstallmühle (Britta)
- Manages cancellation deadlines
- Confirms team requests for cancel/switch bookings
- Thorough worker - catches inconsistencies beyond locations
- Key pain point: Online sessions "attached" to in-presence events get overlooked → conflicting bookings

### Requirements for Eleanora (6 items)

1. **Intelligent event listing** - visualization of issues via color-tags
2. **No quick inline-edit** - wizard instead (3 steps: action-type / inputs / workflow-trigger)
3. **Smart search/filter** - presets: instructor, location, date, keywords ("offene Tasks", "Stornierungen")
4. **Email-a-report** - location bookings list with status-highlighting, issue-tags
5. **Email-a-request** - assisted quick-query for booking/alteration/cancellation via wizard
6. **Config entries** - menu crearis→agenda→dasei for templates, wizard settings

### Key Insight: NOT SharePoint-tied

These features are:
- Generic Odoo event-location management
- Applicable beyond DASEi
- Could become tutorial material for other orgs

### The SPEC Vision (Event Tracks)

Existing fine-grained SPEC targets event-tracks:
- Preconfigure location-details (rooms per location)
- Integrate online workflows (MS Teams)
- Break up multi-day events into tracks

**Two leverage points:**

1. **Tracks visible:** GraphQL, intelligent list, reports, SP write-back
2. **Defaults without tracks:** Much more important - provide detailed/manageable dataset without manual track creation

### The Hybrid Event Problem

~50% of DASEi events are hybrid:
```
FR: online
SA/SO: in-presence  
DI: online
```

Current pain:
- Text-based `seminarzeiten` allows "whatever" in memo fields
- Perfect for far-away scheduling → trouble in realtime
- Double-source-of-truth workflows → errors
- Online tracks get overlooked

**Proposed solution:**
- GraphQL provides standardized events
- VueJS client parses text-based info into tracks cleanly
- JSONB-driven approach (beyond standard Odoo patterns)
- Location-management + event-tracks showcase this architecture

### Architecture Question

> What is crearis, where does agenda_dasei add on?

See: [2026-01-28_research_event_tracks_hybrid.md](2026-01-28_research_event_tracks_hybrid.md)

### Hans' Answers (2026-01-28)

**Q1 - Schedule format:** Reasonably structured. Better yet: define conventions for crearis-wide use!
- ~300 entries with custom Seminarzeiten, 1-2h to standardize
- **Convention:** `_online_` marker in schedule text
- Per-company config: what "online" means (MS Teams, Zoom, Jitsi, etc.)
- Adapter pattern for conference auto-acquisition (MS Teams first)
- Team + channel already known via product!
- **Today:** Prepare fields, not automation yet

**Q2 - Run diagnostics:** Yes

**Q3 - JSONB approach:** Exactly!
- `schedule_data` JSONB → writes back to SharePoint
- MS Access can read into on-the-fly details table
- Power Automate can trigger actions from JSON (e.g., acquire Teams conference)

**Q4 - Eleanora's view:** Event-level + click-open-inspect
- Main view: events with tags/flags
- Click to expand: see session details
- Special view: "All online sessions" line-by-line

**Q5 - event.track.location:** Half-dormant
- Shows early thinking on tracks (1.5 years ago)
- Not actively used
- Will refactor against event_package product implementation

---

*Last updated: 2026-01-28*
