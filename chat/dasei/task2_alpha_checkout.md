# Task 2: Alpha Checkout Strategy

*Plan Document - Alpha Version (4 weeks scope) - Created: 2025-12-27*

---

## Overview

Minimal-change approach to integrate Odoo checkout via existing SharePoint infrastructure. **No changes to Nuxt components** - only update the PowerAutomate flow to route data to Odoo.

## Goals

1. Update only the API route URL in Nuxt (single line change)
2. Reuse existing SharePoint fields to pass Odoo-specific data
3. PowerAutomate flow creates Odoo records from existing payload
4. Zero new Nuxt components or composables

---

## Current Nuxt Checkout (Unchanged)

### DataViewDetails.vue - Existing Code

```typescript
// ONLY CHANGE: Update this URL
const data = await $fetch(
  'https://default430c53e6651e45efa53c004ea96dd2.16.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/e24e854998a44b8990cb883f006b0612/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=dW-If8W3p85RTFP0mE2PD-r0sgu9opFXOmmwKuJ7xwU',
  {
    method: 'post',
    body: checkoutRecord,  // Existing payload - NO CHANGES
    responseType: 'stream'
  }
)
```

### Existing CheckoutRecord Fields (Reuse These)

```typescript
interface CheckoutRecord {
  // Contact info
  email: string
  vorname: string
  name: string           // nachname
  strasse: string
  plz: string
  ort: string
  mobil: string
  
  // Course info
  kurs: string           // ← REUSE: Pass product shortcode (m17e, m18e)
  basistag: string
  ratentyp: string
  kursumfang: string
  
  // Dates
  start: string
  ende: string
  
  // Identifiers
  actionstep: string     // ← REUSE: Pass product.id or shortcode for lookup
  
  // Notes
  anmerkungen: string
  bemerkungen: string
  
  // Full JSON
  json: string           // ← Contains full record - can be parsed by Flow
}
```

---

## Field Mapping Strategy

### Map Existing Fields to Odoo Concepts

| Existing Field | Current Usage | Alpha Reuse for Odoo |
|---------------|---------------|---------------------|
| `kurs` | Course name like "M17E" | **Product lookup key** → `product.template.default_code` |
| `actionstep` | Product shortcode | **Odoo writeback** → receives `odoo_order_id` or `odoo_event_id` |
| `email` | Contact email | **Partner lookup/create key** |
| `vorname` + `name` | Contact name | **Partner name** |
| `json` | Full record JSON | **Full payload for Odoo parsing** |

### No New Fields Needed

The existing `kurs` field already contains values like:
- `"m17e"` → Maps to `default_code='M17E'`
- `"M17E"` → Direct match

The existing `actionstep` field contains the shortcode as backup.

---

## PowerAutomate Flow Update

### Flow: Checkout Handler (Updated)

**Site:** `https://dasei.sharepoint.com/sites/api`

```
┌─────────────────────────────────────────────────────────────────┐
│ Trigger: HTTP Request (POST) - EXISTING                          │
│ URL: https://default430c53e6651e45efa53c004ea96dd2...            │
│ Input: CheckoutRecord JSON (unchanged)                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Action 1: Parse JSON - EXISTING                                  │
│ Extract all fields from body                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Action 2: SharePoint - Create Item - EXISTING                    │
│ List: registrations / plan_anmeldungen                           │
│ (Keep existing SharePoint write for backup/audit)                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ **NEW** Action 3: HTTP - Odoo Create Checkout                    │
│ Endpoint: https://odoo.dasei.eu/api/v1/checkout                  │
│ Method: POST                                                     │
│ Headers:                                                         │
│   Authorization: Bearer {{ODOO_API_KEY}}                        │
│   Content-Type: application/json                                 │
│ Body: @{triggerBody()}  (forward entire payload)                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ **NEW** Action 4: Update SharePoint Item - actionstep field      │
│ Field: actionstep                                                │
│ Value: @{body('Odoo_Checkout').odoo_order_id}                   │
│        OR @{body('Odoo_Checkout').odoo_event_id} (if Offenes P.)│
│ NOTE: This OVERWRITES the existing actionstep value             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Response: HTTP 200 - EXISTING                                    │
│ Body: { "success": true }                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Odoo REST Endpoint (Alpha)

### Single Endpoint: `/api/v1/checkout`

```python
# agenda_dasei/controllers/checkout.py

from odoo import http
from odoo.http import request
import json

