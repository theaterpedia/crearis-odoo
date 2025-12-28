# Task 3: Beta Checkout Strategy

*Plan Document - Beta Version (Direct Odoo REST API) - Created: 2025-12-27*

---

## Overview

Direct REST API checkout to Odoo sales, bypassing SharePoint entirely. No updates to existing GraphQL setup - this is a standalone REST module.

## Goals

1. Direct Nuxt → Odoo REST API (no PowerAutomate middleware)
2. Complete checkout flow with partner, order, and registration creation
3. Payment integration readiness (Adyen, etc.)
4. Self-contained module with no GraphQL dependencies

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Nuxt.js Website                                   │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ DataViewDetails.vue (Updated)                                  │  │
│  │                                                                │  │
│  │ const { checkout } = useOdooCheckout()                        │  │
│  │                                                                │  │
│  │ await checkout({                                               │  │
│  │   product_ref: 'M18E',                                        │  │
│  │   contact: { email, vorname, nachname, ... },                 │  │
│  │   notes: '...',                                                │  │
│  │ })                                                             │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ Direct HTTPS POST
                              │ (no PowerAutomate)
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Odoo Backend                                 │
│  Module: rest_dasei (standalone)                                    │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ REST API Endpoints                                             │  │
│  │                                                                │  │
│  │ POST /api/v2/checkout/init                                    │  │
│  │   → Create draft order, return checkout_id                    │  │
│  │                                                                │  │
│  │ POST /api/v2/checkout/{id}/confirm                            │  │
│  │   → Confirm order, create registrations                       │  │
│  │                                                                │  │
│  │ GET /api/v2/checkout/{id}/status                              │  │
│  │   → Get order status                                          │  │
│  │                                                                │  │
│  │ POST /api/v2/checkout/{id}/payment                            │  │
│  │   → Initialize payment (future: Adyen)                        │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ Models                                                         │  │
│  │                                                                │  │
│  │ res.partner      ← Created/found by email                     │  │
│  │ sale.order       ← Draft → Confirmed                          │  │
│  │ event.registration ← Created on confirmation                  │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Module: rest_dasei

### Manifest

```python
# rest_dasei/__manifest__.py
{
    'name': 'DASEi REST API',
    'version': '16.0.1.0.0',
    'summary': 'REST API for DASEi course checkout',
    'description': """
Direct REST API for Nuxt website checkout.

Endpoints:
- POST /api/v2/checkout/init - Initialize checkout
- POST /api/v2/checkout/{id}/confirm - Confirm order
- GET /api/v2/checkout/{id}/status - Get status
- POST /api/v2/checkout/{id}/payment - Payment integration
    """,
    'category': 'Website/Crearis',
    'license': 'LGPL-3',
    'author': 'Theaterpedia',
    'depends': [
        'sale',
        'event',
        'agenda_dasei',  # For course_event_ids on product
    ],
    'data': [
        'data/ir_config_parameter_data.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
}
```

### API Key Configuration

```xml
<!-- rest_dasei/data/ir_config_parameter_data.xml -->
<odoo>
    <data noupdate="1">
        <record id="config_rest_api_key" model="ir.config_parameter">
            <field name="key">dasei.rest_api_key</field>
            <field name="value">GENERATE_SECURE_KEY_HERE</field>
        </record>
        <record id="config_rest_api_origins" model="ir.config_parameter">
            <field name="key">dasei.rest_api_origins</field>
            <field name="value">https://www.dasei.eu,https://dasei.eu,http://localhost:3000</field>
        </record>
    </data>
</odoo>
```

---

## REST Controller

