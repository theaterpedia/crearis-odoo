# -*- coding: utf-8 -*-
# Copyright 2026 crearis.io
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
"""
Calendar Event extension for SCL consulting workflow.

Adds:
- consulting_status: confirmed, pending_reconfirm, cancellable
- consulting_token: one-time token for confirm/cancel links
- product_slug: related product for smart enrichment
- Helper methods for QWeb templates
"""

import json
import secrets
from datetime import datetime, timedelta

from odoo import api, fields, models


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    # SCL: Consulting status for confirmation workflow
    consulting_status = fields.Selection([
        ('none', 'Not a consultation'),
        ('confirmed', 'Confirmed'),
        ('pending_reconfirm', 'Pending Reconfirmation'),
        ('cancellable', 'Cancellable by Customer'),
        ('cancelled', 'Cancelled'),
        ('reconfirmed', 'Reconfirmed'),
    ], string='Consulting Status', default='none', tracking=True)

    consulting_token = fields.Char(
        string='Consulting Token',
        help='One-time token for confirm/cancel links',
        copy=False, index=True
    )

    consulting_token_used = fields.Boolean(
        string='Token Used',
        default=False, copy=False
    )

    # SCL: Product context for smart enrichment
    product_slug = fields.Char(
        string='Product Slug',
        help='Related product slug for smart enrichment (e.g., m18w)'
    )

    # SCL: Consulting data as JSONB (selections, schedule config, call type)
    # Structure:
    # {
    #     "selections": [{"key": "schedules", "label": "Verläufe", "options": [...], "text": "..."}],
    #     "schedule": {"product_slugs": ["MOD-A"], "city": "München", "city_exclude": false},
    #     "call_type": "video"
    # }
    consulting_data = fields.Json(
        string='Consulting Data',
        help='JSON with consultation selections, schedule config, call type',
        default=False
    )

    @api.model
    def _generate_consulting_token(self):
        """Generate a secure one-time token."""
        return secrets.token_urlsafe(32)

    def get_consulting_selections(self):
        """Helper for QWeb - returns parsed list of selection dicts."""
        self.ensure_one()
        if not self.consulting_data or not isinstance(self.consulting_data, dict):
            return []
        return self.consulting_data.get('selections', [])

    def get_consulting_option(self, section, key=None, default=None):
        """Helper for QWeb - get nested value from consulting_data.
        
        Examples:
            get_consulting_option('schedule', 'city')  # → 'München'
            get_consulting_option('call_type')  # → 'video'
            get_consulting_option('schedule')  # → {'product_slugs': [...], 'city': '...'}
        """
        self.ensure_one()
        if not self.consulting_data or not isinstance(self.consulting_data, dict):
            return default
        
        value = self.consulting_data.get(section, default)
        if key and isinstance(value, dict):
            return value.get(key, default)
        return value

    def get_product_info(self):
        """Helper for QWeb - returns product info dict for email templates.
        
        Falls back through: product_slug → consulting_data.schedule.product_slugs[0]
        Parses shortcode (z15e) → flag (e) → default_code (MOD-E) for product lookup.
        
        Returns:
            {
                'shortcode': 'z15e',
                'is_course': True,  # True for m**, n**, z** patterns
                'type_label': 'Kurs' or 'Veranstaltung',
                'product_name': 'Full product name',
                'headline': 'Extracted headline' or 'Full product name'
            }
        """
        import re
        self.ensure_one()
        
        # Try product_slug field first, then consulting_data.schedule.product_slugs
        shortcode = self.product_slug or ''
        if not shortcode:
            schedule = self.get_consulting_option('schedule', default={}) or {}
            slugs = schedule.get('product_slugs', []) if isinstance(schedule, dict) else []
            shortcode = slugs[0] if slugs else ''
        
        if not shortcode:
            return {}
        
        # Determine if course (m**, n**, z**) or event
        is_course = bool(re.match(r'^[mnz]\d', shortcode.lower())) if shortcode else False
        type_label = 'Kurs' if is_course else 'Veranstaltung'
        
        # Parse shortcode to get product default_code
        # Shortcode format: {location}{id}{flag} e.g. z15e → flag=e → MOD-E
        product_name = ''
        headline = ''
        ProductProduct = self.env['product.product'].sudo()
        
        # First try direct lookup (for MOD-A style codes)
        product = ProductProduct.search([('default_code', '=ilike', shortcode)], limit=1)
        
        if not product and len(shortcode) >= 3:
            # Parse shortcode: extract flag (last char) and map to default_code
            flag = shortcode[-1].lower()
            flag_to_code = {
                'w': 'MOD-A', 'x': 'MOD-B', 'a': 'MOD-A', 'b': 'MOD-B',
                'c': 'MOD-C', 'd': 'MOD-D', 'e': 'MOD-E',
                't': 'MOD-AUFBAU-T', 'r': 'MOD-AUFBAU-R', 'p': 'MOD-AUFBAU-P',
            }
            mapped_code = flag_to_code.get(flag, '')
            if mapped_code:
                product = ProductProduct.search([('default_code', '=ilike', mapped_code)], limit=1)
        
        if product:
            product_name = product.name or ''
            # Extract headline from "xyz **headline**" format
            match = re.search(r'\*\*(.+?)\*\*', product_name)
            headline = match.group(1) if match else product_name
        
        # Fallback: use flag title mapping if no product found
        if not headline and len(shortcode) >= 3:
            flag = shortcode[-1].lower()
            flag_to_title = {
                'w': 'Grundlagenbildung Theaterpädagogik (Tageskurs)',
                'x': 'Grundlagenbildung Theaterpädagogik (Blockkurs)',
                'a': 'Modul A: Einstiege ins Theaterspiel',
                'b': 'Modul B: Eine Bühne voll Erfahrung',
                'c': 'Modul C: Szenische Welten',
                'd': 'Modul D: Präsentation',
                'e': 'Aufbaustufe Teil 1: Modul E – Vertiefung',
                't': 'Aufbaustufe Profil: Theatrales Lernen',
                'r': 'Aufbaustufe Profil: Performance & Interkulturell',
                'p': 'Aufbaustufe Abschluss: Berufsabschluss (BuT)',
                'v': 'Beratung: Aufbaustufe / Beraten & Ausprobieren',
            }
            headline = flag_to_title.get(flag, shortcode)
        
        return {
            'shortcode': shortcode,
            'is_course': is_course,
            'type_label': type_label,
            'product_name': product_name,
            'headline': headline,
        }

    def get_confirm_url(self):
        """Get the reconfirmation URL."""
        self.ensure_one()
        if not self.consulting_token:
            return ''
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/consulting/confirm/{self.consulting_token}"

    def get_cancel_url(self):
        """Get the cancellation URL."""
        self.ensure_one()
        if not self.consulting_token:
            return ''
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/consulting/cancel/{self.consulting_token}"

    # ===== Generic Event Helpers (no company-specific logic) =====
    
    def search_upcoming_events(self, event_type_ids, city=None, city_exclude=False, limit=5):
        """Search upcoming events by type + city filter.
        
        Generic helper for QWeb templates - no product knowledge.
        Respects multi-company access rules (no sudo).
        
        Args:
            event_type_ids: list of event.type IDs to filter by
            city: optional city filter string
            city_exclude: if True, exclude events IN this city (inverse filter)
            limit: max events to return
            
        Returns:
            event.event recordset
        """
        if not event_type_ids:
            return self.env['event.event'].browse()
        
        domain = [
            ('event_type_id', 'in', event_type_ids),
            ('date_begin', '>', datetime.now()),
        ]
        
        if city:
            op = 'not ilike' if city_exclude else 'ilike'
            domain.append(('address_id.city', op, city))
        
        return self.env['event.event'].search(
            domain, order='date_begin asc', limit=limit
        )

    def format_event_for_template(self, event):
        """Format single event record for QWeb rendering.
        
        Generic helper - returns dict with standard event info.
        """
        return {
            'id': event.id,
            'name': event.name,
            'event_type': event.event_type_id.name if event.event_type_id else '',
            'overline': event.subtitle if hasattr(event, 'subtitle') else '',
            'headline': event.name,
            'start': event.date_begin.strftime('%d.%m.%Y %H:%M') if event.date_begin else '',
            'end': event.date_end.strftime('%d.%m.%Y %H:%M') if event.date_end else '',
            'location': event.address_id.city if event.address_id else '',
        }

    def get_related_events(self, limit=5):
        """DEPRECATED: Use QWeb template resolution instead.
        
        This method contains company-specific product→event logic.
        New templates should call search_upcoming_events() directly
        after resolving event_type_ids via product.get_linked_event_type_ids().
        
        See mail_template_consulting_data.xml for the QWeb pattern.
        
        Kept for backward compatibility during migration.
        """
        self.ensure_one()
        
        # Read config from JSONB
        schedule = self.get_consulting_option('schedule', default={})
        product_codes = schedule.get('product_slugs', []) if isinstance(schedule, dict) else []
        city_filter = schedule.get('city', '') if isinstance(schedule, dict) else ''
        city_exclude = schedule.get('city_exclude', False) if isinstance(schedule, dict) else False
        
        # Fall back to product_slug if no resolved codes
        if not product_codes and self.product_slug:
            product_codes = [self.product_slug]
        
        if not product_codes:
            return []

        # DEPRECATED: Product→EventType resolution (now in QWeb)
        ProductProduct = self.env['product.product'].sudo()
        all_event_type_ids = []
        for code in product_codes:
            pv = ProductProduct.search([('default_code', '=ilike', code)], limit=1)
            if pv and hasattr(pv.product_tmpl_id, 'get_linked_event_type_ids'):
                all_event_type_ids.extend(pv.product_tmpl_id.get_linked_event_type_ids())
        
        if not all_event_type_ids:
            return []

        # Use generic helper for event search
        events = self.search_upcoming_events(all_event_type_ids, city_filter, city_exclude, limit)

        result = []
        for ev in events:
            result.append({
                'id': ev.id,
                'name': ev.name,
                'event_type': ev.event_type_id.name if ev.event_type_id else '',
                'overline': ev.subtitle if hasattr(ev, 'subtitle') else '',
                'headline': ev.name,
                'start': ev.date_begin.strftime('%d.%m.%Y %H:%M') if ev.date_begin else '',
                'end': ev.date_end.strftime('%d.%m.%Y %H:%M') if ev.date_end else '',
                'location': ev.address_id.city if ev.address_id else (ev.location if hasattr(ev, 'location') else ''),
            })

        return result

    def action_reconfirm(self):
        """Mark consultation as reconfirmed."""
        self.ensure_one()
        if self.consulting_status == 'pending_reconfirm':
            self.write({
                'consulting_status': 'reconfirmed',
                'consulting_token_used': True,
            })

    def action_cancel_consultation(self):
        """Cancel the consultation."""
        self.ensure_one()
        if self.consulting_status in ('pending_reconfirm', 'cancellable'):
            self.write({
                'consulting_status': 'cancelled',
                'consulting_token_used': True,
                'active': False,
            })

    @api.model
    def _cron_consulting_reconfirm(self):
        """Cron: Send reconfirmation emails 36h before consultation.
        
        Finds consultations with status='pending_reconfirm' starting in 30-42h window
        and sends them a reconfirmation email with confirm/cancel links.
        """
        import logging
        _logger = logging.getLogger(__name__)
        
        now = datetime.now()
        window_start = now + timedelta(hours=30)
        window_end = now + timedelta(hours=42)
        
        consultations = self.search([
            ('consulting_status', '=', 'pending_reconfirm'),
            ('start', '>=', window_start),
            ('start', '<=', window_end),
            ('consulting_token_used', '=', False),
        ])
        
        if not consultations:
            return
        
        _logger.info("Consulting reconfirm: found %d consultations in 36h window", len(consultations))
        
        # Find the reconfirmation email template
        MailTemplate = self.env['mail.template'].sudo()
        template = MailTemplate.search([
            ('name', '=', 'Consulting Booking: Reconfirmation Request')
        ], limit=1)
        
        if not template:
            _logger.warning("Consulting reconfirm: template 'Consulting Booking: Reconfirmation Request' not found")
            return
        
        for consultation in consultations:
            try:
                template.send_mail(consultation.id, force_send=True)
                _logger.info("Reconfirmation email sent for consultation %s", consultation.id)
            except Exception as e:
                _logger.error("Failed to send reconfirmation email for %s: %s", consultation.id, e)

    @api.model
    def _cron_consulting_alert(self):
        """Cron: Alert consultant 6h before if consultation still pending.
        
        Finds consultations with status='pending_reconfirm' starting in 4-8h window
        and sends an alert to the consultant that the customer hasn't confirmed.
        """
        import logging
        _logger = logging.getLogger(__name__)
        
        now = datetime.now()
        window_start = now + timedelta(hours=4)
        window_end = now + timedelta(hours=8)
        
        consultations = self.search([
            ('consulting_status', '=', 'pending_reconfirm'),
            ('start', '>=', window_start),
            ('start', '<=', window_end),
        ])
        
        if not consultations:
            return
        
        _logger.info("Consulting alert: found %d unconfirmed consultations in 6h window", len(consultations))
        
        # Find the alert email template
        MailTemplate = self.env['mail.template'].sudo()
        template = MailTemplate.search([
            ('name', '=', 'Consulting Booking: Consultant Alert')
        ], limit=1)
        
        if not template:
            _logger.warning("Consulting alert: template 'Consulting Booking: Consultant Alert' not found")
            return
        
        for consultation in consultations:
            try:
                template.send_mail(consultation.id, force_send=True)
                _logger.info("Consultant alert sent for consultation %s", consultation.id)
                # Post note to chatter
                consultation.message_post(
                    body="⚠️ 6h-Warnung: Kunde hat Beratung noch nicht bestätigt",
                    message_type='notification',
                )
            except Exception as e:
                _logger.error("Failed to send consultant alert for %s: %s", consultation.id, e)
