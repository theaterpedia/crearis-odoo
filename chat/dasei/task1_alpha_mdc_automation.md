# Task 1: Automated MDC Generation from Odoo

*Plan Document - Alpha Version - Updated: 2025-12-28*

---

## Overview

This document describes how to automate the generation of MDC files by pulling content from Odoo `event.event` records and mapping course-event relationships from SharePoint to Odoo.

## Goals

1. **1.1** YAML content in MDC files should be sourced from Odoo `event.event` fields (heading, teasertext, cimg)
2. **1.2** Event-to-course mapping (from SharePoint `plan_veranstaltungsteilnehmer`) should be replicated in Odoo
3. **1.3** "Offenes Programm" events (standalone events without course product) should be exported as individual MDC files

---

## Part 1.1: Event → MDC YAML Mapping

### Field Mapping (Updated: Use event.event, not event.type)

| MDC YAML Field | Odoo Field | Source | Notes |
|----------------|------------|--------|-------|
| `shortcode` | `event_type_id.name` | event.type | Event type code (A1, A2, AA, etc.) |
| `title` / `heading` | `name` | **event.event** | Event heading (synced from SharePoint oheading) |
| `body` / `teaser` | `teasertext` | **event.event** | Description/teaser text |
| `image.url` | `cimg` | **event.event** | Cloudinary image reference |
| `start` | `date_begin` | event.event | Event start datetime |
| `ende` | `date_end` | event.event | Event end datetime |
| `ort` | `address_id` | event.event | Location address |
| `ablauf` | `schedule` | event.event | Schedule text |
| `mit` | `trainer_ids` | event.event | Trainer name(s) |

### Odoo event.event Fields (from crearis_agenda sync)

```python
# Current fields in event.event (synced from SharePoint plan_veranstaltungen)
class EventEvent(models.Model):
    _inherit = 'event.event'
    
    # Core fields
    name = fields.Char()                    # Heading: "Kurzbeschreibung **Veranstaltungstitel**"
    teasertext = fields.Text()              # Teaser/description text
    cimg = fields.Char()                    # Cloudinary image code or URL
    schedule = fields.Text()                # Schedule/ablauf text
    
    # Dates
    date_begin = fields.Datetime()
    date_end = fields.Datetime()
    
    # Relations
    event_type_id = fields.Many2one()       # Links to event.type (for shortcode)
    address_id = fields.Many2one()          # Location
    
    # Sync fields
    ms_id = fields.Char()                   # SharePoint item ID
    ms_version = fields.Char()              # ETag for change detection
```

### Data Flow: event.type as Template, event.event as Instance

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Odoo Backend                                 │
│                                                                      │
│  ┌─────────────────────────┐                                        │
│  │ event.type              │  TEMPLATE (fallback values)            │
│  │ - name: 'A1'            │  - Used for shortcode                  │
│  │ - template_heading      │  - Fallback if event.name empty        │
│  │ - template_teasertext   │  - Fallback if event.teasertext empty  │
│  │ - template_cimg         │  - Fallback if event.cimg empty        │
│  └───────────┬─────────────┘                                        │
│              │                                                       │
│              │ event_type_id                                        │
│              ▼                                                       │
│  ┌─────────────────────────┐                                        │
│  │ event.event             │  INSTANCE (actual values - preferred)  │
│  │ - name (heading)        │  ◄─ PRIMARY source for MDC             │
│  │ - teasertext            │  ◄─ PRIMARY source for MDC             │
│  │ - cimg                  │  ◄─ PRIMARY source for MDC             │
│  │ - date_begin, date_end  │                                        │
│  │ - schedule              │                                        │
│  └─────────────────────────┘                                        │
└─────────────────────────────────────────────────────────────────────┘
```

### API Endpoint for MDC Generation

```python
# In agenda_dasei module: controllers/mdc_generator.py

from odoo import http
from odoo.http import request
import yaml
import zipfile
import io
from datetime import datetime

