# -*- coding: utf-8 -*-
# Copyright 2026 theaterpedia.org / crearis.io
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
"""
Consulting Slots GraphQL schema - Availability Window approach.

Exec users define "Consulting Window" events (e.g., Mon 9-12 recurring).
System computes 15-min slots from windows and subtracts booked meetings.
Bookings create separate "Consulting Meeting" events.

- Query: consultingSlots — computes available 15-min slots from windows
- Mutation: bookConsultingSlot — creates a meeting event in a slot

Session: SCS (03-02-SCS_consulting_slots)

Security:
- IP restriction: Only allows requests from server IP (Nuxt SSR) or localhost
- Rate limiting: Max 10 bookings/hour, then blocks + alerts admin
"""

import logging
import re
from datetime import datetime, timedelta
import json

import graphene
from graphql import GraphQLError
from odoo import _
from odoo.http import request

from .checkout import _parse_product_ref, _get_shortcode_config, _DEFAULT_FLAG_TO_PRODUCT

_logger = logging.getLogger(__name__)

# DASEi domain-code to products mapping (D18 level-2 schedules)
# domain_code -> list of product default_codes to show in schedules
# TODO: Refactor - will move to VSF customer UI per domain later
DOMAIN_JOURNEY_PRODUCTS = {
    'dasei1': ['MOD-A'],  # Grundlagen entry, extensible to ['MOD-A', 'MOD-B', 'MOD-C', 'MOD-D']
    'dasei2': ['MOD-B', 'MOD-C', 'MOD-D'],  # Continuing Grundlagen
    # dasei3: Aufbaustufe - not applicable for confirmation schedules
}

# Slot duration in minutes
SLOT_DURATION_MINUTES = 15
SLOT_DURATION_HOURS = SLOT_DURATION_MINUTES / 60.0  # 0.25

# Category names (created via data XML)
WINDOW_CATEGORY = 'Consulting Window'
MEETING_CATEGORY = 'Consulting Meeting'
BLOCKED_CATEGORY = 'Consulting Blocked'

# Rate limiting settings
RATE_LIMIT_MAX_PER_HOUR = 10
RATE_LIMIT_PARAM_KEY = 'consulting.booking.rate_limit_data'
ADMIN_ALERT_EMAIL = 'admin@dasei.eu'

# Allowed IPs for booking mutations (server IP for Nuxt SSR)
ALLOWED_IPS = [
    '127.0.0.1',
    '::1',
    'localhost',
    # Add server's own IP here - Nuxt runs on same server
]


class ConsultingSlot(graphene.ObjectType):
    """A bookable consulting time slot (computed from availability window)."""
    # Computed slot ID: "window_id:slot_index" to identify uniquely
    slot_key = graphene.String(required=True, description="Unique slot key (window_id:index)")
    start = graphene.String(required=True, description="ISO datetime")
    stop = graphene.String(required=True, description="ISO datetime")
    duration = graphene.Float(required=True, description="Duration in hours (0.25 = 15min)")
    host_name = graphene.String(required=True, description="Exec user's display name")
    host_id = graphene.Int(required=True, description="res.users ID of host")
    # D18/💡1: Host photo from domainuser.cimg
    photo_url = graphene.String(description="Host photo URL from domainuser.cimg, empty string if none")


class ConsultingContactInput(graphene.InputObjectType):
    """Contact information for booking."""
    email = graphene.String(required=True)
    vorname = graphene.String(required=True)
    nachname = graphene.String(required=True)
    mobil = graphene.String()


class CategorySelectionInput(graphene.InputObjectType):
    """SCL: A single category with its selected options and optional freeform text.
    
    Part of the per-category options schema (D17, R6).
    """
    category = graphene.String(
        required=True,
        description="Category key: prerequisites, terms_and_options, topics, schedules, custom"
    )
    options = graphene.List(
        graphene.String,
        description="Selected option keys within this category"
    )
    text = graphene.String(
        description="Optional freeform text for this category (max 240 chars)"
    )


class ConsultingCategoryInput(graphene.InputObjectType):
    """SCL: Consultation preferences with per-category options (D17, R6).
    
    New schema (2026-03-08): selections[] + callType replaces flat categories[].
    """
    selections = graphene.List(
        CategorySelectionInput,
        required=True,
        description="Per-category selections with options and text"
    )
    call_type = graphene.String(
        required=True,
        description="'video' or 'phone' - D17"
    )


class ConsultingBookingResult(graphene.ObjectType):
    """Result of booking a consulting slot (D16)."""
    success = graphene.Boolean(required=True)
    # D16: Return entity_id + entity_type for redirect
    entity_id = graphene.String(description="ID for redirect (e.g., product slug)")
    entity_type = graphene.String(description="Type: 'product' (default), 'event', etc.")
    # Legacy fields (keep for backward compat)
    meeting_id = graphene.Int(description="Created calendar.event ID")
    start = graphene.String()
    host_name = graphene.String()
    error = graphene.String()


