# -*- coding: utf-8 -*-
# Copyright 2026 theaterpedia.org / crearis.io
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
"""
CheckoutMutation for DASEi checkout flow.

Two-tier checkout:
- AUTO (location m/n + flag w/x): Creates partner, sale.order,
  product.package.event.line(s), and event.registration(s).
- MANUAL_REVIEW (z*, module letters c/d/e, single events): Creates partner,
  sends customer confirmation + manager notification emails. No sale.order.

ProductRef format: {location}{cohort}{flag}
- location: m=München, n=Nürnberg, z=zentral
- cohort: 15, 17, 18 (year code)
- flag: w=Tageskurs, x=Block, a-g=module letters

Also accepts: MOD-A style (backwards compat), ra_1373 style (single events).

Usage:
    mutation {
        checkout(checkout: {
            product_ref: "m18w",
            contact: { email: "...", vorname: "...", nachname: "..." },
            accept_terms: true,
            accept_privacy: true,
            accept_cancellation: true
        }) {
            success
            checkoutType
            error
            order { id name }
            partner { id email }
            registrations
            packageLines
        }
    }
"""

import logging
import re

import graphene
from graphql import GraphQLError
from odoo.http import request
from odoo import _

from odoo.addons.graphql_theaterpedia.schemas.objects import Order, Partner

_logger = logging.getLogger(__name__)


def _get_client_ip():
    """Get the real client IP, considering reverse-proxy headers."""
    forwarded_for = request.httprequest.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    real_ip = request.httprequest.headers.get('X-Real-IP')
    if real_ip:
        return real_ip.strip()
    return request.httprequest.remote_addr


# --- Product ref parsing ---

# DEFAULT shortcode mappings (legacy fallback)
# These are overridden by website.shortcode_config when available (I2)

# Flag → Odoo default_code mapping
# For bundles (y/z), see _DEFAULT_BUNDLE_TO_PRODUCTS below
_DEFAULT_FLAG_TO_PRODUCT = {
    # Grundlagen (Module A-D)
    'w': 'MOD-A',  # Tageskurs format → Module A product
    'x': 'MOD-B',  # Block format → Module B product (different price)
    'a': 'MOD-A',
    'b': 'MOD-B',
    'c': 'MOD-C',
    'd': 'MOD-D',
    # Aufbaustufe (Module E+)
    'e': 'MOD-E',           # Vertiefung (Lenka checkout)
    't': 'MOD-AUFBAU-T',    # Profil Theatrales Lernen
    'r': 'MOD-AUFBAU-R',    # Profil Performance & Interkulturell
    'p': 'MOD-AUFBAU-P',    # Berufsabschluss: Kolloquium & Praxis
}

# Bundle shortcodes → multiple products (Mattis/Rike full Aufbau checkout)
# These resolve to 3 products + loyalty discount applied at cart level
_DEFAULT_BUNDLE_TO_PRODUCTS = {
    'y': ['MOD-E', 'MOD-AUFBAU-T', 'MOD-AUFBAU-P'],  # Full Aufbau Profil T
    'z': ['MOD-E', 'MOD-AUFBAU-R', 'MOD-AUFBAU-P'],  # Full Aufbau Profil R
}

# Consultation shortcodes (no product, manual_review only)
# z15v = "Beraten & Ausprobieren" (Rike 3b flow) — contact-only, no sale.order
_DEFAULT_CONTACT_ONLY_FLAGS = {'v'}  # Only for z-location

# Shortcode flag → human-readable title for emails
_FLAG_TO_TITLE = {
    # Grundlagen
    'w': 'Grundlagenbildung Theaterpädagogik (Tageskurs)',
    'x': 'Grundlagenbildung Theaterpädagogik (Blockkurs)',
    'a': 'Modul A: Einstiege ins Theaterspiel',
    'b': 'Modul B: Eine Bühne voll Erfahrung',
    'c': 'Modul C: Szenische Welten',
    'd': 'Modul D: Präsentation',
    # Aufbaustufe
    'e': 'Aufbaustufe Teil 1: Modul E – Vertiefung',
    't': 'Aufbaustufe Profil: Theatrales Lernen',
    'r': 'Aufbaustufe Profil: Performance & Interkulturell',
    'p': 'Aufbaustufe Abschluss: Berufsabschluss (BuT)',
    'y': 'Aufbaustufe komplett: Profil Theatrales Lernen',
    'z': 'Aufbaustufe komplett: Profil Performance & Interkulturell',
    'v': 'Beratung: Aufbaustufe / Beraten & Ausprobieren',
}

