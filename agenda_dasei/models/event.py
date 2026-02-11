# -*- coding: utf-8 -*-
# Copyright 2026 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class EventEvent(models.Model):
    _inherit = 'event.event'

    @api.onchange('event_type_id')
    def _onchange_event_type_set_website(self):
        """
        Auto-map event to website based on event_type.name (template code).
        
        Rules:
        - A1, A2, A3... → dasei1 (Einstiege)
        - B1, B2, B3... → dasei2 (Grundstufe)
        - C1, C2, C3... → dasei2 (Grundstufe)  
        - D1, D2, D3... → dasei2 (Grundstufe)
        - Other codes → no change (keep default)
        
        Triggered on:
        - Event creation (when event_type_id is set)
        - Event type change (manual edit)
        """
        if not self.event_type_id:
            return

        template_code = (self.event_type_id.name or '').strip().upper()
        if not template_code:
            return

        # Extract first letter from template code
        first_letter = template_code[0] if template_code else ''

        # Map to website
        website_domain_code = None
        if first_letter == 'A':
            website_domain_code = 'dasei1'
        elif first_letter in ['B', 'C', 'D']:
            website_domain_code = 'dasei2'
        
        if website_domain_code:
            website = self.env['website'].search([
                ('domain_code', '=', website_domain_code)
            ], limit=1)
            
            if website:
                self.domain_code = website
                _logger.debug(
                    "Auto-mapped event %s with template code %s → website %s",
                    self.id or '(new)', template_code, website_domain_code
                )
            else:
                _logger.warning(
                    "Website with domain_code '%s' not found for template code %s",
                    website_domain_code, template_code
                )

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to ensure website mapping runs on sync-created events.
        
        Since onchange doesn't trigger during programmatic create (sync),
        we need to apply the mapping logic here as well.
        """
        records = super().create(vals_list)
        
        for record in records:
            if record.event_type_id:
                # Run the mapping logic
                template_code = (record.event_type_id.name or '').strip().upper()
                first_letter = template_code[0] if template_code else ''
                
                website_domain_code = None
                if first_letter == 'A':
                    website_domain_code = 'dasei1'
                elif first_letter in ['B', 'C', 'D']:
                    website_domain_code = 'dasei2'
                
                if website_domain_code:
                    website = self.env['website'].search([
                        ('domain_code', '=', website_domain_code)
                    ], limit=1)
                    
                    if website and record.domain_code != website:
                        record.domain_code = website
                        _logger.info(
                            "Auto-mapped synced event %s (%s) with template %s → %s",
                            record.id, record.name, template_code, website_domain_code
                        )
        
        return records
