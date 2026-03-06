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