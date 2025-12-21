# Action Plan: 3 Modules Implementation

*Created: 2025-12-21*
*Based on: 3_modules_prompt.md, sharepoint_tables.md, crearis_agenda_implementation.md*

---

## Executive Summary

This plan covers the implementation of **three Odoo modules** for DASEi's event management and SharePoint synchronization:

| Module | Type | Purpose |
|--------|------|---------|
| `crearis` | **UPDATE** | Add event stages, event types, units field, template system |
| `crearis_agenda` | **NEW** | SharePoint sync engine with JSONB config, version-controlled sync |
| `agenda_dasei` | **NEW** | DASEi-specific partner status → domaincode mapping |

**Dependency chain**: `crearis` → `crearis_agenda` → `agenda_dasei`

---

## Pre-Implementation: Microsoft API Testing

### Objective
Manually test SharePoint Graph API access before writing any sync code.

### Test Queries (using curl or Postman)

```bash
# 1. Get site ID
GET https://graph.microsoft.com/v1.0/sites/dasei.sharepoint.com:/sites/api1

# 2. List all lists
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists

# 3. Get plan_veranstaltungscodes (event types)
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/E4B1128D-2709-480D-82D0-77F42605FD1A/items?$expand=fields

# 4. Get plan_veranstaltungen (events) - filtered
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/BA5CFB7C-CFE7-4EFD-BA0A-65F9019D5A53/items?$expand=fields&$filter=fields/StatusLookupId in (3,10,14,15,16,17,18,19,25,33)

# 5. Get plan_referenten (speakers)
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/4BFD63EA-425C-4164-9550-2A193F7F98C9/items?$expand=fields

# 6. NEW: Get contacts
GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{contacts-guid}/items?$expand=fields
```

### Validation Checklist
- [ ] Authentication works (bearer token)
- [ ] Can read list items with $expand=fields
- [ ] Can filter by StatusLookupId
- [ ] Can PATCH items (write-back test)
- [ ] Confirm field names match documentation
- [ ] Get GUIDs for new tables (contacts, plan_kursteilnehmer, plan_veranstaltungsteilnehmer)

---

## Module 1: `crearis` (UPDATE)

### 1.1 New Field: `units` on event.event

```python
# models/event.py
units = fields.Float(
    string="Units",
    digits=(10, 2),
    help="Number of units/credits for this event (e.g., 2.5 UE)"
)
```

**View update**: Add to event form, group with date_begin/date_end

### 1.2 Event Stages (data/event_stage_data.xml)

| ID | Name (DE) | Sequence | Fold | Use Case |
|----|-----------|----------|------|----------|
| 1 | Planung | 1 | False | Initial planning |
| 2 | Ausgeschrieben | 64 | False | Published, open for registration |
| 3 | Läuft | 128 | False | In progress |
| 4 | Durchgeführt | 512 | True | Completed successfully |
| 5 | Abgesagt | 1024 | True | Cancelled |
| 6 | Archiviert | 2048 | True | Archived |

**Key rule**: Stages with `sequence >= 512` block backward transitions.

```python
# models/event.py (constraint)
@api.constrains('stage_id')
def _check_stage_backward(self):
    """Prevent backward movement from sequence >= 512"""
    for event in self:
        if event.stage_id.sequence >= 512:
            # Check if trying to move to lower sequence stage
            # This should be a user-facing warning, not hard constraint
            pass
```

### 1.3 Event Types (data/event_type_data.xml)

**Base types** (is_template_code=False, company_id=null):

| ID | Name (de_DE) | Sequence | Notes |
|----|--------------|----------|-------|
| 1 | Workshop (4-8 Std.) | 32 | Short events |
| 2 | workshop > Kurz | 64 | Sub-type |
| 3 | workshop > Mehrtägig | 96 | Multi-day |
| 4 | Kurs (4-10 Monate) | 256 | Course |
| 5 | kurs > Kurz | 512 | Short course |
| 6 | kurs > Fortlaufend | 768 | Ongoing |
| 7 | Projekt (5-9 Tage) | 2048 | Project |
| 8 | projekt > Kurz | 4096 | Short project |
| 9 | projekt > Mehrphasig | 6144 | Multi-phase |
| 10 | Konferenz | 16384 | Conference |
| 11 | Auftritt | 32768 | Performance |

**Company-specific types** (is_template_code=True) are synced from SharePoint `plan_veranstaltungscodes`.
They link to base types via `template_parent_id` by matching `sequence`.

