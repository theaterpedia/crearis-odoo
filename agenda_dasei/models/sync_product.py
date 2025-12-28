# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)

# Product contact IDs to sync
# M18: 530 (Block), 534 (Tag)
# N18: 532 (Block), 536 (Tag)
# ZR: 512, ZT: 550
# Offenes Programm: 474
SYNC_PRODUCT_IDS = ['530', '532', '534', '536', '512', '550', '474']

# Standard order for event types in course
EVENT_ORDER = {
    'a0': 1, 'a1': 2, 'a2': 3, 'a3': 4, 'a4': 5, 'a5': 6,
    'aa': 0, 'info': 0,
}


class SyncProduct(models.AbstractModel):
    """Extend sync engine to include product sync."""
    _inherit = 'crearis.agenda.sync'

    def sync_all(self, company):
        """Extend sync_all to include product sync before partners."""
        # First sync products (before partners, as they're needed for participations)
        try:
            product_stats = self.sync_products(company)
            _logger.info(f"Products: {product_stats}")
        except Exception as e:
            _logger.exception(f"Product sync failed: {e}")

        # Call parent sync (event_types, events, contacts, kursteilnehmer)
        result = super().sync_all(company)
        result['products'] = product_stats.get('synced', 0) if 'product_stats' in dir() else 0
        
        # Sync course-event relationships after events are synced
        try:
            event_mapping_stats = self.sync_course_event_mapping(company)
            _logger.info(f"Course-Event Mapping: {event_mapping_stats}")
            result['course_event_mapping'] = event_mapping_stats.get('synced', 0)
        except Exception as e:
            _logger.exception(f"Course-Event mapping sync failed: {e}")
            result['course_event_mapping'] = 0
        
        return result

    def sync_products(self, company):
        """Sync course products from SharePoint contacts list."""
        list_guid = company.ms_list_contacts
        if not list_guid:
            _logger.warning("No contacts list configured for company %s", company.name)
            return {'synced': 0, 'created': 0, 'updated': 0, 'skipped': 0}

        sp_items = self._get_list_items(company, list_guid)

        stats = {'synced': 0, 'created': 0, 'updated': 0, 'skipped': 0}

        for sp_item in sp_items:
            sp_id = str(sp_item.get('id', ''))
            
            # Only sync specific product IDs
            if sp_id not in SYNC_PRODUCT_IDS:
                continue

            result = self._sync_product(company, sp_item)
            stats['synced'] += 1
            stats[result] += 1

        return stats

    def _sync_product(self, company, sp_item):
        """Sync a single product contact to product.template."""
        Product = self.env['product.template']

        sp_id = str(sp_item['id'])
        sp_etag = sp_item.get('@odata.etag', '')
        sp_fields = sp_item.get('fields', {})

        # Find existing product
        odoo_record = Product.search([('ms_contact_id', '=', sp_id)], limit=1)

        if not odoo_record:
            # Create new product
            vals = self._prepare_product_vals(company, sp_id, sp_etag, sp_fields)
            odoo_record = Product.create(vals)
            _logger.info(f"Created product: {odoo_record.name} (SP ID: {sp_id})")
            return 'created'

        # Check if update needed
        if odoo_record.ms_etag == sp_etag:
            return 'skipped'

        # Update existing
        vals = self._prepare_product_vals(company, sp_id, sp_etag, sp_fields)
        odoo_record.write(vals)
        _logger.info(f"Updated product: {odoo_record.name} (SP ID: {sp_id})")
        return 'updated'

    def _generate_default_code(self, sp_id, fullname):
        """Generate default_code from SharePoint ID and product name.
        
        Mappings:
        - M18_Blockprogramm München (530) → m18b
        - M18_Tageskurs München (534) → m18t
        - N18_Blockprogramm Nürnberg (532) → n18b
        - N18_Tageskurs Nürnberg (536) → n18t
        - Profil ZR 2026-2028 (512) → z15r
        - Profil ZT 2026-2028 (550) → z15t
        - Offenes Programm (474) → op
        """
        # Direct mapping for known products
        code_map = {
            '530': 'm18b',  # M18_Blockprogramm München
            '532': 'n18b',  # N18_Blockprogramm Nürnberg
            '534': 'm18t',  # M18_Tageskurs München
            '536': 'n18t',  # N18_Tageskurs Nürnberg
            '512': 'z15r',  # Profil ZR
            '550': 'z15t',  # Profil ZT
            '474': 'op',    # Offenes Programm
        }
        
        if sp_id in code_map:
            return code_map[sp_id]
        
        # Fallback: generate from name pattern
        name_lower = fullname.lower()
        
        # Pattern: M18_Blockprogramm → m18b, N18_Tageskurs → n18t
        import re
        match = re.match(r'_?([mn])(\d+)_(block|tag)', name_lower)
        if match:
            city = match.group(1)  # m or n
            year = match.group(2)  # 18
            prog_type = 'b' if match.group(3) == 'block' else 't'
            return f"{city}{year}{prog_type}"
        
        # Pattern: Profil ZR/ZT → z + cohort + r/t
        match = re.match(r'_?profil z([rt])', name_lower)
        if match:
            suffix = match.group(1)  # r or t
            return f"z00{suffix}"  # Placeholder cohort
        
        # Fallback to SP ID
        return f"sp{sp_id}"

    def _prepare_product_vals(self, company, sp_id, sp_etag, sp_fields):
        """Prepare product values from SharePoint fields."""
        Product = self.env['product.template']
        
        fullname = sp_fields.get('FullName', '')
        
        # Parse course attributes from fullname
        course_attrs = Product._parse_course_fullname(fullname)
        
        # Build display name
        name = fullname[1:] if fullname.startswith('_') else fullname  # Remove underscore
        
        # Generate default_code
        default_code = self._generate_default_code(sp_id, fullname)
        
        vals = {
            'name': name,
            'default_code': default_code,
            'ms_contact_id': sp_id,
            'ms_etag': sp_etag,
            'company_id': company.id,
            'type': 'service',  # Courses are services
            'sale_ok': True,
            'purchase_ok': False,
            **course_attrs,
        }
        
        return vals

    # =========================================================================
    # COURSE PARTICIPATION SYNC
    # =========================================================================

    def sync_participations(self, company):
        """Sync course participations from plan_kursteilnehmer."""
        list_guid = company.ms_list_kursteilnehmer
        if not list_guid:
            _logger.warning("No kursteilnehmer list configured for company %s", company.name)
            return {'synced': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0}

        sp_items = self._get_list_items(company, list_guid)

        stats = {'synced': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0}

        for sp_item in sp_items:
            sp_fields = sp_item.get('fields', {})
            
            # Only sync participations for our tracked products
            kurs_id = str(sp_fields.get('KursLookupId', ''))
            if kurs_id not in SYNC_PRODUCT_IDS:
                continue

            result = self._sync_participation(company, sp_item)
            stats['synced'] += 1
            stats[result] += 1

        return stats

    def _sync_participation(self, company, sp_item):
        """Sync a single plan_kursteilnehmer to course.participation."""
        Participation = self.env['dasei.course.participation']
        Product = self.env['product.template']
        Partner = self.env['res.partner']

        sp_id = str(sp_item['id'])
        sp_etag = sp_item.get('@odata.etag', '')
        sp_fields = sp_item.get('fields', {})

        # Get related records
        kurs_id = str(sp_fields.get('KursLookupId', ''))
        teilnehmer_id = str(sp_fields.get('TeilnehmerLookupId', ''))

        # Find course product
        course = Product.search([('ms_contact_id', '=', kurs_id)], limit=1)
        if not course:
            _logger.warning(f"Course not found for KursLookupId: {kurs_id}")
            return 'errors'

        # Find participant partner
        partner = Partner.search([('ms_contact_id', '=', teilnehmer_id)], limit=1)
        if not partner:
            _logger.warning(f"Partner not found for TeilnehmerLookupId: {teilnehmer_id}")
            return 'errors'

        # Find existing participation
        odoo_record = Participation.search([('ms_item_id', '=', sp_id)], limit=1)

        if not odoo_record:
            # Create new participation
            vals = self._prepare_participation_vals(sp_id, sp_etag, sp_fields, course.id, partner.id)
            Participation.create(vals)
            _logger.info(f"Created participation: {partner.name} -> {course.name}")
            return 'created'

        # Check if update needed
        if odoo_record.ms_etag == sp_etag:
            return 'skipped'

        # Update existing
        vals = self._prepare_participation_vals(sp_id, sp_etag, sp_fields, course.id, partner.id)
        odoo_record.write(vals)
        _logger.info(f"Updated participation: {partner.name} -> {course.name}")
        return 'updated'

    def _prepare_participation_vals(self, sp_id, sp_etag, sp_fields, course_id, partner_id):
        """Prepare participation values from SharePoint fields."""
        return {
            'ms_item_id': sp_id,
            'ms_etag': sp_etag,
            'course_id': course_id,
            'partner_id': partner_id,
            'status_id': int(sp_fields.get('StatsLookupId', 0) or 0),
            'notes': sp_fields.get('Feld10', ''),  # Bemerkung
            'is_created': sp_fields.get('Feld1', False),  # angelegt
        }

    # =========================================================================
    # COURSE-EVENT MAPPING SYNC
    # =========================================================================

    def sync_course_event_mapping(self, company):
        """Sync course-event relationships from plan_veranstaltungsteilnehmer.
        
        This maps which events (A1, A2, etc.) belong to which course product (M17E, M18B).
        The SharePoint list plan_veranstaltungsteilnehmer contains:
        - TeilnehmerLookupId: Reference to contact (course product or person)
        - VeranstaltungLookupId: Reference to event (plan_veranstaltungen)
        
        For course products (contacts starting with '_'), we build a JSONB mapping:
        {
            "a0": {"event_id": 1328, "order": 1},
            "a1": {"event_id": 1178, "order": 2},
            ...
        }
        """
        list_guid = company.ms_list_veranstaltungsteilnehmer
        if not list_guid:
            _logger.warning("No veranstaltungsteilnehmer list configured for company %s", company.name)
            return {'synced': 0, 'courses_updated': 0, 'events_mapped': 0}

        sp_items = self._get_list_items(company, list_guid)
        
        Product = self.env['product.template']
        Event = self.env['event.event']

        # Group by course (TeilnehmerLookupId points to contact = course product)
        course_events = {}  # {course_ms_id: {shortcode: {event_id, order}}}

        for item in sp_items:
            fields = item.get('fields', {})
            course_id = str(fields.get('TeilnehmerLookupId', ''))
            event_sp_id = str(fields.get('VeranstaltungLookupId', ''))

            if not course_id or not event_sp_id:
                continue
            
            # Only process course products (those in SYNC_PRODUCT_IDS)
            if course_id not in SYNC_PRODUCT_IDS:
                continue

            if course_id not in course_events:
                course_events[course_id] = {}

            # Find Odoo event by SharePoint ID
            event = Event.search([('ms_id', '=', event_sp_id)], limit=1)
            if not event:
                _logger.debug(f"Event not found for SP ID: {event_sp_id}")
                continue
            
            if not event.event_type_id:
                _logger.debug(f"Event {event.id} has no event_type_id")
                continue

            shortcode = event.event_type_id.name.lower()
            order = EVENT_ORDER.get(shortcode, 99)
            
            course_events[course_id][shortcode] = {
                'event_id': event.id,
                'order': order,
                'ms_event_id': event_sp_id,  # Keep reference for debugging
            }

        # Update products with course_event_ids
        stats = {'synced': len(sp_items), 'courses_updated': 0, 'events_mapped': 0}
        
        for course_ms_id, events_map in course_events.items():
            product = Product.search([('ms_contact_id', '=', course_ms_id)], limit=1)
            if product:
                product.write({'course_event_ids': events_map})
                stats['courses_updated'] += 1
                stats['events_mapped'] += len(events_map)
                _logger.info(f"Updated course {product.name} with {len(events_map)} events")

        return stats
