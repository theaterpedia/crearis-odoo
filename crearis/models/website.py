# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import requests
from odoo import models, fields, api


class Website(models.Model):
    _inherit = 'website'

    domain_code = fields.Char('Domain-Code') 

    # DomainCode <-> Users relation (using keyword args)
    domain_exec = fields.Many2many(
        comodel_name="res.users",
        relation="crearis_domain_exec",
        column1="domain_id",
        column2="user_id",
        string="Domain-Managers")

    domain_team = fields.Many2many(
        comodel_name="res.users",
        relation="crearis_domain_team",
        column1="domain_id",
        column2="user_id",
        string="Domain-Team")

    domain_user = fields.Many2many(
        comodel_name="res.users",
        relation="crearis_domain_user",
        column1="domain_id",
        column2="user_id",
        string="Domain-Users")        