# Location → city name for event filtering
_DEFAULT_LOCATION_TO_CITY = {
    'm': 'München',
    'n': 'Nürnberg',
    'z': None,  # zentral (Aufbaustufe) - no city filter
}

# Auto tier: only Module A format variants (w/x) in real locations (m/n)
_DEFAULT_AUTO_FLAGS = {'w', 'x'}
_DEFAULT_AUTO_LOCATIONS = {'m', 'n'}


def _get_shortcode_config(env):
    """Get shortcode config from current website or return defaults.
    
    I2: Per-domain shortcode configuration stored in website.shortcode_config.
    Falls back to hardcoded defaults if no config exists.
    
    Returns dict with keys: products, bundles, contact_only, locations, auto_flags, auto_locations
    """
    website = None
    try:
        website = env['website'].get_current_website()
    except Exception:
        pass  # Not in website context
    
    if website and website.shortcode_config:
        cfg = website.shortcode_config
        # Build config from website JSONB, with defaults for missing keys
        products = {}
        for flag, pdata in cfg.get('products', {}).items():
            if isinstance(pdata, dict):
                products[flag] = pdata.get('default_code', _DEFAULT_FLAG_TO_PRODUCT.get(flag))
            else:
                products[flag] = pdata  # Simple string mapping
        
        bundles = {}
        for flag, bdata in cfg.get('bundles', {}).items():
            if isinstance(bdata, dict):
                bundles[flag] = bdata.get('products', _DEFAULT_BUNDLE_TO_PRODUCTS.get(flag, []))
            else:
                bundles[flag] = bdata  # Direct list
        
        contact_only = set(cfg.get('contact_only', _DEFAULT_CONTACT_ONLY_FLAGS))
        
        locations = {}
        for loc, ldata in cfg.get('locations', {}).items():
            if isinstance(ldata, dict):
                locations[loc] = ldata.get('city')
            else:
                locations[loc] = ldata  # Simple string
        if not locations:
            locations = _DEFAULT_LOCATION_TO_CITY
        
        auto_flags = set(cfg.get('auto_flags', _DEFAULT_AUTO_FLAGS))
        auto_locations = set(cfg.get('auto_locations', _DEFAULT_AUTO_LOCATIONS))
        
        return {
            'products': products if products else _DEFAULT_FLAG_TO_PRODUCT,
            'bundles': bundles if bundles else _DEFAULT_BUNDLE_TO_PRODUCTS,
            'contact_only': contact_only,
            'locations': locations,
            'auto_flags': auto_flags,
            'auto_locations': auto_locations,
            'from_website': True,
        }
    
    # Return defaults
    return {
        'products': _DEFAULT_FLAG_TO_PRODUCT,
        'bundles': _DEFAULT_BUNDLE_TO_PRODUCTS,
        'contact_only': _DEFAULT_CONTACT_ONLY_FLAGS,
        'locations': _DEFAULT_LOCATION_TO_CITY,
        'auto_flags': _DEFAULT_AUTO_FLAGS,
        'auto_locations': _DEFAULT_AUTO_LOCATIONS,
        'from_website': False,
    }


