# Crearis Agenda Module - Implementation Plan

## Overview

The `crearis_agenda` module provides bi-directional synchronization between SharePoint lists (plan_veranstaltungen, plan_veranstaltungscodes) and Odoo models (event.event, event.type). This enables seamless integration between Microsoft SharePoint planning data and Odoo's event management system.

---

## 1. Module Scope

### 1.1 SharePoint → Odoo Sync (Read)
- **plan_veranstaltungscodes** → `event.type` (mostly static, updates every 1-3 months)
- **plan_veranstaltungen** → `event.event` (within status-range: Hauptstatus `[angekündigt]` + `AKTUELL`)

### 1.2 Odoo → SharePoint Sync (Write-back)
- Within the defined status-range, edits happen **only in Odoo**
- Changes must be synced back to SharePoint to keep data consistent
- Affected status IDs: 3, 10, 14, 15, 16, 17, 18, 19, 25, 33

### 1.3 Related Tables (Read-only lookup)
- **plan_planungsstatus** - Status definitions (static reference)
- **plan_referenten** - Instructors/speakers (maps to user_id)
- **plan_raeume** - Rooms/venues (maps to address_id)
- **plan_seminarzeiten** - Schedule templates (maps to schedule field)

---

## 2. Module Structure

```
crearis_agenda/
├── __init__.py
├── __manifest__.py
├── README.md
├── models/
│   ├── __init__.py
│   ├── res_company.py         # Company config fields for MS API
│   ├── event_type.py          # event.type extension with ms_* fields + company_id
│   ├── event_event.py         # event.event extension with MS sync
│   └── agenda_status.py       # Status mapping model (optional)
├── services/
│   ├── __init__.py
│   └── ms_graph_client.py     # Microsoft Graph API client
├── views/
│   ├── res_company_views.xml  # Company form config section
│   ├── event_type_views.xml   # Event type form with company_id field
│   ├── event_event_views.xml  # Event form with filtered event_type_id
│   └── crearis_agenda_menu.xml # Menu items for sync actions
├── security/
│   ├── ir.model.access.csv
│   └── crearis_agenda_security.xml
├── data/
│   └── ir_cron_data.xml       # Optional auto-sync cron job
└── wizard/
    └── sync_wizard.py         # Manual sync wizard (optional)
```

---

## 3. Field Mappings

### 3.1 plan_veranstaltungscodes → event.type

| SharePoint Field | Type | Odoo Field | Type | Notes |
|-----------------|------|------------|------|-------|
| `id` | Number | `ms_id` | Integer | Primary key for sync |
| `Title` | Text | `name` | Char | Event type code |
| `Veranstaltungstitel` | Text | `note` | Html | Event type title/description |
| `Kurzbeschreibung` | Text | `ms_kurzbeschreibung` | Text | Short description |
| `Detailbeschreibung` | Text | `ms_detailbeschreibung` | Html | Detailed description |
| `UE` | Number | `ms_ue` | Float | Teaching units |
| `TeaserText` | Text | `ms_teaser_text` | Text | Teaser text |
| `CloudinaryCode` | Text | `ms_cloudinary_code` | Char | Image reference |
| `Status` | Number | `ms_status` | Integer | Internal status |
| `Kalendertage` | Text | `ms_kalendertage` | Char | Calendar days info |
| `Standardverlauf` | Yes/No | `ms_standardverlauf` | Boolean | Standard flow |
| `oevent_type_id` | Number | - | - | Written back after create |
| `Modified` | DateTime | `ms_last_modified` | Datetime | Sync timestamp |
| - | - | `company_id` | M2O | **NEW**: Company restriction (null=all) |

**Important**: The `company_id` field on `event.type` controls visibility:
- If `company_id` is **empty/null**: Event type available for **all companies**
- If `company_id` is **set**: Event type only available for **that specific company**

### 3.2 plan_veranstaltungen → event.event

