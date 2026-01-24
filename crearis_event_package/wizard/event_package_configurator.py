# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EventPackageConfigurator(models.TransientModel):
    """Wizard for selecting events for a package purchase."""
    _name = 'event.package.configurator'
    _description = 'Event Package Configurator'

    sale_order_line_id = fields.Many2one(
        'sale.order.line',
        string="Sale Order Line",
        required=True,
        ondelete='cascade'
    )
    product_id = fields.Many2one(
        'product.product',
        string="Package Product",
        related='sale_order_line_id.product_id'
    )
    product_tmpl_id = fields.Many2one(
        'product.template',
        string="Package Template",
        related='sale_order_line_id.product_id.product_tmpl_id'
    )
    partner_id = fields.Many2one(
        'res.partner',
        string="Customer",
        related='sale_order_line_id.order_id.partner_id'
    )

    line_ids = fields.One2many(
        'event.package.configurator.line',
        'wizard_id',
        string="Event Selections"
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'sale_order_line_id' in res:
            sol = self.env['sale.order.line'].browse(res['sale_order_line_id'])
            res['line_ids'] = [(0, 0, {
                'package_event_line_id': pel.id,
                'event_type_id': pel.event_type_id.id,
                'event_id': pel.event_id.id,
            }) for pel in sol.package_event_line_ids]
        return res

    def _get_available_events_domain(self, event_type_id):
        """Build domain to filter available events for a package slot."""
        self.ensure_one()
        product_tmpl = self.product_tmpl_id
        
        domain = [
            ('event_type_id', '=', event_type_id),
        ]
        
        # Filter by package date range
        if product_tmpl.package_date_start:
            domain.append(('date_begin', '>=', product_tmpl.package_date_start))
        if product_tmpl.package_date_end:
            domain.append(('date_end', '<=', product_tmpl.package_date_end))
        
        return domain

    def action_confirm(self):
        """Save event selections to package lines."""
        self.ensure_one()
        
        for wiz_line in self.line_ids:
            if wiz_line.event_id:
                wiz_line.package_event_line_id.write({
                    'event_id': wiz_line.event_id.id,
                    'state': 'selected',
                })
        
        return {'type': 'ir.actions.act_window_close'}

    def action_confirm_and_register(self):
        """Save selections and create registrations."""
        self.action_confirm()
        
        # Create registrations for all selected events
        self.sale_order_line_id.package_event_line_ids.filtered(
            lambda l: l.state == 'selected'
        ).action_create_registration()
        
        return {'type': 'ir.actions.act_window_close'}


class EventPackageConfiguratorLine(models.TransientModel):
    """Line in the package configurator wizard."""
    _name = 'event.package.configurator.line'
    _description = 'Event Package Configurator Line'

    wizard_id = fields.Many2one(
        'event.package.configurator',
        string="Wizard",
        required=True,
        ondelete='cascade'
    )
    package_event_line_id = fields.Many2one(
        'product.package.event.line',
        string="Package Line",
        required=True
    )
    event_type_id = fields.Many2one(
        'event.type',
        string="Event Type",
        readonly=True
    )
    event_id = fields.Many2one(
        'event.event',
        string="Selected Event",
        domain="[('event_type_id', '=', event_type_id)]"
    )
    available_event_ids = fields.Many2many(
        'event.event',
        string="Available Events",
        compute='_compute_available_events'
    )

    @api.depends('event_type_id', 'wizard_id.product_tmpl_id')
    def _compute_available_events(self):
        for line in self:
            if line.wizard_id and line.event_type_id:
                domain = line.wizard_id._get_available_events_domain(line.event_type_id.id)
                line.available_event_ids = self.env['event.event'].search(domain)
            else:
                line.available_event_ids = self.env['event.event']
