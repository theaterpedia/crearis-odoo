from odoo import models, fields, api
# from json_field import JsonField

class Company(models.Model):
    _inherit = "res.company"

    domain_code = fields.Many2one(
        'website', string='Domain Code', 
        required=False, domain="[('domain_code','not like','X_EMPTY')]")