def _parse_product_ref(product_ref, config=None):
    """Parse shortcode into structured checkout info.

    Supports five patterns:
    1. Course shortcode: m18w, n18x, m17c, z15e, z15t, z15r, z15p
    2. Bundle shortcode: z15y (Full Aufbau T), z15z (Full Aufbau R)
    3. Contact-only shortcode: z15v (Beratung, no product)
    4. Single event: ra_1373, la_1560
    5. Direct default_code: MOD-A (backwards compat)

    Args:
        product_ref: Shortcode string to parse
        config: Optional shortcode config dict from _get_shortcode_config().
                If None, uses hardcoded defaults.

    Returns dict with keys:
        location, cohort, flag, default_code, default_codes (for bundles),
        checkout_tier, is_single_event, is_bundle, is_contact_only, city_filter, original_ref
    """
    # Use defaults if no config provided
    if config is None:
        config = {
            'products': _DEFAULT_FLAG_TO_PRODUCT,
            'bundles': _DEFAULT_BUNDLE_TO_PRODUCTS,
            'contact_only': _DEFAULT_CONTACT_ONLY_FLAGS,
            'locations': _DEFAULT_LOCATION_TO_CITY,
            'auto_flags': _DEFAULT_AUTO_FLAGS,
            'auto_locations': _DEFAULT_AUTO_LOCATIONS,
        }
    
    ref = (product_ref or '').strip().lower()

    # Pattern 1+2+3: Course/Bundle/Contact-only shortcode {location}{cohort}{flag}
    match = re.match(r'^([mnz])(\d{2})([a-z])$', ref)
    if match:
        location, cohort, flag = match.groups()
        city_filter = config['locations'].get(location)

        # Check if this is a contact-only shortcode (z15v = "Beraten & Ausprobieren")
        if location == 'z' and flag in config['contact_only']:
            return {
                'location': location,
                'cohort': cohort,
                'flag': flag,
                'default_code': None,  # No product
                'default_codes': None,
                'checkout_tier': 'manual_review',  # Contact-only always manual
                'is_single_event': False,
                'is_bundle': False,
                'is_contact_only': True,  # Tier 3: partner + notification only
                'city_filter': city_filter,
                'original_ref': ref,
            }

        # Check if this is a bundle shortcode (y/z)
        if flag in config['bundles']:
            return {
                'location': location,
                'cohort': cohort,
                'flag': flag,
                'default_code': None,  # No single product
                'default_codes': config['bundles'][flag],  # Multiple products
                'checkout_tier': 'manual_review',  # Bundles need review
                'is_single_event': False,
                'is_bundle': True,
                'city_filter': city_filter,
                'original_ref': ref,
            }

        # Regular product shortcode - BLOCKING VALIDATION (I2)
        default_code = config['products'].get(flag)
        if default_code is None:
            # Flag not in products, bundles, or contact_only → invalid
            # Still include city_filter for schedule resolution (D18)
            return {
                'validation_error': f"Unknown shortcode flag '{flag}' in '{ref}'. "
                                   f"Valid flags: {sorted(config['products'].keys())} (products), "
                                   f"{sorted(config['bundles'].keys())} (bundles), "
                                   f"{sorted(config['contact_only'])} (contact-only)",
                'original_ref': ref,
                'city_filter': city_filter,  # D18: still provide city for schedule filtering
                'location': location,
            }
        tier = 'auto' if (location in config['auto_locations'] and flag in config['auto_flags']) else 'manual_review'
        return {
            'location': location,
            'cohort': cohort,
            'flag': flag,
            'default_code': default_code,
            'default_codes': None,
            'checkout_tier': tier,
            'is_single_event': False,
            'is_bundle': False,
            'city_filter': city_filter,
            'original_ref': ref,
        }

    # Pattern 3: Single event {code}_{id}  e.g. ra_1373, t0_50, x1_45
    # Note: [a-z0-9] to handle event types with digits (T0, R0, X1)
    match = re.match(r'^([a-z0-9]{2})_(\d+)$', ref)
    if match:
        event_code, event_num = match.groups()
        return {
            'location': None,
            'cohort': None,
            'flag': None,
            'default_code': None,
            'default_codes': None,
            'checkout_tier': 'manual_review',
            'is_single_event': True,
            'is_bundle': False,
            'city_filter': None,
            'event_code': event_code,
            'event_num': event_num,
            'original_ref': ref,
        }

    # Pattern 4: Direct default_code (MOD-A, MOD-B etc.) — backwards compat
    return {
        'location': None,
        'cohort': None,
        'flag': None,
        'default_code': ref.upper(),
        'default_codes': None,
        'checkout_tier': 'auto',
        'is_single_event': False,
        'is_bundle': False,
        'city_filter': None,
        'original_ref': ref,
    }


class CheckoutContactInput(graphene.InputObjectType):
    """Contact information for checkout"""
    email = graphene.String(required=True)
    vorname = graphene.String(required=True)
    nachname = graphene.String(required=True)
    strasse = graphene.String()
    plz = graphene.String()
    ort = graphene.String()
    mobil = graphene.String()


