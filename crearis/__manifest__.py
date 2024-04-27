# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Crearis',
    'version': '16.0.1.0.0',
    'summary': 'Episodes and Event-Management',
    'description': """Episodes and Event-Management on theaterpedia.org""",
    'category': 'Website/Crearis',
    'license': 'LGPL-3',
    'application': True,
    'author': 'Theaterpedia',
    'website': 'https://theaterpedia.org/',
    'depends': [
        'website_sale_wishlist',
        'website_sale_delivery',
        'website_mass_mailing',
        'website_sale_loyalty',
        'website_blog',
        'contacts',
        'crm',
        'theme_default',
        'event',
        'event_mail',
        'event_registration_mass_mailing',
        'event_registration_partner_unique',
        'event_session',
        'partner_event',
        'website_event_questions_by_ticket',
    ],
    'data': [
        'security/theaterpedia_security.xml',
        'security/ir.model.access.csv',
        'views/crearis_menu.xml',
        'views/crearis_domainuser_views.xml',
        'views/website_pages_views.xml',
        'views/event_event_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'pre_init_hook': 'pre_init_hook_login_check',
    'post_init_hook': 'post_init_hook_login_convert',
}
