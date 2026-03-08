# -*- coding: utf-8 -*-
# Copyright 2026 crearis.io
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
"""
SCL Consulting workflow controllers.

Handles one-time token-based confirm/cancel links for consultations.
"""

import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class ConsultingController(http.Controller):
    """Controller for consulting confirmation/cancellation via token."""

    def _get_event_by_token(self, token):
        """Find calendar event by consulting token."""
        if not token:
            return None
        CalendarEvent = request.env['calendar.event'].sudo()
        return CalendarEvent.search([
            ('consulting_token', '=', token),
            ('consulting_token_used', '=', False),
        ], limit=1)

    def _render_result(self, title, message, success=True):
        """Render a simple result page."""
        return request.render('crearis.consulting_result_page', {
            'title': title,
            'message': message,
            'success': success,
        })

    @http.route('/consulting/confirm/<string:token>', type='http', auth='public', website=True)
    def confirm_consultation(self, token, **kwargs):
        """Reconfirm a consultation using one-time token."""
        event = self._get_event_by_token(token)

        if not event:
            _logger.warning(f"Invalid or expired consulting token: {token[:20]}...")
            return self._render_result(
                'Link ungültig',
                'Dieser Bestätigungslink ist ungültig oder wurde bereits verwendet.',
                success=False
            )

        if event.consulting_status not in ('pending_reconfirm',):
            _logger.info(f"Consulting token {token[:20]} used on event with status {event.consulting_status}")
            return self._render_result(
                'Bereits bestätigt',
                f'Deine Beratung am {event.start.strftime("%d.%m.%Y um %H:%M")} Uhr wurde bereits bestätigt.',
                success=True
            )

        # Reconfirm the consultation
        event.action_reconfirm()
        _logger.info(f"Consultation reconfirmed: {event.name} (ID: {event.id})")

        # Post to chatter
        event.message_post(
            body="✅ Beratung vom Kunden bestätigt (via Link)",
            message_type='notification',
        )

        return self._render_result(
            'Bestätigt!',
            f'Deine Beratung am {event.start.strftime("%d.%m.%Y um %H:%M")} Uhr ist jetzt verbindlich bestätigt. Wir freuen uns auf dich!',
            success=True
        )

    @http.route('/consulting/cancel/<string:token>', type='http', auth='public', website=True)
    def cancel_consultation(self, token, **kwargs):
        """Cancel a consultation using one-time token."""
        event = self._get_event_by_token(token)

        if not event:
            _logger.warning(f"Invalid or expired consulting cancel token: {token[:20]}...")
            return self._render_result(
                'Link ungültig',
                'Dieser Absagelink ist ungültig oder wurde bereits verwendet.',
                success=False
            )

        if event.consulting_status not in ('pending_reconfirm', 'cancellable'):
            _logger.info(f"Consulting cancel denied for status {event.consulting_status}")
            return self._render_result(
                'Absage nicht möglich',
                'Diese Beratung kann nicht mehr über diesen Link abgesagt werden. Bitte kontaktiere uns direkt.',
                success=False
            )

        # Check 6-hour rule for non-cancellable consultations
        if event.consulting_status == 'pending_reconfirm':
            from datetime import datetime, timedelta
            now = datetime.now()
            hours_until = (event.start - now).total_seconds() / 3600 if event.start else 0
            if hours_until < 6:
                _logger.info(f"Consulting cancel denied - less than 6h until event")
                return self._render_result(
                    'Kurzfristige Absage',
                    f'Da die Beratung in weniger als 6 Stunden beginnt, ist eine Absage über diesen Link nicht mehr möglich. Bitte kontaktiere uns direkt unter beratung@crearis.io.',
                    success=False
                )

        # Cancel the consultation
        event_info = f"{event.start.strftime('%d.%m.%Y um %H:%M')}" if event.start else event.name
        event.action_cancel_consultation()
        _logger.info(f"Consultation cancelled: {event.name} (ID: {event.id})")

        return self._render_result(
            'Abgesagt',
            f'Deine Beratung ({event_info}) wurde abgesagt. Du kannst jederzeit einen neuen Termin buchen.',
            success=True
        )