class CheckoutInput(graphene.InputObjectType):
    """Input for checkout mutation"""
    product_ref = graphene.String(
        required=True,
        description="Shortcode (m18w, z15e, ra_1373) or default_code (MOD-A)"
    )
    contact = graphene.Field(CheckoutContactInput, required=True)
    notes = graphene.String(description="Optional booking notes")
    accept_terms = graphene.Boolean(required=True)
    accept_privacy = graphene.Boolean(required=True)
    accept_cancellation = graphene.Boolean(required=True)
    request_full_course = graphene.Boolean(
        description="For z15e: interest in full Berufsabschluss (BuT)"
    )


class CheckoutResult(graphene.ObjectType):
    """Result of checkout mutation"""
    success = graphene.Boolean()
    checkout_type = graphene.String(description="'auto' or 'manual_review'")
    order = graphene.Field(Order)
    partner = graphene.Field(Partner)
    registrations = graphene.List(graphene.Int, description="Created event.registration IDs")
    package_lines = graphene.List(graphene.Int, description="Created product.package.event.line IDs")
    error = graphene.String()


class Checkout(graphene.Mutation):
    """
    Two-tier checkout mutation.

    AUTO tier (m/n + w/x): Creates partner → sale.order → package lines →
    registrations → confirmation email.

    MANUAL_REVIEW tier (z*, module flags, single events): Creates partner →
    customer "received" email → manager notification. No sale.order.
    """
    class Arguments:
        checkout = CheckoutInput(required=True)

    Output = CheckoutResult

    @staticmethod
    def mutate(self, info, checkout):
        env = info.context['env']
        website = env['website'].get_current_website()
        request.website = website

        # --- IP lock check ---
        ICP = env['ir.config_parameter'].sudo()
        lock_ip = (ICP.get_param('vsf_checkout_lock_ip', '') or '').strip()
        if lock_ip:
            client_ip = _get_client_ip()
            allowed = {lock_ip, '127.0.0.1', '::1'}
            if client_ip not in allowed:
                _logger.warning(
                    "Checkout blocked: client_ip=%s not in allowed %s",
                    client_ip, allowed,
                )
                return CheckoutResult(
                    success=False,
                    error=_('Checkout not available from this origin'),
                )

        # Validate terms acceptance
        if not all([
            checkout.accept_terms,
            checkout.accept_privacy,
            checkout.accept_cancellation,
        ]):
            return CheckoutResult(
                success=False,
                error=_('All terms must be accepted'),
            )

        # Parse product reference (I2: config from website if available)
        shortcode_config = _get_shortcode_config(env)
        parsed = _parse_product_ref(checkout.product_ref, config=shortcode_config)
        
        # I2: Blocking validation - fail early if shortcode is unknown
        if 'validation_error' in parsed:
            _logger.warning(
                "Checkout validation failed: ref=%s error=%s",
                checkout.product_ref, parsed['validation_error']
            )
            return CheckoutResult(
                success=False,
                error=parsed['validation_error'],
            )
        
        tier = parsed['checkout_tier']
        _logger.info(
            "Checkout: ref=%s tier=%s from_website=%s parsed=%s",
            checkout.product_ref, tier, shortcode_config.get('from_website', False), parsed,
        )

        # Get or create partner (both tiers need this)
        partner = _get_or_create_partner(env, checkout.contact)

        # Store requestFullCourse flag on partner if applicable
        if checkout.request_full_course and parsed.get('flag') == 'e':
            note = "⚑ Interesse am vollständigen Berufsabschluss Theaterpädagogik (BuT)"
            existing_comment = partner.comment or ''
            if note not in existing_comment:
                partner.sudo().write({
                    'comment': (existing_comment + '\n' + note).strip(),
                })
            _logger.info("requestFullCourse set for partner %s", partner.id)

        # --- Dispatch by tier ---
        if tier == 'auto':
            return _checkout_auto(env, website, checkout, parsed, partner)
        else:
            return _checkout_manual_review(env, checkout, parsed, partner)


def _get_or_create_partner(env, contact):
    """Find existing partner by email or create new one."""
    Partner = env['res.partner'].sudo()
    partner = Partner.search([('email', '=ilike', contact.email)], limit=1)

    if not partner:
        partner_vals = {
            'name': f"{contact.vorname} {contact.nachname}".strip(),
            'email': contact.email,
        }
        # Add partner_firstname fields if available
        if hasattr(Partner, 'firstname'):
            partner_vals['firstname'] = contact.vorname
            partner_vals['lastname'] = contact.nachname
        # Add optional fields
        if contact.mobil:
            partner_vals['phone'] = contact.mobil
        if contact.strasse:
            partner_vals['street'] = contact.strasse
        if contact.plz:
            partner_vals['zip'] = contact.plz
        if contact.ort:
            partner_vals['city'] = contact.ort

        partner = Partner.create(partner_vals)
    return partner


