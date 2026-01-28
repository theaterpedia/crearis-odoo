# DASEi Schedule Shortcodes Configuration

> Generated: 2026-01-28
> Company: DASEi (ID 11)
> Used by: ScheduleParser in crearis/models/schedule_mixin.py

## Shortcode Registry

This JSON can be loaded into `res.company.schedule_shortcodes`:

```json
{
  "_online_": {
    "type": "online",
    "name": "Online",
    "name_de": "Online",
    "provider": "msteams"
  },
  "_TANZEREI_": {
    "type": "venue",
    "name": "Tanzerei Erlangen",
    "name_de": "Tanzerei Erlangen",
    "raum_id": 8,
    "partner_id": null
  },
  "_KINEO_": {
    "type": "venue",
    "name": "Kineo München",
    "name_de": "Kineo München",
    "raum_id": 17,
    "partner_id": null
  },
  "_KHG_": {
    "type": "venue",
    "name": "KHG Nürnberg",
    "name_de": "KHG Nürnberg",
    "raum_id": 4,
    "partner_id": null
  },
  "_KOFFERFABRIK_": {
    "type": "venue",
    "name": "Kofferfabrik Fürth",
    "name_de": "Kofferfabrik Fürth",
    "raum_id": 9,
    "partner_id": null
  },
  "_BURGSTALLMUEHLE_": {
    "type": "venue",
    "name": "Burgstallmühle",
    "name_de": "Burgstallmühle",
    "raum_id": 11,
    "partner_id": null
  },
  "_TREFFPUNKT_": {
    "type": "venue",
    "name": "Treffpunkt Gemeinschaft",
    "name_de": "Treffpunkt Gemeinschaft",
    "raum_id": 13,
    "partner_id": null
  },
  "_EVANG_": {
    "type": "venue",
    "name": "Evangelische Tagungsstätte",
    "name_de": "Evangelische Tagungsstätte",
    "raum_id": 18,
    "partner_id": null
  },
  "_STREITBERG_": {
    "type": "venue",
    "name": "Gut Streitberg",
    "name_de": "Gut Streitberg",
    "raum_id": 16,
    "partner_id": null
  },
  "_MUENCHEN_": {
    "type": "location",
    "name": "München",
    "name_de": "München"
  },
  "_NUERNBERG_": {
    "type": "location",
    "name": "Nürnberg",
    "name_de": "Nürnberg"
  },
  "_FUERTH_": {
    "type": "location",
    "name": "Fürth",
    "name_de": "Fürth"
  },
  "_ERLANGEN_": {
    "type": "location",
    "name": "Erlangen",
    "name_de": "Erlangen"
  }
}
```

## SharePoint plan_raeume Mapping

| raum_id | Title | Type | Shortcode |
|---------|-------|------|-----------|
| 1 | DASEi | abstract | (default) |
| 2 | --- | abstract | (no sessions) |
| 3 | München | location | `_MUENCHEN_` |
| 4 | KHG | venue | `_KHG_` |
| 5 | online | online | `_online_` |
| 6 | Raum Region | abstract | — |
| 7 | Coaching Raum DASEi | abstract | — |
| 8 | Tanzerei | venue | `_TANZEREI_` |
| 9 | Kofferfabrik | venue | `_KOFFERFABRIK_` |
| 10 | Nürnberg/Fürth | location | `_NUERNBERG_` |
| 11 | Burgstallmühle | venue | `_BURGSTALLMUEHLE_` |
| 12 | Erlangen | location | `_ERLANGEN_` |
| 13 | Treffpunkt | venue | `_TREFFPUNKT_` |
| 14 | Coaching online | abstract | — |
| 15 | Prüfung online | abstract | — |
| 16 | Gut Streitberg | venue | `_STREITBERG_` |
| 17 | Kineo | venue | `_KINEO_` |
| 18 | Evangelische Tagungsstätte | venue | `_EVANG_` |
| 19 | Externveranstaltung | abstract | — |
| 20 | JG Fürth | venue | `_JGFUERTH_` |

