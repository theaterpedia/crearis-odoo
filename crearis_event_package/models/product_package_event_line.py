# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from datetime import timedelta
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
        ('attended', 'Attended'),  # First attendance confirmed
        ('cancelled', 'Cancelled'),
    ], string="State", default='pending', required=True, index=True)

    company_id = fields.Many2one(
        'res.company',
        string="Company",
        related='sale_order_line_id.company_id',
        store=True
    )
    
    # First attendance tracking (triggers cancellation period)
    first_attendance_date = fields.Date(
        string="First Attendance Date",
        readonly=True,
        help="Date of first attendance (e.g., A0 Basistag). "
             "Triggers cancellation period calculation."
    )
    is_first_event = fields.Boolean(
        string="Is First Event",
        compute='_compute_is_first_event',
        store=True,
        help="True if this is the first event in the package sequence"
    )
    
    # Link to agenda.line (for product milestones)
    agenda_line_id = fields.Many2one(
        'agenda.line',
        string="Agenda Line",
        ondelete='set null',
        help="Related agenda line for this package event"
    )
    
    @api.depends('sequence', 'sale_order_line_id.package_event_line_ids.sequence')
    def _compute_is_first_event(self):
        for line in self:
            siblings = line.sale_order_line_id.package_event_line_ids
            if siblings:
                min_seq = min(siblings.mapped('sequence'))
                line.is_first_event = line.sequence == min_seq
            else:
                line.is_first_event = False

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

    def action_mark_attended(self):
        """Mark first attendance - triggers cancellation period.
        
        From Ida's journey: After A0 Basistag, 10-day cancellation window starts.
        From Jolanda's journey: When all events attended, completion milestone triggers.
        """
        today = fields.Date.today()
        for line in self.filtered(lambda l: l.state == 'registered' and not l.first_attendance_date):
            line.write({
                'first_attendance_date': today,
                'state': 'attended',
            })
            
            # If this is the first event (A0), create cancellation milestone
            if line.is_first_event:
                line._create_cancellation_milestone()
            
            # Check if all events are now attended → completion milestone
            line.sale_order_line_id._check_and_create_completion_milestone()
        
        return True
    
    def _create_cancellation_milestone(self):
        """Create cancellation period milestone for the customer.
        
        Example from Ida's journey:
        - Ida attends A0 Basistag on 12. September
        - Cancellation deadline = 24. September (10 days later)
        - System creates agenda.line with type='milestone', milestone_key='cancellation'
        """
        self.ensure_one()
        
        product = self.sale_order_line_id.product_id.product_tmpl_id
        cancellation_days = product.cancellation_period_days or 10
        
        # Calculate deadline date
        deadline_date = self.first_attendance_date + timedelta(days=cancellation_days)
        
        # Create the milestone agenda.line
        agenda_line = self.env['agenda.line'].create({
            'type': 'milestone',
            'milestone_key': 'cancellation',
            'provider_type': 'product',
            'product_id': product.id,
            'partner_id': self.partner_id.id,
            'sale_order_line_id': self.sale_order_line_id.id,
            'date': deadline_date,
            'gate_state': 'pending',
            'source': 'template',
            'locked_edits': True,
            'milestone_days_before': 0,  # Deadline is the date itself
            'notes': f"Stornierungsfrist: {cancellation_days} Tage nach {self.event_type_id.name or 'erster Teilnahme'}",
        })
        
        self.agenda_line_id = agenda_line.id
        
        return agenda_line
    
    def _get_cancellation_deadline(self):
        """Get cancellation deadline for this package purchase.
        
        Returns: Date or False if no first attendance yet
        """
        self.ensure_one()
        first_line = self.sale_order_line_id.package_event_line_ids.filtered(
            lambda l: l.is_first_event and l.first_attendance_date
        )
        if not first_line:
            return False
        
        product = self.sale_order_line_id.product_id.product_tmpl_id
        cancellation_days = product.cancellation_period_days or 10
        return first_line.first_attendance_date + timedelta(days=cancellation_days)
