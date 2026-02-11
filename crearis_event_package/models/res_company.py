# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api


class Company(models.Model):
    _inherit = "res.company"

    use_event_packages = fields.Boolean(
        string='Event Packages',
        default=False,
        help="Enable event package products. Works best with Template Codes enabled."
    )

    @api.onchange('use_event_packages')
    def _onchange_use_event_packages(self):
        """Auto-enable template codes when event packages are enabled."""
        if self.use_event_packages and not self.use_template_codes:
            self.use_template_codes = True


class Website(models.Model):
    _inherit = 'website'

    use_event_packages = fields.Boolean(
        string='Event Packages',
        default=False,
        help="Enable event package products. Works best with Template Codes enabled."
    )

    @api.onchange('use_event_packages')
    def _onchange_use_event_packages(self):
        """Auto-enable template codes when event packages are enabled."""
        if self.use_event_packages and not self.use_template_codes:
            self.use_template_codes = True
