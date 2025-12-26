# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models

from .product_template import MODULE_GROUPS


class CourseParticipation(models.Model):
    """Links participants (partners) to course products.
    
    Synced from SharePoint plan_kursteilnehmer list.
    
    Module grouping is derived from event registrations:
    - Events link to event.type via event_type_id
    - event.type.name contains module code (A1, A2, B1, etc.)
    - First letter determines module group (A, B, C, ...)
    """
    _name = 'dasei.course.participation'
    _description = 'Course Participation'
    _order = 'course_id, partner_id'

    # SharePoint sync fields
    ms_item_id = fields.Char(
        string='MS Item ID',
        index=True,
        help='SharePoint plan_kursteilnehmer item ID'
    )
    ms_etag = fields.Char(string='MS ETag')

    # Core relations
    partner_id = fields.Many2one(
        'res.partner',
        string='Participant',
        required=True,
        ondelete='cascade',
        index=True,
    )
    course_id = fields.Many2one(
        'product.template',
        string='Course',
        required=True,
        ondelete='cascade',
        index=True,
        domain="[('ms_contact_id', '!=', False)]",
    )

    # Status and notes
    status_id = fields.Integer(
        string='Status ID',
        help='SharePoint StatsLookupId'
    )
    notes = fields.Text(
        string='Notes',
        help='Bemerkung from SharePoint'
    )
    is_created = fields.Boolean(
        string='Is Created',
        help='SharePoint angelegt flag'
    )

    # Computed module progress
    completed_modules = fields.Char(
        string='Completed Modules',
        compute='_compute_completed_modules',
        store=True,
        help='Comma-separated list of completed module groups (A, B, C...)'
    )

    _sql_constraints = [
        ('ms_item_id_unique', 'unique(ms_item_id)',
         'SharePoint item ID must be unique!'),
        ('partner_course_unique', 'unique(partner_id, course_id)',
         'A participant can only have one participation record per course!'),
    ]

    @api.depends('partner_id', 'course_id')
    def _compute_completed_modules(self):
        """Compute completed modules from event registrations.
        
        Looks at all confirmed event registrations for this partner
        where the event's event_type matches the course program/year,
        and extracts the module group letter from event_type.name.
        """
        Registration = self.env['event.registration']
        
        for record in self:
            if not record.partner_id or not record.course_id:
                record.completed_modules = ''
                continue
            
            # Get all confirmed registrations for this partner
            registrations = Registration.search([
                ('partner_id', '=', record.partner_id.id),
                ('state', 'in', ['open', 'done']),
            ])
            
            # Extract module groups from event types
            modules = set()
            for reg in registrations:
                event_type = reg.event_id.event_type_id
                if event_type and event_type.name:
                    # First letter of event_type.name is the module group
                    module_letter = event_type.name[0].upper()
                    if module_letter in MODULE_GROUPS:
                        modules.add(module_letter)
            
            record.completed_modules = ','.join(sorted(modules))

    def get_module_progress(self):
        """Return detailed module progress for this participation.
        
        Returns dict with:
        - completed: list of completed module letters
        - pending: list of pending module letters for this course type
        - details: dict mapping module letter to list of completed event names
        """
        self.ensure_one()
        Registration = self.env['event.registration']
        
        # Modules required for Grundstufe (M/N programs)
        GRUNDSTUFE_MODULES = ['A', 'B', 'C', 'D', 'E', 'F']
        # Modules for Aufbaustufe (ZR/ZT profiles)
        AUFBAUSTUFE_MODULES = ['G', 'H', 'J', 'L']
        
        required_modules = GRUNDSTUFE_MODULES
        if self.course_id.course_program in ('ZR', 'ZT'):
            required_modules = AUFBAUSTUFE_MODULES
        
        # Get registrations
        registrations = Registration.search([
            ('partner_id', '=', self.partner_id.id),
            ('state', 'in', ['open', 'done']),
        ])
        
        # Build details
        details = {}
        for reg in registrations:
            event_type = reg.event_id.event_type_id
            if event_type and event_type.name:
                module_letter = event_type.name[0].upper()
                if module_letter in MODULE_GROUPS:
                    if module_letter not in details:
                        details[module_letter] = []
                    details[module_letter].append({
                        'event': reg.event_id.name,
                        'code': event_type.name,
                        'date': reg.event_id.date_begin,
                        'state': reg.state,
                    })
        
        completed = list(details.keys())
        pending = [m for m in required_modules if m not in completed]
        
        return {
            'completed': sorted(completed),
            'pending': sorted(pending),
            'details': details,
        }
