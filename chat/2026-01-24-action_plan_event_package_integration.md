# Action Plan: Event Package Integration with Domain Codes & GraphQL

**Date:** 2026-01-24  
**Updated:** 2026-01-26  
**Context:** Integrating `crearis_event_package` module with domain codes system and `graphql_theaterpedia`  
**Sprint:** [2026-01-26_sprint_agenda_dasei.md](./2026-01-26_sprint_agenda_dasei.md)

---

## 🚨 Blocking Tasks (Resolve First)

> These tasks must be explored/resolved before running the main action plan

- [x] **B1**: **cid / xmlid / slug architecture** ✅ RESOLVED
  
  **Decision (2026-01-26):**
  
  | Concept | Purpose | Mutability |
  |---------|---------|------------|
  | `cid` | Stable internal identifier (xmlid) | NEVER changes after creation |
  | `slug` | SEO-friendly URL segment | Auto-created, manual edit only |
  | `cid__slug` | Combined permalink format | Computed from cid + slug |
  
  **CID Format:**
  ```
  # With use_template_codes=True:
  {domain}.event-{template_code}__{id}
  → dasei.event-a1__123
  
  # With use_template_codes=False:
  {domain}.event__{id}
  → dasei.event__123
  
  # OLD format (deprecated, remove 'evnt' fallback):
  dasei.event-evnt__123  ❌
  ```
  
  **Slug behavior:**
  - Auto-generated on record creation from `name`/`heading`
  - Does NOT auto-update when name changes (preserves permalinks)
  - Editable via explicit "Edit Slug" button in UI
  - Example: `am_anfang_war_der_kreis`
  
  **GraphQL interface:**
  ```graphql
  type Event {
    cid: String!      # "dasei.event-a1__123"
    slug: String!     # "am_anfang_war_der_kreis"
    cidSlug: String!  # "dasei.event-a1__123__am_anfang_war_der_kreis"
  }
  ```
  
  **Implementation tasks:**
  - [ ] T-CID-1: Update `_compute_cid` to drop 'evnt' fallback
  - [ ] T-CID-2: Add `slug` field to `event.event` (stored, manual edit)
  - [ ] T-CID-3: Add `_compute_slug` for initial slug generation
  - [ ] T-CID-4: Add "Edit Slug" button to event form view
  - [ ] T-CID-5: Same slug architecture for `blog.post`
  - [ ] T-CID-6: Add `cidSlug` computed field
  - [ ] G-CID-1: Expose `cid`, `slug`, `cidSlug` in GraphQL EventType

- [x] **B2**: **Event-stages sysreg mapping** ✅ RESOLVED
  
  **Decision (2026-01-26): Sysreg bitmask-compatible stages**
  
  | Sysreg | Name | EN | DE | CS | Odoo xmlid |
  |--------|------|----|----|----|-----------|
  | 1 | new | new | neu | nový | `event.event_stage_new` |
  | 8 | demo | planned | vorgemerkt | plánovaný | `event.event_stage_booked` |
  | 64 | draft | booked | geplant | rezervovaný | `crearis.event_stage_booked` |
  | 512 | confirmed | announced | angekündigt | oznámený | `event.event_stage_announced` |
  | 4096 | released | current | aktuell | aktuální | `crearis.event_stage_current` |
  | 8192 | completed | completed | vollständig | dokončený | `event.event_stage_done` |
  | 12288 | cancelled | cancelled | gestrichen | zrušený | `event.event_stage_cancelled` |
  | 32768 | archived | — | — | — | Odoo `active=False` |
  | 65536 | trash | — | — | — | Odoo `active=False` |
  
  **Implementation:**
  - ✅ Updated `crearis/data/event_stage_data.xml`
  - ✅ Created `crearis/i18n/de.po` (German)
  - ✅ Created `crearis/i18n/cs.po` (Czech)
  - ⏳ DB cleanup: delete duplicate stages after module update
  - ⏳ Update `crearis_agenda` sync to map `StatusLookupId` → `stage_id`
  
  **SharePoint Mapping (plan_planungsstatus.StatusLookupId):**
  See dev-docs for full mapping table.