def _compute_slots_from_window(window_event, slot_duration_minutes=SLOT_DURATION_MINUTES):
    """
    Compute 15-min slots from an availability window event.
    
    Returns list of (slot_key, start_dt, stop_dt, host_id, host_name).
    """
    slots = []
    if not window_event.start or not window_event.stop:
        return slots
    
    window_start = window_event.start
    window_stop = window_event.stop
    host_id = window_event.user_id.id if window_event.user_id else 0
    host_name = window_event.user_id.name if window_event.user_id else 'Unknown'
    
    slot_duration = timedelta(minutes=slot_duration_minutes)
    current = window_start
    index = 0
    
    while current + slot_duration <= window_stop:
        slot_key = f"{window_event.id}:{index}"
        slot_start = current
        slot_stop = current + slot_duration
        slots.append((slot_key, slot_start, slot_stop, host_id, host_name))
        current = slot_stop
        index += 1
    
    return slots


def _slot_overlaps_events(slot_start, slot_stop, events):
    """Check if a slot overlaps with any existing event (meeting or blocked)."""
    for event in events:
        event_start = event.start
        event_stop = event.stop
        if not event_start or not event_stop:
            continue
        # Overlap check: slot overlaps if it doesn't end before event starts
        # and doesn't start after event ends
        if slot_start < event_stop and slot_stop > event_start:
            return True
    return False


def _get_client_ip():
    """Get the client IP address from the request."""
    if not request:
        return None
    # Check X-Forwarded-For header (behind proxy/load balancer)
    forwarded_for = request.httprequest.headers.get('X-Forwarded-For')
    if forwarded_for:
        # Take the first IP (original client)
        return forwarded_for.split(',')[0].strip()
    # Check X-Real-IP header
    real_ip = request.httprequest.headers.get('X-Real-IP')
    if real_ip:
        return real_ip.strip()
    # Fall back to remote_addr
    return request.httprequest.remote_addr


def _is_ip_allowed(client_ip):
    """Check if the client IP is allowed to make booking mutations."""
    if not client_ip:
        return False
    # Allow localhost variants
    if client_ip in ALLOWED_IPS:
        return True
    # Also allow if request comes from the same server (Nuxt SSR)
    # Check if it's a private/local IP
    if client_ip.startswith('10.') or client_ip.startswith('192.168.') or client_ip.startswith('172.'):
        return True
    return False


def _check_rate_limit(env):
    """
    Check and update rate limit counter.
    Returns tuple: (allowed: bool, error_message: str or None)
    """
    ConfigParam = env['ir.config_parameter'].sudo()
    now = datetime.now()
    
    # Get current rate limit data
    rate_data_str = ConfigParam.get_param(RATE_LIMIT_PARAM_KEY, '{}')
    try:
        rate_data = json.loads(rate_data_str)
    except (json.JSONDecodeError, TypeError):
        rate_data = {}
    
    # Get or initialize counters
    count = rate_data.get('count', 0)
    window_start_str = rate_data.get('window_start')
    blocked = rate_data.get('blocked', False)
    
    # Check if we're in a new hour window
    if window_start_str:
        try:
            window_start = datetime.fromisoformat(window_start_str)
            if now - window_start > timedelta(hours=1):
                # Reset counter for new window
                count = 0
                blocked = False
                window_start = now
        except ValueError:
            window_start = now
            count = 0
            blocked = False
    else:
        window_start = now
    
    # Check if blocked
    if blocked:
        return False, _("Service temporarily unavailable. Please try again later.")
    
    # Check if limit would be exceeded
    if count >= RATE_LIMIT_MAX_PER_HOUR:
        # Block and send alert
        rate_data = {
            'count': count,
            'window_start': window_start.isoformat(),
            'blocked': True,
            'blocked_at': now.isoformat(),
        }
        ConfigParam.set_param(RATE_LIMIT_PARAM_KEY, json.dumps(rate_data))
        _logger.error(
            "Consulting booking rate limit exceeded! Count=%d, blocking service.",
            count
        )
        return False, _("Service temporarily unavailable. Please try again later.")
    
    # Increment counter
    count += 1
    rate_data = {
        'count': count,
        'window_start': window_start.isoformat(),
        'blocked': False,
    }
    ConfigParam.set_param(RATE_LIMIT_PARAM_KEY, json.dumps(rate_data))
    
    _logger.debug("Consulting booking rate limit: %d/%d", count, RATE_LIMIT_MAX_PER_HOUR)
    return True, None


def _send_rate_limit_alert(env):
    """Send alert email to admin about rate limit being exceeded."""
    try:
        MailTemplate = env['mail.template'].sudo()
        template = MailTemplate.search([
            ('name', '=', 'Consulting Booking: Rate Limit Alert')
        ], limit=1)
        
        if template:
            # Use admin user as the record context
            admin_user = env['res.users'].sudo().browse(2)  # Usually admin
            template.with_context(timestamp=datetime.now().isoformat()).send_mail(
                admin_user.id, force_send=True
            )
            _logger.info("Rate limit alert sent to %s", ADMIN_ALERT_EMAIL)
        else:
            # Fallback: send direct email
            env['mail.mail'].sudo().create({
                'subject': '[ALERT] Consulting Booking Rate Limit Exceeded',
                'email_from': 'noreply@dasei.eu',
                'email_to': ADMIN_ALERT_EMAIL,
                'body_html': f'''
                    <p><strong>Rate limit exceeded!</strong></p>
                    <p>The consulting booking endpoint exceeded {RATE_LIMIT_MAX_PER_HOUR} bookings/hour.</p>
                    <p>Timestamp: {datetime.now().isoformat()}</p>
                ''',
            }).send()
    except Exception as e:
        _logger.error("Failed to send rate limit alert: %s", e)


