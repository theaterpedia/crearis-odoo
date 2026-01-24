# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Crearis Event Package',
    'version': '16.0.1.0.0',
    'summary': 'Event Package Products for Crearis',
    'description': """
Crearis Event Package - Sell bundled events as products.

Features:
- Product type 'event_package' for bundling multiple events
- Package configuration via event types
- Event selection wizard during purchase
- Package-only events (not sold individually)
- Complete traceability of package event selections

This module provides the general packaging functionality and does NOT depend on
SharePoint sync modules (crearis_agenda, agenda_dasei).
    """,
    'category': 'Website/Crearis',
    'license': 'LGPL-3',
    'application': False,
    'author': 'Theaterpedia',
    'website': 'https://theaterpedia.org/',
    'depends': [
        'crearis',
        'event_sale',
        'sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_company_views.xml',
        'views/res_config_settings_views.xml',
        'views/product_template_views.xml',
        'views/event_event_views.xml',
        'views/sale_order_views.xml',
        'wizard/event_package_configurator_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
