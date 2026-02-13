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

        stats = {'synced': 0, 'created': 0, 'updated': 0, 'unchanged': 0, 'skipped': 0}
        
        # Track status distribution for debugging
        status_counts = {}
        
        # Sample SP IDs for debugging
        sample_sp_ids = []

        for sp_item in sp_items:
            # Count status distribution
            sp_fields = sp_item.get('fields', {})
            status_id = sp_fields.get('StatusLookupId', 'None')
            status_counts[status_id] = status_counts.get(status_id, 0) + 1
            
            # Collect sample IDs
            if len(sample_sp_ids) < 10:
                sample_sp_ids.append(sp_item['id'])
            
            result = self._sync_registration(company, sp_item)
            stats['synced'] += 1
            stats[result] += 1

        _logger.info(f"Registration status distribution: {status_counts}")
        _logger.info(f"Sample SharePoint IDs: {sample_sp_ids}")
        _logger.info(f"Odoo ms_id range: 7882-15274 (968 records)")
        return stats

    def backfill_registration_mails(self, registrations=None):
        """Trigger mail schedulers for registrations that were synced without mail generation.
        
        Call this after sync to generate confirmation emails/tickets for 'open' registrations.
        Can be run via cron or manually.
        
        Args:
            registrations: Optional recordset. If None, finds all ms_synced registrations in 'open' state.
        """
        if registrations is None:
            registrations = self.env['event.registration'].search([
                ('ms_synced', '=', True),
                ('state', '=', 'open'),
            ])
        
        if not registrations:
            _logger.info("No registrations to backfill mails for")
            return
        
        _logger.info(f"Backfilling mail schedulers for {len(registrations)} registrations...")
        
        # Find event mail schedulers for "after subscription" type
        onsubscribe_schedulers = self.env['event.mail'].sudo().search([
            ('event_id', 'in', registrations.event_id.ids),
            ('interval_type', '=', 'after_sub')
        ])
        
        if onsubscribe_schedulers:
            # Reset mail_done to allow re-processing
            onsubscribe_schedulers.write({'mail_done': False})
            # Execute will create missing event.mail.registration records and send mails
            onsubscribe_schedulers.execute()
            _logger.info(f"Executed {len(onsubscribe_schedulers)} mail schedulers")
        else:
            _logger.info("No 'after_sub' mail schedulers found for these events")

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
        
        sp_id = str(sp_item['id'])  # Ensure string for ms_id comparison
        sp_etag = sp_item.get('@odata.etag', '')
        sp_fields = sp_item.get('fields', {})
        
        # Debug for specific known ID
        debug_id = (sp_id == '13677')

        # Resolve event from VeranstaltungLookupId
        event_sp_id = sp_fields.get('VeranstaltungLookupId')
        if not event_sp_id:
            if debug_id: _logger.info(f"DEBUG {sp_id}: No event link")
            return 'skipped'
            
        event = Event.search([('ms_id', '=', str(event_sp_id))], limit=1)
        if not event:
            # Event not synced - could be a heading event (event_type.name like "d_")
            if debug_id: _logger.info(f"DEBUG {sp_id}: Event {event_sp_id} not found (may be heading)")
            return 'skipped'
        if debug_id: _logger.info(f"DEBUG {sp_id}: Found event {event.id} (ms_id={event_sp_id})")

        # Find existing registration FIRST (before partner check)
        registration = Registration.search([
            ('ms_id', '=', sp_id),
        ], limit=1)
        if debug_id: _logger.info(f"DEBUG {sp_id}: Existing registration search result: {registration}")

        # Resolve partner from TeilnehmerLookupId
        partner_sp_id = sp_fields.get('TeilnehmerLookupId')
        partner = False
        if partner_sp_id:
            partner = Partner.search([('ms_contact_id', '=', str(partner_sp_id))], limit=1)
        if debug_id: _logger.info(f"DEBUG {sp_id}: Partner search for {partner_sp_id}: {partner}")
        
        # For NEW registrations: require partner (skip orphans)
        # For EXISTING registrations: allow update even without partner (keeps historical data)
        if not registration and not partner:
            if debug_id: _logger.info(f"DEBUG {sp_id}: No registration AND no partner - skipping")
            return 'skipped'

        vals = self._map_registration_from_sp(company, sp_fields, event, partner)
        if debug_id: 
            status_id = sp_fields.get('StatusLookupId')
            _logger.info(f"DEBUG {sp_id}: SP StatusLookupId={status_id} → state={vals.get('state')}")
            if registration:
                _logger.info(f"DEBUG {sp_id}: Current Odoo state={registration.state}")

        # Use context to skip mail/PDF generation during sync
        # install_mode=True is key - it prevents _update_mail_schedulers() from running wkhtmltopdf
        Registration = Registration.with_context(
            mail_create_nosubscribe=True,
            mail_create_nolog=True,
            mail_notrack=True,
            tracking_disable=True,
            no_reset_password=True,
            import_file=True,
            install_mode=True,  # Critical: prevents event mail schedulers from triggering PDF generation
        )

        if not registration:
            # Create new registration - partner is guaranteed at this point (checked above)
            vals['ms_id'] = sp_id
            vals['ms_version'] = sp_etag
            vals['ms_synced'] = True
            vals['event_id'] = event.id
            vals['partner_id'] = partner.id
            vals['name'] = partner.name
            vals['email'] = partner.email
            vals['phone'] = partner.phone
            Registration.create(vals)
            return 'created'

        # Check if changed
        if registration.ms_version == sp_etag:
            if debug_id: _logger.info(f"DEBUG {sp_id}: Version unchanged, skipping (existing)")
            return 'unchanged'  # Different from 'skipped' (no partner)

        if debug_id: _logger.info(f"DEBUG {sp_id}: Version changed, updating")

        # Update existing registration
        # Update partner info if partner found (may fill in previously missing data)
        if partner and not registration.partner_id:
            vals['partner_id'] = partner.id
            vals['name'] = partner.name
            vals['email'] = partner.email
            vals['phone'] = partner.phone
        
        vals['ms_version'] = sp_etag
        registration.with_context(
            mail_create_nosubscribe=True,
            mail_notrack=True,
            tracking_disable=True,
        ).write(vals)
        return 'updated'

    def _map_registration_from_sp(self, company, sp_fields, event, partner):
        """Map SharePoint plan_veranstaltungsteilnehmer fields to event.registration
        
        SharePoint fields:
        - StatusLookupId: Registration status
        - UE: Units attended
        - Bemerkung: Notes
        """
        vals = {
            'units': sp_fields.get('UE', 0) or 0,
            'internal_notes': sp_fields.get('Bemerkung', ''),
        }

        # Map status — only set if we have a known mapping
        # Unknown StatusLookupIds are logged and state is NOT overwritten
        status_id = sp_fields.get('StatusLookupId')
        if status_id is not None:
            status_int = int(status_id)
            state = STATUS_TO_REGISTRATION_STATE.get(status_int)
            if state:
                vals['state'] = state
            else:
                _logger.warning(
                    "Unmapped StatusLookupId=%s for registration SP %s (event %s, partner %s) — state NOT updated",
                    status_int,
                    sp_fields.get('id', '?'),
                    event.id if event else '?',
                    partner.name if partner else '?',
                )
        else:
            # No StatusLookupId at all — default to draft for new records only
            vals['state'] = 'draft'

        return vals
