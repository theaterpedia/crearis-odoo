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

        products = Product.search([
            ('course_event_ids', '!=', False),
            ('default_code', '!=', False),
        ])

        courses = []
        for p in products:
            courses.append({
                'id': p.id,
                'default_code': p.default_code,
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

        for event in events:
            event_type = event.event_type_id
            shortcode = event_type.name.lower() if event_type else 'unknown'
            item_key = f"{shortcode}_{event.id}"

            # Use event.event fields (PRIMARY), fallback to event.type (TEMPLATE)
            heading = event.name or (event_type.template_heading if event_type else '')
            teasertext = event.teasertext if hasattr(event, 'teasertext') else ''
            if not teasertext and event_type:
                teasertext = event_type.template_teasertext or ''
            cimg = event.cimg if hasattr(event, 'cimg') else ''
            if not cimg and event_type:
                cimg = event_type.template_cimg or ''

            items[item_key] = {
                'ctype': 'event',
                'shortcode': shortcode,
                'title': heading,
                'body': teasertext,
                'image': {
                    'url': self._build_cloudinary_url(cimg),
                    'caption': f"Theaterpädagogik {event_type.name if event_type else ''}",
                },
                'start': event.date_begin.isoformat() if event.date_begin else None,
                'ende': event.date_end.isoformat() if event.date_end else None,
                'ort': event.address_id.contact_address if event.address_id else '',
                'ablauf': event.schedule if hasattr(event, 'schedule') else '',
                'mit': ', '.join(event.user_id.mapped('name')) if event.user_id else '',
            }

        # Build full MDC structure
        mdc = {
            'navigation': False,
            'shortcode': product.default_code.lower() if product.default_code else '',
            'odoo_product_ref': product.default_code or '',
            'odoo_product_id': product.id,
            'heading': product.name,
            'ctype': 'course',
            'items': items,
        }

        return self._to_yaml(mdc)

    def _build_event_mdc(self, event):
        """Build MDC content for a standalone event (Offenes Programm)."""
        event_type = event.event_type_id
        shortcode = event_type.name.lower() if event_type else 'event'

        # Use event.event fields (PRIMARY), fallback to event.type (TEMPLATE)
        heading = event.name or (event_type.template_heading if event_type else '')
        teasertext = event.teasertext if hasattr(event, 'teasertext') else ''
        if not teasertext and event_type:
            teasertext = event_type.template_teasertext or ''
        cimg = event.cimg if hasattr(event, 'cimg') else ''
        if not cimg and event_type:
            cimg = event_type.template_cimg or ''

        # Format heading for MDC: "date time: description **title**"
        date_str = event.date_begin.strftime('%-d.%-m') if event.date_begin else ''
        time_str = event.date_begin.strftime('%H:%M') if event.date_begin else ''

        mdc = {
            'navigation': False,
            'navigation_highlight': '/ausbildung-theaterpaedagogik',
            'ctype': 'event',
            'id': f"{shortcode}_{event.ms_id or event.id}",
            'odoo_event_id': event.id,
            'tag': self._get_event_tag(event),
            'heading': f"{date_str} {time_str}: {heading}" if date_str else heading,
            'description': event.description if hasattr(event, 'description') else '',
            'title': event_type.name if event_type else event.name,
            'start': event.date_begin.strftime('%Y-%m-%d') if event.date_begin else None,
            'ende': event.date_end.strftime('%Y-%m-%d') if event.date_end else None,
            'teaser': teasertext,
            'hero': {
                'height': 'full',
                'image_focus_y': 'cover',
                'image_focus_x': 'center',
                'content': 'banner',
                'content_y': 'bottom',
                'content_width': 'short',
                'cta': {
                    'title': 'anmelden (kostenfrei)' if self._is_free_event(event) else 'anmelden',
                },
            },
            'image': {
                'alt': event_type.name if event_type else 'Event',
                'src': self._build_cloudinary_url(cimg),
            },
            'cssclasses': ['workshop'],
            'views': ['details'],
            'details': self._build_event_details(event),
        }

        return self._to_yaml(mdc)

    def _build_event_details(self, event):
        """Build details section for standalone event."""
        schedule = event.schedule if hasattr(event, 'schedule') else 'Details folgen'
        
        return {
            'programm': {
                'title': 'Programm',
                'agenda': {'style': 'default'},
                'info': {
                    'struktur': f"#### Programm\n{schedule or 'Details folgen'}",
                    'beratung': "#### Beratung\n> nach der Veranstaltung erhältst du ggf. weitere Informationen",
                },
            },
            'konditionen': {
                'title': 'Teilnahme',
                'header': '### Teilnahme',
                'info': {
                    'kosten': self._get_cost_text(event),
                    'storno': "### Abmeldung\n= bitte melde eine Absage bis spätestens 18:00 Uhr am Vorabend",
                },
            },
            'checks': {
                'title': 'Anmelden',
            },
        }

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
        return "### Kosten\nDetails zur Teilnahmegebühr folgen."

    def _to_yaml(self, data):
        """Convert dict to YAML string with MDC frontmatter markers."""
        if yaml:
            yaml_str = yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
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
