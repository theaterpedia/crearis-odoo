# Crearis Event Package - Developer Documentation

> **Module:** `crearis_event_package`  
> **Version:** 16.0.1.0.0  
> **Dependencies:** `crearis`, `event_sale`, `sale`  
> **Last Updated:** 2026-01-25

---

## Overview

The `crearis_event_package` module enables selling bundled events as a single product. Customers purchase a package (e.g., "Grundkurs Theaterpädagogik M18") and then select specific events from a pool defined by event types.

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Event Package** | A product (`detailed_type='event_package'`) containing multiple event type slots |
| **Package Event Line** | Links a sale order line to selected events, one per event type |
| **Package Only** | Flag on events preventing individual ticket sales |
| **Event Pool** | Available events filtered by type, date range, and package settings |

---

## Module Structure

```
crearis_event_package/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── res_company.py              # Company settings
│   ├── res_config_settings.py      # Config UI integration
│   ├── product_template.py         # Event package product type
│   ├── product_package_event_line.py  # Package-event linking
│   ├── event_event.py              # Event extensions
│   └── sale_order.py               # Sale order extensions
├── wizard/
│   ├── __init__.py
│   ├── event_package_configurator.py
│   └── event_package_configurator_views.xml
├── views/
│   ├── res_company_views.xml
│   ├── res_config_settings_views.xml
│   ├── product_template_views.xml
│   ├── event_event_views.xml
│   └── sale_order_views.xml
└── security/
    └── ir.model.access.csv
```

---

## Data Models

### 1. Product Template Extension

**File:** `models/product_template.py`

```python
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    detailed_type = fields.Selection(selection_add=[
        ('event_package', 'Event Package'),
    ])
    
    # Package configuration
    package_event_type_ids = fields.Many2many('event.type', ...)
    package_date_start = fields.Date(...)
    package_date_end = fields.Date(...)
    package_edition_code = fields.Char(...)
```

| Field | Type | Description |
|-------|------|-------------|
| `detailed_type` | Selection | Extended with `'event_package'` option |
| `package_event_type_ids` | Many2many | Event types included in the package |
| `package_date_start` | Date | Start of event selection window |
| `package_date_end` | Date | End of event selection window |
| `package_edition_code` | Char | Edition identifier (e.g., "M18") |

---

### 2. Product Package Event Line

**File:** `models/product_package_event_line.py`

**Model:** `product.package.event.line`

This is the **core traceability model** linking package purchases to actual events.

```python
class ProductPackageEventLine(models.Model):
    _name = 'product.package.event.line'
    
    sale_order_line_id = fields.Many2one('sale.order.line', required=True)
    sale_order_id = fields.Many2one('sale.order', related=...)
    partner_id = fields.Many2one('res.partner', related=...)
    product_id = fields.Many2one('product.product', related=...)
    
    event_type_id = fields.Many2one('event.type', required=True)
    event_id = fields.Many2one('event.event')
    registration_id = fields.Many2one('event.registration')
    
    state = fields.Selection([
        ('pending', 'Pending Selection'),
        ('selected', 'Event Selected'),
        ('registered', 'Registered'),
        ('cancelled', 'Cancelled'),
    ])
```

**State Flow:**
```
pending → selected → registered
    ↓         ↓
cancelled  cancelled
```

**Key Methods:**

| Method | Description |
|--------|-------------|
| `action_create_registration()` | Creates `event.registration` for selected events |
| `action_cancel()` | Cancels the line and associated registration |

---

### 3. Event Event Extension

**File:** `models/event_event.py`

```python
class EventEvent(models.Model):
    _inherit = 'event.event'

    package_only = fields.Boolean(default=False)
    use_event_packages = fields.Boolean(compute='_compute_use_event_packages')
    is_in_package = fields.Boolean(compute='_compute_is_in_package')
    package_line_ids = fields.One2many('product.package.event.line', 'event_id')
```

| Field | Type | Description |
|-------|------|-------------|
| `package_only` | Boolean | If True, event cannot be sold individually |
| `use_event_packages` | Boolean | Computed from website/company settings |
| `is_in_package` | Boolean | True if event has any package line references |
| `package_line_ids` | One2many | All package lines referencing this event |

**Auto-set `package_only` on create:**

When an event is created and:
1. `use_event_packages` is enabled for the website/company
2. The event's `event_type_id` is referenced in any `product.template` with `detailed_type='event_package'`

Then `package_only` defaults to `True`.

---

### 4. Sale Order Extension

**File:** `models/sale_order.py`

```python
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    package_event_line_ids = fields.One2many('product.package.event.line', 'sale_order_id')
    package_event_count = fields.Integer(compute=...)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    package_event_line_ids = fields.One2many('product.package.event.line', 'sale_order_line_id')
    is_event_package = fields.Boolean(compute=...)
```

**Auto-creation of Package Event Lines:**

