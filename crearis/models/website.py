# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json
import requests
from odoo import models, fields, api


class Website(models.Model):
    _inherit = 'website'
    _order = "domain_code"

    domain_code = fields.Char('Domain-Code', help="Subdomain on theaterpedia.org / unique key-prefix for data-keys") 
    _rec_name = "domain_code"

    is_hubsite = fields.Boolean('Hubsite')
    use_msteams = fields.Boolean('MS Teams')
    use_jitsi = fields.Boolean('Jitsi Rooms')
    use_template_codes = fields.Boolean('Use Template Codes')
    use_tracks = fields.Boolean('Use Tracks')
    # Note: use_event_packages is defined in crearis_event_package module
    use_overline = fields.Boolean('Use Overline')
    use_teasertext = fields.Boolean('Use Teasertext')
    use_milestones = fields.Boolean(
        'Use Milestones',
        help="Enable milestone workflow (gate pattern) for events in this domain"
    )

    def _compute_use_products(self):
        """
        T11: use_products is computed, auto-enabled when any product sub-feature is active.
        Detects use_event_packages dynamically (added by crearis_event_package module).
        """
        for website in self:
            # Check if use_event_packages exists (added by crearis_event_package)
            use_packages = getattr(website, 'use_event_packages', False)
            website.use_products = use_packages

    use_products = fields.Boolean(
        'Use Products',
        compute='_compute_use_products',
        store=False,  # Cannot store: depends on optional module field
        readonly=True,
        help="Auto-computed: True when any product sub-feature (e.g., event packages) is enabled."
    )

    @api.depends("company_id.domain_code")
    def _compute_is_homedomain(self):
        for website in self:
            website.is_company_domain = website.company_id.domain_code.id == website.id

    is_company_domain = fields.Boolean(compute=_compute_is_homedomain)

    post_domain_ids = fields.Many2many(
        comodel_name="website",
        relation="website_post_domains",
        column1="a_id",
        column2="b_id",
        string="Post-Domains",
    )

    event_domain_ids = fields.Many2many(
        comodel_name="website",
        relation="website_event_domains",
        column1="a_id",
        column2="b_id",
        string="Event-Domains",
    )

    # =========================
    # SHORTCODE CONFIGURATION (I2)
    # =========================

    shortcode_config = fields.Json(
        string='Shortcode Configuration',
        help='Per-domain shortcode→product mapping for checkout flow. '
             'Format: {"products": {"w": {"default_code": "...", "tier": "..."}}, '
             '"bundles": {"y": {"products": [...]}}, "contact_only": ["v"]}',
        default=lambda self: {}
    )

    shortcode_config_text = fields.Text(
        string='Shortcode Configuration (JSON)',
        compute='_compute_shortcode_config_text',
        inverse='_inverse_shortcode_config_text',
        help='Editable JSON text for shortcode configuration'
    )

    @api.depends('shortcode_config')
    def _compute_shortcode_config_text(self):
        for rec in self:
            config = rec.shortcode_config or {}
            rec.shortcode_config_text = json.dumps(config, indent=2) if config else '{}'

    def _inverse_shortcode_config_text(self):
        for rec in self:
            text = (rec.shortcode_config_text or '').strip()
            if not text or text == '{}':
                rec.shortcode_config = {}
            else:
                try:
                    rec.shortcode_config = json.loads(text)
                except json.JSONDecodeError:
                    pass  # Keep existing value on parse error

    # =========================
    # DOMAIN CONFIGURATION (Option C - Separate Fields)
    # =========================
    # Pattern follows weboptions.py: separate JSON fields per concern + stored booleans
    # See: _meta/Act26/03-14-SNAPSHOT_saas_config_externalization.md

    config_preset = fields.Selection([
        ('academy', 'Academy (Education/Training)'),
        ('retail', 'Retail / Shop'),
        ('association', 'Association / Verein'),
        ('agency', 'Agency / Events'),
        ('minimal', 'Minimal / Landing'),
    ], string='Configuration Preset', default='minimal',
       help='Base configuration preset. Local overrides are merged on top.')

    # --- Consulting Configuration ---

    consulting_config = fields.Json(
        string='Consulting Configuration',
        help='{"default_ctype": "...", "category_labels": {...}, "tone": "formal", "greeting": "Sie"}',
        default=lambda self: {}
    )

    consulting_config_text = fields.Text(
        string='Consulting Configuration (JSON)',
        compute='_compute_consulting_config_text',
        inverse='_inverse_consulting_config_text',
    )

    consulting_has_config = fields.Boolean(
        string='Has Consulting Config',
        compute='_compute_consulting_has_config',
        store=True,
        help='Whether consulting_config has any content (weboptions pattern)'
    )

    @api.depends('consulting_config')
    def _compute_consulting_has_config(self):
        for rec in self:
            rec.consulting_has_config = bool(rec.consulting_config and isinstance(rec.consulting_config, dict) and rec.consulting_config)

    @api.depends('consulting_config')
    def _compute_consulting_config_text(self):
        for rec in self:
            config = rec.consulting_config or {}
            rec.consulting_config_text = json.dumps(config, indent=2) if config else '{}'

    def _inverse_consulting_config_text(self):
        for rec in self:
            text = (rec.consulting_config_text or '').strip()
            if not text or text == '{}':
                rec.consulting_config = {}
            else:
                try:
                    rec.consulting_config = json.loads(text)
                except json.JSONDecodeError:
                    pass

    # --- Routing Configuration ---

    routing_config = fields.Json(
        string='Routing Configuration',
        help='{"flag_to_domain": {...}, "product_to_domain": {...}, "default": "..."}',
        default=lambda self: {}
    )

    routing_config_text = fields.Text(
        string='Routing Configuration (JSON)',
        compute='_compute_routing_config_text',
        inverse='_inverse_routing_config_text',
    )

    routing_has_config = fields.Boolean(
        string='Has Routing Config',
        compute='_compute_routing_has_config',
        store=True,
    )

    @api.depends('routing_config')
    def _compute_routing_has_config(self):
        for rec in self:
            rec.routing_has_config = bool(rec.routing_config and isinstance(rec.routing_config, dict) and rec.routing_config)

    @api.depends('routing_config')
    def _compute_routing_config_text(self):
        for rec in self:
            config = rec.routing_config or {}
            rec.routing_config_text = json.dumps(config, indent=2) if config else '{}'

    def _inverse_routing_config_text(self):
        for rec in self:
            text = (rec.routing_config_text or '').strip()
            if not text or text == '{}':
                rec.routing_config = {}
            else:
                try:
                    rec.routing_config = json.loads(text)
                except json.JSONDecodeError:
                    pass

    # --- Email Configuration ---

    email_config = fields.Json(
        string='Email Configuration',
        help='{"from": "...", "reply_to": "...", "tone": "formal", "greeting": "Sie"}',
        default=lambda self: {}
    )

    email_config_text = fields.Text(
        string='Email Configuration (JSON)',
        compute='_compute_email_config_text',
        inverse='_inverse_email_config_text',
    )

    email_has_config = fields.Boolean(
        string='Has Email Config',
        compute='_compute_email_has_config',
        store=True,
    )

    @api.depends('email_config')
    def _compute_email_has_config(self):
        for rec in self:
            rec.email_has_config = bool(rec.email_config and isinstance(rec.email_config, dict) and rec.email_config)

    @api.depends('email_config')
    def _compute_email_config_text(self):
        for rec in self:
            config = rec.email_config or {}
            rec.email_config_text = json.dumps(config, indent=2) if config else '{}'

    def _inverse_email_config_text(self):
        for rec in self:
            text = (rec.email_config_text or '').strip()
            if not text or text == '{}':
                rec.email_config = {}
            else:
                try:
                    rec.email_config = json.loads(text)
                except json.JSONDecodeError:
                    pass

    # =========================
    # PRESET DEFAULTS
    # =========================
    # Placeholders: @homedomain, @domain1, @domain2, @domain3, @@homedomain
    # Only preset values are parsed; local overrides bypass this.

    PRESET_DEFAULTS = {
        'academy': {
            'consulting': {
                'default_ctype': 'purchase_consultation',
                'category_labels': {
                    'prerequisites': 'Zulassung, Anerkennung',
                    'terms_and_options': 'Frühbucher, Paketrabatt',
                    'other': 'Sonstiges',
                },
                'tone': 'formal',
                'greeting': 'Sie',
            },
            'routing': {
                'default': '@domain1',
                'flag_to_domain': {
                    'w': '@domain1',
                    'x': '@domain1',
                    'e': '@domain3',
                },
            },
            'email': {
                'from': 'service@@homedomain',
                'tone': 'formal',
            },
        },
        'retail': {
            'consulting': {
                'default_ctype': 'general_inquiry',
                'category_labels': {
                    'products': 'Produktanfrage',
                    'shipping': 'Versand & Lieferung',
                    'other': 'Sonstiges',
                },
                'tone': 'friendly',
                'greeting': 'Du',
            },
            'routing': {
                'default': '@homedomain',
            },
            'email': {
                'from': 'shop@@homedomain',
                'tone': 'friendly',
            },
        },
        'association': {
            'consulting': {
                'default_ctype': 'contact_inquiry',
                'category_labels': {
                    'membership': 'Mitgliedschaft',
                    'events': 'Veranstaltungen',
                    'other': 'Allgemeine Anfrage',
                },
                'tone': 'warm',
                'greeting': 'Sie',
            },
            'routing': {
                'default': '@homedomain',
            },
            'email': {
                'from': 'info@@homedomain',
                'tone': 'warm',
            },
        },
        'agency': {
            'consulting': {
                'default_ctype': 'event_inquiry',
                'category_labels': {
                    'booking': 'Buchungsanfrage',
                    'availability': 'Verfügbarkeit',
                    'custom': 'Individuelle Anfrage',
                },
                'tone': 'professional',
                'greeting': 'Sie',
            },
            'routing': {
                'default': '@domain1',
            },
            'email': {
                'from': 'booking@@homedomain',
                'tone': 'professional',
            },
        },
        'minimal': {
            'consulting': {
                'default_ctype': 'general_inquiry',
            },
            'routing': {
                'default': '@homedomain',
            },
            'email': {
                'from': 'noreply@@homedomain',
            },
        },
    }

    # =========================
    # EFFECTIVE CONFIG METHODS
    # =========================

    def get_effective_config(self, section):
        """
        Get merged config: preset defaults (with placeholders resolved) + local overrides.
        
        Preset placeholders (@homedomain, @domain1, @@homedomain) are resolved.
        Local overrides are NOT parsed (allows explicit legacy domain codes).
        
        Usage:
            website.get_effective_config('consulting')
            website.get_effective_config('email')
        
        Returns:
            dict: Merged configuration for the requested section
        """
        self.ensure_one()
        preset_defaults = self.PRESET_DEFAULTS.get(self.config_preset or 'minimal', {}).get(section, {})
        local_config = getattr(self, f'{section}_config', None) or {}
        
        # Resolve preset placeholders
        resolved_preset = self._resolve_domain_placeholders(preset_defaults)
        
        # Deep merge: local overrides preset (local is NOT parsed)
        result = dict(resolved_preset)
        for key, value in local_config.items():
            if isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = {**result[key], **value}
            else:
                result[key] = value
        return result

    def get_config_value(self, section, key, default=None):
        """Shorthand for single value lookup from effective config."""
        return self.get_effective_config(section).get(key, default)

    def _resolve_domain_placeholders(self, config):
        """
        Resolve domain placeholders in preset config values.
        
        Placeholders:
          @homedomain  → company's base domain_code (e.g., 'dasei')
          @domain1     → first subdomain (e.g., 'dasei1')
          @domain2     → second subdomain (e.g., 'dasei2')
          @domain3     → third subdomain (e.g., 'dasei3')
          @@homedomain → email domain suffix (e.g., '@dasei.eu')
        
        Only preset values are parsed; local overrides bypass this.
        """
        if not config:
            return config
        
        # Get homedomain from company or fallback to self
        company = self.company_id
        if company and company.domain_code:
            homedomain = company.domain_code.domain_code
        else:
            homedomain = self.domain_code or 'example'
        
        # Email domain convention: {homedomain}.eu (or .org, etc.)
        email_domain = f'@{homedomain}.eu'
        
        # Build replacement map
        replacements = {
            '@homedomain': homedomain,
            '@domain1': f'{homedomain}1',
            '@domain2': f'{homedomain}2',
            '@domain3': f'{homedomain}3',
            '@@homedomain': email_domain,
        }
        
        # 2026-08-04: substitute LONGEST placeholder first.
        # '@homedomain' is a strict suffix of '@@homedomain'. Iterating in dict
        # insertion order applied the shorter key first, so 'noreply@@homedomain'
        # became 'noreply' + '@' + 'dasei' = 'noreply@dasei' -- the TLD was never
        # appended because '@@homedomain' no longer matched. That malformed sender
        # went out on 28 checkout notifications between 2026-05-04 and 2026-07-25.
        # Sorting by length makes order-independence a property of the algorithm
        # rather than of how the map above happens to be typed, so a future
        # placeholder cannot silently reintroduce the same collision.
        ordered_placeholders = sorted(replacements, key=len, reverse=True)

        def resolve_value(val):
            if isinstance(val, str):
                for placeholder in ordered_placeholders:
                    val = val.replace(placeholder, replacements[placeholder])
                return val
            elif isinstance(val, dict):
                return {k: resolve_value(v) for k, v in val.items()}
            elif isinstance(val, list):
                return [resolve_value(v) for v in val]
            return val
        
        return resolve_value(config)