class CheckoutController(http.Controller):

    @http.route('/api/v1/checkout', type='json', auth='api_key', methods=['POST'])
    def process_checkout(self, **kwargs):
        """Process checkout from Nuxt via PowerAutomate
        
        Expects existing CheckoutRecord fields:
        - kurs: Product code (m17e, M17E)
        - email: Contact email
        - vorname, name: Contact name
        - strasse, plz, ort: Address
        - mobil: Phone
        - start, ende: Course dates
        - anmerkungen: Notes
        """
        try:
            # 1. Find or create partner
            partner = self._get_or_create_partner(kwargs)
            
            # 2. Find product by kurs code
            product = self._find_product(kwargs.get('kurs') or kwargs.get('actionstep'))
            if not product:
                return {'success': False, 'error': 'Product not found'}
            
            # 3. Create sale order (skip for Offenes Programm single events)
            order = None
            event_only = self._is_offenes_programm(product)
            
            if not event_only:
                order = self._create_sale_order(partner, product, kwargs)
            
            # 4. Create event registrations (if product has linked events)
            registrations = self._create_registrations(partner, product)
            
            # Build response - different for course vs single event
            response = {
                'success': True,
                'odoo_partner_id': partner.id,
                'registration_count': len(registrations),
            }
            
            if order:
                # Course checkout → return order ID for actionstep
                response['odoo_order_id'] = order.id
                response['odoo_order_name'] = order.name
                response['actionstep_value'] = f"order:{order.id}"  # For SharePoint
            elif registrations:
                # Offenes Programm → return event ID for actionstep
                response['odoo_event_id'] = registrations[0].event_id.id
                response['actionstep_value'] = f"event:{registrations[0].event_id.id}"  # For SharePoint
            
            return response
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_or_create_partner(self, data):
        """Find partner by email or create new"""
        Partner = request.env['res.partner'].sudo()
        
        email = data.get('email', '').strip().lower()
        if not email:
            raise ValueError('Email is required')
        
        partner = Partner.search([('email', '=ilike', email)], limit=1)
        
        if not partner:
            partner = Partner.create({
                'name': f"{data.get('vorname', '')} {data.get('name', '')}".strip() or email,
                'firstname': data.get('vorname', ''),
                'lastname': data.get('name', ''),
                'email': email,
                'mobile': data.get('mobil', ''),
                'street': data.get('strasse', ''),
                'zip': data.get('plz', ''),
                'city': data.get('ort', ''),
            })
        
        return partner
    
    def _find_product(self, kurs_code):
        """Find product by kurs code (case-insensitive)"""
        if not kurs_code:
            return None
        
        Product = request.env['product.template'].sudo()
        
        # Try exact match first
        product = Product.search([('default_code', '=', kurs_code.upper())], limit=1)
        
        if not product:
            # Try case-insensitive
            product = Product.search([('default_code', '=ilike', kurs_code)], limit=1)
        
        return product
    
    def _create_sale_order(self, partner, product, data):
        """Create sale order for course"""
        SaleOrder = request.env['sale.order'].sudo()
        
        # Get product variant
        product_variant = product.product_variant_id
        
        order = SaleOrder.create({
            'partner_id': partner.id,
            'note': data.get('anmerkungen', ''),
            'order_line': [(0, 0, {
                'product_id': product_variant.id,
                'name': product.name,
                'product_uom_qty': 1,
                'price_unit': product.list_price,
            })],
        })
        
        return order
    
    def _create_registrations(self, partner, product):
        """Create event registrations for course events"""
        Registration = request.env['event.registration'].sudo()
        registrations = []
        
        # Get events from course_event_ids JSONB field
        if not product.course_event_ids:
            return registrations
        
        Event = request.env['event.event'].sudo()
        event_ids = list(product.course_event_ids.values())
        events = Event.browse(event_ids)
        
        for event in events:
            # Check if already registered
            existing = Registration.search([
                ('partner_id', '=', partner.id),
                ('event_id', '=', event.id),
            ], limit=1)
            
            if not existing:
                reg = Registration.create({
                    'event_id': event.id,
                    'partner_id': partner.id,
                    'email': partner.email,
                    'name': partner.name,
                })
                registrations.append(reg)
        
        return registrations
    
    def _is_offenes_programm(self, product):
        """Check if product is from 'Offenes Programm' (single event, no order)
        
        Offenes Programm events (SharePoint contact ID: 474) are standalone
        events without a course product. They don't create a sale order,
        only an event registration.
        """
        # Check by ms_contact_id (SharePoint contact ID for _Offenes Programm)
        if product.ms_contact_id == '474':
            return True
        # Or check by product type/category if configured
        return False
