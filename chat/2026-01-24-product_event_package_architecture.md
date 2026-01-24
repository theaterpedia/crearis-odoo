# Product-Event Package Architecture

> **Document Type:** Technical Architecture Draft  
> **Version:** 1.0  
> **Date:** 2026-01-24  
> **Status:** Draft for refinement

---

## Question

Is it possible to define a product (service-type) that contains several events? How to setup the product-events-relation?

### Proposed Approach

Using `product_template` + `product_template_attribute_line/value` + (from module crearis) `event_type`, a basic configuration of a product as a line of events (by event_type) is defined. If a product is created from the template, the line of events is not being configured. But if a customer buys the product, this means that for each of the event_type entries one event is part of the package, and a wizard could guide the process of selecting from a pool of events. The pool could be filtered by settings made on the product (start - end of the product, location=city...).

---

## Analysis

### Current Odoo Architecture

Odoo's standard `event_sale` module creates a **1:1 relationship**:
- `product.template` with `detailed_type='event'` links to tickets
- `product.product` → `event.event.ticket` → single `event.event`
- When sold, it creates one `event.registration` per quantity

This works for single events but **NOT for packages containing multiple events**.

---

## Recommended Solution: Event Type-Based Product Template

### Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│  PRODUCT TEMPLATE (Package Definition)                                            │
│  ══════════════════════════════════════                                          │
│                                                                                   │
│  product.template: "Grundkurs Theaterpädagogik M18"                              │
│      detailed_type: 'event_package' (new type!)                                  │
│      list_price: 4920.00                                                         │
│                                                                                   │
│      ┌─────────────────────────────────────────────────────────────────────────┐│
│      │ ATTRIBUTE: "Included Event Types" (create_variant='no_variant')         ││
│      │ ────────────────────────────────────────────────────────────────────    ││
│      │ product.template.attribute.line                                         ││
│      │    └── event_type_ids (custom Many2many to event.type)                  ││
│      │        ├── event.type: "A" (Modul A)                                    ││
│      │        ├── event.type: "B" (Modul B)                                    ││
│      │        ├── event.type: "C" (Modul C)                                    ││
│      │        └── event.type: "D" (Modul D)                                    ││
│      └─────────────────────────────────────────────────────────────────────────┘│
│                                                                                   │
│      Package Settings:                                                           │
│      ├── date_start: 2026-10-01                                                  │
│      ├── date_end: 2028-12-31                                                    │
│      ├── location_city: "München"                                                │
│      └── edition_code: "M18"                                                     │
│                                                                                   │
└──────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ Customer purchases
┌──────────────────────────────────────────────────────────────────────────────────┐
│  SALE ORDER LINE                                                                  │
│  ═══════════════                                                                 │
│                                                                                   │
│  sale.order.line:                                                                │
│      product_id: "Grundkurs Theaterpädagogik M18"                                │
│      ┌─────────────────────────────────────────────────────────────────────────┐│
│      │  WIZARD TRIGGERS: "Select Your Events"                                  ││
│      │  ─────────────────────────────────────────────                          ││
│      │                                                                          ││
│      │  For each event_type in package:                                        ││
│      │    Pool = event.event filtered by:                                      ││
│      │      - event_type_id matches                                            ││
│      │      - date_begin >= package.date_start                                 ││
│      │      - date_end <= package.date_end                                     ││
│      │      - location matches package criteria                                 ││
│      │                                                                          ││
│      │  Customer selects:                                                      ││
│      │    └── Modul A: M18E (München 2026)                                     ││
│      │    └── Modul B: M18B (München JAN-MAI 2027)                             ││
│      │    └── Modul C: M18C (München JUN-DEZ 2027)                             ││
│      │    └── Modul D: M18D (München JAN-JUL 2028)                             ││
│      └─────────────────────────────────────────────────────────────────────────┘│
│                                                                                   │
└──────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ After confirmation
┌──────────────────────────────────────────────────────────────────────────────────┐
│  EVENT REGISTRATIONS (Created by wizard)                                          │
│  ═══════════════════════════════════════                                         │
│                                                                                   │
│  event.registration: Partner → M18E event                                        │
│  event.registration: Partner → M18B event                                        │
│  event.registration: Partner → M18C event                                        │
│  event.registration: Partner → M18D event                                        │
│                                                                                   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Approach

### 1. New Models for `crearis` Module

