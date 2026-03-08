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
        help='Related product slug for smart enrichment (e.g., dasei1)'
    )

    # SCL: Store selections as JSON for QWeb templates (Odoo 16 pattern)
    consulting_selections_raw = fields.Text(
        string='Consulting Selections JSON',
        help='Stored as JSON array of {key, label, options[], text}'
    )

    @api.model
    def _generate_consulting_token(self):
        """Generate a secure one-time token."""
        return secrets.token_urlsafe(32)

    def get_consulting_selections(self):
        """Helper for QWeb - returns parsed list of dicts."""
        self.ensure_one()
        if not self.consulting_selections_raw:
            return []
        try:
            return json.loads(self.consulting_selections_raw)
        except (json.JSONDecodeError, TypeError):
            return []

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

    def get_related_events(self, limit=5):
        """Get next events for the related product (for QWeb schedules snippet).
        
        Returns list of dicts with event info for template rendering.
        """
        self.ensure_one()
        if not self.product_slug:
            return []

        # Find product by slug
        Product = self.env['product.template'].sudo()
        # Try default_code on product.product or name matching on template
        ProductProduct = self.env['product.product'].sudo()
        product_variant = ProductProduct.search([
            ('default_code', '=ilike', self.product_slug),
        ], limit=1)
        
        if product_variant:
            product = product_variant.product_tmpl_id
        else:
            # Fall back to template name match
            product = Product.search([
                ('name', 'ilike', self.product_slug.replace('-', ' ')),
            ], limit=1)

        if not product:
            return []
        
        # Get event types from package (Many2many field)
        event_type_ids = []
        if hasattr(product, 'package_event_type_ids') and product.package_event_type_ids:
            event_type_ids = product.package_event_type_ids.ids
        
        if not event_type_ids:
            return []

        # Find upcoming events of these types
        Event = self.env['event.event'].sudo()
        now = datetime.now()
        events = Event.search([
            ('event_type_id', 'in', event_type_ids),
            ('date_begin', '>', now),
        ], order='date_begin asc', limit=limit)

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
