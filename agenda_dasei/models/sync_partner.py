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
        """Extend sync_all to include partner sync and registration sync"""
        result = super().sync_all(company)

        # Sync contacts → partners
        try:
            # First, build the participant → kurs_level mapping from kursteilnehmer
            # This is used during contact sync to set ms_kurs_level directly
            participant_kurs_map = self._build_participant_kurs_map(company)
            _logger.info(f"Built participant kurs map with {len(participant_kurs_map)} entries")

            # Now sync contacts with kurs levels applied
            contact_stats = self.sync_contacts(company, participant_kurs_map)
            result['contacts'] = contact_stats.get('synced', 0)
            result['kursteilnehmer'] = len(participant_kurs_map)
            _logger.info(f"Contacts: {contact_stats}")

        except Exception as e:
            _logger.exception(f"Partner sync failed: {e}")

        # Sync event registrations (plan_veranstaltungsteilnehmer)
        try:
            reg_stats = self.sync_registrations(company)
            result['registrations'] = reg_stats.get('synced', 0)
            _logger.info(f"Registrations: {reg_stats}")
        except Exception as e:
            _logger.exception(f"Registration sync failed: {e}")

        return result

    def sync_contacts(self, company, participant_kurs_map=None):
        """Sync contacts from SharePoint to res.partner
        
        Args:
            company: res.company record
            participant_kurs_map: dict of contact_id → kurs_code from kursteilnehmer evaluation
        """
        if participant_kurs_map is None:
            participant_kurs_map = {}
            
        list_guid = company.ms_list_contacts
        if not list_guid:
            return {'synced': 0, 'created': 0, 'updated': 0, 'skipped': 0}

        _logger.info("Fetching contacts from SharePoint...")
        sp_items = self._get_list_items(company, list_guid)
        _logger.info(f"Fetched {len(sp_items)} contacts from SharePoint, processing...")

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

            result = self._sync_contact(company, sp_item, participant_kurs_map)
            stats['synced'] += 1
            stats[result] += 1

        return stats

    def _sync_contact(self, company, sp_item, participant_kurs_map=None):
        """Sync a single contact to res.partner
        
        Args:
            participant_kurs_map: dict of contact_id → kurs_code for setting ms_kurs_level
        """
        if participant_kurs_map is None:
            participant_kurs_map = {}
            
        Partner = self.env['res.partner']

        sp_id = sp_item['id']
        sp_etag = sp_item.get('@odata.etag', '')
        sp_fields = sp_item.get('fields', {})
        
        # Look up kurs level from participant map
        kurs_level = participant_kurs_map.get(str(sp_id))

        # Find existing partner by ms_contact_id or email
        odoo_record = Partner.search([('ms_contact_id', '=', sp_id)], limit=1)

        if not odoo_record:
            # Try to match by email
            email = sp_fields.get('Email')
            if email:
                odoo_record = Partner.search([('email', '=ilike', email)], limit=1)

        if not odoo_record:
            # Create new partner
            vals = self._map_contact_from_sp(sp_fields, kurs_level)
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
            # Even if contact unchanged, update kurs_level if we have new data
            if kurs_level and odoo_record.ms_kurs_level != kurs_level:
                odoo_record.write({'ms_kurs_level': kurs_level})
                _logger.info(f"Updated kurs_level for '{odoo_record.name}': {kurs_level}")
            return 'skipped'

        # Update existing
        vals = self._map_contact_from_sp(sp_fields, kurs_level)
        vals['ms_contact_id'] = sp_id
        vals['ms_version'] = sp_etag
        odoo_record.write(vals)

        return 'updated'

    def _map_contact_from_sp(self, sp_fields, kurs_level=None):
        """Map SharePoint contact fields to res.partner
        
        Args:
            kurs_level: Optional kurs code from kursteilnehmer evaluation (e.g., 'M17', 'ZR')
        """
        # Parse status
        status_id = None
        try:
            status_id = int(sp_fields.get('StatusLookupId', 0))
        except (ValueError, TypeError):
            pass

        vals = {
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
        
        # Include kurs_level if provided (from kursteilnehmer evaluation)
        if kurs_level:
            vals['ms_kurs_level'] = kurs_level
            
        return vals

    def _build_participant_kurs_map(self, company):
        """Build mapping of participant contact_id → highest kurs_code.
        
        Chain: kursteilnehmer.KursLookupId → plan_kurse.kursverlauf_id → contacts._M18... → kurs_code
        
        Returns dict: participant_contact_id → kurs_code (e.g., '563' → 'M17')
        """
        # Step 1: Build contact_id → kurs_code map from product contacts (with '_' prefix)
        contact_kurs_map = self._build_kurs_code_map(company)
        if not contact_kurs_map:
            _logger.warning("No kurs code map built from contacts")
            return {}
        
        # Step 2: Build kurs_id → contact_id map from plan_kurse via kursverlauf_id
        kurs_to_contact_map = self._build_kurs_to_contact_map(company)
        if not kurs_to_contact_map:
            _logger.warning("No kurs_to_contact map built from plan_kurse")
            return {}
        
        # Step 3: Evaluate kursteilnehmer to map participants → kurs codes
        list_guid = company.ms_list_kursteilnehmer
        if not list_guid:
            return {}

        _logger.info("Fetching kursteilnehmer from SharePoint...")
        sp_items = self._get_list_items(company, list_guid)
        _logger.info(f"Fetched {len(sp_items)} kursteilnehmer records")

        # Priority: ZR/ZT > M?/N? (not ME/NE) > ME/NE
        def get_kurs_priority(kurs_code):
            if not kurs_code:
                return 0
            if kurs_code in ('ZR', 'ZT'):
                return 30  # Aufbaustufe (highest)
            if kurs_code.startswith(('M', 'N')) and kurs_code not in ('ME', 'NE'):
                return 20  # Grundstufe
            if kurs_code in ('ME', 'NE'):
                return 10  # Einstiege
            return 0

        participant_map = {}  # contact_id → (kurs_code, priority)
        
        # Debug counters
        debug_stats = {'total': 0, 'no_status': 0, 'invalid_status': 0, 'no_contact': 0, 'no_kurs': 0, 'kurs_not_found': 0, 'matched': 0}

        # Track unique KursLookupIds for debugging
        valid_kurs_ids = set()
        
        for sp_item in sp_items:
            sp_fields = sp_item.get('fields', {})
            debug_stats['total'] += 1

            # Filter by valid teilnahmestatus
            status_id = sp_fields.get('StatsLookupId')
            if not status_id:
                debug_stats['no_status'] += 1
                continue
            try:
                status_int = int(status_id)
                if status_int not in VALID_TEILNAHME_STATUS_IDS:
                    debug_stats['invalid_status'] += 1
                    continue
            except (ValueError, TypeError):
                debug_stats['invalid_status'] += 1
                continue

            contact_id = sp_fields.get('TeilnehmerLookupId')
            kurs_lookup_id = sp_fields.get('KursLookupId')
            
            # Track valid KursLookupIds for debugging
            if kurs_lookup_id:
                valid_kurs_ids.add(str(kurs_lookup_id))

            if not contact_id:
                debug_stats['no_contact'] += 1
                continue
            if not kurs_lookup_id:
                debug_stats['no_kurs'] += 1
                continue

            # Two-step lookup: KursLookupId → plan_kurse.kursverlauf_id → contact kurs_code
            contact_id_for_kurs = kurs_to_contact_map.get(str(kurs_lookup_id))
            if not contact_id_for_kurs:
                debug_stats['kurs_not_found'] += 1
                if debug_stats['kurs_not_found'] <= 5:
                    _logger.info(f"KursLookupId {kurs_lookup_id} not found in kurs_to_contact_map (participant {contact_id})")
                continue
            
            kurs_code = contact_kurs_map.get(contact_id_for_kurs)
            if not kurs_code:
                debug_stats['kurs_not_found'] += 1
                if debug_stats['kurs_not_found'] <= 5:
                    _logger.info(f"Contact {contact_id_for_kurs} (from kurs {kurs_lookup_id}) not found in contact_kurs_map")
                continue
            
            debug_stats['matched'] += 1

            priority = get_kurs_priority(kurs_code)
            contact_id_str = str(contact_id)

            # Keep highest priority kurs for this participant
            if contact_id_str not in participant_map:
                participant_map[contact_id_str] = (kurs_code, priority)
            else:
                existing_kurs, existing_priority = participant_map[contact_id_str]
                if priority > existing_priority:
                    participant_map[contact_id_str] = (kurs_code, priority)

        _logger.info(f"Kursteilnehmer debug: {debug_stats}")
        _logger.info(f"Valid-status KursLookupIds (unique): {sorted(valid_kurs_ids)[:20]}...")
        _logger.info(f"Kurs-to-contact map keys (plan_kurse IDs): {sorted(kurs_to_contact_map.keys())[:20]}...")
        _logger.info(f"Contact-kurs map keys (contact IDs): {sorted(contact_kurs_map.keys())[:20]}...")
        
        # Return just the kurs codes (without priorities)
        return {cid: kurs for cid, (kurs, _) in participant_map.items()}

    def _build_kurs_to_contact_map(self, company):
        """Build mapping of plan_kurse IDs → contact IDs.
        
        HARDCODED until July 31, 2026 - SharePoint kursverlauf_id field not working.
        TODO: Replace with dynamic lookup once SharePoint field is fixed (post Feb 1st).
        
        Returns dict: kurs_id → contact_id (e.g., '119' → '477')
        """
        # Hardcoded mapping: kurs_id → contact_id
        # See chat/2026-01-26-kursteilnehmer_mapping_summary.md for details
        kurs_to_contact = {
            # M16 - Tageskurs München (variants M16E, M16T)
            '119': '477', '100': '477', '120': '477',
            # M17 - Tageskurs München
            '124': '533', '110': '533', '125': '533',
            # M18 - Tageskurs München  
            '130': '534', '111': '534', '131': '534',
            # N16 - Tageskurs Nürnberg
            '101': '478',
            # N17 - Tageskurs Nürnberg
            '122': '535',
            # N18 - Tageskurs Nürnberg
            '127': '536',
            # M16B - Blockprogramm München
            '118': '403',
            # M17B - Blockprogramm München
            '123': '529',
            # M18B - Blockprogramm München
            '129': '530',
            # N16B - Blockprogramm Nürnberg
            '121': '329',
            # N17B - Blockprogramm Nürnberg
            '126': '531',
            # N18B - Blockprogramm Nürnberg
            '132': '532',
            # Z15R - Profil ZR 2026-2028
            '115': '512',
            # Z15T - Profil ZT 2026-2028
            '116': '550',
            # Z15 (112) - missing contact_id, TODO: create SP product entry
        }
        
        _logger.info(f"Using hardcoded kurs→contact map with {len(kurs_to_contact)} entries")
        return kurs_to_contact

    def _build_kurs_code_map(self, company):
        """Build mapping of SharePoint contact IDs → Kurs codes.
        
        Kurs products are stored in the contacts list with FullName starting with underscore,
        e.g., '_M17_Tageskurs München' → Kurs code 'M17'
        
        We extract the code pattern (letters + optional digits) after the first underscore.
        """
        list_guid = company.ms_list_contacts
        if not list_guid:
            return {}

        _logger.info("Fetching contacts for kurs code map...")
        sp_items = self._get_list_items(company, list_guid)
        kurs_map = {}

        for sp_item in sp_items:
            sp_id = str(sp_item.get('id', ''))
            sp_fields = sp_item.get('fields', {})
            full_name = sp_fields.get('FullName', '')

            # Only process product references (start with underscore)
            if not full_name.startswith('_'):
                continue

            # Extract Kurs code from FullName like '_M17_Tageskurs' or '_ZR_Regie'
            # Pattern: _<CODE>_... where CODE is letters + optional digits
            parts = full_name.split('_')
            if len(parts) >= 2:
                kurs_code = parts[1]  # e.g., 'M17', 'ZR', 'ME'
                if kurs_code:
                    kurs_map[sp_id] = kurs_code
                    _logger.info(f"Kurs map: contact_id={sp_id} → kurs_code={kurs_code} (from '{full_name}')")

        return kurs_map
