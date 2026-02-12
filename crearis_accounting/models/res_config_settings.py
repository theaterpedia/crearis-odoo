# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    installment_rate = fields.Float(
        related='company_id.installment_rate',
        readonly=False,
        string='Default Installment Rate',
    )

    simple_invoicing = fields.Boolean(
        related='company_id.simple_invoicing',
        readonly=False,
        string='Simple Invoicing',
    )
