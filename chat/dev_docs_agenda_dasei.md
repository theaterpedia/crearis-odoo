# agenda_dasei - Developer Documentation

*Module Version: 16.0.1.2.0*  
*Created: 2025-12-22*  
*Last Updated: 2026-01-27*

---

## Overview

`agenda_dasei` extends `crearis_agenda` with DASEi-specific partner synchronization and domaincode mapping. It syncs contacts from SharePoint and computes the highest domaincode for each partner based on their course participation status.

## Dependencies

```python
'depends': [
    'crearis_agenda',
    'crearis_event_package',  # For event package products
    'product',
    'event',
]
```

Transitive: `crearis`, `event_sale`, `sale`

## Architecture

```
agenda_dasei/
├── __init__.py
├── __manifest__.py
├── hooks.py                        # post_init_hook, website creation, XMLId helpers
├── models/
│   ├── res_partner.py              # Partner fields + domaincode computation
│   ├── sync_partner.py             # Contact sync (inherits crearis.agenda.sync)
│   ├── course.py                   # dasei.course model (D3)
│   ├── course_participation.py     # dasei.course.participation model
│   ├── sync_kurse.py               # Course sync from plan_kurse (D3)
│   └── sync_registrations.py       # Registration sync (D4)
├── views/
│   ├── agenda_dasei_menu.xml       # DASEi submenu structure (DA1)
│   ├── res_partner_views.xml       # DASEi tab + search filters
│   ├── course_views.xml            # Course model views
│   └── course_participation_views.xml
├── data/
│   ├── ir_cron_data.xml            # Cron jobs for course/registration sync (D6)
│   ├── website_data.xml            # Server actions for website management
│   └── product_template_data.xml   # Grundkurs module products (A, B, C, D)
└── security/
    └── ir.model.access.csv
```

---

## DASEi Domain Structure

| Domaincode | URL | Purpose | Priority |
|------------|-----|---------|----------|
| `dasei` | verein.dasei.eu | Vereinsmitglieder (org members) | 100 |
| `dasei3` | aufbaustufe.dasei.eu | Aufbaustufe (advanced, ZR/ZT) | 30 |
| `dasei2` | grundstufe.dasei.eu | Grundstufe (intermediate, M?/N?) | 20 |
| `dasei1` | einstiege.dasei.eu | Einstiege (beginner, ME/NE) | 10 |
| `dasei0` | login.dasei.eu | Quick entry (newsletter, first contact) | 1 |

---

## Partner Fields (res.partner)

### SharePoint Sync Fields

| Field | Type | Purpose |
|-------|------|---------|
| `ms_contact_id` | Char | SharePoint contact item ID |
| `ms_contact_status` | Integer | Status from plan_contacts_status |
| `ms_kursteilnehmer_id` | Char | SharePoint kursteilnehmer ID |
| `ms_kurs_level` | Char | Highest evaluated Kurs code |
| `ms_version` | Char | SharePoint oversion |

### Computed Field

```python
dasei_domaincode = fields.Char(
    compute='_compute_dasei_domaincode',
    store=True,  # Stored for filtering/grouping
)
```

---

## Status → Domaincode Mapping

### From contacts.Status (plan_contacts_status)

| Status ID | Meaning | Domaincode | Sync Behavior |
|-----------|---------|------------|---------------|
| 1 | Active participant | dasei1* | *Further evaluate via kursteilnehmer |
| 2 | Former participant L2 | dasei2 | Direct |
| 3 | Former participant L3 | dasei3 | Direct |
| 4 | Aborted participation | dasei1 | Direct |
| 5 | Quick entry | dasei0 | Direct |
| 8 | Vereinsmitglied (member) | dasei | Only if no existing domainuser |
| 9 | Vereinsmitglied (participant) | dasei | Only if no existing domainuser |
| 10 | Partner | dasei | Only if no existing domainuser |

### Status 8, 9, 10 Special Handling

```python
def should_sync_vereinsmitglied(self):
    """Only sync if partner has no existing domainuser entries"""
    return len(self.domainuser_ids) == 0
```

This prevents overwriting manually configured domainuser roles.

---

## Kursteilnehmer Evaluation

For partners with `Status = 1` (active), the Kurs field from plan_kursteilnehmer determines the actual level.

### Kurs Code → Domaincode

| Kurs Pattern | Examples | Domaincode | Level |
|--------------|----------|------------|-------|
| `ZR`, `ZT` | ZR, ZT | dasei3 | Aufbaustufe (highest) |
| `M?`, `N?` (not ME/NE) | M_, MB, MA, NA, NB | dasei2 | Grundstufe |
| `ME`, `NE` | ME, NE | dasei1 | Einstiege |

