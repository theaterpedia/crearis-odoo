# Investigation: Odoo Built-in Workflows for DASEi Deadlines

**Date:** 2026-01-31
**Purpose:** Map DASEi requirements (Meldefrist, Stornierungsfrist) to existing Odoo workflows

---

## Executive Summary

Odoo provides several relevant workflow patterns that can be adapted for DASEi's deadline requirements. The `event.mail` scheduler is the closest match for Meldefrist reminders, while `membership.membership_line` and `sale.order.validity_date` provide patterns for cancellation deadlines.

**Key Finding:** No built-in "confirmation deadline" concept exists. Custom implementation required, but can leverage existing scheduler infrastructure.

---

## 1. Relevant Odoo Modules Analyzed

### 1.1 Event Module (`event`)

**Source:** [event/models/event_mail.py](../../versions/16.0/odoo/addons/event/models/event_mail.py)

#### event.mail — Mail Scheduler

| Field | Type | Values | Use Case |
|-------|------|--------|----------|
| `interval_nbr` | Integer | — | Number of intervals |
| `interval_unit` | Selection | now, hours, days, weeks, months | Time unit |
| `interval_type` | Selection | after_sub, before_event, after_event | Trigger type |
| `scheduled_date` | Datetime | Computed | When to send |
| `mail_done` | Boolean | — | Sent flag |
| `mail_state` | Selection | running, scheduled, sent | Status |

**Pattern:** Cron job (`event_mail_scheduler`) runs hourly, finds schedulers where:
```python
schedulers = self.search([
    ('event_id.active', '=', True),
    ('mail_done', '=', False),
    ('scheduled_date', '<=', fields.Datetime.now())
])
```

**Reuse Potential for Meldefrist:** ⭐⭐⭐⭐⭐
- `before_event` trigger type is exactly what we need
- Can set `interval_nbr=60, interval_unit='days'` for 60-day Meldefrist reminder
- Already has email template integration

#### event.registration — Registration States

| State | Description |
|-------|-------------|
| `draft` | Not confirmed |
| `cancel` | Cancelled |
| `open` | Confirmed |
| `done` | Attended |

**Reuse Potential:** ⭐⭐⭐⭐
- Missing: "waitlisted", "expired" states for deadline logic
- `auto_confirm` on event type controls automatic confirmation

#### event.ticket — Sale Window

| Field | Type | Description |
|-------|------|-------------|
| `start_sale_datetime` | Datetime | Registration opens |
| `end_sale_datetime` | Datetime | Registration closes |
| `is_launched` | Boolean | Sale has started |
| `is_expired` | Boolean | Sale has ended |
| `sale_available` | Boolean | Currently open |

**Reuse Potential for Meldefrist:** ⭐⭐⭐
- `end_sale_datetime` could be used as Meldefrist
- But: ticket-level, not registration-level
- Pattern: computed field `is_expired` based on date comparison

---

### 1.2 Sale Module (`sale`)

**Source:** [sale/models/sale_order.py](../../versions/16.0/odoo/addons/sale/models/sale_order.py)

#### sale.order — Quote Validity

| Field | Type | Description |
|-------|------|-------------|
| `validity_date` | Date | Quote expiration |
| `is_expired` | Boolean | Computed: state='sent' AND validity_date < today |

**Pattern:**
```python
@api.depends('company_id')
def _compute_validity_date(self):
    today = fields.Date.context_today(self)
    for order in self:
        days = order.company_id.quotation_validity_days
        if days > 0:
            order.validity_date = today + timedelta(days)
```

**Reuse Potential for Stornierungsfrist:** ⭐⭐⭐⭐
- Pattern for "X days after event" computation
- `is_expired` computed field pattern
- Company-level configuration for default days

#### sale.order.cancel — Cancel Wizard

**Source:** [sale/wizard/sale_order_cancel.py](../../versions/16.0/odoo/addons/sale/wizard/sale_order_cancel.py)

| Feature | Implementation |
|---------|----------------|
| Email notification | Template on cancel |
| Reason tracking | Optional |
| Multi-order support | Batch cancellation |

**Reuse Potential:** ⭐⭐⭐
- Pattern for cancellation with notification
- Could adapt for Module cancellation (Stornierungsfrist breach)

---

### 1.3 Membership Module (`membership`)

**Source:** [membership/models/membership.py](../../versions/16.0/odoo/addons/membership/models/membership.py)

#### membership.membership_line — Subscription Pattern