### 1.4 Event Type Schema Extension

```python
# models/event_type.py
class EventType(models.Model):
    _inherit = 'event.type'
    
    # Template system
    is_template_code = fields.Boolean(
        string="Is Template Code",
        default=False,
        help="If True, name is a shortcode and has template_parent"
    )
    template_parent_id = fields.Many2one(
        'event.type',
        string="Template Parent",
        domain=[('is_template_code', '=', False)],
        help="Link to base event type (filter: is_template_code=False)"
    )
    
    # Template content fields (synced from SharePoint)
    template_cimg = fields.Text(
        string="Hero-Image-Link",
        translate=False,
        default='',
        help="xmlid or public url for hero and thumbnail image"
    )
    template_teasertext = fields.Text(
        string="Teaser Text",
        help="Short description for listings"
    )
    template_units = fields.Float(
        string="Teaching Units",
        digits=(10, 2),
        help="Default units/credits for events of this type"
    )
    template_heading = fields.Text(
        string="Website Heading",
        help="Heading for website display"
    )
    template_ext = fields.Json(
        string="Template Extensions",
        default=dict,
        help="JSONB for additional template settings"
    )
    template_config = fields.Integer(
        string="Config Flags",
        default=0,
        help="Bitmask of configuration flags"
    )
    
    # Sync tracking
    ms_id = fields.Char(string="SharePoint ID", index=True)
    ms_synced = fields.Boolean(string="Synced from SharePoint", default=False)
    ms_version = fields.Char(string="SharePoint Version", help="oversion for conflict detection")
    
    # Company isolation
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        help="Empty = available to all companies"
    )
```

### 1.5 Implementation Tasks

- [ ] Add `units` field to event.event
- [ ] Create event_stage_data.xml with 6 stages
- [ ] Create event_type_data.xml with 11 base types
- [ ] Add template system fields to event.type:
  - [ ] is_template_code (Boolean)
  - [ ] template_parent_id (Many2one)
  - [ ] template_cimg (Text - hero image link)
  - [ ] template_teasertext (Text)
  - [ ] template_units (Float)
  - [ ] template_heading (Text)
  - [ ] template_ext (Json)
  - [ ] template_config (Integer - bitmask)
- [ ] Add ms_* tracking fields to event.type (ms_id, ms_synced, ms_version)
- [ ] Add company_id to event.type
- [ ] Update event form view (units, stage filtering)
- [ ] Update event.type form view (add template fields, make accessible from crearis menu)
- [ ] Add stage backward-transition warning

---

## Module 2: `crearis_agenda` (NEW)

### 2.1 Module Structure

```
crearis_agenda/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── res_company.py      # ms_agenda_api config
│   ├── event_type.py       # Sync extensions
│   ├── event_event.py      # Sync extensions
│   └── sync_log.py         # Audit trail
├── services/
│   ├── __init__.py
│   ├── ms_graph_client.py  # API wrapper
│   └── sync_engine.py      # Sync orchestration
├── data/
│   └── cron_data.xml       # Scheduled sync
├── security/
│   └── ir.model.access.csv
└── views/
    ├── res_company_views.xml
    └── sync_menu_views.xml
```

### 2.2 Company Configuration (JSONB Pattern)

```python
# models/res_company.py
class ResCompany(models.Model):
    _inherit = 'res.company'
    
    # Simple credential fields
    ms_agenda_tenant_id = fields.Char(string="Tenant ID")
    ms_agenda_client_id = fields.Char(string="Client ID")
    ms_agenda_client_secret = fields.Char(string="Client Secret", password=True)
    ms_agenda_site_id = fields.Char(string="Site ID")
    
    # JSONB for list GUIDs
    ms_agenda_api = fields.Json(
        string="MS Agenda API Config",
        default=lambda self: self._default_ms_agenda_api()
    )
    
    # Computed accessors (following web.options.abstract pattern)
    ms_list_veranstaltungen = fields.Char(
        compute='_compute_ms_agenda_fields',
        inverse='_inverse_ms_list_veranstaltungen',
        string="List: Veranstaltungen"
    )
    ms_list_veranstaltungscodes = fields.Char(
        compute='_compute_ms_agenda_fields',
        inverse='_inverse_ms_list_veranstaltungscodes',
        string="List: Veranstaltungscodes"
    )
    # ... more computed accessors for each list GUID
    
    @api.model
    def _default_ms_agenda_api(self):
        return {
            'list_veranstaltungen': '',
            'list_veranstaltungscodes': '',
            'list_referenten': '',
            'list_planungsstatus': '',
            'list_seminarzeiten': '',
            'list_contacts': '',
            'list_kursteilnehmer': '',
            'list_veranstaltungsteilnehmer': '',
        }
    
    @api.depends('ms_agenda_api')
    def _compute_ms_agenda_fields(self):
        for rec in self:
            api = rec.ms_agenda_api or {}
            rec.ms_list_veranstaltungen = api.get('list_veranstaltungen', '')
            rec.ms_list_veranstaltungscodes = api.get('list_veranstaltungscodes', '')
            # ... etc
    
    ms_agenda_configured = fields.Boolean(
        compute='_compute_ms_agenda_configured',
        string="Agenda Configured"
    )
    
    @api.depends('ms_agenda_tenant_id', 'ms_agenda_client_id', 'ms_agenda_site_id')
    def _compute_ms_agenda_configured(self):
        for rec in self:
            rec.ms_agenda_configured = bool(
                rec.ms_agenda_tenant_id and 
                rec.ms_agenda_client_id and 
                rec.ms_agenda_site_id
            )
```