```

---

## Security: API Key Authentication

### Setup in Odoo

```python
# Use existing auth='api_key' from OCA rest-framework
# Or simple header-based auth:

@http.route('/api/v1/checkout', type='json', auth='none', methods=['POST'], csrf=False)
def process_checkout(self, **kwargs):
    # Validate API key
    api_key = request.httprequest.headers.get('X-API-Key')
    expected_key = request.env['ir.config_parameter'].sudo().get_param('dasei.checkout_api_key')
    
    if not api_key or api_key != expected_key:
        return {'success': False, 'error': 'Invalid API key'}
    
    # ... rest of method
```

### Configure in PowerAutomate

```
HTTP Action Headers:
  X-API-Key: {{ODOO_CHECKOUT_API_KEY}}
  Content-Type: application/json
```

---

## Data Flow Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Nuxt.js Website                                   │
│  DataViewDetails.vue                                                │
│  └─► POST checkoutRecord (unchanged payload)                        │
│      URL: PowerAutomate (new URL, same format)                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PowerAutomate Flow                                │
│  Site: https://dasei.sharepoint.com/sites/api                       │
│  ┌────────────────────────────────────────────────────────────────┐│
│  │ 1. Receive POST                                                 ││
│  │ 2. Write to SharePoint (existing - for audit)                  ││
│  │ 3. **NEW** POST to Odoo /api/v1/checkout                       ││
│  │ 4. **NEW** Update SharePoint actionstep with Odoo ID           ││
│  │    → For course: odoo_order_id (sale.order.id)                ││
│  │    → For Offenes Programm: odoo_event_id (event.event.id)     ││
│  │ 5. Return success                                               ││
│  └────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Odoo Backend                                 │
│  /api/v1/checkout                                                   │
│  ┌────────────────────────────────────────────────────────────────┐│
│  │ 1. Find/create res.partner by email                            ││
│  │ 2. Find product.template by kurs code                          ││
│  │ 3. Create sale.order with order line                           ││
│  │ 4. Create event.registration for each course event             ││
│  │ 5. Return { odoo_order_id, odoo_order_name }                   ││
│  └────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

---

## Nuxt Changes (Minimal)

### Single Line Change in DataViewDetails.vue

```diff
- const data = await $fetch('https://prod-53.westeurope.logic.azure.com:443/workflows/e24e854998a44b8990cb883f006b0612/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=lQRSV83cnOJ69qBn_SWojAazlEcoZu8yntN4m_ZhFec', {
+ const data = await $fetch('https://default430c53e6651e45efa53c004ea96dd2.16.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/e24e854998a44b8990cb883f006b0612/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=dW-If8W3p85RTFP0mE2PD-r0sgu9opFXOmmwKuJ7xwU', {
      method: 'post',
      body: checkoutRecord,
      responseType: 'stream'
  })
```

**Alternatively**, move URL to runtime config:

```typescript
// nuxt.config.ts
runtimeConfig: {
  public: {
    checkoutApiUrl: process.env.CHECKOUT_API_URL || 'https://default430c53e6651e45efa53c004ea96dd2...'
  }
}

// DataViewDetails.vue
const config = useRuntimeConfig()
const data = await $fetch(config.public.checkoutApiUrl, { ... })
```

---

## Implementation Checklist (Alpha - 4 Weeks)

### Week 1: Odoo Endpoint

- [ ] Create `controllers/checkout.py` in agenda_dasei
- [ ] Implement `_get_or_create_partner()` method
- [ ] Implement `_find_product()` method
- [ ] Implement `_create_sale_order()` method
- [ ] Add API key config parameter

### Week 2: Event Registrations

- [ ] Ensure `course_event_ids` JSONB field exists on products
- [ ] Implement `_create_registrations()` method
- [ ] Test with manually configured product

### Week 3: PowerAutomate Flow

- [ ] Add HTTP action to call Odoo endpoint
- [ ] Configure API key in Flow
- [ ] Add action to update SharePoint with odoo_order_id
- [ ] Test flow end-to-end

### Week 4: Integration & Testing

- [ ] Update Nuxt URL (single line change)
- [ ] Test full checkout flow
- [ ] Verify Odoo records created (partner, order, registrations)
- [ ] Verify SharePoint record has odoo_order_id

---

## Rollback Plan

If issues occur:
1. Revert Nuxt URL to old Azure Logic App endpoint
2. PowerAutomate still writes to SharePoint (existing behavior preserved)
3. Odoo endpoint can be disabled without affecting checkout

---

*This plan enables Odoo integration with minimal Nuxt changes.*
