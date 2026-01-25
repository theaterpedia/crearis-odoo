# Action Plan: DASEi Event Package Integration

**Date**: 2026-01-24  
**Updated**: 2026-01-26  
**Purpose**: Validate `crearis_event_package` flexibility with real-world DASEi organization  
**Blocking Decision**: D0 must be resolved before D1-D68  
**Sprint**: [2026-01-26_sprint_agenda_dasei.md](./2026-01-26_sprint_agenda_dasei.md)

---

## 🚨 Blocking Tasks (Resolve First)

> These tasks must be resolved before running the main action plan. Some require interactive confirmation.

- [x] **DB1**: **Move out event-stages definition** ✅ RESOLVED
  
  Move the definition of event-stages + event-registration-stages/states out of `agenda_dasei`.
  Use the values that are prepared by module `crearis`.
  
  **Cross-ref**: B2, B3 in crearis action plan
  
  **Status**: Stage definitions created in `crearis/data/event_stage_data.xml` with sysreg-compatible sequences.
  Registration states implementation planned in [impl_plan_registration_states.md](./2026-01-26-impl_plan_registration_states.md)
  
  **Remaining**: 
  - Update agenda_dasei module to remove any duplicate stage XML
  - Update sync_engine.py to map StatusLookupId → stage_id

- [ ] **DB2**: **event.user_id mapping**
  
  At the moment most of the events go to user: 2 "Administrator" but we need different values like: Hans Dönitz, Rosalin Hertrich.
  
  **Investigation needed**:
  - Field names on SharePoint
  - Mapping of SharePoint IDs / lookup-IDs to Odoo users
  
  **Action**: Review SharePoint fields, create user mapping

---

## 🔷 First Batch (Run First)

- [ ] **DA1**: **Menu entry "dasei" on menu "crearis"**
  
  Move all commands and views special for `agenda_dasei` to a submenu "dasei" under the main "crearis" menu.
  
  In the next iteration we will toggle visibility so that it only shows if company 'dasei' is active.
  
  **Action**: Refactor menu structure in `agenda_dasei`

---

## � Prod A — First Production Deployment

> Deploy early so the website-coding project (separate repo) can start working as soon as dasei data is available. Production is not actively used yet but will be soon.

- [ ] **DPa1**: **Extract product-templates A, B, C, D once** ⚠️ INTERACTIVE
  
  This task has to be done interactively during first production deployment:
  Once event-packages run smoothly, we extract product-templates once and set them up using `agenda_dasei:demo-data`.
  
  **Prerequisites**: Event packages working correctly
  
  **Action**: Manual extraction + demo data creation

---

## 🔷 Late Phase (Run with Remaining Tasks)

- [ ] **DL1**: **Non-Hauptstatus → Odoo tags mapping**
  
  SharePoint plan_planungsstatus has sub-statuses (non-Hauptstatus) that indicate data issues or special conditions.
  When StatusLookupId maps to a non-Hauptstatus entry, create/assign Odoo tags instead of changing stage.
  
  **Examples:**
  - ID 11 `(geplant - Konfigurationsfehler)` → tag "config-error"
  - ID 20 `X :verloschen:` → tag "verloschen" (deactivated on SP)
  
  **Implementation:** Add tag mapping logic to `_map_event_from_sp` in `crearis_agenda`

- [ ] **DL2**: **Verify StatusLookupId field name**
  
  Confirm the SharePoint field name for plan_veranstaltungen.status is `StatusLookupId`.
  SharePoint sometimes uses obscure/automated field names.
  
  **Status:** ✅ Verified - field is `fields/StatusLookupId`

---

## ✅ D0 — Blocking Decision: `use_event_packages` Scope (RESOLVED)

**Decision (2026-01-26): Option B — Company-primary + product filtering**

| Aspect | Implementation |
|--------|----------------|
| Primary toggle | Enable `use_event_packages` at company level |
| Product filtering | Each package has `domain_code` to control visibility per website |
| Website override | Keep website toggle for special cases |