| Field | Type | Description |
|-------|------|-------------|
| `date_from` | Date | Membership start |
| `date_to` | Date | Membership end |
| `date_cancel` | Date | Cancellation date |
| `date` | Date | Join date |
| `state` | Selection | none, canceled, old, waiting, invoiced, free, paid |

**States Flow:**
```
none → waiting → invoiced → paid → old
                    ↓
                canceled (on payment reversal)
```

**Reuse Potential for Module Lifecycle:** ⭐⭐⭐⭐⭐
- Date range pattern (date_from, date_to) maps to Module duration
- `date_cancel` pattern for Stornierungsfrist tracking
- State machine for payment-based transitions

#### product.template (membership extension)

| Field | Type | Description |
|-------|------|-------------|
| `membership` | Boolean | Is membership product |
| `membership_date_from` | Date | Membership period start |
| `membership_date_to` | Date | Membership period end |

**Reuse Potential:** ⭐⭐⭐
- Product with date range pattern
- Could extend for Module products with Stornierungsfrist

---

### 1.4 Event Sale Module (`event_sale`)

**Source:** [event_sale/models/event_registration.py](../../versions/16.0/odoo/addons/event_sale/models/event_registration.py)

#### event.registration (extended)

| Field | Type | Description |
|-------|------|-------------|
| `sale_order_id` | Many2one | Linked sale order |
| `sale_order_line_id` | Many2one | Linked order line |
| `is_paid` | Boolean | Payment completed |
| `payment_status` | Selection | to_pay, paid, free |

**Reuse Potential:** ⭐⭐⭐⭐
- Links registration to sale order (important for Module billing)
- Payment tracking pattern

---

### 1.5 Product Template (`sale`)

**Source:** [sale/models/product_template.py](../../versions/16.0/odoo/addons/sale/models/product_template.py)

#### product.template — Service Types

| Field | Values | Description |
|-------|--------|-------------|
| `service_type` | manual | Track service manually |
| `invoice_policy` | order, delivery | When to invoice |

**Reuse Potential for Module Products:** ⭐⭐⭐
- `service_type` could be extended for "event registration" type
- `invoice_policy` could be "on registration" vs "on attendance"

---

## 2. Decision Matrix: Meldefrist Implementation

| Approach | Reuses | Custom Code | Complexity | Recommendation |
|----------|--------|-------------|------------|----------------|
| **A: Extend event.mail** | event.mail scheduler | New interval_type='before_meldefrist' | Low | ⭐ RECOMMENDED |
| **B: New computed field** | is_expired pattern | meldefrist_date + is_meldefrist_passed | Low | ✓ Good alternative |
| **C: Extend event.ticket** | end_sale_datetime | Rename/reuse as Meldefrist | Medium | Not ideal semantically |

### Recommended Approach A: Extend event.mail

```python
# In crearis_agenda/models/event_mail.py
class EventMail(models.Model):
    _inherit = 'event.mail'
    
    interval_type = fields.Selection(
        selection_add=[('before_meldefrist', 'Before Meldefrist')],
        ondelete={'before_meldefrist': 'set default'}
    )
    
    @api.depends('event_id.meldefrist_date', 'interval_type', ...)
    def _compute_scheduled_date(self):
        for scheduler in self:
            if scheduler.interval_type == 'before_meldefrist':
                date, sign = scheduler.event_id.meldefrist_date, -1
                scheduler.scheduled_date = date + _INTERVALS[...](sign * scheduler.interval_nbr)
            else:
                super()._compute_scheduled_date()
```

---

## 3. Decision Matrix: Stornierungsfrist Implementation

| Approach | Reuses | Custom Code | Complexity | Recommendation |
|----------|--------|-------------|------------|----------------|
| **A: Extend membership pattern** | date_from, date_to, date_cancel | Module as membership-like product | Medium | ⭐ RECOMMENDED |
| **B: Extend sale.order** | validity_date, is_expired | Module subscription order | Medium | ✓ Good alternative |
| **C: Custom model** | None | agenda.module.subscription | High | Avoid if possible |

### Recommended Approach A: Module as Product with Dates

```python
# In crearis_agenda/models/product_template.py
class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    is_dasei_module = fields.Boolean("Is DASEi Module")
    stornierungsfrist_days = fields.Integer(
        "Stornierungsfrist (Days)", 
        default=10,
        help="Days after first attendance for free cancellation"
    )
```

