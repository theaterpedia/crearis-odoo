# -*- coding: utf-8 -*-
# Copyright 2026 theaterpedia.org / crearis.io
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api


class EventSessionLine(models.Model):
    """
    Lightweight session line model for schedule display and filtering.
    
    These records are synced from schedule_data.sessions[] JSONB.
    They provide:
    - Searchable/filterable session records
    - O2M table in event form
    - "All Online Sessions" list view
    - Conference URL storage (future: MS Teams integration)
    
    This is NOT the heavy OCA event.session (which has own registrations).
    This is a display/reporting layer on top of the JSONB schedule_data.
    """
    _name = 'event.session.line'
    _description = 'Event Session Line'
    _order = 'date, start, event_id'
    _rec_name = 'display_name'

    # =========================
    # Core Fields (from schedule_data.sessions[])
    # =========================
    
    event_id = fields.Many2one(
        'event.event', 
        string='Event',
        required=True, 
        ondelete='cascade', 
        index=True
    )
    sequence = fields.Integer(default=10, help="Session order within event")
    
    # Time information
    day = fields.Char('Weekday', size=3, help="MON, TUE, WED, THU, FRI, SAT, SUN")
    date = fields.Date('Date', index=True)
    start = fields.Char('Start Time', size=5, help="HH:MM format")
    end = fields.Char('End Time', size=5, help="HH:MM format")
    duration_h = fields.Float('Duration (h)', digits=(4, 1))
    
    # Session type and location
    type = fields.Selection([
        ('online', 'Online'),
        ('venue', 'Venue'),
        ('individual', 'Individual'),
        ('tbd', 'TBD'),
    ], string='Type', default='venue', index=True)
    
    location_hint = fields.Char('Location Hint', help="Parsed location name")
    room = fields.Char('Room', help="Room identifier if specified")
    notes = fields.Text('Notes', help="Additional notes for this session")
    
    # =========================
    # Conference Integration (Scenario E: Hybrid JSONB + Product)
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
    
    @api.depends('event_id.name', 'date', 'start', 'type')
    def _compute_display_name(self):
        for rec in self:
            type_icon = '🌐' if rec.type == 'online' else '📍' if rec.type == 'venue' else '📋'
            date_str = rec.date.strftime('%Y-%m-%d') if rec.date else ''
            rec.display_name = f"{type_icon} {date_str} {rec.start or ''} - {rec.event_id.name or ''}"
    
    # =========================
    # Conference Actions
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
        # This would need JS widget support
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