def _checkout_auto(env, website, checkout, parsed, partner):
    """AUTO tier: create sale.order + registrations + send confirmation."""
    default_code = parsed.get('default_code')
    if not default_code:
        return CheckoutResult(
            success=False,
            checkout_type='auto',
            error=_('No product mapping for ref: %s') % parsed['original_ref'],
        )

    Product = env['product.template'].sudo()
    product = Product.search([
        ('default_code', '=ilike', default_code),
    ], limit=1)
    if not product:
        return CheckoutResult(
            success=False,
            checkout_type='auto',
            error=_('Product not found: %s (from ref %s)') % (default_code, parsed['original_ref']),
        )

    # Create sale order
    SaleOrder = env['sale.order'].sudo()
    order = SaleOrder.create({
        'partner_id': partner.id,
        'partner_invoice_id': partner.id,
        'partner_shipping_id': partner.id,
        'website_id': website.id,
        'note': checkout.notes or '',
        'order_line': [(0, 0, {
            'product_id': product.product_variant_id.id,
            'product_uom_qty': 1,
            'price_unit': product.list_price,
        })],
    })

    # Confirm order (draft → sent)
    order.action_quotation_sent()

    # Update package event lines + create registrations
    registration_ids = []
    package_line_ids = []

    if product.detailed_type == 'event_package':
        registration_ids, package_line_ids = _process_package_lines(
            env, order, product, partner, parsed.get('city_filter'),
        )

    # Send auto-checkout confirmation email (T2)
    try:
        tpl = env.ref('agenda_dasei.mail_template_checkout_confirmation', raise_if_not_found=False)
        if tpl:
            tpl.sudo().send_mail(order.id, force_send=False)
    except Exception as e:
        _logger.warning("Auto checkout email failed for order %s: %s", order.name, e)

    return CheckoutResult(
        success=True,
        checkout_type='auto',
        order=order,
        partner=partner,
        registrations=registration_ids,
        package_lines=package_line_ids,
    )


