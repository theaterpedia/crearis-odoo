# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Crearis Agenda',
    'version': '16.0.1.0.0',
    'summary': 'SharePoint Agenda Sync for Crearis Events',
    'description': """
Synchronize events and event types between Odoo and Microsoft SharePoint.

Features:
- Sync event types from SharePoint plan_veranstaltungscodes
- Sync events from SharePoint plan_veranstaltungen
- Version-controlled conflict detection (oversion field)
- Three sync levels: init, slave, master
- Template application on event creation
- Hourly cron job for automatic sync
    """,
    'category': 'Website/Crearis',
    'license': 'LGPL-3',
    'application': False,
    'author': 'Theaterpedia',
    'website': 'https://theaterpedia.org/',
    'depends': [
        'crearis',
        'event',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_company_views.xml',
        'views/sync_menu_views.xml',
        'data/cron_data.xml',
    ],
    'installable': True,
    'auto_install': False,
}
