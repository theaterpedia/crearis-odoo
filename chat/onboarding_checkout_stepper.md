# Checkout Stepper Integration

**Type**: master  
**Stage**: task  
**Original Prompts**: [urls_and_code](2026-01-30-agenda_extended_urls_and_code.md), [intro](2026-01-30-agenda_extended_intro.md)

---

## Inside-Out Architecture (Key Insight)

**We control both ends of the data flow.**

```
┌─────────────────────────────────────────────────────────┐
│                    ODOO (Source of Truth)               │
│  product.template + event.event + event.type models     │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│         agenda_dasei/controllers/mdc_generator.py       │
│  /api/v1/mdc/course/<product_ref> → YAML generation     │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│               Static Site (Nuxt/Vue)                    │
│  Stepper UI reads YAML → displays product info          │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                 User fills checkout form                │
│  checkoutRecord → POST to Odoo controller               │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              Odoo Checkout Controller (NEW)             │
│  Creates: partner, registration, verification email    │
└─────────────────────────────────────────────────────────┘
```

**Principle**: Think "inside-out" — get Odoo models right first, then YAML export adapts.

---

## YAML Change Strategy

**Two-round approach for YAML/stepper changes:**

| Round | Timeframe | Scope | Coordination |
|-------|-----------|-------|--------------|
| **1** | Next 2-4 weeks | Small patches, minimal Vue changes | Internal |
| **2** | In 2-4 months | Fundamental restructuring | Cross-consult with 'claude-on-the-vuejs-project' |

**Round 1 candidates** (low-effort, high-value):
- Add `odoo_product_id` to existing YAML structure
- Add `checkout_endpoint` URL
- Pass through existing product variant info

**Round 2 considerations**:
- If YAML plays well with GraphQL data → strong argument for alignment
- Stepper might receive data from both YAML (static) and GraphQL (dynamic)
- Coordinate schema decisions with Vue project maintainer

**Principle**: The current YAML was a first-shot implementation 2 years ago when the rest of the system didn't exist. We can evolve it, but strategically.

---

## mdc_generator.py Summary

**Location**: [mdc_generator.py](agenda_dasei/controllers/mdc_generator.py) (887 lines)

**Endpoints**:
| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/mdc/course/<ref>` | Single course YAML (e.g., m17e) |
| `GET /api/v1/mdc/event/<id>` | Single event YAML (Offenes Programm) |
| `GET /api/v1/mdc/export` | Bulk ZIP export |
| `GET /api/v1/mdc/courses` | List all courses |
| `GET /api/v1/mdc/events` | List open program events |

**Current YAML structure built from**:
- `product.template` fields: default_code, course_program, course_type, course_event_ids
- `event.event` fields: name, date_begin/end, teasertext, address_id, schedule
- `event.type` fields: template_heading, template_teasertext, template_cimg (fallbacks)

**Key method**: `_build_course_mdc(product, events)` creates full course YAML with items

---

## mdc_generator.py Deep Dive

### Key Data Structures

**Course Events Mapping** (`product.course_event_ids` JSONB):
```python
# Format in product.template.course_event_ids:
{
    "a0": {"event_id": 1234, "order": 0},   # Basistag
    "a1": {"event_id": 1235, "order": 1},   # Block 1
    "a2": {"event_id": 1236, "order": 2},   # Block 2
    ...
}
```

**Shortcode Convention**:
- `a0` - a5: Course events (Am Anfang war der Kreis, etc.)
- `AA`, `INFO`, `LR`: Open program event types
- Used as keys in items: `a1_1178` = shortcode + event_id

### Location Logic

```python
_get_course_location():  # From program code
    'M' → 'München'
    'N' → 'Nürnberg'
    'ZR' → 'Region'
    'ZT' → 'Theater'

_get_location_abbrev():  # From event address
    'münchen' → 'MÜ'
    'nürnberg' → 'NÜ'
