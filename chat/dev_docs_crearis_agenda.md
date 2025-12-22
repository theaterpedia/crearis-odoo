# crearis_agenda - Developer Documentation

*Module Version: 16.0.1.0.0*
*Created: 2025-12-22*

---

## Overview

`crearis_agenda` provides bidirectional synchronization between Odoo and Microsoft SharePoint for event management. It syncs event types and events using the Microsoft Graph API with version-controlled conflict resolution.

## Dependencies

```python
'depends': ['crearis', 'event']
```

## Architecture

```
crearis_agenda/
├── models/
│   ├── res_company.py      # Configuration fields + JSONB accessors
│   └── sync_engine.py      # AbstractModel for sync logic
├── views/
│   ├── res_company_views.xml   # MS Agenda tab in company form
│   └── sync_menu_views.xml     # Sync Now menu action
├── data/
│   └── cron_data.xml       # Hourly sync cron job
└── security/
    └── ir.model.access.csv
```

---

## Configuration (res.company)

### Credential Fields

| Field | Type | Purpose |
|-------|------|---------|
| `ms_agenda_tenant_id` | Char | Azure AD Tenant ID |
| `ms_agenda_client_id` | Char | App Registration Client ID |
| `ms_agenda_client_secret` | Char | App Registration Secret (password field) |
| `ms_agenda_site_id` | Char | SharePoint Site ID |

### JSONB Configuration

The `ms_agenda_api` JSON field stores SharePoint list GUIDs with computed accessors:

```python
ms_agenda_api = {
    'list_veranstaltungen': 'BA5CFB7C-CFE7-4EFD-BA0A-65F9019D5A53',
    'list_veranstaltungscodes': 'E4B1128D-2709-480D-82D0-77F42605FD1A',
    'list_referenten': '4BFD63EA-425C-4164-9550-2A193F7F98C9',
    'list_planungsstatus': '6ADC07D7-8208-4370-AFBF-67B223F2C996',
    'list_contacts': '7a77d6af-3a91-4109-8f56-9dbac73d2fa4',
    'list_kursteilnehmer': '2bf5f8e7-ebca-4a8b-b11e-feaee6a30287',
    'list_veranstaltungsteilnehmer': 'C9E05737-4C47-4E0F-A6B6-C6D6F3FBE88D',
    'list_seminarzeiten': '6BBE92C5-82C5-40E7-8C5F-D6CB3018EC23',
}
```

Each list GUID has a computed accessor field (e.g., `ms_list_veranstaltungen`) with inverse method for easy editing in the UI.

### Sync Level

```python
ms_agenda_sync_level = fields.Selection([
    ('init', 'Init - Full import from SharePoint'),
    ('slave', 'Slave - SharePoint drives updates'),
    ('master', 'Master - Odoo drives updates'),
])
```

| Level | SP→Odoo | Odoo→SP | Conflict Winner |
|-------|---------|---------|-----------------|
| init | ✅ Full import | ❌ Write-back IDs only | SharePoint |
| slave | ✅ Updates | ❌ Write-back IDs only | SharePoint |
| master | ✅ Updates | ✅ Full push | Odoo |

---

## Sync Engine (crearis.agenda.sync)

### AbstractModel Design

The sync engine is an `AbstractModel` (no database table) that provides sync methods:

```python
class AgendaSyncEngine(models.AbstractModel):
    _name = 'crearis.agenda.sync'
```

### Key Methods

| Method | Purpose |
|--------|---------|
| `_get_access_token(company)` | Get/refresh OAuth2 token (cached in memory) |
| `_graph_request(company, method, endpoint, json_data)` | Make Graph API request |
| `_get_list_items(company, list_guid, filter_query, top)` | Fetch list items with pagination |
| `_patch_list_item(company, list_guid, item_id, fields_data)` | Update list item |
| `sync_event_types(company)` | Sync plan_veranstaltungscodes → event.type |
| `sync_events(company)` | Sync plan_veranstaltungen → event.event |
| `sync_all(company)` | Run full sync cycle |
| `cron_sync_all_companies()` | Cron entry point |

---

## Version-Controlled Sync (oversion Pattern)

### The Problem

Bidirectional sync can cause infinite loops:
1. Odoo changes → push to SP
2. SP webhook/poll sees change → pull to Odoo
3. Odoo sees "new" data → push to SP
4. ...forever

