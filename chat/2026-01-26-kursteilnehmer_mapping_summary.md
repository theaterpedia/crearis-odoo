# Kursteilnehmer Mapping Summary

**Date:** 2026-01-26  
**Status:** For review Thu/Fri this week  
**Priority:** Later (post Feb 1st)

## Understanding

### Data Flow

```
plan_kursteilnehmer.KursLookupId → kurs_id → (hardcoded map) → contact_id → kurs_code
```

### Key Tables

1. **plan_kursteilnehmer** - Contains participant enrollments
   - `KursLookupId` → points to `kurs_id`
   - `TeilnehmerLookupId` → points to contact (participant)

2. **plan_veranstaltungsteilnehmer** - Contains default schedule for each `kurs_id`

3. **contacts** - Contains both:
   - Real people (participants, referents)
   - Product references (prefixed with `_`, e.g., `_M17_Tageskurs München`)

### Hardcoded Mapping (until July 31, 2026)

| kurs_id(s) | contact_id | Title | Notes |
|------------|------------|-------|-------|
| 119, 100, 120 | 477 | M16 | Tageskurs München (M16E, M16T variants) |
| 124, 110, 125 | 533 | M17 | Tageskurs München |
| 130, 111, 131 | 534 | M18 | Tageskurs München |
| 101 | 478 | N16 | Tageskurs Nürnberg |
| 122 | 535 | N17 | Tageskurs Nürnberg |
| 127 | 536 | N18 | Tageskurs Nürnberg |
| 118 | 403 | M16B | Blockprogramm München |
| 123 | 529 | M17B | Blockprogramm München |
| 129 | 530 | M18B | Blockprogramm München |
| 121 | 329 | N16B | Blockprogramm Nürnberg |
| 126 | 531 | N17B | Blockprogramm Nürnberg |
| 132 | 532 | N18B | Blockprogramm Nürnberg |
| 115 | 512 | Z15R | Profil ZR 2026-2028 |
| 116 | 550 | Z15T | Profil ZT 2026-2028 |

### Missing / TODO

- **Z15 (kurs_id 112)**: No contact_id - needs SharePoint product entry created
- **Original 5 IDs**: Not used at the moment (were from earlier iteration)

### Future: contact_id Usage

The `contact_id` mapping to product contacts could be used to:
- Control naming output
- Other stuff via MS ACCESS integration
- Currently just for documentation

## Tasks for Later (Feb 1st+)

- [ ] Create SharePoint product entry for Z15 (kurs_id 112)
- [ ] Investigate dynamic SharePoint field `kursverlauf_id` in plan_kurse (currently not working)
- [ ] Consider using contact_ids to control naming via MS ACCESS
- [ ] Review and expand this documentation
