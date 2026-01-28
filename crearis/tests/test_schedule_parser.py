# -*- coding: utf-8 -*-
"""
Test helpers for schedule_mixin.

Run in Odoo shell:
    exec(open('/path/to/test_schedule_parser.py').read())
    
Or via heredoc:
    cd /home/persona/crearis/odoo/versions/16.0 && ./odoo/odoo-bin shell ... << 'EOF'
    from crearis.models.schedule_mixin import ScheduleParser, WEEKDAYS
    parser = ScheduleParser()
    ... tests ...
    EOF
"""

# =============================================================================
# STANDALONE TESTS (run outside Odoo)
# =============================================================================

def test_parser_standalone():
    """Test parser without Odoo environment."""
    # Import only the pure Python parts
    import sys
    import re
    from datetime import datetime, timedelta
    
    # Copy the essential constants and class here for standalone testing
    WEEKDAYS_DE = {'MO': 0, 'DI': 1, 'MI': 2, 'DO': 3, 'FR': 4, 'SA': 5, 'SO': 6}
    WEEKDAYS_EN = {'MON': 0, 'TUE': 1, 'WED': 2, 'THU': 3, 'FRI': 4, 'SAT': 5, 'SUN': 6}
    WEEKDAYS = {**WEEKDAYS_DE, **WEEKDAYS_EN}
    WEEKDAY_NAMES = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
    SHORTCODE_PATTERN = r'_([A-Za-z0-9]+)(?::([A-Za-z0-9]+))?_'
    
    class ScheduleParser:
        def __init__(self, locale='de', shortcodes=None):
            self.locale = locale
            self.shortcodes = shortcodes or {'_online_': {'type': 'online'}}
        
        def parse(self, text, date_begin=None, date_end=None):
            if not text:
                return None
            
            result = {
                '$schema': 'schedule_data_v1',
                'source': 'parsed',
                'raw_text': text[:500],
                'sessions': [],
                'summary': {},
                'unparsed_notes': [],
            }
            
            current_context = None
            lines = text.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check for section header (word followed by colon at end)
                header_match = re.match(r'^([A-Za-zÄÖÜäöüß-]+)\s*:\s*$', line)
                if header_match:
                    current_context = header_match.group(1).lower()
                    continue
                
                # Also handle "online: DI 18:00-21:00" on same line
                inline_header = re.match(r'^(online)\s*:\s*(.+)$', line, re.IGNORECASE)
                if inline_header:
                    current_context = 'online'
                    line = inline_header.group(2)
                
                session = self._parse_timeslot(line, current_context, date_begin, date_end)
                if session:
                    result['sessions'].append(session)
            
            result['summary'] = self._calculate_summary(result['sessions'])
            return result if result['sessions'] else None
        
        def _parse_timeslot(self, line, context, date_begin, date_end):
            shortcode_match = re.search(SHORTCODE_PATTERN, line)
            session_type = 'venue'
            location_hint = None
            shortcode_room = None
            
            if shortcode_match:
                shortcode = f'_{shortcode_match.group(1)}_'
                shortcode_room = shortcode_match.group(2)
                for k, v in self.shortcodes.items():
                    if k.lower() == shortcode.lower():
                        session_type = v.get('type', 'venue')
                        location_hint = v.get('name')
                        break
            
            if re.search(r'\bonline\b', line, re.IGNORECASE):
                session_type = 'online'
            
            if context and session_type == 'venue':
                if context == 'online':
                    session_type = 'online'
                else:
                    location_hint = context.title()
            
            weekday_match = re.search(
                rf'({"|".join(WEEKDAYS.keys())})\s*'
                rf'(?:(\d{{1,2}})\.(\d{{1,2}})(?:\.(\d{{2,4}}))?\s*)?'
                rf'(\d{{1,2}}):(\d{{2}})\s*[-–]\s*(\d{{1,2}}):(\d{{2}})',
                line, re.IGNORECASE
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
            
            # Resolve date if present in line
            resolved_date = None
            if date_day and date_month:
                from datetime import datetime
                year = datetime.now().year
                if date_year:
                    year = int(date_year)
                    if year < 100:
                        year += 2000
                try:
                    resolved_date = f'{year}-{int(date_month):02d}-{int(date_day):02d}'
                except ValueError:
                    pass
            
            start_minutes = start_hour * 60 + start_min
            end_minutes = end_hour * 60 + end_min
            if end_minutes < start_minutes:
                end_minutes += 24 * 60
            duration_h = (end_minutes - start_minutes) / 60
            
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
        
        def _calculate_summary(self, sessions):
            total_hours = sum(s.get('duration_h', 0) for s in sessions)
            online_sessions = [s for s in sessions if s.get('type') == 'online']
            online_hours = sum(s.get('duration_h', 0) for s in online_sessions)
            return {
                'total_hours': round(total_hours, 2),
                'online_hours': round(online_hours, 2),
                'venue_hours': round(total_hours - online_hours, 2),
                'has_online': len(online_sessions) > 0,
                'session_count': len(sessions),
                'online_session_count': len(online_sessions),
            }
    
    # Now run the tests
    print("=" * 60)
    print("SCHEDULE PARSER TESTS")
    print("=" * 60)
    
    parser = ScheduleParser()
    
    # Test 1: Basic time slot with online shortcode
    test1 = "FR 18:00-20:00 _online_"
    parser = ScheduleParser()
    result1 = parser.parse(test1)
    print(f"\nTest 1: {test1}")
    print(f"  Sessions: {len(result1['sessions']) if result1 else 0}")
    if result1 and result1['sessions']:
        s = result1['sessions'][0]
        print(f"  Day: {s['day']}, Time: {s['start']}-{s['end']}, Type: {s['type']}")
        assert s['day'] == 'FRI', f"Expected FRI, got {s['day']}"
        assert s['type'] == 'online', f"Expected online, got {s['type']}"
        print("  ✓ PASS")
    
    # Test 2: Section header style
    test2 = """online:
FR 18:00-20:00
München:
SA 09:30-18:30
SO 09:00-15:00
online:
DI 19:30-21:00"""
    result2 = parser.parse(test2)
    print(f"\nTest 2: Multi-line with sections")
    print(f"  Sessions: {len(result2['sessions']) if result2 else 0}")
    if result2:
        online_count = result2['summary']['online_session_count']
        print(f"  Online sessions: {online_count}")
        print(f"  Total hours: {result2['summary']['total_hours']}")
        assert online_count == 2, f"Expected 2 online sessions, got {online_count}"
        print("  ✓ PASS")
    
    # Test 3: Date in line
    test3 = "FR 24.6 18:00-20:00 online"
    result3 = parser.parse(test3)
    print(f"\nTest 3: {test3}")
    if result3 and result3['sessions']:
        s = result3['sessions'][0]
        print(f"  Date resolved: {s['date']}")
        assert s['date'] is not None, "Date should be resolved"
        assert s['date'].endswith('-06-24'), f"Expected date ending with -06-24, got {s['date']}"
        assert s['type'] == 'online', f"Expected online, got {s['type']}"
        print("  ✓ PASS")
    else:
        print("  ✗ FAIL - No sessions parsed")
        assert False, "Test 3 failed"
    
    # Test 4: Venue shortcode
    test4 = "SA 09:00-18:00 _TANZEREI_"
    shortcodes = {
        '_online_': {'type': 'online'},
        '_TANZEREI_': {'type': 'venue', 'raum_id': 8, 'name': 'Tanzerei'},
    }
    parser4 = ScheduleParser(shortcodes=shortcodes)
    result4 = parser4.parse(test4)
    print(f"\nTest 4: {test4}")
    if result4 and result4['sessions']:
        s = result4['sessions'][0]
        print(f"  Type: {s['type']}, Location: {s['location_hint']}")
        assert s['type'] == 'venue', f"Expected venue, got {s['type']}"
        assert s['location_hint'] == 'Tanzerei', f"Expected Tanzerei, got {s['location_hint']}"
        print("  ✓ PASS")
    
    # Test 5: Real DASEi example
    test5 = """online:
FR 18:00-20:00
München:
SA 09:30-18:30
SO 09:00-15:00
online:
DI 19:30-21:00"""
    result5 = parser.parse(test5)
    print(f"\nTest 5: Real DASEi hybrid pattern")
    if result5:
        print(f"  Total sessions: {result5['summary']['session_count']}")
        print(f"  Online sessions: {result5['summary']['online_session_count']}")
        print(f"  Total hours: {result5['summary']['total_hours']}")
        print(f"  Online hours: {result5['summary']['online_hours']}")
        print(f"  Venue hours: {result5['summary']['venue_hours']}")
        assert result5['summary']['session_count'] == 4
        assert result5['summary']['online_session_count'] == 2
        print("  ✓ PASS")
    
    # Test 6: Complex example from diagnostics
    test6 = """online: 
MI 18:00-20:00
Burgstallmühle:
DO 19:00-21:30
FR 09:00-18:30
SA 09:00-18:30
SO 09:00-16:30
online: DI 18:00-21:00"""
    result6 = parser.parse(test6)
    print(f"\nTest 6: Complex Burgstallmühle example")
    if result6:
        print(f"  Total sessions: {result6['summary']['session_count']}")
        for i, s in enumerate(result6['sessions']):
            print(f"    {i+1}. {s['day']} {s['start']}-{s['end']} [{s['type']}] {s.get('location_hint', '')}")
        print(f"  Online hours: {result6['summary']['online_hours']}")
        print(f"  Venue hours: {result6['summary']['venue_hours']}")
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETE")
    print("=" * 60)


# =============================================================================
# ODOO SHELL TESTS
# =============================================================================

ODOO_TEST_SCRIPT = '''
# Run this in Odoo shell to test the mixin with real data

from crearis.models.schedule_mixin import ScheduleParser

# Test with DASEi company shortcodes
company = env['res.company'].browse(11)
print(f"Company: {company.name}")
print(f"Locale: {company.schedule_locale}")
print(f"Shortcodes: {company.schedule_shortcodes}")

# Get a hybrid event
events = env['event.event'].search([
    ('company_id', '=', 11),
    ('sp_textinfo', 'ilike', 'online'),
], limit=5)

for event in events:
    print(f"\\nEvent: {event.name}")
    print(f"  Dates: {event.date_begin} - {event.date_end}")
    print(f"  Raw text: {event.sp_textinfo[:200] if event.sp_textinfo else 'N/A'}...")
    
    # Parse
    shortcodes = company.schedule_shortcodes or {'_online_': {'type': 'online'}}
    parser = ScheduleParser(
        locale=company.schedule_locale or 'de',
        shortcodes=shortcodes
    )
    result = parser.parse(event.sp_textinfo, event.date_begin, event.date_end)
    
    if result:
        print(f"  Sessions: {result['summary']['session_count']}")
        print(f"  Online: {result['summary']['online_session_count']}")
        print(f"  Hours: {result['summary']['total_hours']}")
        for s in result['sessions']:
            print(f"    - {s['day']} {s['start']}-{s['end']} [{s['type']}]")
    else:
        print("  Could not parse")

env.cr.commit()
'''


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    test_parser_standalone()