### The Solution: oversion Echo Marker

| Location | Field | Purpose |
|----------|-------|---------|
| Odoo `event.event` | `version` | Auto-increments on every write |
| Odoo `event.event` | `ms_version` | Last seen SharePoint etag |
| Odoo `event.event` | `ms_pushed_version` | Odoo version at last push |
| SharePoint | `oversion` | Written by Odoo on push |

### Sync Algorithm

```python
def _sync_event(self, company, sp_item):
    sp_oversion = sp_item['fields'].get('oversion', 0)
    
    # ECHO DETECTION
    if sp_oversion == odoo_record.version:
        # This is our own push echoed back - skip!
        return 'skipped'
    
    # CHANGE DETECTION
    sp_changed = (odoo_record.ms_version != sp_etag)
    odoo_changed = (odoo_record.version > odoo_record.ms_pushed_version)
    
    # CONFLICT RESOLUTION
    if sp_changed and odoo_changed:
        if sync_level == 'master':
            return self._push_to_sp(odoo_record)  # Odoo wins
        else:
            return self._import_from_sp(sp_item)  # SP wins
```

### Visual Flow

```
SCENARIO: Odoo user edits
─────────────────────────
1. User edits in Odoo          → version: 5
2. Sync pushes to SP           → SP.oversion = 5
3. Next sync sees SP           → oversion(5) == version(5) → SKIP ✅

SCENARIO: SharePoint user edits  
───────────────────────────────
1. User edits in SP            → etag changes, oversion still = 4
2. Sync detects change         → etag differs, oversion(4) != version(5)
3. Import to Odoo              → version: 6
4. Push oversion back          → SP.oversion = 6
5. Next sync                   → oversion(6) == version(6) → SKIP ✅
```

### skip_version_increment Context

To update sync metadata without triggering version increment:

```python
odoo_record.with_context(skip_version_increment=True).write({
    'ms_version': new_etag,
    'ms_pushed_version': odoo_record.version,
})
```

This is implemented in `crearis/models/event.py`:

```python
def write(self, vals):
    if not self.env.context.get('skip_version_increment'):
        for rec in self:
            vals['version'] = rec.version + 1
    return super().write(vals)
```

---

## Field Mappings

### Event Types (plan_veranstaltungscodes → event.type)

| SharePoint Field | Odoo Field | Notes |
|------------------|------------|-------|
| `id` | `ms_id` | SharePoint item ID |
| `@odata.etag` | `ms_version` | Version tracking |
| `Title` | `name` | Event type code (e.g., "ME", "MB") |
| `Kurzbeschreibung` + `Veranstaltungstitel` | `template_heading` | Synthesized: "overline **headline**" |
| `TeaserText` | `template_teasertext` | Template content |
| `cimg` / `CloudinaryCode` | `template_cimg` | Hero image reference |
| `UE` | `template_units` | Teaching units |
| - | `is_template_code` | Set to `True` |
| - | `company_id` | Set to syncing company |
| `oevent_type_id` | - | Write-back: Odoo ID |
| `oversion` | - | Write-back: Echo marker |
| `oheading` | - | Write-back: from template_heading |

### template_heading Synthesis

On init sync, `template_heading` is built from SharePoint fields:

```python
# Format: "Kurzbeschreibung **Veranstaltungstitel**"
if kurzbeschreibung and veranstaltungstitel:
    template_heading = f"{kurzbeschreibung} **{veranstaltungstitel}**"
elif veranstaltungstitel:
    template_heading = f"**{veranstaltungstitel}**"
```

### Events (plan_veranstaltungen → event.event)

