# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Agenda DASEi',
    'version': '16.0.1.5.0',
    'summary': 'DASEi-specific partner status, course products, domain config, and MDC generation',
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
- Event registration sync from plan_veranstaltungsteilnehmer
- Status mapping: SharePoint StatusLookupId → Odoo registration state
- Auto-creates DASEi websites (dasei0, dasei1, dasei2, dasei3) on install
- Domain configuration: config_preset='academy', routing + email overrides
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
        'crearis_accounting',     # Fiscal position, Bildungsleistungen category
        'crearis_event_package',  # For event package products
        'crearis_milestones',     # For milestone labels and Controlling UI
        'portal',                 # For customer portal
        'product',
        'event',
        'website_event',          # For website event templates
        'website_sale_loyalty',   # For Aufbaustufe Komplett bundle discount
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',  # D6: Cron jobs for course and registration sync
        'data/website_data.xml',  # DASEi website check/create server actions
        'data/milestone_defaults.xml',  # German milestone labels and defaults
        'data/product_template_data.xml',  # Grundkurs module products (A, B, C, D)
        'data/product_defaults.xml',  # Assign Bildungsleistungen category to course products
        'data/event_tag_data.xml',  # Location type tags (online, on_request_*, tbd)
        'data/loyalty_aufbaustufe_komplett.xml',  # SAC: Aufbaustufe bundle discount
        'data/mail_template_checkout.xml',  # T2: Checkout confirmation email template
        'data/mail_template_checkout_review.xml',  # Manual review tier email template
        'views/agenda_dasei_menu.xml',  # DA1: DASEi submenu structure
        'views/res_partner_views.xml',
        'views/course_views.xml',  # D3: Course model views
        'views/portal_templates.xml',  # SDC: Customer portal (Agenda/Service/Curriculum tabs)
        # TODO: Refactor to crearis_event_package module
        # 'views/product_template_views.xml',
        'views/course_participation_views.xml',
        # TODO: Fix xpath - Odoo 16 events_list structure changed
        # 'views/website_event_templates.xml',  # W3/W4: DASEi event card + detail templates
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'auto_install': False,
}
