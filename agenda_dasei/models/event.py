# -*- coding: utf-8 -*-
# Copyright 2025 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)

# Template code first-letter → website domain_code mapping
# DASEi progression:  dasei1=Einstiege, dasei2=Grundstufe, dasei3=Aufbaustufe
# NOTE: Still used as fallback; SaaS-ready config should use website.routing_config
TEMPLATE_WEBSITE_MAP = {
    'A': 'dasei1',
    'B': 'dasei2',
    'C': 'dasei2',
    'D': 'dasei2',
}

# Checkout shortcode → domain_code routing for exec notifications
# NOTE: Fallback maps; SaaS-ready config should use website.routing_config
CHECKOUT_DOMAIN_MAP_FLAG = {
    'w': 'dasei1',  # Tageskurs → Einstiege
    'x': 'dasei1',  # Block → Einstiege
    'a': 'dasei1',  # Module A
    'b': 'dasei2',  # Module B → Grundstufe
    'c': 'dasei2',  # Module C → Grundstufe
    'd': 'dasei2',  # Module D → Grundstufe
    'e': 'dasei3',  # Module E → Aufbaustufe
    'f': 'dasei3',  # Module F → Aufbaustufe
    'g': 'dasei3',  # Module G → Aufbaustufe
}

CHECKOUT_DOMAIN_MAP_PRODUCT = {
    'MOD-A': 'dasei1',
    'MOD-B': 'dasei1',
    'MOD-C': 'dasei2',
    'MOD-D': 'dasei2',
}

# Default domain for unresolved shortcodes
CHECKOUT_DOMAIN_DEFAULT = 'dasei1'


def resolve_checkout_domain_code(parsed_ref, env=None, source_website=None):
    """Resolve domain_code for checkout notification routing.

    SaaS-ready: reads from website.routing_config if available,
    falls back to CHECKOUT_DOMAIN_MAP constants for backward compatibility.

    Args:
        parsed_ref: dict from _parse_product_ref() with keys:
            location, flag, default_code, is_single_event, original_ref
        env: Odoo environment (optional, for config lookup)
        source_website: website record to read config from (optional)

    Returns:
        str: domain_code (e.g. 'dasei1', 'dasei2', 'dasei3')
    """
    # Get routing config from website if available
    routing = {}
    website = source_website
    if not website and env:
        Website = env['website'].sudo()
        website = Website.get_current_website() if hasattr(Website, 'get_current_website') else None
    
    if website and hasattr(website, 'get_effective_config'):
        routing = website.get_effective_config('routing')
    
    # z-locations always go to dasei3 (Aufbaustufe) - hardcoded rule
    if parsed_ref.get('location') == 'z':
        return 'dasei3'

    # Single events → fallback default (all of them, including 'a*' prefix)
    if parsed_ref.get('is_single_event'):
        return routing.get('default') or CHECKOUT_DOMAIN_DEFAULT

    # Course shortcodes: route by flag
    flag = parsed_ref.get('flag')
    if flag:
        # Try website config first
        flag_to_domain = routing.get('flag_to_domain', {})
        if flag in flag_to_domain:
            return flag_to_domain[flag]
        # Fall back to hardcoded map
        if flag in CHECKOUT_DOMAIN_MAP_FLAG:
            return CHECKOUT_DOMAIN_MAP_FLAG[flag]

    # Direct default_code (MOD-A etc.)
    default_code = parsed_ref.get('default_code')
    if default_code:
        # Try website config first
        product_to_domain = routing.get('product_to_domain', {})
        if default_code in product_to_domain:
            return product_to_domain[default_code]
        # Fall back to hardcoded map
        if default_code in CHECKOUT_DOMAIN_MAP_PRODUCT:
            return CHECKOUT_DOMAIN_MAP_PRODUCT[default_code]

    return routing.get('default') or CHECKOUT_DOMAIN_DEFAULT


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
