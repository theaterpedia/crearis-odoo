# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

"""
D3: Sync plan_kurse from SharePoint

SharePoint plan_kurse contains course definitions (K26, K27, etc.)
These map to domain codes / websites in Odoo.

Fields from SharePoint:
- Title: Course name (e.g., "K27 Kassel")
- KursNr: Course number/code (e.g., "K27")
- Jahr: Year (e.g., 2027)
- Startdatum, Enddatum: Course date range
- Ort: Location (Witten, Kassel, Online)
"""

import logging
from odoo import models, api

_logger = logging.getLogger(__name__)


class AgendaSyncKurse(models.AbstractModel):
    _inherit = 'crearis.agenda.sync'

    def sync_kurse(self, company):
        """Sync courses from SharePoint plan_kurse
        
        Courses in DASEi represent annual training cohorts (K26, K27, etc.)
        They are used to:
        1. Group participants (via plan_kursteilnehmer)
        2. Map to domain codes for website filtering
        
        Returns:
            dict: Sync statistics
        """
        list_guid = company.ms_list_kurse
        if not list_guid:
            _logger.warning("No list_kurse GUID configured")
            return {'synced': 0, 'created': 0, 'updated': 0, 'skipped': 0}

        _logger.info("Fetching courses from SharePoint plan_kurse...")
        sp_items = self._get_list_items(company, list_guid)
        _logger.info(f"Fetched {len(sp_items)} courses from SharePoint")

        stats = {'synced': 0, 'created': 0, 'updated': 0, 'skipped': 0}

        for sp_item in sp_items:
            result = self._sync_kurs(company, sp_item)
            stats['synced'] += 1
            stats[result] += 1

        return stats

    def _sync_kurs(self, company, sp_item):
        """Sync a single course record
        
        Currently stores in dasei.course model for reference.
        Future: May create/update website records for domain code mapping.
        
        Args:
            company: res.company record
            sp_item: SharePoint list item dict
            
        Returns:
            str: 'created', 'updated', or 'skipped'
        """
        DaseiCourse = self.env['dasei.course']
        
        sp_id = sp_item['id']
        sp_etag = sp_item.get('@odata.etag', '')
        sp_fields = sp_item.get('fields', {})

        # Find existing record
        course = DaseiCourse.search([('ms_item_id', '=', sp_id)], limit=1)

        vals = self._map_kurs_from_sp(company, sp_fields)

        if not course:
            # Create new course
            vals['ms_item_id'] = sp_id
            vals['ms_etag'] = sp_etag
            vals['company_id'] = company.id
            DaseiCourse.create(vals)
            return 'created'

        # Check if changed
        if course.ms_etag == sp_etag:
            return 'skipped'

        # Update existing
        vals['ms_etag'] = sp_etag
        course.write(vals)
        return 'updated'

    def _map_kurs_from_sp(self, company, sp_fields):
        """Map SharePoint plan_kurse fields to dasei.course
        
        SharePoint fields:
        - Title: Full course name
        - KursNr: Course code (K26, K27)
        - Jahr: Year
        - Ort: Location
        - Startdatum, Enddatum: Date range
        """
        return {
            'name': sp_fields.get('Title', ''),
            'code': sp_fields.get('KursNr', ''),
            'year': sp_fields.get('Jahr', 0) or 0,
            'location': sp_fields.get('Ort', ''),
            'date_start': self._parse_sp_datetime(sp_fields.get('Startdatum')),
            'date_end': self._parse_sp_datetime(sp_fields.get('Enddatum')),
        }
