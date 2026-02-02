# -*- coding: utf-8 -*-
# Copyright 2026 theaterpedia.org / crearis.io
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api, _


class AgendaLine(models.Model):
    """
    Extend agenda.line with milestone business logic for crearis_milestones.
    
    The base gate_state field is in crearis module.
    This extension adds:
    - Helper method to check if line is a deadline milestone
    - Extended cron to sync check_states on registrations
    """
    _inherit = 'agenda.line'
    
    is_deadline_milestone = fields.Boolean(
        compute='_compute_is_deadline_milestone',
        store=True,
        help="True if this is the deadline milestone for the event"
    )
    
    @api.depends('type', 'milestone_key')
    def _compute_is_deadline_milestone(self):
        for rec in self:
            rec.is_deadline_milestone = (
                rec.type == 'milestone' 
                and rec.milestone_key == 'deadline'
            )
    
    @api.model
    def _cron_check_milestone_dates(self):
        """
        Extended cron: also sync check_states on registrations.
        
        This overrides the base crearis cron to add:
        1. Sync registration check_states when milestone becomes ready
        2. Check for blockers on each registration
        """
        # Call parent implementation first
        result = super()._cron_check_milestone_dates()
        
        # Now find milestones that just became ready and sync registrations
        ready_milestones = self.search([
            ('type', '=', 'milestone'),
            ('gate_state', '=', 'ready'),
            ('event_id', '!=', False),
        ])
        
        for milestone in ready_milestones:
            milestone.event_id._sync_check_states_from_milestone()
        
        return result


class EventEvent(models.Model):
    """
    Extend event.event with milestone helper methods.
    """
    _inherit = 'event.event'
    
    def _get_milestone_line(self, key='deadline'):
        """
        Return the milestone agenda.line for this event.
        
        Args:
            key: 'activation', 'deadline', or 'completion'
        
        Returns:
            agenda.line record or empty recordset
        """
        self.ensure_one()
        return self.agenda_line_ids.filtered(
            lambda l: l.type == 'milestone' and l.milestone_key == key
        )[:1]
    
    def _sync_check_states_from_milestone(self):
        """
        Sync check_state on registrations from milestone gate_state.
        Called when milestone becomes ready.
        """
        for event in self:
            milestone = event._get_milestone_line('deadline')
            if not milestone:
                continue
            
            if milestone.gate_state == 'ready':
                # Set all pending registrations to ready
                registrations = event.registration_ids.filtered(
                    lambda r: r.state == 'open' and r.check_state == 'pending'
                )
                registrations.write({'check_state': 'ready'})
                
                # Check for blockers on each registration
                for reg in registrations:
                    blockers = reg._check_blockers()
                    if blockers:
                        reg.check_state = 'issue'
