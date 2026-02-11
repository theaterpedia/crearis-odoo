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
    - Special shortcodes: _anfrage_, _individuell_, _reihe_
    """
    
    # Special shortcodes with custom behavior
    SPECIAL_SHORTCODES = {'_anfrage_', '_individuell_', '_reihe_'}
    
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
        
        # Check for special shortcodes FIRST
        special_result = self._handle_special_shortcodes(text, date_begin, date_end, result)
        if special_result:
            return special_result
        
        # Track current context (set by section headers)
        current_context = None
        
        # Split by newlines, then expand comma-separated entries
        raw_lines = text.strip().split('\n')
        lines = []
        for raw_line in raw_lines:
            stripped = raw_line.strip()
            if not stripped:
                continue
            # Keep section headers intact (e.g., "online:", "München:")
            if self.header_pattern.match(stripped):
                lines.append(stripped)
            elif ',' in stripped:
                # Split comma-separated entries (e.g., "DO 19:00-21:00, FR 09:00-18:00")
                lines.extend(part.strip() for part in stripped.split(',') if part.strip())
            else:
                lines.append(stripped)
        
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
    
    def _handle_special_shortcodes(self, text, date_begin, date_end, result):
        """
        Handle special shortcodes (_anfrage_, _individuell_, _reihe_) that generate
        sessions programmatically rather than parsing text.
        
        Returns:
            dict: Complete result if special shortcode handled, None otherwise
        """
        text_lower = text.lower()
        
        # =========================
        # _anfrage_ - Times on request
        # =========================
        if '_anfrage_' in text_lower:
            result['source'] = 'shortcode:anfrage'
            result['flags'] = ['issue_schedule']  # Tag for follow-up
            
            if not date_begin or not date_end:
                result['unparsed_notes'].append('_anfrage_: Missing event dates')
                return result
            
            # Convert to date objects
            if isinstance(date_begin, datetime):
                date_begin = date_begin.date()
            if isinstance(date_end, datetime):
                date_end = date_end.date()
            
            # Validate range (max 14 days)
            day_span = (date_end - date_begin).days + 1
            if day_span > 14:
                result['unparsed_notes'].append(f'_anfrage_: Date range too long ({day_span} days)')
                result['flags'].append('range_exceeded')
                return result
            
            # Generate session per day: 09:00-18:00
            current = date_begin
            while current <= date_end:
                result['sessions'].append({
                    'day': WEEKDAY_NAMES[current.weekday()],
                    'date': current.isoformat(),
                    'start': '09:00',
                    'end': '18:00',
                    'duration_h': 9.0,
                    'type': 'venue',
                    'location_hint': None,
                    'notes': 'Zeiten auf Anfrage',
                })
                current += timedelta(days=1)
            
            result['summary'] = self._calculate_summary(result['sessions'])
            return result
        
        # =========================
        # _individuell_ - Individual appointments
        # =========================
        if '_individuell_' in text_lower:
            result['source'] = 'shortcode:individuell'
            
            # Extract original text after shortcode (preserve as notes)
            notes_match = re.search(r'_individuell_\s*\|\s*(.+)', text, re.IGNORECASE | re.DOTALL)
            original_notes = notes_match.group(1).strip() if notes_match else text.replace('_individuell_', '').strip()
            
            result['notes'] = original_notes  # Store original description
            
            if not date_begin:
                result['unparsed_notes'].append('_individuell_: Missing event start date')
                return result
            
            # Convert to date
            if isinstance(date_begin, datetime):
                date_begin = date_begin.date()
            
            # Generate single placeholder session on first day: 09:00-09:00
            result['sessions'].append({
                'day': WEEKDAY_NAMES[date_begin.weekday()],
                'date': date_begin.isoformat(),
                'start': '09:00',
                'end': '09:00',
                'duration_h': 0.0,
                'type': 'individual',  # Special type for individual appointments
                'location_hint': None,
                'notes': original_notes,
            })
            
            result['summary'] = self._calculate_summary(result['sessions'])
            return result
        
        # =========================
        # _reihe_ - Weekly series (Terminreihe)
        # NOTE: Full parsing planned for next sprint
        # Currently only recognizes the normalized format
        # =========================
        if '_reihe_' in text_lower:
            result['source'] = 'shortcode:reihe'
            result['flags'] = ['series_pending']  # Mark for future implementation
            
            # Try to parse: "_reihe_ N Termine WD HH:MM-HH:MM _online_"
            reihe_match = re.search(
                r'_reihe_\s+(\d+)\s+Termine?\s+([A-Z]{2})\s+(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})\s*(_online_)?',
                text, re.IGNORECASE
            )
            
            if reihe_match:
                num_sessions = int(reihe_match.group(1))
                weekday = reihe_match.group(2).upper()
                start_h = int(reihe_match.group(3))
                start_m = int(reihe_match.group(4))
                end_h = int(reihe_match.group(5))
                end_m = int(reihe_match.group(6))
                is_online = bool(reihe_match.group(7))
                
                duration_h = (end_h * 60 + end_m - start_h * 60 - start_m) / 60
                session_type = 'online' if is_online else 'venue'
                
                # For now, create a single "template" session representing the series
                # Full implementation will generate N weekly sessions
                result['series_info'] = {
                    'num_sessions': num_sessions,
                    'weekday': weekday,
                    'start': f'{start_h:02d}:{start_m:02d}',
                    'end': f'{end_h:02d}:{end_m:02d}',
                    'duration_h': round(duration_h, 2),
                    'type': session_type,
                }
                
                # Create placeholder session for first occurrence
                if date_begin:
                    if isinstance(date_begin, datetime):
                        date_begin = date_begin.date()
                    
                    result['sessions'].append({
                        'day': weekday if weekday in WEEKDAY_NAMES else WEEKDAY_NAMES[WEEKDAYS.get(weekday, 0)],
                        'date': date_begin.isoformat(),
                        'start': f'{start_h:02d}:{start_m:02d}',
                        'end': f'{end_h:02d}:{end_m:02d}',
                        'duration_h': round(duration_h, 2),
                        'type': session_type,
                        'location_hint': None,
                        'notes': f'Serie: {num_sessions} Termine',
                    })
                
                result['unparsed_notes'].append(
                    f'Terminreihe: {num_sessions}x {weekday} {start_h:02d}:{start_m:02d}-{end_h:02d}:{end_m:02d} '
                    f'(full series generation pending)'
                )
            else:
                result['unparsed_notes'].append(f'_reihe_: Could not parse format from: {text[:100]}')
            
            result['summary'] = self._calculate_summary(result['sessions'])
            return result
        
        # No special shortcode found
        return None


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
        Also syncs agenda_line_ids if the model supports it.
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
                
                # Sync agenda lines if model supports it (event.event has this)
                if hasattr(record, '_sync_agenda_lines'):
                    record._sync_agenda_lines()
                    _logger.info(
                        "Synced %d agenda lines for %s",
                        len(record.agenda_line_ids),
                        record.display_name
                    )
                # Backward compatibility
                elif hasattr(record, '_sync_session_lines'):
                    record._sync_session_lines()
    
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
