# -*- coding: utf-8 -*-
# Copyright 2025 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)

# Template code first-letter → website domain_code mapping
# DASEi progression:  dasei1=Einstiege, dasei2=Grundstufe, dasei3=Aufbaustufe
TEMPLATE_WEBSITE_MAP = {
    'A': 'dasei1',
    'B': 'dasei2',
    'C': 'dasei2',
    'D': 'dasei2',
}


class EventEvent(models.Model):
    _inherit = 'event.event'

    def _resolve_website_from_template_code(self, event_type_id):
        """Resolve website from event type template code.

        Looks up event_type.name first letter in TEMPLATE_WEBSITE_MAP
        and returns the matching website record, or None.
        """
        if not event_type_id:
            return None

        event_type = self.env['event.type'].browse(event_type_id)
        if not event_type.exists():
            return None

        template_code = (event_type.name or '').strip().upper()
        if not template_code:
            return None

        first_letter = template_code[0]
        website_domain_code = TEMPLATE_WEBSITE_MAP.get(first_letter)
        if not website_domain_code:
            return None

        website = self.env['website'].search([
            ('domain_code', '=', website_domain_code)
        ], limit=1)

        if not website:
            _logger.warning(
                "Website with domain_code '%s' not found for template code %s",
                website_domain_code, template_code
            )
        return website or None

    def _resolve_domain_code_for_template(self, event_type_id, vals):
        """DASEi: Map template code first letter → dasei1/dasei2 website.

        Overrides the crearis base hook to implement DASEi progression mapping.
        """
        website = self._resolve_website_from_template_code(event_type_id)
        if website:
            old = vals.get('domain_code')
            vals['domain_code'] = website.id
            if old and old != website.id:
                _logger.info(
                    "Remapped domain_code %s → %s (%s) for event_type %s",
                    old, website.id, website.domain_code, event_type_id
                )
        return super()._resolve_domain_code_for_template(event_type_id, vals)