| SharePoint Field | Type | Odoo Field | Type | Notes |
|-----------------|------|------------|------|-------|
| `id` | Number | `ms_id` | Integer | Primary key for sync |
| `Title` | Text | `name` | Char | Event name |
| `Start` | DateTime | `date_begin` | Datetime | Event start |
| `Ende` | DateTime | `date_end` | Datetime | Event end |
| `VeranstaltungsCode` | Lookup | `event_type_id` | M2O | Via oevent_type_id |
| `Hauptreferent` | Lookup | `user_id` | M2O | Via ouser_id |
| `Raum` | Lookup | `address_id` | M2O | Via oaddress_id |
| `Status` | Lookup | `ms_status_id` | Integer | Status reference |
| `MinTeilnehmer` | Number | `seats_min` | Integer | Min attendees |
| `MaxTeilnehmer` | Number | `seats_max` | Integer | Max attendees |
| `UE` | Number | `ms_ue` | Float | Teaching units |
| `Seminarplan` | Lookup | - | - | Schedule template ref |
| `Seminarplan_Memo` | Text | `schedule` | Text | Custom schedule |
| `InternKommentar` | Text | `ms_intern_comment` | Char | Internal comment |
| `Orga_Info` | Text | `ms_orga_info` | Text | Organization info |
| `Orga_Team` | Text | `ms_orga_team` | Text | Team info |
| `OffenesProgramm` | Yes/No | `ms_offenes_programm` | Boolean | Open program flag |
| `Untertermin` | Yes/No | `ms_untertermin` | Boolean | Sub-event flag |
| `Meldefrist` | DateTime | `ms_meldefrist` | Datetime | Registration deadline |
| `oevent_id` | Number | - | - | Written back after create |
| `Modified` | DateTime | `ms_last_modified` | Datetime | Sync timestamp |

---

## 4. Company Configuration

### 4.1 New Fields on res.company

```python
class Company(models.Model):
    _inherit = 'res.company'
    
    # Microsoft API Configuration
    ms_agenda_api_key = fields.Char('MS API Key', help='Microsoft Graph API Client Secret')
    ms_agenda_client_id = fields.Char('MS Client ID', help='Azure AD Application Client ID')
    ms_agenda_tenant_id = fields.Char('MS Tenant ID', help='Azure AD Tenant ID')
    ms_agenda_base_url = fields.Char('SharePoint Base URL', default='https://graph.microsoft.com/v1.0')
    ms_agenda_site_id = fields.Char('SharePoint Site ID', help='Format: hostname,site-guid,web-guid')
    
    # List GUIDs
    ms_agenda_list_veranstaltungen = fields.Char('List: plan_veranstaltungen', 
        help='GUID: BA5CFB7C-CFE7-4EFD-BA0A-65F9019D5A53')
    ms_agenda_list_veranstaltungscodes = fields.Char('List: plan_veranstaltungscodes',
        help='GUID: E4B1128D-2709-480D-82D0-77F42605FD1A')
    ms_agenda_list_planungsstatus = fields.Char('List: plan_planungsstatus',
        help='GUID: 6ADC07D7-8208-4370-AFBF-67B223F2C996')
    ms_agenda_list_referenten = fields.Char('List: plan_referenten',
        help='GUID: 4BFD63EA-425C-4164-9550-2A193F7F98C9')
    ms_agenda_list_seminarzeiten = fields.Char('List: plan_seminarzeiten',
        help='GUID: 6BBE92C5-82C5-40E7-8C5F-D6CB3018EC23')
    
    # Sync Settings
    ms_agenda_autosync = fields.Boolean('Auto-Sync Enabled', default=False)
    ms_agenda_last_sync = fields.Datetime('Last Sync', readonly=True)
    ms_agenda_configured = fields.Boolean('Is Configured', compute='_compute_ms_agenda_configured')
    
    @api.depends('ms_agenda_api_key', 'ms_agenda_client_id', 'ms_agenda_tenant_id', 
                 'ms_agenda_site_id', 'ms_agenda_list_veranstaltungen')
    def _compute_ms_agenda_configured(self):
        for company in self:
            company.ms_agenda_configured = all([
                company.ms_agenda_api_key,
                company.ms_agenda_client_id,
                company.ms_agenda_tenant_id,
                company.ms_agenda_site_id,
                company.ms_agenda_list_veranstaltungen,
            ])
```

