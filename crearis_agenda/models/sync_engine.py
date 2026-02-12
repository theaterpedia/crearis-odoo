# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
import requests
from datetime import datetime, timedelta

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Status IDs that should be synced from SharePoint
# From plan_planungsstatus:
# 3=[angekündigt #ORGA#], 10=[angekündigt mit Vorbehalt], 14=[angekündigt], 15=AKTUELL mit Vorbehalt
# 16=AKTUELL #ORGA#, 17=[angekündigt #TEAM#], 18=AKTUELL #TEAM#], 19=AKTUELL, 25=[angekündigt #USER#]
# 33=AKTUELL #USER#
SYNC_STATUS_IDS = [3, 10, 14, 15, 16, 17, 18, 19, 25, 33]

# S7.2: StatusLookupId → stage sysreg mapping
# Maps SharePoint plan_planungsstatus IDs to Odoo event stage sequences (sysreg values)
# Stage sequences (sysreg): 1=new, 8=planned, 64=booked, 512=announced, 4096=current, 8192=completed, 12288=cancelled
STATUS_TO_STAGE_SYSREG = {
    # angekündigt variants → announced (512)
    3: 512,    # [angekündigt #ORGA#]
    10: 512,   # [angekündigt mit Vorbehalt]
    14: 512,   # [angekündigt]
    17: 512,   # [angekündigt #TEAM#]
    25: 512,   # [angekündigt #USER#]
    # AKTUELL variants → current (4096)
    15: 4096,  # AKTUELL mit Vorbehalt
    16: 4096,  # AKTUELL #ORGA#
    18: 4096,  # AKTUELL #TEAM#
    19: 4096,  # AKTUELL
    33: 4096,  # AKTUELL #USER#
}

# S7.2 Reverse: stage sysreg → StatusLookupId (for push to SP)
# Maps Odoo stage sequences to primary SharePoint plan_planungsstatus IDs
STAGE_SYSREG_TO_STATUS = {
    1: 4,       # new → ID 4
    8: 9,       # planned → ID 9
    64: 13,     # booked → ID 13
    512: 14,    # announced → ID 14 [angekündigt]
    4096: 19,   # current → ID 19 AKTUELL
    8192: 30,   # completed → ID 30
    12288: 7,   # cancelled → ID 7
}

# L4: Location sync constants
# Physical venues → sync to res.partner with address data
VENUE_IDS = {1, 3, 4, 6, 7, 8, 13, 16, 17, 18, 19, 20}

# Abstract locations → set event tag, no partner sync
# Maps raum_id → tag xmlid in agenda_dasei module
ABSTRACT_TO_TAG = {
    2: 'event_tag_tbd',              # Leer
    5: 'event_tag_online',           # Web: Standard
    9: 'event_tag_on_request_nbg',   # Nbg: Sonstige
    10: 'event_tag_on_request_deu',  # DEU: Nachfrage
    11: 'event_tag_on_request_bay',  # BAY: Nachfrage
    12: 'event_tag_on_request_czb',  # CZB: Nachfrage
    14: 'event_tag_tbd',             # -
    15: 'event_tag_on_request_eu',   # EU
}