| SharePoint Field | Odoo Field | Notes |
|------------------|------------|-------|
| `id` | `ms_id` | SharePoint item ID |
| `@odata.etag` | `ms_version` | Version tracking |
| `Title` | `name` | Event title |
| `Start` | `date_begin` | Start date/time |
| `Ende` | `date_end` | End date/time |
| `cimg` | `cimg` | Hero image (direct) |
| `domain_code` | `domain_code` | Domain assignment (direct) |
| `UE` | `units` | Teaching units override |
| `SeminarplanLookupId` | - | Link to plan_seminarzeiten |
| `Seminarplan_Memo` | `schedule` | Custom schedule (if SeminarplanLookupId=1) |
| `VeranstaltungsCodeLookupId` | `event_type_id` | Via ms_id lookup |
| `StatusLookupId` | - | Filter only (SYNC_STATUS_IDS) |
| **Write-back fields:** | | |
| `oheading` | `name` | Event name in "overline **headline**" format |
| `oteasertext` | `teasertext` | Teaser text |
| `omd` | `md` | Markdown content |
| `oschedule` | `schedule` | Schedule text |
| `oversion` | `version` | Echo marker |
| `oevent_id` | `id` | Odoo event ID |

### name Field Format

The `name` field on `event.event` uses the overline-headline format:

```
"Kurzbeschreibung **Veranstaltungstitel**"
```

On init sync, `name` is synthesized:
1. If `oheading` exists on SharePoint → use it (previously synced)
2. Else build from `event_type.template_heading` (overline) + `Title` (headline):
   ```python
   overline = template_heading.split('**')[0].strip()
   name = f'{overline} **{Title}**'
   ```

The `rectitle` field remains unchanged - it shows shortcode + name for list display.

### Schedule Resolution Logic

The `schedule` field is resolved in this priority order:

1. If `oschedule` exists on SharePoint → use it (write-back from Odoo)
2. Else if `SeminarplanLookupId = 1` → use `Seminarplan_Memo` 
3. Else if `SeminarplanLookupId` set → fetch from `plan_seminarzeiten`
4. Else → empty

### Status Filter

Only events with these `StatusLookupId` values are synced:

```python
SYNC_STATUS_IDS = [3, 10, 14, 15, 16, 17, 18, 19, 25, 33]
```

---

## Template Application

When a new event is created from SharePoint, template defaults are applied ONE TIME:

```python
def _apply_event_template(self, event):
    if not event.event_type_id.template_parent_id:
        return
    
    template = event.event_type_id
    if template.template_teasertext and not event.teasertext:
        event.teasertext = template.template_teasertext
    if template.template_cimg and not event.cimg:
        event.cimg = template.template_cimg
    if template.template_units and not event.units:
        event.units = template.template_units
    # Note: heading comes via rectitle computed from template_heading
```

This uses `skip_version_increment=True` to avoid triggering unnecessary sync cycles.

---

## API Reference

### Microsoft Graph Endpoints Used

```bash
# Get access token
POST https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token

# Get list items
GET /sites/{site-id}/lists/{list-guid}/items?$expand=fields&$top=200

# Update list item
PATCH /sites/{site-id}/lists/{list-guid}/items/{item-id}/fields
```

### Token Caching

Tokens are cached in memory per company with automatic refresh:

```python
_token_cache = {
    company_id: {
        'token': 'eyJ...',
        'expires_at': datetime(...)
    }
}
```

---

## Extending the Sync Engine

The `agenda_dasei` module demonstrates how to extend:

```python
class AgendaSyncPartner(models.AbstractModel):
    _inherit = 'crearis.agenda.sync'
    
    def sync_all(self, company):
        result = super().sync_all(company)
        # Add custom sync logic
        result['contacts'] = self.sync_contacts(company)
        return result
```

---

## Cron Configuration

Runs every hour for companies with:
- `ms_agenda_configured = True`
- `ms_agenda_sync_enabled = True`

```xml
<record id="cron_sync_agenda" model="ir.cron">
    <field name="interval_number">1</field>
    <field name="interval_type">hours</field>
</record>
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Token error | Check tenant_id, client_id, client_secret |
| 403 Forbidden | App needs Sites.ReadWrite.All permission |
| Empty sync | Check status filter (SYNC_STATUS_IDS) |
| Infinite loop | Verify oversion field exists in SharePoint lists |

### Debug Logging

```python
import logging
_logger = logging.getLogger(__name__)

# In sync methods:
_logger.info(f"Event types: {type_stats}")
_logger.info(f"Events: {event_stats}")
```

---

## Security

### Required Graph API Permissions

- `Sites.ReadWrite.All` (Application permission)

### Odoo Groups

- `crearis.group_crearis_user` - Can view sync status
- `crearis.group_crearis_manager` - Can configure and trigger sync

---

*Last updated: 2025-12-22*
