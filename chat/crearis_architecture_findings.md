# Crearis Architecture: Preparational Findings for Code-Automation

> **Purpose:** Negative Spec + Architecture Documentation for future pickup  
> **Sprint End:** December 21, 2025 (last day)  
> **Resume:** In 2-3 weeks  
> **Author:** Claude (Code Automation Prep)

---

## 1. Architecture Overview: What Already Exists

### 1.1 Module Dependency Chain

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EXISTING ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │                    CREARIS (base module)                     │           │
│  │                                                              │           │
│  │  Models:                                                     │           │
│  │  • event.event (extended)     • crearis.domainuser           │           │
│  │  • website (extended)         • res.company (extended)       │           │
│  │  • res.partner (extended)     • web.options.abstract         │           │
│  │                                                              │           │
│  │  Infrastructure:                                             │           │
│  │  • JSON field widget          • use_* feature flags          │           │
│  │  • domain_code pattern        • cid (crearis ID) pattern     │           │
│  │  • web.options.abstract       • demo.data.mixin              │           │
│  └──────────────────────────────────┬──────────────────────────┘           │
│                                     │                                       │
│                                     ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │              GRAPHQL_THEATERPEDIA (API layer)               │           │
│  │                                                              │           │
│  │  Full e-commerce checkout via GraphQL:                       │           │
│  │  • ShoppingCartQuery + ShopMutation (add/update/remove)      │           │
│  │  • PaymentQuery + PaymentMutation (Adyen integration)        │           │
│  │  • OrderQuery + OrderMutation                                │           │
│  │  • DomainUserQuery + DomainUserMutation                      │           │
│  │  • EventQuery + EventMutation                                │           │
│  │                                                              │           │
│  │  Already supports: Cart → Order → Payment flow              │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Multi-Company / Multi-Website Pattern

**Key Insight:** The `website` model acts as the primary domain/tenant identifier, NOT `res.company`.

```python
# From crearis/models/website.py
class Website(models.Model):
    _inherit = 'website'
    
    domain_code = fields.Char('Domain-Code')  # e.g., "dasei", "theaterpedia"
    
    # Feature flags - stored on website, not company
    use_msteams = fields.Boolean()
    use_jitsi = fields.Boolean()
    use_template_codes = fields.Boolean()
    use_tracks = fields.Boolean()
    use_products = fields.Boolean()
    use_overline = fields.Boolean()
    use_teasertext = fields.Boolean()
```

```python
# From crearis/models/event.py - features are COMPUTED from website
class EventEvent(models.Model):
    _inherit = "event.event"
    
    domain_code = fields.Many2one('website', ...)  # Links event to a website/domain
    
    # Computed from domain_code (website), not stored
    use_tracks = fields.Boolean(compute=_compute_use_tracks)
    use_products = fields.Boolean(compute=_compute_use_products)
```

**Performance Assessment:**
- ✅ **Good Pattern**: Feature flags on `website` are efficient (100-200 websites vs 100-200 companies)
- ✅ **Computed fields on event**: No storage bloat, dynamically resolved
- ⚠️ **Potential issue**: Each event access triggers computed field evaluation
- 💡 **Recommendation**: Consider `store=True` on critical computed fields if query performance becomes an issue

---

## 2. The `use_*` Feature Flag Convention

### 2.1 Pattern Analysis

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  FEATURE FLAG FLOW                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  res.config.settings (UI)                                                  │
│         │                                                                   │
│         │ related='website_id.use_*'                                       │
│         ▼                                                                   │
│  website (storage)                                                         │
│         │                                                                   │
│         │ event.domain_code → website                                      │
│         ▼                                                                   │
│  event.event (computed)                                                    │
│         │                                                                   │
│         │ view attrs: {'invisible': [('use_tracks','=',False)]}            │
│         ▼                                                                   │
│  Conditional UI fields                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Odoo Best Practices Assessment

