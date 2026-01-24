# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Company(models.Model):
    _inherit = "res.company"

    use_event_packages = fields.Boolean(
        string='Event Packages',
        default=False,
        help="Enable event package products. Requires Template Codes to be active."
    )

    @api.onchange('use_template_codes')
    def _onchange_use_template_codes_packages(self):
        """Disable event packages if template codes are disabled."""
        if not self.use_template_codes:
            self.use_event_packages = False

    @api.constrains('use_event_packages', 'use_template_codes')
    def _check_event_packages_requires_template_codes(self):
        """Ensure event packages can only be enabled if template codes are active."""
        for company in self:
            if company.use_event_packages and not company.use_template_codes:
                raise ValidationError(
                    "Event Packages require Template Codes to be enabled first."
                )


class Website(models.Model):
    _inherit = 'website'

    use_event_packages = fields.Boolean(
        string='Event Packages',
        default=False,
        help="Enable event package products. Requires Template Codes to be active."
    )

    @api.onchange('use_template_codes')
    def _onchange_use_template_codes_packages(self):
        """Disable event packages if template codes are disabled."""
        if not self.use_template_codes:
            self.use_event_packages = False

    @api.constrains('use_event_packages', 'use_template_codes')
    def _check_event_packages_requires_template_codes(self):
        """Ensure event packages can only be enabled if template codes are active."""
        for website in self:
            if website.use_event_packages and not website.use_template_codes:
                raise ValidationError(
                    "Event Packages require Template Codes to be enabled first."
                )
