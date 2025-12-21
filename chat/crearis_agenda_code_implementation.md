# Crearis Agenda: Grundkurs Code Implementation

> **Purpose:** Minimal code changes to support Grundkurs two-checkout model  
> **Module:** `crearis_agenda`  
> **Target:** Odoo 16.0  
> **Date:** December 21, 2025

---

## 1. Implementation Philosophy

### Guiding Principles

1. **MINIMAL model changes** - Use existing Odoo/OCA fields where possible
2. **MINIMAL view changes** - Extend rather than replace
3. **Config over code** - Use data records (XML) for business rules
4. **SharePoint as source** - Session codes come from `plan_veranstaltungscodes`

### What We're NOT Building

- ❌ Custom checkout wizard
- ❌ New payment processing
- ❌ Custom session management (use OCA `event_session`)
- ❌ Custom loyalty system (use `sale_loyalty`)

---

## 2. Model Extensions

### 2.1 Event Session Extension

**File:** `models/event_session.py`

```python
# -*- coding: utf-8 -*-
from odoo import fields, models

class EventSession(models.Model):
    _inherit = 'event.session'
    
    # SharePoint sync field
    sharepoint_code = fields.Char(
        string="SharePoint Session Code",
        help="Code from plan_veranstaltungscodes (e.g., A0, A1, B2)",
        index=True,
    )
    
    # Entry session flag for cancellation window
    is_entry_session = fields.Boolean(
        string="Is Entry Session",
        help="If True, attending this session starts the 10-day cancellation window",
        default=False,
    )
```

**Why:** 
- `sharepoint_code`: Links to SharePoint `plan_veranstaltungscodes` table
- `is_entry_session`: A0, A1, A4 sessions trigger the 10-day rule

---

### 2.2 Event Registration Extension

**File:** `models/event_registration.py`

```python
# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import timedelta

class EventRegistration(models.Model):
    _inherit = 'event.registration'
    
    # Cancellation tracking
    first_entry_session_date = fields.Datetime(
        string="First Entry Session Date",
        help="Date when attendee first attended an entry session (A0/A1/A4)",
        readonly=True,
    )
    cancellation_deadline = fields.Datetime(
        string="Cancellation Deadline",
        compute='_compute_cancellation_deadline',
        store=True,
        help="10 days after first entry session",
    )
    within_cancellation_window = fields.Boolean(
        string="Within Cancellation Window",
        compute='_compute_within_cancellation_window',
    )
    
    # Qualification for Checkout 2
    grundkurs_sessions_attended = fields.Integer(
        string="Sessions Attended",
        compute='_compute_sessions_attended',
        help="Number of sessions attended in this event",
    )
    grundkurs_consultation_done = fields.Boolean(
        string="Consultation Done",
        help="30-minute online consultation completed",
        default=False,
    )
    grundkurs_qualified_for_continuation = fields.Boolean(
        string="Qualified for Continuation",
        compute='_compute_qualified_for_continuation',
        store=True,
        help="Can book modules B-D (2+ sessions + consultation)",
    )
    
    @api.depends('first_entry_session_date')
    def _compute_cancellation_deadline(self):
        for reg in self:
            if reg.first_entry_session_date:
                reg.cancellation_deadline = reg.first_entry_session_date + timedelta(days=10)
            else:
                reg.cancellation_deadline = False
    
    @api.depends('cancellation_deadline')
    def _compute_within_cancellation_window(self):
        now = fields.Datetime.now()
        for reg in self:
            if reg.cancellation_deadline:
                reg.within_cancellation_window = now <= reg.cancellation_deadline
            else:
                reg.within_cancellation_window = False
    
    def _compute_sessions_attended(self):
        """Count attended sessions for this registration"""
        for reg in self:
            # Assuming session attendance tracked via event.track.visitor or similar
            # This is a placeholder - actual implementation depends on attendance tracking
            reg.grundkurs_sessions_attended = 0  # TODO: Implement based on attendance model
    
    @api.depends('grundkurs_sessions_attended', 'grundkurs_consultation_done')
    def _compute_qualified_for_continuation(self):
        for reg in self:
            reg.grundkurs_qualified_for_continuation = (
                reg.grundkurs_sessions_attended >= 2 and 
                reg.grundkurs_consultation_done
            )
```

**Why:**
- Tracks the 10-day cancellation window from first entry session
- Tracks qualification requirements for Checkout 2

---

### 2.3 Product Extension (Optional)

**File:** `models/product_template.py`

```python
# -*- coding: utf-8 -*-
from odoo import fields, models

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    grundkurs_checkout_type = fields.Selection([
        ('entry', 'Entry (Modul A)'),
        ('continuation', 'Continuation (B-D)'),
        ('continuation_bundle', 'Continuation Bundle (B+C+D)'),
    ], string="Grundkurs Checkout Type")
```