- [x] **B3**: **Registration states sysreg mapping** ✅ RESOLVED
  
  **Decision (2026-01-26): Extend Odoo Selection field with sysreg-compatible states**
  
  | Odoo State | Sysreg | SP ID | EN | DE |
  |------------|--------|-------|----|----|  
  | new | 1 | 12 | offer | Angebot |
  | demo | 8 | 5 | proposal | vorbehaltlich |
  | draft | 64 | 1 | unconfirmed | unbestätigt |
  | open | 512 | 13 | confirmed | bestätigt |
  | done | 4096 | 3 | attended | vollständig |
  | cancel | 12288 | 8 | canceled | storniert |
  | no_show | 16384 | 6 | absent | abwesend |
  | partial | 20480 | 4 | partial | teilweise |
  
  **New states:** `new`, `demo`, `no_show`, `partial`
  
  **Implementation plan:** [2026-01-26-impl_plan_registration_states.md](./2026-01-26-impl_plan_registration_states.md)

---

## 🔷 Moderate Priority (First Batch)

- [ ] **T-UI-1**: **Template code visualization**
  
  If `use_template_codes` is active, we should display the template-code of the event prominently (like 24px font-size) in a square-box with grey background top-left of the `event.event` main-view.
  
  **Implementation**: Add to event form view in `crearis` module

---

## Task Collection (Unsorted)

### ✅ Critical Decision (RESOLVED)

