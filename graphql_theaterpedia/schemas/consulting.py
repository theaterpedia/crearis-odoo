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
from datetime import datetime, timedelta
import json

import graphene
from graphql import GraphQLError
from odoo import _
from odoo.http import request

_logger = logging.getLogger(__name__)

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


class ConsultingCategoryInput(graphene.InputObjectType):
    """SCL: Consultation preferences selected in dialog (D17, R6).
    
    Categories are string keys that map to calendar.event.type records.
    """
    categories = graphene.List(
        graphene.String,
        required=True,
        description="Category keys: prerequisites, terms_and_options, topics, schedules, custom"
    )
    freeform_text = graphene.String(
        description="Optional custom text (max 240 chars) - D27"
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


def _send_booking_emails(env, meeting, partner, notes=None):
    """Send confirmation emails to customer and exec, and log to partner chatter (R2)."""
    MailTemplate = env['mail.template'].sudo()
    
    # Send customer confirmation
    try:
        customer_template = MailTemplate.search([
            ('name', '=', 'Consulting Booking: Customer Confirmation')
        ], limit=1)
        if customer_template:
            customer_template.send_mail(meeting.id, force_send=True)
            _logger.info("Customer confirmation sent for meeting %s", meeting.id)
    except Exception as e:
        _logger.error("Failed to send customer confirmation: %s", e)
    
    # Send exec notification
    try:
        exec_template = MailTemplate.search([
            ('name', '=', 'Consulting Booking: Exec Notification')
        ], limit=1)
        if exec_template:
            exec_template.send_mail(meeting.id, force_send=True)
            _logger.info("Exec notification sent for meeting %s", meeting.id)
    except Exception as e:
        _logger.error("Failed to send exec notification: %s", e)
    
    # SCL R2: Log booking confirmation to partner chatter
    try:
        from datetime import datetime
        start_str = meeting.start.strftime('%d.%m.%Y %H:%M') if meeting.start else ''
        host_name = meeting.user_id.name if meeting.user_id else 'Host'
        
        # Build category list
        category_names = [cat.name for cat in meeting.categ_ids 
                         if cat.name not in ['Consulting Window', 'Consulting Meeting', 'Consulting Blocked']]
        categories_str = ', '.join(category_names) if category_names else 'keine'
        
        chatter_body = f"""<p><strong>Beratungstermin gebucht</strong></p>
<ul>
    <li><strong>Datum:</strong> {start_str} Uhr</li>
    <li><strong>Berater:</strong> {host_name}</li>
    <li><strong>Themen:</strong> {categories_str}</li>
</ul>"""
        
        partner.message_post(
            body=chatter_body,
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )
        _logger.info("Chatter note posted for partner %s", partner.id)
    except Exception as e:
        _logger.error("Failed to post chatter note: %s", e)


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
    
    Output = ConsultingBookingResult
    
    @staticmethod
    def mutate(root, info, slot_key, start, host_id, contact, notes=None, consultation=None, product_slug=None):
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
        category_type_ids = []
        if meeting_type:
            category_type_ids.append(meeting_type.id)
        
        if consultation and consultation.categories:
            # Map string keys to XML IDs
            category_xmlid_map = {
                'prerequisites': 'crearis.calendar_event_type_cat_prerequisites',
                'terms_and_options': 'crearis.calendar_event_type_cat_terms_and_options',
                'topics': 'crearis.calendar_event_type_cat_topics',
                'schedules': 'crearis.calendar_event_type_cat_schedules',
                'custom': 'crearis.calendar_event_type_cat_custom',
            }
            for cat_key in consultation.categories:
                xmlid = category_xmlid_map.get(cat_key)
                if xmlid:
                    try:
                        cat_type = env.ref(xmlid)
                        if cat_type:
                            category_type_ids.append(cat_type.id)
                    except ValueError:
                        _logger.warning("BookConsultingSlot: category xmlid not found: %s", xmlid)
        
        # SCL: Build description with consultation details
        description_parts = []
        if consultation:
            call_type = getattr(consultation, 'call_type', None)
            if call_type:
                description_parts.append(f"Call Type: {call_type}")
            freeform = getattr(consultation, 'freeform_text', None)
            if freeform:
                description_parts.append(f"Custom Notes: {freeform}")
        if notes:
            description_parts.append(f"Booking Notes:\n{notes}")
        
        # Create the meeting event
        meeting_name = f"Consulting: {contact.vorname} {contact.nachname}"
        meeting_vals = {
            'name': meeting_name,
            'start': slot_start,
            'stop': slot_stop,
            'duration': SLOT_DURATION_HOURS,
            'user_id': host_id,
            'partner_ids': [(4, partner.id)],
            'show_as': 'busy',
        }
        
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
        
        _logger.info(
            "BookConsultingSlot: created meeting %s for partner %s with host %s",
            meeting.id, partner.id, host_id
        )
        
        # Send confirmation emails (to customer and exec)
        _send_booking_emails(env, meeting, partner, notes)
        
        # D16: Return entity_id (product_slug) and entity_type for redirect
        return ConsultingBookingResult(
            success=True,
            entity_id=product_slug or '',
            entity_type='product',  # D16: default to 'product'
            meeting_id=meeting.id,
            start=slot_start.isoformat(),
            host_name=host.name,
        )


class ConsultingMutation(graphene.ObjectType):
    """Consulting mutations."""
    book_consulting_slot = BookConsultingSlot.Field()
