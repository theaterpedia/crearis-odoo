# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Website-level setting (primary)
    crearis_use_event_packages = fields.Boolean(
        string='Event Packages',
        related='website_id.use_event_packages',
        readonly=False,
        help="Enable event package products. Requires Template Codes to be active."
    )

    # Company-level setting (for backwards compatibility)
    use_event_packages = fields.Boolean(
        related='company_id.use_event_packages',
        readonly=False,
        string='Event Packages (Company)',
        help="Enable event package products at company level."
    )
