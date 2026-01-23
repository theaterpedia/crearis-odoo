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


---

# detailed chat-log from 2026-12-21

## Now I understand the structure. These are course products in the contacts list, identified by underscore prefix. The pattern is:

Course Programs (Grundstufe - M/N):
_M16, _M17, _M18 - München programs (cohort years)
_N16, _N17, _N18 - Nürnberg programs
Types: _Blockprogramm (block program), _Tageskurs (day course)

Aufbaustufe (ZR/ZT):
_PROFIL ZR - Profil Theaterpädagogische Regie
_PROFIL ZT - Profil Theaterpädagogisches Training
_Aufbaustufe Z13 - older cohort

Other:
_Referentin_* - Instructor/trainer references
_Offenes Programm - Open program
_theaterpedia-programm - Theaterpedia program

The sync should exclude these from real partner creation. Let me update the sync_partner.py to filter them out:

Read sync_partner.py, lines 55 to 80

Summarized conversation history

Optimizing tool selection...

Read sync_partner.py, lines 35 to 70

I'll add a filter to skip product references (contacts with FullName starting with underscore):

Edited
sync_partner.py+8-0
Done. Now the partner sync will skip contacts with FullName starting with underscore (the 28 course products), and count them in the skipped stat.

Should we also consider syncing these products to a different model (like product.template) in the future, or are they just reference data used for linking purposes in SharePoint?

So plan_kursteilnehmer links:

Kurs (KursLookupId) → course/product (contact)
Teilnehmer (TeilnehmerLookupId) → participant (contact)
Now let me understand how plan_veranstaltungscode relates - with its a1, a2, b1 module grouping:

## Now I understand the structure:
Module grouping: A1-A5 (Module A), B1-B7 (Module B), C1-C8 (Module C), D1-D4 (Module D), etc.
Products: M18/N18 courses, ZR/ZT profiles link to events via plan_veranstaltungscode
plan_kursteilnehmer: Links participants to courses/products
Let me create the product sync model in agenda_dasei:

Read model and manifest files
Now let me create the product sync and models:

Created product_template and course_participation files
Now let me create the sync logic for products and participations:

Created sync_product.py

Now update the __init__.py and add the list GUID field to company:

Edited
__init__.py+4-0
Created res_company.py

Now update the security CSV with the new model:

Read ir.model.access.csv

Edited
ir.model.access.csv+2-0
Now let me also add a method to relate module grouping (A, B, C, D...) from veranstaltungscode to events/participations:

Read product_template.py, lines 1 to 90

Now let me check what event_type looks like in crearis_agenda to see how we can link modules:

Searched for regex and files, read lines
I see - the event_type Title field contains the module code (A1, A2, B1, etc.). Let me check how events are linked to event_types:

Read sync_engine.py, lines 400 to 420

Good. So events link to event.type via VeranstaltungsCodeLookupId. The Title of the event_type (A1, B1, etc.) tells us the module.

Now I need to think about the module grouping. The module letter (A, B, C, D, E, F, G, H) determines the module group. Let me add a helper to extract this:

Edited
product_template.py+17-0
Now let me also enhance course_participation to know which module the participant attended based on events they registered for. But first, let me check if there's an event registration model:


Searched for regex `event.registration`
Good. So there's already event.registration model. The relationship is:

dasei.course.participation links participant (partner) to course (product)
event.registration links participant to individual events
Events have event.type which has the module code (A1, B1, etc.)
The module grouping from plan_veranstaltungscode Title tells us which module each event belongs to. Let me also add a computed field to relate participations to completed modules:

Read course_participation.py, lines 1 to 60

Edited
course_participation.py+15-0
Read course_participation.py, lines 65 to 77

Edited
course_participation.py+84-0
Now let me add the list GUID view for the company:

Read res_partner_views.xml, lines 1 to 50

Let me create a views file for the company and course participation:

Created multiple XML view files
Now update the manifest to include the new views and add product dependency:

Edited
__manifest__.py+7-0
Now let me verify the module loads correctly by checking for errors:

Checked agenda_dasei file
Let me also check the res_company view in crearis_agenda to make sure the xpath target exists:

Searched for text in XML files
The field already exists in crearis_agenda! Let me check the res_company.py there:

Searched for text in specified file
The field already exists in crearis_agenda. Let me remove my duplicate in agenda_dasei:

rm /home/persona/crearis/odoo/dev/crearis-odoo/agenda_dasei/models/res_company.py /home/persona/crearis/odoo/dev/crearis-odoo/agenda_dasei/views/res_company_views.xml
Edited
__init__.py+0-1
Edited
__manifest__.py+0-1
Now let me summarize what was created:

Created files in agenda_dasei:

product_template.py - Extends product.template with:

ms_contact_id, ms_etag - SharePoint sync fields
course_program - M/N/ZR/ZT selection
course_year - Year/cohort (18, 2026-2028)
course_type - block/day/profile
_parse_course_fullname() - Parses FullName like _M18_Blockprogramm München
MODULE_GROUPS dict mapping A→Modul A, B→Modul B, etc.
course_participation.py - New dasei.course.participation model:

Links partner to course product
Tracks completed modules via completed_modules computed field
get_module_progress() method returns detailed progress
sync_product.py - Sync logic:

SYNC_PRODUCT_IDS = ['530', '532', '534', '536', '512', '550'] - M18, N18, ZR 2026-2028, ZT 2026-2028
sync_products() - Syncs these contacts as products
sync_participations() - Syncs plan_kursteilnehmer for these courses
Views for products and participations with menu items under Events

Module grouping logic:

Event types have Title like A1, A2, B1, B2...
First letter = module group (A, B, C, D, E, F for Grundstufe; G, H, J, L for Aufbaustufe)
Participants' completed modules computed from their event registrations