```

### Course Type Distinctions

| course_type | Title | Description |
|-------------|-------|-------------|
| `block` | "Einstiege ins Theaterspiel" | "Blockseminarverlauf" |
| `day` | "Einstiege ins Theaterspiel" | "Tageskursverlauf" |
| `profile` | "Profil {program}" | — |

### MDC Frontmatter Protocol

- 1-space indentation for nested objects
- 2-space indentation for array items (cssclasses, views)
- Unquoted dates
- Body content required after `---` (for Nuxt Content indexing)
- `items: ` has trailing space per protocol

### Existing Model Fields Used

**product.template**:
- `default_code` (m17b, m18e...)
- `course_type` (block, day, profile)
- `course_program` (M, N, ZR, ZT)
- `course_event_ids` (JSONB mapping)
- `course_year`
- `ms_contact_id` (474 = Offenes Programm)

**event.event**:
- `name`, `description`, `teasertext`
- `date_begin`, `date_end`
- `address_id` (partner with location)
- `schedule`
- `cimg` (Cloudinary image code)
- `ms_id` (Microsoft sync ID)

**event.type** (templates):
- `name` (shortcode: A1, LR, AA...)
- `template_heading`, `template_teasertext`
- `template_cimg`

---

## Current Stepper Flow (DataViewDetails.vue)

```
1. Product steps (from YAML details: programm, konditionen)
2. kontakt step (contact form)
3. checks step (AGB, Datenschutz, Rücktritt checkboxes)
    ↓
 handle_checkout() → POST to Azure Logic Apps
    ↓
 Email confirmation workflow
```

### Current CheckoutRecord Structure

```typescript
checkoutRecord: {
  basistag: string,      // '-'
  ratentyp: string,      // 'Standard'
  kursumfang: string,    // '-'
  kurs: string,          // '-'
  vorname, nachname, strasse, plz, ort, mobil, email,
  start, ende,           // from product.start/end
  actionstep: string,    // product.id or product.shortcode
  mailbody: string,      // HTML email body
  json: string           // JSON.stringify(checkoutRecord)
}
```

### Current Endpoint (to replace)

```javascript
// DataViewDetails.vue line 168
await $fetch('https://prod-53.westeurope.logic.azure.com:443/workflows/...', {
  method: 'post',
  body: checkoutRecord,
})
```

→ Replace with: `await $fetch('/api/v1/checkout', { ... })`

---

## Checkout Extension Plan

### Step 1: Add Checkout Fields to product.template

```python
# crearis/models/product_template.py
checkout_endpoint = fields.Char('Checkout Endpoint', default='/api/v1/checkout')
checkout_config = fields.Json('Checkout Configuration')  # Or structured fields:
# variant_ids = fields.One2many('product.variant', ...)
# basistag_event_ids = fields.Many2many('event.event', ...)
```

### Step 2: Extend _build_course_mdc()

```python
# In mdc_generator.py, add to course MDC:
mdc['checkout'] = {
    'odoo_product_id': product.id,
    'odoo_endpoint': product.checkout_endpoint or '/api/v1/checkout',
    'variants': self._get_checkout_variants(product),
    'basistag_options': self._get_basistag_options(product),
}
```

### Step 3: Create Checkout Controller

```python
# crearis/controllers/checkout.py
class CheckoutController(http.Controller):
    @http.route('/api/v1/checkout', type='json', auth='public', methods=['POST'])
    def process_checkout(self, **kwargs):
        # 1. Validate checkoutRecord
        # 2. Find or create partner by email
        # 3. Create event.registration
        # 4. Send verification email
        # 5. Return confirmation
```

---

## Key Files Reference

- [mdc_generator.py](agenda_dasei/controllers/mdc_generator.py) — YAML generation (we control)
- `DataViewDetails.vue` — Stepper UI component (in files/agenda_extended/)
- `einstiege-ins-theaterspiel-m18b.md` — Product YAML example (in files/agenda_extended/)
