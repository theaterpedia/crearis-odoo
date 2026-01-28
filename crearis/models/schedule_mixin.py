# -*- coding: utf-8 -*-
# Copyright 2026 theaterpedia.org / crearis.io
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import re
import logging
from datetime import datetime, timedelta

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

# Weekday mapping: German (primary) and English (fallback)
WEEKDAYS_DE = {'MO': 0, 'DI': 1, 'MI': 2, 'DO': 3, 'FR': 4, 'SA': 5, 'SO': 6}
WEEKDAYS_EN = {'MON': 0, 'TUE': 1, 'WED': 2, 'THU': 3, 'FRI': 4, 'SAT': 5, 'SUN': 6}
WEEKDAYS = {**WEEKDAYS_DE, **WEEKDAYS_EN}

# Internal storage uses English 3-letter codes
WEEKDAY_NAMES = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']

# Date patterns by locale
DATE_PATTERNS = {
    'de': r'(\d{1,2})\.(\d{1,2})(?:\.(\d{2,4}))?',  # 17.9 or 17.9.24
    'en': r'(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?',    # 9/17 or 9/17/24
}

# Time pattern: HH:MM-HH:MM or HH:MM - HH:MM
TIME_PATTERN = r'(\d{1,2}):(\d{2})\s*[-–]\s*(\d{1,2}):(\d{2})'

# Shortcode pattern: _SOMETHING_ or _SOMETHING:ROOM_
SHORTCODE_PATTERN = r'_([A-Za-z0-9]+)(?::([A-Za-z0-9]+))?_'


# =============================================================================
# SCHEDULE PARSER
# =============================================================================

