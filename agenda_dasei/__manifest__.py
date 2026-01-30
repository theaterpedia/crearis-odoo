# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Agenda DASEi',
    'version': '16.0.1.2.0',
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
- Event registration sync from plan_veranstaltungsteilnehmer
- Status mapping: SharePoint StatusLookupId → Odoo registration state
- Auto-creates DASEi websites (dasei0, dasei1, dasei2, dasei3) on install
    """,
    'category': 'Website/Crearis',
    'license': 'LGPL-3',
    'application': False,
    'author': 'Theaterpedia',
    'website': 'https://theaterpedia.org/',
    'depends': [
        'crearis_agenda',
        'crearis_event_package',  # For event package products
        'product',
        'event',
        'website_event',  # For website event templates
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',  # D6: Cron jobs for course and registration sync
        'data/website_data.xml',  # DASEi website check/create server actions
        'data/product_template_data.xml',  # Grundkurs module products (A, B, C, D)
        'data/event_tag_data.xml',  # Location type tags (online, on_request_*, tbd)
        'views/agenda_dasei_menu.xml',  # DA1: DASEi submenu structure
        'views/res_partner_views.xml',
        'views/course_views.xml',  # D3: Course model views
        # TODO: Refactor to crearis_event_package module
        # 'views/product_template_views.xml',
        'views/course_participation_views.xml',
        'views/website_event_templates.xml',  # W3/W4: DASEi event card + detail templates (xpath needs fix)
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'auto_install': False,
}
