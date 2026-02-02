# -*- coding: utf-8 -*-
# Copyright 2026 theaterpedia.org / crearis.io
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json
from odoo import models, fields, api, _


class EventRegistration(models.Model):
    """
    Extend event.registration with Check-level milestone tracking.
    
    Terminology (from architecture_milestones_and_actions.md):
    - Milestone = Event-level gate (agenda.line)
    - Check = Participant-level within milestone (this model)
    
    The registration IS the check. Controlling view groups by event_id
    to show milestones, with individual registrations as checks.
    """
    _inherit = 'event.registration'

    # =========================
    # Check State (mirrors gate_state on agenda.line)
    # =========================
    
    check_state = fields.Selection([
        ('pending', 'Pending'),
        ('ready', 'Ready'),
        ('sent', 'Sent'),
        ('issue', 'Issue'),
    ], string='Check State', default='pending', index=True,
       help="Milestone check state for this participant")
    
    check_comment = fields.Text(
        string='Comment',
        help="Notes about this registration (shown in Controlling view)"
    )
    
    # =========================
    # Blocker Detection
    # =========================
    
    blocker_ids = fields.One2many(
        'agenda.line.blocker',
        'registration_id',
        string='Blockers',
        help="Active blockers for this registration"
    )
    
    has_blockers = fields.Boolean(
        compute='_compute_has_blockers',
        store=True,
        help="True if partner has unresolved blockers"
    )
    
    blocker_count = fields.Integer(
        compute='_compute_has_blockers',
        store=True
    )
    
    blocker_summary = fields.Char(
        compute='_compute_blocker_summary',
        help="Short summary of blockers for display"
    )
    
    @api.depends('partner_id', 'blocker_ids', 'blocker_ids.resolved')
    def _compute_has_blockers(self):
        """Check if partner has any unresolved blockers."""
        for reg in self:
            if not reg.partner_id:
                reg.has_blockers = False
                reg.blocker_count = 0
                continue
            
            # Check all blockers for this partner (not just this registration)
            unresolved = self.env['agenda.line.blocker'].search_count([
                ('partner_id', '=', reg.partner_id.id),
                ('resolved', '=', False),
            ])
            reg.has_blockers = unresolved > 0
            reg.blocker_count = unresolved
    
    @api.depends('partner_id', 'has_blockers')
    def _compute_blocker_summary(self):
        """Generate short summary for Controlling view."""
        for reg in self:
            if not reg.has_blockers or not reg.partner_id:
                reg.blocker_summary = ''
                continue
            
            blockers = self.env['agenda.line.blocker'].search([
                ('partner_id', '=', reg.partner_id.id),
                ('resolved', '=', False),
            ], order='severity desc')
            
            summaries = []
            for b in blockers[:2]:  # Max 2 in summary
                if b.blocker_type == 'payment_overdue':
                    try:
                        data = json.loads(b.data_json or '{}')
                        amount = data.get('amount', 0)
                        summaries.append(f"EUR {amount:,.0f}")
                    except:
                        summaries.append("Payment")
                elif b.blocker_type == 'event_unresolved':
                    summaries.append("Event")
                elif b.blocker_type == 'confirmation_pending':
                    summaries.append("Confirm")
            
            if len(blockers) > 2:
                summaries.append(f"+{len(blockers) - 2}")
            
            reg.blocker_summary = ' | '.join(summaries)
    
    # =========================
    # Check Detection (called by cron)
    # =========================
    
    def _check_blockers(self):
        """
        Check for conditions that should block this registration's milestone.
        Creates blocker records for any found issues.
        
        Returns:
            list of dict: Created blockers
        
        See: architecture_milestones_and_actions.md Section 10.3
        """
        self.ensure_one()
        blockers_created = []
        partner = self.partner_id
        
        if not partner:
            return blockers_created
        
        Blocker = self.env['agenda.line.blocker']
        
        # 1. Payment overdue
        overdue_invoices = self.env['account.move'].search([
            ('partner_id', '=', partner.id),
            ('move_type', '=', 'out_invoice'),
            ('payment_state', 'in', ['not_paid', 'partial']),
            ('invoice_date_due', '<', fields.Date.today()),
        ])
        
        if overdue_invoices:
            # Check if blocker already exists
            existing = Blocker.search([
                ('partner_id', '=', partner.id),
                ('blocker_type', '=', 'payment_overdue'),
                ('resolved', '=', False),
            ], limit=1)
            
            if not existing:
                data = {
                    'amount': sum(overdue_invoices.mapped('amount_residual')),
                    'count': len(overdue_invoices),
                    'oldest_due': str(min(overdue_invoices.mapped('invoice_date_due'))),
                }
                blocker = Blocker.create({
                    'partner_id': partner.id,
                    'registration_id': self.id,
                    'blocker_type': 'payment_overdue',
                    'severity': 'high',
                    'data_json': json.dumps(data),
                })
                blockers_created.append(blocker)
        
        # 2. Event unresolved (pending package selections)
        # Only check if crearis_event_package is installed
        if hasattr(self.env['res.partner'], 'package_event_line_ids'):
            pending_selections = self.env['product.package.event.line'].search([
                ('partner_id', '=', partner.id),
                ('event_id', '=', False),
                ('state', '!=', 'cancelled'),
            ])
            
            if pending_selections:
                existing = Blocker.search([
                    ('partner_id', '=', partner.id),
                    ('blocker_type', '=', 'event_unresolved'),
                    ('resolved', '=', False),
                ], limit=1)
                
                if not existing:
                    data = {
                        'count': len(pending_selections),
                        'event_types': list(set(pending_selections.mapped('event_type_id.name'))),
                    }
                    blocker = Blocker.create({
                        'partner_id': partner.id,
                        'registration_id': self.id,
                        'blocker_type': 'event_unresolved',
                        'severity': 'medium',
                        'data_json': json.dumps(data),
                    })
                    blockers_created.append(blocker)
        
        # 3. Confirmation pending (overdue activities)
        pending_activities = self.env['mail.activity'].search([
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', partner.id),
            ('date_deadline', '<', fields.Date.today()),
        ])
        
        # Filter for confirmation-type activities (by summary keyword)
        confirmation_activities = pending_activities.filtered(
            lambda a: 'confirm' in (a.summary or '').lower() 
            or 'bestätig' in (a.summary or '').lower()
        )
        
        if confirmation_activities:
            existing = Blocker.search([
                ('partner_id', '=', partner.id),
                ('blocker_type', '=', 'confirmation_pending'),
                ('resolved', '=', False),
            ], limit=1)
            
            if not existing:
                data = {
                    'count': len(confirmation_activities),
                    'oldest': str(min(confirmation_activities.mapped('create_date'))),
                }
                blocker = Blocker.create({
                    'partner_id': partner.id,
                    'registration_id': self.id,
                    'blocker_type': 'confirmation_pending',
                    'severity': 'low',
                    'data_json': json.dumps(data),
                })
                blockers_created.append(blocker)
        
        return blockers_created
    
    # =========================
    # Check Actions
    # =========================
    
    def action_confirm_check(self):
        """
        Confirm this check and send milestone email.
        Called from Controlling view "Bestätigen" button.
        """
        for reg in self:
            if reg.has_blockers:
                raise models.UserError(_(
                    "Cannot confirm %s: has %d unresolved blocker(s). "
                    "Resolve blockers first or use 'Override'."
                ) % (reg.partner_id.name, reg.blocker_count))
            
            if reg.check_state != 'ready':
                continue
            
            # Send email via event's milestone template
            milestone_line = reg.event_id._get_milestone_line()
            if milestone_line and milestone_line.milestone_template_id:
                milestone_line.milestone_template_id.send_mail(
                    reg.id,
                    force_send=False,  # Queue for 4h delay
                )
            
            reg.check_state = 'sent'
        
        return True
    
    def action_confirm_override(self):
        """
        Confirm despite blockers (coordinator override).
        """
        for reg in self:
            if reg.check_state not in ('ready', 'issue'):
                continue
            
            # Mark blockers as resolved with override note
            blockers = self.env['agenda.line.blocker'].search([
                ('partner_id', '=', reg.partner_id.id),
                ('resolved', '=', False),
            ])
            blockers.write({
                'resolved': True,
                'resolved_by': self.env.uid,
                'resolved_date': fields.Datetime.now(),
                'resolution_note': _("Override by %s") % self.env.user.name,
            })
            
            reg.check_state = 'sent'
        
        return True
    
    def action_flag_issue(self):
        """Flag check for review."""
        self.write({'check_state': 'issue'})
        return True
    
    def action_show_blockers(self):
        """Open blocker detail view for this registration."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Blockers: %s') % self.partner_id.name,
            'res_model': 'agenda.line.blocker',
            'view_mode': 'tree,form',
            'domain': [
                ('partner_id', '=', self.partner_id.id),
                ('resolved', '=', False),
            ],
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_registration_id': self.id,
            },
        }
    
    # =========================
    # Bulk Actions (for server action)
    # =========================
    
    def action_confirm_all_ready(self):
        """
        Bulk confirm all ready checks without blockers.
        Used by "Alle bestätigen" button in Controlling.
        """
        ready_clean = self.filtered(
            lambda r: r.check_state == 'ready' and not r.has_blockers
        )
        ready_clean.action_confirm_check()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Checks Confirmed'),
                'message': _('%d checks confirmed and emails queued.') % len(ready_clean),
                'type': 'success',
            }
        }