## Schedule Text Patterns Observed

### Pattern 1: Clean parseable (ready for production)
```
FR 18:00-20:00 online
SA 09:00-18:00
SO 09:00-15:00
```
→ Parser result: 3 sessions, 19 hours

### Pattern 2: Section headers (requires cleanup)
```
online:
FR 18:00-21:00
München:
SA 09:30-18:30
```
→ Need to convert to: `FR 18:00-21:00 _online_` / `SA 09:30-18:30 _MUENCHEN_`

### Pattern 3: Date-specific (parseable)
```
FR 24.6 18:00-20:00 online
SA 25.6 09:00-18:00
```
→ Parser extracts dates from `DD.MM` format

### Pattern 4: Unclear/freeform (needs HANS_RESOLVE)
```
Zeiten auf AnFRage
individueller Prozess (im Rahmen D2-D4)
4 aus 6 Abende a 3h online
einmal monatlich jeweils DO 19:00-21:00
```
→ Cannot parse reliably, mark for manual review

### Pattern 5: Venue prefix (needs cleanup)
```
Fürth Kofferfabrik MI 16:00-21:00
```
→ Should be: `MI 16:00-21:00 _KOFFERFABRIK_`

### Pattern 6: Comments/notes (ignore)
```
*Uhrzeiten können geändert werden
ACHTUNG: Optional!!
TERMIN wird bis 1.1.2026 ggf. noch geändert
```
→ Parser ignores lines without valid time patterns

## Cleanup Script Requirements

1. **Section header conversion** (online:, München:, etc.)
   - Find lines ending with `:`
   - Apply shortcode to subsequent lines until next section
   
2. **Venue prefix removal**
   - Find known venue names at start of line
   - Move to end as shortcode

3. **Time format normalization**
   - `9:00` → `09:00`
   - `18:00 Uhr` → `18:00`
   - `09:00 - 12:00` → `09:00-12:00`

4. **HANS_RESOLVE markers**
   - Free-form text like "Zeiten auf AnFRage"
   - Relative schedules like "einmal monatlich"
   - Multi-week ranges (handled separately)

---

## TASK: Special Shortcodes (Pending Implementation)

### `_anfrage_` - Times on Request
**Status**: 🔲 TODO

**Behavior**:
- Pattern matches: "Zeiten auf Anfrage", "auf AnFRage", "times on request"
- Resolves to `09:00-18:00` for **EACH day** in the event date range
- **Validation**: Error if date range > 14 days (prevent runaway sessions)
- **Side effect**: Tag event with `Issue_schedule` for manual follow-up

**Example**:
```
Input:  "Zeiten auf AnFRage | mit Eleanora Allerdings"
Event:  date_begin=2026-03-15, date_end=2026-03-17
Output: 3 sessions (15., 16., 17.) each 09:00-18:00
```

**Test IDs**: 1096, 1197, 1375, 1389, 1536

---

### `_individuell_` - Individual Appointments
**Status**: 🔲 TODO

**Behavior**:
- Pattern matches: "individueller Prozess", "individueller Termin", "Individuelle"
- Resolves to `09:00-09:00` for **FIRST day only** (placeholder session)
- **Preserves** original Feld11 text in `schedule_data.notes` field
- Does NOT remove original text (keeps context for humans)

**Example**:
```
Input:  "individueller (Telefon-) Termin"
Event:  date_begin=2026-04-01, date_end=2026-04-30
Output: 1 session on 2026-04-01, 09:00-09:00
JSON:   {"sessions": [...], "notes": "individueller (Telefon-) Termin"}
```

**Test IDs**: 1090, 1092, 1222, 1223, 1224, 1225, 1267, 1270, 1285, 1304, 1308, 1355, 1367, 1369, 1425, 1433, 1454, 1487, 1495, 1516, 1593

---

### `_reihe_` - Weekly Series (Terminreihe)
**Status**: 🔲 TODO (this sprint: replacement only, next sprint: proper parsing)