### 2.3 Sync Levels (Progressive Trust)

```python
class SyncLevel:
    INIT = 'init'      # First sync: full import, Odoo creates records
    SLAVE = 'slave'    # SharePoint drives updates, Odoo follows
    MASTER = 'master'  # Odoo drives updates, SharePoint follows
```

| Field | init | slave | master |
|-------|------|-------|--------|
| All SP fields | SP→Odoo | SP→Odoo | Odoo→SP |
| oevent_id (write-back) | Odoo→SP | Odoo→SP | Odoo→SP |
| version | Store | Compare | Compare+Update |

**Promotion logic**: After full review in Odoo, admin promotes from slave→master.

### 2.4 Sync Modes

#### Entity Mode (version-controlled)
For `event.type` and `event.event`:
```python
def sync_entity(self, sp_record, odoo_record, sync_level):
    sp_version = sp_record.get('@odata.etag')
    
    if sync_level == 'init':
        # Always import, store version
        return self._create_or_update(sp_record)
    
    if odoo_record and odoo_record.ms_version == sp_version:
        # No change, skip
        return 'unchanged'
    
    if sync_level == 'slave':
        # SP wins, update Odoo
        return self._update_from_sp(sp_record, odoo_record)
    
    if sync_level == 'master':
        # Odoo wins, push to SP (if Odoo changed)
        if odoo_record.write_date > odoo_record.ms_last_sync:
            return self._push_to_sp(odoo_record)
        else:
            # Accept SP update
            return self._update_from_sp(sp_record, odoo_record)
```

#### Relation Mode (simple takeover)
For lookup tables like `plan_referenten`:
```python
def sync_relation(self, sp_records, model_name, mapping_field):
    """Simple sync - SP always wins, no version tracking"""
    for sp_record in sp_records:
        odoo_record = self.env[model_name].search([
            (mapping_field, '=', sp_record['id'])
        ], limit=1)
        
        if not odoo_record:
            self.env[model_name].create(self._map_fields(sp_record))
        else:
            odoo_record.write(self._map_fields(sp_record))
```

### 2.5 Template Application (One-Time on Create)

```python
def _apply_event_type_template(self, event_type, event_vals):
    """Apply template defaults to new event - ONE TIME ONLY"""
    if not event_type.template_parent_id:
        return event_vals
    
    template = event_type.template_parent_id
    
    # Copy template defaults if not set
    template_fields = ['has_sessions', 'seats_max', 'auto_confirm']
    for field in template_fields:
        if field not in event_vals:
            event_vals[field] = getattr(template, field)
    
    return event_vals
```

### 2.6 Helper: is_local_domaincode()

```python
def is_local_domaincode(self, code):
    """Check if domaincode belongs to current company's website"""
    company = self.env.company
    websites = self.env['website'].search([
        ('company_id', '=', company.id)
    ])
    local_codes = websites.mapped('domain_code')
    return code in local_codes
```

### 2.7 Status Filtering for Events

From SharePoint `plan_planungsstatus`:
```python
SYNC_STATUS_IDS = [3, 10, 14, 15, 16, 17, 18, 19, 25, 33]  # Active planning statuses
```

Events with `StatusLookupId` in this list are synced; others are ignored or archived.

### 2.8 Event Tags for Status Extensions