### Evaluation Logic

```python
def _kurs_to_domaincode(self, kurs):
    if kurs in ('ZR', 'ZT'):
        return 'dasei3'
    if kurs.startswith(('M', 'N')) and kurs not in ('ME', 'NE'):
        return 'dasei2'
    if kurs in ('ME', 'NE'):
        return 'dasei1'
    return False
```

### Teilnahmestatus Filter

Only kursteilnehmer records with these `StatsLookupId` values are evaluated:

```python
VALID_TEILNAHME_STATUS_IDS = [1, 3, 13]
```

---

## Domaincode Computation

The `dasei_domaincode` field aggregates from multiple sources and returns the highest priority:

```python
@api.depends('ms_contact_status', 'ms_kurs_level', 'domainuser_ids', 'domainuser_ids.domain_code')
def _compute_dasei_domaincode(self):
    CODE_PRIORITY = {
        'dasei': 100,   # Highest: Vereinsmitglied
        'dasei3': 30,   # Aufbaustufe
        'dasei2': 20,   # Grundstufe
        'dasei1': 10,   # Einstiege
        'dasei0': 1,    # Quick entry
    }
    
    for partner in self:
        all_codes = []
        
        # From contact status + kurs level
        status_code = partner._status_to_domaincode(
            partner.ms_contact_status,
            partner.ms_kurs_level
        )
        if status_code:
            all_codes.append(status_code)
        
        # From domainuser records
        du_codes = partner.domainuser_ids.mapped('domain_code')
        all_codes.extend([c for c in du_codes if c])
        
        # Find highest
        highest = max(all_codes, key=lambda c: CODE_PRIORITY.get(c, 0))
        partner.dasei_domaincode = highest
```

---

## Sync Extension

### Inheriting crearis.agenda.sync

```python
class AgendaSyncPartner(models.AbstractModel):
    _inherit = 'crearis.agenda.sync'
    
    def sync_all(self, company):
        result = super().sync_all(company)
        
        # Add contact sync
        contact_stats = self.sync_contacts(company)
        result['contacts'] = contact_stats.get('synced', 0)
        
        # Evaluate kursteilnehmer
        kt_stats = self.evaluate_kursteilnehmer(company)
        result['kursteilnehmer'] = kt_stats.get('evaluated', 0)
        
        return result
```

### sync_contacts Method

1. Fetch all contacts from SharePoint
2. Filter by status (1-5, 8-10)
3. Match to Odoo partner by `ms_contact_id` or email
4. Create or update partner
5. Write back `opartner_id`

### evaluate_kursteilnehmer Method

1. Fetch all kursteilnehmer records
2. Filter by valid teilnahmestatus
3. Group by TeilnehmerLookupId (contact ID)
4. Find highest Kurs per contact
5. Update partner's `ms_kurs_level`

---

## Field Mappings

### Contacts (contacts → res.partner)

| SharePoint Field | Odoo Field | Notes |
|------------------|------------|-------|
| `id` | `ms_contact_id` | SharePoint item ID |
| `@odata.etag` | `ms_version` | Version tracking |
| `Title` | `lastname` | Last name |
| `FirstName` | `firstname` | First name |
| `FullName` | `name` | Full display name |
| `Email` | `email` | Email address |
| `WorkPhone` | `phone` | Phone |
| `CellPhone` | `mobile` | Mobile |
| `WorkAddress` | `street` | Street address |
| `WorkCity` | `city` | City |
| `WorkZip` | `zip` | ZIP code |
| `StatusLookupId` | `ms_contact_status` | Status ID |
| `opartner_id` | - | Write-back: Odoo ID |

### Kursteilnehmer (plan_kursteilnehmer)

| SharePoint Field | Usage |
|------------------|-------|
| `TeilnehmerLookupId` | Links to contact ID |
| `KursLookupId` | Kurs ID (needs resolution) |
| `StatsLookupId` | Teilnahmestatus filter |

---

## Views

### Partner Form (DASEi Sync Tab)

```xml
<page string="DASEi Sync" name="dasei_sync">
    <group string="Computed Status">
        <field name="dasei_domaincode" readonly="1"/>
    </group>
    <group string="SharePoint Sync">
        <field name="ms_contact_id"/>
        <field name="ms_contact_status"/>
        <field name="ms_kursteilnehmer_id"/>
        <field name="ms_kurs_level"/>
    </group>
</page>
```

### Search Filters