class ScheduleParser:
    """
    Parser for schedule text into structured JSONB format.
    
    Supports:
    - German weekday codes (MO, DI, MI, DO, FR, SA, SO)
    - Time ranges (HH:MM-HH:MM)
    - Shortcodes (_online_, _TANZEREI_, _VENUE:ROOM_)
    - Date specifications (DD.MM or DD.MM.YY)
    - Section headers (online:, München:)
    """
    
    def __init__(self, locale='de', shortcodes=None):
        self.locale = locale
        self.shortcodes = shortcodes or {'_online_': {'type': 'online'}}
        self._build_patterns()
    
    def _build_patterns(self):
        """Build regex patterns based on locale."""
        # Weekday pattern (accepts both DE and EN)
        weekday_codes = '|'.join(WEEKDAYS.keys())
        self.weekday_pattern = re.compile(
            rf'({weekday_codes})\s*'
            rf'(?:{DATE_PATTERNS[self.locale]}\s*)?'  # Optional date
            rf'{TIME_PATTERN}'  # Required time
            rf'(?:\s*(?:Uhr|h))?\s*'  # Optional "Uhr" suffix
            rf'({SHORTCODE_PATTERN}|online|ONLINE)?',  # Optional shortcode or "online"
            re.IGNORECASE
        )
        
        # Section header pattern
        self.header_pattern = re.compile(
            r'^(online|[A-ZÄÖÜ][a-zäöüß]+(?:[-\s][A-ZÄÖÜ]?[a-zäöüß]+)*)\s*:\s*$',
            re.MULTILINE
        )
    
    def parse(self, text, date_begin=None, date_end=None):
        """
        Parse schedule text into structured data.
        
        Args:
            text: Raw schedule text
            date_begin: Event start date for resolving weekdays
            date_end: Event end date
            
        Returns:
            dict: Parsed schedule_data structure
        """
        if not text:
            return None
        
        result = {
            '$schema': 'schedule_data_v1',
            'source': 'parsed',
            'raw_text': text[:500],  # Store first 500 chars
            'sessions': [],
            'summary': {},
            'unparsed_notes': [],
        }
        
        # Track current context (set by section headers)
        current_context = None
        
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for section header
            header_match = self.header_pattern.match(line)
            if header_match:
                current_context = header_match.group(1).lower()
                continue
            
            # Try to parse as time slot
            session = self._parse_timeslot(line, current_context, date_begin, date_end)
            if session:
                result['sessions'].append(session)
            else:
                # Store as unparsed note
                if line and not line.startswith('*'):
                    result['unparsed_notes'].append(line)
        
        # Calculate summary
        result['summary'] = self._calculate_summary(result['sessions'])
        
        return result if result['sessions'] else None
    
    def _parse_timeslot(self, line, context, date_begin, date_end):
        """Parse a single time slot line."""
        # Check for shortcode at end of line
        shortcode_match = re.search(SHORTCODE_PATTERN, line)
        shortcode = None
        shortcode_room = None
        session_type = 'venue'  # default
        location_hint = None
        
        if shortcode_match:
            shortcode = f'_{shortcode_match.group(1)}_'
            shortcode_room = shortcode_match.group(2)
            
            # Look up shortcode config
            if shortcode.lower() in [k.lower() for k in self.shortcodes]:
                sc_key = next(k for k in self.shortcodes if k.lower() == shortcode.lower())
                sc_config = self.shortcodes[sc_key]
                session_type = sc_config.get('type', 'venue')
                location_hint = sc_config.get('name')
        
        # Check for "online" keyword (without underscore)
        if re.search(r'\bonline\b', line, re.IGNORECASE):
            session_type = 'online'
        
        # Use context if no explicit type
        if context and session_type == 'venue':
            if context == 'online':
                session_type = 'online'
            elif context not in ('online',):
                location_hint = context.title()
        
        # Parse weekday and time
        # Simplified pattern for more flexibility
        weekday_match = re.search(
            rf'({"|".join(WEEKDAYS.keys())})\s*'
            rf'(?:(\d{{1,2}})\.(\d{{1,2}})(?:\.(\d{{2,4}}))?\s*)?'
            rf'(\d{{1,2}}):(\d{{2}})\s*[-–]\s*(\d{{1,2}}):(\d{{2}})',
            line,
            re.IGNORECASE
        )
        
        if not weekday_match:
            return None
        
        day_code = weekday_match.group(1).upper()
        date_day = weekday_match.group(2)
        date_month = weekday_match.group(3)
        date_year = weekday_match.group(4)
        start_hour = int(weekday_match.group(5))
        start_min = int(weekday_match.group(6))
        end_hour = int(weekday_match.group(7))
        end_min = int(weekday_match.group(8))
        
        # Calculate duration
        start_minutes = start_hour * 60 + start_min
        end_minutes = end_hour * 60 + end_min
        if end_minutes < start_minutes:
            end_minutes += 24 * 60  # Handle overnight
        duration_h = (end_minutes - start_minutes) / 60
        
        # Resolve date
        resolved_date = None
        if date_day and date_month:
            year = datetime.now().year
            if date_year:
                year = int(date_year)
                if year < 100:
                    year += 2000
            try:
                resolved_date = f'{year}-{int(date_month):02d}-{int(date_day):02d}'
            except ValueError:
                pass
        elif date_begin:
            # Resolve from event date range
            resolved_date = self._resolve_weekday_date(day_code, date_begin, date_end)
        
        # Normalize day code to English
        day_index = WEEKDAYS.get(day_code, WEEKDAYS.get(day_code[:3]))
        normalized_day = WEEKDAY_NAMES[day_index] if day_index is not None else day_code
        
        return {
            'day': normalized_day,
            'date': resolved_date,
            'start': f'{start_hour:02d}:{start_min:02d}',
            'end': f'{end_hour:02d}:{end_min:02d}',
            'duration_h': round(duration_h, 2),
            'type': session_type,
            'location_hint': location_hint,
            'room': shortcode_room,
            'notes': None,
        }
    
    def _resolve_weekday_date(self, day_code, date_begin, date_end):
        """Resolve a weekday code to a specific date within event range."""
        if not date_begin:
            return None
        
        target_weekday = WEEKDAYS.get(day_code)
        if target_weekday is None:
            return None
        
        # Convert to date if datetime
        if isinstance(date_begin, datetime):
            date_begin = date_begin.date()
        if isinstance(date_end, datetime):
            date_end = date_end.date()
        
        # Find first matching weekday in range
        current = date_begin
        end = date_end or (date_begin + timedelta(days=7))
        
        while current <= end:
            if current.weekday() == target_weekday:
                return current.isoformat()
            current += timedelta(days=1)
        
        return None
    
    def _calculate_summary(self, sessions):
        """Calculate summary statistics from sessions."""
        total_hours = sum(s.get('duration_h', 0) for s in sessions)
        online_sessions = [s for s in sessions if s.get('type') == 'online']
        online_hours = sum(s.get('duration_h', 0) for s in online_sessions)
        venue_hours = total_hours - online_hours
        
        return {
            'total_hours': round(total_hours, 2),
            'online_hours': round(online_hours, 2),
            'venue_hours': round(venue_hours, 2),
            'has_online': len(online_sessions) > 0,
            'session_count': len(sessions),
            'online_session_count': len(online_sessions),
        }


# =============================================================================
# ODOO MIXIN
# =============================================================================

