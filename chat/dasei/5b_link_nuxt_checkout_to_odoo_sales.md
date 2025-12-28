# 5b: Link Nuxt Checkout to Odoo Sales

*Proposal Document - Created: 2025-12-27*

---

## Overview

This document describes how to connect the Nuxt.js website checkout process to Odoo's sales/order system, using Azure Logic App (PowerAutomate) as the integration layer to create Odoo sales orders.

## Current State

### Nuxt Checkout Flow
The checkout is implemented in `DataViewDetails.vue`:

1. **Stepper Steps:**
   - Step 1-2: Product info (Programm, Konditionen) from markdown
   - Step 3: Contact form (`UiFormContactInformation`)
   - Step 4: Booking confirmation (`UiFormChecksAndSummary`)

2. **Current Submission:**
   ```typescript
   // Posts to Azure Logic App (OLD URL)
   await $fetch('https://prod-53.westeurope.logic.azure.com:443/workflows/...', {
     method: 'post',
     body: checkoutRecord,
   })
   ```

3. **CheckoutRecord Structure:**
   ```typescript
   interface CheckoutRecord {
     basistag: string
     ratentyp: string
     kursumfang: string
     kurs: string
     email: string
     vorname: string
     name: string  // nachname
     strasse: string
     plz: string
     ort: string
     mobil: string
     start: string
     ende: string
     actionstep: string  // product.id or shortcode
     anmerkungen: string
     json: string  // full record as JSON
     // ... other fields
   }
   ```

## Proposed Solution

### Step 1: Update PowerAutomate Flow URL

Replace the old Azure Logic App URL with the new PowerAutomate API URL:

**Old URL (to be replaced):**
```
https://prod-53.westeurope.logic.azure.com:443/workflows/e24e854998a44b8990cb883f006b0612/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=lQRSV83cnOJ69qBn_SWojAazlEcoZu8yntN4m_ZhFec
```

**New URL:**
```
https://default430c53e6651e45efa53c004ea96dd2.16.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/e24e854998a44b8990cb883f006b0612/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=dW-If8W3p85RTFP0mE2PD-r0sgu9opFXOmmwKuJ7xwU
```

### Step 2: Extend CheckoutRecord for Odoo Integration

Add Odoo-specific fields to the checkout payload:

```typescript
interface CheckoutRecordV2 extends CheckoutRecord {
  // Existing fields...
  
  // NEW: Odoo integration fields
  odoo_product_ref: string      // e.g., 'M17E' - maps to product.template.default_code
  odoo_create_order: boolean    // Flag to trigger Odoo order creation
  odoo_partner_email: string    // For partner lookup/creation
  odoo_order_lines: {           // Product lines for the order
    product_ref: string
    quantity: number
    price_unit?: number         // Optional override
  }[]
}
```

### Step 3: Update DataViewDetails.vue

Modify the checkout submission to include Odoo data:

```vue
<script lang="ts" setup>
// ... existing code ...

const handle_checkout = async () => {
  // Existing record population
  checkoutRecord.anmerkungen = checksAndSummary.value.anmerkungen ?? ''
  checkoutRecord.start = props.product.start?.toString() ?? ''
  checkoutRecord.ende = props.product.ende?.toString() ?? ''
  checkoutRecord.actionstep = props.product.id ?? props.product.shortcode ?? ''
  
  // NEW: Add Odoo integration fields
  const odooPayload = {
    ...checkoutRecord,
    odoo_product_ref: props.product.odoo_product_ref ?? props.product.shortcode?.toUpperCase(),
    odoo_create_order: true,
    odoo_partner_email: contactInfo.value.email,
    odoo_order_lines: [
      {
        product_ref: props.product.odoo_product_ref ?? props.product.shortcode?.toUpperCase(),
        quantity: 1,
      }
    ],
  }
  
  checkoutRecord.json = JSON.stringify(odooPayload)
  
  // Submit to NEW PowerAutomate URL
  const data = await $fetch(
    'https://default430c53e6651e45efa53c004ea96dd2.16.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/e24e854998a44b8990cb883f006b0612/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=dW-If8W3p85RTFP0mE2PD-r0sgu9opFXOmmwKuJ7xwU',
    {
      method: 'post',
      body: odooPayload,
      responseType: 'stream'
    }
  )
  // ... existing stream handling ...
}
</script>
```

### Step 4: PowerAutomate Flow Configuration

The PowerAutomate flow needs to:

1. **Receive the checkout payload**
2. **Create/lookup Odoo partner** via Odoo REST API
3. **Create Odoo sales order** with order lines
4. **Write to SharePoint** (existing functionality)

#### PowerAutomate Actions:

```
┌─────────────────────────────────────────────────────────────────┐
│ Trigger: HTTP Request (POST)                                     │
│ Input: CheckoutRecordV2 JSON                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Action 1: Parse JSON                                             │
│ Extract: odoo_product_ref, odoo_partner_email, odoo_order_lines │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Action 2: HTTP - Odoo Partner Lookup/Create                      │
│ Endpoint: https://odoo.dasei.eu/api/v1/partners                  │
│ Method: POST                                                     │
│ Body: {                                                          │
│   "email": "@{body('Parse_JSON')?['odoo_partner_email']}",      │
│   "name": "@{body('Parse_JSON')?['name']}",                     │
│   "firstname": "@{body('Parse_JSON')?['vorname']}",             │
│   ...                                                            │
│ }                                                                │
│ Response: { "partner_id": 12345 }                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Action 3: HTTP - Odoo Get Product by Ref                         │
│ Endpoint: https://odoo.dasei.eu/api/v1/products                  │
│ Method: GET                                                      │
│ Query: ?default_code=@{body('Parse_JSON')?['odoo_product_ref']} │
│ Response: { "product_id": 789, "list_price": 1180.00 }          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Action 4: HTTP - Odoo Create Sales Order                         │
│ Endpoint: https://odoo.dasei.eu/api/v1/sales/orders              │
│ Method: POST                                                     │
│ Body: {                                                          │
│   "partner_id": @{body('Partner_Lookup')?['partner_id']},       │
│   "order_line": [[0, 0, {                                       │
│     "product_id": @{body('Product_Lookup')?['product_id']},     │
│     "product_uom_qty": 1,                                        │
│     "price_unit": @{body('Product_Lookup')?['list_price']}      │
│   }]]                                                            │
│ }                                                                │
│ Response: { "order_id": 456, "name": "SO00456" }                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Action 5: SharePoint - Create Item (Existing)                    │
│ Site: https://dasei.sharepoint.com/sites/api                    │
│ List: registrations / plan_anmeldungen                           │
│ + Add odoo_order_id to SharePoint item                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Response: HTTP 200                                               │
│ Body: { "success": true, "odoo_order": "SO00456" }              │
└─────────────────────────────────────────────────────────────────┘
```

### Step 5: Odoo REST API Endpoints

Create/extend REST API in `graphql_theaterpedia` or a new `rest_dasei` module:

```python
# rest_dasei/controllers/main.py
from odoo import http
from odoo.http import request

class DaseiAPI(http.Controller):

    @http.route('/api/v1/partners', type='json', auth='api_key', methods=['POST'])
    def create_or_get_partner(self, **kwargs):
        """Find partner by email or create new one"""
        Partner = request.env['res.partner'].sudo()
        
        email = kwargs.get('email')
        partner = Partner.search([('email', '=', email)], limit=1)
        
        if not partner:
            partner = Partner.create({
                'name': f"{kwargs.get('vorname', '')} {kwargs.get('name', '')}".strip(),
                'firstname': kwargs.get('vorname'),
                'lastname': kwargs.get('name'),
                'email': email,
                'phone': kwargs.get('mobil'),
                'street': kwargs.get('strasse'),
                'zip': kwargs.get('plz'),
                'city': kwargs.get('ort'),
            })
        
        return {'partner_id': partner.id}

    @http.route('/api/v1/products', type='json', auth='api_key', methods=['GET'])
    def get_product(self, default_code=None, **kwargs):
        """Get product by default_code"""
        Product = request.env['product.template'].sudo()
        product = Product.search([('default_code', '=', default_code)], limit=1)
        
        if not product:
            return {'error': 'Product not found'}
        
        return {
            'product_id': product.id,
            'product_product_id': product.product_variant_id.id,
            'list_price': product.list_price,
            'name': product.name,
        }

    @http.route('/api/v1/sales/orders', type='json', auth='api_key', methods=['POST'])
    def create_sale_order(self, **kwargs):
        """Create a sales order"""
        SaleOrder = request.env['sale.order'].sudo()
        
        order = SaleOrder.create({
            'partner_id': kwargs.get('partner_id'),
            'order_line': kwargs.get('order_line', []),
        })
        
        return {
            'order_id': order.id,
            'name': order.name,
        }
```