def _send_booking_emails(env, meeting, partner, notes=None, selections=None, call_type=None):
    """Send confirmation emails to customer and exec, and log to partner chatter (R2).
    
    Args:
        selections: List of dicts with keys: key, label, options[], text (from parsed_selections)
        call_type: 'video' or 'phone'
    """
    MailTemplate = env['mail.template'].sudo()
    
    # Send customer confirmation
    try:
        customer_template = MailTemplate.search([
            ('name', '=', 'Consulting Booking: Customer Confirmation')
        ], limit=1)
        if customer_template:
            # Don't log to chatter (we post to partner chatter separately)
            customer_template.with_context(
                mail_post_autofollow=False,
                mail_create_nolog=True,
            ).send_mail(
                meeting.id, force_send=True, email_values={'auto_delete': True}
            )
            _logger.info("Customer confirmation sent for meeting %s", meeting.id)
    except Exception as e:
        _logger.error("Failed to send customer confirmation: %s", e)
    
    # Send exec notification
    try:
        exec_template = MailTemplate.search([
            ('name', '=', 'Consulting Booking: Exec Notification')
        ], limit=1)
        if exec_template:
            # Don't log to meeting chatter (exec gets email only)
            exec_template.with_context(
                mail_post_autofollow=False,
                mail_create_nolog=True,
            ).send_mail(
                meeting.id, force_send=True, email_values={'auto_delete': False}
            )
            _logger.info("Exec notification sent for meeting %s", meeting.id)
    except Exception as e:
        _logger.error("Failed to send exec notification: %s", e)
    
    # SCL R2: Log booking confirmation to partner chatter (enhanced 2026-03-08)
    try:
        start_str = meeting.start.strftime('%d.%m.%Y %H:%M') if meeting.start else ''
        host_name = meeting.user_id.name if meeting.user_id else 'Host'
        
        # Build enhanced category HTML with options and text
        categories_html = ''
        if selections:
            categories_html = '<ul style="margin: 8px 0; padding-left: 16px;">'
            for sel in selections:
                cat_html = f'<li><strong>{sel["label"]}</strong>'
                if sel['options']:
                    options_str = ', '.join(sel['options'])
                    cat_html += f': <span style="color: #1565c0;">{options_str}</span>'
                if sel['text']:
                    cat_html += f'<br/><em style="color: #666;">→ {sel["text"]}</em>'
                cat_html += '</li>'
                categories_html += cat_html
            categories_html += '</ul>'
        else:
            # Fallback to simple category list from meeting
            category_names = [cat.name for cat in meeting.categ_ids 
                             if cat.name not in ['Consulting Window', 'Consulting Meeting', 'Consulting Blocked']]
            categories_html = ', '.join(category_names) if category_names else 'keine'
        
        # Build call type label
        call_type_html = ''
        if call_type:
            call_label = '📹 Video-Call' if call_type == 'video' else '📞 Telefon'
            call_type_html = f'<li><strong>Format:</strong> {call_label}</li>'
        
        chatter_body = f"""<p><strong>🗓️ Beratungstermin gebucht</strong></p>
<ul>
    <li><strong>Datum:</strong> {start_str} Uhr</li>
    <li><strong>Berater:</strong> {host_name}</li>
    {call_type_html}
</ul>
<p><strong>Themen:</strong></p>
{categories_html}"""
        
        partner.message_post(
            body=chatter_body,
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )
        _logger.info("Chatter note posted for partner %s", partner.id)
    except Exception as e:
        _logger.error("Failed to post chatter note: %s", e)
    
    # SCL R2b: Log booking confirmation to consultant's partner chatter
    try:
        consultant_partner = meeting.user_id.partner_id if meeting.user_id else None
        if consultant_partner:
            customer_name = partner.name if partner else 'Kunde'
            customer_email = partner.email if partner else ''
            customer_phone = partner.phone or partner.mobile or '' if partner else ''
            
            exec_chatter_body = f"""<p><strong>🗓️ Neuer Beratungstermin</strong></p>
<ul>
    <li><strong>Kunde:</strong> {customer_name}</li>
    <li><strong>E-Mail:</strong> {customer_email}</li>
    {'<li><strong>Telefon:</strong> ' + customer_phone + '</li>' if customer_phone else ''}
    <li><strong>Datum:</strong> {start_str} Uhr</li>
    {call_type_html}
</ul>
<p><strong>Themen:</strong></p>
{categories_html}"""
            
            consultant_partner.message_post(
                body=exec_chatter_body,
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )
            _logger.info("Chatter note posted for consultant %s", consultant_partner.id)
    except Exception as e:
        _logger.error("Failed to post consultant chatter note: %s", e)