**Why:** Helps identify products in loyalty rules and checkout logic.

---

## 3. View Extensions

### 3.1 Event Session Form Extension

**File:** `views/event_session_views.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_event_session_form_grundkurs" model="ir.ui.view">
        <field name="name">event.session.form.grundkurs</field>
        <field name="model">event.session</field>
        <field name="inherit_id" ref="event_session.view_event_session_form"/>
        <field name="arch" type="xml">
            <xpath expr="//field[@name='name']" position="after">
                <field name="sharepoint_code"/>
                <field name="is_entry_session"/>
            </xpath>
        </field>
    </record>
</odoo>
```

---

### 3.2 Event Registration Form Extension

**File:** `views/event_registration_views.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_event_registration_form_grundkurs" model="ir.ui.view">
        <field name="name">event.registration.form.grundkurs</field>
        <field name="model">event.registration</field>
        <field name="inherit_id" ref="event.view_event_registration_form"/>
        <field name="arch" type="xml">
            <xpath expr="//group[@name='registration_info']" position="after">
                <group string="Grundkurs Status" name="grundkurs_status">
                    <field name="first_entry_session_date"/>
                    <field name="cancellation_deadline"/>
                    <field name="within_cancellation_window"/>
                    <field name="grundkurs_sessions_attended"/>
                    <field name="grundkurs_consultation_done"/>
                    <field name="grundkurs_qualified_for_continuation" 
                           widget="boolean_toggle"/>
                </group>
            </xpath>
        </field>
    </record>
</odoo>
```

---

## 4. Data Records (XML)

### 4.1 Product Tags

**File:** `data/product_tags.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data noupdate="1">
        <!-- Product tags for loyalty program rules -->
        <record id="product_tag_grundkurs_entry" model="product.tag">
            <field name="name">Grundkurs Entry (Modul A)</field>
        </record>
        
        <record id="product_tag_grundkurs_continuation" model="product.tag">
            <field name="name">Grundkurs Continuation (B-D)</field>
        </record>
        
        <record id="product_tag_grundkurs_m18" model="product.tag">
            <field name="name">Grundkurs M18 (2026-2028)</field>
        </record>
    </data>
</odoo>
```

---

### 4.2 Loyalty Program

**File:** `data/loyalty_program_grundkurs.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data noupdate="1">
        <!-- 
            Grundkurs Komplett Promotion
            When customer buys B + C + D together: EUR 880 discount
            4 Raten = 4 x EUR 220 = EUR 880
        -->
        <record id="loyalty_grundkurs_komplett_m18" model="loyalty.program">
            <field name="name">Grundkurs Weiterbildung Komplett (M18)</field>
            <field name="program_type">promotion</field>
            <field name="trigger">auto</field>
            <field name="applies_on">current</field>
            <field name="company_id" ref="base.main_company"/>
            <field name="active" eval="True"/>
        </record>
        
        <!-- Rule: All 3 continuation modules required -->
        <record id="loyalty_grundkurs_komplett_m18_rule" model="loyalty.rule">
            <field name="program_id" ref="loyalty_grundkurs_komplett_m18"/>
            <field name="minimum_qty">3</field>
            <field name="product_tag_id" ref="product_tag_grundkurs_continuation"/>
        </record>
        
        <!-- Reward: EUR 880 fixed discount -->
        <record id="loyalty_grundkurs_komplett_m18_reward" model="loyalty.reward">
            <field name="program_id" ref="loyalty_grundkurs_komplett_m18"/>
            <field name="reward_type">discount</field>
            <field name="discount">880</field>
            <field name="discount_mode">per_order</field>
            <field name="discount_applicability">order</field>
        </record>
    </data>
</odoo>
```

---

### 4.3 Entry Session Config (Loaded from SharePoint)

**File:** `data/session_codes_entry.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data noupdate="0">
        <!-- 
            Entry session codes configuration
            These sessions trigger the 10-day cancellation window
            Synced from SharePoint plan_veranstaltungscodes
        -->
        
        <!-- Note: Actual session records created via SharePoint sync
             This file shows the pattern for manual config if needed -->
        
        <function model="ir.config_parameter" name="set_param">
            <value>grundkurs.entry_session_codes</value>
            <value>A0,A1,A4</value>
        </function>
    </data>
</odoo>
```

---

## 5. SharePoint Sync Extension

### 5.1 Session Code Mapping

Add to existing SharePoint sync in `crearis_agenda`:

**File:** `models/sharepoint_sync.py` (extend existing)

```python
def _sync_session_codes(self, sharepoint_data):
    """
    Sync session codes from plan_veranstaltungscodes
    Maps SharePoint codes to event.session records
    """
    EventSession = self.env['event.session']
    
    entry_codes = self.env['ir.config_parameter'].sudo().get_param(
        'grundkurs.entry_session_codes', 'A0,A1,A4'
    ).split(',')
    
    for row in sharepoint_data:
        code = row.get('veranstaltungscode')  # e.g., "A0", "B2"
        
        # Find or create session
        session = EventSession.search([
            ('sharepoint_code', '=', code)
        ], limit=1)
        
        if session:
            session.write({
                'is_entry_session': code in entry_codes,
                # Map other fields...
            })
```