def _checkout_manual_review(env, checkout, parsed, partner):
    """MANUAL_REVIEW tier: send customer + manager emails, no sale.order."""

    # Build context info for manager notification
    contact = checkout.contact
    ref = parsed['original_ref']
    notes = checkout.notes or ''
    full_course = getattr(checkout, 'request_full_course', False) or False

    # --- Build product/bundle info for non-single-event checkouts ---
    product_info = {}
    if not parsed.get('is_single_event') and parsed.get('flag'):
        flag = parsed['flag']
        title = _FLAG_TO_TITLE.get(flag, '')
        is_bundle = parsed.get('is_bundle', False)
        cohort = parsed.get('cohort', '')
        location = parsed.get('location', 'z')
        # Build start info: Aufbaustufe courses start in specific cohort year
        cohort_year = f'20{cohort}' if cohort else ''
        product_info = {
            'product_title': title,
            'product_ref': ref.upper(),
            'is_bundle': is_bundle,
            'cohort_year': cohort_year,
            'product_codes': parsed.get('default_codes') or ([parsed.get('default_code')] if parsed.get('default_code') else []),
        }

    # --- Look up event data for single events ---
    event = None
    event_info = {}
    registration = None
    if parsed.get('is_single_event') and parsed.get('event_num'):
        try:
            event_id = int(parsed['event_num'])
            event = env['event.event'].sudo().browse(event_id)
            if event.exists():
                event_info = {
                    'event_id': event.id,
                    'event_name': event.name or '',
                    'event_code': parsed.get('event_code', '').upper(),
                    'event_start': event.date_begin.strftime('%d.%m.%Y %H:%M') if event.date_begin else '',
                    'event_start_date': event.date_begin.strftime('%d.%m.%Y') if event.date_begin else '',
                }
                
                # --- Create event registration (draft state, no confirmation sent) ---
                try:
                    EventRegistration = env['event.registration'].sudo()
                    registration = EventRegistration.create({
                        'event_id': event.id,
                        'partner_id': partner.id,
                        'name': partner.name,
                        'email': partner.email,
                        'phone': partner.phone or '',
                        'mobile': partner.mobile or '',
                        'state': 'draft',  # Unconfirmed - staff will manually confirm
                    })
                    event_info['registration_id'] = registration.id
                    _logger.info(
                        "Created draft registration %s for event %s partner %s",
                        registration.id, event.id, partner.id
                    )
                except Exception as e:
                    _logger.warning("Failed to create registration for event %s: %s", event.id, e)
                    
        except (ValueError, Exception) as e:
            _logger.warning("Could not look up event for ref %s: %s", ref, e)

    # --- Get company phone from website's company ---
    website = env['website'].get_current_website()
    company = website.company_id or env.company
    company_phone = company.phone or '+49 911 7808476'
    # Clean up phone format
    if company_phone.startswith("'"):
        company_phone = company_phone[1:]

    # --- Customer email: "We received your registration" ---
    try:
        tpl = env.ref('agenda_dasei.mail_template_checkout_review_customer', raise_if_not_found=False)
        if tpl:
            # Pass event/product info and company phone as context for template rendering
            ctx = {
                **event_info,
                **product_info,
                'company_phone': company_phone,
                'product_ref': ref,
            }
            tpl.sudo().with_context(ctx).send_mail(partner.id, force_send=False)
    except Exception as e:
        _logger.warning("Manual review customer email failed for partner %s: %s", partner.id, e)

    # --- Manager notification email ---
    try:
        _send_manager_notification(env, partner, parsed, contact, notes, full_course, event_info, company_phone)
    except Exception as e:
        _logger.warning("Manager notification email failed for ref %s: %s", ref, e)

    _logger.info(
        "Manual review checkout completed: ref=%s partner=%s registration=%s",
        ref, partner.id, registration.id if registration else None,
    )

    return CheckoutResult(
        success=True,
        checkout_type='manual_review',
        partner=partner,
        registrations=[registration.id] if registration else [],
    )


def _send_manager_notification(env, partner, parsed, contact, notes, full_course, event_info=None, company_phone=None):
    """Send checkout notification to exec domainusers for the resolved domain.

    Uses agenda_dasei.resolve_checkout_domain_code() to find the target
    domain_code, then queries crearis.domainuser for exec-role users.
    SaaS-ready: reads routing from website.routing_config when available.
    """
    from odoo.addons.agenda_dasei.models.event import resolve_checkout_domain_code

    event_info = event_info or {}
    domain_code = resolve_checkout_domain_code(parsed, env=env)

    DomainUser = env['crearis.domainuser'].sudo()
    exec_users = DomainUser.search([
        ('domain_id.domain_code', '=', domain_code),
        ('role', '=', 'exec'),
        ('active', '=', True),
    ])

    if not exec_users:
        _logger.warning(
            "No exec domainusers for domain_code '%s' — skipping notification (ref=%s)",
            domain_code, parsed['original_ref'],
        )
        return

    manager_emails = exec_users.mapped('user_id.partner_id.email')
    manager_emails = [e for e in manager_emails if e]
    if not manager_emails:
        _logger.warning(
            "Exec domainusers for '%s' have no email — skipping notification",
            domain_code,
        )
        return

    ref = parsed['original_ref']
    flag_info = parsed.get('flag') or 'single event'
    location = parsed.get('location') or '–'
    is_single = parsed.get('is_single_event', False)

    # Build body
    lines = [
        '<div style="font-family: Arial, sans-serif; max-width: 600px; color: #333;">',
        f'<h2 style="color: #8B4513;">Neue Anmeldung — {domain_code} (manuelle Bearbeitung)</h2>',
        '<table style="border-collapse: collapse; width: 100%;">',
    ]

    def _row(label, value):
        return (
            f'<tr><td style="padding: 4px 8px; font-weight: bold; vertical-align: top;">'
            f'{label}</td><td style="padding: 4px 8px;">{value}</td></tr>'
        )

    lines.append(_row('Produkt-Ref', ref))
    # Add event details if available
    if event_info.get('event_name'):
        lines.append(_row('Veranstaltung', event_info['event_name']))
    if event_info.get('event_start'):
        lines.append(_row('Start', event_info['event_start']))
    if is_single:
        lines.append(_row('Typ', 'Einzelveranstaltung'))
        lines.append(_row('Event-Code', parsed.get('event_code', '–')))
        lines.append(_row('Event-Nr', parsed.get('event_num', '–')))
    else:
        lines.append(_row('Typ', 'Kurs'))
        lines.append(_row('Standort', location.upper()))
        lines.append(_row('Flag', flag_info))

    lines.append(_row('Name', f"{contact.vorname} {contact.nachname}"))
    lines.append(_row('E-Mail', contact.email))
    if contact.mobil:
        lines.append(_row('Mobil', contact.mobil))
    if contact.strasse:
        lines.append(_row('Adresse', f"{contact.strasse}, {contact.plz or ''} {contact.ort or ''}"))
    if notes:
        lines.append(_row('Anmerkungen', notes))
    if full_course:
        lines.append(_row('⚑ Berufsabschluss', 'Interesse am vollständigen BuT'))

    lines.append('</table>')
    lines.append(
        f'<p style="margin-top: 15px;">Partner in Odoo: '
        f'<a href="/web#id={partner.id}&model=res.partner&view_type=form">'
        f'{partner.name}</a> (ID {partner.id})</p>'
    )
    lines.append('</div>')

    body_html = '\n'.join(lines)

    # Get email_from from website config (SaaS-ready)
    Website = env['website'].sudo()
    website = Website.search([('domain_code', '=', domain_code)], limit=1)
    email_from = 'service@dasei.eu'  # fallback
    if website and hasattr(website, 'get_config_value'):
        email_from = website.get_config_value('email', 'from', email_from)

    MailMail = env['mail.mail'].sudo()
    MailMail.create({
        'subject': f'[Checkout] Neue Anmeldung: {ref} — {contact.vorname} {contact.nachname}',
        'email_from': email_from,
        'email_to': ', '.join(manager_emails),
        'body_html': body_html,
        'auto_delete': False,
    })