| Aspect | Current Implementation | Best Practice | Verdict |
|--------|------------------------|---------------|---------|
| **Storage location** | `website` model | ✅ Correct for multi-tenant | ✅ |
| **Computed fields** | `store=False` | OK for simple lookups | ⚠️ |
| **UI configuration** | `res.config.settings` related fields | ✅ Standard Odoo pattern | ✅ |
| **View conditionals** | `attrs` based on computed boolean | ✅ Standard pattern | ✅ |
| **Performance** | Re-computed on each access | Acceptable for booleans | ✅ |

**Q2 Answer:** Your `use_*` pattern is **well-designed and follows Odoo conventions**. It's performant because:
1. Boolean computed fields are cheap
2. The computation is a simple field lookup (`domain_code.use_tracks`)
3. No complex SQL or joins involved

---

## 3. JSONB Fields: The `web.options.abstract` Pattern

### 3.1 Current Implementation

```python
# From crearis/models/weboptions.py
class WebOptionsAbstract(models.AbstractModel):
    _name = 'web.options.abstract'
    
    # Four JSON fields for structured options
    page_options = fields.Json(default=False)
    aside_options = fields.Json(default=False)
    header_options = fields.Json(default=False)
    footer_options = fields.Json(default=False)
    
    # Individual field accessors via compute/inverse
    page_background = fields.Selection(..., compute='_compute_page_background', inverse='_inverse_page_background')
    page_cssvars = fields.Text(..., compute='_compute_page_cssvars', inverse='_inverse_page_cssvars')
    # ... many more computed accessors
```

### 3.2 JSONB Effort Analysis

| Use Case | Effort Level | Recommendation |
|----------|--------------|----------------|
| **GUIDs/Config (admin, one-time)** | Low | ✅ JSONB is ideal |
| **Display-only in views** | Low | ✅ JSONB works well |
| **Editable fields in form views** | Medium-High | ⚠️ Requires computed field accessors |
| **Search/Filter on JSON content** | High | ❌ Avoid for searchable data |
| **Inline tree editing** | Very High | ❌ Not worth the effort |

### 3.3 Q1 Answer: JSONB for SharePoint GUIDs

**Recommendation: YES, use JSONB for SharePoint config**

For GUIDs (tenant_id, site_id, list_ids), JSONB is ideal because:
1. Admin sets these once during setup
2. No need for inline editing or searching
3. Keeps `res.company` clean for 95% of companies not using SharePoint

**Proposed structure:**
```python
class Company(models.Model):
    _inherit = "res.company"
    
    sharepoint_config = fields.Json(
        string='SharePoint Configuration',
        help='SharePoint connection settings (tenant, site, lists)',
        default=False
    )
```

**Config structure:**
```json
{
  "tenant_id": "uuid-here",
  "site_id": "uuid-here",
  "lists": {
    "plan_veranstaltungscodes": "list-guid",
    "plan_events": "list-guid",
    "plan_sessions": "list-guid"
  },
  "sync_enabled": true,
  "last_sync": "2025-12-21T10:00:00Z"
}
```

### 3.4 The `web.options.abstract` Mixin Cost

Looking at `weboptions.py` (672 lines), the pattern is **heavyweight**:
- 4 JSON fields
- ~30 computed field accessors with inverse methods
- Complex get/set helpers

**Verdict for new modules:**
- For `crearis_agenda`: Use simple individual fields OR single JSONB with wizard
- For `crearis_dasei`: Can inherit `web.options.abstract` if visual options needed

---

## 4. Q3: Separate Config Model Alternative

### 4.1 Pattern: `crearis.agenda.config`

```python
class CreariAgendaConfig(models.Model):
    _name = 'crearis.agenda.config'
    _description = 'SharePoint Sync Configuration'
    
    company_id = fields.Many2one('res.company', required=True, ondelete='cascade')
    
    # Simple fields instead of JSONB
    sharepoint_tenant_id = fields.Char('Tenant ID')
    sharepoint_site_id = fields.Char('Site ID')
    sync_enabled = fields.Boolean('Sync Enabled', default=False)
    last_sync = fields.Datetime('Last Sync')
    
    # List GUIDs - could be JSONB or dedicated model
    list_config = fields.Json('List Configuration')
```