### 4.2 View Extension (res_company_views.xml)

Add a configuration group to `view_company_form` for MS Agenda settings:

```xml
<group string="Microsoft Agenda Sync" name="ms_agenda_config">
    <group>
        <field name="ms_agenda_client_id"/>
        <field name="ms_agenda_tenant_id"/>
        <field name="ms_agenda_api_key" password="True"/>
        <field name="ms_agenda_site_id"/>
        <field name="ms_agenda_base_url"/>
    </group>
    <group>
        <field name="ms_agenda_list_veranstaltungen"/>
        <field name="ms_agenda_list_veranstaltungscodes"/>
        <field name="ms_agenda_list_planungsstatus"/>
        <field name="ms_agenda_list_referenten"/>
        <field name="ms_agenda_list_seminarzeiten"/>
    </group>
    <group>
        <field name="ms_agenda_autosync"/>
        <field name="ms_agenda_last_sync"/>
        <field name="ms_agenda_configured" invisible="1"/>
    </group>
</group>
```

---

## 5. Sync Logic

### 5.1 Sync Direction

```
┌─────────────────────────────────────────────────────────────────┐
│                        SYNC FLOW                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  SharePoint                         Odoo                        │
│  ──────────                         ────                        │
│                                                                  │
│  plan_veranstaltungscodes  ───────►  event.type                 │
│  (read-only sync)                   (ms_synced=True)            │
│                                                                  │
│  plan_veranstaltungen      ◄──────►  event.event                │
│  (bi-directional)                   (within status range)       │
│                                                                  │
│  Status Range: Hauptstatus IN ('[angekündigt]', 'AKTUELL')      │
│  Status IDs: 3,10,14,15,16,17,18,19,25,33                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Sync Algorithm

#### 5.2.1 Event Types Sync (plan_veranstaltungscodes → event.type)

```python
def sync_event_types_from_microsoft(self):
    """
    1. Fetch all records from plan_veranstaltungscodes
    2. For each record:
       - If oevent_type_id exists: find & update in Odoo
       - If oevent_type_id is empty: create in Odoo, write back ID
    3. Mark records as ms_synced=True
    """
```

#### 5.2.2 Events Sync (plan_veranstaltungen ↔ event.event)

```python
def sync_events_from_microsoft(self):
    """
    1. Fetch records from plan_veranstaltungen WHERE Status.Hauptstatus IN ('[angekündigt]', 'AKTUELL')
    2. For each record:
       - If oevent_id exists AND ms_last_modified < SP.Modified:
         → Update Odoo record
       - If oevent_id is empty:
         → Create Odoo record, write back oevent_id to SharePoint
    3. Handle deletions (records removed from status range)
    """

def sync_events_to_microsoft(self):
    """
    1. Find Odoo events with ms_synced=True AND write_date > ms_last_sync
    2. For each changed record:
       → Update corresponding SharePoint record
       → Update ms_last_modified
    """
