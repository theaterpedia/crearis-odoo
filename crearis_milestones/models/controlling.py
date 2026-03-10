# -*- coding: utf-8 -*-
# Copyright 2026 theaterpedia.org / crearis.io
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

"""
S2L Controlling Layer (Direction 4).

Transient models providing unified biweekly dashboard across:
- agenda.line (events, milestones)
- calendar.event (consulting video/phone calls)
- crm.lead (email-only inquiries)

Staff can view/group by: exec, domain, lane_type, state.
"""

from datetime import timedelta
from odoo import api, fields, models


class ControllingLine(models.TransientModel):
    """Unified controlling line reading from all source models.
    
    Direction 4: No persistent data - computes from sources on dashboard refresh.
    """
    _name = 'controlling.line'
    _description = 'S2L Controlling Line'
    _order = 'date desc'

    # ─── Source Reference ────────────────────────────────────────────────────
    dashboard_id = fields.Many2one(
        'controlling.dashboard',
        string='Dashboard',
        ondelete='cascade',
    )
    
    source_type = fields.Selection([
        ('agenda', 'Agenda Line'),
        ('consulting', 'Consulting Meeting'),
        ('inquiry', 'Email Inquiry'),
    ], string='Source Type', required=True)
    
    agenda_line_id = fields.Many2one('agenda.line', string='Agenda Line')
    calendar_event_id = fields.Many2one('calendar.event', string='Calendar Event')
    crm_lead_id = fields.Many2one('crm.lead', string='CRM Lead')

    # ─── Unified Computed Fields ─────────────────────────────────────────────
    partner_id = fields.Many2one('res.partner', compute='_compute_unified', store=True)
    partner_name = fields.Char(compute='_compute_unified', store=True)
    date = fields.Datetime(compute='_compute_unified', store=True)
    assigned_exec_id = fields.Many2one('res.users', compute='_compute_unified', store=True, string='Exec')
    state = fields.Char(compute='_compute_unified', store=True)
    state_color = fields.Char(compute='_compute_unified', store=True)
    
    lane_type = fields.Selection([
        ('event', 'Event Session'),
        ('email_only', 'Email Only'),
        ('15_min', '15-Minute Call'),
        ('30_min', '30-Minute Call'),
        ('coaching', 'Coaching Session'),
    ], compute='_compute_unified', store=True, string='Lane')
    
    domain_code = fields.Char(compute='_compute_unified', store=True, string='Domain')
    category_summary = fields.Char(compute='_compute_unified', store=True, string='Categories')

    @api.depends('source_type', 'agenda_line_id', 'calendar_event_id', 'crm_lead_id')
    def _compute_unified(self):
        for line in self:
            if line.source_type == 'agenda' and line.agenda_line_id:
                al = line.agenda_line_id
                line.partner_id = al.partner_id
                line.partner_name = al.partner_id.name if al.partner_id else ''
                line.date = al.date
                line.assigned_exec_id = al.user_id
                line.state = al.gate_state or 'pending'
                line.state_color = 'info' if al.gate_state == 'pending' else 'success'
                line.lane_type = 'event'
                line.domain_code = getattr(al, 'domain_code', '') or ''
                line.category_summary = ''
                
            elif line.source_type == 'consulting' and line.calendar_event_id:
                event = line.calendar_event_id
                partner = event.partner_ids[:1] if event.partner_ids else None
                line.partner_id = partner
                line.partner_name = partner.name if partner else ''
                line.date = event.start
                line.assigned_exec_id = event.user_id
                line.state = event.consulting_status or 'scheduled'
                line.state_color = {
                    'pending_reconfirm': 'warning',
                    'confirmed': 'success',
                    'cancellable': 'info',
                    'cancelled': 'danger',
                }.get(event.consulting_status, 'secondary')
                # Duration: 0.5 hours = 30 min, 0.25 hours = 15 min
                duration_hours = event.duration or 0.25
                if duration_hours >= 1.0:
                    line.lane_type = 'coaching'
                elif duration_hours >= 0.5:
                    line.lane_type = '30_min'
                else:
                    line.lane_type = '15_min'
                line.domain_code = event.domain_code or ''
                # Parse categories from consulting_data
                data = event.consulting_data or {}
                if isinstance(data, dict):
                    cats = [s.get('category', '') for s in data.get('selections', [])]
                    line.category_summary = ', '.join(cats[:3])
                else:
                    line.category_summary = ''
                
            elif line.source_type == 'inquiry' and line.crm_lead_id:
                lead = line.crm_lead_id
                line.partner_id = lead.partner_id
                line.partner_name = lead.partner_id.name if lead.partner_id else lead.contact_name or ''
                line.date = lead.create_date
                line.assigned_exec_id = lead.user_id
                line.state = lead.stage_id.name if lead.stage_id else 'New'
                line.state_color = 'info'
                line.lane_type = 'email_only'
                line.domain_code = lead.consulting_domain_code or ''
                line.category_summary = ', '.join(lead.tag_ids.mapped('name')[:3])
            
            else:
                # Fallbacks for empty records
                line.partner_id = False
                line.partner_name = ''
                line.date = False
                line.assigned_exec_id = False
                line.state = ''
                line.state_color = 'secondary'
                line.lane_type = False
                line.domain_code = ''
                line.category_summary = ''

    def action_open_source(self):
        """Open the source record in form view."""
        self.ensure_one()
        model_map = {
            'agenda': ('agenda.line', self.agenda_line_id.id if self.agenda_line_id else False),
            'consulting': ('calendar.event', self.calendar_event_id.id if self.calendar_event_id else False),
            'inquiry': ('crm.lead', self.crm_lead_id.id if self.crm_lead_id else False),
        }
        model, res_id = model_map.get(self.source_type, (None, None))
        if not model or not res_id:
            return {}
        return {
            'type': 'ir.actions.act_window',
            'res_model': model,
            'res_id': res_id,
            'view_mode': 'form',
            'target': 'current',
        }