```xml
<filter string="DASEi Verein" domain="[('dasei_domaincode', '=', 'dasei')]"/>
<filter string="DASEi Aufbaustufe" domain="[('dasei_domaincode', '=', 'dasei3')]"/>
<filter string="DASEi Grundstufe" domain="[('dasei_domaincode', '=', 'dasei2')]"/>
<filter string="DASEi Einstiege" domain="[('dasei_domaincode', '=', 'dasei1')]"/>
<filter string="DASEi Quick" domain="[('dasei_domaincode', '=', 'dasei0')]"/>
```

### Group By

```xml
<filter string="DASEi Domaincode" context="{'group_by': 'dasei_domaincode'}"/>
```

---

## Use Case: Login Routing

The `dasei_domaincode` field enables automatic routing to the correct login portal:

```python
def get_login_url(self, partner):
    """Route partner to appropriate DASEi portal"""
    DOMAIN_URLS = {
        'dasei': 'https://verein.dasei.eu',
        'dasei3': 'https://aufbaustufe.dasei.eu',
        'dasei2': 'https://grundstufe.dasei.eu',
        'dasei1': 'https://einstiege.dasei.eu',
        'dasei0': 'https://login.dasei.eu',
    }
    return DOMAIN_URLS.get(partner.dasei_domaincode, 'https://login.dasei.eu')
```

---

## TODO / Known Limitations

1. **Kurs Code Resolution**: Currently stores `KursLookupId` instead of actual Kurs code (ME, MB, ZR). Need to either:
   - Pre-sync plan_kurse list
   - Or expand lookup in Graph API query

2. **Vereinsmitglied Role Creation**: Status 8, 9, 10 should create domainuser record if none exists - not yet implemented.

3. **Veranstaltungsteilnehmer Sync**: Registration sync not yet implemented.

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     SharePoint                                   │
├─────────────────────────────────────────────────────────────────┤
│  contacts              plan_kursteilnehmer                       │
│  ├─ Title              ├─ TeilnehmerLookupId → contact.id       │
│  ├─ FirstName          ├─ KursLookupId → Kurs code              │
│  ├─ Email              └─ StatsLookupId (1,3,13 = valid)        │
│  └─ StatusLookupId                                               │
└──────────────┬────────────────────────────┬─────────────────────┘
               │                            │
               ▼                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Odoo                                      │
├─────────────────────────────────────────────────────────────────┤
│  res.partner                                                     │
│  ├─ ms_contact_id ◄─────────────────────┘                       │
│  ├─ ms_contact_status                                            │
│  ├─ ms_kurs_level ◄──────── evaluated from kursteilnehmer       │
│  └─ dasei_domaincode ◄────── computed (highest priority)        │
│                                                                  │
│  crearis.domainuser (existing)                                   │
│  └─ domain_code ────────────► feeds into dasei_domaincode       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Course Model (dasei.course) — D3

Represents annual training cohorts synced from SharePoint plan_kurse.

### Fields

| Field | Type | Purpose |
|-------|------|---------|
| `code` | Char | Course code (K26, K27) |
| `name` | Char | Full course name |
| `year` | Integer | Year |
| `location` | Char | Location (Witten, Kassel, Online) |
| `date_start` | Datetime | Course start |
| `date_end` | Datetime | Course end |
| `ms_item_id` | Char | SharePoint item ID |
| `domain_code_id` | Many2one | Optional website mapping |

### SharePoint → Odoo Mapping (plan_kurse)

| SharePoint | Odoo |
|------------|------|
| Title | name |
| KursNr | code |
| Jahr | year |
| Ort | location |
| Startdatum | date_start |
| Enddatum | date_end |

---

## Registration Sync (D4)

Syncs event registrations from SharePoint plan_veranstaltungsteilnehmer.

### Status Mapping (plan_teilnahmestatus → registration state)

```python
STATUS_TO_REGISTRATION_STATE = {
    12: 'new',      # Angebot
    5: 'demo',      # vorbehaltlich
    1: 'draft',     # unbestätigt
    13: 'open',     # bestätigt
    3: 'done',      # vollständig (attended)
    8: 'cancel',    # storniert
    6: 'no_show',   # abwesend
    4: 'partial',   # teilweise
}
```

### SharePoint → Odoo Mapping (plan_veranstaltungsteilnehmer)

| SharePoint | Odoo |
|------------|------|
| TeilnehmerLookupId | partner_id (via ms_contact_id) |
| VeranstaltungLookupId | event_id (via ms_id) |
| StatusLookupId | state (mapped) |
| UE | units |
| Bemerkung | internal_notes |

---

## Cron Jobs (D6)

| Job | Interval | Model Method |
|-----|----------|--------------|
| Sync Courses | Daily | `sync_kurse(company)` |
| Sync Registrations | 4 hours | `sync_registrations(company)` |

Both jobs iterate over companies with `ms_agenda_configured=True`.