When `plan_veranstaltungen.Kennzeichnung` contains special markers:
```python
def _parse_kennzeichnung(self, value):
    """Extract status tags from Kennzeichnung field"""
    tags = []
    if '#ORGA#' in (value or ''):
        tags.append('orga')  # Organizational event
    if '#TEAM#' in (value or ''):
        tags.append('team')  # Team-only event
    if '#USER#' in (value or ''):
        tags.append('user')  # User-visible event
    return tags
```

### 2.9 Implementation Tasks

- [ ] Create module scaffold
- [ ] Add JSONB config fields to res.company
- [ ] Create computed accessors for JSONB (following web.options pattern)
- [ ] Implement MS Graph client (adapt from ms_taxonomy_sync)
- [ ] Implement sync_entity logic with version control
- [ ] Implement sync_relation for lookup tables
- [ ] Add sync level field to company config
- [ ] Implement template application on event create
- [ ] Add is_local_domaincode() helper
- [ ] Implement status filtering
- [ ] Parse Kennzeichnung for tags
- [ ] Add sync log model
- [ ] Create sync menu items
- [ ] Add cron job for scheduled sync (1x per hour)

---

## Module 3: `agenda_dasei` (NEW)

### 3.1 Module Structure

```
agenda_dasei/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── res_partner.py      # Status → domaincode mapping
├── data/
│   └── status_mapping_data.xml
└── security/
    └── ir.model.access.csv
```

### 3.2 Partner Status → Domaincode Mapping

From `contacts.Status` (lookup to `plan_contacts_status`):

| Status ID | Meaning | Target Domaincode | Sync Behavior |
|-----------|---------|-------------------|---------------|
| 1 | Active participant | dasei1 (min) | Further evaluate via plan_kursteilnehmer |
| 2 | Former participant (level 2) | dasei2 | Direct mapping |
| 3 | Former participant (level 3) | dasei3 | Direct mapping |
| 4 | Aborted participation | dasei1 | Direct mapping |
| 5 | Quick entry | dasei0 | Direct mapping |
| 8 | Vereinsmitglied (member) | dasei (role: member) | Only if no existing entries |
| 9 | Vereinsmitglied (participant) | dasei (role: participant) | Only if no existing entries |
| 10 | Partner | dasei (role: partner) | Only if no existing entries |

**Note**: ~60% of contacts are kursteilnehmer. Status 8, 9, 10 require special handling:
- Only sync if partner has no existing domainuser entries
- Otherwise, manual configuration required

**Filter**: Only sync contacts with status 1-5, 8-10 (ignore others)

### 3.2.1 Kursteilnehmer Evaluation (for Status=1)

When `contacts.Status = 1` (active participant), further evaluate via `plan_kursteilnehmer`:

**Lookup**: Find kursteilnehmer records with `plan_teilnahmestatus` in (1, 3, 13)

**Kurs field priority** (most advanced wins):

| Kurs Pattern | Examples | Domaincode | Level |
|--------------|----------|------------|-------|
| `ME`, `NE` | ME, NE | dasei1 | Einstiege (Module A) |
| `M?`, `N?` | M_, MB, MA, NA, NB | dasei2 | Grundstufe (Modules B/C/D) |
| `ZR`, `ZT` | ZR, ZT | dasei3 | Aufbaustufe (highest) |

**Algorithm**:
```python
def _evaluate_kursteilnehmer(self, partner):
    """Find highest domaincode from kursteilnehmer records"""
    KURS_PRIORITY = {
        'dasei3': ['ZR', 'ZT'],
        'dasei2': ['M', 'N'],  # Any M?/N? pattern (except ME/NE)
        'dasei1': ['ME', 'NE'],
    }
    VALID_STATUS = [1, 3, 13]  # plan_teilnahmestatus
    
    kursteilnehmer = self._fetch_kursteilnehmer_for_contact(partner.ms_contact_id)
    
    highest_level = 0
    result_code = 'dasei1'  # minimum for status=1
    
    for kt in kursteilnehmer:
        if kt.get('teilnahmestatus') not in VALID_STATUS:
            continue
        
        kurs = kt.get('Kurs', '')
        
        if kurs in ('ZR', 'ZT'):
            return 'dasei3'  # Highest, return immediately
        elif kurs.startswith(('M', 'N')) and kurs not in ('ME', 'NE'):
            if highest_level < 2:
                highest_level = 2
                result_code = 'dasei2'
        elif kurs in ('ME', 'NE'):
            if highest_level < 1:
                highest_level = 1
                result_code = 'dasei1'
    
    return result_code
```