### 4.2 Trade-off Analysis

| Approach | Pros | Cons |
|----------|------|------|
| **JSONB on res.company** | Simple, no new model | Field exists on all companies |
| **Separate config model** | Zero bloat, clear separation | Extra join for queries |
| **JSONB on website** | Fits existing pattern | SharePoint is company-level, not website |

**Recommendation:** For SharePoint sync, use **JSONB on res.company** with a helper method:

```python
class Company(models.Model):
    _inherit = "res.company"
    
    sharepoint_config = fields.Json(default=False)
    
    @property
    def uses_sharepoint(self):
        return bool(self.sharepoint_config and self.sharepoint_config.get('sync_enabled'))
```

---

## 5. The CID (Crearis ID) Pattern

### 5.1 Current Implementation

```python
# From crearis/models/event.py
@api.depends("domain_code", "event_type_id")
def _compute_cid(self):
    template_code = 'evnt'
    if self.use_template_codes:
        template_code = self.event_type_id.name

    for event in self:
        domain_code = event.domain_code.domain_code
        if not event.id:
            event.cid = '{}.event-{}__{}'.format(domain_code, template_code, "-1")
        else:
            event.cid = '{}.event-{}__{}'.format(domain_code, template_code, event.id)

cid = fields.Char("Crearis ID", compute=_compute_cid, store=True)
```

**Current format:** `{domain_code}.event-{type}__{id}`  
**Example:** `dasei.event-M18__42`

### 5.2 Proposed Extension

Your idea for flexible CID patterns:

```
Templated events:  {domain_code}.event-{type}-{template}__{slug}
Simple events:     {domain_code}.event__{slug}
```

**Examples:**
- `dasei.event-grundkurs-m18__einstiege-theaterspiel`
- `theaterpedia.event__sommerfest-2025`

### 5.3 Implementation Sketch (FUTURE WORK)

```python
@api.depends("domain_code", "event_type_id", "name")
def _compute_cid(self):
    for event in self:
        domain = event.domain_code.domain_code
        slug = slugify(event.name) if event.name else str(event.id)
        
        if event.use_template_codes and event.event_type_id:
            type_code = event.event_type_id.code or event.event_type_id.name
            # Check if it's a templated event (like Grundkurs with cohort)
            if event.template_cohort:  # NEW field
                cid = f'{domain}.event-{type_code}-{event.template_cohort}__{slug}'
            else:
                cid = f'{domain}.event-{type_code}__{slug}'
        else:
            cid = f'{domain}.event__{slug}'
        
        event.cid = cid.lower()
```

---

## 6. DomainUser: Multi-Website User Roles

### 6.1 Current Model

```python
# From crearis/models/domainuser.py
class DomainUser(models.Model):
    _name = "crearis.domainuser"
    _inherit = ['web.options.abstract', "demo.data.mixin"]
    
    domain_id = fields.Many2one("website", required=True)
    user_id = fields.Many2one("res.users", required=True)
    role = fields.Selection([
        ("user", "Teilnehmer:in"),
        ("team", "Team"),
        ("exec", "Manager:in"),
        ("spec", "Special")
    ])
```

### 6.2 Use Case Understanding

The `crearis.domainuser` bridges users to websites with roles:
- One user can be "Team" on dasei.de but "Teilnehmer:in" on theaterpedia.org
- This is the backbone for multi-tenant authorization
- 100-200 websites × users = potentially 1000s of domainuser records

### 6.3 GraphQL Integration

