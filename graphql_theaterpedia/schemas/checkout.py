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

# Flag → Odoo default_code mapping
# For bundles (y/z), see _BUNDLE_TO_PRODUCTS below
_FLAG_TO_PRODUCT = {
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
_BUNDLE_TO_PRODUCTS = {
    'y': ['MOD-E', 'MOD-AUFBAU-T', 'MOD-AUFBAU-P'],  # Full Aufbau Profil T
    'z': ['MOD-E', 'MOD-AUFBAU-R', 'MOD-AUFBAU-P'],  # Full Aufbau Profil R
}

# Location → city name for event filtering
_LOCATION_TO_CITY = {
    'm': 'München',
    'n': 'Nürnberg',
    'z': None,  # zentral (Aufbaustufe) - no city filter
}

# Auto tier: only Module A format variants (w/x) in real locations (m/n)
_AUTO_FLAGS = {'w', 'x'}
_AUTO_LOCATIONS = {'m', 'n'}


def _parse_product_ref(product_ref):
    """Parse shortcode into structured checkout info.

    Supports four patterns:
    1. Course shortcode: m18w, n18x, m17c, z15e, z15t, z15r, z15p
    2. Bundle shortcode: z15y (Full Aufbau T), z15z (Full Aufbau R)
    3. Single event: ra_1373, la_1560
    4. Direct default_code: MOD-A (backwards compat)

    Returns dict with keys:
        location, cohort, flag, default_code, default_codes (for bundles),
        checkout_tier, is_single_event, is_bundle, city_filter, original_ref
    """
    ref = (product_ref or '').strip().lower()

    # Pattern 1+2: Course/Bundle shortcode {location}{cohort}{flag}
    match = re.match(r'^([mnz])(\d{2})([a-z])$', ref)
    if match:
        location, cohort, flag = match.groups()
        city_filter = _LOCATION_TO_CITY.get(location)

        # Check if this is a bundle shortcode (y/z)
        if flag in _BUNDLE_TO_PRODUCTS:
            return {
                'location': location,
                'cohort': cohort,
                'flag': flag,
                'default_code': None,  # No single product
                'default_codes': _BUNDLE_TO_PRODUCTS[flag],  # Multiple products
                'checkout_tier': 'manual_review',  # Bundles need review
                'is_single_event': False,
                'is_bundle': True,
                'city_filter': city_filter,
                'original_ref': ref,
            }

        # Regular product shortcode
        default_code = _FLAG_TO_PRODUCT.get(flag)
        tier = 'auto' if (location in _AUTO_LOCATIONS and flag in _AUTO_FLAGS) else 'manual_review'
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

    # Pattern 3: Single event {code}_{id}  e.g. ra_1373
    match = re.match(r'^([a-z]{2})_(\d+)$', ref)
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

        # Parse product reference
        parsed = _parse_product_ref(checkout.product_ref)
        tier = parsed['checkout_tier']
        _logger.info(
            "Checkout: ref=%s tier=%s parsed=%s",
            checkout.product_ref, tier, parsed,
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
            # Pass event info and company phone as context for template rendering
            ctx = {
                **event_info,
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
    """
    from odoo.addons.agenda_dasei.models.event import resolve_checkout_domain_code

    event_info = event_info or {}
    domain_code = resolve_checkout_domain_code(parsed)

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

    MailMail = env['mail.mail'].sudo()
    MailMail.create({
        'subject': f'[Checkout] Neue Anmeldung: {ref} — {contact.vorname} {contact.nachname}',
        'email_from': 'service@dasei.eu',
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
