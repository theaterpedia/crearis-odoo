# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

"""
D4: Sync plan_veranstaltungsteilnehmer from SharePoint

SharePoint plan_veranstaltungsteilnehmer contains event registrations.
These map to event.registration records in Odoo.

Key fields from SharePoint:
- TeilnehmerLookupId: Link to contact (→ res.partner)
- VeranstaltungLookupId: Link to event (→ event.event)
- StatusLookupId: Registration status (→ state)
- UE: Units attended (for partial attendance)
"""

import logging
from odoo import models, api

_logger = logging.getLogger(__name__)

# Map SharePoint StatusLookupId to Odoo registration states
# From plan_teilnahmestatus lookup table
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


class AgendaSyncRegistrations(models.AbstractModel):
    _inherit = 'crearis.agenda.sync'

    def sync_registrations(self, company):
        """Sync event registrations from SharePoint plan_veranstaltungsteilnehmer
        
        This syncs participant registrations for events.
        Direction: SharePoint → Odoo (read-only for now)
        
        Returns:
            dict: Sync statistics
        """
        list_guid = company.ms_list_veranstaltungsteilnehmer
        if not list_guid:
            _logger.warning("No list_veranstaltungsteilnehmer GUID configured")
            return {'synced': 0, 'created': 0, 'updated': 0, 'skipped': 0}

        _logger.info("Fetching registrations from SharePoint plan_veranstaltungsteilnehmer...")
        sp_items = self._get_list_items(company, list_guid)
        _logger.info(f"Fetched {len(sp_items)} registrations from SharePoint")

        stats = {'synced': 0, 'created': 0, 'updated': 0, 'skipped': 0}

        for sp_item in sp_items:
            result = self._sync_registration(company, sp_item)
            stats['synced'] += 1
            stats[result] += 1

        return stats

    def _sync_registration(self, company, sp_item):
        """Sync a single registration record
        
        Args:
            company: res.company record
            sp_item: SharePoint list item dict
            
        Returns:
            str: 'created', 'updated', or 'skipped'
        """
        Registration = self.env['event.registration']
        Event = self.env['event.event']
        Partner = self.env['res.partner']
        
        sp_id = sp_item['id']
        sp_etag = sp_item.get('@odata.etag', '')
        sp_fields = sp_item.get('fields', {})

        # Resolve event from VeranstaltungLookupId
        event_sp_id = sp_fields.get('VeranstaltungLookupId')
        if not event_sp_id:
            _logger.debug(f"Registration {sp_id} has no event link, skipping")
            return 'skipped'
            
        event = Event.search([('ms_id', '=', str(event_sp_id))], limit=1)
        if not event:
            _logger.debug(f"Event {event_sp_id} not found in Odoo, skipping registration {sp_id}")
            return 'skipped'

        # Resolve partner from TeilnehmerLookupId
        partner_sp_id = sp_fields.get('TeilnehmerLookupId')
        partner = False
        if partner_sp_id:
            partner = Partner.search([('ms_contact_id', '=', str(partner_sp_id))], limit=1)

        # Find existing registration
        registration = Registration.search([
            ('ms_id', '=', sp_id),
            ('event_id', '=', event.id),
        ], limit=1)

        vals = self._map_registration_from_sp(company, sp_fields, event, partner)

        if not registration:
            # Create new registration
            vals['ms_id'] = sp_id
            vals['ms_version'] = sp_etag
            vals['ms_synced'] = True
            vals['event_id'] = event.id
            if partner:
                vals['partner_id'] = partner.id
                vals['name'] = partner.name
                vals['email'] = partner.email
                vals['phone'] = partner.phone
            Registration.create(vals)
            return 'created'

        # Check if changed
        if registration.ms_version == sp_etag:
            return 'skipped'

        # Update existing
        vals['ms_version'] = sp_etag
        registration.write(vals)
        return 'updated'

    def _map_registration_from_sp(self, company, sp_fields, event, partner):
        """Map SharePoint plan_veranstaltungsteilnehmer fields to event.registration
        
        SharePoint fields:
        - StatusLookupId: Registration status
        - UE: Units attended
        - Bemerkung: Notes
        """
        # Map status
        status_id = sp_fields.get('StatusLookupId')
        state = 'draft'
        if status_id:
            state = STATUS_TO_REGISTRATION_STATE.get(int(status_id), 'draft')

        return {
            'state': state,
            'units': sp_fields.get('UE', 0) or 0,
            'internal_notes': sp_fields.get('Bemerkung', ''),
        }
