# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json
import io
import re
import zipfile
from datetime import datetime

from odoo import http
from odoo.http import request

try:
    import yaml
except ImportError:
    yaml = None

# Offenes Programm SharePoint contact ID
OFFENES_PROGRAMM_ID = '474'


class MDCGeneratorController(http.Controller):
    """REST API for generating MDC (Markdown Content) files from Odoo data.
    
    Endpoints:
    - GET /api/v1/mdc/course/<product_ref>  - Single course MDC
    - GET /api/v1/mdc/event/<event_id>      - Single event MDC (Offenes Programm)
    - GET /api/v1/mdc/export                - Bulk ZIP export
    """

    # =========================================================================
    # Single Course MDC
    # =========================================================================

    @http.route('/api/v1/mdc/course/<string:product_ref>', type='http',
                auth='public', methods=['GET'], csrf=False)
    def generate_course_mdc(self, product_ref, **kwargs):
        """Generate MDC YAML for a single course product.
        
        Args:
            product_ref: Product default_code (e.g., 'm17e', 'M17E')
            
        Returns:
            JSON with YAML string and metadata
        """
        # API key validation (optional - can be enabled later)
        # if not self._validate_api_key():
        #     return self._json_response({'error': 'Invalid API key'}, 401)

        Product = request.env['product.template'].sudo()

        product = Product.search([('default_code', '=ilike', product_ref)], limit=1)
        if not product:
            return self._json_response({'error': 'Product not found'}, 404)

        events = self._get_course_events(product)
        mdc_content = self._build_course_mdc(product, events)

        return self._json_response({
            'product_ref': product_ref,
            'product_id': product.id,
            'filename': f"einstiege-ins-theaterspiel_{product_ref.lower()}.md",
            'event_count': len(events),
            'yaml': mdc_content,
        })

    # =========================================================================
    # Single Event MDC (Offenes Programm)
    # =========================================================================

    @http.route('/api/v1/mdc/event/<int:event_id>', type='http',
                auth='public', methods=['GET'], csrf=False)
    def generate_event_mdc(self, event_id, **kwargs):
        """Generate MDC YAML for a single standalone event.
        
        Args:
            event_id: Odoo event.event ID
            
        Returns:
            JSON with YAML string and metadata
        """
        Event = request.env['event.event'].sudo()

        event = Event.browse(event_id)
        if not event.exists():
            return self._json_response({'error': 'Event not found'}, 404)

        mdc_content = self._build_event_mdc(event)
        filename = self._build_event_filename(event)

        return self._json_response({
            'event_id': event_id,
            'filename': filename,
            'yaml': mdc_content,
        })

    # =========================================================================
    # Bulk Export as ZIP
    # =========================================================================

    @http.route('/api/v1/mdc/export', type='http',
                auth='public', methods=['GET'], csrf=False)
    def export_mdc_zip(self, year=None, include_courses='true', include_events='true', **kwargs):
        """Export all MDC files as ZIP archive.
        
        Query params:
            year: Filter by year (e.g., 2026). Default: current year
            include_courses: Include course products (default: true)
            include_events: Include standalone events (default: true)
            
        Returns:
            ZIP file download
        """
        year = int(year) if year else datetime.now().year
        include_courses = include_courses in [True, 'true', '1', 'yes']
        include_events = include_events in [True, 'true', '1', 'yes']

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:

            # Export course products
            if include_courses:
                courses = self._get_courses_for_year(year)
                for product in courses:
                    events = self._get_course_events(product)
                    mdc_content = self._build_course_mdc(product, events)
                    filename = f"courses/einstiege-ins-theaterspiel_{product.default_code.lower()}.md"
                    zf.writestr(filename, mdc_content)

            # Export standalone events (Offenes Programm)
            if include_events:
                events = self._get_open_program_events(year)
                for event in events:
                    mdc_content = self._build_event_mdc(event)
                    filename = f"events/{self._build_event_filename(event)}"
                    zf.writestr(filename, mdc_content)

        zip_buffer.seek(0)

        return request.make_response(
            zip_buffer.getvalue(),
            headers=[
                ('Content-Type', 'application/zip'),
                ('Content-Disposition', f'attachment; filename="mdc_export_{year}.zip"'),
            ]
        )

    # =========================================================================
    # List Endpoints
    # =========================================================================

    @http.route('/api/v1/mdc/courses', type='http',
                auth='public', methods=['GET'], csrf=False)
    def list_courses(self, **kwargs):
        """List all available course products with event counts."""
        Product = request.env['product.template'].sudo()

        # Search for products with ms_contact_id (synced from SharePoint)
        # and non-empty course_event_ids (has events mapped)
        products = Product.search([
            ('ms_contact_id', '!=', False),
        ])

        # Filter to only products with actual events
        products = products.filtered(lambda p: p.course_event_ids and p.course_event_ids != {})

        courses = []
        for p in products:
            courses.append({
                'id': p.id,
                'default_code': p.default_code or p.ms_contact_id,
                'name': p.name,
                'course_program': p.course_program,
                'course_year': p.course_year,
                'course_type': p.course_type,
                'event_count': p.course_event_count,
                'ms_contact_id': p.ms_contact_id,
            })

        return self._json_response({
            'count': len(courses),
            'courses': courses,
        })

    @http.route('/api/v1/mdc/events', type='http',
                auth='public', methods=['GET'], csrf=False)
    def list_open_events(self, year=None, **kwargs):
        """List all Offenes Programm events for a year."""
        year = int(year) if year else datetime.now().year
        events = self._get_open_program_events(year)

        event_list = []
        for e in events:
            event_list.append({
                'id': e.id,
                'name': e.name,
                'event_type': e.event_type_id.name if e.event_type_id else None,
                'date_begin': e.date_begin.isoformat() if e.date_begin else None,
                'date_end': e.date_end.isoformat() if e.date_end else None,
                'ms_id': e.ms_id,
            })

        return self._json_response({
            'year': year,
            'count': len(event_list),
            'events': event_list,
        })

    # =========================================================================
    # Builder Methods
    # =========================================================================

    def _build_course_mdc(self, product, events):
        """Build MDC content for a course product."""
        items = {}
        
        # Sort events by date
        sorted_events = sorted(events, key=lambda e: e.date_begin or datetime.min)

        for event in sorted_events:
            event_type = event.event_type_id
            shortcode = event_type.name.lower() if event_type else 'unknown'
            item_key = f"{shortcode}_{event.id}"

            # Use event.event fields (PRIMARY), fallback to event.type (TEMPLATE)
            event_title = event.name or (event_type.template_heading if event_type else '')
            teasertext = self._safe_string(event.teasertext if hasattr(event, 'teasertext') else '')
            if not teasertext and event_type:
                teasertext = self._safe_string(event_type.template_teasertext or '')
            cimg = event.cimg if hasattr(event, 'cimg') else ''
            if not cimg and event_type:
                cimg = event_type.template_cimg or ''
            
            # Build tag (date range text)
            tag = self._build_event_tag_text(event)

            items[item_key] = {
                'ctype': 'event',
                'shortcode': shortcode,
                'tag': tag,
                'title': event_title,
                'image': {
                    'url': self._build_cloudinary_url(cimg),
                    'caption': f"Theaterpädagogik {event_type.name if event_type else ''}",
                },
                'body': teasertext,
                'start': event.date_begin.isoformat() if event.date_begin else None,
                'ende': event.date_end.isoformat() if event.date_end else None,
                'ort': self._format_address(event.address_id) if event.address_id else '',
                'ablauf': self._safe_string(event.schedule if hasattr(event, 'schedule') else ''),
                'mit': ', '.join(event.user_id.mapped('name')) if event.user_id else '',
            }

        # Get course date range from events
        course_start = sorted_events[0].date_begin if sorted_events else None
        course_end = sorted_events[-1].date_end if sorted_events else None
        
        # Build course title and heading
        course_title = self._get_course_title(product)
        course_heading = self._build_course_heading(product, course_start, course_end)
        course_description = self._get_course_description(product, course_start, course_end)

        # Build full MDC structure
        mdc = {
            'navigation': False,
            'navigation_highlight': '/ausbildung-theaterpaedagogik/einstiege',
            'shortcode': product.default_code.lower() if product.default_code else '',
            'heading': course_heading,
            'start': course_start.strftime('%Y-%m-%d') if course_start else None,
            'end': course_end.strftime('%Y-%m-%d') if course_end else None,
            'ctype': 'course',
            'tag': 'course',
            'description': course_description,
            'title': course_title,
            'cssclasses': ['course'],
            'views': ['product', 'details'],
            'details': self._build_course_details(product),
            'product': self._build_course_product_section(product, len(sorted_events), course_start, course_end),
            'items': items,
        }

        return self._to_yaml(mdc)

    def _get_course_title(self, product):
        """Get course title (e.g., 'Einstiege ins Theaterspiel')."""
        # For block/day courses, use standard title
        if product.course_type in ('block', 'day'):
            return 'Einstiege ins Theaterspiel'
        # For profile courses
        if product.course_type == 'profile':
            return f"Profil {product.course_program}"
        return product.name

    def _build_course_heading(self, product, start_date, end_date):
        """Build course heading like '**Title** Location dates // description'."""
        title = self._get_course_title(product)
        location = self._get_course_location(product)
        
        # Format date range - show year on start if years differ
        if start_date and end_date:
            if start_date.year != end_date.year:
                date_range = f"{start_date.strftime('%-d.%-m.%Y')} - {end_date.strftime('%-d.%-m.%Y')}"
            else:
                date_range = f"{start_date.strftime('%-d.%-m')} - {end_date.strftime('%-d.%-m.%Y')}"
        elif start_date:
            date_range = start_date.strftime('%Y')
        else:
            date_range = ''
        
        # Build description based on course type
        if product.course_type == 'block':
            desc = 'Blockseminarverlauf'
        elif product.course_type == 'day':
            desc = 'Tageskursverlauf'
        else:
            desc = ''
        
        return f"**{title}** {location} {date_range} // {desc}".strip()

    def _get_course_location(self, product):
        """Get course location from program (M=München, N=Nürnberg, etc.)."""
        locations = {
            'M': 'München',
            'N': 'Nürnberg',
            'ZR': 'Region',
            'ZT': 'Theater',
        }
        return locations.get(product.course_program, '')

    def _get_course_description(self, product, start_date, end_date):
        """Build course description."""
        title = self._get_course_title(product)
        code = product.default_code.upper() if product.default_code else ''
        location = self._get_course_location(product)
        
        if start_date and end_date:
            date_range = f"{start_date.strftime('%-d.%-m')} - {end_date.strftime('%-d.%-m.%Y')}"
        else:
            date_range = product.course_year or ''
        
        desc_type = 'Blockseminarverlauf' if product.course_type == 'block' else 'Tageskursverlauf'
        
        return f"Weiterbildung Theaterpädagogik - Kurs {code} {location} {date_range} // {desc_type} {location}"

    def _build_course_details(self, product):
        """Build details section for course."""
        return {
            'programm': {
                'title': 'Programm & Struktur',
                'header': '## Programm & Struktur',
                'info': {
                    'struktur': self._get_course_struktur(product),
                    'beratung': "#### individuelle Fachberatung vereinbaren\n- Ausbildung oder Weiterbildung? Format?\n- Fördermöglichkeiten\n- Fortsetzung Aufbaustufe möglich mit Abschluss Theaterpädagog:in (BuT)",
                },
            },
            'konditionen': {
                'title': 'Kosten & Konditionen',
                'header': '## Kosten & Konditionen',
                'info': {
                    'kosten': self._get_course_kosten(product),
                },
            },
        }

    def _get_course_struktur(self, product):
        """Get course structure text."""
        if product.course_type == 'block':
            return "- **SEMINARBLOCK 1** (3-4 Tage im Seminarhaus)\n- **SEMINARBLOCK 2** (4 Tage)\n- **1 Basisblock** (= Basistag +1 Termin)\n- **SUMME** mind. 120 UE"
        elif product.course_type == 'day':
            return "- **6 TAGESSEMINARE** (So. ganztags + 2 Abende)\n- **1 Basisblock** (= Basistag +1 Termin)\n- **SUMME** mind. 120 UE"
        return "Details folgen"

    def _get_course_kosten(self, product):
        """Get course cost text."""
        return "### Teilnahmegebühr\n- Kursgebühr: Details folgen\n- Anmeldung erforderlich\n- Zahlung: auf Rechnung in Raten"

    def _build_course_product_section(self, product, event_count, start_date, end_date):
        """Build product section for course."""
        title = self._get_course_title(product)
        location = self._get_course_location(product)
        
        # German month abbreviations
        months_de = ['JAN', 'FEB', 'MÄR', 'APR', 'MAI', 'JUN', 'JUL', 'AUG', 'SEP', 'OKT', 'NOV', 'DEZ']
        
        if start_date and end_date:
            start_month = months_de[start_date.month - 1]
            end_month = months_de[end_date.month - 1]
            date_range = f"{start_month} - {end_month} {end_date.year}"
        else:
            date_range = product.course_year or ''
        
        return {
            'header': f"## {event_count} Kurseinheiten\nIn prägnanten Einheiten wirst Du beide Wege erleben, verstehen und selber anleiten: Du lernst die Methoden, die Leitungshaltung und typische Abläufe.",
            'footer': f"## {date_range} // {location} **{title}**",
        }

    def _build_event_tag_text(self, event):
        """Build tag text for event (date range description)."""
        if not event.date_begin:
            return ''
        
        start = event.date_begin
        end = event.date_end
        
        # German day names
        days = ['Mo.', 'Di.', 'Mi.', 'Do.', 'Fr.', 'Sa.', 'So.']
        start_day = days[start.weekday()]
        
        # Check if schedule mentions online
        schedule = self._safe_string(event.schedule if hasattr(event, 'schedule') else '')
        has_online = 'online' in schedule.lower() if schedule else False
        online_suffix = ' + Abende online' if has_online else ''
        
        if end and end.date() != start.date():
            end_day = days[end.weekday()]
            return f"{start_day}, {start.day}.{start.month}. bis {end_day}, {end.day}.{end.month}{online_suffix}"
        else:
            return f"{start_day}, {start.day}.{start.month}. ganztags{online_suffix}"

    def _format_address(self, address):
        """Format address for display."""
        if not address:
            return ''
        parts = []
        if address.name:
            parts.append(address.name)
        if address.street:
            parts.append(address.street)
        if address.street2:
            parts.append(address.street2)
        city_line = f"{address.zip or ''} {address.city or ''}".strip()
        if city_line:
            parts.append(city_line)
        return '\n'.join(parts)

    def _build_event_mdc(self, event):
        """Build MDC content for a standalone event (Offenes Programm)."""
        event_type = event.event_type_id
        shortcode = event_type.name.lower() if event_type else 'event'

        # Use event.event fields (PRIMARY), fallback to event.type (TEMPLATE)
        # Event name is the full title, event_type.name is the shortcode (e.g., "LR")
        event_title = self._get_event_title(event)
        heading = event.name or (event_type.template_heading if event_type else '')
        teasertext = self._safe_string(event.teasertext if hasattr(event, 'teasertext') else '')
        if not teasertext and event_type:
            teasertext = self._safe_string(event_type.template_teasertext or '')
        cimg = event.cimg if hasattr(event, 'cimg') else ''
        if not cimg and event_type:
            cimg = event_type.template_cimg or ''
        
        # Get image alt text from event or derive from title
        image_alt = self._get_image_alt(event)

        # Format heading for MDC: "ORT D.-D.M // Kurzbeschreibung **Titel**"
        heading_formatted = self._format_event_heading(event, event_title)
        
        # Description - convert Markup to plain string
        description = self._safe_string(event.description if hasattr(event, 'description') else '')

        mdc = {
            'publish': 'draft',
            'id': f"{shortcode}_{event.ms_id or event.id}",
            'heading': heading_formatted,
            'description': description or teasertext,
            'teaser': teasertext,
            'title': event_title,
            'cssclasses': ['workshop'],
            'start': event.date_begin.strftime('%Y-%m-%d') if event.date_begin else None,
            'ende': event.date_end.strftime('%Y-%m-%d') if event.date_end else None,
            'hero': {
                'height': 'prominent',
                'image_focus_y': 'cover',
                'image_focus_x': 'center',
                'content': 'banner',
                'content_y': 'top',
                'content_width': 'short',
                'cta': {
                    'title': 'jetzt anmelden',
                },
            },
            'image': {
                'alt': image_alt,
                'src': self._build_cloudinary_url(cimg),
            },
            'views': ['details'],
            'details': self._build_event_details(event),
        }

        return self._to_yaml(mdc)

    def _get_event_title(self, event):
        """Extract meaningful title from event name.
        
        Event name format: "Kurzbeschreibung **Titel**" or "Titel"
        Returns the part in **bold** or the whole name.
        """
        event_name = event.name or ''
        # Check for **title** pattern
        import re
        match = re.search(r'\*\*(.+?)\*\*', event_name)
        if match:
            return match.group(1)
        # Fallback to event name without location/date prefix
        return event_name

    def _format_event_heading(self, event, title):
        """Format heading like: 'ORT D.-D.M // Kurzbeschreibung **Titel**'"""
        if not event.date_begin:
            return event.name or title
        
        # Get location abbreviation
        location = self._get_location_abbrev(event)
        
        # Format date range: "4.-6.4" or just "4.4" if single day
        start = event.date_begin
        end = event.date_end
        
        if end and end.date() != start.date():
            date_str = f"{start.day}.-{end.day}.{start.month}"
        else:
            date_str = f"{start.day}.{start.month}"
        
        # Use event name which should already contain **title**
        return f"{location} {date_str} // {event.name}" if location else f"{date_str} // {event.name}"

    def _get_location_abbrev(self, event):
        """Get location abbreviation (MÜ for München, NÜ for Nürnberg, etc.)"""
        if not event.address_id:
            return ''
        city = event.address_id.city or ''
        abbrevs = {
            'münchen': 'MÜ',
            'munich': 'MÜ',
            'nürnberg': 'NÜ',
            'nuremberg': 'NÜ',
        }
        return abbrevs.get(city.lower(), city[:2].upper() if city else '')

    def _get_image_alt(self, event):
        """Get alt text for event image."""
        # Try to extract from title
        title = self._get_event_title(event)
        if title and title != event.name:
            return title
        # Fallback to event type description or name
        if event.event_type_id:
            return event.event_type_id.template_heading or event.event_type_id.name
        return 'Workshop'

    def _safe_string(self, value):
        """Convert value to plain string, handling Markup objects."""
        if value is None:
            return ''
        # Convert Markup and other objects to string
        return str(value) if value else ''

    def _build_event_details(self, event):
        """Build details section for standalone event."""
        schedule = self._safe_string(event.schedule if hasattr(event, 'schedule') else '')
        location = self._get_full_location(event)
        
        # Build schedule info with location
        schedule_text = schedule or 'Details folgen'
        if location:
            schedule_text = f"{schedule_text}\n\n{location}"
        
        return {
            'programm': {
                'title': 'Programm',
                'header': '## **Programm**',
                'info': {
                    'struktur': schedule_text,
                },
            },
            'konditionen': {
                'title': 'Konditionen',
                'info': {
                    'kosten': self._get_cost_text(event),
                    'storno': "### Widerruf & Storno\n- 14 Tage Widerruf\n- bis 6 Wochen vor Veranstaltungsbeginn kostenfreie Stornierung formlos schriftlich\n- danach Einbehalt von 50% der Teilnahmegebühr",
                },
            },
        }

    def _get_full_location(self, event):
        """Get full location string for event."""
        if not event.address_id:
            return ''
        addr = event.address_id
        parts = []
        if addr.city:
            parts.append(addr.city)
        if addr.street:
            parts.append(addr.street)
        return ', '.join(parts) if parts else ''

    def _build_event_filename(self, event):
        """Build filename for standalone event.
        
        Convention: {year_digit}{month}.{name}-{shortcode}_{record_id}.md
        Example: 704.info-teaser-aa_1580.md
        """
        if not event.date_begin:
            return f"event_{event.id}.md"

        year_digit = str(event.date_begin.year)[-1]
        month = f"{event.date_begin.month:02d}"

        event_type = event.event_type_id
        shortcode = event_type.name.lower() if event_type else 'event'

        # Slugify event name
        name_slug = (event.name or 'event').lower()
        name_slug = name_slug.replace('**', '').replace('*', '')
        name_slug = '-'.join(name_slug.split()[:3])
        name_slug = re.sub(r'[^a-z0-9-]', '', name_slug)

        record_id = event.ms_id or str(event.id)

        return f"{year_digit}{month}.{name_slug}-{shortcode}_{record_id}.md"

    # =========================================================================
    # Query Methods
    # =========================================================================

    def _get_course_events(self, product):
        """Get events linked to course via JSONB mapping, sorted by order."""
        Event = request.env['event.event'].sudo()

        if not product.course_event_ids:
            return Event.browse()

        # Extract event_ids and order from metadata structure
        events_with_order = []
        for shortcode, meta in product.course_event_ids.items():
            event_id = meta.get('event_id') if isinstance(meta, dict) else meta
            order = meta.get('order', 99) if isinstance(meta, dict) else 99
            if event_id:
                events_with_order.append((event_id, order, shortcode))

        # Sort by order field
        events_with_order.sort(key=lambda x: x[1])

        event_ids = [e[0] for e in events_with_order]
        return Event.browse(event_ids)

    def _get_courses_for_year(self, year):
        """Get course products with events in the given year."""
        Product = request.env['product.template'].sudo()

        return Product.search([
            ('course_event_ids', '!=', False),
            ('default_code', '!=', False),
            ('ms_contact_id', '!=', OFFENES_PROGRAMM_ID),  # Exclude Offenes Programm
        ])

    def _get_open_program_events(self, year):
        """Get standalone events for 'Offenes Programm' in given year.
        
        These are events registered to the special contact '_Offenes Programm' (id: 474)
        """
        Event = request.env['event.event'].sudo()
        Product = request.env['product.template'].sudo()

        # Find the "Offenes Programm" product by ms_contact_id
        open_program = Product.search([('ms_contact_id', '=', OFFENES_PROGRAMM_ID)], limit=1)

        if not open_program or not open_program.course_event_ids:
            # Fallback: get events by date range without course assignment
            return Event.search([
                ('date_begin', '>=', f'{year}-01-01'),
                ('date_begin', '<', f'{year + 1}-01-01'),
            ], order='date_begin')

        # Extract event_ids from metadata structure
        event_ids = []
        for shortcode, meta in open_program.course_event_ids.items():
            event_id = meta.get('event_id') if isinstance(meta, dict) else meta
            if event_id:
                event_ids.append(event_id)
        
        events = Event.browse(event_ids)

        # Filter by year
        return events.filtered(
            lambda e: e.date_begin and e.date_begin.year == year
        ).sorted(key=lambda e: e.date_begin)

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _build_cloudinary_url(self, cimg_code):
        """Build full Cloudinary URL from code."""
        if not cimg_code:
            return ''
        if cimg_code.startswith('http'):
            return cimg_code
        return f"https://res.cloudinary.com/little-papillon/image/upload/w_400/{cimg_code}"

    def _get_event_tag(self, event):
        """Get tag for event (online, präsenz, etc.)."""
        if event.address_id:
            return 'präsenz'
        return 'online'

    def _is_free_event(self, event):
        """Check if event is free (kostenfrei)."""
        event_type = event.event_type_id
        if event_type and event_type.name.upper() in ['AA', 'INFO']:
            return True
        return False

    def _get_cost_text(self, event):
        """Get cost description for event."""
        if self._is_free_event(event):
            return "### die Teilnahme ist kostenfrei\nSei bitte voll präsent."
        # TODO: Get actual price from event/product if available
        return "### Teilnahmegebühr: € --,--\n- Anmeldung bis X Wochen vor Beginn\n- Zahlung: auf Rechnung"

    def _to_yaml(self, data):
        """Convert dict to YAML string with MDC frontmatter markers."""
        if yaml:
            # Use block style for multiline strings, allow unicode
            yaml_str = yaml.dump(
                data, 
                allow_unicode=True, 
                default_flow_style=False, 
                sort_keys=False,
                width=1000,  # Prevent line wrapping
            )
        else:
            # Fallback to JSON if yaml not available
            yaml_str = json.dumps(data, ensure_ascii=False, indent=2)
        return f"---\n{yaml_str}---\n"

    def _json_response(self, data, status=200):
        """Create JSON HTTP response."""
        return request.make_response(
            json.dumps(data, ensure_ascii=False, indent=2),
            headers=[('Content-Type', 'application/json; charset=utf-8')],
            status=status,
        )

    def _validate_api_key(self):
        """Validate API key from request header (optional security)."""
        api_key = request.httprequest.headers.get('X-API-Key')
        expected_key = request.env['ir.config_parameter'].sudo().get_param('dasei.mdc_api_key')
        
        if not expected_key:
            # If no key configured, allow all requests
            return True
        
        return api_key and api_key == expected_key