```python
# rest_dasei/controllers/checkout.py

from odoo import http
from odoo.http import request, Response
import json

class DaseiCheckoutController(http.Controller):
    """REST API for course checkout - Beta version
    
    Direct Nuxt → Odoo without SharePoint/PowerAutomate middleware.
    """
    
    # =========================================================================
    # CORS & Auth Helpers
    # =========================================================================
    
    def _cors_headers(self):
        """Return CORS headers for cross-origin requests"""
        origins = request.env['ir.config_parameter'].sudo().get_param(
            'dasei.rest_api_origins', 'https://www.dasei.eu'
        )
        origin = request.httprequest.headers.get('Origin', '')
        
        allowed_origin = '*'  # Default
        for allowed in origins.split(','):
            if origin == allowed.strip():
                allowed_origin = origin
                break
        
        return {
            'Access-Control-Allow-Origin': allowed_origin,
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, X-API-Key',
            'Access-Control-Max-Age': '86400',
        }
    
    def _json_response(self, data, status=200):
        """Return JSON response with CORS headers"""
        return Response(
            json.dumps(data),
            status=status,
            headers={
                'Content-Type': 'application/json',
                **self._cors_headers(),
            }
        )
    
    def _validate_api_key(self):
        """Validate API key from header"""
        api_key = request.httprequest.headers.get('X-API-Key')
        expected = request.env['ir.config_parameter'].sudo().get_param('dasei.rest_api_key')
        
        if not api_key or api_key != expected:
            return False
        return True
    
    def _get_json_body(self):
        """Parse JSON body from request"""
        try:
            return json.loads(request.httprequest.data.decode('utf-8'))
        except:
            return {}
    
    # =========================================================================
    # CORS Preflight
    # =========================================================================
    
    @http.route('/api/v2/checkout/<path:path>', type='http', auth='none', 
                methods=['OPTIONS'], csrf=False)
    def checkout_options(self, path=None, **kwargs):
        """Handle CORS preflight"""
        return Response('', status=204, headers=self._cors_headers())
    
    # =========================================================================
    # Checkout Init
    # =========================================================================
    
    @http.route('/api/v2/checkout/init', type='http', auth='none', 
                methods=['POST'], csrf=False)
    def checkout_init(self, **kwargs):
        """Initialize checkout - create draft order
        
        POST Body:
        {
            "product_ref": "M18E",
            "contact": {
                "email": "test@example.com",
                "vorname": "Max",
                "nachname": "Mustermann",
                "strasse": "Musterstr. 1",
                "plz": "12345",
                "ort": "München",
                "mobil": "+49 123 456789"
            },
            "notes": "Optional notes"
        }
        
        Response:
        {
            "success": true,
            "checkout_id": "abc123",
            "order_id": 456,
            "order_name": "SO00456",
            "partner_id": 789,
            "total": 1180.00
        }
        """
        if not self._validate_api_key():
            return self._json_response({'error': 'Invalid API key'}, 401)
        
        data = self._get_json_body()
        
        try:
            # Validate required fields
            if not data.get('product_ref'):
                return self._json_response({'error': 'product_ref is required'}, 400)
            if not data.get('contact', {}).get('email'):
                return self._json_response({'error': 'contact.email is required'}, 400)
            
            # Find product
            Product = request.env['product.template'].sudo()
            product = Product.search([
                ('default_code', '=ilike', data['product_ref'])
            ], limit=1)
            
            if not product:
                return self._json_response({'error': 'Product not found'}, 404)
            
            # Get or create partner
            partner = self._get_or_create_partner(data['contact'])
            
            # Create draft sale order
            order = self._create_draft_order(partner, product, data.get('notes', ''))
            
            # Generate checkout token (for security)
            checkout_id = self._generate_checkout_token(order)
            
            return self._json_response({
                'success': True,
                'checkout_id': checkout_id,
                'order_id': order.id,
                'order_name': order.name,
                'partner_id': partner.id,
                'total': order.amount_total,
                'currency': order.currency_id.name,
            })
            
        except Exception as e:
            return self._json_response({'error': str(e)}, 500)
    
    # =========================================================================
    # Checkout Confirm
    # =========================================================================
    
    @http.route('/api/v2/checkout/<string:checkout_id>/confirm', type='http', 
                auth='none', methods=['POST'], csrf=False)
    def checkout_confirm(self, checkout_id, **kwargs):
        """Confirm checkout - finalize order and create registrations
        
        POST Body:
        {
            "accept_terms": true,
            "accept_privacy": true,
            "accept_cancellation": true
        }
        
        Response:
        {
            "success": true,
            "order_id": 456,
            "order_name": "SO00456",
            "state": "sent",
            "registrations": [
                {"event_id": 1178, "event_name": "A1 - Am Anfang war der Kreis"},
                ...
            ]
        }
        """
        if not self._validate_api_key():
            return self._json_response({'error': 'Invalid API key'}, 401)
        
        data = self._get_json_body()
        
        try:
            # Validate checkout token
            order = self._validate_checkout_token(checkout_id)
            if not order:
                return self._json_response({'error': 'Invalid checkout'}, 404)
            
            # Validate acceptance
            if not all([
                data.get('accept_terms'),
                data.get('accept_privacy'),
                data.get('accept_cancellation'),
            ]):
                return self._json_response({
                    'error': 'All terms must be accepted'
                }, 400)
            
            # Confirm order (quotation → sent)
            order.action_quotation_sent()
            
            # Create event registrations
            registrations = self._create_event_registrations(order)
            
            return self._json_response({
                'success': True,
                'order_id': order.id,
                'order_name': order.name,
                'state': order.state,
                'registrations': [
                    {
                        'event_id': reg.event_id.id,
                        'event_name': reg.event_id.name,
                    }
                    for reg in registrations
                ],
            })
            
        except Exception as e:
            return self._json_response({'error': str(e)}, 500)
    
    # =========================================================================
    # Checkout Status
    # =========================================================================
    
    @http.route('/api/v2/checkout/<string:checkout_id>/status', type='http', 
                auth='none', methods=['GET'], csrf=False)
    def checkout_status(self, checkout_id, **kwargs):
        """Get checkout/order status
        
        Response:
        {
            "order_id": 456,
            "order_name": "SO00456",
            "state": "sent",
            "total": 1180.00,
            "paid": false,
            "partner": {
                "name": "Max Mustermann",
                "email": "test@example.com"
            }
        }
        """
        if not self._validate_api_key():
            return self._json_response({'error': 'Invalid API key'}, 401)
        
        try:
            order = self._validate_checkout_token(checkout_id)
            if not order:
                return self._json_response({'error': 'Invalid checkout'}, 404)
            
            return self._json_response({
                'order_id': order.id,
                'order_name': order.name,
                'state': order.state,
                'total': order.amount_total,
                'paid': order.invoice_status == 'invoiced',
                'partner': {
                    'name': order.partner_id.name,
                    'email': order.partner_id.email,
                },
            })
            
        except Exception as e:
            return self._json_response({'error': str(e)}, 500)
    
    # =========================================================================
    # Payment (Future)
    # =========================================================================
    
    @http.route('/api/v2/checkout/<string:checkout_id>/payment', type='http', 
                auth='none', methods=['POST'], csrf=False)
    def checkout_payment(self, checkout_id, **kwargs):
        """Initialize payment - Future Adyen integration
        
        POST Body:
        {
            "payment_method": "adyen",
            "return_url": "https://www.dasei.eu/checkout/complete"
        }
        
        Response:
        {
            "payment_url": "https://checkout.adyen.com/...",
            "payment_id": "..."
        }
        """
        if not self._validate_api_key():
            return self._json_response({'error': 'Invalid API key'}, 401)
        
        # Placeholder for future implementation
        return self._json_response({
            'error': 'Payment integration not yet implemented',
            'message': 'For beta, payment is handled offline via invoice'
        }, 501)
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _get_or_create_partner(self, contact):
        """Find partner by email or create new"""
        Partner = request.env['res.partner'].sudo()
        
        email = contact.get('email', '').strip().lower()
        partner = Partner.search([('email', '=ilike', email)], limit=1)
        
        if not partner:
            partner = Partner.create({
                'name': f"{contact.get('vorname', '')} {contact.get('nachname', '')}".strip() or email,
                'firstname': contact.get('vorname', ''),
                'lastname': contact.get('nachname', ''),
                'email': email,
                'mobile': contact.get('mobil', ''),
                'street': contact.get('strasse', ''),
                'zip': contact.get('plz', ''),
                'city': contact.get('ort', ''),
            })
        else:
            # Update partner info if provided
            updates = {}
            if contact.get('mobil') and not partner.mobile:
                updates['mobile'] = contact['mobil']
            if contact.get('strasse') and not partner.street:
                updates['street'] = contact['strasse']
            if contact.get('plz') and not partner.zip:
                updates['zip'] = contact['plz']
            if contact.get('ort') and not partner.city:
                updates['city'] = contact['ort']
            if updates:
                partner.write(updates)
        
        return partner
    
    def _create_draft_order(self, partner, product, notes=''):
        """Create draft sale order"""
        SaleOrder = request.env['sale.order'].sudo()
        
        order = SaleOrder.create({
            'partner_id': partner.id,
            'note': notes,
            'order_line': [(0, 0, {
                'product_id': product.product_variant_id.id,
                'name': product.name,
                'product_uom_qty': 1,
                'price_unit': product.list_price,
            })],
        })
        
        return order
    
    def _generate_checkout_token(self, order):
        """Generate secure checkout token"""
        import hashlib
        import time
        
        # Simple token: order_id + timestamp hash
        secret = request.env['ir.config_parameter'].sudo().get_param('dasei.rest_api_key')
        data = f"{order.id}:{secret}:{int(time.time() // 3600)}"  # Valid for 1 hour
        token = hashlib.sha256(data.encode()).hexdigest()[:16]
        
        return f"{order.id}-{token}"
    
    def _validate_checkout_token(self, checkout_id):
        """Validate checkout token and return order"""
        try:
            order_id, token = checkout_id.rsplit('-', 1)
            order = request.env['sale.order'].sudo().browse(int(order_id))
            
            if not order.exists():
                return None
            
            # Verify token
            expected_token = self._generate_checkout_token(order).split('-')[1]
            if token != expected_token:
                return None
            
            return order
        except:
            return None
    
    def _create_event_registrations(self, order):
        """Create event registrations for course"""
        Registration = request.env['event.registration'].sudo()
        registrations = []
        
        for line in order.order_line:
            product = line.product_id.product_tmpl_id
            
            # Get events from course_event_ids
            if not product.course_event_ids:
                continue
            
            Event = request.env['event.event'].sudo()
            event_ids = list(product.course_event_ids.values())
            events = Event.browse(event_ids)
            
            for event in events:
                # Skip if already registered
                existing = Registration.search([
                    ('partner_id', '=', order.partner_id.id),
                    ('event_id', '=', event.id),
                ], limit=1)
                
                if not existing:
                    reg = Registration.create({
                        'event_id': event.id,
                        'partner_id': order.partner_id.id,
                        'email': order.partner_id.email,
                        'name': order.partner_id.name,
                        'sale_order_id': order.id,
                        'sale_order_line_id': line.id,
                    })
                    registrations.append(reg)
        
        return registrations
```