**DASEi Implementation:**
- Enable `use_event_packages` once on DASEi company
- Package A: `domain_code = dasei1`
- Package B/C/D: `domain_code = dasei2`
- GraphQL filters events/packages by domain context

**Cross-ref**: See T0 in [crearis action plan](./2026-01-24-action_plan_event_package_integration.md) for detailed concerns about cross-domain display.

**Dependency**: T0 in crearis action plan ✅

---

## Phase 1: SharePoint List Infrastructure (D1–D8)

### D1 — Add `plan_kurse` GUID to JSONB config
- File: `agenda_dasei/data/res_company_data.xml` or config
- GUID: `{AA5F4A45-DB15-4588-BD12-4F38E99ACE0F}`
- Pattern: Use existing `ms_agenda_api` JSONB field on `res.company`

### D2 — Add `plan_veranstaltungsteilnehmer` GUID to JSONB config
- GUID: `{C9E05737-4C47-4E0F-A6B6-C6D6F3FBE88D}`
- This is the registration sync list

### D3 — Create `sync_plan_kurse.py` model
- Purpose: Sync intermediate course list from SharePoint
- Inherits base sync pattern from `crearis_agenda`

### D4 — Create `sync_plan_veranstaltungsteilnehmer.py` model
- Purpose: Sync registrations bidirectionally
- Critical for attendance tracking

### D5 — Register new sync models in `__init__.py`

### D6 — Add cron jobs for new sync models
- File: `agenda_dasei/data/ir_cron_data.xml`
- Frequency: TBD (hourly? daily?)

### D7 — Add access rights for new models
- File: `agenda_dasei/security/ir.model.access.csv`

### D8 — Test SharePoint connection for both lists
- Manual test before proceeding

---

## Phase 2: Course → Domaincode Mapping (D9–D18)

### D9 — Define DASEi course semantics
- Courses = organizational containers (e.g., "K26", "K27")
- Map to: `website` records (domain codes)
- **NOT** products — products are modules A/B/C/D

### D10 — Refactor `sync_product.py` to `sync_course.py`
- Current file incorrectly syncs courses as products
- Should sync courses as domain codes (websites)

### D11 — Map SharePoint course fields to website fields
| SharePoint | Odoo | Notes |
|------------|------|-------|
| Title | name | Course name |
| KursNr | short_name / code | "K26", "K27" |
| Jahr | ??? | Year attribute (where?) |
| Startdatum | ??? | Course start date |
| Enddatum | ??? | Course end date |

### D12 — Handle course year attribute
- Question: Is year a field on website or a computed value?
- DASEi pattern: Courses repeat annually (K26, K27, K28...)

### D13 — Handle course location
- DASEi locations: Witten, Kassel, (Online)
- Map to: `res.partner` addresses? `event.track.location`?

### D14 — Create course → domaincode sync logic
- Direction: SharePoint → Odoo
- Creates/updates website records

### D15 — Handle KursLookupId resolution
- This was the bug from 2025-01-23
- Modules reference courses via KursLookupId
- Need plan_kurse synced FIRST to resolve lookups

### D16 — Test: Sync courses from SharePoint
- Verify websites created correctly

### D17 — Test: Verify domain_code shows on events
- Events should be assignable to synced courses

### D18 — Document course sync in README

---

## Phase 3: Module → Product Mapping (D19–D32)

### D19 — Define DASEi module semantics
- Modules = purchasable items (A, B, C, D, Profile)
- Each module is an `event.event.package` (product)
- Progression: A → B → C → D (sequential, multi-year)

### D20 — Define product attribute: `course_type`
- Values: `block`, `day`, `profile`
- Block = multi-day intensive (A, B, C, D)
- Day = single-day event
- Profile = special/assessment module

### D21 — Create product.attribute for `course_type`
- Use Odoo native product attributes
- Or: Custom field on product template?

### D22 — Define product attribute: `year`
- Which year in the progression
- A=1, B=2, C=3, D=4

