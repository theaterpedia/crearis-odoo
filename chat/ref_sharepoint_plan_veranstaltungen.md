# SharePoint plan_veranstaltungen Reference

> Generated: 2026-01-28
> Source: Graph API column metadata
> List GUID: BA5CFB7C-CFE7-4EFD-BA0A-65F9019D5A53

## Core Fields

| Display Name | Internal Name | Type | Description |
|--------------|---------------|------|-------------|
| Title | Title | text(255) | Headline des Dokuments (required) |
| ID | ID | auto | SharePoint item ID |
| Start | Feld17 | dateTime | Event start |
| Ende | Feld18 | dateTime | Event end |

## Lookup Fields (Foreign Keys)

| Display Name | Internal Name | Lookup List | Multi-value |
|--------------|---------------|-------------|-------------|
| Hauptreferent | Hauptreferent | plan_referenten | No |
| Nebenreferent | Nebenreferent | plan_referenten | No |
| Status | Status | plan_status | No |
| Seminarplan | Seminarplan | plan_seminarzeiten | No |
| VeranstaltungsCode | VeranstaltungsCode | plan_veranstaltungscodes | No |
| SecondaryCode | SecondaryCode | plan_veranstaltungscodes | No |
| Kurse_deleted | Kurse | plan_kurse | Yes (deprecated) |
| **Raum** | Raum | **plan_raeume** | Yes (deprecated) |
| **raum1** | raum1 | **plan_raeume** | **No (NEW)** |

## Derived Lookup Fields (Read-only)

| Display Name | Internal Name | Source |
|--------------|---------------|--------|
| Seminarplan:Seminarplan | Seminarplan_x003a_Seminarplan | plan_seminarzeiten.Feld1 |
| VeranstaltungsCode:Veranstaltungstitel | VeranstaltungsCode_x003a_Veranst | plan_veranstaltungscodes.Feld10 |
| Raum:oaddress_id | Raum_x003a_oaddress_id | plan_raeume.oaddress_id (multi) |
| raum1:oaddress_id | raum1_x003a_oaddress_id | plan_raeume.oaddress_id (single) |
| VeranstaltungsCode:oevent_type_id | VeranstaltungsCode_x003a_oevent_ | plan_veranstaltungscodes.oevent_type_id |
| Hauptreferent:ouser_id | Hauptreferent_x003a_ouser_id | plan_referenten.ouser_id |

## Text Fields

| Display Name | Internal Name | Type | Lines | Description |
|--------------|---------------|------|-------|-------------|
| **Seminarplan_Memo** | **Feld11** | text(multi) | 6 | **Schedule input** (parsed → schedule_data) |
| InternKommentar | Feld110 | text(255) | - | Internal comment |
| Raumreservierung | Feld111 | text(multi) | 6 | Room reservation notes |
| Raumbemerkungen | Feld112 | text(multi) | 6 | Room remarks |
| Orga_Info | Orga_Info | text(multi) | 6 | Organization info |
| Orga_Team | Orga_Team | text(multi) | 6 | Team info |
| UrlChannel | UrlChannel | text(255) | - | Teams channel URL |

## Number Fields

| Display Name | Internal Name | Type | Decimals |
|--------------|---------------|------|----------|
| UE | Feld1 | number | 2 |
| Kursraten | Feld13 | number | auto |
| MinTeilnehmer | Feld15 | number | auto |
| MaxTeilnehmer | Feld16 | number | auto |

## Currency Fields

| Display Name | Internal Name | Locale |
|--------------|---------------|--------|
| Honorar | Feld10 | de-DE |
| Raumkosten | Feld12 | de-DE |
| SonstigeKosten | Feld19 | de-DE |

## Boolean Fields

| Display Name | Internal Name | Default |
|--------------|---------------|---------|
| OffenesProgramm | Feld14 | false |
| Untertermin | Feld113 | false |

## Odoo Integration Fields