```python
# In crearis_agenda/models/sale_order_line.py
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    first_attendance_date = fields.Date("First Attendance")
    stornierungsfrist_date = fields.Date(
        "Stornierungsfrist",
        compute="_compute_stornierungsfrist_date",
        store=True
    )
    is_stornierungsfrist_passed = fields.Boolean(
        "Stornierungsfrist Passed",
        compute="_compute_is_stornierungsfrist_passed"
    )
    
    @api.depends('first_attendance_date', 'product_id.stornierungsfrist_days')
    def _compute_stornierungsfrist_date(self):
        for line in self:
            if line.first_attendance_date and line.product_id.stornierungsfrist_days:
                line.stornierungsfrist_date = line.first_attendance_date + timedelta(
                    days=line.product_id.stornierungsfrist_days
                )
```

---

## 4. Summary: What Odoo Provides vs What's Custom

### Odoo Provides (Reusable)

| Feature | Source | DASEi Use |
|---------|--------|-----------|
| Mail scheduler with before_event | event.mail | Meldefrist reminders |
| Cron infrastructure | ir.cron | Hourly deadline checks |
| Registration states (draft→open→done) | event.registration | Base flow |
| Sale order cancellation wizard | sale.order.cancel | Module cancellation |
| Membership date ranges | membership | Module duration pattern |
| Quote validity pattern | sale.order | is_expired computed field |
| Payment status on registration | event_sale | Track paid modules |

### Custom Development Required

| Feature | Complexity | Priority |
|---------|------------|----------|
| `meldefrist_date` on event.event | Low | P1 |
| `interval_type='before_meldefrist'` on event.mail | Low | P1 |
| `stornierungsfrist_days` on product.template | Low | P1 |
| `first_attendance_date` tracking | Medium | P1 |
| `stornierungsfrist_date` computed on sale.order.line | Low | P1 |
| Batch reminder action for dashboard | Medium | P2 |
| Email templates for Meldefrist/Stornierungsfrist | Low | P2 |

---

## 5. Architecture Recommendation

```
┌─────────────────────────────────────────────────────────────────┐
│                    crearis_agenda module                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  event.event (extended)                                         │
│  ├── meldefrist_date (computed from event_type + date_begin)    │
│  └── is_meldefrist_passed (computed)                            │
│                                                                 │
│  event.type (extended)                                          │
│  └── meldefrist_days_before (default: 60)                       │
│                                                                 │
│  event.mail (extended)                                          │
│  └── interval_type += 'before_meldefrist'                       │
│                                                                 │
│  product.template (extended)                                    │
│  ├── is_dasei_module                                            │
│  └── stornierungsfrist_days (default: 10)                       │
│                                                                 │
│  sale.order.line (extended)                                     │
│  ├── first_attendance_date                                      │
│  ├── stornierungsfrist_date (computed)                          │
│  └── is_stornierungsfrist_passed (computed)                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ inherits from
┌─────────────────────────────────────────────────────────────────┐
│  event (core)    sale (core)    membership (optional reference) │
│  - event.mail    - validity     - date patterns                 │
│  - cron          - is_expired   - states                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Next Steps

1. **Create technical spec** for `meldefrist_date` and `stornierungsfrist_date` fields
2. **Prototype** event.mail extension with `before_meldefrist` trigger
3. **Define email templates** for both deadline types
4. **Test** with existing event_session module integration
5. **Document** admin configuration for default days

---

---

## 7. Cross-Check: graphql_theaterpedia & crearis_event_package

### 7.1 Existing Product/Order Implementation

The workspace already has a sophisticated product-line implementation for event packages:

#### crearis_event_package Module

**Key Models:**

| Model | Purpose |
|-------|---------|
| `product.template` extended | `detailed_type='event_package'`, `package_event_type_ids` (M2M to event.type) |
| `product.package.event.line` | Links sale.order.line → event.type → event.event → event.registration |
| `sale.order.line` extended | Auto-creates package_event_line_ids on create |

**Flow:**
```
Customer purchases Module A (event_package product)
    ↓
sale.order.line.create() triggers _create_package_event_lines()
    ↓
Creates product.package.event.line for each event_type in package
    state='pending', event_id=False
    ↓
Configurator wizard allows event selection
    state='selected', event_id=chosen_event
    ↓
action_confirm_and_register() creates event.registration
    state='registered', registration_id=created_reg