class EventScheduleMixin(models.AbstractModel):
    """
    Abstract mixin providing schedule_data JSONB field and parsing capabilities.
    
    Inherit this mixin in any model that needs structured schedule data:
    
        class MyEvent(models.Model):
            _name = 'my.event'
            _inherit = ['event.schedule.mixin']
    """
    _name = 'event.schedule.mixin'
    _description = 'Event Schedule Mixin'
    
    # =========================
    # FIELDS
    # =========================
    
    schedule_data = fields.Json(
        string='Schedule Data',
        help='Parsed session schedule in JSONB format',
        default=False
    )
    
    schedule_raw = fields.Text(
        string='Schedule Raw Text',
        help='Original schedule text before parsing'
    )
    
    # Computed summary fields (stored for filtering/reporting)
    has_online_sessions = fields.Boolean(
        string='Has Online Sessions',
        compute='_compute_schedule_summary',
        store=True,
        help='Whether this event has any online sessions'
    )
    
    total_hours = fields.Float(
        string='Total Hours',
        compute='_compute_schedule_summary',
        store=True,
        digits=(6, 2)
    )
    
    online_hours = fields.Float(
        string='Online Hours',
        compute='_compute_schedule_summary',
        store=True,
        digits=(6, 2)
    )
    
    venue_hours = fields.Float(
        string='Venue Hours',
        compute='_compute_schedule_summary',
        store=True,
        digits=(6, 2)
    )
    
    session_count = fields.Integer(
        string='Session Count',
        compute='_compute_schedule_summary',
        store=True
    )
    
    # =========================
    # COMPUTED METHODS
    # =========================
    
    @api.depends('schedule_data')
    def _compute_schedule_summary(self):
        for record in self:
            data = record.schedule_data or {}
            summary = data.get('summary', {})
            record.has_online_sessions = summary.get('has_online', False)
            record.total_hours = summary.get('total_hours', 0.0)
            record.online_hours = summary.get('online_hours', 0.0)
            record.venue_hours = summary.get('venue_hours', 0.0)
            record.session_count = summary.get('session_count', 0)
    
    # =========================
    # PUBLIC METHODS
    # =========================
    
    def parse_schedule_text(self, text, date_begin=None, date_end=None, company=None):
        """
        Parse schedule text into schedule_data JSONB.
        
        Args:
            text: Raw schedule text to parse
            date_begin: Event start date for resolving weekdays
            date_end: Event end date
            company: Company for locale/shortcode config (defaults to current)
            
        Returns:
            dict: Parsed schedule_data structure
        """
        self.ensure_one()
        company = company or self.env.company
        
        locale = company.schedule_locale or 'de'
        shortcodes = company.schedule_shortcodes or {'_online_': {'type': 'online'}}
        
        parser = ScheduleParser(locale=locale, shortcodes=shortcodes)
        return parser.parse(text, date_begin, date_end)
    
    def action_parse_schedule(self):
        """
        Action to parse schedule_raw into schedule_data.
        Can be triggered from UI button.
        """
        for record in self:
            if not record.schedule_raw:
                continue
            
            date_begin = getattr(record, 'date_begin', None)
            date_end = getattr(record, 'date_end', None)
            
            schedule_data = record.parse_schedule_text(
                record.schedule_raw,
                date_begin=date_begin,
                date_end=date_end
            )
            
            if schedule_data:
                record.schedule_data = schedule_data
                _logger.info(
                    "Parsed schedule for %s: %d sessions, %.1f hours",
                    record.display_name,
                    schedule_data.get('summary', {}).get('session_count', 0),
                    schedule_data.get('summary', {}).get('total_hours', 0)
                )
    
    def get_online_sessions(self):
        """Get all online sessions from schedule_data."""
        self.ensure_one()
        sessions = (self.schedule_data or {}).get('sessions', [])
        return [s for s in sessions if s.get('type') == 'online']
    
    def get_venue_sessions(self):
        """Get all venue (non-online) sessions from schedule_data."""
        self.ensure_one()
        sessions = (self.schedule_data or {}).get('sessions', [])
        return [s for s in sessions if s.get('type') != 'online']
    
    def get_session_by_day(self, day_code):
        """Get sessions for a specific day (MON, TUE, etc.)."""
        self.ensure_one()
        day_code = day_code.upper()
        sessions = (self.schedule_data or {}).get('sessions', [])
        return [s for s in sessions if s.get('day') == day_code]
    
    # =========================
    # MULTI-WEEK DETECTION
    # =========================
    
    def is_multi_week_event(self):
        """
        Detect if this is a multi-week event that should be excluded from
        schedule_data sync (needs sessions feature instead).
        
        Returns:
            bool: True if multi-week pattern detected
        """
        self.ensure_one()
        
        # Check raw text for "N Termine/Abende" pattern
        raw = self.schedule_raw or ''
        if re.search(r'\d+\s+(Termine|Abende)', raw, re.IGNORECASE):
            return True
        
        # Check date span > 28 days
        date_begin = getattr(self, 'date_begin', None)
        date_end = getattr(self, 'date_end', None)
        
        if date_begin and date_end:
            if isinstance(date_begin, datetime):
                date_begin = date_begin.date()
            if isinstance(date_end, datetime):
                date_end = date_end.date()
            
            if (date_end - date_begin).days > 28:
                return True
        
        return False
