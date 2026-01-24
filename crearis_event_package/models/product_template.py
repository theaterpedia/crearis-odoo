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

    @api.onchange('detailed_type')
    def _onchange_type_event_package(self):
        if self.detailed_type == 'event_package':
            self.invoice_policy = 'order'

    def _detailed_type_mapping(self):
        type_mapping = super()._detailed_type_mapping()
        type_mapping['event_package'] = 'service'
        return type_mapping


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # Reverse relation to see which package lines reference this product
    package_line_ids = fields.One2many(
        'product.package.event.line',
        'product_id',
        string="Package Event Lines",
        help="Event selections made for this product in sales"
    )
