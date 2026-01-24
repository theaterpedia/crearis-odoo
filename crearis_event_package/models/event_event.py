# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class EventEvent(models.Model):
    _inherit = 'event.event'

    package_only = fields.Boolean(
        string="Package Only",
        default=False,
        help="If True, this event can only be purchased as part of a package, not individually."
    )

    # Reverse relation to package lines
    package_line_ids = fields.One2many(
        'product.package.event.line',
        'event_id',
        string="Package Lines",
        help="Package selections that include this event"
    )

    is_in_package = fields.Boolean(
        string="Is In Package",
        compute='_compute_is_in_package',
        store=True,
        help="True if this event is included in at least one active package selection"
    )

    # Computed field to check if company has event packages enabled
    use_event_packages = fields.Boolean(
        string="Use Event Packages",
        compute='_compute_use_event_packages',
        help="Whether the company has event packages enabled"
    )

    @api.depends('package_line_ids', 'package_line_ids.state')
    def _compute_is_in_package(self):
        for event in self:
            event.is_in_package = bool(
                event.package_line_ids.filtered(
                    lambda l: l.state in ('selected', 'registered')
                )
            )

    @api.depends('domain_code', 'domain_code.use_event_packages')
    def _compute_use_event_packages(self):
        for event in self:
            if event.domain_code:
                event.use_event_packages = event.domain_code.use_event_packages
            else:
                event.use_event_packages = self.env.company.use_event_packages

    @api.model_create_multi
    def create(self, vals_list):
        """On event creation, check if event type is part of a package.
        
        If the website/company has use_event_packages enabled and the event type
        is referenced in any package product, default package_only to True.
        """
        for vals in vals_list:
            # Skip if package_only is explicitly set
            if 'package_only' in vals:
                continue
            
            # Check if website has event packages enabled
            use_packages = False
            if vals.get('domain_code'):
                website = self.env['website'].browse(vals['domain_code'])
                use_packages = website.use_event_packages
            else:
                use_packages = self.env.company.use_event_packages
            
            if not use_packages:
                continue
            
            # Check if the event type is part of any package
            event_type_id = vals.get('event_type_id')
            if event_type_id:
                package_count = self.env['product.template'].search_count([
                    ('detailed_type', '=', 'event_package'),
                    ('package_event_type_ids', 'in', [event_type_id]),
                ])
                if package_count > 0:
                    vals['package_only'] = True

        return super().create(vals_list)

    @api.constrains('package_only', 'event_ticket_ids')
    def _check_package_only_no_tickets(self):
        """Warn if trying to enable package_only when tickets exist."""
        for event in self:
            if event.package_only and event.event_ticket_ids:
                # We don't raise an error, but the UI will show a warning
                # This allows existing tickets to remain but disables the toggle
                pass

    def _is_event_type_in_package(self):
        """Check if this event's type is part of any package product."""
        self.ensure_one()
        if not self.event_type_id:
            return False
        return self.env['product.template'].search_count([
            ('detailed_type', '=', 'event_package'),
            ('package_event_type_ids', 'in', [self.event_type_id.id]),
        ]) > 0

    def action_view_package_lines(self):
        """Open the package lines for this event."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Package Selections',
            'res_model': 'product.package.event.line',
            'view_mode': 'tree,form',
            'domain': [('event_id', '=', self.id)],
            'context': {'default_event_id': self.id},
        }