### 3.3 Model Extension

```python
# models/res_partner.py
class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    # SharePoint sync fields
    ms_contact_id = fields.Char(string="SP Contact ID", index=True)
    ms_contact_status = fields.Integer(string="Contact Status (from plan_contacts_status)")
    ms_kursteilnehmer_id = fields.Char(string="SP Kursteilnehmer ID", index=True)
    ms_version = fields.Char(string="SharePoint oversion")
    
    # Computed highest domaincode
    dasei_domaincode = fields.Char(
        compute='_compute_dasei_domaincode',
        store=True,
        string="DASEi Domaincode"
    )
    
    # Existing domainuser records (from crearis)
    domainuser_ids = fields.One2many(
        'crearis.domainuser',
        'partner_id',
        string="Domain Users"
    )
    
    @api.depends('ms_contact_status', 'domainuser_ids', 'domainuser_ids.domain_code')
    def _compute_dasei_domaincode(self):
        """Compute highest domaincode from contact status or domainuser records"""
        CODE_PRIORITY = {
            'dasei': 100,   # Vereinsmitglied (status 8, 9, 10)
            'dasei3': 30,   # Former participant level 3
            'dasei2': 20,   # Former participant level 2
            'dasei1': 10,   # Active/aborted participant
            'dasei0': 1,    # Quick entry
        }
        
        for partner in self:
            # Get domaincode from contact status
            status_code = partner._status_to_domaincode(partner.ms_contact_status)
            
            # Get highest from domainuser records
            du_codes = partner.domainuser_ids.mapped('domain_code')
            
            # Combine and find highest priority
            all_codes = [status_code] + list(du_codes) if status_code else list(du_codes)
            
            if not all_codes:
                partner.dasei_domaincode = False
                continue
            
            highest = max(all_codes, key=lambda c: CODE_PRIORITY.get(c, 0))
            partner.dasei_domaincode = highest
    
    def _status_to_domaincode(self, status, kursteilnehmer_code=None):
        """Map contacts.Status (plan_contacts_status ID) to domaincode
        
        For status=1, kursteilnehmer_code overrides if provided
        """
        if status == 1 and kursteilnehmer_code:
            return kursteilnehmer_code  # From _evaluate_kursteilnehmer()
        
        STATUS_MAP = {
            1: 'dasei1',   # Active participant (default, may be overridden)
            2: 'dasei2',   # Former participant level 2
            3: 'dasei3',   # Former participant level 3
            4: 'dasei1',   # Aborted participation
            5: 'dasei0',   # Quick entry
            8: 'dasei',    # Vereinsmitglied (member role)
            9: 'dasei',    # Vereinsmitglied (participant role)
            10: 'dasei',   # Partner role
        }
        return STATUS_MAP.get(status, False)
    
    def _evaluate_kurs_level(self, kurs):
        """Evaluate single Kurs value to domaincode
        
        ZR/ZT → dasei3 (highest)
        M?/N? (except ME/NE) → dasei2
        ME/NE → dasei1
        """
        if not kurs:
            return None, 0
        if kurs in ('ZR', 'ZT'):
            return 'dasei3', 3
        if kurs.startswith(('M', 'N')) and kurs not in ('ME', 'NE'):
            return 'dasei2', 2
        if kurs in ('ME', 'NE'):
            return 'dasei1', 1
        return None, 0
    
    def _should_sync_vereinsmitglied(self):
        """Status 8,9,10 only sync if no existing domainuser entries"""
        return len(self.domainuser_ids) == 0
```

### 3.4 Sync Integration with crearis_agenda

```python
def sync_kursteilnehmer(self):
    """Sync plan_kursteilnehmer → res.partner"""
    sp_records = self._fetch_sp_list('list_kursteilnehmer')
    
    for rec in sp_records:
        partner = self.env['res.partner'].search([
            ('ms_kursteilnehmer_id', '=', rec['id'])
        ], limit=1)
        
        vals = {
            'ms_kursteilnehmer_id': rec['id'],
            'ms_stand': rec['fields'].get('Stand', 0),
            'name': rec['fields'].get('Nachname'),
            'email': rec['fields'].get('Email'),
            # ... other fields
        }
        
        if partner:
            partner.write(vals)
        else:
            # Match by email first
            partner = self.env['res.partner'].search([
                ('email', '=', vals.get('email'))
            ], limit=1)
            if partner:
                partner.write(vals)
            else:
                self.env['res.partner'].create(vals)
```

