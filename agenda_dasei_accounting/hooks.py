import logging
from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def _post_init_hook(cr, registry):
    """Chart-agnostic setup for fiscal position, tax mappings, and accounts.

    Searches for taxes/accounts by amount/code rather than XML IDs,
    so this works with SKR03, SKR04, or any other German chart.
    Iterates all companies that have a chart of accounts configured.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Find companies that actually have accounting (taxes exist)
    cr.execute(
        "SELECT DISTINCT company_id FROM account_tax WHERE company_id IS NOT NULL"
    )
    company_ids = [row[0] for row in cr.fetchall()]
    if not company_ids:
        _logger.warning("No companies with accounting found — skipping hook.")
        return

    companies = env['res.company'].browse(company_ids)
    _logger.info(
        "Running post_init_hook for %d companies: %s",
        len(companies), ', '.join(companies.mapped('name')),
    )

    categ = env.ref(
        'agenda_dasei_accounting.product_category_bildungsleistung',
        raise_if_not_found=False,
    )

    for company in companies:
        _setup_company(env, company, categ)

    _logger.info("agenda_dasei_accounting post_init_hook completed.")


def _setup_company(env, company, categ):
    """Set up fiscal position, tax/account mappings for one company."""
    _logger.info("--- Setting up company %s (id=%d) ---", company.name, company.id)

    Account = env['account.account']
    Tax = env['account.tax']

    # --- 1. Income account: steuerfreie Umsätze Inland ---
    # SKR04: 4110, SKR03: 8110
    account_stfrei = Account.search([
        ('company_id', '=', company.id),
        ('code', 'in', ['8110', '4110']),
        ('account_type', 'in', ['income', 'income_other']),
    ], limit=1)

    if not account_stfrei:
        # Fallback: name-based (handles abbreviation "steuerfr.")
        account_stfrei = Account.search([
            ('company_id', '=', company.id),
            ('name', 'ilike', 'steuerfr'),
            ('name', 'ilike', 'umsätze'),
            ('name', 'ilike', 'inland'),
            ('account_type', 'in', ['income', 'income_other']),
        ], limit=1)

    if account_stfrei and categ:
        categ.with_company(company).property_account_income_categ_id = account_stfrei
        _logger.info(
            "Set income account %s (%s) on category '%s'",
            account_stfrei.code, account_stfrei.name, categ.name,
        )
    elif not account_stfrei:
        _logger.warning(
            "Steuerfreie Umsätze account not found for company %s — "
            "set income account on Bildungsleistungen category manually.",
            company.name,
        )

    # --- 2. Fiscal position: Bildungsleistung §4 Nr. 21 UStG ---
    FiscalPosition = env['account.fiscal.position']
    fp = FiscalPosition.search([
        ('name', '=', 'Bildungsleistung §4 Nr. 21 UStG'),
        ('company_id', '=', company.id),
    ], limit=1)

    if not fp:
        fp = FiscalPosition.create({
            'name': 'Bildungsleistung §4 Nr. 21 UStG',
            'auto_apply': False,
            'sequence': 100,
            'company_id': company.id,
            'note': (
                'Steuerbefreiung gem. §4 Nr. 21 UStG für Leistungen '
                'privater Bildungseinrichtungen mit Bescheinigung der '
                'zuständigen Landesbehörde.'
            ),
        })
        _logger.info("Created fiscal position '%s' for %s", fp.name, company.name)

    # --- 3. Tax mappings: 19% → free, 7% → free ---
    # Standard 19% sale tax
    tax_19 = Tax.search([
        ('type_tax_use', '=', 'sale'),
        ('amount', '=', 19.0),
        ('company_id', '=', company.id),
        ('name', 'ilike', 'umsatzsteuer'),
        ('name', 'not ilike', 'inkludiert'),
        ('name', 'not ilike', 'EU'),
        ('name', 'not ilike', 'farmer'),
        ('name', 'not ilike', 'forstwirtschaft'),
    ], limit=1)
    if not tax_19:
        tax_19 = Tax.search([
            ('type_tax_use', '=', 'sale'),
            ('amount', '=', 19.0),
            ('company_id', '=', company.id),
        ], limit=1)

    # Standard 7% sale tax
    tax_7 = Tax.search([
        ('type_tax_use', '=', 'sale'),
        ('amount', '=', 7.0),
        ('company_id', '=', company.id),
        ('name', 'ilike', 'umsatzsteuer'),
        ('name', 'not ilike', 'inkludiert'),
        ('name', 'not ilike', 'EU'),
    ], limit=1)
    if not tax_7:
        tax_7 = Tax.search([
            ('type_tax_use', '=', 'sale'),
            ('amount', '=', 7.0),
            ('company_id', '=', company.id),
        ], limit=1)

    # §4 Nr. 21 falls under §4 Nr. 8-28 → "ohne Vorsteuerabzug"
    tax_free = Tax.search([
        ('type_tax_use', '=', 'sale'),
        ('amount', '=', 0.0),
        ('company_id', '=', company.id),
        ('name', 'ilike', 'ohne vorsteuerabzug'),
    ], limit=1)
    if not tax_free:
        tax_free = Tax.search([
            ('type_tax_use', '=', 'sale'),
            ('amount', '=', 0.0),
            ('company_id', '=', company.id),
            ('name', 'ilike', 'steuerfrei'),
        ], limit=1)

    FPTax = env['account.fiscal.position.tax']
    for tax_src, label in [(tax_19, '19%'), (tax_7, '7%')]:
        if tax_src and tax_free:
            existing = FPTax.search([
                ('position_id', '=', fp.id),
                ('tax_src_id', '=', tax_src.id),
            ], limit=1)
            if not existing:
                FPTax.create({
                    'position_id': fp.id,
                    'tax_src_id': tax_src.id,
                    'tax_dest_id': tax_free.id,
                })
                _logger.info(
                    "Tax mapping: %s (%s) → %s",
                    tax_src.name, label, tax_free.name,
                )
        else:
            _logger.warning(
                "Could not create %s tax mapping for %s — "
                "tax_src=%s, tax_free=%s. Set up manually.",
                label, company.name, tax_src, tax_free,
            )

    # --- 4. Account mappings: revenue accounts → steuerfreie Umsätze ---
    if account_stfrei:
        FPAccount = env['account.fiscal.position.account']
        for code in ['4400', '8400', '4300', '8300']:
            acc_src = Account.search([
                ('code', '=', code),
                ('company_id', '=', company.id),
            ], limit=1)
            if acc_src and acc_src.id != account_stfrei.id:
                existing = FPAccount.search([
                    ('position_id', '=', fp.id),
                    ('account_src_id', '=', acc_src.id),
                ], limit=1)
                if not existing:
                    FPAccount.create({
                        'position_id': fp.id,
                        'account_src_id': acc_src.id,
                        'account_dest_id': account_stfrei.id,
                    })
                    _logger.info(
                        "Account mapping: %s → %s",
                        acc_src.code, account_stfrei.code,
                    )