class ControllingDashboard(models.TransientModel):
    """Biweekly controlling dashboard builder.
    
    Creates transient controlling.line records from all sources.
    """
    _name = 'controlling.dashboard'
    _description = 'S2L Controlling Dashboard'

    name = fields.Char(default='S2L Dashboard', readonly=True)
    line_ids = fields.One2many('controlling.line', 'dashboard_id', string='Lines')
    
    # ─── Filters ─────────────────────────────────────────────────────────────
    exec_id = fields.Many2one('res.users', string='Filter by Exec')
    domain_code = fields.Selection([
        ('dasei1', 'Einstiege'),
        ('dasei2', 'Grundlagen'),
        ('dasei3', 'Aufbaustufe'),
    ], string='Filter by Domain')
    date_from = fields.Date(
        string='From',
        default=lambda self: fields.Date.today() - timedelta(days=14),
    )
    date_to = fields.Date(
        string='To',
        default=lambda self: fields.Date.today() + timedelta(days=14),
    )
    
    # ─── Stats ───────────────────────────────────────────────────────────────
    line_count = fields.Integer(compute='_compute_stats', string='Total Lines')
    consulting_count = fields.Integer(compute='_compute_stats', string='Consulting Calls')
    inquiry_count = fields.Integer(compute='_compute_stats', string='Email Inquiries')
    
    @api.depends('line_ids')
    def _compute_stats(self):
        for dashboard in self:
            dashboard.line_count = len(dashboard.line_ids)
            dashboard.consulting_count = len(dashboard.line_ids.filtered(
                lambda l: l.source_type == 'consulting'
            ))
            dashboard.inquiry_count = len(dashboard.line_ids.filtered(
                lambda l: l.source_type == 'inquiry'
            ))

    def action_refresh(self):
        """Rebuild controlling lines from all sources."""
        self.ensure_one()
        self.line_ids.unlink()
        
        lines_data = []
        date_from_dt = fields.Datetime.to_datetime(self.date_from) if self.date_from else None
        date_to_dt = fields.Datetime.to_datetime(self.date_to) if self.date_to else None
        if date_to_dt:
            # Make date_to inclusive (end of day)
            date_to_dt = date_to_dt.replace(hour=23, minute=59, second=59)
        
        # 1. Agenda lines
        agenda_domain = []
        if date_from_dt:
            agenda_domain.append(('date', '>=', date_from_dt))
        if date_to_dt:
            agenda_domain.append(('date', '<=', date_to_dt))
        if self.exec_id:
            agenda_domain.append(('user_id', '=', self.exec_id.id))
        
        AgendaLine = self.env['agenda.line']
        for al in AgendaLine.search(agenda_domain):
            lines_data.append({
                'dashboard_id': self.id,
                'source_type': 'agenda',
                'agenda_line_id': al.id,
            })
        
        # 2. Consulting calendar events (have consulting_status)
        event_domain = [('consulting_status', '!=', False)]
        if date_from_dt:
            event_domain.append(('start', '>=', date_from_dt))
        if date_to_dt:
            event_domain.append(('start', '<=', date_to_dt))
        if self.exec_id:
            event_domain.append(('user_id', '=', self.exec_id.id))
        
        CalendarEvent = self.env['calendar.event']
        for ce in CalendarEvent.search(event_domain):
            lines_data.append({
                'dashboard_id': self.id,
                'source_type': 'consulting',
                'calendar_event_id': ce.id,
            })
        
        # 3. Email inquiries (crm.lead with is_consulting_inquiry)
        lead_domain = [('is_consulting_inquiry', '=', True)]
        if date_from_dt:
            lead_domain.append(('create_date', '>=', date_from_dt))
        if date_to_dt:
            lead_domain.append(('create_date', '<=', date_to_dt))
        if self.exec_id:
            lead_domain.append(('user_id', '=', self.exec_id.id))
        
        CrmLead = self.env['crm.lead']
        for lead in CrmLead.search(lead_domain):
            lines_data.append({
                'dashboard_id': self.id,
                'source_type': 'inquiry',
                'crm_lead_id': lead.id,
            })
        
        if lines_data:
            self.env['controlling.line'].create(lines_data)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'controlling.dashboard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model
    def action_open_dashboard(self):
        """Action to open a new dashboard (creates fresh transient record)."""
        dashboard = self.create({})
        dashboard.action_refresh()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'controlling.dashboard',
            'res_id': dashboard.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'form_view_initial_mode': 'edit'},
        }