```

### 5.3 Status Filter

Only sync events with these status values:
| ID | Title | Hauptstatus |
|----|-------|-------------|
| 3 | [angekündigt #ORGA#] | [angekündigt] |
| 10 | [angekündigt mit Vorbehalt] | [angekündigt] |
| 14 | [angekündigt] | [angekündigt] |
| 15 | AKTUELL mit Vorbehalt | AKTUELL |
| 16 | AKTUELL #ORGA# | AKTUELL |
| 17 | [angekündigt #TEAM#] | [angekündigt] |
| 18 | AKTUELL #TEAM# | AKTUELL |
| 19 | AKTUELL | AKTUELL |
| 25 | [angekündigt #USER#] | [angekündigt] |
| 33 | AKTUELL #USER# | AKTUELL |

---

## 6. Event Type Company Filtering (NEW)

### 6.1 Model Extension: event.type

```python
class EventType(models.Model):
    _inherit = 'event.type'
    
    company_id = fields.Many2one(
        'res.company', 
        string='Company',
        default=False,  # null = available for all companies
        help="If set, this event type is only available for the specified company. "
             "Leave empty to make it available for all companies."
    )
    
    # MS sync fields...
    ms_id = fields.Integer(...)
    ms_synced = fields.Boolean(...)
    # etc.
```

### 6.2 Model Extension: event.event

Update the `event_type_id` field domain to filter by company:

```python
class EventEvent(models.Model):
    _inherit = 'event.event'
    
    # Override event_type_id to add company filter
    event_type_id = fields.Many2one(
        'event.type', 
        string='Template', 
        ondelete='set null',
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]"
    )
```

### 6.3 View Extension: event.view_event_form

Add domain filter to `event_type_id` field in the event form:

```xml
<!-- In crearis_agenda/views/event_event_views.xml -->
<record id="view_event_form_agenda" model="ir.ui.view">
    <field name="name">event.event.form.agenda</field>
    <field name="model">event.event</field>
    <field name="inherit_id" ref="event.view_event_form"/>
    <field name="arch" type="xml">
        <xpath expr="//field[@name='event_type_id']" position="attributes">
            <attribute name="domain">
                ['|', ('company_id', '=', False), ('company_id', '=', company_id)]
            </attribute>
        </xpath>
    </field>
</record>
```

### 6.4 View Extension: event.type form

Add `company_id` field to event type form:

```xml
<!-- In crearis_agenda/views/event_type_views.xml -->
<record id="view_event_type_form_agenda" model="ir.ui.view">
    <field name="name">event.type.form.agenda</field>
    <field name="model">event.type</field>
    <field name="inherit_id" ref="event.view_event_type_form"/>
    <field name="arch" type="xml">
        <xpath expr="//field[@name='name']" position="after">
            <field name="company_id" 
                   options="{'no_create': True}"
                   help="Leave empty to make this type available for all companies"/>
        </xpath>
        <!-- MS sync fields (read-only info section) -->
        <xpath expr="//sheet" position="inside">
            <group string="Microsoft Sync Info" attrs="{'invisible': [('ms_synced', '!=', True)]}">
                <field name="ms_id" readonly="1"/>
                <field name="ms_last_modified" readonly="1"/>
                <field name="ms_synced" readonly="1"/>
            </group>
        </xpath>
    </field>
</record>
```

### 6.5 Sync Behavior for company_id

When syncing from SharePoint:
- **Default**: `company_id` is set to the company that triggered the sync (the one with MS credentials configured)
- **Rationale**: Event types synced from a company's SharePoint should belong to that company
- **Override**: Manual editing in Odoo can change `company_id` to `False` (all companies) if needed

```python
def _map_event_type_fields(self, ms_record):
    """Map SharePoint fields to event.type, setting company_id to sync company."""
    return {
        'ms_id': ms_record.get('id'),
        'name': ms_record.get('fields', {}).get('Title'),
        # ... other fields ...
        'company_id': self.env.company.id,  # Set to syncing company
        'ms_synced': True,
    }
```

---

## 7. Menu Integration

### 7.1 Menu Structure (under Crearis menu)

```xml
<!-- Agenda Sync submenu -->
<menuitem id="menu_crearis_agenda" name="Agenda Sync" parent="crearis.menu_crearis_settings"/>

<!-- Manual sync action (only visible if company is configured) -->
<record id="action_agenda_sync_now" model="ir.actions.server">
    <field name="name">Sync Agenda Now</field>
    <field name="model_id" ref="event.model_event_event"/>
    <field name="state">code</field>
    <field name="code">
        if env.company.ms_agenda_configured:
            model.sync_from_microsoft()
    </field>