### D23 — Define product attribute: `location`
- Witten, Kassel, Online
- Multi-value possible?

### D24 — Map SharePoint module fields to product fields
| SharePoint | Odoo | Notes |
|------------|------|-------|
| Title | product.name | Module name |
| ModulNr | product.default_code | "A", "B", "C", "D" |
| KursLookupId | ??? | Links to course (domain_code) |
| Preis | product.list_price | Price |
| MS Teams Link | ??? | Product attribute or event field? |

### D25 — Handle MS Teams link as product attribute
- Per user feedback: "MS Teams config = Product attribute"
- Or: Field on event.event.package?

### D26 — Create module → product sync logic
- Direction: SharePoint → Odoo
- Creates `product.product` records

### D27 — Link products to domain_code (course)
- Via KursLookupId → website lookup
- Field: `product.product.domain_code_id`? Or via package?

### D28 — Handle module progression logic
- A before B before C before D
- Enforce via prerequisites? Or just informational?

### D29 — Create/update `event.event.package` records
- Package = bridge between product and event
- Links product to specific event occurrence

### D30 — Test: Sync modules from SharePoint
- Verify products created with correct attributes

### D31 — Test: Create event package from product
- Manual test: product → package → event

### D32 — Document module/product sync in README

---

## Phase 4: Registration Sync (D33–D48)

### D33 — Map registration status codes ✅ MAPPED

**Full mapping defined in:** [2026-01-26-impl_plan_registration_states.md](./2026-01-26-impl_plan_registration_states.md)

| SP ID | SP Title | Odoo State | Sysreg |
|-------|----------|------------|--------|
| 1 | (angemeldet) | draft | 64 |
| 3 | : vollständig | done | 4096 |
| 4 | : teilweise | partial | 20480 |
| 5 | (vorbehaltlich) | demo | 8 |
| 6 | : abwesend | no_show | 16384 |
| 8 | (storniert) | cancel | 12288 |
| 12 | __Angebot | new | 1 |
| 13 | : angemeldet | open | 512 |

**Skip IDs:** 9, 10, 11, 14, 15, 16 (internal/unused)

### D34 — Add custom registration states to crearis module
- **Status**: Planned in [impl_plan_registration_states.md](./2026-01-26-impl_plan_registration_states.md)
- **Module**: CREARIS (not DASEi)
- **New states**: `new`, `demo`, `no_show`, `partial`
- **Cross-ref**: B3 in crearis action plan ✅

### D35 — Add `units` field to `event.registration` (crearis)
- **Note**: Base field belongs in CREARIS — see **T38** in crearis action plan
- DASEi maps: `UE` (Unterrichtseinheiten) → `units`
- **Implementation**: Part of [impl_plan_registration_states.md](./2026-01-26-impl_plan_registration_states.md) task R5

### D36 — Add/verify `comments` field on registration (crearis)
- **Note**: Base field belongs in CREARIS — see **T39** in crearis action plan  
- DASEi maps: `Bemerkungen` → `comments`
- **Implementation**: Part of [impl_plan_registration_states.md](./2026-01-26-impl_plan_registration_states.md) task R6

### D37 — Map SharePoint registration fields to Odoo
| SharePoint | Odoo | Notes |
|------------|------|-------|
| TeilnehmerLookupId | partner_id | Via contact sync |
| VeranstaltungLookupId | event_id | Via event sync |
| Status | state | See D33 mapping |
| UE | units | Teaching units attended |
| Bemerkungen | comment | Free text notes |
| Datum | date_open | Registration date |

### D38 — Create registration sync: SharePoint → Odoo

> ⚠️ **STOP**: Before implementing this task, provide a detailed explanation of the proposed sync architecture and wait for user confirmation.

- Direction: Inbound
- Creates `event.registration` records
- Handles status mapping

### D39 — Create registration sync: Odoo → SharePoint
- Direction: Outbound
- Updates SharePoint when Odoo registration changes
- Critical for: confirmations, cancellations