---

## 6. File Structure Summary

```
crearis_agenda/
├── __manifest__.py          # Add dependencies: event_session, sale_loyalty
├── models/
│   ├── __init__.py          # Add new model imports
│   ├── event_session.py     # NEW: SharePoint code, entry flag
│   ├── event_registration.py # NEW: Cancellation window, qualification
│   └── product_template.py  # NEW: Checkout type field
├── views/
│   ├── event_session_views.xml      # NEW: Form extension
│   └── event_registration_views.xml # NEW: Form extension
├── data/
│   ├── product_tags.xml              # NEW: Loyalty tags
│   ├── loyalty_program_grundkurs.xml # NEW: Komplett discount
│   └── session_codes_entry.xml       # NEW: Entry session config
└── security/
    └── ir.model.access.csv  # Update if new models added
```

---

## 7. __manifest__.py Updates

```python
{
    'name': 'Crearis Agenda',
    'version': '16.0.2.0.0',  # Bump version
    'depends': [
        'event',
        'event_sale',
        'event_session',      # OCA module
        'sale_loyalty',       # Odoo standard
        'website_sale_loyalty', # For website checkout
        # ... existing dependencies
    ],
    'data': [
        # ... existing data files
        'data/product_tags.xml',
        'data/loyalty_program_grundkurs.xml',
        'data/session_codes_entry.xml',
        'views/event_session_views.xml',
        'views/event_registration_views.xml',
    ],
}
```

---

## 8. Implementation Checklist

### Phase 1: Core Models (Week 1)

- [ ] Add `sharepoint_code` to `event.session`
- [ ] Add `is_entry_session` to `event.session`
- [ ] Add cancellation tracking to `event.registration`
- [ ] Add qualification fields to `event.registration`
- [ ] Create view extensions

### Phase 2: Data & Config (Week 2)

- [ ] Create product tags
- [ ] Configure loyalty program
- [ ] Set up entry session codes config
- [ ] Create M18 product records (Modul A, B, C, D)

### Phase 3: SharePoint Integration (Week 3)

- [ ] Extend sync to populate `sharepoint_code`
- [ ] Auto-set `is_entry_session` based on code pattern
- [ ] Test sync with real SharePoint data

### Phase 4: Testing (Week 4)

- [ ] Test cancellation window calculation
- [ ] Test qualification logic
- [ ] Test loyalty discount application
- [ ] End-to-end checkout test

---

## 9. Testing Scenarios

### Scenario 1: New Registration Modul A

```python
# Create registration
reg = env['event.registration'].create({
    'event_id': modul_a_event.id,
    'partner_id': customer.id,
})

# Simulate attending entry session A0
reg.write({
    'first_entry_session_date': fields.Datetime.now()
})

# Check cancellation window
assert reg.within_cancellation_window == True
assert reg.cancellation_deadline == reg.first_entry_session_date + timedelta(days=10)
```

### Scenario 2: Qualification for Checkout 2

```python
# After 2 sessions + consultation
reg.write({
    'grundkurs_sessions_attended': 3,
    'grundkurs_consultation_done': True,
})

assert reg.grundkurs_qualified_for_continuation == True
```

### Scenario 3: Komplett Discount

```python
# Create sale order with B + C + D
order = env['sale.order'].create({
    'partner_id': customer.id,
    'order_line': [
        (0, 0, {'product_id': modul_b.id}),
        (0, 0, {'product_id': modul_c.id}),
        (0, 0, {'product_id': modul_d.id}),
    ]
})

# Loyalty program should auto-apply
order._update_programs_and_rewards()

# Check discount
assert order.reward_amount == -880.0
```

---

## 10. Dependencies Graph

```
                    ┌─────────────────┐
                    │   base (Odoo)   │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│      event      │ │      sale       │ │   sale_loyalty  │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         ▼                   ▼                   │
┌─────────────────┐ ┌─────────────────┐          │
│   event_sale    │ │ website_sale    │          │
└────────┬────────┘ └────────┬────────┘          │
         │                   │                   │
         └───────────┬───────┴───────────────────┘
                     │
                     ▼
           ┌─────────────────────┐
           │   event_session     │  (OCA)
           │       (OCA)         │
           └──────────┬──────────┘
                      │
                      ▼
           ┌─────────────────────┐
           │   crearis_agenda    │
           │   (our extension)   │
           └─────────────────────┘
```

---

*Code Implementation Guide for crearis_agenda*  
*Grundkurs Theaterpädagogik M18*  
*December 2024*
