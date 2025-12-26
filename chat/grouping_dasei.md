# DASEi Course Products & Module Grouping

## Overview

DASEi training programs are structured as **course products** with participants tracked via **course participations**. Progress is measured by **module completion** derived from event registrations.

## SharePoint Data Structure

### Contacts as Products

In SharePoint `contacts` list, records with FullName starting with `_` are **course products**, not people:

| ID | FullName | Program | Type |
|----|----------|---------|------|
| 530 | `_M18_Blockprogramm München` | M (München) | Blockprogramm |
| 532 | `_N18_Blockprogramm Nürnberg` | N (Nürnberg) | Blockprogramm |
| 534 | `_M18_Tageskurs München` | M (München) | Tageskurs |
| 536 | `_N18_Tageskurs Nürnberg` | N (Nürnberg) | Tageskurs |
| 512 | `_Profil ZR 2026-2028` | ZR (Regie) | Aufbaustufe |
| 550 | `_Profil ZT 2026-2028` | ZT (Training) | Aufbaustufe |

### List: plan_kursteilnehmer

Links participants to course products:

```
GUID: 2bf5f8e7-ebca-4a8b-b11e-feaee6a30287
```

| Field | Internal Name | Description |
|-------|---------------|-------------|
| Kurs | KursLookupId | → contacts (course product) |
| Teilnehmer | TeilnehmerLookupId | → contacts (participant) |
| Status | StatsLookupId | Participation status |
| Bemerkung | Feld10 | Notes |
| angelegt | Feld1 | Boolean - record created |

### List: plan_veranstaltungscodes (Event Types)

Defines modules via Title field:

```
GUID: E4B1128D-2709-480D-82D0-77F42605FD1A
```

| Title | Name (Feld10) | Module |
|-------|---------------|--------|
| A1 | Am Anfang war der Kreis | A |
| A2 | Die Bühne kommt von selbst | A |
| B1 | Das fiktive Situationsbildverfahren | B |
| B2 | Klischees, Situationen & Skulpturen | B |
| C1 | Initiierung | C |
| ... | ... | ... |

## Module Groups

First letter of event_type Title determines the module group:

### Grundstufe (M/N Programs)

| Module | Description | Required |
|--------|-------------|----------|
| A | Grundlagen Spielen | ✓ |
| B | Grundlagen Anleiten | ✓ |
| C | Theaterprojekt | ✓ |
| D | Konzeption | ✓ |
| E | Gruppenarbeit | ✓ |
| F | Feedback | ✓ |

### Aufbaustufe (ZR/ZT Profiles)

| Module | Description | Required |
|--------|-------------|----------|
| G | Vertiefung | ✓ |
| H | Bewegungstheater | ✓ |
| J | Abenteuertheater | ✓ |
| L | Zusatzqualifikation | ✓ |

### Additional Modules

| Module | Description |
|--------|-------------|
| T | Tagesseminare |
| R | Trainings |
| Z | Specials |

## Odoo Models

### product.template (extended)

```python
# SharePoint sync
ms_contact_id = fields.Char(index=True)  # SP contacts item ID
ms_etag = fields.Char()

# Course attributes
course_program = fields.Selection([
    ('M', 'München'),
    ('N', 'Nürnberg'),
    ('ZR', 'Profil Theaterpädagogische Regie'),
    ('ZT', 'Profil Theaterpädagogisches Training'),
])
course_year = fields.Char()  # "18" or "2026-2028"
course_type = fields.Selection([
    ('block', 'Blockprogramm'),
    ('day', 'Tageskurs'),
    ('profile', 'Aufbaustufe'),
])
```

### dasei.course.participation

```python
# Relations
partner_id = fields.Many2one('res.partner')  # Participant
course_id = fields.Many2one('product.template')  # Course product

# From SharePoint
ms_item_id = fields.Char(index=True)  # plan_kursteilnehmer ID
status_id = fields.Integer()  # StatsLookupId
notes = fields.Text()  # Feld10/Bemerkung
is_created = fields.Boolean()  # Feld1/angelegt

# Computed
completed_modules = fields.Char(compute='_compute_completed_modules')
```

## Sync Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    SharePoint                                │
├─────────────────────────────────────────────────────────────┤
│  contacts (FullName="_...")  →  product.template            │
│  contacts (real people)      →  res.partner                 │
│  plan_kursteilnehmer         →  dasei.course.participation  │
│  plan_veranstaltungscodes    →  event.type                  │
│  plan_veranstaltungen        →  event.event                 │
└─────────────────────────────────────────────────────────────┘
```

### Sync Order

1. **Products first** (`dasei.sync.product`)
   - Filter: `SYNC_PRODUCT_IDS = ['530', '532', '534', '536', '512', '550']`
   - Creates `product.template` records

2. **Partners** (`dasei.sync.partner`)
   - Filter: Skip FullName starting with `_`
   - Creates `res.partner` records

3. **Participations** (`dasei.sync.participation`)
   - Filter: Only KursLookupId in SYNC_PRODUCT_IDS
   - Links partners to products

## Module Progress Computation

```python
def _compute_completed_modules(self):
    """
    1. Get all confirmed event.registration for partner
    2. Extract event_type.name first letter (A, B, C...)
    3. Filter to valid MODULE_GROUPS
    4. Store as comma-separated: "A,B,C"
    """
```

### get_module_progress() Method

Returns detailed progress:

```python
{
    'completed': ['A', 'B', 'C'],
    'pending': ['D', 'E', 'F'],
    'details': {
        'A': [
            {'event': 'A1 München 2024', 'code': 'A1', 'date': ..., 'state': 'done'},
            {'event': 'A2 München 2024', 'code': 'A2', 'date': ..., 'state': 'done'},
        ],
        'B': [...],
    }
}
```

## Configuration

### Company Settings

Set in `res.company` MS Agenda config:

```
ms_list_kursteilnehmer = "2bf5f8e7-ebca-4a8b-b11e-feaee6a30287"
```

### Syncing Products

```python
# In shell or scheduled action
company = env.ref('base.main_company')
env['dasei.sync.product'].sync_products(company)
env['dasei.sync.participation'].sync_participations(company)
```

## Menu Access

Under **Events** menu:
- **Course Products** - List of synced course products (filtered by ms_contact_id)
- **Course Participations** - Participant ↔ Course links with module progress

## Future Considerations

1. **Auto-sync participations** when event registrations change
2. **Certificate generation** when all required modules completed
3. **Dashboard** showing cohort progress statistics
4. **Extend to older cohorts** (M17, N17, etc.) by adding IDs to SYNC_PRODUCT_IDS
