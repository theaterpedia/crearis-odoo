# -*- coding: utf-8 -*-
# Copyright 2026 theaterpedia.org / crearis.io
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json
from odoo import models, fields, api, _


class AgendaLineBlocker(models.Model):
    """
    Blocker record that prevents a milestone check from completing.
    
    Three blocker types (from architecture_milestones_and_actions.md Section 10):
    - payment_overdue: Partner has unpaid invoices
    - event_unresolved: Pending event selections in package
    - confirmation_pending: Overdue confirmation request activities
    
    Blockers are linked to partner (not registration) so they appear
    across all milestones for that participant.
    
    See: _meta/Whitepaper/journey_selma_issue_driver.md
    """
    _name = 'agenda.line.blocker'
    _description = 'Milestone Blocker'
    _rec_name = 'display_name'
    _order = 'severity desc, create_date desc'

    # =========================
    # Relations
    # =========================
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        ondelete='cascade',
        index=True,
        help="The participant with this blocker"
    )
    registration_id = fields.Many2one(
        'event.registration',
        string='Registration',
        ondelete='cascade',
        index=True,
        help="Optional: specific registration this blocker affects"
    )

    # =========================
    # Blocker Type and Severity
    # =========================
    
    blocker_type = fields.Selection([
        ('payment_overdue', 'Payment Overdue'),
        ('event_unresolved', 'Event Unresolved'),
        ('confirmation_pending', 'Confirmation Pending'),
    ], string='Type', required=True, index=True)
    
    severity = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Severity', default='medium', required=True)
    
    # =========================
    # Data Storage
    # =========================
    
    data_json = fields.Text(
        string='Data (JSON)',
        help="JSON-encoded blocker details"
    )
    
    # Computed display fields from JSON
    display_name = fields.Char(compute='_compute_display_name', store=True)
    data_display = fields.Html(compute='_compute_data_display')
    
    @api.depends('blocker_type', 'partner_id', 'data_json')
    def _compute_display_name(self):
        type_labels = {
            'payment_overdue': _('Payment Overdue'),
            'event_unresolved': _('Event Unresolved'),
            'confirmation_pending': _('Confirmation Pending'),
        }
        for rec in self:
            partner_name = rec.partner_id.name or ''
            type_label = type_labels.get(rec.blocker_type, rec.blocker_type)
            rec.display_name = f"{partner_name}: {type_label}"
    
    @api.depends('blocker_type', 'data_json')
    def _compute_data_display(self):
        """Format blocker data for display in UI."""
        for rec in self:
            if not rec.data_json:
                rec.data_display = ''
                continue
            
            try:
                data = json.loads(rec.data_json)
            except (json.JSONDecodeError, TypeError):
                rec.data_display = ''
                continue
            
            if rec.blocker_type == 'payment_overdue':
                amount = data.get('amount', 0)
                count = data.get('count', 0)
                rec.data_display = f"<strong>EUR {amount:,.2f}</strong> ({count} invoices)"
            
            elif rec.blocker_type == 'event_unresolved':
                count = data.get('count', 0)
                event_types = data.get('event_types', [])
                types_str = ', '.join(event_types[:3])
                if len(event_types) > 3:
                    types_str += '...'
                rec.data_display = f"<strong>{count}</strong> pending: {types_str}"
            
            elif rec.blocker_type == 'confirmation_pending':
                count = data.get('count', 0)
                rec.data_display = f"<strong>{count}</strong> requests pending"
            
            else:
                rec.data_display = str(data)

    # =========================
    # Resolution Tracking
    # =========================
    
    resolved = fields.Boolean(
        default=False,
        index=True,
        help="True when blocker has been resolved"
    )
    resolved_by = fields.Many2one(
        'res.users',
        string='Resolved By',
        readonly=True
    )
    resolved_date = fields.Datetime(
        string='Resolved On',
        readonly=True
    )
    resolution_note = fields.Text(
        string='Resolution Note',
        help="How this blocker was resolved"
    )
    
    # =========================
    # Actions
    # =========================
    
    def action_resolve(self):
        """Mark blocker as resolved."""
        self.write({
            'resolved': True,
            'resolved_by': self.env.uid,
            'resolved_date': fields.Datetime.now(),
        })
        # Recompute has_blockers on affected registrations
        registrations = self.mapped('registration_id') | self.env['event.registration'].search([
            ('partner_id', 'in', self.mapped('partner_id').ids),
            ('state', '!=', 'cancel'),
        ])
        registrations._compute_has_blockers()
        return True
    
    def action_open_related(self):
        """Open the related record (invoice, package, activity)."""
        self.ensure_one()
        
        if self.blocker_type == 'payment_overdue':
            # Open partner's unpaid invoices
            return {
                'type': 'ir.actions.act_window',
                'name': _('Unpaid Invoices'),
                'res_model': 'account.move',
                'view_mode': 'tree,form',
                'domain': [
                    ('partner_id', '=', self.partner_id.id),
                    ('move_type', '=', 'out_invoice'),
                    ('payment_state', 'in', ['not_paid', 'partial']),
                ],
                'context': {'default_partner_id': self.partner_id.id},
            }
        
        elif self.blocker_type == 'event_unresolved':
            # Open partner form with package tab
            return {
                'type': 'ir.actions.act_window',
                'name': self.partner_id.name,
                'res_model': 'res.partner',
                'res_id': self.partner_id.id,
                'view_mode': 'form',
            }
        
        elif self.blocker_type == 'confirmation_pending':
            # Open pending activities
            return {
                'type': 'ir.actions.act_window',
                'name': _('Pending Activities'),
                'res_model': 'mail.activity',
                'view_mode': 'tree,form',
                'domain': [
                    ('res_model', '=', 'res.partner'),
                    ('res_id', '=', self.partner_id.id),
                ],
            }
        
        return True