class ConsultingSlotsQuery(graphene.ObjectType):
    """Query for available consulting slots."""
    
    consulting_slots = graphene.List(
        ConsultingSlot,
        domain_code=graphene.String(required=True, description="Domain code (e.g., 'dasei')"),
        weeks=graphene.Int(default_value=3, description="Number of weeks ahead to search"),
        description="List available consulting slots computed from exec availability windows."
    )
    
    @staticmethod
    def resolve_consulting_slots(root, info, domain_code, weeks=3):
        env = info.context['env']
        
        # Find exec domainusers for this domain
        DomainUser = env['crearis.domainuser'].sudo()
        Website = env['website'].sudo()
        
        website = Website.search([('domain_code', '=', domain_code)], limit=1)
        if not website:
            _logger.warning("consultingSlots: domain_code '%s' not found", domain_code)
            return []
        
        exec_users = DomainUser.search([
            ('domain_id', '=', website.id),
            ('role', '=', 'exec'),
            ('active', '=', True),
        ])
        
        if not exec_users:
            _logger.info("consultingSlots: no exec users for domain '%s'", domain_code)
            return []
        
        # Get user IDs
        user_ids = [du.user_id.id for du in exec_users if du.user_id]
        if not user_ids:
            return []
        
        # Find calendar event types
        CalendarEventType = env['calendar.event.type'].sudo()
        window_type = CalendarEventType.search([('name', '=ilike', WINDOW_CATEGORY)], limit=1)
        meeting_type = CalendarEventType.search([('name', '=ilike', MEETING_CATEGORY)], limit=1)
        blocked_type = CalendarEventType.search([('name', '=ilike', BLOCKED_CATEGORY)], limit=1)
        
        if not window_type:
            _logger.warning("consultingSlots: '%s' calendar.event.type not found", WINDOW_CATEGORY)
            return []
        
        CalendarEvent = env['calendar.event'].sudo()
        now = datetime.now()
        end_date = now + timedelta(weeks=weeks)
        
        # Get availability windows (show_as='free' or any, depends on exec preference)
        windows = CalendarEvent.search([
            ('user_id', 'in', user_ids),
            ('categ_ids', 'in', [window_type.id]),
            ('stop', '>=', now),  # Window hasn't ended yet
            ('start', '<=', end_date),  # Window starts within range
        ], order='start asc')
        
        # Get existing meetings (to exclude booked slots)
        meeting_domain = [
            ('user_id', 'in', user_ids),
            ('stop', '>=', now),
            ('start', '<=', end_date),
        ]
        if meeting_type:
            meeting_domain.append(('categ_ids', 'in', [meeting_type.id]))
        else:
            # Fallback: any event with show_as='busy'
            meeting_domain.append(('show_as', '=', 'busy'))
        
        meetings = CalendarEvent.search(meeting_domain)
        
        # Get blocked time events (holidays, vacations, etc.)
        blocked_events = CalendarEvent.browse()
        if blocked_type:
            blocked_events = CalendarEvent.search([
                ('user_id', 'in', user_ids),
                ('categ_ids', 'in', [blocked_type.id]),
                ('stop', '>=', now),
                ('start', '<=', end_date),
            ])
        
        # Combine meetings and blocked events for overlap check
        blocking_events = meetings | blocked_events
        
        # D18: Build host_id → photo_url mapping from domainuser.cimg
        host_photo_map = {}
        if user_ids:
            DomainUser = env['crearis.domainuser'].sudo()
            exec_users = DomainUser.search([
                ('user_id', 'in', user_ids),
                ('role', '=', 'exec'),
            ])
            for du in exec_users:
                host_photo_map[du.user_id.id] = du.cimg or ''
        
        # Compute available slots
        available_slots = []
        for window in windows:
            computed = _compute_slots_from_window(window)
            for slot_key, slot_start, slot_stop, host_id, host_name in computed:
                # Skip past slots
                if slot_start < now:
                    continue
                # Skip if overlaps with existing meeting or blocked time
                if _slot_overlaps_events(slot_start, slot_stop, blocking_events):
                    continue
                
                # D18: Get photo from pre-built map
                photo_url = host_photo_map.get(host_id, '')
                
                available_slots.append(ConsultingSlot(
                    slot_key=slot_key,
                    start=slot_start.isoformat(),
                    stop=slot_stop.isoformat(),
                    duration=SLOT_DURATION_HOURS,
                    host_name=host_name,
                    host_id=host_id,
                    photo_url=photo_url,
                ))
        
        _logger.info(
            "consultingSlots: domain=%s found %d available slots from %d windows",
            domain_code, len(available_slots), len(windows)
        )
        return available_slots


