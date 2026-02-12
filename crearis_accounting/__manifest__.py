{
    'name': 'Crearis Accounting',
    'version': '16.0.0.2.0',
    'summary': 'Chart-agnostic accounting: fiscal positions, installment wizard, simple invoicing',
    'description': """
Generic accounting configuration module providing:
- Fiscal position "Bildungsleistung §4 Nr. 21 UStG" (19%/7% → 0%)
- Product category "Bildungsleistungen" with chart-agnostic income account
- Installment wizard on sale.order for splitting into monthly invoices
- Simple invoicing toggle for companies without chart of accounts
- Default installment rate per company (res.company field)

Works with SKR03, SKR04, SKR42, or no chart at all.
    """,
    'category': 'Accounting',
    'license': 'LGPL-3',
    'author': 'crearis oHG',
    'depends': [
        'account',               # Core accounting
        'sale',                  # sale.order for wizard trigger
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/product_category_data.xml',
        'wizard/installment_wizard_views.xml',
        'views/sale_order_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'post_init_hook': '_post_init_hook',
    'installable': True,
    'auto_install': False,
}
