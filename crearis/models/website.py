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

    use_channels = fields.Boolean('Use Channels', related='company_id.use_channels', readonly=False, default=False)
    use_rooms = fields.Boolean('Use Rooms', related='company_id.use_rooms', readonly=False, default=False)
    use_company_templates = fields.Boolean('Use Company Templates', related='company_id.use_company_templates', readonly=False, default=False)
    use_tracks = fields.Boolean('Use Tracks', related='company_id.use_tracks', readonly=False, default=False)
    use_products = fields.Boolean('Use Products', related='company_id.use_products', readonly=False, default=False)
    use_overline = fields.Boolean('Use Overline', related='company_id.use_overline', readonly=False, default=False)
    use_teasertext = fields.Boolean('Use Teasertext', related='company_id.use_teasertext', readonly=False, default=False)    

    @api.depends("company_id.domain_code")
    def _compute_is_homedomain(self):
        for website in self:
            website.is_company_domain = website.company_id.domain_code.id == website.id

    is_company_domain = fields.Boolean(compute=_compute_is_homedomain)