class AgendaSyncEngine(models.AbstractModel):
    _name = 'crearis.agenda.sync'
    _description = 'SharePoint Agenda Sync Engine'

    """
    Sync Levels:
    - init:   SP → Odoo import. Write-back o* fields ONLY if empty on SP (non-destructive).
    - slave:  SP drives updates. Conflicts: SP wins.
    - master: Odoo drives updates. Conflicts: Odoo wins. Write-back overwrites SP o* fields.
    
    Write-back fields (o* = Odoo-owned on SharePoint):
    - oheading:    event.name (format: "overline **headline**")
    - oteasertext: event.teasertext
    - omd:         event.md (markdown content)
    - oschedule:   event.schedule
    - oversion:    event.version (for echo detection)
    - oevent_id:   event.id (Odoo record ID)
    
    To force re-init: clear o* fields on SharePoint manually, then run sync.
    """

    # Token cache (in-memory, per-company)
    _token_cache = {}

    def _get_access_token(self, company):
        """Get or refresh Microsoft Graph API access token"""
        cache_key = company.id
        cached = self._token_cache.get(cache_key)
        
        if cached and cached['expires_at'] > datetime.now():
            return cached['token']

        if not company.ms_agenda_tenant_id or not company.ms_agenda_client_id:
            raise UserError("Microsoft API credentials not configured")

        url = f"https://login.microsoftonline.com/{company.ms_agenda_tenant_id}/oauth2/v2.0/token"
        data = {
            'client_id': company.ms_agenda_client_id,
            'client_secret': company.ms_agenda_client_secret,
            'scope': 'https://graph.microsoft.com/.default',
            'grant_type': 'client_credentials',
        }

        response = requests.post(url, data=data)
        if response.status_code != 200:
            raise UserError(f"Failed to get access token: {response.text}")

        token_data = response.json()
        self._token_cache[cache_key] = {
            'token': token_data['access_token'],
            'expires_at': datetime.now() + timedelta(seconds=token_data['expires_in'] - 60)
        }

        return token_data['access_token']

    def _parse_sp_datetime(self, sp_datetime):
        """Convert SharePoint ISO 8601 datetime to Odoo format
        
        SharePoint: 2019-09-13T07:00:00Z
        Odoo: 2019-09-13 07:00:00
        """
        if not sp_datetime:
            return None
        # Remove timezone suffix and replace T with space
        return sp_datetime.replace('T', ' ').replace('Z', '')

    def _get_whitelist_entry(self, company, event_id):
        """Check if event is in push whitelist and return its entry.
        
        Returns:
            - None if whitelist mode disabled or event not in whitelist
            - dict with {'id': event_id, 'reg_ids': [...] or None} if whitelisted
        
        Whitelist format examples:
            [1234, {"id": 1235, "reg_ids": [100, 101]}, {"id": 1236}]
            
        - Integer: Event ID (syncs event + all registrations)
        - Object with id only: Same as integer
        - Object with reg_ids: Syncs event + only specified registration IDs
        """
        if not company.ms_agenda_whitelist_push:
            return None
        
        whitelist = company.ms_agenda_push_whitelist or []
        
        for entry in whitelist:
            if isinstance(entry, int):
                if entry == event_id:
                    return {'id': event_id, 'reg_ids': None}
            elif isinstance(entry, dict):
                entry_id = entry.get('id')
                if entry_id == event_id:
                    return {
                        'id': event_id,
                        'reg_ids': entry.get('reg_ids')  # None means all regs
                    }
        
        return None

    def _is_push_allowed(self, company, event_id):
        """Check if push is allowed for this event.
        
        - If whitelist mode is OFF: push always allowed (normal master mode behavior)
        - If whitelist mode is ON: push only if event is in whitelist
        """
        if not company.ms_agenda_whitelist_push:
            return True  # Normal mode - no restriction
        
        entry = self._get_whitelist_entry(company, event_id)
        return entry is not None

    def _graph_request(self, company, method, endpoint, json_data=None):
        """Make a request to Microsoft Graph API"""
        token = self._get_access_token(company)
        base_url = f"https://graph.microsoft.com/v1.0/sites/{company.ms_agenda_site_id}"
        url = f"{base_url}{endpoint}"

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }

        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'PATCH':
            response = requests.patch(url, headers=headers, json=json_data)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=json_data)
        else:
            raise UserError(f"Unsupported HTTP method: {method}")

        if response.status_code not in (200, 201, 204):
            _logger.error(f"Graph API error: {response.status_code} - {response.text}")
            raise UserError(f"Graph API error: {response.text}")

        if response.status_code == 204:
            return {}
        return response.json()

    def _get_list_items(self, company, list_guid, filter_query=None, top=200):
        """Fetch items from a SharePoint list"""
        endpoint = f"/lists/{list_guid}/items?$expand=fields&$top={top}"
        if filter_query:
            endpoint += f"&$filter={filter_query}"

        all_items = []
        while endpoint:
            result = self._graph_request(company, 'GET', endpoint)
            all_items.extend(result.get('value', []))
            
            # Handle pagination
            next_link = result.get('@odata.nextLink')
            if next_link:
                # Extract the endpoint part after the site URL
                endpoint = next_link.split(company.ms_agenda_site_id)[1]
            else:
                endpoint = None

        return all_items

    def _patch_list_item(self, company, list_guid, item_id, fields_data):
        """Update a SharePoint list item"""
        endpoint = f"/lists/{list_guid}/items/{item_id}/fields"
        return self._graph_request(company, 'PATCH', endpoint, fields_data)

    def _get_item_etag(self, company, list_guid, item_id):
        """Fetch the current @odata.etag for a single list item.

        Used after a PATCH write-back to capture the new etag so the next
        sync cycle won't see a false-positive 'sp_changed'.  Returns None
        on any error (caller should handle gracefully).
        """
        try:
            endpoint = f"/lists/{list_guid}/items/{item_id}?$select=id"
            result = self._graph_request(company, 'GET', endpoint)
            return result.get('@odata.etag')
        except Exception:
            _logger.debug("Could not fetch etag for item %s", item_id, exc_info=True)
            return None

    # =========================================================================
    # RESET WRITEBACK FIELDS
    # =========================================================================

    def reset_writeback_fields(self, company, dry_run=True):
        """Clear writeback fields in SharePoint to allow fresh sync from new Odoo database.
        
        This clears:
        - plan_veranstaltungscodes: oevent_type_id, oversion
        - plan_veranstaltungen: oevent_id, oversion  
        - plan_raeume: opartner_id
        
        Usage from shell:
            company = env['res.company'].browse(2)  # DASEi company ID
            # Dry run first (shows what would be cleared):
            env['crearis.agenda.sync'].reset_writeback_fields(company, dry_run=True)
            # Actually clear:
            env['crearis.agenda.sync'].reset_writeback_fields(company, dry_run=False)
        
        Args:
            company: res.company record with MS Graph config
            dry_run: If True, only count items without clearing (default: True)
        
        Returns:
            dict with counts per list
        """
        results = {}
        
        # 1. plan_veranstaltungscodes (event.type)
        if company.ms_list_veranstaltungscodes:
            count = self._reset_list_writeback(
                company, 
                company.ms_list_veranstaltungscodes,
                ['oevent_type_id', 'oversion'],
                'plan_veranstaltungscodes',
                dry_run
            )
            results['event_types'] = count
        
        # 2. plan_veranstaltungen (event.event)
        if company.ms_list_veranstaltungen:
            count = self._reset_list_writeback(
                company,
                company.ms_list_veranstaltungen,
                ['oevent_id', 'oversion'],
                'plan_veranstaltungen',
                dry_run
            )
            results['events'] = count
        
        # 3. plan_raeume (res.partner locations)
        if company.ms_list_raeume:
            count = self._reset_list_writeback(
                company,
                company.ms_list_raeume,
                ['oaddress_id'],
                'plan_raeume',
                dry_run
            )
            results['locations'] = count
        
        action = "Would clear" if dry_run else "Cleared"
        _logger.info(
            "%s writeback fields: %d event types, %d events, %d locations",
            action,
            results.get('event_types', 0),
            results.get('events', 0),
            results.get('locations', 0)
        )
        
        return results

    def _reset_list_writeback(self, company, list_guid, fields, list_name, dry_run):
        """Clear writeback fields for all items in a SharePoint list.
        
        Args:
            fields: List of field names to set to null
            dry_run: If True, only count without patching
        
        Returns:
            Number of items processed
        """
        # Get all items with any of the writeback fields set
        # For SharePoint list items, filter uses fields/fieldName syntax
        filter_parts = [f"fields/{f} ne null" for f in fields]
        filter_query = " or ".join(filter_parts)
        
        sp_items = self._get_list_items(company, list_guid, filter_query=filter_query)
        
        if dry_run:
            _logger.info(
                "[DRY RUN] %s: %d items have writeback fields (%s)",
                list_name, len(sp_items), ', '.join(fields)
            )
            return len(sp_items)
        
        # Clear the fields
        clear_data = {f: None for f in fields}
        cleared = 0
        
        for sp_item in sp_items:
            sp_id = sp_item['id']
            try:
                self._patch_list_item(company, list_guid, sp_id, clear_data)
                cleared += 1
            except Exception as e:
                _logger.warning("Failed to clear item %s in %s: %s", sp_id, list_name, e)
        
        _logger.info("%s: Cleared %d/%d items", list_name, cleared, len(sp_items))
        return cleared

    def cleanup_duplicate_locations(self, company, dry_run=True):
        """Remove duplicate location partners created by sync bug.
        
        For each sp_raum_id with multiple partners, keeps the oldest (lowest ID)
        and deletes/archives the rest. Updates event.event.address_id references.
        
        Usage:
            company = env['res.company'].browse(11)
            engine = env['crearis.agenda.sync']
            engine.cleanup_duplicate_locations(company, dry_run=True)  # Preview
            engine.cleanup_duplicate_locations(company, dry_run=False)  # Execute
        """
        Partner = self.env['res.partner'].sudo()
        Event = self.env['event.event'].sudo()
        
        # Find all location partners with sp_raum_id
        locations = Partner.search([
            ('is_event_location', '=', True),
            ('sp_raum_id', '!=', False),
            ('company_id', '=', company.id),
        ])
        
        # Group by sp_raum_id
        from collections import defaultdict
        by_raum = defaultdict(list)
        for loc in locations:
            by_raum[loc.sp_raum_id].append(loc)
        
        # Find duplicates
        stats = {'duplicated_raums': 0, 'to_delete': 0, 'events_updated': 0}
        to_delete = Partner.browse()
        event_remap = {}
        
        for raum_id, partners in by_raum.items():
            if len(partners) <= 1:
                continue
            
            stats['duplicated_raums'] += 1
            
            # Sort by ID (oldest first) - keep the first one
            partners.sort(key=lambda p: p.id)
            keep = partners[0]
            duplicates = partners[1:]
            
            _logger.info(
                "raum_id=%s: Keep %s (id=%d), delete %d duplicates",
                raum_id, keep.name, keep.id, len(duplicates)
            )
            
            for dup in duplicates:
                stats['to_delete'] += 1
                to_delete |= dup
                event_remap[dup.id] = keep.id
        
        # Find events referencing duplicates
        if event_remap:
            events_to_fix = Event.search([
                ('address_id', 'in', list(event_remap.keys())),
            ])
            stats['events_updated'] = len(events_to_fix)
        
        _logger.info(
            "Cleanup summary: %d raum_ids have duplicates, %d partners to delete, %d events to update",
            stats['duplicated_raums'], stats['to_delete'], stats['events_updated']
        )
        
        if dry_run:
            _logger.info("[DRY RUN] Would delete: %s", to_delete.mapped('name'))
            return stats
        
        # Update events first
        for old_id, new_id in event_remap.items():
            Event.search([('address_id', '=', old_id)]).write({'address_id': new_id})
        
        # Delete duplicates (or archive if delete fails)
        for partner in to_delete:
            try:
                partner.unlink()
            except Exception as e:
                _logger.warning("Cannot delete %s, archiving: %s", partner.name, e)
                partner.active = False
        
        return stats

    # =========================================================================
    # DIAGNOSTIC TOOLS
    # =========================================================================

    def diagnose_event_fields(self, company, limit=3):
        """Dump raw SharePoint fields for a few events to discover field structure.
        
        Usage from shell:
            company = env['res.company'].browse(1)
            env['crearis.agenda.sync'].diagnose_event_fields(company)
        """
        list_guid = company.ms_list_veranstaltungen
        if not list_guid:
            _logger.warning("No plan_veranstaltungen list configured")
            return []
        
        sp_items = self._get_list_items(company, list_guid, top=limit)
        
        results = []
        for sp_item in sp_items:
            sp_id = sp_item['id']
            sp_fields = sp_item.get('fields', {})
            
            # Look for raum-related fields
            raum_fields = {k: v for k, v in sp_fields.items() 
                          if 'raum' in k.lower() or 'room' in k.lower() or 'location' in k.lower()}
            
            # Also grab title for context
            result = {
                'id': sp_id,
                'Title': sp_fields.get('Title', ''),
                'raum_fields': raum_fields,
                'all_field_keys': sorted(sp_fields.keys()),
            }
            results.append(result)
            
            _logger.info(f"Event {sp_id} '{sp_fields.get('Title', '')}':")
            _logger.info(f"  Raum-related fields: {raum_fields}")
            _logger.info(f"  All fields: {sorted(sp_fields.keys())}")
        
        return results

    def export_seminarzeiten_full(self, company):
        """Export ALL plan_seminarzeiten items for documentation.
        
        Fields exported:
        - id: SharePoint list item ID
        - Title: Schedule template name
        - Feld1: Short schedule description
        - Feld12: Detailed schedule text (multiline)
        
        Usage from shell:
            company = env['res.company'].browse(11)
            data = env['crearis.agenda.sync'].export_seminarzeiten_full(company)
            for r in data: print(f"{r['id']:>3} | {r['Title']}")
        """
        list_guid = company.ms_list_seminarzeiten
        if not list_guid:
            _logger.warning("ms_list_seminarzeiten not configured for company %s", company.name)
            return []
        
        sp_items = self._get_list_items(company, list_guid, top=200)
        
        results = []
        for sp_item in sp_items:
            sp_id = sp_item['id']
            f = sp_item.get('fields', {})
            
            result = {
                'id': int(sp_id),
                'Title': f.get('Title', ''),
                'Feld1': f.get('Feld1', ''),  # Short description
                'Feld12': f.get('Feld12', ''),  # Detailed schedule
                'all_fields': list(f.keys()),
            }
            results.append(result)
            
            # Preview first 100 chars of detailed schedule
            preview = (result['Feld12'] or '').replace('\n', ' | ')[:100]
            _logger.info(
                f"Seminarzeit {sp_id:>3}: {result['Title']:<30} | "
                f"Feld1: {(result['Feld1'] or '')[:30]} | "
                f"Feld12: {preview}..."
            )
        
        results.sort(key=lambda x: x['id'])
        _logger.info(f"Exported {len(results)} schedule templates from plan_seminarzeiten")
        return results

    def diagnose_hybrid_events(self, company, limit=50):
        """Diagnose hybrid events (online + in-presence) to understand schedule patterns.
        
        Looks for events with:
        - Seminarplan_Memo containing 'online' or 'Teams' 
        - Multiple location types implied
        
        Usage from shell:
            company = env['res.company'].browse(11)
            data = env['crearis.agenda.sync'].diagnose_hybrid_events(company, limit=100)
        """
        list_guid = company.ms_list_veranstaltungen
        sp_items = self._get_list_items(company, list_guid, top=limit)
        
        hybrid_events = []
        for sp_item in sp_items:
            sp_id = sp_item['id']
            f = sp_item.get('fields', {})
            
            title = f.get('Title', '')
            seminarplan_memo = f.get('Feld11', '') or ''  # Custom schedule text
            seminarplan_id = f.get('SeminarplanLookupId')
            raum_id = f.get('raum1LookupId')
            date_begin = f.get('Feld17', '')
            date_end = f.get('Feld18', '')
            
            # Check if schedule mentions online/Teams
            memo_lower = seminarplan_memo.lower()
            is_hybrid = any(kw in memo_lower for kw in ['online', 'teams', 'zoom', 'web', 'digital'])
            
            # Also check if raum_id = 5 (Web: Standard) but memo has in-presence hints
            has_presence = any(kw in memo_lower for kw in ['vor ort', 'präsenz', 'tanzerei', 'khg', 'kineo'])
            
            if is_hybrid or (raum_id == 5 and has_presence) or (raum_id != 5 and 'online' in memo_lower):
                result = {
                    'id': int(sp_id),
                    'Title': title,
                    'SeminarplanLookupId': seminarplan_id,
                    'raum1LookupId': raum_id,
                    'date_begin': date_begin,
                    'date_end': date_end,
                    'Seminarplan_Memo': seminarplan_memo,
                    'is_hybrid': is_hybrid,
                    'has_presence': has_presence,
                }
                hybrid_events.append(result)
                
                _logger.info(
                    f"HYBRID Event {sp_id}: {title[:40]} | "
                    f"Raum: {raum_id} | SeminarplanId: {seminarplan_id} | "
                    f"Dates: {date_begin[:10] if date_begin else 'N/A'} - {date_end[:10] if date_end else 'N/A'}"
                )
                _logger.info(f"  Memo: {seminarplan_memo[:150]}...")
        
        _logger.info(f"Found {len(hybrid_events)} potential hybrid events out of {len(sp_items)} scanned")
        return hybrid_events

    def diagnose_raeume_list(self, company, limit=10):
        """Dump raw SharePoint fields from plan_raeume to discover field structure.
        
        Usage from shell:
            company = env['res.company'].browse(1)
            env['crearis.agenda.sync'].diagnose_raeume_list(company)
        """
        list_guid = '705952ee-bc5e-476f-88ea-31d21d5d3f7d'  # plan_raeume
        
        sp_items = self._get_list_items(company, list_guid, top=limit)
        
        results = []
        for sp_item in sp_items:
            sp_id = sp_item['id']
            sp_fields = sp_item.get('fields', {})
            
            result = {
                'id': sp_id,
                'fields': sp_fields,
            }
            results.append(result)
            
            _logger.info(f"Raum {sp_id}: {sp_fields}")
        
        return results

    def export_raeume_full(self, company):
        """Export ALL plan_raeume items with relevant fields for documentation.
        
        Fields exported:
        - id: SharePoint list item ID (used as LookupId)
        - Title: Location short name (required)
        - Feld1: Beschreibung (description)
        - Feld10: Ort (city)
        - Feld11: Adresse (address, multiline)
        - PLZ: Postal code
        - Anfahrt: Directions (richtext)
        - CloudinaryCode: Image reference
        - Koordination: Lookup to contacts list
        - oaddress_id: Odoo res.partner ID (for sync)
        
        Usage from shell:
            company = env['res.company'].browse(11)
            data = env['crearis.agenda.sync'].export_raeume_full(company)
            for r in data: print(f"{r['id']:>3} | {r['Title']:<25} | {r['Ort']:<15} | {r['PLZ']}")
        """
        list_guid = '705952ee-bc5e-476f-88ea-31d21d5d3f7d'  # plan_raeume
        
        # Fetch all items (no top limit)
        sp_items = self._get_list_items(company, list_guid, top=500)
        
        results = []
        for sp_item in sp_items:
            sp_id = sp_item['id']
            f = sp_item.get('fields', {})
            
            result = {
                'id': int(sp_id),
                'Title': f.get('Title', ''),
                'Beschreibung': f.get('Feld1', ''),
                'Ort': f.get('Feld10', ''),
                'Adresse': f.get('Feld11', ''),
                'PLZ': f.get('PLZ', ''),
                'Anfahrt': f.get('Anfahrt', ''),
                'CloudinaryCode': f.get('CloudinaryCode', ''),
                'Koordination': f.get('KoordinationLookupId'),
                'oaddress_id': f.get('oaddress_id'),
            }
            results.append(result)
            
            _logger.info(
                f"Raum {sp_id:>3}: {result['Title']:<25} | "
                f"Ort: {result['Ort']:<15} | PLZ: {result['PLZ']} | "
                f"Koordination: {result['Koordination']} | "
                f"Beschreibung: {(result['Beschreibung'] or '')[:30]} | "
                f"Adresse: {(result['Adresse'] or '').replace(chr(10), ' ')[:40]} | "
                f"Anfahrt: {'Yes' if result['Anfahrt'] else 'No'} | "
                f"oaddress_id: {result['oaddress_id']}"
            )
        
        # Sort by ID for consistent output
        results.sort(key=lambda x: x['id'])
        
        _logger.info(f"Exported {len(results)} locations from plan_raeume")
        return results

    def diagnose_update_raum(self, company, event_sp_id, raum_lookup_id):
        """Test updating Raum field on an event.
        
        Usage from shell:
            company = env['res.company'].browse(11)
            env['crearis.agenda.sync'].diagnose_update_raum(company, '1616', 1)
        """
        list_guid = company.ms_list_veranstaltungen
        
        # Try different formats - SharePoint lookup fields can be picky
        formats_to_try = [
            # Format 1: Array of {id: value} objects (from MS docs)
            ('Raum with id', {'Raum': [{'id': raum_lookup_id}]}),
            # Format 2: RaumLookupId with array of IDs
            ('RaumLookupId array', {'RaumLookupId': [raum_lookup_id]}),
            # Format 3: RaumLookupId as single value (for single-select mode)
            ('RaumLookupId single', {'RaumLookupId': raum_lookup_id}),
            # Format 4: Array of {LookupId: value}
            ('Raum with LookupId', {'Raum': [{'LookupId': raum_lookup_id}]}),
        ]
        
        for fmt_name, fields_data in formats_to_try:
            try:
                _logger.info(f"Trying format '{fmt_name}': {fields_data}")
                result = self._patch_list_item(company, list_guid, event_sp_id, fields_data)
                _logger.info(f"SUCCESS with '{fmt_name}'! Result: {result}")
                return {'success': True, 'format': fmt_name, 'result': result}
            except Exception as e:
                _logger.warning(f"Format '{fmt_name}' failed: {e}")
                continue
        
        return {'success': False, 'message': 'All formats failed'}

    def migrate_raum_to_raum1(self, company, dry_run=True):
        """Migrate Raum[0] multivalue to raum1 single-value lookup.
        
        Usage from shell:
            company = env['res.company'].browse(11)
            # Dry run first:
            env['crearis.agenda.sync'].migrate_raum_to_raum1(company, dry_run=True)
            # Then execute:
            env['crearis.agenda.sync'].migrate_raum_to_raum1(company, dry_run=False)
        """
        list_guid = company.ms_list_veranstaltungen
        if not list_guid:
            return {'error': 'No plan_veranstaltungen list configured'}
        
        _logger.info(f"Starting Raum → raum1 migration (dry_run={dry_run})")
        
        # Fetch all events
        sp_items = self._get_list_items(company, list_guid)
        _logger.info(f"Fetched {len(sp_items)} events")
        
        stats = {'total': 0, 'migrated': 0, 'skipped_empty': 0, 'skipped_already': 0, 'errors': 0}
        errors = []
        
        for sp_item in sp_items:
            stats['total'] += 1
            sp_id = sp_item['id']
            sp_fields = sp_item.get('fields', {})
            
            # Get Raum multivalue field
            raum_list = sp_fields.get('Raum', [])
            
            # Skip if no Raum value
            if not raum_list or len(raum_list) == 0:
                stats['skipped_empty'] += 1
                continue
            
            # Extract first LookupId
            raum_id = raum_list[0].get('LookupId')
            if not raum_id:
                stats['skipped_empty'] += 1
                continue
            
            # Check if raum1 already set
            existing_raum1 = sp_fields.get('raum1LookupId')
            if existing_raum1:
                stats['skipped_already'] += 1
                continue
            
            # Update raum1LookupId
            if dry_run:
                _logger.info(f"[DRY RUN] Would update event {sp_id}: raum1LookupId = {raum_id}")
                stats['migrated'] += 1
            else:
                try:
                    self._patch_list_item(company, list_guid, sp_id, {'raum1LookupId': raum_id})
                    _logger.info(f"Updated event {sp_id}: raum1LookupId = {raum_id}")
                    stats['migrated'] += 1
                except Exception as e:
                    _logger.error(f"Failed to update event {sp_id}: {e}")
                    stats['errors'] += 1
                    errors.append({'id': sp_id, 'error': str(e)})
            
            # Progress logging
            if stats['total'] % 50 == 0:
                _logger.info(f"Progress: {stats['total']} processed, {stats['migrated']} migrated")
        
        _logger.info(f"Migration complete: {stats}")
        return {'stats': stats, 'errors': errors[:10] if errors else []}

    # =========================================================================
    # EVENT TYPE SYNC
    # =========================================================================

    def sync_event_types(self, company):
        """Sync event types from SharePoint plan_veranstaltungscodes"""
        list_guid = company.ms_list_veranstaltungscodes
        if not list_guid:
            return {'synced': 0, 'created': 0, 'updated': 0, 'skipped': 0}

        sp_items = self._get_list_items(company, list_guid)
        
        stats = {'synced': 0, 'created': 0, 'updated': 0, 'skipped': 0}

        for sp_item in sp_items:
            result = self._sync_event_type(company, sp_item)
            stats['synced'] += 1
            stats[result] += 1

        return stats

    def _sync_event_type(self, company, sp_item):
        """Sync a single event type with version control"""
        EventType = self.env['event.type'].sudo()
        
        sp_id = sp_item['id']
        sp_etag = sp_item.get('@odata.etag', '')
        sp_fields = sp_item.get('fields', {})
        sp_oversion = sp_fields.get('oversion', 0) or 0

        # Find existing Odoo record
        odoo_record = EventType.search([('ms_id', '=', sp_id)], limit=1)

        if not odoo_record:
            # New record - create in Odoo
            vals = self._map_event_type_from_sp(company, sp_fields)
            vals['ms_id'] = sp_id
            vals['ms_version'] = sp_etag
            vals['ms_synced'] = True
            odoo_record = EventType.create(vals)
            
            # Write back oevent_type_id
            self._patch_list_item(company, company.ms_list_veranstaltungscodes, sp_id, {
                'oevent_type_id': odoo_record.id,
                'oversion': 1,
            })
            return 'created'

        # Echo detection - if oversion matches our record, skip
        # But if ms_version is NULL, we want to force re-import
        if sp_oversion and sp_oversion == odoo_record.id and odoo_record.ms_version:
            if odoo_record.ms_version != sp_etag:
                odoo_record.write({'ms_version': sp_etag})
            return 'skipped'

        # Check if SP changed
        sp_changed = (odoo_record.ms_version != sp_etag)

        if not sp_changed:
            return 'skipped'

        # SP changed - import updates
        vals = self._map_event_type_from_sp(company, sp_fields)
        vals['ms_version'] = sp_etag
        odoo_record.write(vals)

        # Update oversion to prevent re-import
        self._patch_list_item(company, company.ms_list_veranstaltungscodes, sp_id, {
            'oversion': odoo_record.id,
        })

        return 'updated'

    def _map_event_type_from_sp(self, company, sp_fields):
        """Map SharePoint fields to event.type fields
        
        SharePoint plan_veranstaltungscodes fields:
        - Title: Event type code (e.g., 'ME', 'MB')
        - Feld1: Kurzbeschreibung (full descriptive title)
        - Feld10: Veranstaltungstitel (short catchy title)
        - TeaserText: Short description
        - CloudinaryCode / cimg: Hero image reference
        - UE: Teaching units
        - domain_code: Domain assignment
        """
        # Find template parent by sequence
        template_parent = None
        sequence = sp_fields.get('Sequence', 0) or 0
        if sequence:
            template_parent = self.env['event.type'].sudo().search([
                ('is_template_code', '=', False),
                ('sequence', '=', sequence),
                ('company_id', '=', False),
            ], limit=1)

        # Synthesize template_heading: "Kurzbeschreibung **Veranstaltungstitel**"
        # SharePoint internal names: Feld1=Kurzbeschreibung, Feld10=Veranstaltungstitel
        kurzbeschreibung = sp_fields.get('Feld1', '') or ''
        veranstaltungstitel = sp_fields.get('Feld10', '') or ''
        template_heading = ''
        if kurzbeschreibung and veranstaltungstitel:
            template_heading = '{} **{}**'.format(kurzbeschreibung.strip(), veranstaltungstitel.strip())
        elif veranstaltungstitel:
            template_heading = '**{}**'.format(veranstaltungstitel.strip())
        elif kurzbeschreibung:
            template_heading = kurzbeschreibung.strip()

        return {
            'name': sp_fields.get('Title', ''),
            'sequence': sequence,
            'is_template_code': True,
            'template_parent_id': template_parent.id if template_parent else False,
            'template_teasertext': sp_fields.get('TeaserText', ''),
            'template_cimg': sp_fields.get('cimg') or sp_fields.get('CloudinaryCode', ''),
            'template_heading': template_heading,
            'template_units': sp_fields.get('UE', 0) or 0,
            'company_id': company.id,
        }

    # =========================================================================
    # EVENT SYNC
    # =========================================================================

    def sync_events(self, company):
        """Sync events from SharePoint plan_veranstaltungen"""
        list_guid = company.ms_list_veranstaltungen
        if not list_guid:
            return {'synced': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'pushed': 0}

        # Build filter for active statuses
        status_filter = ','.join(str(s) for s in SYNC_STATUS_IDS)
        filter_query = f"fields/StatusLookupId in ({status_filter})"

        _logger.info("Fetching events from SharePoint...")
        sp_items = self._get_list_items(company, list_guid)  # TODO: add filter when SP supports it
        _logger.info(f"Fetched {len(sp_items)} events from SharePoint, processing...")

        stats = {'synced': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'pushed': 0}

        for sp_item in sp_items:
            # Manual status filter (Graph API filter on lookup fields can be tricky)
            status_id = sp_item.get('fields', {}).get('StatusLookupId')
            if status_id and int(status_id) not in SYNC_STATUS_IDS:
                continue

            result = self._sync_event(company, sp_item)
            stats['synced'] += 1
            stats[result] += 1
            
            # Progress logging every 100 events
            if stats['synced'] % 100 == 0:
                _logger.info(f"Events progress: {stats['synced']} synced, {stats['updated']} updated, {stats['created']} created")

        return stats

    def _sync_event(self, company, sp_item):
        """Sync a single event with version control"""
        Event = self.env['event.event'].sudo()
        EventType = self.env['event.type'].sudo()

        sp_id = sp_item['id']
        sp_etag = sp_item.get('@odata.etag', '')
        sp_fields = sp_item.get('fields', {})
        sp_oversion = sp_fields.get('oversion', 0) or 0

        # Skip events without required date fields
        # SharePoint uses Feld17 (Start) and Feld18 (Ende) as internal names
        if not sp_fields.get('Feld17'):
            _logger.debug("Skipping event %s - no Start date (Feld17)", sp_id)
            return 'skipped'

        # Skip "heading" events - these are report section headers, not real events
        # Rule: event_type.name matching pattern *_ (letter + underscore) are headings
        # e.g., d_ = heading, d1 = real event
        type_code = sp_fields.get('VeranstaltungsCodeLookupId')
        if type_code:
            event_type = EventType.search([
                ('ms_id', '=', str(type_code)),
                ('company_id', '=', company.id),
            ], limit=1)
            if event_type and event_type.name and len(event_type.name) >= 2:
                # Check if name matches heading pattern: letter + underscore (e.g., d_, m_)
                if event_type.name[1:2] == '_':
                    _logger.debug("Skipping heading event %s - event_type '%s' is a report header", sp_id, event_type.name)
                    return 'skipped'

        # Find existing Odoo record
        odoo_record = Event.search([('ms_id', '=', sp_id)], limit=1)
        sync_level = company.ms_agenda_sync_level

        if not odoo_record:
            # New record - create in Odoo with de_DE language context
            # Suppress mail.thread tracking — sync imports must never generate
            # user-facing notifications ("Sie wurden … zugewiesen").
            vals = self._map_event_from_sp(company, sp_fields)
            vals['ms_id'] = sp_id
            vals['ms_version'] = sp_etag
            vals['ms_synced'] = True
            vals['ms_pushed_version'] = 0
            odoo_record = Event.with_context(
                lang='de_DE',
                mail_notrack=True,
                tracking_disable=True,
                mail_create_nolog=True,
            ).create(vals)

            # Apply template defaults if event type has template parent
            self._apply_event_template(odoo_record)
            
            # Parse schedule into schedule_data
            self._parse_event_schedule(company, odoo_record)

            # Write back oevent_id + content fields (if empty on SP)
            # Init mode: only populate empty o* fields, never overwrite existing
            writeback_data = {
                'oevent_id': odoo_record.id,
                'oversion': odoo_record.version,
            }
            # Add content fields only if SP field is empty
            # DISABLED: SP fields broken - waiting for MS Support
            # if not sp_fields.get('oheading'):
            #     writeback_data['oheading'] = odoo_record.name or ''
            
            self._patch_list_item(company, company.ms_list_veranstaltungen, sp_id, writeback_data)
            return 'created'

        # === ECHO DETECTION ===
        # oversion matching our record version indicates our previous push
        # BUT: if etag changed, SP was edited AFTER our push → not an echo
        if sp_oversion and sp_oversion == odoo_record.version:
            if odoo_record.ms_version == sp_etag:
                # etag unchanged - this is truly our echo, skip
                return 'skipped'
            # etag changed - SP was edited after our push, continue to change detection
            _logger.info(f"Event {odoo_record.id} (ms_id={sp_id}): oversion matches but etag changed, processing SP edit")

        # === CHANGE DETECTION ===
        sp_changed = (odoo_record.ms_version != sp_etag)
        odoo_changed = (odoo_record.version > (odoo_record.ms_pushed_version or 0))

        # Dev mode: always force update for testing
        if company.ms_dev_mode and sync_level == 'init':
            return self._import_event_from_sp(company, sp_item, odoo_record)

        if not sp_changed and not odoo_changed:
            return 'skipped'

        # === WHITELIST PUSH MODE ===
        # When enabled, whitelisted events can be pushed even in slave mode
        whitelist_allows_push = (
            company.ms_agenda_whitelist_push and 
            self._is_push_allowed(company, odoo_record.id)
        )

        # === CONFLICT RESOLUTION ===
        if sp_changed and odoo_changed:
            if sync_level == 'master' or whitelist_allows_push:
                # Odoo wins - push our changes
                if self._is_push_allowed(company, odoo_record.id):
                    return self._push_event_to_sp(company, odoo_record)
                else:
                    return 'skipped'  # Whitelist mode but not in whitelist
            else:
                # Slave/init mode - SP wins
                return self._import_event_from_sp(company, sp_item, odoo_record)

        if sp_changed:
            return self._import_event_from_sp(company, sp_item, odoo_record)

        if odoo_changed:
            # Push if master mode OR whitelist allows
            if sync_level == 'master' or whitelist_allows_push:
                if self._is_push_allowed(company, odoo_record.id):
                    return self._push_event_to_sp(company, odoo_record)
            # Odoo changed but can't push - skip (will be overwritten on next SP change)

        return 'skipped'

    def _writeback_empty_ofields(self, company, sp_item, odoo_record, sp_fields):
        """Write back empty o* fields to SharePoint (init mode only)"""
        writeback_data = {}
        if not sp_fields.get('oheading'):
            writeback_data['oheading'] = odoo_record.name or ''
        if not sp_fields.get('otesasertext'):
            writeback_data['otesasertext'] = odoo_record.teasertext or ''  # SP field has typo
        if not sp_fields.get('omd'):
            writeback_data['omd'] = odoo_record.md or ''
        if not sp_fields.get('oschedule'):
            writeback_data['oschedule'] = odoo_record.schedule or ''
        
        if writeback_data:
            _logger.info(f"Init write-back for event {odoo_record.id}: {list(writeback_data.keys())}")
            self._patch_list_item(company, company.ms_list_veranstaltungen, sp_item['id'], writeback_data)

    def _import_event_from_sp(self, company, sp_item, odoo_record):
        """Import SharePoint changes to Odoo event.

        Three defences against the notification-flood loop:
        1. Diff-based write — only write fields whose values actually changed,
           so mail.thread tracking never fires for unchanged Many2one fields.
        2. mail_notrack / tracking_disable context — belt-and-suspenders
           suppression of all tracking notifications during sync.
        3. skip_version_increment — incoming sync must not bump the Odoo
           version counter (that's reserved for user edits / Odoo→SP push).
        4. oversion write-back only when content actually changed, and
           ms_version updated to the post-writeback etag to break the
           etag → false-positive loop.
        """
        sp_fields = sp_item.get('fields', {})
        sp_etag = sp_item.get('@odata.etag', '')

        vals = self._map_event_from_sp(company, sp_fields)

        # --- Fix 1: diff-based write — filter out unchanged values ----------
        filtered_vals = {}
        for key, new_val in vals.items():
            old_val = odoo_record[key]
            # Many2one → compare IDs
            if hasattr(old_val, 'id'):
                old_cmp = old_val.id or False
            # x2many (tag_ids) → keep as-is (command tuples can't be diffed)
            elif hasattr(old_val, 'ids'):
                filtered_vals[key] = new_val
                continue
            else:
                old_cmp = old_val
            if old_cmp != new_val:
                filtered_vals[key] = new_val

        # Always update the etag bookmark
        filtered_vals['ms_version'] = sp_etag

        has_real_changes = any(k != 'ms_version' for k in filtered_vals)

        if has_real_changes:
            _logger.info(
                "Importing SP changes for event %s (ms_id=%s): %s",
                odoo_record.id, sp_item['id'],
                [k for k in filtered_vals if k != 'ms_version'],
            )

        # --- Fix 2 + Fix 4: suppress tracking, don't bump version ----------
        odoo_record.with_context(
            lang='de_DE',
            skip_version_increment=True,
            mail_notrack=True,
            tracking_disable=True,
            mail_create_nolog=True,
        ).write(filtered_vals)

        # Parse schedule into schedule_data if we have schedule text
        self._parse_event_schedule(company, odoo_record)

        # --- Fix 3: only write back oversion when content changed ----------
        if has_real_changes:
            writeback_data = {
                'oversion': odoo_record.version,
            }
            self._patch_list_item(
                company, company.ms_list_veranstaltungen,
                sp_item['id'], writeback_data,
            )
            # The PATCH changes SP's etag.  Re-fetch it so the next sync
            # cycle won't see a false-positive "sp_changed".
            new_etag = self._get_item_etag(
                company, company.ms_list_veranstaltungen, sp_item['id'],
            )
            update_vals = {'ms_pushed_version': odoo_record.version}
            if new_etag:
                update_vals['ms_version'] = new_etag
            odoo_record.with_context(skip_version_increment=True).write(update_vals)
        else:
            # No real changes — just update etag bookmark, no SP write-back
            odoo_record.with_context(skip_version_increment=True).write({
                'ms_pushed_version': odoo_record.version,
            })

        return 'updated'
    
    def _parse_event_schedule(self, company, event):
        """Parse schedule text into schedule_data JSONB.
        
        Uses ScheduleParser from crearis module with company-configured shortcodes.
        """
        if not event.schedule:
            return
        
        try:
            from odoo.addons.crearis.models.schedule_mixin import ScheduleParser
            
            # Get company shortcodes config
            shortcodes = company.schedule_shortcodes or {'_online_': {'type': 'online', 'name': 'Online'}}
            # Handle both 'de' and 'de_DE' formats; default to 'de' if unset
            locale = company.schedule_locale or 'de'
            
            parser = ScheduleParser(locale=locale, shortcodes=shortcodes)
            
            # Parse with event dates for weekday resolution
            schedule_data = parser.parse(
                event.schedule,
                date_begin=event.date_begin,
                date_end=event.date_end
            )
            
            if schedule_data:
                event.with_context(skip_version_increment=True).write({
                    'schedule_data': schedule_data,
                    'schedule_raw': event.schedule,
                })
                _logger.debug("Parsed schedule for event %s: %d sessions", 
                             event.id, schedule_data.get('summary', {}).get('session_count', 0))
                # Sync agenda_line_ids from schedule_data sessions
                if hasattr(event, '_sync_agenda_lines'):
                    event._sync_agenda_lines()
        except Exception as e:
            _logger.warning("Failed to parse schedule for event %s: %s", event.id, e)

    def _push_event_to_sp(self, company, odoo_record):
        """Push Odoo event changes to SharePoint"""
        # Log whitelist push mode
        if company.ms_agenda_whitelist_push:
            entry = self._get_whitelist_entry(company, odoo_record.id)
            _logger.info("Whitelist push: event %s (ms_id=%s), reg_ids=%s", 
                        odoo_record.id, odoo_record.ms_id, 
                        entry.get('reg_ids') if entry else 'N/A')
        
        sp_data = self._map_event_to_sp(odoo_record)
        sp_data['oversion'] = odoo_record.version

        response = self._patch_list_item(
            company,
            company.ms_list_veranstaltungen,
            odoo_record.ms_id,
            sp_data
        )

        # Update tracking without incrementing version
        new_etag = response.get('@odata.etag', odoo_record.ms_version)
        odoo_record.with_context(skip_version_increment=True).write({
            'ms_version': new_etag,
            'ms_pushed_version': odoo_record.version,
        })

        return 'pushed'

    def _map_event_from_sp(self, company, sp_fields):
        """Map SharePoint fields to event.event fields
        
        SharePoint plan_veranstaltungen fields:
        - Title: Event name
        - Start, Ende: Date/time range
        - VeranstaltungsCodeLookupId: Link to event type
        - Seminarplan/SeminarplanLookupId: Link to plan_seminarzeiten (schedule template)
        - Seminarplan_Memo: Custom schedule text (used when Seminarplan = 1 or override)
        - cimg: Hero image (direct mapping)
        - domain_code: Domain assignment (direct mapping)
        - oheading, oteasertext, omd, oschedule: Write-back fields from Odoo
        - UE: Teaching units override
        """
        # Find event type by lookup ID
        event_type = None
        type_code = sp_fields.get('VeranstaltungsCodeLookupId')
        if type_code:
            event_type = self.env['event.type'].sudo().search([
                ('ms_id', '=', str(type_code)),
                ('company_id', '=', company.id),
            ], limit=1)

        # Parse dates (SharePoint internal names: Feld17=Start, Feld18=Ende)
        # SharePoint returns ISO 8601 format: 2019-09-13T07:00:00Z
        # Odoo expects: %Y-%m-%d %H:%M:%S
        date_begin = self._parse_sp_datetime(sp_fields.get('Feld17'))
        date_end = self._parse_sp_datetime(sp_fields.get('Feld18')) or date_begin

        # Find website for domain_code
        website = None
        domain_code_value = sp_fields.get('domain_code')
        if domain_code_value:
            website = self.env['website'].search([
                ('domain_code', '=', domain_code_value),
            ], limit=1)
        if not website:
            website = self.env['website'].search([
                ('company_id', '=', company.id)
            ], limit=1)

        # Resolve schedule text:
        # 1. If SP has oschedule (written back from Odoo), use it
        # 2. Else use Feld11 (custom schedule memo on the event)
        # 3. Else if SeminarplanLookupId > 1, fetch from plan_seminarzeiten template
        schedule_text = sp_fields.get('oschedule') or ''
        if not schedule_text:
            schedule_text = sp_fields.get('Feld11') or ''
        if not schedule_text:
            seminarplan_id = sp_fields.get('SeminarplanLookupId')
            if seminarplan_id and str(seminarplan_id) != '1':
                # Fetch from plan_seminarzeiten template
                schedule_text = self._fetch_seminarplan_text(company, seminarplan_id)
        
        _logger.debug("Schedule for %s: oschedule=%s, Feld11=%s, SeminarplanLookupId=%s, result=%s",
                     sp_fields.get('Title'), sp_fields.get('oschedule'), sp_fields.get('Feld11'),
                     sp_fields.get('SeminarplanLookupId'), schedule_text)

        # Resolve name (heading):
        # 1. If SP has oheading (written back from Odoo), use it
        # 2. Else use template_heading from event_type directly
        # 3. Fallback to SP Title
        name = sp_fields.get('oheading', '') or ''
        if not name and event_type and event_type.template_heading:
            name = event_type.template_heading
        if not name:
            name = sp_fields.get('Title', '')

        # Resolve teasertext:
        # 1. If SP has otesasertext (written back from Odoo), use it - note SP field has typo
        # 2. Else use template_teasertext from event_type
        teasertext = sp_fields.get('otesasertext', '') or ''
        if not teasertext and event_type and event_type.template_teasertext:
            # template_teasertext might be JSONB dict, extract de_DE or string value
            tt = event_type.template_teasertext
            if isinstance(tt, dict):
                teasertext = tt.get('de_DE') or tt.get('en_US') or ''
            else:
                teasertext = tt or ''

        # S7.2: Resolve stage from StatusLookupId
        # Maps SP planning status → Odoo event stage by sysreg sequence
        stage_id = False
        status_id = sp_fields.get('StatusLookupId')
        if status_id:
            stage_sysreg = STATUS_TO_STAGE_SYSREG.get(int(status_id))
            if stage_sysreg:
                stage = self.env['event.stage'].search([
                    ('sequence', '=', stage_sysreg)
                ], limit=1)
                if stage:
                    stage_id = stage.id
                else:
                    _logger.warning("No stage found with sequence %s for StatusLookupId %s", stage_sysreg, status_id)
            else:
                _logger.debug("No sysreg mapping for StatusLookupId %s", status_id)

        # Resolve user_id from Hauptreferent (if dasei.referent.sync is available)
        # SharePoint internal name: HauptreferentLookupId
        user_id = False
        hauptreferent_id = sp_fields.get('HauptreferentLookupId')
        if hauptreferent_id:
            try:
                referent_sync = self.env['dasei.referent.sync']
                user_id = referent_sync.get_referent_user_id(company, hauptreferent_id)
            except KeyError:
                # dasei.referent.sync not installed (agenda_dasei not loaded)
                pass

        # L6: Resolve location from raum1LookupId
        raum_id = sp_fields.get('raum1LookupId')
        location_vals = self._sync_event_location(company, raum_id)

        # Return plain strings - caller uses with_context(lang='de_DE')
        return {
            'name': name,
            'event_type_id': event_type.id if event_type else False,
            'stage_id': stage_id,
            'user_id': user_id,
            'organizer_id': company.partner_id.id,  # Set organizer to company partner
            'date_begin': date_begin,
            'date_end': date_end,
            'teasertext': teasertext,
            'md': sp_fields.get('omd', '') or '',
            'schedule': schedule_text,
            'cimg': sp_fields.get('cimg', ''),
            'units': sp_fields.get('UE', 0) or 0,
            'domain_code': website.id if website else False,
            'company_id': company.id,
            **location_vals,  # sp_raum_id, address_id, tag_ids
        }

    def _sync_event_location(self, company, raum_id):
        """L6-L7: Sync location from SharePoint raum1LookupId
        
        Type A (VENUE_IDS): Find/create res.partner with address data
        Type B (ABSTRACT_TO_TAG): Set event tag, no partner
        
        Returns dict with:
        - sp_raum_id: Always set if raum_id provided
        - address_id: Partner ID for venues, False for abstract
        - tag_ids: [(4, tag_id)] for abstract locations
        """
        if not raum_id:
            return {'sp_raum_id': False}
        
        raum_id = int(raum_id)
        vals = {'sp_raum_id': raum_id}
        
        if raum_id in VENUE_IDS:
            # Type A: Physical venue → find/create partner
            partner = self.env['res.partner'].search([
                ('sp_raum_id', '=', raum_id),
                ('is_event_location', '=', True),
                ('company_id', '=', company.id),
            ], limit=1)
            
            if not partner:
                # Lazy create: fetch from SP and create partner
                partner = self._create_location_partner(company, raum_id)
            
            if partner:
                vals['address_id'] = partner.id
                # Remove any abstract location tags
                vals['tag_ids'] = self._get_remove_abstract_tags_commands()
            else:
                _logger.warning("Could not find/create partner for venue raum_id=%s", raum_id)
                
        elif raum_id in ABSTRACT_TO_TAG:
            # Type B: Abstract location → add tag, clear address
            tag_xmlid = ABSTRACT_TO_TAG[raum_id]
            try:
                tag = self.env.ref(f'agenda_dasei.{tag_xmlid}')
                vals['address_id'] = False
                vals['tag_ids'] = [(4, tag.id)]
            except ValueError:
                _logger.warning("Tag %s not found for raum_id=%s", tag_xmlid, raum_id)
        else:
            # Unknown raum_id - log warning
            _logger.debug("Unknown raum_id=%s, not in VENUE_IDS or ABSTRACT_TO_TAG", raum_id)
        
        return vals

    def _get_remove_abstract_tags_commands(self):
        """Get ORM commands to remove all abstract location tags"""
        commands = []
        for tag_xmlid in set(ABSTRACT_TO_TAG.values()):
            try:
                tag = self.env.ref(f'agenda_dasei.{tag_xmlid}')
                commands.append((3, tag.id))  # Remove tag
            except ValueError:
                pass
        return commands

    def _create_location_partner(self, company, raum_id):
        """L8: Create res.partner from SharePoint plan_raeume
        
        SP fields → Odoo:
        - Title → name
        - Feld1 (Beschreibung) → comment  
        - Feld10 (Ort) → city
        - Feld11 (Adresse) → street
        - PLZ → zip
        """
        if not company.ms_list_raeume:
            _logger.warning("Company %s missing ms_list_raeume, cannot sync locations", company.name)
            return False
        
        try:
            result = self._graph_request(
                company, 'GET',
                f"/lists/{company.ms_list_raeume}/items/{raum_id}?$expand=fields"
            )
            fields = result.get('fields', {})
            
            partner_vals = {
                'name': fields.get('Title') or f'Location {raum_id}',
                'is_event_location': True,
                'sp_raum_id': raum_id,
                'comment': fields.get('Feld1') or '',
                'city': fields.get('Feld10') or '',
                'street': fields.get('Feld11') or '',
                'zip': fields.get('PLZ') or '',
                'company_id': company.id,
            }
            
            partner = self.env['res.partner'].create(partner_vals)
            # Flush immediately so partner is visible if multiple events reference same location
            self.env['res.partner'].flush_model()
            _logger.info("Created location partner: %s (sp_raum_id=%s)", partner.name, raum_id)
            
            # L9: Write-back oaddress_id to SharePoint
            self._write_back_location(company, raum_id, partner.id)
            
            return partner
            
        except Exception as e:
            _logger.error("Failed to create location partner for raum_id=%s: %s", raum_id, e)
            return False

    def _write_back_location(self, company, raum_id, partner_id):
        """L9: Write-back Odoo partner ID to SharePoint plan_raeume"""
        if not company.ms_list_raeume:
            return
        
        try:
            self._patch_list_item(company, company.ms_list_raeume, raum_id, {
                'oaddress_id': partner_id,
            })
            _logger.debug("Wrote back oaddress_id=%s for raum_id=%s", partner_id, raum_id)
        except Exception as e:
            _logger.warning("Failed to write-back oaddress_id for raum_id=%s: %s", raum_id, e)

    def sync_locations(self, company, dry_run=False):
        """L8: Sync all venue locations from SharePoint plan_raeume
        
        Pre-syncs all VENUE_IDS to res.partner before event sync.
        Use this for eager sync instead of lazy create.
        """
        if not company.ms_list_raeume:
            _logger.warning("Company %s missing ms_list_raeume", company.name)
            return {'created': 0, 'updated': 0, 'skipped': 0}
        
        stats = {'created': 0, 'updated': 0, 'skipped': 0}
        
        for raum_id in VENUE_IDS:
            existing = self.env['res.partner'].search([
                ('sp_raum_id', '=', raum_id),
                ('is_event_location', '=', True),
            ], limit=1)
            
            if existing:
                stats['skipped'] += 1
                _logger.debug("Location partner already exists: %s (raum_id=%s)", existing.name, raum_id)
                continue
            
            if dry_run:
                _logger.info("[DRY RUN] Would create partner for raum_id=%s", raum_id)
                stats['created'] += 1
                continue
            
            partner = self._create_location_partner(company, raum_id)
            if partner:
                stats['created'] += 1
            else:
                _logger.warning("Failed to create partner for raum_id=%s", raum_id)
        
        _logger.info("sync_locations complete: created=%s, updated=%s, skipped=%s",
                    stats['created'], stats['updated'], stats['skipped'])
        return stats

    def _fetch_seminarplan_text(self, company, seminarplan_id):
        """Fetch schedule text from plan_seminarzeiten by ID
        
        SharePoint plan_seminarzeiten fields:
        - Feld12: Detailed schedule text (preferred)
        - Feld1: Short schedule description (fallback)
        """
        if not seminarplan_id or not company.ms_list_seminarzeiten:
            return ''
        
        try:
            result = self._graph_request(
                company, 'GET',
                f"/lists/{company.ms_list_seminarzeiten}/items/{seminarplan_id}?$expand=fields"
            )
            fields = result.get('fields', {})
            # Prefer Feld12 (detailed), fallback to Feld1 (short)
            return fields.get('Feld12') or fields.get('Feld1') or ''
        except Exception as e:
            _logger.warning(f"Failed to fetch seminarplan {seminarplan_id}: {e}")
            return ''

    def _map_event_to_sp(self, odoo_record):
        """Map Odoo event fields to SharePoint fields (write-back)
        
        Write-back fields to plan_veranstaltungen:
        - oheading: from heading (de)
        - oteasertext: from teasertext (de) - note: SharePoint has typo 'otesasertext'
        - omd: from md (de)
        - oschedule: from schedule_data JSONB (serialized as text)
        - oversion: from version
        - cimg: direct sync
        - domain_code: direct sync
        - oevent_id: Odoo event ID
        """
        import json
        
        # Serialize schedule_data to JSON for oschedule write-back
        oschedule = ''
        if odoo_record.schedule_data:
            try:
                oschedule = json.dumps(odoo_record.schedule_data, ensure_ascii=False, indent=2)
            except Exception:
                oschedule = odoo_record.schedule or ''
        else:
            oschedule = odoo_record.schedule or ''
        
        # Map stage to StatusLookupId for push
        status_lookup_id = None
        if odoo_record.stage_id:
            stage_sysreg = odoo_record.stage_id.sequence
            status_lookup_id = STAGE_SYSREG_TO_STATUS.get(stage_sysreg)
        
        result = {
            'oheading': odoo_record.name or '',  # name is in "overline **headline**" format
            'otesasertext': odoo_record.teasertext or '',  # SP field has typo
            'omd': odoo_record.md or '',
            'oschedule': oschedule,
            'cimg': odoo_record.cimg or '',
            'domain_code': odoo_record.domain_code.domain_code if odoo_record.domain_code else '',
            'oevent_id': odoo_record.id,
        }
        
        # Only include StatusLookupId if we have a valid mapping
        if status_lookup_id:
            result['StatusLookupId'] = status_lookup_id
        
        return result

    def _apply_event_template(self, event):
        """Apply template defaults from event type (one-time on create)
        
        From event.type template fields:
        - template_teasertext → teasertext (if not already set)
        - template_cimg → cimg (if not already set)
        - template_units → units (if not already set)
        
        Note: name/heading and teasertext are now applied in _map_event_from_sp
        This method handles any remaining template fields.
        """
        if not event.event_type_id:
            return

        template = event.event_type_id
        updates = {}

        # Only apply cimg and units here - teasertext and heading handled in mapping
        if template.template_cimg and not event.cimg:
            updates['cimg'] = template.template_cimg
        if template.template_units and not event.units:
            updates['units'] = template.template_units

        if updates:
            event.with_context(skip_version_increment=True).write(updates)

    # =========================================================================
    # MAIN SYNC ENTRY POINT
    # =========================================================================

    SYNC_LOCK_TIMEOUT = 1800  # 30 minutes

    def sync_all(self, company):
        """Run full sync for a company.
        
        Uses timestamp-based lock with auto-expiry to prevent:
        - Concurrent sync runs
        - Stuck locks from crashed transactions
        - Endless lock-renewal without actual sync work
        """
        # Check timestamp-based lock
        if company.ms_agenda_sync_started:
            elapsed = (fields.Datetime.now() - company.ms_agenda_sync_started).total_seconds()
            if elapsed < self.SYNC_LOCK_TIMEOUT:
                _logger.warning(
                    "Sync locked for %s (started %ds ago, expires in %ds)",
                    company.name, int(elapsed), int(self.SYNC_LOCK_TIMEOUT - elapsed)
                )
                return {
                    'skipped': True,
                    'reason': 'already_running',
                    'locked_since': str(company.ms_agenda_sync_started),
                }
            else:
                _logger.warning(
                    "Clearing stale sync lock for %s (started %ds ago, timeout=%ds)",
                    company.name, int(elapsed), self.SYNC_LOCK_TIMEOUT
                )

        # Set lock timestamp via ORM (no manual commit — Odoo manages transaction)
        company.sudo().write({'ms_agenda_sync_started': fields.Datetime.now()})

        _logger.info(f"Starting agenda sync for company {company.name}")

        results = {
            'event_types': 0,
            'locations': 0,
            'events': 0,
        }

        try:
            # Sync event types first
            type_stats = self.sync_event_types(company)
            results['event_types'] = type_stats.get('synced', 0)
            _logger.info(f"Event types: {type_stats}")

            # Pre-sync locations to avoid duplicates during event sync
            loc_stats = self.sync_locations(company)
            results['locations'] = loc_stats.get('created', 0) + loc_stats.get('skipped', 0)
            _logger.info(f"Locations: {loc_stats}")

            # Then sync events
            event_stats = self.sync_events(company)
            results['events'] = event_stats.get('synced', 0)
            _logger.info(f"Events: {event_stats}")

            # Update last sync timestamp
            company.write({'ms_agenda_last_sync': fields.Datetime.now()})

        except Exception as e:
            _logger.exception(f"Sync failed for company {company.name}")
            # Clear lock before raising — use SQL as fallback since ORM may fail
            try:
                self.env.cr.execute(
                    "UPDATE res_company SET ms_agenda_sync_started = NULL WHERE id = %s",
                    [company.id]
                )
            except Exception:
                _logger.warning("Could not clear sync lock for %s — will auto-expire after %ds",
                                company.name, self.SYNC_LOCK_TIMEOUT)
            raise UserError(f"Sync failed: {str(e)}")

        # Success path: clear lock via ORM
        company.sudo().write({'ms_agenda_sync_started': False})

        return results

    @api.model
    def cron_sync_all_companies(self):
        """Cron job to sync all configured companies"""
        # Search on stored fields that indicate configuration
        companies = self.env['res.company'].search([
            ('ms_agenda_tenant_id', '!=', False),
            ('ms_agenda_client_id', '!=', False),
            ('ms_agenda_site_id', '!=', False),
            ('ms_agenda_sync_enabled', '=', True),
        ])

        for company in companies:
            # Skip if sync is already running (check lock)
            if company.ms_agenda_sync_started:
                _logger.info(f"Skipping {company.name} - sync in progress or locked")
                continue
            try:
                self.sync_all(company)
            except Exception as e:
                _logger.exception(f"Cron sync failed for {company.name}: {e}")
