{
    'name': 'Agenda DASEi Accounting',
    'version': '16.0.0.1.0',
    'summary': 'Invoicing defaults and installment wizard for DASEi event courses',
    'description': """
Temporary module providing:
- Fiscal position "Bildungsleistung §4 Nr. 21 UStG" (19% → 0%)
- Product category with income account 4110 (steuerfreie Umsätze)
- Installment wizard on sale.order for splitting into monthly invoices
- Default installment rate per company (res.company field)

Designed for 6-12 week trial, then classify into:
- crearis_accounting (generic: wizard, fiscal position pattern)
- agenda_dasei (DASEi-specific: rate defaults, account mapping)
    """,
    'category': 'Accounting',
    'license': 'LGPL-3',
    'author': 'crearis oHG',
    'depends': [
        'agenda_dasei',          # DASEi products, courses, registrations
        'account',               # Core accounting
        'sale',                  # sale.order for wizard trigger
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/product_category_data.xml',
        'data/product_defaults.xml',
        'wizard/installment_wizard_views.xml',
        'views/sale_order_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'post_init_hook': '_post_init_hook',
    'installable': True,
    'auto_install': False,
}
