# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    installment_rate = fields.Float(
        string='Default Installment Rate',
        default=220.0,
        help='Default monthly installment amount for course invoicing (EUR). '
             'Used as pre-filled value in the installment wizard.',
    )

    simple_invoicing = fields.Boolean(
        string='Simple Invoicing',
        default=False,
        help='Enable minimal invoicing without a full chart of accounts. '
             'Creates a receivable account, income account, suspense account, '
             'and a sale journal so this company can send invoices.',
    )

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------

    def write(self, vals):
        res = super().write(vals)
        if vals.get('simple_invoicing'):
            for company in self:
                if not company.chart_template_id:
                    company._setup_simple_invoicing()
        return res

    # ------------------------------------------------------------------
    # Simple-invoicing provisioning
    # ------------------------------------------------------------------

    def _setup_simple_invoicing(self):
        """Provision the minimum accounting records so this company can
        create, post, and send invoices — without a chart of accounts.

        Creates:
        - 3 accounts  (REC / INC / SUS)
        - 1 sale journal
        - ir.property defaults for receivable / payable
        - company-level suspense account
        """
        self.ensure_one()
        _logger.info(
            "Setting up simple invoicing for company %s (id=%d)",
            self.name, self.id,
        )

        Account = self.env['account.account'].sudo()
        Journal = self.env['account.journal'].sudo()

        # --- 1. Receivable account ------------------------------------------
        acc_rec = Account.search([
            ('company_id', '=', self.id),
            ('account_type', '=', 'asset_receivable'),
        ], limit=1)
        if not acc_rec:
            acc_rec = Account.create({
                'code': 'REC',
                'name': 'Forderungen',
                'account_type': 'asset_receivable',
                'reconcile': True,
                'company_id': self.id,
            })
            _logger.info("Created receivable account REC for %s", self.name)

        # --- 2. Income account -----------------------------------------------
        acc_inc = Account.search([
            ('company_id', '=', self.id),
            ('account_type', '=', 'income'),
        ], limit=1)
        if not acc_inc:
            acc_inc = Account.create({
                'code': 'INC',
                'name': 'Erlöse',
                'account_type': 'income',
                'reconcile': False,
                'company_id': self.id,
            })
            _logger.info("Created income account INC for %s", self.name)

        # --- 3. Suspense account ---------------------------------------------
        acc_sus = Account.search([
            ('company_id', '=', self.id),
            ('code', '=', 'SUS'),
        ], limit=1)
        if not acc_sus:
            acc_sus = Account.create({
                'code': 'SUS',
                'name': 'Abgrenzungskonto',
                'account_type': 'asset_current',
                'reconcile': False,
                'company_id': self.id,
            })
            _logger.info("Created suspense account SUS for %s", self.name)

        # --- 4. Sale journal -------------------------------------------------
        journal = Journal.search([
            ('company_id', '=', self.id),
            ('type', '=', 'sale'),
        ], limit=1)
        if not journal:
            journal = Journal.create({
                'name': 'Kundenrechnungen',
                'code': 'INV',
                'type': 'sale',
                'company_id': self.id,
                'default_account_id': acc_inc.id,
            })
            _logger.info("Created sale journal INV for %s", self.name)

        # --- 5. Company-level config -----------------------------------------
        self.sudo().write({
            'account_journal_suspense_account_id': acc_sus.id,
            'expects_chart_of_accounts': False,
        })

        # --- 6. ir.property defaults (receivable / payable) ------------------
        IrProperty = self.env['ir.property'].sudo()
        field_rec = self.env['ir.model.fields']._get(
            'res.partner', 'property_account_receivable_id',
        )
        field_pay = self.env['ir.model.fields']._get(
            'res.partner', 'property_account_payable_id',
        )
        for field_obj, account in [
            (field_rec, acc_rec),
            (field_pay, acc_rec),  # reuse receivable — no vendor bills
        ]:
            if not field_obj:
                continue
            existing = IrProperty.search([
                ('fields_id', '=', field_obj.id),
                ('company_id', '=', self.id),
                ('res_id', '=', False),
            ], limit=1)
            if not existing:
                IrProperty.create({
                    'name': field_obj.name,
                    'fields_id': field_obj.id,
                    'company_id': self.id,
                    'type': 'many2one',
                    'value_reference': f'account.account,{account.id}',
                    'res_id': False,
                })
                _logger.info(
                    "Created ir.property %s → %s for %s",
                    field_obj.name, account.code, self.name,
                )

        # --- 7. Set income account on default product category ---------------
        default_categ = self.env.ref(
            'product.product_category_all', raise_if_not_found=False,
        )
        if default_categ:
            default_categ.with_company(self).property_account_income_categ_id = acc_inc
            _logger.info(
                "Set income account %s on default product category for %s",
                acc_inc.code, self.name,
            )

        _logger.info(
            "Simple invoicing setup complete for %s (id=%d)",
            self.name, self.id,
        )
