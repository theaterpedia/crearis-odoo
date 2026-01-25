# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Agenda DASEi',
    'version': '16.0.1.0.0',
    'summary': 'DASEi-specific partner status and domaincode mapping',
    'description': """
DASEi-specific extensions for Crearis Agenda sync.

Features:
- Partner status → domaincode mapping from contacts.Status
- Kursteilnehmer evaluation (Kurs field → dasei1/2/3)
- Computed highest domaincode for login routing
- Sync of plan_kursteilnehmer and contacts
- Course products (M18, N18, ZR, ZT profiles)
- Module progress tracking (A, B, C, D modules)
    """,
    'category': 'Website/Crearis',
    'license': 'LGPL-3',
    'application': False,
    'author': 'Theaterpedia',
    'website': 'https://theaterpedia.org/',
    'depends': [
        'crearis_agenda',
        'product',
        'event',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',  # D6: Cron jobs for course and registration sync
        'views/agenda_dasei_menu.xml',  # DA1: DASEi submenu structure
        'views/res_partner_views.xml',
        'views/course_views.xml',  # D3: Course model views
        # TODO: Refactor to crearis_event_package module
        # 'views/product_template_views.xml',
        'views/course_participation_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