Already fully implemented in `graphql_theaterpedia/schemas/domainuser.py`:
- `DomainUserQuery.domainuser(id)` - Get single
- `DomainUserQuery.domainusers(domain_code, filter)` - List for domain
- `AddDomainUser` / `UpdateDomainUser` / `DeleteDomainUser` - Full CRUD

**This is checkout-ready!** VueJS can:
1. Query user's role on current domain
2. Show/hide features based on capabilities
3. Update profile via GraphQL mutations

### 6.4 DASEi Case Study: Multi-Domain Single-Company Pattern

DAS Ei e.V. demonstrates how **one company uses multiple domain_codes** to segment products and user experiences:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  DAS Ei e.V. (res.company)                                                 │
│  One legal entity, FIVE websites/domain_codes                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐                                  │
│  │ dasei           │  │ dasei0          │                                  │
│  │ verein.dasei.eu │  │ login.dasei.eu  │                                  │
│  │                 │  │                 │                                  │
│  │ Org Participants│  │ Quick & Easy    │                                  │
│  │ • Blog authors  │  │ • First contact │                                  │
│  │ • Contributors  │  │ • Newsletter    │                                  │
│  │ • Board/Verein  │  │ • Book 1 workshop│                                 │
│  └─────────────────┘  │ • Look around   │                                  │
│                       └────────┬────────┘                                  │
│                                │                                            │
│           ┌────────────────────┼────────────────────┐                      │
│           ▼                    ▼                    ▼                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │ dasei1          │  │ dasei2          │  │ dasei3          │             │
│  │ einstiege.      │  │ grundstufe.     │  │ aufbaustufe.    │             │
│  │ dasei.eu        │  │ dasei.eu        │  │ dasei.eu        │             │
│  │                 │  │                 │  │                 │             │
│  │ MODUL A         │  │ MODULE B,C,D    │  │ MODULE E-P      │             │
│  │ (Einstiege)     │  │ (Grundstufe)    │  │ (Aufbaustufe)   │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                             │
│  CONTENT INCLUSION:                                                        │
│  • dasei3 includes content from dasei2 AND dasei1                          │
│  • Progressive access as students advance                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.5 How DomainUsers Enable This

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  EXAMPLE: User "Maria" progresses through DAS Ei                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  crearis.domainuser records for Maria (casual visitor booking 1 workshop): │
│                                                                             │
│  ┌─────────────┬────────────┬─────────────┬────────────────────────┐       │
│  │ domain_id   │ role       │ capabilities│ What Maria sees        │       │
│  ├─────────────┼────────────┼─────────────┼────────────────────────┤       │
│  │ dasei0      │ user       │ visitor     │ Quick booking, browse  │       │
│  │ dasei1      │ (none yet) │ -           │ No access              │       │
│  └─────────────┴────────────┴─────────────┴────────────────────────┘       │
│                                                                             │
│  Maria books Modul A (Grundkurs entry):                                    │
│                                                                             │
│  ┌─────────────┬────────────┬─────────────┬────────────────────────┐       │
│  │ domain_id   │ role       │ capabilities│ What Maria sees        │       │
│  ├─────────────┼────────────┼─────────────┼────────────────────────┤       │
│  │ dasei0      │ user       │ visitor     │ Quick booking, browse  │       │
│  │ dasei1      │ user       │ participant │ Modul A dashboard      │       │
│  │ dasei2      │ (none yet) │ -           │ No access              │       │
│  │ dasei3      │ (none yet) │ -           │ No access              │       │
│  └─────────────┴────────────┴─────────────┴────────────────────────┘       │
│                                                                             │
│  After completing Modul A + qualification:                                 │
│                                                                             │
│  ┌─────────────┬────────────┬─────────────┬────────────────────────┐       │
│  │ domain_id   │ role       │ capabilities│ What Maria sees        │       │
│  ├─────────────┼────────────┼─────────────┼────────────────────────┤       │
│  │ dasei0      │ user       │ visitor     │ Quick booking, browse  │       │
│  │ dasei1      │ user       │ alumni      │ Modul A (completed)    │       │
│  │ dasei2      │ user       │ participant │ Modules B,C,D dashboard│       │
│  │ dasei3      │ (none yet) │ -           │ No access              │       │
│  └─────────────┴────────────┴─────────────┴────────────────────────┘       │
│                                                                             │
│  Staff member "Hans" (works across all):                                   │
│                                                                             │
│  ┌─────────────┬────────────┬─────────────┬────────────────────────┐       │
│  │ domain_id   │ role       │ capabilities│ What Hans sees         │       │
│  ├─────────────┼────────────┼─────────────┼────────────────────────┤       │
│  │ dasei       │ exec       │ board       │ Verein, org internals  │       │
│  │ dasei0      │ team       │ admin       │ Manage public site     │       │
│  │ dasei1      │ team       │ instructor  │ Teach + manage Mod A   │       │
│  │ dasei2      │ team       │ instructor  │ Teach + manage B,C,D   │       │
│  │ dasei3      │ team       │ instructor  │ Teach + manage E-P     │       │
│  └─────────────┴────────────┴─────────────┴────────────────────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.6 Architecture Insight: Website vs Company

