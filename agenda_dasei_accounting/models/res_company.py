# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    installment_rate = fields.Float(
        string='Default Installment Rate',
        default=220.0,
        help='Default monthly installment amount for course invoicing (EUR). '
             'Used as pre-filled value in the installment wizard.',
    )
