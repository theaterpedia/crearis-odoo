# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import uuid
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Crearis-Website-Config
    domain_code = fields.Char(
        'Domain Code', related='website_id.domain_code', readonly=False,
        required=True
    )
    # DomainCode <-> Users relation (using keyword args)
    domain_exec = fields.Many2many(
        comodel_name="res.users",
        relation="crearis_settings_domain_exec",
        column1="domain_id",
        column2="user_id",
        string="Domain-Managers", 
        readonly=False, 
        related='website_id.domain_exec')

    domain_team = fields.Many2many(
        comodel_name="res.users",
        relation="crearis_settings_domain_team",
        column1="domain_id",
        column2="user_id",
        string="Domain-Team", 
        readonly=False, 
        related='website_id.domain_team')

    domain_user = fields.Many2many(
        comodel_name="res.users",
        relation="crearis_settings_domain_user",
        column1="domain_id",
        column2="user_id",
        string="Domain-Users", 
        readonly=False, 
        related='website_id.domain_user')                

