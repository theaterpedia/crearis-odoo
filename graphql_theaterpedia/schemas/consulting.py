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
"""

import logging
from datetime import datetime, timedelta

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


class ConsultingSlot(graphene.ObjectType):
    """A bookable consulting time slot (computed from availability window)."""
    # Computed slot ID: "window_id:slot_index" to identify uniquely
    slot_key = graphene.String(required=True, description="Unique slot key (window_id:index)")
    start = graphene.String(required=True, description="ISO datetime")
    stop = graphene.String(required=True, description="ISO datetime")
    duration = graphene.Float(required=True, description="Duration in hours (0.25 = 15min)")
    host_name = graphene.String(required=True, description="Exec user's display name")
    host_id = graphene.Int(required=True, description="res.users ID of host")


class ConsultingContactInput(graphene.InputObjectType):
    """Contact information for booking."""
    email = graphene.String(required=True)
    vorname = graphene.String(required=True)
    nachname = graphene.String(required=True)
    mobil = graphene.String()


class ConsultingBookingResult(graphene.ObjectType):
    """Result of booking a consulting slot."""
    success = graphene.Boolean(required=True)
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
                
                available_slots.append(ConsultingSlot(
                    slot_key=slot_key,
                    start=slot_start.isoformat(),
                    stop=slot_stop.isoformat(),
                    duration=SLOT_DURATION_HOURS,
                    host_name=host_name,
                    host_id=host_id,
                ))
        
        _logger.info(
            "consultingSlots: domain=%s found %d available slots from %d windows",
            domain_code, len(available_slots), len(windows)
        )
        return available_slots


class BookConsultingSlot(graphene.Mutation):
    """Book a consulting slot by creating a meeting event."""
    
    class Arguments:
        slot_key = graphene.String(required=True, description="Slot key from consultingSlots query")
        start = graphene.String(required=True, description="Slot start time (ISO datetime)")
        host_id = graphene.Int(required=True, description="Host user ID")
        contact = ConsultingContactInput(required=True)
        notes = graphene.String(description="Optional notes from customer")
    
    Output = ConsultingBookingResult
    
    @staticmethod
    def mutate(root, info, slot_key, start, host_id, contact, notes=None):
        env = info.context['env']
        
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
        CalendarEvent = env['calendar.event'].sudo()
        conflicts = CalendarEvent.search([
            ('user_id', '=', host_id),
            ('start', '<', slot_stop),
            ('stop', '>', slot_start),
            ('show_as', '=', 'busy'),
        ], limit=1)
        
        if conflicts:
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
        
        # Find meeting category
        CalendarEventType = env['calendar.event.type'].sudo()
        meeting_type = CalendarEventType.search([('name', '=ilike', MEETING_CATEGORY)], limit=1)
        
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
        
        if meeting_type:
            meeting_vals['categ_ids'] = [(4, meeting_type.id)]
        
        if notes:
            meeting_vals['description'] = f"Booking Notes:\n{notes}"
        
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
        
        # TODO: Send confirmation emails (future enhancement)
        
        return ConsultingBookingResult(
            success=True,
            meeting_id=meeting.id,
            start=slot_start.isoformat(),
            host_name=host.name,
        )


class ConsultingMutation(graphene.ObjectType):
    """Consulting mutations."""
    book_consulting_slot = BookConsultingSlot.Field()
