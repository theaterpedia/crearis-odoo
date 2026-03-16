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

    # SharePoint sync fields
    ms_id = fields.Char(
        string='SharePoint ID',
        index=True,
        copy=False,
        help='SharePoint plan_veranstaltungsteilnehmer ID'
    )
    ms_version = fields.Char(
        string='SharePoint Version',
        copy=False,
        help='SharePoint @odata.etag for change detection'
    )
    ms_synced = fields.Boolean(
        string='Synced from SharePoint',
        default=False,
        copy=False,
        help='True if this registration was created/updated by SharePoint sync'
    )

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

    # =========================
    # Email Template Helpers
    # =========================

    def get_event_title_parts(self):
        """
        Parse event name into overline/headline structure.
        
        Pattern: "Prefix text **Headline**" or "Prefix text"
        
        Returns dict with:
            - overline: Event type name (e.g., "DAS Ei - Intensivkurs")
            - headline: Main title wrapped in ** (e.g., "Das Theaterpädagogische Dreieck")
            - subline: Text before ** (e.g., "Repetitorium zu den Modulen A-C")
            - full_name: Original name
        """
        self.ensure_one()
        event = self.event_id
        name = event.name or ''
        
        result = {
            'overline': '',
            'headline': name,
            'subline': '',
            'full_name': name,
        }
        
        # Event type as overline
        if event.event_type_id:
            result['overline'] = event.event_type_id.name or ''
        
        # Parse **headline** from name
        import re
        match = re.search(r'\*\*(.+?)\*\*', name)
        if match:
            result['headline'] = match.group(1)
            result['subline'] = name[:match.start()].strip()
        
        return result

    def get_session_schedule_html(self):
        """
        Generate HTML table for session schedule from agenda_line_ids.
        
        Shows session-type lines with:
        - Date (formatted German)
        - Weekday
        - Start-End times
        - Mode icon (🌐 online, 📍 venue)
        
        Returns: HTML string or empty string if no sessions
        """
        self.ensure_one()
        event = self.event_id
        
        # Get session lines only (not milestones, info, etc.)
        sessions = event.agenda_line_ids.filtered(
            lambda l: l.type == 'session' and l.date
        ).sorted(key=lambda l: (l.date, l.start or ''))
        
        if not sessions:
            return ''
        
        # German month names
        months_de = {
            1: 'Januar', 2: 'Februar', 3: 'März', 4: 'April',
            5: 'Mai', 6: 'Juni', 7: 'Juli', 8: 'August',
            9: 'September', 10: 'Oktober', 11: 'November', 12: 'Dezember'
        }
        weekdays_de = {
            0: 'Mo', 1: 'Di', 2: 'Mi', 3: 'Do', 4: 'Fr', 5: 'Sa', 6: 'So'
        }
        
        rows = []
        for sess in sessions:
            date_obj = sess.date
            weekday = weekdays_de.get(date_obj.weekday(), '')
            date_str = f"{weekday}, {date_obj.day}. {months_de.get(date_obj.month, '')}"
            
            # Time range
            time_str = ''
            if sess.start:
                time_str = sess.start
                if sess.end:
                    time_str += f' – {sess.end}'
            
            # Mode icon
            mode_icon = '🌐' if sess.mode == 'online' else '📍'
            
            rows.append(f'''
                <tr>
                    <td style="padding: 4px 8px; vertical-align: top;">{mode_icon}</td>
                    <td style="padding: 4px 8px; vertical-align: top; white-space: nowrap;">{date_str}</td>
                    <td style="padding: 4px 8px; vertical-align: top; white-space: nowrap;">{time_str}</td>
                </tr>
            ''')
        
        return f'''
            <table style="border-collapse: collapse; font-size: 14px;">
                {''.join(rows)}
            </table>
        '''

    def get_session_schedule_text(self):
        """
        Generate plain text schedule summary.
        Format: "Do, 19. März 09:00 – 17:00 | Fr, 20. März 09:00 – 17:00"
        """
        self.ensure_one()
        event = self.event_id
        
        sessions = event.agenda_line_ids.filtered(
            lambda l: l.type == 'session' and l.date
        ).sorted(key=lambda l: (l.date, l.start or ''))
        
        if not sessions:
            return ''
        
        months_de = {
            1: 'Jan', 2: 'Feb', 3: 'Mär', 4: 'Apr', 5: 'Mai', 6: 'Jun',
            7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Okt', 11: 'Nov', 12: 'Dez'
        }
        weekdays_de = {
            0: 'Mo', 1: 'Di', 2: 'Mi', 3: 'Do', 4: 'Fr', 5: 'Sa', 6: 'So'
        }
        
        parts = []
        for sess in sessions:
            date_obj = sess.date
            weekday = weekdays_de.get(date_obj.weekday(), '')
            date_str = f"{weekday}, {date_obj.day}. {months_de.get(date_obj.month, '')}"
            
            if sess.start:
                date_str += f' {sess.start}'
                if sess.end:
                    date_str += f'–{sess.end}'
            
            parts.append(date_str)
        
        return ' | '.join(parts)
