# -*- coding: utf-8 -*-
# Copyright 2026 theaterpedia.org / crearis.io
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AgendaLine(models.Model):
    """
    Unified agenda line model for events, posts, and products.
    
    Renamed from event.session.line (2026-02-02) to support:
    - Multiple providers (event, post, product)
    - Five line types (session, meeting, milestone, info, action)
    - Gate pattern for milestone tracking
    
    See: _meta/Whitepaper/architecture_agenda_lines.md
    """
    _name = 'agenda.line'
    _description = 'Agenda Line'
    _order = 'date, start, event_id'
    _rec_name = 'display_name'

    # =========================
    # Provider Relations (polymorphic)
    # =========================
    
    provider_type = fields.Selection([
        ('event', 'Event Session'),
        ('post', 'Info Post'),
        ('product', 'Product Milestone'),
    ], string='Provider Type', compute='_compute_provider_type', store=True)
    
    event_id = fields.Many2one(
        'event.event', 
        string='Event',
        ondelete='cascade', 
        index=True
    )
    post_id = fields.Many2one(
        'blog.post',
        string='Post',
        ondelete='cascade',
        index=True
    )
    product_id = fields.Many2one(
        'product.template',
        string='Product',
        ondelete='cascade',
        index=True
    )
    
    # Customer-specific fields (for product milestones like cancellation period)
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        ondelete='cascade',
        index=True,
        help="Customer for product-level milestones (e.g., cancellation period)"
    )
    sale_order_line_id = fields.Many2one(
        'sale.order.line',
        string='Sale Order Line',
        ondelete='cascade',
        index=True,
        help="Originating purchase for product milestones"
    )
    
    @api.depends('event_id', 'post_id', 'product_id')
    def _compute_provider_type(self):
        for rec in self:
            if rec.product_id:
                rec.provider_type = 'product'
            elif rec.post_id:
                rec.provider_type = 'post'
            else:
                rec.provider_type = 'event'
    
    @api.constrains('event_id', 'post_id', 'product_id')
    def _check_single_provider(self):
        """At least event_id should be set for event/post lines."""
        for rec in self:
            if rec.provider_type == 'product' and not rec.product_id:
                raise UserError(_("Product milestone lines require a product."))
            # Note: event_id can be set alongside post_id (post linked to event)

    # =========================
    # Line Type and Mode
    # =========================
    
    type = fields.Selection([
        ('session', 'Session'),
        ('meeting', 'Meeting'),
        ('milestone', 'Milestone'),
        ('info', 'Info'),
        ('action', 'Action'),
    ], string='Type', default='session', required=True, index=True)
    
    mode = fields.Selection([
        ('online', 'Online'),
        ('venue', 'Venue'),
        ('individual', 'Individual'),
        ('tbd', 'TBD'),
    ], string='Mode', default='venue', index=True,
       help="Session mode: online, at venue, individual work, or TBD")
    
    # =========================
    # Source Tracking
    # =========================
    
    source = fields.Selection([
        ('json', 'From Schedule JSON'),
        ('template', 'From Template'),
        ('manual', 'Manual Entry'),
        ('chatter', 'From Chatter'),
    ], string='Source', default='manual',
       help="How this line was created")
    
    locked_edits = fields.Boolean(
        default=False,
        help="True for json/template sources - prevents direct editing"
    )

    # =========================
    # Core Fields
    # =========================
    
    sequence = fields.Integer(default=10, help="Order within event")
    
    # Time information (keeping compatibility with old field names)
    day = fields.Char('Weekday', size=3, help="MON, TUE, WED, THU, FRI, SAT, SUN")
    date = fields.Date('Date', index=True)
    start = fields.Char('Start Time', size=5, help="HH:MM format")
    end = fields.Char('End Time', size=5, help="HH:MM format")
    duration_h = fields.Float('Duration (h)', digits=(4, 1))
    
    # Datetime fields for milestone calculations
    date_start = fields.Datetime('Start DateTime', index=True)
    date_end = fields.Datetime('End DateTime')
    
    # Location
    location_hint = fields.Char('Location Hint', help="Parsed location name")
    room = fields.Char('Room', help="Room identifier if specified")
    notes = fields.Text('Notes', help="Additional notes")
    
    # Teaching units
    teaching_units = fields.Float(
        'Teaching Units', 
        digits=(4, 1),
        help="UE (Unterrichtseinheiten) for certification tracking"
    )
    
    # =========================
    # Gate Pattern (Milestones Only)
    # =========================
    
    gate_state = fields.Selection([
        ('pending', 'Pending'),
        ('ready', 'Ready'),
        ('sent', 'Sent'),
        ('issue', 'Issue'),
    ], string='Gate State', default='pending',
       help="Milestone state: pending until date, ready for action, sent or issue")
    
    milestone_key = fields.Selection([
        ('activation', 'Activation'),
        ('deadline', 'Deadline'),
        ('completion', 'Completion'),
        ('cancellation', 'Cancellation Period'),  # Product-level: X days after first attendance
    ], string='Milestone Key',
       help="Which of the milestone types this is")
    
    milestone_days_before = fields.Integer(
        'Days Before Event',
        help="When this milestone triggers (days before event start)"
    )
    
    milestone_template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        help="Template to use when sending milestone communication"
    )
    
    @api.model
    def _cron_check_milestone_dates(self):
        """Daily cron: mark milestones as ready when date is reached."""
        today = fields.Date.today()
        pending_milestones = self.search([
            ('type', '=', 'milestone'),
            ('gate_state', '=', 'pending'),
            ('event_id', '!=', False),
        ])
        
        for line in pending_milestones:
            if not line.event_id.date_begin:
                continue
            event_date = line.event_id.date_begin.date()
            trigger_date = event_date - timedelta(days=line.milestone_days_before or 0)
            if today >= trigger_date:
                line.gate_state = 'ready'
                # Create activity for responsible user
                line._create_milestone_activity()
    
    def _create_milestone_activity(self):
        """Create an activity when milestone becomes ready."""
        self.ensure_one()
        if not self.event_id or not self.event_id.user_id:
            return
        
        # Get milestone label from company
        company = self.event_id.company_id or self.env.company
        label_field = f'milestone_label_{self.milestone_key}' if self.milestone_key else 'milestone_label_deadline'
        label = getattr(company, label_field, 'Milestone') if hasattr(company, label_field) else 'Milestone'
        
        self.env['mail.activity'].create({
            'res_model_id': self.env['ir.model']._get('event.event').id,
            'res_id': self.event_id.id,
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'summary': f'{label}: {self.event_id.name}',
            'user_id': self.event_id.user_id.id,
            'date_deadline': fields.Date.today(),
        })
    
    def action_confirm_and_send(self):
        """Instructor confirms milestone, sends communication."""
        for line in self:
            if line.gate_state != 'ready':
                continue
            
            # Send email if template configured
            if line.milestone_template_id and line.event_id:
                line.milestone_template_id.send_mail(line.event_id.id)
            
            # Mark as sent
            line.gate_state = 'sent'
    
    def action_flag_issue(self):
        """Flag milestone for review."""
        self.write({'gate_state': 'issue'})
    
    # =========================
    # Conference Integration
    # =========================
    
    conference_url = fields.Char(
        'Conference URL',
        help="Video conference meeting URL (MS Teams, Zoom, etc.)"
    )
    conference_id = fields.Char(
        'Conference ID',
        help="External meeting ID for API operations"
    )
    conference_provider = fields.Selection([
        ('msteams', 'Microsoft Teams'),
        ('zoom', 'Zoom'),
        ('jitsi', 'Jitsi Meet'),
        ('other', 'Other'),
    ], string='Provider', help="Conference provider for this session")
    
    # =========================
    # Related Fields (for filtering/reporting)
    # =========================
    
    event_name = fields.Char(
        related='event_id.name', 
        store=True, 
        string='Event Name'
    )
    company_id = fields.Many2one(
        related='event_id.company_id', 
        store=True, 
        index=True,
        string='Company'
    )
    event_date_begin = fields.Datetime(
        related='event_id.date_begin', 
        store=True,
        string='Event Start'
    )
    address_id = fields.Many2one(
        related='event_id.address_id', 
        store=True, 
        string='Venue'
    )
    event_type_id = fields.Many2one(
        related='event_id.event_type_id',
        store=True,
        string='Event Type'
    )
    user_id = fields.Many2one(
        related='event_id.user_id',
        store=True,
        string='Responsible'
    )
    
    # =========================
    # Computed Display
    # =========================
    
    display_name = fields.Char(
        compute='_compute_display_name', 
        store=True,
        string='Description'
    )
    
    @api.depends('event_id.name', 'product_id.name', 'partner_id.name', 'date', 'start', 'type', 'mode', 'milestone_key')
    def _compute_display_name(self):
        for rec in self:
            if rec.type == 'milestone':
                icon = '🎯'
            elif rec.type == 'info':
                icon = 'ℹ️'
            elif rec.type == 'action':
                icon = '✅'
            elif rec.mode == 'online':
                icon = '🌐'
            else:
                icon = '📍'
            
            date_str = rec.date.strftime('%Y-%m-%d') if rec.date else ''
            
            # Product milestone (e.g., Ida's cancellation period)
            if rec.provider_type == 'product' and rec.product_id:
                name = rec.product_id.name or ''
                if rec.milestone_key == 'cancellation':
                    name = f"Stornierungsfrist - {name}"
                elif rec.milestone_key:
                    name = f"{rec.milestone_key.title()} - {name}"
                rec.display_name = f"{icon} {date_str} {name}"
            else:
                rec.display_name = f"{icon} {date_str} {rec.start or ''} - {rec.event_id.name or ''}"
    
    # =========================
    # Actions
    # =========================
    
    def action_open_conference(self):
        """Open conference URL in new browser tab."""
        self.ensure_one()
        if self.conference_url:
            return {
                'type': 'ir.actions.act_url',
                'url': self.conference_url,
                'target': 'new',
            }
        return False
    
    def action_copy_conference_url(self):
        """Copy conference URL to clipboard (client-side action)."""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Conference URL',
                'message': self.conference_url or 'No URL available',
                'type': 'info',
                'sticky': False,
            }
        }
