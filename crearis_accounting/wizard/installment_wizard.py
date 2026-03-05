# -*- coding: utf-8 -*-
# Copyright 2026 crearis oHG
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


def _first_tuesday(year, month):
    """Return the date of the first Tuesday in the given month."""
    first_day = date(year, month, 1)
    offset = (1 - first_day.weekday()) % 7  # days until Tuesday
    return first_day.replace(day=1 + offset)


class InstallmentWizard(models.TransientModel):
    _name = 'sale.installment.wizard'
    _description = 'Installment Invoice Wizard'

    # ── context / source ─────────────────────────────────────────────
    sale_order_id = fields.Many2one(
        'sale.order', string='Sale Order',
        readonly=True, ondelete='cascade',
    )
    invoice_id = fields.Many2one(
        'account.move', string='Invoice',
        readonly=True, ondelete='cascade',
        domain=[('move_type', '=', 'out_invoice')],
    )
    source_type = fields.Selection([
        ('sale_order', 'Sale Order'),
        ('invoice', 'Invoice'),
    ], compute='_compute_source_type', store=True)

    currency_id = fields.Many2one(
        'res.currency', compute='_compute_source_fields',
    )
    partner_id = fields.Many2one(
        'res.partner', compute='_compute_source_fields',
    )
    company_id = fields.Many2one(
        'res.company', compute='_compute_source_fields',
    )

    # ── input parameters ─────────────────────────────────────────────
    full_amount = fields.Monetary(
        string='Total Amount',
        currency_field='currency_id',
        readonly=True,
        help='Total amount from the source document',
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
        help='Month of the first installment (due date = first Tuesday)',
    )
    installment_mode = fields.Selection([
        ('payment_term', 'One invoice with payment schedule'),
        ('multi_invoice', 'One invoice per installment'),
    ], string='Mode', required=True)

    # ── computed / preview ───────────────────────────────────────────
    num_installments = fields.Integer(
        string='Number of Installments',
        compute='_compute_preview', store=True,
    )
    last_rate_amount = fields.Monetary(
        string='Last Rate',
        currency_field='currency_id',
        compute='_compute_preview', store=True,
    )
    preview_html = fields.Html(
        string='Preview',
        compute='_compute_preview', store=True,
        sanitize=False,
    )
    crosses_year_boundary = fields.Boolean(
        compute='_compute_preview', store=True,
    )
    year_split_info = fields.Char(
        compute='_compute_preview', store=True,
        help='Info about year split if applicable',
    )

    # ── computed source ──────────────────────────────────────────────

    @api.depends('sale_order_id', 'invoice_id')
    def _compute_source_type(self):
        for wiz in self:
            if wiz.invoice_id:
                wiz.source_type = 'invoice'
            elif wiz.sale_order_id:
                wiz.source_type = 'sale_order'
            else:
                wiz.source_type = False

    @api.depends('sale_order_id', 'invoice_id')
    def _compute_source_fields(self):
        for wiz in self:
            if wiz.invoice_id:
                wiz.currency_id = wiz.invoice_id.currency_id
                wiz.partner_id = wiz.invoice_id.partner_id
                wiz.company_id = wiz.invoice_id.company_id
            elif wiz.sale_order_id:
                wiz.currency_id = wiz.sale_order_id.currency_id
                wiz.partner_id = wiz.sale_order_id.partner_id
                wiz.company_id = wiz.sale_order_id.company_id
            else:
                wiz.currency_id = False
                wiz.partner_id = False
                wiz.company_id = False

    # ── default values ───────────────────────────────────────────────

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')

        if active_model == 'sale.order' and active_id:
            order = self.env['sale.order'].browse(active_id)
            res['sale_order_id'] = order.id
            res['full_amount'] = order.amount_untaxed
            res['rate_amount'] = order.company_id.installment_rate or 220.0
            res['installment_mode'] = order.company_id.installment_mode or 'payment_term'
        elif active_model == 'account.move' and active_id:
            invoice = self.env['account.move'].browse(active_id)
            if invoice.move_type != 'out_invoice':
                raise UserError(_("Installments can only be created for customer invoices."))
            if invoice.state != 'draft':
                raise UserError(_("Invoice must be in draft state to create installments."))
            res['invoice_id'] = invoice.id
            res['full_amount'] = invoice.amount_untaxed
            res['rate_amount'] = invoice.company_id.installment_rate or 220.0
            # Invoice source only works with payment_term mode
            res['installment_mode'] = 'payment_term'
        else:
            return res

        # Default first_month: first day of next month
        today = fields.Date.context_today(self)
        if today.month == 12:
            res['first_month'] = date(today.year + 1, 1, 1)
        else:
            res['first_month'] = date(today.year, today.month + 1, 1)

        return res

    # ── computation ──────────────────────────────────────────────────

    def _build_schedule(self):
        """Build installment schedule as list of (nr, due_date, label, amount)."""
        self.ensure_one()
        if not self.rate_amount or self.rate_amount <= 0 or not self.first_month or not self.full_amount:
            return []

        total = self.full_amount
        rate = self.rate_amount

        full_count = int(total // rate)
        remainder = round(total - full_count * rate, 2)
        if remainder > 0:
            num = full_count + 1
        else:
            num = full_count
            remainder = rate

        rows = []
        y = self.first_month.year
        m = self.first_month.month

        for i in range(num):
            due = _first_tuesday(y, m)
            amt = rate if i < full_count else remainder
            label = self._line_label(i + 1, num)
            rows.append((i + 1, due, label, amt))
            # Advance month
            if m == 12:
                m = 1
                y += 1
            else:
                m += 1

        return rows

    @api.depends('full_amount', 'rate_amount', 'first_month', 'installment_mode')
    def _compute_preview(self):
        for wiz in self:
            wiz.crosses_year_boundary = False
            wiz.year_split_info = ''

            rows = wiz._build_schedule()
            if not rows:
                wiz.num_installments = 0
                wiz.last_rate_amount = 0
                wiz.preview_html = ''
                continue

            wiz.num_installments = len(rows)
            wiz.last_rate_amount = rows[-1][3]

            # Year boundary check
            start_year = rows[0][1].year
            last_year = rows[-1][1].year
            if last_year != start_year:
                wiz.crosses_year_boundary = True
                # Count per year for info
                y1_count = sum(1 for r in rows if r[1].year == start_year)
                y2_count = len(rows) - y1_count
                y1_amt = sum(r[3] for r in rows if r[1].year == start_year)
                y2_amt = sum(r[3] for r in rows if r[1].year != start_year)
                wiz.year_split_info = _(
                    "Year %(y1)s: %(n1)d installments (%(a1).2f EUR) | "
                    "Year %(y2)s: %(n2)d installments (%(a2).2f EUR)",
                    y1=start_year, n1=y1_count, a1=y1_amt,
                    y2=last_year, n2=y2_count, a2=y2_amt,
                )

            # Build HTML preview table
            locale_fmt = '%d.%m.%Y'
            html = [
                '<table class="table table-sm table-striped">',
                '<thead><tr>',
                '<th>#</th><th>Faellig</th><th>Bezeichnung</th><th class="text-end">Betrag</th>',
                '</tr></thead><tbody>',
            ]

            prev_year = None
            for nr, due, label, amt in rows:
                # Year separator
                if wiz.crosses_year_boundary and prev_year and due.year != prev_year:
                    html.append(
                        f'<tr class="table-warning"><td colspan="4" class="text-center fw-bold">'
                        f'-- {due.year} --</td></tr>'
                    )
                prev_year = due.year
                html.append(
                    f'<tr><td>{nr}</td>'
                    f'<td>{due.strftime(locale_fmt)}</td>'
                    f'<td>{label}</td>'
                    f'<td class="text-end">{amt:,.2f} EUR</td></tr>'
                )

            total = wiz.full_amount
            html.append('</tbody>')
            html.append(
                f'<tfoot><tr class="fw-bold"><td colspan="3">Gesamt</td>'
                f'<td class="text-end">{total:,.2f} EUR</td></tr></tfoot>'
            )
            html.append('</table>')
            wiz.preview_html = '\n'.join(html)

    # ── helpers ───────────────────────────────────────────────────────

    def _line_label(self, index, total):
        """Build invoice line description, e.g. 'Kursrate - Modul A 3/5'."""
        product_name = ''
        if self.sale_order_id and self.sale_order_id.order_line:
            product_name = self.sale_order_id.order_line[0].product_id.name or ''
        elif self.invoice_id and self.invoice_id.invoice_line_ids:
            for line in self.invoice_id.invoice_line_ids:
                if line.display_type == 'product' or not line.display_type:
                    product_name = line.name or ''
                    break

        # Shorten "Modul A: Einstiege in's Theaterspiel" -> "Modul A"
        if ':' in product_name:
            short = product_name.split(':')[0].strip()
        elif '\n' in product_name:
            short = product_name.split('\n')[0].strip()
        else:
            short = product_name[:30] if len(product_name) > 30 else product_name

        return f"Kursrate - {short} {index}/{total}"

    # ── main action ───────────────────────────────────────────────────

    def action_create_installments(self):
        """Create installments based on selected mode."""
        self.ensure_one()

        if not self.num_installments:
            raise UserError(_("No installments to create. Check amount and rate."))

        if self.installment_mode == 'payment_term':
            return self._create_payment_term_installments()
        else:
            return self._create_multi_invoice_installments()

    # ── payment_term mode ─────────────────────────────────────────────

    def _create_payment_term_installments(self):
        """Create payment term with installment schedule, apply to invoice(s).

        If year boundary is crossed, creates 2 invoices (one per year).
        """
        self.ensure_one()
        rows = self._build_schedule()

        if self.crosses_year_boundary:
            return self._create_year_split_invoices(rows)

        # Single invoice case
        if self.invoice_id:
            invoice = self.invoice_id
        elif self.sale_order_id:
            # Create invoice from SO
            invoice = self._create_invoice_from_so(self.sale_order_id, rows)
        else:
            raise UserError(_("No source document found."))

        # Create and apply payment term
        payment_term = self._create_payment_term(rows, invoice.company_id)
        invoice.write({'invoice_payment_term_id': payment_term.id})
        invoice._onchange_invoice_payment_term_id()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _create_year_split_invoices(self, rows):
        """Split schedule by year, create one invoice per year."""
        self.ensure_one()

        # Group rows by year
        by_year = {}
        for row in rows:
            year = row[1].year
            by_year.setdefault(year, []).append(row)

        created_invoices = self.env['account.move']

        for year, year_rows in sorted(by_year.items()):
            # Recalculate amounts for this year
            year_total = sum(r[3] for r in year_rows)

            # Create invoice for this year
            if self.source_type == 'invoice':
                # Clone the original invoice for each year
                invoice = self._clone_invoice_for_year(self.invoice_id, year_rows, year_total)
            else:
                invoice = self._create_invoice_from_so_for_year(
                    self.sale_order_id, year_rows, year_total, year
                )

            # Create payment term for this year's installments
            # Renumber rows for this year
            renumbered = [(i+1, r[1], r[2], r[3]) for i, r in enumerate(year_rows)]
            payment_term = self._create_payment_term(renumbered, invoice.company_id, year=year)
            invoice.write({'invoice_payment_term_id': payment_term.id})
            invoice._onchange_invoice_payment_term_id()

            created_invoices |= invoice

        # If we had a draft invoice source, we should delete/cancel it
        if self.invoice_id and len(created_invoices) > 1:
            self.invoice_id.button_cancel()
            self.invoice_id.unlink()

        if len(created_invoices) == 1:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'res_id': created_invoices.id,
                'view_mode': 'form',
                'target': 'current',
            }

        return {
            'type': 'ir.actions.act_window',
            'name': _('Installment Invoices'),
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', created_invoices.ids)],
            'target': 'current',
        }

    def _create_payment_term(self, rows, company, year=None):
        """Create a dynamic payment term with lines for each installment."""
        total = sum(r[3] for r in rows)
        name = f"Ratenzahlung {len(rows)}x ({rows[0][1].strftime('%m/%Y')})"
        if year:
            name = f"Ratenzahlung {len(rows)}x {year}"

        # Calculate days from first due date for each installment
        first_due = rows[0][1]
        lines = []

        for i, (nr, due, label, amt) in enumerate(rows):
            # Days from invoice date (which will be set to first due date)
            days = (due - first_due).days if i > 0 else 0
            is_last = (i == len(rows) - 1)

            lines.append((0, 0, {
                'value': 'balance' if is_last else 'percent',
                'value_amount': 0 if is_last else round(100 * amt / total, 4),
                'days': days,
                'months': 0,
            }))

        payment_term = self.env['account.payment.term'].create({
            'name': name,
            'company_id': company.id,
            'line_ids': lines,
        })

        return payment_term

    def _create_invoice_from_so(self, order, rows):
        """Create a single invoice from sale order with total amount."""
        order.ensure_one()
        invoices = order._create_invoices()
        if not invoices:
            raise UserError(_("Could not create invoice from sale order."))
        invoice = invoices[0]
        # Set invoice date to first installment due date
        invoice.write({'invoice_date': rows[0][1]})
        return invoice

    def _create_invoice_from_so_for_year(self, order, year_rows, year_total, year):
        """Create invoice for a specific year's installments from SO."""
        order.ensure_one()

        fiscal_pos = order.fiscal_position_id
        product = order.order_line[0].product_id if order.order_line else False
        account = False
        taxes = self.env['account.tax']

        if product:
            account = (product.with_company(order.company_id)
                       .categ_id.property_account_income_categ_id)
            taxes = product.taxes_id.filtered(
                lambda t: t.company_id == order.company_id
            )
            if fiscal_pos and taxes:
                taxes = fiscal_pos.map_tax(taxes)
            if fiscal_pos and account:
                account = fiscal_pos.map_account(account)

        # Build description from year_rows
        line_names = [r[2] for r in year_rows]
        description = f"Kursgebuehr {year} ({len(year_rows)} Raten)\n" + "\n".join(line_names)

        invoice_vals = {
            'move_type': 'out_invoice',
            'company_id': order.company_id.id,
            'partner_id': order.partner_id.id,
            'invoice_date': year_rows[0][1],
            'fiscal_position_id': fiscal_pos.id if fiscal_pos else False,
            'invoice_origin': order.name,
            'ref': f"{order.name} ({year})",
            'invoice_line_ids': [(0, 0, {
                'name': description,
                'quantity': 1,
                'price_unit': year_total,
                'account_id': account.id if account else False,
                'tax_ids': [(6, 0, taxes.ids)] if taxes else [],
                'sale_line_ids': [(6, 0, order.order_line[:1].ids)],
            })],
        }

        return self.env['account.move'].with_company(order.company_id).create(invoice_vals)

    def _clone_invoice_for_year(self, original, year_rows, year_total):
        """Clone invoice for a specific year, adjusting amounts."""
        year = year_rows[0][1].year

        # Copy basic fields
        new_invoice = original.copy({
            'invoice_date': year_rows[0][1],
            'ref': f"{original.ref or original.name} ({year})",
        })

        # Adjust line amounts proportionally
        original_total = original.amount_untaxed
        if original_total:
            ratio = year_total / original_total
            for line in new_invoice.invoice_line_ids.filtered(
                lambda l: l.display_type not in ('line_section', 'line_note')
            ):
                line.price_unit = line.price_unit * ratio

        return new_invoice

    # ── multi_invoice mode (existing behavior) ────────────────────────

    def _create_multi_invoice_installments(self):
        """Create separate invoices for each installment (original behavior)."""
        self.ensure_one()

        if self.source_type == 'invoice':
            raise UserError(_(
                "Multi-invoice mode only works from sale orders. "
                "Use 'Payment schedule' mode for existing invoices."
            ))

        if self.crosses_year_boundary:
            raise UserError(_(
                "Installment plan crosses a year boundary. "
                "In multi-invoice mode, please adjust the rate or start month "
                "so all installments fall within the same calendar year, "
                "or switch to 'Payment schedule' mode."
            ))

        order = self.sale_order_id
        rows = self._build_schedule()
        created_moves = self.env['account.move']

        for nr, due, label, amt in rows:
            fiscal_pos = order.fiscal_position_id
            product = order.order_line[0].product_id if order.order_line else False
            account = False
            taxes = self.env['account.tax']

            if product:
                account = (product.with_company(order.company_id)
                           .categ_id.property_account_income_categ_id)
                taxes = product.taxes_id.filtered(
                    lambda t: t.company_id == order.company_id
                )
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
                'ref': f"{order.name} Rate {nr}/{len(rows)}",
                'invoice_line_ids': [(0, 0, {
                    'name': label,
                    'quantity': 1,
                    'price_unit': amt,
                    'account_id': account.id if account else False,
                    'tax_ids': [(6, 0, taxes.ids)] if taxes else [],
                    'sale_line_ids': [(6, 0, order.order_line[:1].ids)],
                })],
            }

            move = self.env['account.move'].with_company(order.company_id).create(invoice_vals)
            created_moves |= move

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