This pattern reveals why **features are on `website`, not `res.company`**:

| Aspect | res.company | website (domain_code) |
|--------|-------------|----------------------|
| **Legal entity** | DAS Ei e.V. | - |
| **Tax/Invoicing** | One company | - |
| **Products** | Shared catalog | Filtered per domain |
| **Users** | `res.users` | `crearis.domainuser` per domain |
| **Feature flags** | - | `use_tracks`, `use_sessions`, etc. |
| **VueJS dashboards** | - | One per domain_code |
| **Events** | - | `event.domain_code` → website |

**Key insight:** The `res.company` is for legal/financial, while `website` (domain_code) is for **product segmentation and user experience**.

### 6.7 Implications for crearis_agenda / crearis_dasei

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  MODULE SCOPE CLARITY                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  crearis_agenda (generic)                                                  │
│  • SharePoint sync config on res.company (one per legal entity)            │
│  • NOT aware of dasei1/dasei2/dasei3 split                                 │
│  • Syncs to events that get assigned to domains by other logic             │
│                                                                             │
│  crearis_dasei (DASEi-specific)                                            │
│  • Knows about dasei/dasei0/dasei1/dasei2/dasei3 domain_codes              │
│  • dasei = verein (org contributors), dasei0 = public (casual visitors)    │
│  • Routes products to correct domains                                       │
│  • Manages qualification → domainuser creation on dasei2                   │
│  • Loyalty programs, session tracking, checkout rules                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. GraphQL Checkout: Already Implemented!

### 7.1 Existing Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GRAPHQL CHECKOUT FLOW (graphql_theaterpedia)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  VueJS / Nuxt / Nitro                                                      │
│         │                                                                   │
│         │ GraphQL                                                           │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  ShoppingCartQuery                                          │           │
│  │  • cart → current order                                     │           │
│  └─────────────────────────────────────────────────────────────┘           │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  ShopMutation                                               │           │
│  │  • cartAddItem(product_id, quantity)                        │           │
│  │  • cartUpdateItem(line_id, quantity)                        │           │
│  │  • cartRemoveItem(line_id)                                  │           │
│  │  • cartAddMultipleItems([{id, qty}])                        │           │
│  │  • setShippingMethod(shipping_method_id)                    │           │
│  └─────────────────────────────────────────────────────────────┘           │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  PaymentMutation (Adyen)                                    │           │
│  │  • adyenProviderInfo(provider_id)                           │           │
│  │  • adyenPaymentMethods(provider_id)                         │           │
│  │  • adyenTransaction(provider_id)                            │           │
│  │  • adyenPayments(provider_id, payment_method, ...)          │           │
│  │  • adyenPaymentDetails(provider_id, payment_details)        │           │
│  └─────────────────────────────────────────────────────────────┘           │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  OrderMutation                                              │           │
│  │  • (order confirmation, status updates)                     │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Implication for Grundkurs

