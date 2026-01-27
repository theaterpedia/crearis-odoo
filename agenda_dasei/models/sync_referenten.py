# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

"""
DASEi Referent Sync

Maps SharePoint plan_referenten to Odoo res.users for event.user_id assignment.
The 'user' field in plan_referenten holds contacts.id directly.
We match: plan_referenten.user → contacts.id → res.partner.ms_id → res.users

Cache is built once per sync run and reused for all events.
"""

import logging
from odoo import models

_logger = logging.getLogger(__name__)


class DaseiReferentSync(models.AbstractModel):
    _name = 'dasei.referent.sync'
    _description = 'DASEi Referent to User Mapping'

    # In-memory cache: {company_id: {sp_referent_id: odoo_user_id}}
    _referent_cache = {}

    def get_referent_user_id(self, company, sp_referent_id):
        """
        Get Odoo user ID for a SharePoint referent ID.
        
        Args:
            company: res.company record
            sp_referent_id: SharePoint plan_referenten ID (int or str)
        
        Returns:
            int: Odoo res.users ID, or False if not found
        """
        if not sp_referent_id:
            return False
        
        sp_referent_id = str(sp_referent_id)
        cache_key = company.id
        
        # Build cache if not exists
        if cache_key not in self._referent_cache:
            self._build_referent_cache(company)
        
        return self._referent_cache.get(cache_key, {}).get(sp_referent_id, False)

    def _build_referent_cache(self, company):
        """
        Build the referent→user cache by fetching plan_referenten from SharePoint.
        
        Mapping chain:
        plan_referenten.id → plan_referenten.contactLookupId → contacts.id → res.partner.ms_contact_id → res.users
        
        Args:
            company: res.company record
        """
        cache_key = company.id
        self._referent_cache[cache_key] = {}
        
        list_guid = company.ms_list_referenten
        if not list_guid:
            _logger.warning("No plan_referenten list GUID configured for company %s", company.name)
            return
        
        # Get filter IDs if configured
        filter_ids = []
        if company.ms_referenten_filter:
            filter_ids = [int(x.strip()) for x in company.ms_referenten_filter.split(',') if x.strip().isdigit()]
            _logger.info("Referent filter active: %s", filter_ids)
        
        sync_engine = self.env['crearis.agenda.sync']
        
        try:
            # Fetch referenten from SharePoint
            sp_items = sync_engine._get_list_items(company, list_guid)
            _logger.info("Fetched %d referenten from SharePoint", len(sp_items))
            
            # Debug: log first item's fields
            if sp_items:
                first_fields = sp_items[0].get('fields', {})
                _logger.info("Referent sample fields: %s", list(first_fields.keys()))
            
            for sp_item in sp_items:
                sp_id = sp_item.get('id')
                sp_fields = sp_item.get('fields', {})
                
                # Apply filter if configured
                if filter_ids and int(sp_id) not in filter_ids:
                    continue
                
                # Get contacts.id from 'contact' field (stored as contactLookupId)
                contact_sp_id = sp_fields.get('contactLookupId')
                if not contact_sp_id:
                    _logger.debug("No contactLookupId for referent %s (%s)", sp_id, sp_fields.get('Title'))
                    continue
                
                # Find Odoo user by partner.ms_contact_id matching contacts.id
                user = self.env['res.users'].search([
                    ('partner_id.ms_contact_id', '=', str(contact_sp_id))
                ], limit=1)
                
                if user:
                    self._referent_cache[cache_key][str(sp_id)] = user.id
                    _logger.debug("Mapped referent %s (%s) → contact %s → user %s", 
                                 sp_id, sp_fields.get('Title'), contact_sp_id, user.login)
                else:
                    _logger.debug("No Odoo user found for referent %s (%s) with contact_sp_id %s", 
                                 sp_id, sp_fields.get('Title'), contact_sp_id)
            
            _logger.info("Referent cache built: %d mappings for company %s", 
                        len(self._referent_cache[cache_key]), company.name)
            
        except Exception as e:
            _logger.error("Failed to build referent cache: %s", str(e))

    def clear_cache(self, company=None):
        """
        Clear the referent cache.
        
        Args:
            company: res.company record (optional). If None, clears all.
        """
        if company:
            self._referent_cache.pop(company.id, None)
        else:
            self._referent_cache.clear()
        _logger.info("Referent cache cleared")