---

## Testing

### Manual Test: Verify Domaincode Computation

```python
# In Odoo shell
partner = env['res.partner'].browse(123)
partner.ms_contact_status = 1
partner.ms_kurs_level = 'ZR'
partner._compute_dasei_domaincode()
print(partner.dasei_domaincode)  # Should be 'dasei3'
```

### Test Priority Order

```python
# Partner with both status 1 (dasei1) and domainuser dasei3
partner.ms_contact_status = 1
partner.ms_kurs_level = 'ME'  # dasei1
env['crearis.domainuser'].create({
    'partner_id': partner.id,
    'domain_code': 'dasei3'
})
partner._compute_dasei_domaincode()
print(partner.dasei_domaincode)  # Should be 'dasei3' (higher priority)
```

---

## Post-Init Hook & Website Management

### hooks.py

The module uses a `post_init_hook` to automatically create DASEi websites on installation:

```python
# In __manifest__.py
'post_init_hook': 'post_init_hook',
```

### DASEi Website Creation

```python
DASEI_DOMAIN_CODES = {
    'dasei0': {'name': 'DASEi Quick Entry', 'sequence': 100},
    'dasei1': {'name': 'DASEi Einstiege', 'sequence': 101},
    'dasei2': {'name': 'DASEi Grundstufe', 'sequence': 102},
    'dasei3': {'name': 'DASEi Aufbaustufe', 'sequence': 103},
}
```

On module install, `_check_and_create_dasei_websites()` creates missing websites and their XMLIds.

### Utility Functions

| Function | Purpose |
|----------|--------|
| `check_dasei_websites(env)` | Check status, optionally raise error |
| `create_dasei_websites(env, company)` | Manually create missing websites |
| `ensure_event_type_xmlids(env)` | Create XMLIds for synced event types |

### Shell Usage

```python
# Check website status
from odoo.addons.agenda_dasei.hooks import check_dasei_websites
check_dasei_websites(env)

# Create XMLIds for event types (after SharePoint sync)
from odoo.addons.agenda_dasei.hooks import ensure_event_type_xmlids
ensure_event_type_xmlids(env)
```

---

## Event Package Products (Grundkurs)

The module creates 4 product templates for the DASEi Grundkurs program, each linked to specific event types via `crearis_event_package`.

### Product Templates (data/product_template_data.xml)

| Product | XMLId | Domain | Event Types | Price |
|---------|-------|--------|-------------|-------|
| Modul A: Einstiege | `product_modul_a` | dasei1 | A0-A5 | €1,100 |
| Modul B: Szenische Themenarbeit | `product_modul_b` | dasei2 | B1-B8 | €1,320 |
| Modul C: Pädagogische Regie | `product_modul_c` | dasei2 | C0-C8 | €1,320 |
| Modul D: Kolloquium & Projekt | `product_modul_d` | dasei2 | D0-D4 | €1,100 |

### How It Works

1. **Event types are synced** from SharePoint (via `crearis_agenda`)
2. **XMLIds are created** by `ensure_event_type_xmlids()` during `post_init_hook`
3. **Products reference** event types via XMLIds: `ref('agenda_dasei.event_type_a1')`
4. **Products are linked** to websites via `website_id` field

### Example Product Definition

```xml
<record id="product_modul_a" model="product.template">
    <field name="name">Modul A: Einstiege in's Theaterspiel</field>
    <field name="detailed_type">event_package</field>
    <field name="list_price">1100.00</field>
    <field name="website_id" ref="agenda_dasei.website_dasei1"/>
    <field name="package_edition_code">M18E</field>
    <field name="package_event_type_ids" eval="[(6, 0, [
        ref('agenda_dasei.event_type_a0'),
        ref('agenda_dasei.event_type_a1'),
        ref('agenda_dasei.event_type_a2'),
        ref('agenda_dasei.event_type_a3'),
        ref('agenda_dasei.event_type_a4'),
        ref('agenda_dasei.event_type_a5'),
    ])]"/>
</record>
```

### Event Type XMLId Pattern

XMLIds are generated with pattern: `agenda_dasei.event_type_{lowercase_name}`

| Event Type Name | XMLId |
|-----------------|-------|
| A1 | `agenda_dasei.event_type_a1` |
| B2 | `agenda_dasei.event_type_b2` |
| ME | `agenda_dasei.event_type_me` |

---

## Server Actions (website_data.xml)

Two server actions are available from the Website list view:

| Action | Purpose |
|--------|--------|
| Check DASEi Websites | Shows status of dasei0-3 websites |
| Create Missing DASEi Websites | Creates any missing websites |

---

*Last updated: 2026-01-27*