The checkout infrastructure is **already built**. For Grundkurs we only need:
1. Products configured in Odoo (Modul A, B, C, D)
2. Loyalty program for EUR 880 discount
3. Qualification check before Checkout 2 (new logic)

---

## 8. NEGATIVE SPEC: Ideas to Set Aside

These are the "spectacular ideas" that should be **deferred** to focus on today's KISS work:

### 8.1 ❌ Custom CID Slug System
**Idea:** `dasei.event-grundkurs-m18__einstiege-theaterspiel`  
**Why defer:** Current CID with numeric IDs works. Slug-based CIDs need URL handling, uniqueness validation, slug generation on name change. Complexity for later.

### 8.2 ❌ Transient JSONB Editor Wizard
**Idea:** Nice wizard UI for editing JSON config fields  
**Why defer:** Compute/inverse pattern works for now. A polished wizard is UX enhancement, not MVP blocker.

### 8.3 ❌ Session Attendance Tracking
**Idea:** Track which sessions each participant attended  
**Why defer:** Standard Odoo event attendance or manual tracking suffices for MVP. Can enhance later with QR scanning integration.

### 8.4 ❌ Automatic Checkout 2 Unlock
**Idea:** System auto-detects qualification and sends email invite  
**Why defer:** Manual qualification marking works. Automation is nice-to-have.

### 8.5 ❌ VueJS Checkout Component
**Idea:** Full VueJS two-checkout flow  
**Why defer:** Build Odoo-native checkout first. GraphQL integration works, but VueJS UI is Phase 2.

### 8.6 ❌ event_session Integration
**Idea:** Integrate OCA event_session into crearis_agenda  
**Why defer:** Session management is DASEi-specific. Goes into `crearis_dasei`, not the generic `crearis_agenda`.

---

## 9. KISS Work for Today

### 9.1 What the Architecture Tells Us

Based on the investigation, here's what should happen **now**:

#### crearis (update existing)
1. **No changes needed** - the base infrastructure is solid
2. The `use_*` pattern, `cid` pattern, and `web.options.abstract` are all working

#### crearis_agenda (new module)
1. **Minimal scope**: SharePoint sync infrastructure only
2. **JSONB on company**: `sharepoint_config` field
3. **No event_session**: That's DASEi-specific
4. **No qualification logic**: That's DASEi-specific

#### crearis_dasei (new module, later)
1. **Depends on**: `crearis`, `crearis_agenda`, `event_session`
2. **Implements**: Grundkurs products, sessions, qualification, loyalty

### 9.2 Concrete Today Tasks

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TODAY'S WORK (KISS)                                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. CREATE: crearis_agenda module skeleton                                  │
│     • __manifest__.py (depends: crearis)                                   │
│     • models/res_company.py (sharepoint_config JSONB field)                │
│     • views/res_company_views.xml (show config field)                      │
│                                                                             │
│  2. DOCUMENT: SharePoint field mapping                                      │
│     • Which SharePoint columns → which Odoo fields                         │
│     • Standard Odoo naming (Title→name, Created→create_date)               │
│                                                                             │
│  3. STUB: Sync infrastructure                                               │
│     • models/sharepoint_sync.py (empty class, method stubs)                │
│     • Security rules                                                        │
│                                                                             │
│  4. DO NOT: Add event_session, qualification, loyalty, products            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Resume Checklist (In 2-3 Weeks)

When you return to this project:

1. **Read this document** - You're already caught up!
2. **Check chat/*.md reports** - Grundkurs specs are there
3. **crearis_agenda**: Implement actual SharePoint sync
4. **crearis_dasei**: Start with product/event configuration
5. **Test loyalty program** in Odoo UI before any VueJS work

---

*Preparational Findings for Code-Automation*  
*Last Sprint Day: December 21, 2025*  
*Resume: ~January 2026*