### 3.5 Implementation Tasks

- [ ] Create module scaffold
- [ ] Add ms_kursteilnehmer_id and ms_stand to res.partner
- [ ] Implement _stand_to_domaincode mapping
- [ ] Implement dasei_domaincode computed field
- [ ] Add sync method for plan_kursteilnehmer
- [ ] Create status_mapping_data.xml with Stand→domaincode rules
- [ ] Add to partner form view
- [ ] Test domaincode computation

---

## SharePoint Tables Reference (Quick Reference)

### Existing Tables
| Table | GUID | Maps To |
|-------|------|---------|
| plan_veranstaltungen | BA5CFB7C-CFE7-4EFD-BA0A-65F9019D5A53 | event.event |
| plan_veranstaltungscodes | E4B1128D-2709-480D-82D0-77F42605FD1A | event.type |
| plan_referenten | 4BFD63EA-425C-4164-9550-2A193F7F98C9 | res.users (mapping) |
| plan_planungsstatus | 6ADC07D7-8208-4370-AFBF-67B223F2C996 | event.stage |
| plan_seminarzeiten | 6BBE92C5-82C5-40E7-8C5F-D6CB3018EC23 | schedule (memo) |
| plan_contacts_status | 74b74ebc-9ece-4101-80f0-79316c17f6b3 | status mapping |

### New Tables (GUIDs confirmed)
| Table | GUID | Maps To |
|-------|------|---------|
| contacts | 7a77d6af-3a91-4109-8f56-9dbac73d2fa4 | res.partner |
| plan_kursteilnehmer | 2bf5f8e7-ebca-4a8b-b11e-feaee6a30287 | res.partner (course status) |
| plan_veranstaltungsteilnehmer | C9E05737-4C47-4E0F-A6B6-C6D6F3FBE88D | event.registration |

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
1. [ ] Microsoft API testing (manual queries)
2. [ ] Update crearis: add units field
3. [ ] Update crearis: create event_stage_data.xml
4. [ ] Update crearis: create event_type_data.xml
5. [ ] Update crearis: add template fields to event.type

### Phase 2: Sync Engine (Week 2)
1. [ ] Create crearis_agenda scaffold
2. [ ] Implement res.company JSONB config
3. [ ] Port MS Graph client
4. [ ] Implement sync_entity for event.type
5. [ ] Implement sync_entity for event.event
6. [ ] Test sync cycle

### Phase 3: Partner Sync (Week 3)
1. [ ] Create agenda_dasei scaffold
2. [ ] Implement partner status mapping
3. [ ] Sync plan_kursteilnehmer → res.partner
4. [ ] Implement dasei_domaincode computation
5. [ ] Add to partner views

### Phase 4: Registration Sync (Week 4)
1. [ ] Sync plan_veranstaltungsteilnehmer → event.registration
2. [ ] Implement domainuser creation from registrations
3. [ ] Test full flow

### Phase 5: Polish & Testing
1. [ ] Add sync logging
2. [ ] Add cron jobs
3. [ ] UI polish (menus, buttons)
4. [ ] Integration testing
5. [ ] Documentation

---

## Open Questions for Q&A

✅ All questions answered!

| # | Question | Answer |
|---|----------|--------|
| 1 | Vereinsmitglied detection | Status 8, 9 in contacts.Status |
| 2 | Contacts vs Kursteilnehmer | ~60% of contacts are kursteilnehmer |
| 3 | GUIDs | All confirmed |
| 4 | Sync frequency | 1x per hour |
| 5 | Write-back fields | YES - need more than oevent_id, oevent_type_id, opartner_id, oversion |
| 6 | Kursteilnehmer evaluation | By Kurs field + plan_teilnahmestatus (see 3.4) |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| API rate limiting | Implement backoff, batch requests |
| Data conflicts | Version-based detection, Odoo-wins policy |
| Missing lookups | Pre-sync lookup tables before main sync |
| Large datasets | Pagination, delta sync by modified date |
| Token expiry | Auto-refresh, store expiry time |

---

*Next step: Manual Microsoft API testing with credentials*

---

## Changelog

### Initial Version
- Created based on 3_modules_prompt.md
- Incorporated yesterday's crearis_agenda_implementation.md decisions
- Added new SharePoint tables (contacts, kursteilnehmer, veranstaltungsteilnehmer)
- Defined sync levels (init/slave/master) and sync modes (entity/relation)
- Defined partner status → domaincode mapping for agenda_dasei
