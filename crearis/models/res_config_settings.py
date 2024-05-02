# -*- coding: utf-8 -*-
# Copyright 2024 Theaterpedia E.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import uuid
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    _order = 'domain_code'

    # Crearis-Website-Config
    domain_code = fields.Char(
        'Domain Code', related='website_id.domain_code', readonly=False,
        help="Subdomain on theaterpedia.org / unique key-prefix for data-keys"
    )

    crearis_use_channels = fields.Boolean('Use Channels', related='website_id.use_channels', readonly=False, default=False)
    crearis_use_templates = fields.Boolean('Use Event Templates', related='website_id.use_templates', readonly=False, default=False)
    crearis_use_tracks = fields.Boolean('Use Tracks', related='website_id.use_tracks', readonly=False, default=False)
    crearis_use_products = fields.Boolean('Use Products', related='website_id.use_products', readonly=False, default=False)
    crearis_use_overline = fields.Boolean('Use Overline', related='website_id.use_overline', readonly=False, default=False)
    crearis_use_teasertext = fields.Boolean('Use Teasertext', related='website_id.use_teasertext', readonly=False, default=False)
    is_company_domain = fields.Boolean('is Company Website', related='website_id.is_company_domain', readonly=True)

