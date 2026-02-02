# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from datetime import timedelta
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
    
    # Cancellation period tracking (from Ida's journey)
    first_attendance_date = fields.Date(
        string="First Attendance",
        compute='_compute_cancellation_status',
        store=True,
        help="Date of first event attendance (e.g., A0 Basistag)"
    )
    cancellation_deadline = fields.Date(
        string="Cancellation Deadline",
        compute='_compute_cancellation_status',
        store=True,
        help="Last day to cancel with reduced fee"
    )
    is_cancellation_period_passed = fields.Boolean(
        string="Cancellation Period Passed",
        compute='_compute_cancellation_status',
        store=True,
        help="True if cancellation deadline has passed"
    )
    cancellation_state = fields.Selection([
        ('not_started', 'Not Started'),
        ('in_period', 'In Cancellation Period'),
        ('passed', 'Period Passed'),
    ], string="Cancellation State",
       compute='_compute_cancellation_status',
       store=True)
    
    # Completion tracking (from Jolanda's journey)
    is_completed = fields.Boolean(
        string="Completed",
        compute='_compute_completion_status',
        store=True,
        help="True if all package events are attended"
    )
    completion_date = fields.Date(
        string="Completion Date",
        compute='_compute_completion_status',
        store=True,
        help="Date when all events were attended"
    )
    
    # Activation milestone tracking
    activation_milestone_id = fields.Many2one(
        'agenda.line',
        string="Activation Milestone",
        ondelete='set null',
        help="Activation milestone for this package purchase"
    )
    completion_milestone_id = fields.Many2one(
        'agenda.line',
        string="Completion Milestone",
        ondelete='set null',
        help="Completion milestone for this package purchase"
    )

    @api.depends('product_id.detailed_type')
    def _compute_is_event_package(self):
        for line in self:
            line.is_event_package = line.product_id.detailed_type == 'event_package'
    
    @api.depends('package_event_line_ids.first_attendance_date', 
                 'package_event_line_ids.is_first_event',
                 'product_id.cancellation_period_days')
    def _compute_cancellation_status(self):
        today = fields.Date.today()
        for line in self:
            # Find first attendance from first event
            first_event = line.package_event_line_ids.filtered(
                lambda l: l.is_first_event and l.first_attendance_date
            )
            
            if first_event:
                line.first_attendance_date = first_event.first_attendance_date
                cancellation_days = line.product_id.cancellation_period_days or 10
                line.cancellation_deadline = first_event.first_attendance_date + timedelta(days=cancellation_days)
                line.is_cancellation_period_passed = today > line.cancellation_deadline
                line.cancellation_state = 'passed' if line.is_cancellation_period_passed else 'in_period'
            else:
                line.first_attendance_date = False
                line.cancellation_deadline = False
                line.is_cancellation_period_passed = False
                line.cancellation_state = 'not_started'
    
    @api.depends('package_event_line_ids.state')
    def _compute_completion_status(self):
        """Check if all package events are attended (from Jolanda's journey)."""
        for line in self:
            package_lines = line.package_event_line_ids.filtered(
                lambda l: l.state != 'cancelled'
            )
            if not package_lines:
                line.is_completed = False
                line.completion_date = False
                continue
            
            all_attended = all(pl.state == 'attended' for pl in package_lines)
            if all_attended:
                line.is_completed = True
                # Use the latest attendance date
                attendance_dates = package_lines.mapped('first_attendance_date')
                line.completion_date = max(d for d in attendance_dates if d) if any(attendance_dates) else False
            else:
                line.is_completed = False
                line.completion_date = False

    @api.model_create_multi
    def create(self, vals_list):
        """Create package event lines when adding an event package product."""
        lines = super().create(vals_list)
        for line in lines:
            if line.product_id.detailed_type == 'event_package':
                line._create_package_event_lines()
                line._create_activation_milestone()
        return lines
    
    def _create_activation_milestone(self):
        """Create activation milestone for module start (from Jolanda's journey).
        
        Example: Module B activation - triggered 14 days before first session.
        """
        self.ensure_one()
        product = self.product_id.product_tmpl_id
        
        if not product.activation_days_before:
            return  # No activation milestone configured
        
        # Get first event date from package
        first_event_line = self.package_event_line_ids.filtered(
            lambda l: l.is_first_event and l.event_id and l.event_id.date_begin
        )
        if not first_event_line:
            return  # No event selected yet
        
        first_event = first_event_line.event_id
        activation_date = first_event.date_begin.date() - timedelta(days=product.activation_days_before)
        
        agenda_line = self.env['agenda.line'].create({
            'type': 'milestone',
            'milestone_key': 'activation',
            'provider_type': 'product',
            'product_id': product.id,
            'partner_id': self.order_id.partner_id.id,
            'sale_order_line_id': self.id,
            'event_id': first_event.id,  # Link to first event
            'date': activation_date,
            'gate_state': 'pending',
            'source': 'template',
            'locked_edits': True,
            'milestone_days_before': product.activation_days_before,
        })
        
        self.activation_milestone_id = agenda_line.id
        return agenda_line
    
    def _create_completion_milestone(self):
        """Create completion milestone when all events attended (from Jolanda's journey).
        
        Example: Module A completion - triggered 7 days after last session.
        """
        self.ensure_one()
        product = self.product_id.product_tmpl_id
        
        if not product.use_completion_milestone:
            return  # No completion milestone configured
        
        if self.completion_milestone_id:
            return  # Already created
        
        if not self.is_completed or not self.completion_date:
            return  # Not yet completed
        
        completion_milestone_date = self.completion_date + timedelta(
            days=product.completion_days_after or 7
        )
        
        # Find last event for linking
        last_event_line = self.package_event_line_ids.filtered(
            lambda l: l.state == 'attended' and l.first_attendance_date
        ).sorted(key=lambda l: l.first_attendance_date, reverse=True)[:1]
        
        last_event = last_event_line.event_id if last_event_line else False
        
        agenda_line = self.env['agenda.line'].create({
            'type': 'milestone',
            'milestone_key': 'completion',
            'provider_type': 'product',
            'product_id': product.id,
            'partner_id': self.order_id.partner_id.id,
            'sale_order_line_id': self.id,
            'event_id': last_event.id if last_event else False,
            'date': completion_milestone_date,
            'gate_state': 'ready',  # Immediately ready for certificate
            'source': 'template',
            'locked_edits': True,
            'milestone_days_before': 0,
        })
        
        self.completion_milestone_id = agenda_line.id
        return agenda_line
    
    def _check_and_create_completion_milestone(self):
        """Hook called when completion status changes."""
        for line in self.filtered(lambda l: l.is_completed and not l.completion_milestone_id):
            line._create_completion_milestone()
    
    def action_create_consulting_meeting(self):
        """Create a consulting meeting agenda.line (from Ida's journey: Beratungsgespräch).
        
        Opens a wizard to schedule the meeting date and responsible user.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Schedule Consulting Meeting',
            'res_model': 'agenda.line',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_type': 'meeting',
                'default_mode': 'online',
                'default_provider_type': 'product',
                'default_product_id': self.product_id.product_tmpl_id.id,
                'default_partner_id': self.order_id.partner_id.id,
                'default_sale_order_line_id': self.id,
                'default_source': 'manual',
            },
        }

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