- [x] **T0**: **DECIDE: `use_event_packages` scope — Company-level or Website/Domaincode-level?**
  
  **Decision (2026-01-26): Option B — Company-primary + product filtering**
  
  | Aspect | Implementation |
  |--------|----------------|
  | Primary toggle | `res.company.use_event_packages` — enable once per company |
  | Product filtering | `product.template.domain_code` — filter which packages show on which website |
  | Website override | Keep `website.use_event_packages` for special cases (website doesn't sell packages) |
  | Event compute | Falls back: `domain_code.use_event_packages` → `company.use_event_packages` |
  
  **Rationale:**
  - Simpler mental model: "DASEi sells event packages" (company-level)
  - Flexible filtering: Package A shows on dasei1, Package B on dasei2 (via product.domain_code)
  - No need to enable same feature on multiple websites
  - Current fallback logic already supports this pattern

---

### ⚠️ Cross-Domain Display Concerns (Document for GraphQL/VueJS)

> These concerns must be addressed when implementing GraphQL layer and VueJS frontend.

**Problem:** If a company partially has event_packages across domains, the VueJS frontend could get confused:

| Scenario | Risk | Mitigation |
|----------|------|------------|
| Packaged event displayed as autonomous | Sold standalone instead of via package | `package_only=True` must hide from public listings |
| Package A events visible on dasei2 | Wrong domain shows irrelevant events | Filter by `domain_code` in GraphQL queries |
| Anon user sees package-only event | Confusion, can't register | GraphQL: don't return `package_only` events in public queries |

**Required GraphQL signals for VueJS:**
1. `event.package_only` — Boolean, hide from public if True
2. `event.use_event_packages` — Boolean, context for frontend logic
3. `event.domain_code` — String, filter events by current website
4. `product.domain_code` — String, filter packages by current website

**Action items for GraphQL (see 2026-01-28-action_plan_graphql.md):**
- G-NEW: Add `package_only` to EventType GraphQL
- G-NEW: Ensure event queries filter by `domain_code` context
- G-NEW: Add query parameter `includePackageOnly` (default False for public)

---

### 🔷 Feature Flag Hierarchy (use_products → use_event_packages)

### �🔷 GraphQL Schema Extensions

- [ ] **T1**: Extend `EventType` GraphQL object with template_code fields (`is_template_code`, `template_parent_id`, `template_cimg`, `template_teasertext`, `template_units`, `template_heading`)
- [ ] **T2**: Add `company_id` to `EventType` GraphQL for multi-tenant filtering
- [ ] **T3**: Create new `ProductPackage` GraphQL type (or extend `Product`) for `event_package` detailed_type
- [ ] **T4**: Add `package_event_type_ids` relation to Product GraphQL
- [ ] **T5**: Create `PackageEventLine` GraphQL type for traceability queries
- [ ] **T6**: Add GraphQL query `eventPackages` to fetch products of type `event_package`
- [ ] **T7**: Add GraphQL query `availableEventsForPackage(productId, eventTypeId)` for wizard support

### 🔷 Domain Code Integration

- [ ] **T8**: Add `domain_code` field to `product.template` for event packages (inherit from company or explicit)
- [ ] **T9**: Filter `package_event_type_ids` by domain/company in package configuration
- [ ] **T10**: Ensure event filtering in wizard respects `domain_code` context

### 🔷 Feature Flag Hierarchy (use_products → use_event_packages)

> **Decision (2026-01-24):** `use_products` is an automated (computed) parent flag that enables when any product-related sub-feature is active. It has NO dependencies itself. `use_event_packages` is a sub-feature that requires `use_template_codes`, and when enabled, it auto-triggers `use_products`.

- [ ] **T11**: Make `website.use_products` a computed field (not manually togglable), auto-enabled when `use_event_packages=True` (or any future product sub-feature)
- [ ] **T12**: Add constraint: `use_event_packages` requires `use_template_codes=True` on the website
- [ ] **T13**: Update res_config_settings view: show `use_products` as readonly indicator, place `use_event_packages` below it (visual hierarchy)
- [ ] **T14**: Update event form: the "Products" button shows when `use_products=True` (now computed)

### 🔷 EventType Template System

- [ ] **T15**: Review/complete SharePoint sync fields usage (`ms_id`, `ms_synced`, `ms_version`)
- [ ] **T16**: Add EventType hierarchy view (template codes grouped under parent types)
- [ ] **T17**: Create EventType GraphQL resolver for template_parent relationship
- [ ] **T18**: Add `template_config` bitmask documentation

### 🔷 crearis_event_package Module Completion

- [ ] **T19**: Fix wizard to use `domain_code` for event filtering
- [ ] **T20**: Add `cid` (content ID) generation for package lines following crearis pattern
- [ ] **T21**: Implement `_compute_rectitle` style naming for packages
- [ ] **T22**: Add package-level `edition_code` to GraphQL
- [ ] **T23**: Create package line state machine (draft → confirmed → registered → done)

### 🔷 Sales & Registration Flow

- [ ] **T24**: Test wizard integration with sale order line creation
- [ ] **T25**: Implement automatic event registration creation from confirmed package lines
- [ ] **T26**: Add registration cancellation cascade to package lines
- [ ] **T27**: Create PDF report for package confirmation (listing all selected events)

### 🔷 Views & UI

- [ ] **T28**: Create EventType tree view with template_code grouping
- [ ] **T29**: Add Package configuration tab to product.template form
- [ ] **T30**: Create Package Event Lines tree view (filterable by state, order, customer)
- [ ] **T31**: Add dashboard widget for package sales overview

### 🔷 Security & Access

- [ ] **T32**: Review `event_type_company_rule` effectiveness
- [ ] **T33**: Add security rules for `product.package.event.line`
- [ ] **T34**: Ensure GraphQL respects company/domain isolation

### 🔷 Data & Migration

- [ ] **T35**: Create demo data for event packages
- [ ] **T36**: Document mapping: AGENDA Kurs → Odoo Product (event_package)
- [ ] **T37**: Plan import strategy from existing AGENDA course structures

### 🔷 Registration Extensions (NEW — from DASEi cross-check)

> These are generic registration fields/states that any organization could use. DASEi needs them, but they belong in the **crearis base module**, not DASEi-specific.
>
> **Implementation plan**: [2026-01-26-impl_plan_registration_states.md](./2026-01-26-impl_plan_registration_states.md)

- [ ] **T38**: Add `units` field to `event.registration` (integer, tracks teaching units / UE attended)
- [ ] **T39**: Add/verify `comments` field on `event.registration` (text, free-form notes)
- [ ] **T40**: Add custom registration states: `new`, `demo`, `no_show`, `partial` to selection field
  - Current states: `draft`, `open`, `done`, `cancel`
  - New states per B3 resolution: `new` (offer), `demo` (provisional), `no_show` (absent), `partial` (partial attendance)
  - **Cross-ref**: B3 blocking task, D33-D34 in DASEi plan
- [ ] **T41**: Update registration state workflow to support new states
- [ ] **T42**: Add `units` and new states to GraphQL `EventRegistration` type

### 🔷 CID/Slug Review (Late Round)

- [ ] **T43**: Review `blog.post` cid naming pattern
  - Current: `{domain}.blog-post__{id}`
  - Proposed: `{domain}.post{-templatecode}__{id}` (same pattern as event)
  - Check if blog posts need template codes
  - Consider: `{domain}.post__{id}` (no template code) vs `{domain}.post-{blog_code}__{id}`
  
- [ ] **T44**: Review `domain.user` cid — consider adding slug for public profile URLs
- [ ] **T45**: Review `res.partner` cid — consider adding slug for venue pages

---

## Dependencies & Grouping

```
                    ┌──────────────────────────────────────────────────────┐
                    │         Feature Flag Hierarchy (T11-T14)            │
                    │                                                      │
                    │   use_template_codes ──► use_event_packages         │
                    │                                 │                   │
                    │                                 ▼                   │
                    │                          use_products (auto)        │
                    │                          (computed parent flag)     │
                    └──────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
           ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
           │  Domain Codes   │ │  EventType      │ │    GraphQL      │
           │  T8, T9, T10    │ │  T15-T18        │ │    T1-T7        │
           └────────┬────────┘ └────────┬────────┘ └────────┬────────┘
                    │                   │                   │
                    └───────────────────┼───────────────────┘
                                        ▼
                               ┌─────────────────┐
                               │  Package Module │
                               │  T19-T23        │
                               └────────┬────────┘
                                        │
                               ┌────────▼────────┐
                               │  Sales Flow     │
                               │  T24-T27        │
                               └────────┬────────┘
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           ▼                            ▼                            ▼
  ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
  │    Views/UI     │         │    Security     │         │  Data/Migration │
  │    T28-T31      │         │    T32-T34      │         │    T35-T37      │
  └─────────────────┘         └─────────────────┘         └─────────────────┘
```

---

## Implementation Sequence

| Phase | Tasks | Priority | Est. Time |
|-------|-------|----------|----------|
| **Phase A1** | DB cleanup (stage dedup) | 🔴 Critical | 30min |
| **Phase A2** | T-CID-1 to T-CID-6: cid/slug architecture | 🔴 Critical | 2-3h |
| **Phase A3** | Registration states (B3/R1-R8) | 🔴 Critical | 2h |
| **Phase A4** | T-UI-1: Template code visualization | 🟡 Moderate | 1h |
| **Phase A5** | T11-T14: Feature flag hierarchy | 🟡 Moderate | 1-2h |
| **Phase C** | T1-T7, T42, G-CID-1: GraphQL extensions | 🟢 Later | 3-4h |
| **Phase D** | T8-T10, T15-T37: Domain codes, packages | 🟢 Later | Multi-day |

---

## Notes & Decisions

### Decision 1: Feature Flag Hierarchy (2026-01-24)

**Removed:** "Website Logic Mode System" (was T35-T41) — deemed overkill for current needs.

**Adopted:** Dependency-based feature flags:
- `use_products` → **computed/readonly**, no dependencies, auto-enabled when any product sub-feature is active
- `use_event_packages` → **manual toggle**, requires `use_template_codes`, and when enabled auto-triggers `use_products`

```
use_template_codes ──► use_event_packages ──► use_products (auto)
```

This is the maximum complexity level for the current implementation. Visual hierarchy in config view makes dependencies clear.

### Decision 2: use_sessions Postponed (2026-01-24)

`use_sessions` operates at **event type level** (not domain/company level) and is orthogonal to the current work. It will enable bulk operations on series of related standalone events — future scope.

### Decision 3: domain_code on event.event (2026-01-24)

The `domain_code` field was added on **2024-05-03** (commit `da5af93`). It's a `Many2one` to `website` and drives all `use_*` computed fields on events. GraphQL exposes it via `resolve_domain_code()` using `self.domain_id.domain_code`.

---

## Related Files

- [crearis_event_package/](../crearis_event_package/) - New module
- [crearis/models/event.py](../crearis/models/event.py) - EventType with template_code
- [graphql_theaterpedia/schemas/objects.py](../graphql_theaterpedia/schemas/objects.py) - GraphQL types
- [Architecture Doc](./2026-01-24-product_event_package_architecture.md)
