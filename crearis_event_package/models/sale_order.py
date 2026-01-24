# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    package_event_line_ids = fields.One2many(
        'product.package.event.line',
        'sale_order_id',
        string="Package Event Selections",
        help="Event selections for package products in this order"
    )

    package_event_count = fields.Integer(
        string="Package Events",
        compute='_compute_package_event_count'
    )

    @api.depends('package_event_line_ids')
    def _compute_package_event_count(self):
        for order in self:
            order.package_event_count = len(order.package_event_line_ids)

    def action_view_package_events(self):
        """Open the package event selections for this order."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Package Event Selections',
            'res_model': 'product.package.event.line',
            'view_mode': 'tree,form',
            'domain': [('sale_order_id', '=', self.id)],
            'context': {'default_sale_order_id': self.id},
        }


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    package_event_line_ids = fields.One2many(
        'product.package.event.line',
        'sale_order_line_id',
        string="Package Events",
        help="Event selections for this package line"
    )

    is_event_package = fields.Boolean(
        string="Is Event Package",
        compute='_compute_is_event_package'
    )

    @api.depends('product_id.detailed_type')
    def _compute_is_event_package(self):
        for line in self:
            line.is_event_package = line.product_id.detailed_type == 'event_package'

    @api.model_create_multi
    def create(self, vals_list):
        """Create package event lines when adding an event package product."""
        lines = super().create(vals_list)
        for line in lines:
            if line.product_id.detailed_type == 'event_package':
                line._create_package_event_lines()
        return lines

    def _create_package_event_lines(self):
        """Create pending event selections for each event type in the package."""
        self.ensure_one()
        if self.product_id.detailed_type != 'event_package':
            return

        PackageEventLine = self.env['product.package.event.line']
        product_tmpl = self.product_id.product_tmpl_id

        for sequence, event_type in enumerate(product_tmpl.package_event_type_ids, start=10):
            PackageEventLine.create({
                'sale_order_line_id': self.id,
                'event_type_id': event_type.id,
                'sequence': sequence,
                'state': 'pending',
            })

    def action_configure_package(self):
        """Open the package configurator wizard."""
        self.ensure_one()
        if not self.is_event_package:
            return

        return {
            'type': 'ir.actions.act_window',
            'name': 'Configure Event Package',
            'res_model': 'event.package.configurator',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_line_id': self.id,
            },
        }