```python
# models/product_event_package.py

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    detailed_type = fields.Selection(selection_add=[
        ('event_package', 'Event Package'),
    ], ondelete={'event_package': 'set service'})

    # Package configuration
    package_event_type_ids = fields.Many2many(
        'event.type',
        'product_template_event_type_rel',
        'product_tmpl_id', 'event_type_id',
        string="Included Event Types",
        help="Event types that must be selected when purchasing this package"
    )
    package_date_start = fields.Date("Package Start Date")
    package_date_end = fields.Date("Package End Date")
    package_location_id = fields.Many2one('res.city', string="Package Location")
    package_edition_code = fields.Char("Edition Code", help="e.g., M18, M19")

    def _detailed_type_mapping(self):
        type_mapping = super()._detailed_type_mapping()
        type_mapping['event_package'] = 'service'
        return type_mapping


class ProductPackageEventLine(models.Model):
    """Links a sold product package line to selected events"""
    _name = 'product.package.event.line'
    _description = 'Package Event Selection'

    sale_order_line_id = fields.Many2one('sale.order.line', required=True, ondelete='cascade')
    event_type_id = fields.Many2one('event.type', string="Event Type", required=True)
    event_id = fields.Many2one('event.event', string="Selected Event")
    registration_id = fields.Many2one('event.registration', string="Registration")
    state = fields.Selection([
        ('pending', 'Pending Selection'),
        ('selected', 'Event Selected'),
        ('registered', 'Registered'),
    ], default='pending')
```

### 2. Sale Order Line Extension

```python
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    package_event_line_ids = fields.One2many(
        'product.package.event.line',
        'sale_order_line_id',
        string="Package Events"
    )

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        for line in lines:
            if line.product_id.detailed_type == 'event_package':
                # Create pending selections for each event type
                for event_type in line.product_id.package_event_type_ids:
                    self.env['product.package.event.line'].create({
                        'sale_order_line_id': line.id,
                        'event_type_id': event_type.id,
                        'state': 'pending',
                    })
        return lines
```

### 3. Event Selection Wizard

```python
class EventPackageConfigurator(models.TransientModel):
    _name = 'event.package.configurator'
    _description = 'Event Package Configurator'

    sale_order_line_id = fields.Many2one('sale.order.line')
    line_ids = fields.One2many('event.package.configurator.line', 'wizard_id')

    def _get_available_events(self, event_type, product_template):
        """Filter events based on package settings"""
        domain = [('event_type_id', '=', event_type.id)]
        if product_template.package_date_start:
            domain.append(('date_begin', '>=', product_template.package_date_start))
        if product_template.package_date_end:
            domain.append(('date_end', '<=', product_template.package_date_end))
        # Add location filter based on your setup
        return self.env['event.event'].search(domain)

    def action_confirm(self):
        """Create registrations for selected events"""
        for line in self.line_ids:
            package_line = line.package_event_line_id
            package_line.write({
                'event_id': line.event_id.id,
                'state': 'selected',
            })
        # Trigger registration creation when SO is confirmed
        return {'type': 'ir.actions.act_window_close'}
```

---

## Why NOT Use Standard Product Attributes

Using standard `product.attribute` / `product.attribute.value` has issues:

| Approach | Problem |
|----------|---------|
| **Each event = one attribute value** | Doesn't scale (1000s of events), can't filter dynamically, bloats variant matrix |
| **One attribute = all events** | Same problem, plus loses the event_type structure |
| **Attribute per event_type** | Works better but still static - can't dynamically filter by date/location |

The proposed approach of **using event_type to DEFINE the structure** and **filtering events at purchase time** is much more flexible.

---

## Advantages of Proposed Architecture

1. **Separation of Concerns**
   - `event.type` defines WHAT kinds of events are in the package
   - `event.event` instances are filtered dynamically at purchase time
   - Product template defines the commercial wrapper (price, dates, location)

2. **Flexibility**
   - Same package template can sell different editions (M18, M19, etc.)
   - Location filter allows multi-city offerings
   - Date range filter handles different cohorts

3. **Leverages Existing Work**
   - `event.type` with `template_parent_id` and `is_template_code` already has the hierarchy
   - SharePoint sync (`crearis_agenda`) maintains event types centrally
   - Events linked to types can be filtered without attribute maintenance

4. **Two-Checkout Model**
   - Checkout 1 (Modul A only): Creates package with only A-type events required
   - Checkout 2 (B+C+D upgrade): Can add to existing package or create new package

---

## Suggested Module Structure

```
crearis_event_package/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── product_template.py      # detailed_type='event_package', package fields
│   ├── product_package_event_line.py  # Links SO line to events
│   └── sale_order.py            # Override to create registrations
├── wizard/
│   ├── __init__.py
│   └── event_package_configurator.py  # Selection wizard
├── views/
│   ├── product_template_views.xml
│   ├── sale_order_views.xml
│   └── wizard_views.xml
└── security/
    └── ir.model.access.csv
```

---

## Open Questions / Next Steps

- [ ] Define exact filtering criteria for event pool (location field mapping)
- [ ] Determine wizard trigger point (on SO line add vs. on SO confirm)
- [ ] Handle partial package purchases (e.g., only Modul A first)
- [ ] Integration with existing loyalty program for "Komplett" discount
- [ ] Website checkout UX for event selection
- [ ] Handle event changes/substitutions after purchase

---

## Related Documents

- [grundkurs_pricing_report.md](grundkurs_pricing_report.md) - Pricing model and checkout flows
- [crearis_agenda_code_implementation.md](crearis_agenda_code_implementation.md) - SharePoint sync implementation
