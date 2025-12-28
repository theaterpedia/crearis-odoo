# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Agenda DASEi',
    'version': '16.0.1.1.0',
    'summary': 'DASEi-specific partner status, course products, and MDC generation',
    'description': """
DASEi-specific extensions for Crearis Agenda sync.

Features:
- Partner status → domaincode mapping from contacts.Status
- Kursteilnehmer evaluation (Kurs field → dasei1/2/3)
- Computed highest domaincode for login routing
- Sync of plan_kursteilnehmer and contacts
- Course products (M18, N18, ZR, ZT profiles)
- Course-Event mapping (JSONB) from plan_veranstaltungsteilnehmer
- Module progress tracking (A, B, C, D modules)
- REST API for MDC file generation (/api/v1/mdc/*)
- Support for Offenes Programm (standalone events)
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
    'external_dependencies': {
        'python': ['PyYAML'],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'views/product_template_views.xml',
        'views/course_participation_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