</record>

<menuitem id="menu_agenda_sync_now" 
          name="Sync Now" 
          parent="menu_crearis_agenda" 
          action="action_agenda_sync_now"/>
```

---

## 8. Dependencies

### 8.1 Module Dependencies

```python
'depends': [
    'crearis',      # Base crearis module (must load first)
    'event',        # Odoo event management
],
```

### 8.2 Python Dependencies

```python
# requirements.txt additions
requests>=2.28.0
msal>=1.20.0  # Microsoft Authentication Library (optional, for advanced auth)
```

---

## 9. Security

### 9.1 Access Groups

- **Crearis User**: Can view sync status, trigger manual sync
- **Crearis Manager**: Can configure MS settings, view all sync logs

### 9.2 ir.model.access.csv

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_event_event_agenda_user,event.event.agenda.user,event.model_event_event,crearis.group_crearis_user,1,0,0,0
access_event_type_agenda_user,event.type.agenda.user,event.model_event_type,crearis.group_crearis_user,1,0,0,0
access_event_event_agenda_manager,event.event.agenda.manager,event.model_event_event,crearis.group_crearis_manager,1,1,1,1
access_event_type_agenda_manager,event.type.agenda.manager,event.model_event_type,crearis.group_crearis_manager,1,1,1,1
```

---

## 10. Implementation Phases

### Phase 1: Foundation
- [ ] Create module scaffold (`__manifest__.py`, `__init__.py`)
- [ ] Add res.company config fields
- [ ] Add company form view extension
- [ ] Adapt MS Graph client service from ms_taxonomy_sync

### Phase 2: Event Types Sync + Company Filtering
- [ ] Extend event.type with ms_* fields
- [ ] **Add `company_id` field to event.type**
- [ ] Implement one-way sync: SharePoint → Odoo
- [ ] Implement write-back of oevent_type_id
- [ ] **Update event.type form view with company_id**

### Phase 3: Events Sync + Filtered Event Type Selection
- [ ] Extend event.event with ms_* fields
- [ ] **Update event.event form to filter event_type_id by company**
- [ ] Implement sync from SharePoint (filtered by status)
- [ ] Implement sync to SharePoint (Odoo changes - Odoo wins)
- [ ] Handle oevent_id write-back
- [ ] **Implement archive logic for out-of-range events**

### Phase 4: Lookup Pre-Sync
- [ ] Pre-sync plan_referenten for user_id mapping
- [ ] Implement schedule logic (Seminarplan_Memo when Seminarplan=1)

### Phase 5: Menu & UI
- [ ] Add menu items to crearis menu
- [ ] Add manual sync button (conditional on config)
- [ ] Add sync status indicator

### Phase 6: Auto-sync (Optional)
- [ ] Implement cron job for auto-sync
- [ ] Add enable/disable toggle
- [ ] Add sync logging

---

## 10. API Endpoints Reference

### SharePoint Lists

| List | URL | GUID |
|------|-----|------|
| plan_veranstaltungen | `https://dasei.sharepoint.com/sites/api1/_layouts/15/listedit.aspx?List={BA5CFB7C-CFE7-4EFD-BA0A-65F9019D5A53}` | BA5CFB7C-CFE7-4EFD-BA0A-65F9019D5A53 |
| plan_veranstaltungscodes | `https://dasei.sharepoint.com/sites/api1/_layouts/15/ListEdit.aspx?List={E4B1128D-2709-480D-82D0-77F42605FD1A}` | E4B1128D-2709-480D-82D0-77F42605FD1A |
| plan_planungsstatus | `https://dasei.sharepoint.com/sites/api1/_layouts/15/ListEdit.aspx?List={6ADC07D7-8208-4370-AFBF-67B223F2C996}` | 6ADC07D7-8208-4370-AFBF-67B223F2C996 |
| plan_referenten | `https://dasei.sharepoint.com/sites/api1/_layouts/15/ListEdit.aspx?List={4BFD63EA-425C-4164-9550-2A193F7F98C9}` | 4BFD63EA-425C-4164-9550-2A193F7F98C9 |
| plan_seminarzeiten | `https://dasei.sharepoint.com/sites/api1/_layouts/15/ListEdit.aspx?List={6BBE92C5-82C5-40E7-8C5F-D6CB3018EC23}` | 6BBE92C5-82C5-40E7-8C5F-D6CB3018EC23 |

