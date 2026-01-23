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
SYNC_PRODUCT_IDS = ['530', '532', '534', '536', '512', '550']


class SyncProduct(models.AbstractModel):
    """Sync SharePoint product contacts to Odoo products."""
    _name = 'dasei.sync.product'
    _inherit = 'crearis.agenda.sync'
    _description = 'SharePoint Product Sync'

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
            vals = self._prepare_product_vals(sp_id, sp_etag, sp_fields)
            odoo_record = Product.create(vals)
            _logger.info(f"Created product: {odoo_record.name} (SP ID: {sp_id})")
            return 'created'

        # Check if update needed
        if odoo_record.ms_etag == sp_etag:
            return 'skipped'

        # Update existing
        vals = self._prepare_product_vals(sp_id, sp_etag, sp_fields)
        odoo_record.write(vals)
        _logger.info(f"Updated product: {odoo_record.name} (SP ID: {sp_id})")
        return 'updated'

    def _prepare_product_vals(self, sp_id, sp_etag, sp_fields):
        """Prepare product values from SharePoint fields."""
        Product = self.env['product.template']
        
        fullname = sp_fields.get('FullName', '')
        
        # Parse course attributes from fullname
        course_attrs = Product._parse_course_fullname(fullname)
        
        # Build display name
        name = fullname[1:] if fullname.startswith('_') else fullname  # Remove underscore
        
        vals = {
            'name': name,
            'ms_contact_id': sp_id,
            'ms_etag': sp_etag,
            'type': 'service',  # Courses are services
            'sale_ok': True,
            'purchase_ok': False,
            **course_attrs,
        }
        
        return vals


class SyncCourseParticipation(models.AbstractModel):
    """Sync SharePoint plan_kursteilnehmer to course participations."""
    _name = 'dasei.sync.participation'
    _inherit = 'crearis.agenda.sync'
    _description = 'SharePoint Course Participation Sync'

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