**Pre-Processing (Feld11 Replacement)**:
- Pattern matches: "X aus Y Abende a Zh online", "Y Abende a Zh online"
- **Replaces** Feld11 text with normalized format
- Weekday calculated from event's `date_begin`
- Times always start at 18:00 (evening series assumption)
- Duration from text (e.g., "3h" → 21:00)

**Replacement Logic**:
```
Input:  "4 aus 6 Abende a 3h online"
Event:  date_begin=2026-02-03 (Tuesday)
Replace Feld11 with: "_reihe_ 6 Termine DI 18:00-21:00 _online_"
```

**German weekday mapping**:
- MO, DI, MI, DO, FR, SA, SO

**Test IDs**: 1183, 1268, 1305, 1339, 1400, 1413, 1460, 1475

**NOTE**: Proper `_reihe_` parsing (generating N weekly sessions) is planned for **next sprint**. 
Current sprint only normalizes the text format for consistency.

---

### WISHLIST: Videocall Tracks (Future)
**Status**: 💭 Wishlist

When `_individuell_` is used, future enhancement could treat the event as containing
multiple individual "videocall tracks" rather than a single session:

- Event has N participants
- Each participant gets their own video call slot (e.g., 30 min each)
- `event.session` becomes a container for micro-appointments
- Calendar integration shows individual slots
- May need new model: `event.videocall.slot` or `event.appointment`

**Use Cases**:
- P5: "Individuelle Prüfungsterrmine, Dauer 30 Min"
- P4: "Coaching-Kleingruppen-Termine (pro Person 2 Termine)"
- AZ: "individueller (Telefon-) Termin"

## SQL for Shortcode Initialization

```sql
-- Initialize DASEi shortcodes
UPDATE res_company
SET schedule_shortcodes = '{
  "_online_": {"type": "online", "name": "Online"},
  "_TANZEREI_": {"type": "venue", "name": "Tanzerei Erlangen", "raum_id": 8},
  "_KINEO_": {"type": "venue", "name": "Kineo München", "raum_id": 17},
  "_KHG_": {"type": "venue", "name": "KHG Nürnberg", "raum_id": 4},
  "_KOFFERFABRIK_": {"type": "venue", "name": "Kofferfabrik Fürth", "raum_id": 9},
  "_BURGSTALLMUEHLE_": {"type": "venue", "name": "Burgstallmühle", "raum_id": 11}
}'::jsonb,
    schedule_locale = 'de_DE',
    online_provider = 'msteams'
WHERE id = 11;
```

## Data File for Module Init

Create `agenda_dasei/data/res_company_schedule.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo noupdate="1">
    <record id="dasei_schedule_config" model="res.company">
        <field name="id" ref="theaterpedia.company_dasei"/>
        <field name="schedule_locale">de_DE</field>
        <field name="online_provider">msteams</field>
        <field name="schedule_shortcodes">{
  "_online_": {"type": "online", "name": "Online"},
  "_TANZEREI_": {"type": "venue", "name": "Tanzerei Erlangen", "raum_id": 8},
  "_KINEO_": {"type": "venue", "name": "Kineo München", "raum_id": 17},
  "_KHG_": {"type": "venue", "name": "KHG Nürnberg", "raum_id": 4},
  "_KOFFERFABRIK_": {"type": "venue", "name": "Kofferfabrik Fürth", "raum_id": 9},
  "_BURGSTALLMUEHLE_": {"type": "venue", "name": "Burgstallmühle", "raum_id": 11},
  "_TREFFPUNKT_": {"type": "venue", "name": "Treffpunkt Gemeinschaft", "raum_id": 13},
  "_EVANG_": {"type": "venue", "name": "Evangelische Tagungsstätte", "raum_id": 18},
  "_STREITBERG_": {"type": "venue", "name": "Gut Streitberg", "raum_id": 16},
  "_JGFUERTH_": {"type": "venue", "name": "JG Fürth", "raum_id": 20}
}</field>
    </record>
</odoo>
```