### Microsoft Graph API Calls

```bash
# Get list items with expanded fields
GET /sites/{site-id}/lists/{list-id}/items?$expand=fields&$top=200

# Get single item
GET /sites/{site-id}/lists/{list-id}/items/{item-id}?$expand=fields

# Update item (write-back)
PATCH /sites/{site-id}/lists/{list-id}/items/{item-id}/fields
Content-Type: application/json
{
  "oevent_id": 123,
  "oevent_type_id": 456
}

# Filter by status (OData)
GET /sites/{site-id}/lists/{list-id}/items?$expand=fields&$filter=fields/StatusLookupId in (3,10,14,15,16,17,18,19,25,33)
```

---

## 11. Design Decisions (Confirmed)

1. **Token Storage**: Store API credentials per-company in res.company
   - ✅ **Decision**: Per-company in res.company for multi-tenant support

2. **Conflict Resolution**: If both SharePoint and Odoo have changes, which wins?
   - ✅ **Decision**: **Odoo always wins** - Odoo is the master for edits within the active status range

3. **Soft Delete Handling**: When event status changes to outside sync-range in SharePoint, should Odoo record be archived?
   - ✅ **Decision**: Yes, archive in Odoo (set `active=False`), preserve data

4. **Lookup Resolution**: How to resolve lookups (Hauptreferent → user_id)?
   - ✅ **Decision**: Pre-sync `plan_referenten`, maintain `ouser_id` mapping

5. **Schedule Field**: When `Seminarplan` = 1, use `Seminarplan_Memo`. Otherwise lookup plan_seminarzeiten?
   - ✅ **Decision**: Confirmed - use `Seminarplan_Memo` content when `Seminarplan = 1`

---

## 12. Testing Plan

### 12.1 Unit Tests
- [ ] Test field mappings
- [ ] Test API client authentication
- [ ] Test sync logic (create/update/delete)
- [ ] **Test company_id filtering on event_type_id**
- [ ] **Test archive behavior for out-of-range events**

### 12.2 Integration Tests
- [ ] Test full sync cycle
- [ ] Test write-back functionality
- [ ] **Test Odoo-wins conflict resolution**
- [ ] **Test pre-sync of plan_referenten**

### 12.3 Manual Testing
- [ ] Configure company settings
- [ ] Trigger manual sync
- [ ] Verify data in both systems
- [ ] **Verify event_type filtering in event form by company**

---

## 13. Next Steps

1. **Review this plan** - confirm requirements and field mappings
2. **API Testing** - Test MS Graph API connection with provided credentials
3. **Implement Phase 1** - Module scaffold and company configuration
4. **Iterate** - Implement remaining phases with testing

---

*Document created: 2025-12-20*
*Last updated: 2025-12-20*
*Module: crearis_agenda*
*Depends on: crearis*

---

## Changelog

### 2025-12-20 - Initial Plan + Updates
- Created initial implementation plan
- **Confirmed design decisions**:
  - Odoo always wins in conflict resolution
  - Pre-sync plan_referenten for user_id mapping
  - Archive out-of-range events in Odoo (active=False)
  - Use Seminarplan_Memo when Seminarplan=1
- **Added new requirement**: `company_id` field on `event.type`
  - null/empty = available for all companies
  - set = only for specific company
  - Updated event.event form to filter event_type_id by company