---

## Nuxt Composable

```typescript
// composables/useOdooCheckout.ts

interface CheckoutContact {
  email: string
  vorname: string
  nachname: string
  strasse?: string
  plz?: string
  ort?: string
  mobil?: string
}

interface CheckoutInitRequest {
  product_ref: string
  contact: CheckoutContact
  notes?: string
}

interface CheckoutConfirmRequest {
  accept_terms: boolean
  accept_privacy: boolean
  accept_cancellation: boolean
}

interface CheckoutInitResponse {
  success: boolean
  checkout_id: string
  order_id: number
  order_name: string
  partner_id: number
  total: number
  currency: string
  error?: string
}

interface CheckoutConfirmResponse {
  success: boolean
  order_id: number
  order_name: string
  state: string
  registrations: Array<{
    event_id: number
    event_name: string
  }>
  error?: string
}

export const useOdooCheckout = () => {
  const config = useRuntimeConfig()
  
  const baseUrl = config.public.odooRestApiUrl || 'https://odoo.dasei.eu'
  const apiKey = config.public.odooRestApiKey
  
  const headers = {
    'Content-Type': 'application/json',
    'X-API-Key': apiKey,
  }
  
  /**
   * Initialize checkout - creates draft order
   */
  const initCheckout = async (data: CheckoutInitRequest): Promise<CheckoutInitResponse> => {
    const response = await $fetch<CheckoutInitResponse>(`${baseUrl}/api/v2/checkout/init`, {
      method: 'POST',
      headers,
      body: data,
    })
    return response
  }
  
  /**
   * Confirm checkout - finalizes order and creates registrations
   */
  const confirmCheckout = async (
    checkoutId: string, 
    data: CheckoutConfirmRequest
  ): Promise<CheckoutConfirmResponse> => {
    const response = await $fetch<CheckoutConfirmResponse>(
      `${baseUrl}/api/v2/checkout/${checkoutId}/confirm`,
      {
        method: 'POST',
        headers,
        body: data,
      }
    )
    return response
  }
  
  /**
   * Get checkout status
   */
  const getCheckoutStatus = async (checkoutId: string) => {
    const response = await $fetch(`${baseUrl}/api/v2/checkout/${checkoutId}/status`, {
      method: 'GET',
      headers,
    })
    return response
  }
  
  /**
   * Full checkout flow - init + confirm in one call
   */
  const checkout = async (
    initData: CheckoutInitRequest,
    confirmData: CheckoutConfirmRequest
  ) => {
    // Step 1: Initialize
    const initResponse = await initCheckout(initData)
    if (!initResponse.success) {
      throw new Error(initResponse.error || 'Checkout init failed')
    }
    
    // Step 2: Confirm
    const confirmResponse = await confirmCheckout(initResponse.checkout_id, confirmData)
    if (!confirmResponse.success) {
      throw new Error(confirmResponse.error || 'Checkout confirm failed')
    }
    
    return {
      init: initResponse,
      confirm: confirmResponse,
    }
  }
  
  return {
    initCheckout,
    confirmCheckout,
    getCheckoutStatus,
    checkout,
  }
}
```

