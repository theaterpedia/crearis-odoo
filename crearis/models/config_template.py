# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia E.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models, fields

class ConfigTemplates(models.Model):
    _name = "crearis.config.template"
    _description = "Config-Templates"
    _order = "type, sequence"

    sequence = fields.Integer(default=10, help='Define the order in which the config-entries will be listed')    
    name = fields.Char('Config-Code', required=True, translate=False, help="Code-Name of the Config-Entry.", default='')
    description = fields.Char('Description', translate=True, help="Short-Description of the space.", default='')
    json_config = fields.Text('Config-Entry', translate=False, help="Settings (Json or other).", default='{}')
    html_config = fields.Html('Config-Entry', sanitize=False, help="Settings Html-Logic.", default='{}')
    type = fields.Selection([("json.schedule", "schedule"),("test.props", "test comp props")], default="json.schedule", string="Config-Type")
    is_default = fields.Boolean('is default-value', default=False)

    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        required=True,
        help="Company that owns this config",
        index=True,
    )
