# -*- coding: utf-8 -*-
# Copyright 2026 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api

# Sysreg values for registration states
# Follows bitmask architecture compatible with website project
REGISTRATION_STATE_SYSREG = {
    'new': 1,        # Offer / pre-registration
    'demo': 8,       # Proposal / tentative
    'draft': 64,     # Unconfirmed (base Odoo)
    'open': 512,     # Confirmed (base Odoo)
    'done': 4096,    # Attended (base Odoo)
    'cancel': 12288, # Cancelled (base Odoo)
    'no_show': 16384,  # Registered but didn't attend
    'partial': 20480,  # Partial attendance
}


class EventRegistration(models.Model):
    _inherit = 'event.registration'

    # Override state field with extended selection
    # Base Odoo states: draft, open, done, cancel
    # New states: new, demo, no_show, partial
    state = fields.Selection(
        selection_add=[
            ('new', 'Offer'),
            ('demo', 'Proposal'),
            ('no_show', 'Absent'),
            ('partial', 'Partial'),
        ],
        ondelete={
            'new': 'set default',
            'demo': 'set default',
            'no_show': 'set default',
            'partial': 'set default',
        }
    )

    # Computed sysreg value for external systems
    state_sysreg = fields.Integer(
        string='State (sysreg)',
        compute='_compute_state_sysreg',
        store=True,
        help='Sysreg bitmask value for state'
    )

    # Additional fields for registration tracking
    units = fields.Float(
        string='Units',
        digits=(10, 2),
        default=0.0,
        help='Teaching units / credits attended (e.g., 2.5 UE)'
    )

    # Note: 'note' field already exists in base event.registration
    # We add 'internal_notes' for staff-only comments
    internal_notes = fields.Text(
        string='Internal Notes',
        help='Staff-only notes about this registration'
    )

    @api.depends('state')
    def _compute_state_sysreg(self):
        for reg in self:
            reg.state_sysreg = REGISTRATION_STATE_SYSREG.get(reg.state, 0)

    def action_set_new(self):
        """Set registration to 'new' (offer) state."""
        self.write({'state': 'new'})

    def action_set_demo(self):
        """Set registration to 'demo' (proposal) state."""
        self.write({'state': 'demo'})

    def action_set_no_show(self):
        """Set registration to 'no_show' (absent) state."""
        self.write({'state': 'no_show'})

    def action_set_partial(self):
        """Set registration to 'partial' attendance state."""
        self.write({'state': 'partial'})