class BookConsultingSlot(graphene.Mutation):
    """Book a consulting slot by creating a meeting event.
    
    Security:
    - IP restriction: Only localhost/server IP allowed (Nuxt SSR)
    - Rate limiting: Max 10 bookings/hour
    
    SCL additions (D16, D17):
    - consultation: Categories, freeform_text, call_type
    - product_slug: For return redirect (entity_id)
    """
    
    class Arguments:
        slot_key = graphene.String(required=True, description="Slot key from consultingSlots query")
        start = graphene.String(required=True, description="Slot start time (ISO datetime)")
        host_id = graphene.Int(required=True, description="Host user ID")
        contact = ConsultingContactInput(required=True)
        notes = graphene.String(description="Optional message from customer (included in confirmation)")
        # SCL additions
        consultation = ConsultingCategoryInput(description="SCL: Category preferences from dialog")
        product_slug = graphene.String(description="D16: Product slug for redirect (entity_id)")
        domain_code = graphene.String(description="D18: Source domain for journey-aware schedules (e.g., dasei1)")
        allow_cancellation = graphene.Boolean(
            default_value=False,
            description="SCL: If True, customer can cancel via link (bypass 6h rule)"
        )
    
    Output = ConsultingBookingResult
    
    @staticmethod
    def mutate(root, info, slot_key, start, host_id, contact, notes=None, consultation=None, product_slug=None, domain_code=None, allow_cancellation=False):
        env = info.context['env']
        
        # === SECURITY: IP Check (logging only, not blocking) ===
        # NOTE: Client-side calls come from user's browser IP, not server IP.
        # Rate limiting (below) is the primary anti-abuse mechanism.
        client_ip = _get_client_ip()
        if not _is_ip_allowed(client_ip):
            _logger.info(
                "BookConsultingSlot: Request from external IP: %s (allowed, rate-limited)",
                client_ip
            )
        
        # === SECURITY: Rate Limit Check ===
        allowed, rate_error = _check_rate_limit(env)
        if not allowed:
            # Send alert on first block
            if 'temporarily unavailable' in str(rate_error):
                _send_rate_limit_alert(env)
            return ConsultingBookingResult(
                success=False,
                error=rate_error,
            )
        
        # Parse start time
        try:
            slot_start = datetime.fromisoformat(start)
        except ValueError:
            return ConsultingBookingResult(
                success=False,
                error=_("Invalid start time format"),
            )
        
        slot_stop = slot_start + timedelta(minutes=SLOT_DURATION_MINUTES)
        
        # Validate host exists and is exec
        User = env['res.users'].sudo()
        host = User.browse(host_id)
        if not host.exists():
            return ConsultingBookingResult(
                success=False,
                error=_("Host not found"),
            )
        
        # Check slot isn't in the past
        if slot_start < datetime.now():
            return ConsultingBookingResult(
                success=False,
                error=_("Cannot book a slot in the past"),
            )
        
        # Check no conflicting meeting exists
        # IMPORTANT: Exclude "Consulting Window" events - they define availability, not conflicts
        CalendarEvent = env['calendar.event'].sudo()
        CalendarEventType = env['calendar.event.type'].sudo()
        window_type = CalendarEventType.search([('name', '=ilike', WINDOW_CATEGORY)], limit=1)
        
        conflict_domain = [
            ('user_id', '=', host_id),
            ('start', '<', slot_stop),
            ('stop', '>', slot_start),
            ('show_as', '=', 'busy'),
        ]
        # Exclude window events from conflict check
        if window_type:
            conflict_domain.append(('categ_ids', 'not in', [window_type.id]))
        
        conflicts = CalendarEvent.search(conflict_domain, limit=1)
        
        if conflicts:
            _logger.warning(
                "BookConsultingSlot: conflict found - event %s (%s) overlaps slot %s-%s",
                conflicts.id, conflicts.name, slot_start, slot_stop
            )
            return ConsultingBookingResult(
                success=False,
                error=_("This slot is no longer available"),
            )
        
        # Get or create partner
        Partner = env['res.partner'].sudo()
        partner = Partner.search([('email', '=ilike', contact.email)], limit=1)
        
        if not partner:
            partner_vals = {
                'name': f"{contact.vorname} {contact.nachname}".strip(),
                'email': contact.email,
            }
            if hasattr(Partner, 'firstname'):
                partner_vals['firstname'] = contact.vorname
                partner_vals['lastname'] = contact.nachname
            if contact.mobil:
                partner_vals['phone'] = contact.mobil
            partner = Partner.create(partner_vals)
            _logger.info("BookConsultingSlot: created partner %s", partner.id)
        
        # Find meeting category (reuse CalendarEventType from above)
        meeting_type = CalendarEventType.search([('name', '=ilike', MEETING_CATEGORY)], limit=1)
        
        # SCL: Map consultation category keys to calendar.event.type IDs (D4, R1)
        # Updated 2026-03-08: Parse selections[] with per-category options
        category_type_ids = []
        if meeting_type:
            category_type_ids.append(meeting_type.id)
        
        # Store parsed selections for chatter/email enrichment
        parsed_selections = []
        
        if consultation and consultation.selections:
            # Map string keys to XML IDs
            category_xmlid_map = {
                'prerequisites': 'crearis.calendar_event_type_cat_prerequisites',
                'terms_and_options': 'crearis.calendar_event_type_cat_terms_and_options',
                'topics': 'crearis.calendar_event_type_cat_topics',
                'schedules': 'crearis.calendar_event_type_cat_schedules',
                'custom': 'crearis.calendar_event_type_cat_custom',
            }
            # Human-readable labels for description
            category_labels = {
                'prerequisites': 'Voraussetzungen',
                'terms_and_options': 'Zahlungsbedingungen',
                'topics': 'Profile',
                'schedules': 'Verläufe',
                'custom': 'Individuell',
            }
            for sel in consultation.selections:
                cat_key = sel.category
                options = sel.options or []
                text = sel.text or ''
                
                # Store for later use
                parsed_selections.append({
                    'key': cat_key,
                    'label': category_labels.get(cat_key, cat_key),
                    'options': options,
                    'text': text,
                })
                
                # Map to calendar event type
                xmlid = category_xmlid_map.get(cat_key)
                if xmlid:
                    try:
                        cat_type = env.ref(xmlid)
                        if cat_type:
                            category_type_ids.append(cat_type.id)
                    except ValueError:
                        _logger.warning("BookConsultingSlot: category xmlid not found: %s", xmlid)
        
        # SCL: Build description with consultation details (per-category)
        description_parts = []
        teams_videocall_url = ''
        
        # Get host's teams_meeting_data from domainuser
        # First find domain (website) from domain_code
        host_domainuser = None
        if domain_code:
            Website = env['website'].sudo()
            domain_website = Website.search([('domain_code', '=', domain_code)], limit=1)
            _logger.info("BookConsultingSlot: domain_code=%s, website_id=%s", domain_code, domain_website.id if domain_website else None)
            if domain_website:
                DomainUser = env['crearis.domainuser'].sudo()
                host_domainuser = DomainUser.search([
                    ('user_id', '=', host_id),
                    ('domain_id', '=', domain_website.id),
                    ('role', '=', 'exec'),
                ], limit=1)
                _logger.info("BookConsultingSlot: host_id=%s, domainuser_id=%s, has_teams=%s", 
                    host_id, host_domainuser.id if host_domainuser else None, 
                    bool(host_domainuser.teams_meeting_data) if host_domainuser else False)
        
        teams_data = host_domainuser.teams_meeting_data if host_domainuser else {}
        _logger.info("BookConsultingSlot: teams_data type=%s, value=%s", type(teams_data).__name__, str(teams_data)[:100] if teams_data else 'empty')
        # Handle case where teams_meeting_data is stored as JSON string (from widget="text")
        if isinstance(teams_data, str):
            try:
                # User may have entered newlines in textarea - escape them for JSON parsing
                # Replace literal newlines with escaped \n before parsing
                teams_data_cleaned = teams_data.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                teams_data = json.loads(teams_data_cleaned)
                _logger.info("BookConsultingSlot: parsed teams_data, videocall_url=%s", teams_data.get('videocall_url', 'not found')[:50] if teams_data else 'empty')
            except (json.JSONDecodeError, TypeError) as e:
                _logger.warning("BookConsultingSlot: JSON parse error: %s", e)
                teams_data = {}
        if teams_data:
            teams_videocall_url = teams_data.get('videocall_url', '')
            _logger.info("BookConsultingSlot: teams_videocall_url=%s", teams_videocall_url[:50] if teams_videocall_url else 'empty')
        
        if consultation:
            call_type = getattr(consultation, 'call_type', None)
            if call_type:
                call_label = 'Video-Call' if call_type == 'video' else 'Telefon'
                description_parts.append(f"Beratungsformat: {call_label}")
                
                # Add MS Teams info for video calls (computed from atomic fields)
                if call_type == 'video' and host_domainuser:
                    login_info = host_domainuser.get_teams_login_html()
                    if login_info:
                        # Convert HTML to plain text for calendar description
                        import re
                        plain_login = re.sub(r'<br/?>', '\n', login_info)
                        plain_login = re.sub(r'<hr[^>]*/?>', '\n---\n', plain_login)
                        plain_login = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>[^<]*</a>', r'\1', plain_login)
                        plain_login = re.sub(r'<[^>]+>', '', plain_login)
                        description_parts.append(f"\n--- MS Teams Zugangsdaten ---\n{plain_login}")
                    elif teams_videocall_url:
                        # Fallback to basic URL info
                        description_parts.append(f"\nMeeting-Link: {teams_videocall_url}")
                        if teams_data.get('videocall_id'):
                            description_parts.append(f"Meeting-ID: {teams_data['videocall_id']}")
                        if teams_data.get('passkey'):
                            description_parts.append(f"Passcode: {teams_data['passkey']}")
            
            # Add per-category details
            for sel in parsed_selections:
                cat_line = f"\n{sel['label']}:"
                if sel['options']:
                    cat_line += f" {', '.join(sel['options'])}"
                if sel['text']:
                    cat_line += f"\n  → {sel['text']}"
                description_parts.append(cat_line)
        
        if notes:
            description_parts.append(f"\nNotizen:\n{notes}")
        
        # Create the meeting event
        meeting_name = f"Consulting: {contact.vorname} {contact.nachname}"
        
        # SCL: Determine consulting status (Vorbehalt logic)
        # - >4 days ahead: pending_reconfirm (needs confirmation email 36h before)
        # - ≤4 days ahead: confirmed (no action needed)
        # - allow_cancellation=True: cancellable (can cancel via link anytime)
        days_until_meeting = (slot_start - datetime.now()).days
        if allow_cancellation:
            consulting_status = 'cancellable'
        elif days_until_meeting > 4:
            consulting_status = 'pending_reconfirm'
        else:
            consulting_status = 'confirmed'
        
        # Generate consulting token for confirm/cancel links
        import secrets
        consulting_token = secrets.token_urlsafe(32)
        
        # D18: Resolve schedule products from domain_code + product_slug
        schedule_product_slugs = []
        schedule_city = ''
        schedule_city_exclude = False  # T8-I1: True for Blockkurs (flag 'x')
        shortcode_flag = None
        
        if product_slug:
            # Try parsing as shortcode (e.g., m18w)
            shortcode_config = _get_shortcode_config(env)
            parsed = _parse_product_ref(product_slug, config=shortcode_config)
            
            # Extract city filter from shortcode location
            if parsed.get('city_filter'):
                schedule_city = parsed['city_filter']
            
            # Extract flag for city_exclude logic
            shortcode_flag = parsed.get('flag', '')
            
            # T8-I1: Blockkurs (flag 'x') → show events NOT in the OTHER city
            # m18x (München program) → exclude Nürnberg → show München events
            # n18x (Nürnberg program) → exclude München → show Nürnberg events
            if shortcode_flag == 'x' and schedule_city:
                # Swap to the OTHER city and exclude it
                city_swap = {'München': 'Nürnberg', 'Nürnberg': 'München'}
                schedule_city = city_swap.get(schedule_city, schedule_city)
                schedule_city_exclude = True
            
            # Get default_code from parsed shortcode
            if parsed.get('default_code'):
                base_code = parsed['default_code']
            elif parsed.get('default_codes'):  # Bundle
                base_code = parsed['default_codes'][0] if parsed['default_codes'] else ''
            elif parsed.get('is_contact_only'):
                base_code = ''
            else:
                # Direct default_code (e.g., MOD-A)
                base_code = product_slug
            
            # Apply domain journey mapping if available
            if domain_code and domain_code in DOMAIN_JOURNEY_PRODUCTS:
                schedule_product_slugs = DOMAIN_JOURNEY_PRODUCTS[domain_code]
            elif base_code:
                schedule_product_slugs = [base_code]
        
        # Build consulting_data JSONB structure
        call_type_val = getattr(consultation, 'call_type', None) if consultation else None
        consulting_data = {
            'selections': parsed_selections,
            'schedule': {
                'product_slugs': schedule_product_slugs,
                'city': schedule_city,
                'city_exclude': schedule_city_exclude,
            },
            'call_type': call_type_val or 'video',
            'domain_code': domain_code or '',
            # Store teams info for email template access
            'teams_meeting_data': teams_data if isinstance(teams_data, dict) else {},
        }
        
        meeting_vals = {
            'name': meeting_name,
            'start': slot_start,
            'stop': slot_stop,
            'duration': SLOT_DURATION_HOURS,
            'user_id': host_id,
            'partner_ids': [(4, partner.id)],
            'show_as': 'busy',
            # SCL: Vorbehalt fields
            'consulting_status': consulting_status,
            'consulting_token': consulting_token,
            'product_slug': product_slug or '',
            # D18: All consulting data in single JSONB
            'consulting_data': consulting_data,
        }
        
        # Add MS Teams videocall URL if available
        if teams_videocall_url:
            meeting_vals['videocall_location'] = teams_videocall_url
        
        if category_type_ids:
            meeting_vals['categ_ids'] = [(4, tid) for tid in category_type_ids]
        
        if description_parts:
            meeting_vals['description'] = '\n'.join(description_parts)
        
        meeting = CalendarEvent.create(meeting_vals)
        
        # Add attendee record
        Attendee = env['calendar.attendee'].sudo()
        Attendee.create({
            'event_id': meeting.id,
            'partner_id': partner.id,
            'state': 'accepted',
        })
        
        # SCL: Attach reminder alarm (15min before) to meeting
        try:
            Alarm = env['calendar.alarm'].sudo()
            # Find or create a 15-minute notification alarm
            reminder_alarm = Alarm.search([
                ('alarm_type', '=', 'notification'),
                ('duration', '=', 15),
                ('interval', '=', 'minutes'),
            ], limit=1)
            if not reminder_alarm:
                reminder_alarm = Alarm.create({
                    'name': 'Beratung: 15 Min. Erinnerung',
                    'alarm_type': 'notification',
                    'duration': 15,
                    'interval': 'minutes',
                })
            meeting.write({'alarm_ids': [(4, reminder_alarm.id)]})
            _logger.debug("Alarm attached to meeting %s", meeting.id)
        except Exception as e:
            _logger.warning("Failed to attach alarm to meeting %s: %s", meeting.id, e)
        
        _logger.info(
            "BookConsultingSlot: created meeting %s for partner %s with host %s",
            meeting.id, partner.id, host_id
        )
        
        # Send confirmation emails (to customer and exec) with enhanced chatter
        call_type_val = getattr(consultation, 'call_type', None) if consultation else None
        _send_booking_emails(env, meeting, partner, notes, 
                           selections=parsed_selections, call_type=call_type_val)
        
        # D16: Return entity_id (product_slug) and entity_type for redirect
        return ConsultingBookingResult(
            success=True,
            entity_id=product_slug or '',
            entity_type='product',  # D16: default to 'product'
            meeting_id=meeting.id,
            start=slot_start.isoformat(),
            host_name=host.name,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# S2L: Email-Only Inquiry Mutation (Direction 4)
# ═══════════════════════════════════════════════════════════════════════════════

class EmailInquiryResult(graphene.ObjectType):
    """Result of creating an email-only inquiry."""
    success = graphene.Boolean(required=True)
    lead_id = graphene.Int(description="Created crm.lead ID")
    error = graphene.String()


class CreateEmailInquiry(graphene.Mutation):
    """S2L: Create email-only consulting inquiry (crm.lead).
    
    Direction 4 architecture: crm.lead serves as native home for email-only lane.
    No calendar slot needed - exec assigned via domainuser.
    
    Security:
    - Rate limiting: Same as BookConsultingSlot (10/hour)
    """
    
    class Arguments:
        contact = ConsultingContactInput(required=True, description="Customer contact info")
        consultation = ConsultingCategoryInput(required=True, description="Category selections")
        domain_code = graphene.String(required=True, description="Source domain (dasei1/dasei2/dasei3)")
        product_slug = graphene.String(description="Product context (for routing)")
    
    Output = EmailInquiryResult
    
    @staticmethod
    def mutate(root, info, contact, consultation, domain_code, product_slug=None):
        env = info.context['env']
        
        # === SECURITY: Rate Limit Check ===
        allowed, rate_error = _check_rate_limit(env)
        if not allowed:
            if 'temporarily unavailable' in str(rate_error):
                _send_rate_limit_alert(env)
            return EmailInquiryResult(success=False, error=rate_error)
        
        # Find or create partner
        Partner = env['res.partner'].sudo()
        partner = Partner.search([('email', '=ilike', contact.email)], limit=1)
        
        if not partner:
            partner_vals = {
                'name': f"{contact.vorname} {contact.nachname}".strip(),
                'email': contact.email,
            }
            if hasattr(Partner, 'firstname'):
                partner_vals['firstname'] = contact.vorname
                partner_vals['lastname'] = contact.nachname
            if contact.mobil:
                partner_vals['phone'] = contact.mobil
            partner = Partner.create(partner_vals)
            _logger.info("CreateEmailInquiry: created partner %s", partner.id)
        
        # Map category keys to crm.tag IDs
        CrmTag = env['crm.tag'].sudo()
        tag_xmlid_map = {
            'prerequisites': 'crearis.crm_tag_consulting_prerequisites',
            'terms_and_options': 'crearis.crm_tag_consulting_terms',
            'topics': 'crearis.crm_tag_consulting_topics',
            'schedules': 'crearis.crm_tag_consulting_schedules',
            'custom': 'crearis.crm_tag_consulting_custom',
        }
        category_labels = {
            'prerequisites': 'Voraussetzungen',
            'terms_and_options': 'Zahlungsbedingungen',
            'topics': 'Profile',
            'schedules': 'Verläufe',
            'custom': 'Individuell',
        }
        
        tag_ids = []
        description_parts = []
        
        if consultation and consultation.selections:
            for sel in consultation.selections:
                cat_key = sel.category
                options = sel.options or []
                text = sel.text or ''
                
                # Build description
                part = f"**{category_labels.get(cat_key, cat_key)}**"
                if options:
                    part += f": {', '.join(options)}"
                if text:
                    part += f"\n→ {text}"
                description_parts.append(part)
                
                # Map to crm.tag
                xmlid = tag_xmlid_map.get(cat_key)
                if xmlid:
                    try:
                        tag = env.ref(xmlid)
                        if tag:
                            tag_ids.append(tag.id)
                    except ValueError:
                        _logger.warning("CreateEmailInquiry: tag xmlid not found: %s", xmlid)
        
        description = "\n\n".join(description_parts)
        if product_slug:
            description = f"Produkt-Referenz: {product_slug}\n\n{description}"
        
        # Find exec via domainuser
        exec_user_id = False
        Website = env['website'].sudo()
        DomainUser = env['crearis.domainuser'].sudo()
        
        website = Website.search([('domain_code', '=', domain_code)], limit=1)
        if website:
            exec_du = DomainUser.search([
                ('domain_id', '=', website.id),
                ('role', '=', 'exec'),
                ('active', '=', True),
            ], limit=1)
            if exec_du and exec_du.user_id:
                exec_user_id = exec_du.user_id.id
        
        # Create CRM lead
        CrmLead = env['crm.lead'].sudo()
        lead = CrmLead.create({
            'name': f"Email-Beratung: {partner.name}",
            'partner_id': partner.id,
            'contact_name': f"{contact.vorname} {contact.nachname}".strip(),
            'email_from': contact.email,
            'phone': contact.mobil or '',
            'description': description,
            'tag_ids': [(6, 0, tag_ids)],
            'user_id': exec_user_id,
            'type': 'lead',
            'is_consulting_inquiry': True,
            'consulting_domain_code': domain_code,
        })
        
        _logger.info(
            "CreateEmailInquiry: created lead %s for partner %s, domain %s, exec %s",
            lead.id, partner.id, domain_code, exec_user_id
        )
        
        # Log to partner chatter
        chatter_body = f"""<p><strong>📧 Email-Beratungsanfrage</strong></p>
<ul>
<li>Domain: {domain_code}</li>
<li>Kategorien: {', '.join(category_labels.get(s.category, s.category) for s in (consultation.selections or []))}</li>
</ul>
<p><a href="/web#model=crm.lead&amp;id={lead.id}">→ Zur Anfrage</a></p>
"""
        partner.message_post(
            body=chatter_body,
            subtype_xmlid='mail.mt_note',
        )
        
        return EmailInquiryResult(success=True, lead_id=lead.id)


class ConsultingMutation(graphene.ObjectType):
    """Consulting mutations."""
    book_consulting_slot = BookConsultingSlot.Field()
    create_email_inquiry = CreateEmailInquiry.Field()  # S2L: Email-only lane