class MDCGeneratorController(http.Controller):

    # =========================================================================
    # Single Course MDC
    # =========================================================================
    
    @http.route('/api/v1/mdc/course/<string:product_ref>', type='http', 
                auth='api_key', methods=['GET'], csrf=False)
    def generate_course_mdc(self, product_ref, **kwargs):
        """Generate MDC YAML for a single course product
        
        Returns JSON with YAML string.
        """
        Product = request.env['product.template'].sudo()
        
        product = Product.search([('default_code', '=ilike', product_ref)], limit=1)
        if not product:
            return self._json_response({'error': 'Product not found'}, 404)
        
        events = self._get_course_events(product)
        mdc_content = self._build_course_mdc(product, events)
        
        return self._json_response({
            'product_ref': product_ref,
            'filename': f"einstiege-ins-theaterspiel_{product_ref.lower()}.md",
            'yaml': mdc_content,
        })
    
    # =========================================================================
    # Single Event MDC (Offenes Programm)
    # =========================================================================
    
    @http.route('/api/v1/mdc/event/<int:event_id>', type='http', 
                auth='api_key', methods=['GET'], csrf=False)
    def generate_event_mdc(self, event_id, **kwargs):
        """Generate MDC YAML for a single standalone event
        
        Returns JSON with YAML string.
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
                auth='api_key', methods=['GET'], csrf=False)
    def export_mdc_zip(self, year=None, include_courses=True, include_events=True, **kwargs):
        """Export all MDC files as ZIP archive
        
        Query params:
        - year: Filter by year (e.g., 2026)
        - include_courses: Include course products (default: true)
        - include_events: Include standalone events (default: true)
        
        Returns: ZIP file with all MDC files
        """
        year = int(year) if year else datetime.now().year
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            
            # Export course products
            if include_courses in [True, 'true', '1']:
                courses = self._get_courses_for_year(year)
                for product in courses:
                    events = self._get_course_events(product)
                    mdc_content = self._build_course_mdc(product, events)
                    filename = f"courses/einstiege-ins-theaterspiel_{product.default_code.lower()}.md"
                    zf.writestr(filename, mdc_content)
            
            # Export standalone events (Offenes Programm)
            if include_events in [True, 'true', '1']:
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
    # Builder Methods
    # =========================================================================
    
    def _build_course_mdc(self, product, events):
        """Build MDC content for a course product"""
        items = {}
        
        for event in events:
            event_type = event.event_type_id
            shortcode = event_type.name.lower() if event_type else 'unknown'
            item_key = f"{shortcode}_{event.id}"
            
            # Use event.event fields (PRIMARY), fallback to event.type (TEMPLATE)
            heading = event.name or (event_type.template_heading if event_type else '')
            teasertext = event.teasertext or (event_type.template_teasertext if event_type else '')
            cimg = event.cimg or (event_type.template_cimg if event_type else '')
            
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
                'ablauf': event.schedule or '',
                'mit': ', '.join(event.user_id.mapped('name')) if event.user_id else '',
            }
        
        # Build full MDC structure
        mdc = {
            'navigation': False,
            'shortcode': product.default_code.lower(),
            'odoo_product_ref': product.default_code,
            'heading': product.name,
            'ctype': 'course',
            'items': items,
        }
        
        return f"---\n{yaml.dump(mdc, allow_unicode=True, default_flow_style=False, sort_keys=False)}---\n"
    
    def _build_event_mdc(self, event):
        """Build MDC content for a standalone event (Offenes Programm)"""
        event_type = event.event_type_id
        shortcode = event_type.name.lower() if event_type else 'event'
        
        # Use event.event fields (PRIMARY), fallback to event.type (TEMPLATE)
        heading = event.name or (event_type.template_heading if event_type else '')
        teasertext = event.teasertext or (event_type.template_teasertext if event_type else '')
        cimg = event.cimg or (event_type.template_cimg if event_type else '')
        
        # Format heading for MDC: "date time: description **title**"
        date_str = event.date_begin.strftime('%-d.%-m') if event.date_begin else ''
        time_str = event.date_begin.strftime('%H:%M') if event.date_begin else ''
        
        mdc = {
            'navigation': False,
            'navigation_highlight': '/ausbildung-theaterpaedagogik',
            'ctype': 'event',
            'id': f"{shortcode}_{event.ms_id or event.id}",
            'tag': self._get_event_tag(event),
            'heading': f"{date_str} {time_str}: {heading}",
            'description': event.description or '',
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
                    'title': 'anmelden' if not self._is_free_event(event) else 'anmelden (kostenfrei)',
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
        
        return f"---\n{yaml.dump(mdc, allow_unicode=True, default_flow_style=False, sort_keys=False)}---\n"
    
    def _build_event_details(self, event):
        """Build details section for standalone event"""
        return {
            'programm': {
                'title': 'Programm',
                'agenda': {'style': 'default'},
                'info': {
                    'struktur': f"#### Programm\n{event.schedule or 'Details folgen'}",
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
        """Build filename for standalone event
        
        Convention: {year_digit}{month}.{name}-{shortcode}_{record_id}.md
        Example: 704.info-teaser-aa_1580.md
        - 7 = year 2027 (last digit)
        - 04 = month April
        - info-teaser = event name slugified
        - aa = shortcode
        - 1580 = SharePoint record ID (ms_id)
        """
        if not event.date_begin:
            return f"event_{event.id}.md"
        
        year_digit = str(event.date_begin.year)[-1]  # Last digit of year
        month = f"{event.date_begin.month:02d}"
        
        event_type = event.event_type_id
        shortcode = event_type.name.lower() if event_type else 'event'
        
        # Slugify event name
        name_slug = (event.name or 'event').lower()
        name_slug = name_slug.replace('**', '').replace('*', '')
        name_slug = '-'.join(name_slug.split()[:3])  # First 3 words
        import re
        name_slug = re.sub(r'[^a-z0-9-]', '', name_slug)
        
        record_id = event.ms_id or str(event.id)
        
        return f"{year_digit}{month}.{name_slug}-{shortcode}_{record_id}.md"
    
    # =========================================================================
    # Query Methods
    # =========================================================================
    
    def _get_course_events(self, product):
        """Get events linked to course via JSONB mapping
        
        JSONB structure: {"a0": {"event_id": 1328, "order": 1}, ...}
        """
        Event = request.env['event.event'].sudo()
        
        if not product.course_event_ids:
            return Event.browse()
        
        # Extract event_ids and order from metadata structure
        events_with_order = []
        for shortcode, meta in product.course_event_ids.items():
            event_id = meta.get('event_id') if isinstance(meta, dict) else meta
            order = meta.get('order', 99) if isinstance(meta, dict) else 99
            events_with_order.append((event_id, order, shortcode))
        
        # Sort by order field
        events_with_order.sort(key=lambda x: x[1])
        
        event_ids = [e[0] for e in events_with_order]
        return Event.browse(event_ids)
    
    def _get_courses_for_year(self, year):
        """Get course products with events in the given year"""
        Product = request.env['product.template'].sudo()
        
        return Product.search([
            ('course_event_ids', '!=', False),
            ('default_code', '!=', False),
        ])
    
    def _get_open_program_events(self, year):
        """Get standalone events for 'Offenes Programm' in given year
        
        These are events registered to the special contact '_Offenes Programm' (id: 474)
        """
        Event = request.env['event.event'].sudo()
        Product = request.env['product.template'].sudo()
        
        # Find the "Offenes Programm" product by ms_contact_id
        open_program = Product.search([('ms_contact_id', '=', '474')], limit=1)
        
        if not open_program or not open_program.course_event_ids:
            # Fallback: get events by date range without course assignment
            return Event.search([
                ('date_begin', '>=', f'{year}-01-01'),
                ('date_begin', '<', f'{year + 1}-01-01'),
                # Add filter for "open" events if needed
            ])
        
        # Extract event_ids from metadata structure
        event_ids = [
            meta.get('event_id') if isinstance(meta, dict) else meta
            for meta in open_program.course_event_ids.values()
        ]
        events = Event.browse(event_ids)
        
        # Filter by year
        return events.filtered(
            lambda e: e.date_begin and e.date_begin.year == year
        ).sorted(key=lambda e: e.date_begin)
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _build_cloudinary_url(self, cimg_code):
        if not cimg_code:
            return ''
        if cimg_code.startswith('http'):
            return cimg_code
        return f"https://res.cloudinary.com/little-papillon/image/upload/w_400/{cimg_code}"
    
    def _get_event_tag(self, event):
        """Get tag for event (online, präsenz, etc.)"""
        # Simple heuristic based on location
        if event.address_id:
            return 'präsenz'
        return 'online'
    
    def _is_free_event(self, event):
        """Check if event is free (kostenfrei)"""
        # Could check product price or specific event type
        event_type = event.event_type_id
        if event_type and event_type.name in ['AA', 'INFO']:
            return True
        return False
    
    def _get_cost_text(self, event):
        """Get cost description for event"""
        if self._is_free_event(event):
            return "### die Teilnahme ist kostenfrei\nSei bitte voll präsent."
        return "### Kosten\nDetails zur Teilnahmegebühr folgen."
    
    def _json_response(self, data, status=200):
        import json
        return request.make_response(
            json.dumps(data),
            headers=[('Content-Type', 'application/json')],
            status=status,
        )
```

---

## Part 1.2: Course-Event Linking Strategy

### Current State (SharePoint)

In SharePoint, course-event relationships are stored in `plan_veranstaltungsteilnehmer`:
- Links a **course** (contact entry starting with `_`) to individual **events** (plan_veranstaltungen)
- This determines which A1, A2, A0, A3, A4, A5 events belong to course M17E, M17B, etc.

### JSONB Field on Product (Recommended for Alpha)

Store event IDs directly on the course product:

```python
# In agenda_dasei/models/product_template.py

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    # Course event mapping (JSONB) - with metadata for flexibility
    course_event_ids = fields.Json(
        string='Course Events',
        help='JSON mapping of event shortcodes to event metadata (id, order, etc.)',
        default=dict,
    )
    # Example value (with metadata):
    # {
    #   "a0": {"event_id": 1328, "order": 1},
    #   "a1": {"event_id": 1178, "order": 2},
    #   "a2": {"event_id": 1190, "order": 3},
    #   "a3": {"event_id": 1346, "order": 4},
    #   "a4": {"event_id": 1294, "order": 5},
    #   "a5": {"event_id": 1295, "order": 6}
    # }
    # 
    # Metadata fields:
    # - event_id: (required) Odoo event.event ID
    # - order: (optional) Display order in course (1-based)
    # - Future: status, override_title, override_date, etc.
    
    # Computed: M2M relation for UI
    course_event_records = fields.Many2many(
        'event.event',
        string='Course Events (Records)',
        compute='_compute_course_event_records',
    )
    
    @api.depends('course_event_ids')
    def _compute_course_event_records(self):
        Event = self.env['event.event']
        for record in self:
            if record.course_event_ids:
                # Extract event_ids from metadata structure
                event_ids = [
                    meta.get('event_id') if isinstance(meta, dict) else meta
                    for meta in record.course_event_ids.values()
                ]
                record.course_event_records = Event.browse(event_ids)
            else:
                record.course_event_records = Event.browse()
```

### Sync from SharePoint

```python
# In agenda_dasei/models/sync_product.py

class AgendaSyncProduct(models.AbstractModel):
    _inherit = 'crearis.agenda.sync'
    
    def sync_course_event_mapping(self, company):
        """Sync course-event relationships from plan_veranstaltungsteilnehmer"""
        Product = self.env['product.template']
        Event = self.env['event.event']
        
        list_guid = company.ms_list_veranstaltungsteilnehmer
        if not list_guid:
            return {'synced': 0}
        
        sp_items = self._get_list_items(company, list_guid)
        
        # Group by course (TeilnehmerLookupId points to contact = course product)
        course_events = {}  # {course_ms_id: {shortcode: {event_id, order}}}
        
        # Define standard order for event types
        EVENT_ORDER = {'a0': 1, 'a1': 2, 'a2': 3, 'a3': 4, 'a4': 5, 'a5': 6, 'aa': 0}
        
        for item in sp_items:
            fields = item.get('fields', {})
            course_id = str(fields.get('TeilnehmerLookupId', ''))
            event_id = str(fields.get('VeranstaltungLookupId', ''))
            
            if course_id and event_id:
                if course_id not in course_events:
                    course_events[course_id] = {}
                
                event = Event.search([('ms_id', '=', event_id)], limit=1)
                if event and event.event_type_id:
                    shortcode = event.event_type_id.name.lower()
                    order = EVENT_ORDER.get(shortcode, 99)
                    course_events[course_id][shortcode] = {
                        'event_id': event.id,
                        'order': order,
                    }
        
        # Update products
        synced = 0
        for course_ms_id, events_map in course_events.items():
            product = Product.search([('ms_contact_id', '=', course_ms_id)], limit=1)
            if product:
                product.write({'course_event_ids': events_map})
                synced += 1
        
        return {'synced': synced}
```

---

## Part 1.3: Offenes Programm (Standalone Events)

### Special Contact: `_Offenes Programm` (SharePoint ID: 474)

In SharePoint, there's a special "contact" entry:
- **Name:** `_Offenes Programm`
- **ID:** 474
- **Purpose:** Groups all publicly available events for direct checkout (not part of a course)

Events registered to this contact are standalone workshop events like:
- Info-Teaser sessions
- Single-day workshops
- Open enrollment events

### MDC Template for Standalone Events

```yaml
# Template: event_standalone.mdc.template
# Filename convention: {year_digit}{month}.{name-slug}-{shortcode}_{record_id}.md
# Example: 704.info-teaser-aa_1580.md

---
navigation: false
navigation_highlight: /ausbildung-theaterpaedagogik
ctype: event
id: {{SHORTCODE}}_{{RECORD_ID}}
tag: {{TAG}}
heading: "{{DATE_SHORT}} {{TIME}}: {{HEADING}}"
description: {{DESCRIPTION}}
title: {{TITLE}}
start: {{START_DATE}}
ende: {{END_DATE}}
teaser: |
  {{TEASER}}
hero:
  height: full
  image_focus_y: cover
  image_focus_x: center
  content: banner
  content_y: bottom
  content_width: short
  cta:
    title: {{CTA_TITLE}}
image:
  alt: {{IMAGE_ALT}}
  src: {{IMAGE_SRC}}
cssclasses:
  - workshop
views:
  - details
details:
 programm:
  title: Programm
  agenda:
   style: default
  info:
   struktur: |
    {{SCHEDULE_STRUKTUR}}
   beratung: |
    {{SCHEDULE_BERATUNG}}
 konditionen:
  title: Teilnahme
  header: | 
   ### Teilnahme
  info:
   kosten: |
    {{KOSTEN_TEXT}}
   storno: |
    {{STORNO_TEXT}}
 checks:
  title: Anmelden
---
```

### Variable Mapping for Standalone Events

| Variable | Source | Example Value |
|----------|--------|---------------|
| `SHORTCODE` | `event.event_type_id.name.lower()` | `aa` |
| `RECORD_ID` | `event.ms_id` or `event.id` | `1580` |
| `TAG` | Computed from location | `online` |
| `DATE_SHORT` | `event.date_begin` formatted | `3.4` |
| `TIME` | `event.date_begin` formatted | `18:00` |
| `HEADING` | `event.name` | `Ausbildung Theaterpädagogik bei DAS Ei **Info-Teaser (online)**` |
| `DESCRIPTION` | `event.description` | `3. April 18:00-20:00 Die Weiterbildung...` |
| `TITLE` | `event.event_type_id.name` | `Info-Teaser (online)` |
| `START_DATE` | `event.date_begin` | `2027-04-03` |
| `END_DATE` | `event.date_end` | `2027-04-03` |
| `TEASER` | `event.teasertext` | `Video-Call mit: ...` |
| `CTA_TITLE` | Computed (free vs paid) | `anmelden (kostenfrei)` |
| `IMAGE_SRC` | `event.cimg` (full URL) | `https://res.cloudinary.com/...` |
| `IMAGE_ALT` | `event.event_type_id.name` | `Info-Teaser` |
| `SCHEDULE_STRUKTUR` | From `event.schedule` | `#### Programm\n- 18:00: ...` |
| `KOSTEN_TEXT` | Computed from product price | `### die Teilnahme ist kostenfrei` |
| `STORNO_TEXT` | Standard text | `### Abmeldung\n= bitte melde...` |

---

## API Endpoints Summary

| Endpoint | Method | Returns | Purpose |
|----------|--------|---------|---------|
| `/api/v1/mdc/course/{product_ref}` | GET | JSON with YAML | Single course MDC |
| `/api/v1/mdc/event/{event_id}` | GET | JSON with YAML | Single event MDC |
| `/api/v1/mdc/export?year=2026` | GET | **ZIP file** | Bulk export all MDCs |

### ZIP File Structure

```
mdc_export_2026.zip
├── courses/
│   ├── einstiege-ins-theaterspiel_m18e.md
│   ├── einstiege-ins-theaterspiel_m18b.md
│   ├── einstiege-ins-theaterspiel_n18e.md
│   └── einstiege-ins-theaterspiel_n18b.md
└── events/
    ├── 604.info-teaser-aa_1580.md
    ├── 609.workshop-xyz_1234.md
    └── ...
```

---

## Implementation Checklist (Alpha)

### Odoo Changes

- [ ] Add `course_event_ids` JSONB field to `product.template` in agenda_dasei
- [ ] Add computed `course_event_records` M2M for UI display
- [ ] Extend product form view with course events tab
- [ ] Create `sync_course_event_mapping()` method in sync engine
- [ ] Handle special contact `_Offenes Programm` (ID: 474) in sync
- [ ] Create MDC generator controller with all endpoints
- [ ] Implement ZIP export endpoint
- [ ] Add sync to cron job (after events sync)

### Testing

- [ ] Manually populate course_event_ids for M17E product
- [ ] Test single course MDC endpoint
- [ ] Test single event MDC endpoint
- [ ] Test ZIP export with year filter
- [ ] Verify event.event fields (name, teasertext, cimg) are used over event.type templates
- [ ] Test Offenes Programm event export

---

*This plan enables automated MDC generation from Odoo event data.*