| Display Name | Internal Name | Type | Direction | Description |
|--------------|---------------|------|-----------|-------------|
| oevent_id | oevent_id | number(unique) | SP←Odoo | Odoo event.event ID |
| oversion | oversion | number | SP←Odoo | Odoo version counter |
| oheading | oheading | text(255) | SP←Odoo | Heading (markdown) |
| otesasertext | oteasertext | text(multi) | SP←Odoo | Teaser text |
| omd | omd | text(multi) | SP←Odoo | Body markdown |
| **oschedule** | **oschedule** | text(multi) | **SP←Odoo** | **Parsed schedule JSONB** |
| cimg | cimg | text(255) | bidirectional | Image xmlid/URL |
| domain_code | domain_code | text(255) | bidirectional | Website domain |
| Meldefrist | Meldefrist | dateOnly | SP only | Registration deadline |

---

## Schedule Data Flow

```
SharePoint (Input)                    Odoo                          SharePoint (Output)
─────────────────────────────────────────────────────────────────────────────────────

Feld11 (Seminarplan_Memo)  ───────►  schedule (text)
        │                                  │
        │                                  ▼
        │                            ScheduleParser.parse()
        │                                  │
        │                                  ▼
        │                            schedule_data (JSONB)  ───────►  oschedule
        │                                  │
        ▼                                  ▼
plan_seminarzeiten.Feld12 ─────►  (fallback if SeminarplanLookupId > 1)
```

### Schedule Resolution Priority

1. `oschedule` (if already written back from Odoo) → `schedule`
2. `Feld11` (Seminarplan_Memo on event) → `schedule`
3. `plan_seminarzeiten.Feld12` (if `SeminarplanLookupId > 1`) → `schedule`

### oschedule Write-back Format

The `oschedule` field receives **JSONB serialized as multiline text**:

```json
{
  "$schema": "schedule_data_v1",
  "sessions": [
    {
      "day_code": "FR",
      "time_start": "18:00",
      "time_end": "20:00",
      "duration_hours": 2.0,
      "location": "online",
      "shortcode": "_online_"
    }
  ],
  "summary": {
    "session_count": 1,
    "total_hours": 2.0,
    "online_hours": 2.0,
    "has_online": true
  },
  "location_hint": "Online"
}
```

---

## raum1 Location Sync

### Old vs New Location Field

| Field | Type | Status | Usage |
|-------|------|--------|-------|
| Raum | lookup(multi) | **Deprecated** | Legacy multi-value |
| raum1 | lookup(single) | **Active** | Primary location |

### Sync Code Pattern

```python
# Read location from SP
raum_id = sp_fields.get('raum1LookupId')  # Integer ID (1-20)
address_id = sp_fields.get('raum1_x003a_oaddress_id')  # Derived Odoo partner ID

# Write location to Odoo
if raum_id:
    # Find partner by SP raum ID
    partner = env['res.partner'].search([
        ('sp_raum_id', '=', raum_id),
        ('is_event_location', '=', True)
    ], limit=1)
    if partner:
        vals['address_id'] = partner.id
```

### Migration Status

- `migrate_raum_to_raum1()` executed: 699 events migrated
- All future events use `raum1` single-value field

---

## Field Name Quick Reference

| Friendly Name | Internal Name | API Access |
|---------------|---------------|------------|
| Schedule Memo | Feld11 | `sp_fields.get('Feld11')` |
| Start Date | Feld17 | `sp_fields.get('Feld17')` |
| End Date | Feld18 | `sp_fields.get('Feld18')` |
| Teaching Units | Feld1 | `sp_fields.get('Feld1')` |
| Room ID | raum1LookupId | `sp_fields.get('raum1LookupId')` |
| Room Address | raum1_x003a_oaddress_id | `sp_fields.get('raum1_x003a_oaddress_id')` |
| Event Type ID | VeranstaltungsCodeLookupId | `sp_fields.get('VeranstaltungsCodeLookupId')` |
| Status ID | StatusLookupId | `sp_fields.get('StatusLookupId')` |

---

## Important Notes

1. **Feld11 vs oschedule**: Feld11 is the **input** (human-edited), oschedule is the **output** (Odoo-parsed)
2. **raum1 vs Raum**: Always use `raum1LookupId` (single), ignore deprecated `Raum` (multi)
3. **Write-back**: Odoo only writes to `o*` prefixed fields and `cimg`/`domain_code`
4. **HANS_RESOLVE marker**: Add to unclear Seminarplan_Memo entries for manual review
