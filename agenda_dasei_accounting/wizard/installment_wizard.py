# -*- coding: utf-8 -*-
# Copyright 2026 crearis oHG
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import calendar
from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import UserError


def _first_tuesday(year, month):
    """Return the date of the first Tuesday in the given month."""
    # weekday(): Monday=0 … Sunday=6  →  Tuesday=1
    first_day = date(year, month, 1)
    offset = (1 - first_day.weekday()) % 7  # days until Tuesday
    return first_day.replace(day=1 + offset)


class InstallmentWizard(models.TransientModel):
    _name = 'sale.installment.wizard'
    _description = 'Installment Invoice Wizard'

    # ── context / source ─────────────────────────────────────────────
    sale_order_id = fields.Many2one(
        'sale.order', string='Sale Order',
        required=True, readonly=True, ondelete='cascade',
    )
    currency_id = fields.Many2one(
        related='sale_order_id.currency_id',
    )
    partner_id = fields.Many2one(
        related='sale_order_id.partner_id',
    )

    # ── input parameters ─────────────────────────────────────────────
    full_amount = fields.Monetary(
        string='Total Amount',
        currency_field='currency_id',
        readonly=True,
        help='Total amount from the sale order',
    )
    rate_amount = fields.Monetary(
        string='Monthly Rate',
        currency_field='currency_id',
        required=True,
        help='Monthly installment amount',
    )
    first_month = fields.Date(
        string='First Installment',
        required=True,
        help='Month of the first installment (day is ignored, due date = first Tuesday)',
    )

    # ── computed / preview ───────────────────────────────────────────
    num_installments = fields.Integer(
        string='Number of Installments',
        compute='_compute_preview', store=True,
    )
    last_rate_amount = fields.Monetary(
        string='Last Rate',
        currency_field='currency_id',
        compute='_compute_preview', store=True,
        help='Last installment amount (remainder)',
    )
    preview_html = fields.Html(
        string='Preview',
        compute='_compute_preview', store=True,
        sanitize=False,
    )
    crosses_year_boundary = fields.Boolean(
        compute='_compute_preview', store=True,
    )

    # ── default values ───────────────────────────────────────────────

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id:
            order = self.env['sale.order'].browse(active_id)
            res['sale_order_id'] = order.id
            res['full_amount'] = order.amount_untaxed
            res['rate_amount'] = order.company_id.installment_rate or 220.0
            # Default first_month: first day of next month
            today = fields.Date.context_today(self)
            if today.month == 12:
                res['first_month'] = date(today.year + 1, 1, 1)
            else:
                res['first_month'] = date(today.year, today.month + 1, 1)
        return res

    # ── computation ──────────────────────────────────────────────────

    @api.depends('full_amount', 'rate_amount', 'first_month')
    def _compute_preview(self):
        for wiz in self:
            wiz.crosses_year_boundary = False
            if not wiz.rate_amount or wiz.rate_amount <= 0 or not wiz.first_month or not wiz.full_amount:
                wiz.num_installments = 0
                wiz.last_rate_amount = 0
                wiz.preview_html = ''
                continue

            total = wiz.full_amount
            rate = wiz.rate_amount
            # How many full-rate installments, plus one remainder?
            full_count = int(total // rate)
            remainder = round(total - full_count * rate, 2)
            if remainder > 0:
                num = full_count + 1
            else:
                num = full_count
                remainder = rate  # last one is also a full rate

            wiz.num_installments = num
            wiz.last_rate_amount = remainder

            # Build schedule rows
            rows = []
            y = wiz.first_month.year
            m = wiz.first_month.month
            start_year = y

            for i in range(num):
                due = _first_tuesday(y, m)
                amt = rate if i < full_count else remainder
                label = self._line_label(wiz.sale_order_id, i + 1, num)
                rows.append((i + 1, due, label, amt))
                # Advance month
                if m == 12:
                    m = 1
                    y += 1
                else:
                    m += 1

            # Year boundary check
            last_year = rows[-1][1].year if rows else start_year
            if last_year != start_year:
                wiz.crosses_year_boundary = True

            # Build HTML preview table
            locale_fmt = '%d.%m.%Y'
            html = [
                '<table class="table table-sm table-striped">',
                '<thead><tr>',
                '<th>#</th><th>Fällig</th><th>Bezeichnung</th><th class="text-end">Betrag</th>',
                '</tr></thead><tbody>',
            ]
            for nr, due, label, amt in rows:
                html.append(
                    f'<tr><td>{nr}</td>'
                    f'<td>{due.strftime(locale_fmt)}</td>'
                    f'<td>{label}</td>'
                    f'<td class="text-end">{amt:,.2f} €</td></tr>'
                )
            html.append('</tbody>')
            html.append(
                f'<tfoot><tr class="fw-bold"><td colspan="3">Gesamt</td>'
                f'<td class="text-end">{total:,.2f} €</td></tr></tfoot>'
            )
            html.append('</table>')
            wiz.preview_html = '\n'.join(html)

    # ── helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _line_label(order, index, total):
        """Build invoice line description, e.g. 'Kursrate - Modul A 3/5'."""
        # Use first order line's product name as module label
        product_name = ''
        if order and order.order_line:
            for line in order.order_line:
                if line.product_id and line.product_id.detailed_type == 'event_package':
                    product_name = line.product_id.name or ''
                    break
            if not product_name:
                product_name = order.order_line[0].product_id.name or ''
        # Shorten "Modul A: Einstiege in's Theaterspiel" → "Modul A"
        short = product_name.split(':')[0].strip() if ':' in product_name else product_name
        return f"Kursrate - {short} {index}/{total}"

    # ── action ────────────────────────────────────────────────────────

    def action_create_installments(self):
        """Create draft invoices for each installment."""
        self.ensure_one()

        if self.crosses_year_boundary:
            raise UserError(_(
                "Installment plan crosses a year boundary "
                "(%(start)s → %(end)s). "
                "Please adjust the rate or start month so all installments "
                "fall within the same calendar year.",
                start=self.first_month.strftime('%Y'),
                end=(self.first_month.year + 1),
            ))

        if not self.num_installments:
            raise UserError(_("No installments to create. Check amount and rate."))

        order = self.sale_order_id
        move_obj = self.env['account.move'].with_company(order.company_id)
        created_moves = self.env['account.move']

        total = self.full_amount
        rate = self.rate_amount
        full_count = int(total // rate)
        remainder = round(total - full_count * rate, 2)
        num = self.num_installments

        y = self.first_month.year
        m = self.first_month.month

        for i in range(num):
            due = _first_tuesday(y, m)
            amt = rate if i < full_count else (remainder if remainder > 0 else rate)
            label = self._line_label(order, i + 1, num)

            # Determine fiscal position & tax
            fiscal_pos = order.fiscal_position_id
            product = order.order_line[0].product_id if order.order_line else False
            account = (
                product.with_company(order.company_id)
                .categ_id.property_account_income_categ_id
                if product else False
            )
            taxes = product.taxes_id.filtered(
                lambda t: t.company_id == order.company_id
            ) if product else self.env['account.tax']
            if fiscal_pos and taxes:
                taxes = fiscal_pos.map_tax(taxes)
            if fiscal_pos and account:
                account = fiscal_pos.map_account(account)

            invoice_vals = {
                'move_type': 'out_invoice',
                'company_id': order.company_id.id,
                'partner_id': order.partner_id.id,
                'invoice_date': due,
                'invoice_date_due': due,
                'fiscal_position_id': fiscal_pos.id if fiscal_pos else False,
                'invoice_origin': order.name,
                'ref': f"{order.name} Rate {i + 1}/{num}",
                'invoice_line_ids': [(0, 0, {
                    'name': label,
                    'quantity': 1,
                    'price_unit': amt,
                    'account_id': account.id if account else False,
                    'tax_ids': [(6, 0, taxes.ids)] if taxes else [],
                    'sale_line_ids': [(6, 0, order.order_line[:1].ids)],
                })],
            }

            move = move_obj.create(invoice_vals)
            created_moves |= move

            # Advance month
            if m == 12:
                m = 1
                y += 1
            else:
                m += 1

        # Return action to show created invoices
        if len(created_moves) == 1:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'res_id': created_moves.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return {
            'type': 'ir.actions.act_window',
            'name': _('Installment Invoices'),
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', created_moves.ids)],
            'target': 'current',
        }