```

**Source:** [crearis_event_package/models/sale_order.py](crearis_event_package/models/sale_order.py#L64-L85)

```python
def _create_package_event_lines(self):
    """Create pending event selections for each event type in the package."""
    for sequence, event_type in enumerate(product_tmpl.package_event_type_ids, start=10):
        PackageEventLine.create({
            'sale_order_line_id': self.id,
            'event_type_id': event_type.id,
            'sequence': sequence,
            'state': 'pending',
        })
```

### 7.2 graphql_theaterpedia API

**Relevant Endpoints:**

| GraphQL | Action | Hook Point |
|---------|--------|------------|
| `cartAddItem(product_id, quantity)` | Adds product to cart | `_cart_update()` |
| `cart` query | Returns current order | `website.sale_get_order()` |
| `payment_confirmation` | Order after payment | `action_confirm()` called |
| `register` mutation | Creates user account | `res.users.signup()` |

**Order Confirmation Trigger:**
```python
# graphql_theaterpedia/schemas/payment.py:122
order.with_context(send_email=True).action_confirm()
```

### 7.3 Key Insight: When to Create agenda.line Records

**CRITICAL DISCOVERY:** The existing `product.package.event.line` model is essentially a **proto-agenda.line**!

| product.package.event.line | agenda.line equivalent |
|---------------------------|------------------------|
| `sale_order_line_id` | Module purchase link |
| `event_type_id` | Event slot to fill |
| `event_id` | Selected event |
| `registration_id` | Created registration |
| `state` (pending→selected→registered) | Progress tracking |

**Trigger Point for agenda.line Creation:**

```
1. TRIGGER: sale.order.line.create() for event_package product
   └─> Creates product.package.event.line (proto-agenda.line)
   
2. TRIGGER: Configurator wizard action_confirm_and_register()
   └─> Creates event.registration linked to package line

3. NEW TRIGGER NEEDED: Map product.package.event.line → agenda.line
   └─> Could be done in _create_package_event_lines()
   └─> Or in a compute field that watches package_event_line_ids
```

### 7.4 Customer Onboarding Workflow (graphql_theaterpedia)

**Flow:**
```
1. Register mutation → Creates res.users + res.partner
2. Cart mutations → Creates draft sale.order
3. Payment flow → Confirms order (action_confirm)
4. Package lines already created by sale.order.line.create()
```

**Implication for agenda.line:**
- The package lines are created at **cart add** time (draft order)
- Registrations are created at **configurator confirm** time
- agenda.line should be created either:
  - At package line creation (early, allows planning)
  - At order confirmation (commits the purchase)
  - At registration creation (late, only for confirmed events)

### 7.5 Two Distinct agenda.line Sources

| Source | Trigger Model | Trigger Point | Lines Created | Key Deadline |
|--------|---------------|---------------|---------------|--------------|
| **Product** (Module A/B/C/D) | `product.package.event.line` | `sale.order.line.create()` | Multiple (6-9 per module) | **Stornierungsfrist** |
| **Event** (Offenes Programm) | `event.registration` | `registration.create()` | One per registration | **Meldefrist** |

**Product-driven** agenda.lines are created when customer purchases a Module package. Each event type slot in the package becomes an agenda.line, initially **without a resolved event** (`event_id=False`).

**Event-driven** agenda.lines are created when customer registers directly for a standalone event. The event is already known, so `event_id` is set immediately.

### 7.6 CRITICAL: Unresolved Event Slots (CRM/After-Sales)

**Problem:** Product-driven agenda.lines start in `state='pending'` with `event_id=False`. Customers must select specific events for each slot, but many procrastinate or struggle to decide.

**Real-world pattern:** "Hanging around with ambiguous, undecided phases" → if not resolved properly → **tends to cancellation**.

#### Recommended Workflow Features

**1. Visual UI: Color-coded agenda.line states**
```
🟢 Green  = resolved (event selected, registration created)
🟡 Yellow = pending (event type known, event not selected)
🔴 Red    = overdue (Meldefrist approaching, still unresolved)
⚫ Gray   = cancelled
```

**2. CRM Report: "Ambiguous Agendas Report"**
```python
# Report: Participants with unresolved agenda.lines in next 6 months
class AmbiguousAgendasReport(models.TransientModel):
    _name = 'agenda.ambiguous.report'
    
    def _get_ambiguous_lines(self):
        six_months = fields.Date.today() + timedelta(days=180)
        return self.env['agenda.line'].search([
            ('event_id', '=', False),  # Unresolved
            ('event_type_id.next_event_date', '<=', six_months),  # Has upcoming events
            ('state', '!=', 'cancelled'),
        ])
    
    def action_generate_report(self):
        """Group by partner, show count of unresolved slots per person."""
        lines = self._get_ambiguous_lines()
        # Group by partner_id, count unresolved, sort by urgency
        ...
