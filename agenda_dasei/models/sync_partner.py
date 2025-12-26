# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
from odoo import models, api

_logger = logging.getLogger(__name__)

# Valid status IDs to sync from contacts
SYNC_CONTACT_STATUS_IDS = [1, 2, 3, 4, 5, 8, 9, 10]

# Valid teilnahmestatus IDs for kursteilnehmer evaluation
VALID_TEILNAHME_STATUS_IDS = [1, 3, 13]


class AgendaSyncPartner(models.AbstractModel):
    _inherit = 'crearis.agenda.sync'

    def sync_all(self, company):
        """Extend sync_all to include partner sync"""
        result = super().sync_all(company)

        # Sync contacts → partners
        try:
            contact_stats = self.sync_contacts(company)
            result['contacts'] = contact_stats.get('synced', 0)
            _logger.info(f"Contacts: {contact_stats}")

            # Evaluate kursteilnehmer for kurs levels
            kt_stats = self.evaluate_kursteilnehmer(company)
            result['kursteilnehmer'] = kt_stats.get('evaluated', 0)
            _logger.info(f"Kursteilnehmer: {kt_stats}")

        except Exception as e:
            _logger.exception(f"Partner sync failed: {e}")

        return result

    def sync_contacts(self, company):
        """Sync contacts from SharePoint to res.partner"""
        list_guid = company.ms_list_contacts
        if not list_guid:
            return {'synced': 0, 'created': 0, 'updated': 0, 'skipped': 0}

        sp_items = self._get_list_items(company, list_guid)

        stats = {'synced': 0, 'created': 0, 'updated': 0, 'skipped': 0}

        for sp_item in sp_items:
            sp_fields = sp_item.get('fields', {})

            # Skip product references (FullName starting with underscore)
            # These are course products like "_M17_Tageskurs München", not real contacts
            full_name = sp_fields.get('FullName', '')
            if full_name.startswith('_'):
                _logger.debug(f"Skipping product reference: {full_name}")
                stats['skipped'] += 1
                continue

            # Filter by status
            status_id = sp_fields.get('StatusLookupId')
            if status_id:
                try:
                    status_int = int(status_id)
                    if status_int not in SYNC_CONTACT_STATUS_IDS:
                        continue
                except (ValueError, TypeError):
                    continue

            result = self._sync_contact(company, sp_item)
            stats['synced'] += 1
            stats[result] += 1

        return stats

    def _sync_contact(self, company, sp_item):
        """Sync a single contact to res.partner"""
        Partner = self.env['res.partner']

        sp_id = sp_item['id']
        sp_etag = sp_item.get('@odata.etag', '')
        sp_fields = sp_item.get('fields', {})

        # Find existing partner by ms_contact_id or email
        odoo_record = Partner.search([('ms_contact_id', '=', sp_id)], limit=1)

        if not odoo_record:
            # Try to match by email
            email = sp_fields.get('Email')
            if email:
                odoo_record = Partner.search([('email', '=ilike', email)], limit=1)

        if not odoo_record:
            # Create new partner
            vals = self._map_contact_from_sp(sp_fields)
            vals['ms_contact_id'] = sp_id
            vals['ms_version'] = sp_etag
            odoo_record = Partner.create(vals)

            # Write back opartner_id (ignore errors - may have unique constraint issues)
            try:
                self._patch_list_item(company, company.ms_list_contacts, sp_id, {
                    'opartner_id': odoo_record.id,
                })
            except Exception as e:
                _logger.warning(f"Failed to write back opartner_id for contact {sp_id}: {e}")
            return 'created'

        # Check if changed
        if odoo_record.ms_version == sp_etag:
            return 'skipped'

        # Update existing
        vals = self._map_contact_from_sp(sp_fields)
        vals['ms_contact_id'] = sp_id
        vals['ms_version'] = sp_etag
        odoo_record.write(vals)

        return 'updated'

    def _map_contact_from_sp(self, sp_fields):
        """Map SharePoint contact fields to res.partner"""
        # Parse status
        status_id = None
        try:
            status_id = int(sp_fields.get('StatusLookupId', 0))
        except (ValueError, TypeError):
            pass

        return {
            'lastname': sp_fields.get('Title', ''),
            'firstname': sp_fields.get('FirstName', ''),
            'name': sp_fields.get('FullName') or f"{sp_fields.get('FirstName', '')} {sp_fields.get('Title', '')}".strip(),
            'email': sp_fields.get('Email', ''),
            'phone': sp_fields.get('WorkPhone', ''),
            'mobile': sp_fields.get('CellPhone', ''),
            'street': sp_fields.get('WorkAddress', ''),
            'city': sp_fields.get('WorkCity', ''),
            'zip': sp_fields.get('WorkZip', ''),
            'ms_contact_status': status_id,
        }

    def evaluate_kursteilnehmer(self, company):
        """Evaluate kursteilnehmer records to determine highest kurs level per partner"""
        list_guid = company.ms_list_kursteilnehmer
        if not list_guid:
            return {'evaluated': 0}

        sp_items = self._get_list_items(company, list_guid)

        # Group by TeilnehmerLookupId (contact ID)
        contact_kurs_map = {}  # contact_id -> highest (kurs, priority)

        for sp_item in sp_items:
            sp_fields = sp_item.get('fields', {})

            # Filter by valid teilnahmestatus
            status_id = sp_fields.get('StatsLookupId')
            if status_id:
                try:
                    status_int = int(status_id)
                    if status_int not in VALID_TEILNAHME_STATUS_IDS:
                        continue
                except (ValueError, TypeError):
                    continue

            contact_id = sp_fields.get('TeilnehmerLookupId')
            kurs_id = sp_fields.get('KursLookupId')

            if not contact_id:
                continue

            # We need to resolve KursLookupId to actual Kurs code
            # For now, store the lookup ID - we'd need another API call to resolve
            # TODO: Pre-sync plan_kurse to get Kurs codes
            if contact_id not in contact_kurs_map:
                contact_kurs_map[contact_id] = kurs_id
            else:
                # Keep highest (we'd need the actual code to compare properly)
                # For now just keep first one found
                pass

        # Update partners with kurs levels
        Partner = self.env['res.partner']
        evaluated = 0

        for contact_id, kurs_id in contact_kurs_map.items():
            partner = Partner.search([('ms_contact_id', '=', str(contact_id))], limit=1)
            if partner:
                # TODO: Resolve kurs_id to actual code (ME, MB, ZR, etc)
                # For now store the lookup ID
                partner.write({'ms_kursteilnehmer_id': str(kurs_id)})
                evaluated += 1

        return {'evaluated': evaluated}