### D40 — Handle TeilnehmerLookupId resolution
- Requires contacts synced first
- Lookup partner by SharePoint ID

### D41 — Handle VeranstaltungLookupId resolution
- Requires events synced first
- Lookup event by SharePoint ID

### D42 — Implement sync conflict resolution
- What if both sides changed?
- Strategy: Last-write-wins? Or manual review?

### D43 — Handle partial sync (delta)
- Don't re-sync unchanged records
- Track `sync_date` and `modified_date`

### D44 — Test: Registration created in SharePoint → Odoo
- Verify state mapping correct

### D45 — Test: Registration confirmed in Odoo → SharePoint
- Status should update to 13

### D46 — Test: Attendance marked in Odoo → SharePoint
- Status 3 (attended) or 4 (partial)
- Units field populated

### D47 — Test: Cancellation sync both directions

### D48 — Document registration sync in README

---

## Phase 5: Loyalty/Discount Program (D49–D54)

### D49 — Use Odoo native loyalty program for discounts
- Per user feedback: "Loyalty discount = Odoo native program"
- Module: `loyalty` or `sale_loyalty`

### D50 — Define DASEi discount rules
- Early bird discount?
- Multi-module discount?
- Alumni discount?

### D51 — Configure loyalty program for DASEi
- Points or rules-based?
- Apply at checkout

### D52 — Link loyalty to course registration
- Automatic discount when re-enrolling?

### D53 — Test: Discount applied correctly

### D54 — Document loyalty program setup

---

## Phase 6: Package Bundle Logic (D55–D60)

### D55 — Define package bundles
- Example: "Full Course K26" = A + B + C + D
- Discount for bundle vs individual

### D56 — Create bundle products
- Product type: bundle/kit
- Components: individual module products

### D57 — Handle bundle pricing
- Sum of parts vs discounted total

### D58 — Handle bundle registration
- Single registration creates child registrations?
- Or: Single registration for bundle product?

### D59 — Test: Bundle purchase flow

### D60 — Document bundle logic

---

## Phase 7: Testing & Validation (D61–D68)

### D61 — End-to-end test: Course sync
- SharePoint → website (domain_code)

### D62 — End-to-end test: Module sync
- SharePoint → product.product

### D63 — End-to-end test: Event creation with package
- Event + domain_code + package

### D64 — End-to-end test: Registration flow
- SharePoint → Odoo → confirmation → SharePoint

### D65 — End-to-end test: Attendance tracking
- Mark attended in Odoo → SharePoint status 3

### D66 — Performance test: Bulk sync
- 1000+ registrations

### D67 — Error handling test: Invalid data
- Missing lookups, bad status codes

### D68 — Final documentation review

---

## Cross-Reference: Tasks for CREARIS Module

The following tasks from this plan should be implemented in the **crearis** base module, not DASEi-specific:

| DASEi Task | Crearis Equivalent | Description |
|------------|-------------------|-------------|
| D34 | T-NEW-1 | Add `no_show`, `partial` states to registration |
| D35 | T-NEW-2 | Add `units` field to `event.registration` |
| D36 | T-NEW-3 | Add/verify `comments` field on registration |

These are generic event registration extensions that any organization could use.

---

## Dependency Graph

```
D0 (decision)
 └── D1-D8 (SharePoint infrastructure)
      ├── D9-D18 (Course sync) ──► D15 depends on D3
      └── D19-D32 (Module sync) ──► D27 depends on D14
           └── D33-D48 (Registration sync) ──► D40,D41 depend on D14,D26
                └── D49-D60 (Loyalty & Bundles)
                     └── D61-D68 (Testing)
```

---

## Notes

- **Previous Bug (2025-01-23)**: KursLookupId mismatch was caused by missing `plan_kurse` sync. D3 and D15 address this.
- **JSONB Pattern**: All SharePoint list GUIDs stored in `ms_agenda_api` field on `res.company`
- **Sync Direction**: Most syncs are SharePoint → Odoo, except registration status which is bidirectional
