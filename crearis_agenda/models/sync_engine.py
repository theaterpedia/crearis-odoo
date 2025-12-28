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
# 16=AKTUELL #ORGA#, 17=[angekündigt #TEAM#], 18=AKTUELL #TEAM#, 19=AKTUELL, 25=[angekündigt #USER#]
# 33=AKTUELL #USER#
SYNC_STATUS_IDS = [3, 10, 14, 15, 16, 17, 18, 19, 25, 33]


class AgendaSyncEngine(models.AbstractModel):
    _name = 'crearis.agenda.sync'
    _description = 'SharePoint Agenda Sync Engine'

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
        EventType = self.env['event.type']
        
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
            template_parent = self.env['event.type'].search([
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

        sp_items = self._get_list_items(company, list_guid)  # TODO: add filter when SP supports it

        stats = {'synced': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'pushed': 0}

        for sp_item in sp_items:
            # Manual status filter (Graph API filter on lookup fields can be tricky)
            status_id = sp_item.get('fields', {}).get('StatusLookupId')
            if status_id and int(status_id) not in SYNC_STATUS_IDS:
                continue

            result = self._sync_event(company, sp_item)
            stats['synced'] += 1
            stats[result] += 1

        return stats

    def _sync_event(self, company, sp_item):
        """Sync a single event with version control"""
        Event = self.env['event.event']

        sp_id = sp_item['id']
        sp_etag = sp_item.get('@odata.etag', '')
        sp_fields = sp_item.get('fields', {})
        sp_oversion = sp_fields.get('oversion', 0) or 0

        # Skip events without required date fields
        # SharePoint uses Feld17 (Start) and Feld18 (Ende) as internal names
        if not sp_fields.get('Feld17'):
            _logger.debug("Skipping event %s - no Start date (Feld17)", sp_id)
            return 'skipped'

        # Find existing Odoo record
        odoo_record = Event.search([('ms_id', '=', sp_id)], limit=1)
        sync_level = company.ms_agenda_sync_level

        if not odoo_record:
            # New record - create in Odoo with de_DE language context
            vals = self._map_event_from_sp(company, sp_fields)
            vals['ms_id'] = sp_id
            vals['ms_version'] = sp_etag
            vals['ms_synced'] = True
            vals['ms_pushed_version'] = 0
            odoo_record = Event.with_context(lang='de_DE').create(vals)

            # Apply template defaults if event type has template parent
            self._apply_event_template(odoo_record)

            # Write back oevent_id
            self._patch_list_item(company, company.ms_list_veranstaltungen, sp_id, {
                'oevent_id': odoo_record.id,
                'oversion': odoo_record.version,
            })
            return 'created'

        # === ECHO DETECTION ===
        if sp_oversion and sp_oversion == odoo_record.version:
            # This is our own push echoed back - just update etag
            if odoo_record.ms_version != sp_etag:
                odoo_record.with_context(skip_version_increment=True).write({
                    'ms_version': sp_etag
                })
            return 'skipped'

        # === CHANGE DETECTION ===
        sp_changed = (odoo_record.ms_version != sp_etag)
        odoo_changed = (odoo_record.version > (odoo_record.ms_pushed_version or 0))

        if not sp_changed and not odoo_changed:
            return 'skipped'

        # === CONFLICT RESOLUTION ===
        if sp_changed and odoo_changed:
            if sync_level == 'master':
                # Odoo wins - push our changes
                return self._push_event_to_sp(company, odoo_record)
            else:
                # Slave/init mode - SP wins
                return self._import_event_from_sp(company, sp_item, odoo_record)

        if sp_changed:
            return self._import_event_from_sp(company, sp_item, odoo_record)

        if odoo_changed and sync_level == 'master':
            return self._push_event_to_sp(company, odoo_record)

        return 'skipped'

    def _import_event_from_sp(self, company, sp_item, odoo_record):
        """Import SharePoint changes to Odoo event"""
        sp_fields = sp_item.get('fields', {})
        sp_etag = sp_item.get('@odata.etag', '')

        vals = self._map_event_from_sp(company, sp_fields)
        vals['ms_version'] = sp_etag

        # Write with de_DE language context for translated fields
        odoo_record.with_context(lang='de_DE').write(vals)

        # Push oversion back to prevent re-import loop
        self._patch_list_item(company, company.ms_list_veranstaltungen, sp_item['id'], {
            'oversion': odoo_record.version,
        })

        # Update pushed version
        odoo_record.with_context(skip_version_increment=True).write({
            'ms_pushed_version': odoo_record.version,
        })

        return 'updated'

    def _push_event_to_sp(self, company, odoo_record):
        """Push Odoo event changes to SharePoint"""
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
            event_type = self.env['event.type'].search([
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
        # 1. If SP has oteasertext (written back from Odoo), use it
        # 2. Else use template_teasertext from event_type
        teasertext = sp_fields.get('oteasertext', '') or ''
        if not teasertext and event_type and event_type.template_teasertext:
            # template_teasertext might be JSONB dict, extract de_DE or string value
            tt = event_type.template_teasertext
            if isinstance(tt, dict):
                teasertext = tt.get('de_DE') or tt.get('en_US') or ''
            else:
                teasertext = tt or ''

        # Return plain strings - caller uses with_context(lang='de_DE')
        return {
            'name': name,
            'event_type_id': event_type.id if event_type else False,
            'date_begin': date_begin,
            'date_end': date_end,
            'teasertext': teasertext,
            'md': sp_fields.get('omd', '') or '',
            'schedule': schedule_text,
            'cimg': sp_fields.get('cimg', ''),
            'units': sp_fields.get('UE', 0) or 0,
            'domain_code': website.id if website else False,
            'company_id': company.id,
        }

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
        - oschedule: from schedule (de)
        - oversion: from version
        - cimg: direct sync
        - domain_code: direct sync
        - oevent_id: Odoo event ID
        """
        return {
            'oheading': odoo_record.name or '',  # name is in "overline **headline**" format
            'oteasertext': odoo_record.teasertext or '',
            'omd': odoo_record.md or '',
            'oschedule': odoo_record.schedule or '',
            'cimg': odoo_record.cimg or '',
            'domain_code': odoo_record.domain_code.domain_code if odoo_record.domain_code else '',
            'oevent_id': odoo_record.id,
        }

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

    def sync_all(self, company):
        """Run full sync for a company"""
        _logger.info(f"Starting agenda sync for company {company.name}")

        results = {
            'event_types': 0,
            'events': 0,
        }

        try:
            # Sync event types first
            type_stats = self.sync_event_types(company)
            results['event_types'] = type_stats.get('synced', 0)
            _logger.info(f"Event types: {type_stats}")

            # Then sync events
            event_stats = self.sync_events(company)
            results['events'] = event_stats.get('synced', 0)
            _logger.info(f"Events: {event_stats}")

            # Update last sync timestamp
            company.write({'ms_agenda_last_sync': fields.Datetime.now()})

        except Exception as e:
            _logger.exception(f"Sync failed for company {company.name}")
            raise UserError(f"Sync failed: {str(e)}")

        return results

    @api.model
    def cron_sync_all_companies(self):
        """Cron job to sync all configured companies"""
        companies = self.env['res.company'].search([
            ('ms_agenda_configured', '=', True),
            ('ms_agenda_sync_enabled', '=', True),
        ])

        for company in companies:
            try:
                self.sync_all(company)
            except Exception as e:
                _logger.exception(f"Cron sync failed for {company.name}: {e}")