def _process_package_lines(env, order, product, partner, city_filter):
    """Update package event lines and create registrations.

    Returns (registration_ids, package_line_ids).
    """
    PackageEventLine = env['product.package.event.line'].sudo()
    EventEvent = env['event.event'].sudo()
    EventRegistration = env['event.registration'].sudo()

    sale_order_line = order.order_line[0] if order.order_line else False

    existing_lines = PackageEventLine.search([
        ('sale_order_line_id', '=', sale_order_line.id if sale_order_line else False),
        ('state', '=', 'pending'),
    ])

    registration_ids = []
    package_line_ids = []

    for package_line in existing_lines:
        event_type = package_line.event_type_id

        # Build domain for finding events
        domain = [
            ('event_type_id', '=', event_type.id),
            ('stage_id.pipe_end', '=', False),
        ]
        if product.package_date_start:
            domain.append(('date_begin', '>=', product.package_date_start))
        if product.package_date_end:
            domain.append(('date_end', '<=', product.package_date_end))

        # Apply city filter from parsed shortcode
        if city_filter:
            domain.append(('address_id.city', 'ilike', city_filter))

        event = EventEvent.search(domain, order='date_begin asc', limit=1)

        if event:
            update_vals = {
                'event_id': event.id,
                'state': 'selected',
            }

            existing_reg = EventRegistration.search([
                ('partner_id', '=', partner.id),
                ('event_id', '=', event.id),
            ], limit=1)

            if not existing_reg:
                # NOTE: Don't pass sale_order_line_id here!
                # event_sale's EventRegistration.create() would overwrite our
                # event_id with so_line.event_id (which is False for
                # event_package products).
                registration = EventRegistration.create({
                    'partner_id': partner.id,
                    'event_id': event.id,
                    'sale_order_id': order.id,
                })
                registration_ids.append(registration.id)
                update_vals['registration_id'] = registration.id
                update_vals['state'] = 'registered'
            else:
                registration_ids.append(existing_reg.id)
                update_vals['registration_id'] = existing_reg.id
                update_vals['state'] = 'registered'

            package_line.write(update_vals)

        package_line_ids.append(package_line.id)

    return registration_ids, package_line_ids


class CheckoutMutation(graphene.ObjectType):
    checkout = Checkout.Field(description="Complete checkout with partner, order, and registrations")
