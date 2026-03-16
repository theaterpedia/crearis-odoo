# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Crearis',
    'version': '16.0.1.8.0',
    'summary': 'Episodes and Event-Management with Agenda Lines',
    'description': """Episodes and Event-Management on theaterpedia.org

Features:
- Unified agenda.line model (renamed from event.session.line)
- Five line types: session, meeting, milestone, info, action
- Three providers: event, post, product
- Gate pattern for milestone tracking (pending → ready → sent)
- Configurable milestone labels per company
- Daily cron for milestone date checking
- Schedule template system (Phase 5): event types define session patterns
- Template generation with consecutive days algorithm (D8 pattern)
""",
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
        'partner_firstname',
        'crm',
        'theme_default',
        'event',
        'event_mail',
        'event_registration_mass_mailing',
        'event_registration_qr_code',
        'event_registration_partner_unique',
        'website_event_track',
        'event_session',
        'partner_event',
        'website_event_questions_by_ticket',
    ],
    'data': [
        'data/ir_config_parameter_data.xml',
        'data/ir_cron_data.xml',
        'data/event_stage_data.xml',
        'data/event_type_data.xml',
        'data/calendar_event_type_data.xml',  # SCS: Consulting slot category
        'data/crm_tag_consulting_data.xml',  # S2L: Consulting category tags
        'data/mail_activity_consulting_data.xml',  # S2L: Consulting activity types
        'data/mail_template_consulting_data.xml',  # SCS: Consulting booking emails
        'security/theaterpedia_security.xml',
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/res_company_views.xml',
        'views/config_template_views.xml',
        'views/event_track_location_views.xml',
        'views/res_partner_views.xml',
        'views/res_partner.xml',
        'views/crearis_domainuser_views.xml',
        'views/crearis_version_views.xml',
        'views/website_pages_views.xml',
        'views/event_event_views.xml',
        'views/event_schedule_views.xml',
        'views/agenda_line_views.xml',
        'views/crm_lead_views.xml',  # S2L: Consulting inquiries (before menu)
        'views/crearis_menu.xml',  # Menu items (load after actions)
        'views/event_type_views.xml',
        'views/consulting_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'crearis/static/src/js/json_field.js',
            'crearis/static/src/scss/demo_ribbon.scss',
        ],
    },
    'installable': True,
    'auto_install': False,
    'pre_init_hook': 'pre_init_hook_login_check',
    'post_init_hook': 'post_init_hook_login_convert',
}
