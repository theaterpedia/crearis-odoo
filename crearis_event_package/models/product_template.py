# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    detailed_type = fields.Selection(selection_add=[
        ('event_package', 'Event Package'),
    ], ondelete={'event_package': 'set service'})

    # Package configuration
    package_event_type_ids = fields.Many2many(
        'event.type',
        'product_template_event_type_rel',
        'product_tmpl_id', 'event_type_id',
        string="Included Event Types",
        help="Event types that must be selected when purchasing this package"
    )
    package_date_start = fields.Date(
        string="Package Start Date",
        help="Only events starting after this date will be available for selection"
    )
    package_date_end = fields.Date(
        string="Package End Date",
        help="Only events ending before this date will be available for selection"
    )
    package_edition_code = fields.Char(
        string="Edition Code",
        help="Edition identifier for this package (e.g., M18, M19)"
    )
    
    # Cancellation period (Stornierungsfrist) - from Ida's journey
    cancellation_period_days = fields.Integer(
        string="Cancellation Period (Days)",
        default=10,
        help="Days after first attendance during which customer can cancel. "
             "For DASEi Module A: 10 days after Basistag (A0)."
    )
    cancellation_fee = fields.Float(
        string="Cancellation Fee",
        digits='Product Price',
        help="Fee charged if customer cancels within the cancellation period"
    )
    
    # Activation milestone (from Jolanda's journey: Module B starts with activation)
    activation_days_before = fields.Integer(
        string="Activation Days Before",
        default=0,
        help="Days before first event to trigger activation milestone. "
             "0 = no activation milestone. E.g., 14 = notify 2 weeks before module starts."
    )
    
    # Completion milestone (from Jolanda's journey: each module ends with completion)
    use_completion_milestone = fields.Boolean(
        string="Completion Milestone",
        default=True,
        help="Create completion milestone when all events are attended"
    )
    completion_days_after = fields.Integer(
        string="Completion Days After",
        default=7,
        help="Days after last event to trigger completion milestone"
    )
    
    # Consulting/meeting requirement (from Ida/Jolanda: Beratungsgespräch)
    requires_consulting = fields.Boolean(
        string="Requires Consulting",
        default=False,
        help="Customer must complete a consulting meeting during this module"
    )

    @api.onchange('detailed_type')
    def _onchange_type_event_package(self):
        if self.detailed_type == 'event_package':
            self.invoice_policy = 'order'

    def _detailed_type_mapping(self):
        type_mapping = super()._detailed_type_mapping()
        type_mapping['event_package'] = 'service'
        return type_mapping

    def get_linked_event_type_ids(self):
        """Return event type IDs linked to this product.
        
        Used by QWeb templates to resolve product → events.
        This is the crearis_event_package implementation using package_event_type_ids.
        """
        self.ensure_one()
        if self.package_event_type_ids:
            return self.package_event_type_ids.ids
        return []


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # Reverse relation to see which package lines reference this product
    package_line_ids = fields.One2many(
        'product.package.event.line',
        'product_id',
        string="Package Event Lines",
        help="Event selections made for this product in sales"
    )
