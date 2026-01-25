# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

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
    use_event_packages = fields.Boolean(
        'Use Event Packages',
        help="Enable event package products. Requires use_template_codes."
    )
    use_overline = fields.Boolean('Use Overline')
    use_teasertext = fields.Boolean('Use Teasertext')

    @api.depends('use_event_packages')
    def _compute_use_products(self):
        """
        T11: use_products is computed, auto-enabled when any product sub-feature is active.
        Currently: use_event_packages. Future: add more sub-features here.
        """
        for website in self:
            website.use_products = website.use_event_packages

    use_products = fields.Boolean(
        'Use Products',
        compute='_compute_use_products',
        store=True,
        readonly=True,
        help="Auto-computed: True when any product sub-feature (e.g., event packages) is enabled."
    )

    @api.constrains('use_event_packages', 'use_template_codes')
    def _check_event_packages_requires_template_codes(self):
        """
        T12: use_event_packages requires use_template_codes=True
        """
        for website in self:
            if website.use_event_packages and not website.use_template_codes:
                from odoo.exceptions import ValidationError
                raise ValidationError(
                    "Event Packages require Template Codes to be enabled first."
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