### Step 6: Odoo Event Registration (Optional Enhancement)

For course products, also create event registrations:

```python
@http.route('/api/v1/event/register', type='json', auth='api_key', methods=['POST'])
def register_to_events(self, partner_id, product_ref, **kwargs):
    """Register partner to all events linked to a course product"""
    Product = request.env['product.template'].sudo()
    Event = request.env['event.event'].sudo()
    Registration = request.env['event.registration'].sudo()
    
    product = Product.search([('default_code', '=', product_ref)], limit=1)
    if not product:
        return {'error': 'Product not found'}
    
    # Find events linked to this course
    # (depends on how events are linked - via event_type or direct)
    events = Event.search([
        ('event_type_id.name', 'like', product_ref[:2]),  # M17, N17, etc.
        ('date_begin', '>=', product.course_start_date),
    ])
    
    registrations = []
    for event in events:
        reg = Registration.create({
            'event_id': event.id,
            'partner_id': partner_id,
        })
        registrations.append(reg.id)
    
    return {'registration_ids': registrations}
```

## API Configuration

### SharePoint API Site
```
Site: https://dasei.sharepoint.com/sites/api
```

> **Note:** This is different from the sync site (`https://dasei.sharepoint.com/sites/dasei-website`). Once confirmed working, existing PowerAutomate flows will be refactored to use the new api-site.

### PowerAutomate Flow URL (New)
```
https://default430c53e6651e45efa53c004ea96dd2.16.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/e24e854998a44b8990cb883f006b0612/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=dW-If8W3p85RTFP0mE2PD-r0sgu9opFXOmmwKuJ7xwU
```

### Odoo API Base URL
```
https://odoo.dasei.eu/api/v1
```

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Nuxt.js Website                                   │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ DataViewDetails.vue                                            │  │
│  │ Checkout Stepper:                                              │  │
│  │  [Programm] → [Konditionen] → [Kontakt] → [Buchung]           │  │
│  │                                              │                 │  │
│  │                                              ▼                 │  │
│  │                                    handle_checkout()           │  │
│  │                                              │                 │  │
│  └──────────────────────────────────────────────┼────────────────┘  │
└─────────────────────────────────────────────────┼────────────────────┘
                                                  │ POST CheckoutRecordV2
                                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PowerAutomate Flow                                │
│  URL: https://default430c53e6651e45efa53c004ea96dd2...              │
│  ┌────────────────┐                                                 │
│  │ Parse Payload  │                                                 │
│  └───────┬────────┘                                                 │
│          │                                                          │
│    ┌─────┴─────┐                                                    │
│    ▼           ▼                                                    │
│  ┌───────────────────┐    ┌────────────────────────────────────┐   │
│  │ Odoo REST API     │    │ SharePoint                          │   │
│  │ - Create Partner  │    │ Site: .../sites/api                 │   │
│  │ - Get Product     │    │ - Write to plan_anmeldungen         │   │
│  │ - Create SO       │    │ - Include odoo_order_id             │   │
│  └───────────────────┘    └────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Odoo Backend                                 │
│  ┌─────────────────────┐    ┌──────────────────────────────────┐   │
│  │ res.partner         │    │ sale.order                        │   │
│  │ - Created/found     │◄──►│ - partner_id                      │   │
│  │   by email          │    │ - order_line → product.template   │   │
│  └─────────────────────┘    │ - State: draft → sent             │   │
│                              └──────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ event.registration (optional)                                 │  │
│  │ - Auto-register to course events                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Order Confirmation Flow

After successful order creation:

1. **PowerAutomate** returns `{ success: true, odoo_order: "SO00456" }`
2. **Nuxt** displays confirmation with order number
3. **Odoo** (optional): Sends confirmation email via mail template
4. **SharePoint** has record with `odoo_order_id` for tracking

## Implementation Checklist

- [ ] Update PowerAutomate flow URL in DataViewDetails.vue
- [ ] Add `odoo_product_ref` and `odoo_order_lines` to checkout payload
- [ ] Create/extend Odoo REST API module (`rest_dasei`)
- [ ] Configure PowerAutomate flow with Odoo HTTP actions
- [ ] Add API key authentication to Odoo endpoints
- [ ] Test end-to-end checkout → Odoo order creation
- [ ] Configure Odoo mail templates for order confirmation
- [ ] (Optional) Implement event registration endpoint

---

*This document instructs code automation on the Nuxt project.*
