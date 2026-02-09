# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

# Required domain codes for DASEi progression system
DASEI_DOMAIN_CODES = {
    'dasei0': {
        'name': 'DASEi Quick Entry',
        'sequence': 100,
        'description': 'Pre-registration, prospects - public landing page',
    },
    'dasei1': {
        'name': 'DASEi Einstiege',
        'sequence': 101,
        'description': 'Entry modules (ME, NE) - new participants',
    },
    'dasei2': {
        'name': 'DASEi Grundstufe',
        'sequence': 102,
        'description': 'Core modules (A-F) - active trainees',
    },
    'dasei3': {
        'name': 'DASEi Aufbaustufe',
        'sequence': 103,
        'description': 'Advanced modules (G, H, J, L) - advanced trainees',
    },
}


def post_init_hook(cr, registry):
    """
    After module installation, check for required DASEi websites.
    Creates them if they don't exist, then links products to websites.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    _check_and_create_dasei_websites(env)
    _link_products_to_websites(env)


def _check_and_create_dasei_websites(env):
    """
    Check if required DASEi domain code websites exist.
    Creates missing ones linked to the DASEi company.
    
    Required websites: dasei0, dasei1, dasei2, dasei3
    (The main 'dasei' website should already exist)
    """
    Website = env['website']
    Company = env['res.company']
    
    # Find DASEi company (search by various name patterns)
    dasei_company = Company.search([
        '|', '|',
        ('name', 'ilike', 'das ei'),
        ('name', 'ilike', 'dasei'),
        ('name', 'ilike', 'DAS Ei')
    ], limit=1)
    if not dasei_company:
        _logger.warning(
            "agenda_dasei: No company with 'DAS Ei' or 'dasei' in name found. "
            "DASEi websites will not be auto-created. "
            "Please create them manually or ensure a DASEi company exists."
        )
        return
    
    # Check existing websites
    existing_codes = set(Website.search([]).mapped('domain_code'))
    missing_codes = []
    
    for code in DASEI_DOMAIN_CODES:
        if code not in existing_codes:
            missing_codes.append(code)
    
    if not missing_codes:
        _logger.info("agenda_dasei: All required DASEi websites exist (dasei0-3)")
        return
    
    _logger.info(
        "agenda_dasei: Creating missing DASEi websites: %s", 
        ', '.join(missing_codes)
    )
    
    # Create missing websites
    for code in missing_codes:
        config = DASEI_DOMAIN_CODES[code]
        website = Website.create({
            'name': config['name'],
            'domain_code': code,
            'company_id': dasei_company.id,
            'sequence': config.get('sequence', 10),
        })
        # Create XMLId for the website
        _ensure_xmlid(env, 'website', website.id, f'website_{code}')
        _logger.info("agenda_dasei: Created website '%s' (%s)", config['name'], code)


def _ensure_xmlid(env, model, res_id, xmlid_name):
    """Helper to create XMLId in agenda_dasei module"""
    IrModelData = env['ir.model.data']
    existing = IrModelData.search([
        ('module', '=', 'agenda_dasei'),
        ('name', '=', xmlid_name),
    ], limit=1)
    if not existing:
        IrModelData.create({
            'module': 'agenda_dasei',
            'name': xmlid_name,
            'model': model,
            'res_id': res_id,
            'noupdate': True,
        })


# Product to website mapping (XMLId suffix → domain_code)
PRODUCT_WEBSITE_MAP = {
    'product_modul_a': 'dasei1',  # Modul A sold on Einstiege
    'product_modul_b': 'dasei2',  # Modul B sold on Grundstufe
    'product_modul_c': 'dasei2',  # Modul C sold on Grundstufe
    'product_modul_d': 'dasei2',  # Modul D sold on Grundstufe
}


def _link_products_to_websites(env):
    """
    Link module products to their respective DASEi websites.
    Called after websites are created to set the website_id field.
    """
    Website = env['website']
    Product = env['product.template']
    
    # Build domain_code → website mapping
    websites = Website.search([('domain_code', 'in', ['dasei1', 'dasei2'])])
    website_by_code = {w.domain_code: w for w in websites}
    
    if not website_by_code:
        _logger.warning("agenda_dasei: No DASEi websites found, skipping product linking")
        return
    
    linked_count = 0
    for product_xmlid, domain_code in PRODUCT_WEBSITE_MAP.items():
        website = website_by_code.get(domain_code)
        if not website:
            _logger.warning(
                "agenda_dasei: Website %s not found, skipping product %s",
                domain_code, product_xmlid
            )
            continue
        
        # Try to find the product by XMLId
        try:
            product = env.ref(f'agenda_dasei.{product_xmlid}', raise_if_not_found=False)
            if product and not product.website_id:
                product.website_id = website.id
                linked_count += 1
                _logger.debug(
                    "agenda_dasei: Linked %s to website %s",
                    product.name, domain_code
                )
        except Exception as e:
            _logger.warning(
                "agenda_dasei: Could not link %s to website: %s",
                product_xmlid, str(e)
            )
    
    if linked_count:
        _logger.info("agenda_dasei: Linked %d products to DASEi websites", linked_count)


def check_dasei_websites(env, raise_error=False):
    """
    Utility function to check DASEi website status.
    Can be called from shell or other code.
    
    Usage:
        from odoo.addons.agenda_dasei.hooks import check_dasei_websites
        check_dasei_websites(env)  # logs status
        check_dasei_websites(env, raise_error=True)  # raises if missing
    
    Returns:
        dict: {
            'ok': bool,
            'existing': [list of existing codes],
            'missing': [list of missing codes],
            'message': str
        }
    """
    Website = env['website']
    
    existing_websites = Website.search([('domain_code', 'in', list(DASEI_DOMAIN_CODES.keys()))])
    existing_codes = set(existing_websites.mapped('domain_code'))
    missing_codes = [c for c in DASEI_DOMAIN_CODES if c not in existing_codes]
    
    result = {
        'ok': len(missing_codes) == 0,
        'existing': list(existing_codes),
        'missing': missing_codes,
    }
    
    if result['ok']:
        result['message'] = "All DASEi websites exist: " + ', '.join(sorted(existing_codes))
        _logger.info("agenda_dasei: %s", result['message'])
    else:
        result['message'] = (
            f"Missing DASEi websites: {', '.join(missing_codes)}\n\n"
            "To create them, run in Odoo shell:\n"
            "    from odoo.addons.agenda_dasei.hooks import create_dasei_websites\n"
            "    create_dasei_websites(env)\n\n"
            "Or manually create websites with domain_code: " + ', '.join(missing_codes)
        )
        _logger.warning("agenda_dasei: %s", result['message'])
        
        if raise_error:
            from odoo.exceptions import UserError
            raise UserError(result['message'])
    
    return result


def create_dasei_websites(env, company=None):
    """
    Manually create missing DASEi websites.
    
    Usage from Odoo shell:
        from odoo.addons.agenda_dasei.hooks import create_dasei_websites
        create_dasei_websites(env)
        # or with specific company:
        create_dasei_websites(env, env.ref('base.main_company'))
    
    Args:
        env: Odoo environment
        company: res.company record (optional, auto-detects DASEi company)
    
    Returns:
        list: Created website records
    """
    Website = env['website']
    
    if not company:
        company = env['res.company'].search([
            '|', '|',
            ('name', 'ilike', 'das ei'),
            ('name', 'ilike', 'dasei'),
            ('name', 'ilike', 'DAS Ei')
        ], limit=1)
        if not company:
            raise ValueError(
                "No DASEi company found. Please pass company explicitly:\n"
                "    create_dasei_websites(env, env['res.company'].browse(COMPANY_ID))"
            )
    
    existing_codes = set(Website.search([]).mapped('domain_code'))
    created = []
    
    for code, config in DASEI_DOMAIN_CODES.items():
        if code in existing_codes:
            _logger.info("agenda_dasei: Website '%s' already exists, skipping", code)
            continue
        
        website = Website.create({
            'name': config['name'],
            'domain_code': code,
            'company_id': company.id,
            'sequence': config.get('sequence', 10),
        })
        created.append(website)
        _logger.info("agenda_dasei: Created website '%s' (%s)", config['name'], code)
    
    if created:
        _logger.info("agenda_dasei: Created %d websites", len(created))
    else:
        _logger.info("agenda_dasei: All DASEi websites already exist")
    
    return created


def ensure_event_type_xmlids(env, company=None):
    """
    Create XMLIDs for all event.type records belonging to DASEi company.
    XMLIDs follow pattern: agenda_dasei.event_type_{lowercase_name}
    
    This should be called after syncing event types from SharePoint.
    
    Usage from Odoo shell:
        from odoo.addons.agenda_dasei.hooks import ensure_event_type_xmlids
        ensure_event_type_xmlids(env)
    
    Args:
        env: Odoo environment
        company: res.company record (optional, auto-detects DASEi company)
    
    Returns:
        dict: {'created': int, 'existing': int, 'skipped': int}
    """
    EventType = env['event.type']
    IrModelData = env['ir.model.data']
    
    if not company:
        company = env['res.company'].search([
            '|', '|',
            ('name', 'ilike', 'das ei'),
            ('name', 'ilike', 'dasei'),
            ('name', 'ilike', 'DAS Ei')
        ], limit=1)
        if not company:
            _logger.warning("ensure_event_type_xmlids: No DASEi company found")
            return {'created': 0, 'existing': 0, 'skipped': 0}
    
    # Get all event types for this company (synced from SharePoint)
    event_types = EventType.search([
        ('company_id', '=', company.id),
        ('ms_id', '!=', False),  # Only synced records
    ])
    
    stats = {'created': 0, 'existing': 0, 'skipped': 0}
    
    for et in event_types:
        # Get the event type name (handle translated field)
        name = et.name
        if not name:
            stats['skipped'] += 1
            continue
        
        # Generate xmlid name: event_type_a1, event_type_b2, etc.
        # Normalize: lowercase, replace special chars with underscore
        xmlid_name = 'event_type_' + name.lower().replace(' ', '_').replace('-', '_').replace('/', '_')
        
        # Check if xmlid already exists
        existing = IrModelData.search([
            ('module', '=', 'agenda_dasei'),
            ('name', '=', xmlid_name),
        ], limit=1)
        
        if existing:
            # Verify it points to the correct record
            if existing.res_id == et.id and existing.model == 'event.type':
                stats['existing'] += 1
            else:
                # XMLId exists but points elsewhere - update it
                existing.write({'res_id': et.id, 'model': 'event.type'})
                stats['created'] += 1
                _logger.info("Updated XMLId agenda_dasei.%s -> event.type(%s)", xmlid_name, et.id)
        else:
            # Create new xmlid
            IrModelData.create({
                'module': 'agenda_dasei',
                'name': xmlid_name,
                'model': 'event.type',
                'res_id': et.id,
                'noupdate': True,
            })
            stats['created'] += 1
            _logger.debug("Created XMLId agenda_dasei.%s -> event.type(%s) '%s'", xmlid_name, et.id, name)
    
    _logger.info(
        "ensure_event_type_xmlids: created=%d, existing=%d, skipped=%d",
        stats['created'], stats['existing'], stats['skipped']
    )
    
    return stats
