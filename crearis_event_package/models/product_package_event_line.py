# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class ProductPackageEventLine(models.Model):
    """Links a sold product package to selected events.
    
    This model provides complete traceability of:
    - Which events were selected for a package purchase
    - Which sale order line the selection belongs to
    - The registration created for the customer
    - The state of the selection (pending, selected, registered)
    """
    _name = 'product.package.event.line'
    _description = 'Package Event Selection'
    _order = 'sale_order_line_id, sequence, id'

    sequence = fields.Integer(default=10)
    sale_order_line_id = fields.Many2one(
        'sale.order.line',
        string="Sale Order Line",
        required=True,
        ondelete='cascade',
        index=True
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string="Sale Order",
        related='sale_order_line_id.order_id',
        store=True,
        index=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string="Customer",
        related='sale_order_line_id.order_id.partner_id',
        store=True,
        index=True
    )
    product_id = fields.Many2one(
        'product.product',
        string="Package Product",
        related='sale_order_line_id.product_id',
        store=True
    )
    
    # Event Type (from package configuration)
    event_type_id = fields.Many2one(
        'event.type',
        string="Event Type",
        required=True,
        help="The event type slot to be filled from the package"
    )
    
    # Selected Event
    event_id = fields.Many2one(
        'event.event',
        string="Selected Event",
        domain="[('event_type_id', '=', event_type_id)]",
        help="The actual event selected by the customer"
    )
    
    # Registration created
    registration_id = fields.Many2one(
        'event.registration',
        string="Registration",
        readonly=True,
        help="The event registration created for this selection"
    )
    
    state = fields.Selection([
        ('pending', 'Pending Selection'),
        ('selected', 'Event Selected'),
        ('registered', 'Registered'),
        ('cancelled', 'Cancelled'),
    ], string="State", default='pending', required=True, index=True)

    company_id = fields.Many2one(
        'res.company',
        string="Company",
        related='sale_order_line_id.company_id',
        store=True
    )

    def name_get(self):
        result = []
        for line in self:
            name = f"{line.event_type_id.name or 'N/A'}"
            if line.event_id:
                name += f" → {line.event_id.name}"
            result.append((line.id, name))
        return result

    def action_create_registration(self):
        """Create event registration for selected events."""
        Registration = self.env['event.registration']
        for line in self.filtered(lambda l: l.state == 'selected' and l.event_id and not l.registration_id):
            registration = Registration.create({
                'event_id': line.event_id.id,
                'partner_id': line.partner_id.id,
                'sale_order_line_id': line.sale_order_line_id.id,
                'sale_order_id': line.sale_order_id.id,
            })
            line.write({
                'registration_id': registration.id,
                'state': 'registered',
            })
        return True

    def action_cancel(self):
        """Cancel the package line and associated registration."""
        for line in self:
            if line.registration_id:
                line.registration_id.action_cancel()
            line.state = 'cancelled'
        return True