When a `sale.order.line` is created with a product where `detailed_type='event_package'`:
- For each `event_type_id` in `product.package_event_type_ids`
- A `product.package.event.line` is created with `state='pending'`

---

### 5. Website/Company Settings (Feature Flag)

**File:** `models/res_company.py`

This module **owns** the `use_event_packages` feature flag. It extends both `website` and `res.company`:

```python
class Website(models.Model):
    _inherit = 'website'
    
    use_event_packages = fields.Boolean(default=False)
    
    @api.constrains('use_event_packages', 'use_template_codes')
    def _check_event_packages_requires_template_codes(self):
        # Enforces dependency on use_template_codes

class Company(models.Model):
    _inherit = 'res.company'
    
    use_event_packages = fields.Boolean(default=False)
    
    @api.constrains('use_event_packages', 'use_template_codes')
    def _check_event_packages_requires_template_codes(self):
        # Enforces dependency on use_template_codes
```

**Architectural Note:** The `use_event_packages` field is defined here (not in `crearis` base module) so the feature flag lives in the same module as the functionality. The `crearis` module's `use_products` computed field detects this dynamically via `getattr()`.

**Constraint:** `use_event_packages` can only be True if `use_template_codes` is True (defined in `crearis` base module).

---

## Wizard

### Event Package Configurator

**File:** `wizard/event_package_configurator.py`

**Models:**
- `event.package.configurator` - Main wizard
- `event.package.configurator.line` - Line items for each event type

**Purpose:** Allows selecting specific events for each slot in a package.

**Key Methods:**

| Method | Description |
|--------|-------------|
| `_get_available_events_domain()` | Builds domain to filter events by type and date range |
| `action_confirm()` | Saves selections to package lines |
| `action_confirm_and_register()` | Saves and creates registrations |

---

## Views

### Product Template Form

Adds "Event Package" page in notebook with:
- Package edition code
- Date range (start/end)
- Event types selector (many2many tags + tree view)

### Event Form

- Shows/hides `package_only` toggle based on `use_event_packages`
- Displays alerts for package-only events
- Hides ticket form when `package_only=True`
- Disables `package_only` toggle if tickets exist
- Stat button for package lines

### Sale Order Form

- Stat button for package event count
- Configure Package button on sale order lines
- Package event lines tree in line form

---

## Security

### Access Rights

| Model | User | Salesman | Manager |
|-------|------|----------|---------|
| `product.package.event.line` | Read | CRUD | CRUD + Delete |
| `event.package.configurator` | - | CRUD | CRUD |
| `event.package.configurator.line` | - | CRUD | CRUD |

---

## Usage Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. SETUP                                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  ☐ Enable "Template Codes" in website settings                              │
│  ☐ Enable "Event Packages" in website settings                              │
│  ☐ Create event types (e.g., A, B, C, D modules)                            │
│  ☐ Create events with those event types                                     │
│  ☐ Create product with detailed_type='event_package'                        │
│  ☐ Configure package_event_type_ids, date range                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. SALE                                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  ☐ Add event package product to sale order                                  │
│  → Package event lines auto-created (state='pending')                       │
│  ☐ Click "Configure Events" on sale order line                              │
│  → Wizard opens with event type slots                                       │
│  ☐ Select events for each slot from filtered pool                           │
│  ☐ Confirm selections (state='selected')                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. REGISTRATION                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  ☐ Confirm sale order                                                       │
│  ☐ Create registrations (manually or via wizard)                            │
│  → Package lines link to event.registration (state='registered')            │
│  ☐ Customer receives registration confirmations                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Queries & Reporting

### Get all package events for a customer

```python
package_events = env['product.package.event.line'].search([
    ('partner_id', '=', customer_id),
    ('state', '!=', 'cancelled'),
])
```

### Get standalone registrations (not from packages)

```python
# All registrations
all_regs = env['event.registration'].search([('partner_id', '=', customer_id)])

# Package registration IDs
package_reg_ids = env['product.package.event.line'].search([
    ('partner_id', '=', customer_id),
    ('registration_id', '!=', False),
]).mapped('registration_id').ids

# Standalone = All - Package
standalone = all_regs.filtered(lambda r: r.id not in package_reg_ids)
```

### Check if event type is in any package

```python
is_in_package = env['product.template'].search_count([
    ('detailed_type', '=', 'event_package'),
    ('package_event_type_ids', 'in', [event_type_id]),
]) > 0
```

---

## Integration Notes

### Independence from SharePoint modules

This module does **NOT** depend on:
- `crearis_agenda`
- `agenda_dasei`

It provides generic packaging functionality that can be extended by other modules for specific sync or business logic.

### Extending for specific use cases

To add SharePoint sync or DASEi-specific logic, create a separate module that depends on both `crearis_event_package` and the sync module.

---

## Related Documents

- [2026-01-24-product_event_package_architecture.md](2026-01-24-product_event_package_architecture.md) - Architecture design
- [grundkurs_pricing_report.md](grundkurs_pricing_report.md) - Business requirements