```

**3. Automated Reminder Workflow**
- Cron: Check for agenda.lines with `event_id=False` where next available event is within 30 days
- Send reminder email: "Please select your event for [Event Type] - options available: [list]"
- Escalate to course coordinator if no action after 2 reminders

**4. Dashboard Widget: "Resolution Queue"**
```
┌─────────────────────────────────────────────────────┐
│ UNRESOLVED EVENT SELECTIONS                    🔴 23 │
├─────────────────────────────────────────────────────┤
│ Within 30 days:  8 participants (urgent)            │
│ Within 60 days: 12 participants (attention needed)  │
│ Within 90 days:  3 participants                     │
│                                                     │
│ [View All] [Send Bulk Reminder] [Export CSV]        │
└─────────────────────────────────────────────────────┘
```

### 7.7 Recommendation: Extend product.package.event.line (Option A)

```python
class ProductPackageEventLine(models.Model):
    _inherit = 'product.package.event.line'
    
    agenda_line_id = fields.Many2one('agenda.line', string="Agenda Line")
    
    # Resolution tracking
    resolution_reminder_count = fields.Integer(default=0)
    resolution_reminder_last = fields.Date()
    
    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        for line in lines:
            # Create agenda.line immediately (unresolved)
            line.agenda_line_id = self.env['agenda.line'].create({
                'partner_id': line.partner_id.id,
                'event_type_id': line.event_type_id.id,
                'event_id': False,  # UNRESOLVED - needs CRM follow-up
                'source_type': 'product',
                'source_ref': f'product.package.event.line,{line.id}',
                'state': 'pending',
            })
        return lines
    
    def write(self, vals):
        res = super().write(vals)
        # Sync event_id to agenda.line when resolved
        if 'event_id' in vals:
            for line in self:
                if line.agenda_line_id:
                    line.agenda_line_id.write({
                        'event_id': vals['event_id'],
                        'state': 'selected' if vals['event_id'] else 'pending',
                    })
        return res
```

---

## Appendix: Key Odoo Source References

| File | Key Pattern |
|------|-------------|
| [event/models/event_mail.py](../../versions/16.0/odoo/addons/event/models/event_mail.py#L129) | `_compute_scheduled_date()` |
| [event/models/event_mail.py](../../versions/16.0/odoo/addons/event/models/event_mail.py#L261) | `schedule_communications()` cron |
| [event/data/ir_cron_data.xml](../../versions/16.0/odoo/addons/event/data/ir_cron_data.xml) | Hourly scheduler cron |
| [sale/models/sale_order.py](../../versions/16.0/odoo/addons/sale/models/sale_order.py#L306) | `_compute_validity_date()` |
| [sale/models/sale_order.py](../../versions/16.0/odoo/addons/sale/models/sale_order.py#L571) | `_compute_is_expired()` |
| [membership/models/membership.py](../../versions/16.0/odoo/addons/membership/models/membership.py#L25) | date_from, date_to, date_cancel pattern |
| [membership/models/product.py](../../versions/16.0/odoo/addons/membership/models/product.py#L11) | membership_date_from/to on product |

### Workspace-Specific References

| File | Key Pattern |
|------|-------------|
| [crearis_event_package/models/sale_order.py](crearis_event_package/models/sale_order.py#L64) | `_create_package_event_lines()` — trigger point |
| [crearis_event_package/models/product_package_event_line.py](crearis_event_package/models/product_package_event_line.py#L97) | `action_create_registration()` |
| [crearis_event_package/wizard/event_package_configurator.py](crearis_event_package/wizard/event_package_configurator.py#L84) | `action_confirm_and_register()` |
| [graphql_theaterpedia/schemas/shop.py](graphql_theaterpedia/schemas/shop.py#L43) | `CartAddItem` mutation — cart update |
| [graphql_theaterpedia/schemas/payment.py](graphql_theaterpedia/schemas/payment.py#L122) | `action_confirm()` — order confirmation |
| [agenda_dasei/data/product_template_data.xml](agenda_dasei/data/product_template_data.xml) | Module A/B/C/D product definitions |
