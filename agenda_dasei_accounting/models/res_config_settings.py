# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    installment_rate = fields.Float(
        related='company_id.installment_rate',
        readonly=False,
        string='Default Installment Rate',
    )
