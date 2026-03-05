# -*- coding: utf-8 -*-
from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_open_installment_wizard(self):
        """Open the installment wizard for this invoice."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ratenzahlung',
            'res_model': 'sale.installment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_id': self.id,
                'active_model': 'account.move',
            },
        }