---

## Updated DataViewDetails.vue (Beta)

```vue
<script lang="ts" setup>
// ... existing imports ...

const { checkout, initCheckout, confirmCheckout } = useOdooCheckout()

// State for two-step checkout
const checkoutState = ref<{
  checkout_id?: string
  order_name?: string
  total?: number
}>({})

const handle_checkout = async () => {
  try {
    // Build contact info from form
    const contact = {
      email: contactInfo.value.email,
      vorname: contactInfo.value.vorname,
      nachname: contactInfo.value.nachname,
      strasse: contactInfo.value.strasse,
      plz: contactInfo.value.plz,
      ort: contactInfo.value.ort,
      mobil: contactInfo.value.mobil,
    }
    
    // Full checkout in one call
    const result = await checkout(
      {
        product_ref: props.product.odoo_product_ref || props.product.shortcode?.toUpperCase(),
        contact,
        notes: checksAndSummary.value.anmerkungen,
      },
      {
        accept_terms: checksAndSummary.value.agb,
        accept_privacy: checksAndSummary.value.datenschutz,
        accept_cancellation: checksAndSummary.value.ruecktritt,
      }
    )
    
    // Success - update UI
    checkoutState.value = {
      checkout_id: result.init.checkout_id,
      order_name: result.confirm.order_name,
      total: result.init.total,
    }
    
    allsteps.value[activestep.value - 1].completed = true
    
  } catch (error) {
    console.error('Checkout failed:', error)
    alert(`Es kam zu einem Fehler: ${error.message}. Bitte versuche es erneut oder kontaktiere service@dasei.eu.`)
  }
}
</script>
```

