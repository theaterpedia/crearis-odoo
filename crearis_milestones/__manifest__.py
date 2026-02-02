# -*- coding: utf-8 -*-
# Copyright 2026 theaterpedia.org / crearis.io
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Crearis Milestones',
    'version': '16.0.1.0.0',
    'summary': 'Controlling Dashboard for Milestone Management',
    'description': """
Enhanced milestone workflow for participant management.

Features:
- Check-level tracking on event.registration (check_state, check_comment)
- Blocker detection (payment_overdue, event_unresolved, confirmation_pending)
- Controlling dashboard with BEREIT/TRIAGE sections
- Bulk confirmation actions
- Email templates for milestone communications

Terminology:
- Milestone = Event-level gate (agenda.line)
- Check = Participant-level within milestone (event.registration)

See: _meta/Whitepaper/architecture_milestones_and_actions.md
""",
    'category': 'Website/Crearis',
    'license': 'LGPL-3',
    'author': 'Theaterpedia',
    'website': 'https://theaterpedia.org/',
    'depends': [
        'crearis',
        'account',  # For invoice/payment blocker detection
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/mail_template_data.xml',
        'views/event_registration_views.xml',
        'views/agenda_line_blocker_views.xml',
        'views/controlling_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