---

## Configuration

### Nuxt Runtime Config

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  runtimeConfig: {
    public: {
      // Beta: Direct Odoo REST API
      odooRestApiUrl: process.env.ODOO_REST_API_URL || 'https://odoo.dasei.eu',
      odooRestApiKey: process.env.ODOO_REST_API_KEY || '',
    }
  }
})
```

### Environment Variables

```bash
# .env.production
ODOO_REST_API_URL=https://odoo.dasei.eu
ODOO_REST_API_KEY=your-secure-api-key
```

---

## Data Flow (Beta)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Nuxt.js Website                                   │
│                                                                      │
│  1. User fills contact form                                         │
│  2. User accepts terms                                               │
│  3. useOdooCheckout().checkout() called                             │
│                                                                      │
│     ┌─────────────────────────────────────────────────────────────┐ │
│     │ POST /api/v2/checkout/init                                   │ │
│     │   { product_ref: 'M18E', contact: {...}, notes: '...' }     │ │
│     └─────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│                              ▼                                       │
│     ┌─────────────────────────────────────────────────────────────┐ │
│     │ Response: { checkout_id: '456-abc123', total: 1180 }        │ │
│     └─────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│                              ▼                                       │
│     ┌─────────────────────────────────────────────────────────────┐ │
│     │ POST /api/v2/checkout/456-abc123/confirm                    │ │
│     │   { accept_terms: true, accept_privacy: true, ... }         │ │
│     └─────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│                              ▼                                       │
│     ┌─────────────────────────────────────────────────────────────┐ │
│     │ Response: { order_name: 'SO00456', registrations: [...] }   │ │
│     └─────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  4. Show confirmation with order number                             │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ Direct HTTPS
                              │ (CORS enabled)
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Odoo Backend                                 │
│                                                                      │
│  /api/v2/checkout/init:                                             │
│    1. Find product by default_code                                  │
│    2. Find/create partner by email                                  │
│    3. Create draft sale.order                                       │
│    4. Return checkout_id (secure token)                             │
│                                                                      │
│  /api/v2/checkout/{id}/confirm:                                     │
│    1. Validate checkout token                                       │
│    2. Confirm order (draft → sent)                                  │
│    3. Create event.registration for each course event               │
│    4. (Future) Trigger confirmation email                           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Checklist (Beta)

### Odoo Module: rest_dasei

- [ ] Create module structure (`__manifest__.py`, `__init__.py`)
- [ ] Create `controllers/checkout.py` with all endpoints
- [ ] Add CORS handling for cross-origin requests
- [ ] Add API key authentication
- [ ] Create config parameters for API key and origins
- [ ] Add security CSV for model access
- [ ] Test endpoints with curl/Postman

### Nuxt Changes

- [ ] Create `composables/useOdooCheckout.ts`
- [ ] Add runtime config for API URL and key
- [ ] Update DataViewDetails.vue to use composable
- [ ] Handle error states in UI
- [ ] Test full checkout flow

### Testing

- [ ] Unit test each endpoint
- [ ] Integration test: init → confirm flow
- [ ] Test partner creation (new email)
- [ ] Test partner lookup (existing email)
- [ ] Test event registration creation
- [ ] Test CORS from localhost:3000
- [ ] Test CORS from production domain

---

## Comparison: Alpha vs Beta

| Aspect | Alpha | Beta |
|--------|-------|------|
| Middleware | PowerAutomate | None (direct) |
| Nuxt changes | 1 line (URL) | New composable + UI updates |
| Odoo module | Extend agenda_dasei | New rest_dasei module |
| SharePoint | Still writes for audit | Not used |
| Complexity | Low | Medium |
| Latency | Higher (extra hop) | Lower (direct) |
| Maintenance | Two systems | Single system |

---

*This plan provides direct Odoo REST API integration for production checkout.*
