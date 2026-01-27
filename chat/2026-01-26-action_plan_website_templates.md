# Action Plan: Website Templates Implementation

**Created**: 2026-01-26  
**Updated**: 2026-01-27  
**Module**: Odoo Website Templates (dasei1, dasei2, dasei3)  
**Status**: 🟡 In Progress  
**Priority**: HIGH (Demo: 2026-01-27 11:00)

---

## Deep Understanding: Product Templates ↔ Event Types ↔ Domain Codes

### What dasei1, dasei2, dasei3 Represent

These are **progression levels** in the DASEi training system, mapped to Odoo websites (domain codes):

| Domain Code | Level | Description | Who Sees It |
|-------------|-------|-------------|-------------|
| `dasei0` | Quick Entry | Pre-registration, prospects | Public landing page |
| `dasei1` | Einstiege | Entry modules (ME, NE) | New participants |
| `dasei2` | Grundstufe | Core modules (M?/N? except ME/NE) | Active trainees |
| `dasei3` | Aufbaustufe | Advanced modules (ZR, ZT profiles) | Advanced trainees |
| `dasei` | Verein | Association members (status 8,9,10) | Full member portal |

**Key Insight**: A participant's `dasei_domaincode` determines their **highest access level**. Someone at `dasei2` can see `dasei1` content too, but not `dasei3`.

### The Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 1: PRODUCT TEMPLATES (What you can buy)                                       │
│  ═══════════════════════════════════════════════                                    │
│                                                                                      │
│  product.template: "Grundkurs M18 Tageskurs"                                        │
│      detailed_type: 'event_package'                                                 │
│      domain_code: website('dasei2')  ←── Controls visibility on websites            │
│      package_event_type_ids: [A, B, C, D, E, F]  ←── Which event types included     │
│      package_edition_code: "M18"                                                    │
│      package_date_start/end: 2026-10 to 2028-12                                     │
│                                                                                      │
│  product.template: "Aufbaustufe ZR 2026-2028"                                       │
│      detailed_type: 'event_package'                                                 │
│      domain_code: website('dasei3')  ←── Only visible to dasei3 level users         │
│      package_event_type_ids: [G, H, J, L]                                           │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ Package defines which event_types
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 2: EVENT TYPES (Template codes = curriculum structure)                        │
│  ════════════════════════════════════════════════════════════                       │
│                                                                                      │
│  event.type records with is_template_code=True:                                     │
│                                                                                      │
│  GRUNDSTUFE (Required for M/N programs):                                            │
│  ├── A1 "Am Anfang war der Kreis"       → Module A (Grundlagen Spielen)            │
│  ├── A2 "Die Bühne kommt von selbst"    → Module A                                 │
│  ├── B1 "Das fiktive Situationsbildverfahren" → Module B (Grundlagen Anleiten)     │
│  ├── B2 "Klischees, Situationen"        → Module B                                 │
│  ├── C1 "Initiierung"                   → Module C (Theaterprojekt)                │
│  ├── D1 "Konzeption"                    → Module D (Konzeption)                    │
│  └── ...                                                                            │
│                                                                                      │
│  AUFBAUSTUFE (Required for ZR/ZT profiles):                                         │
│  ├── G1, G2, G3...                      → Module G (Vertiefung)                    │
│  ├── H1, H2...                          → Module H (Bewegungstheater)              │
│  ├── J1, J2...                          → Module J (Abenteuertheater)              │
│  └── L1, L2...                          → Module L (Zusatzqualifikation)           │
│                                                                                      │
│  First letter = Module Group (A, B, C, D for Grund / G, H, J, L for Aufbau)         │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ Events instantiate event_types
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 3: EVENTS (Actual occurrences with dates)                                     │
│  ═══════════════════════════════════════════════                                    │
│                                                                                      │
│  event.event: "A1 München 2026"                                                     │
│      event_type_id: A1                                                              │
│      domain_code: website('dasei1')  ←── Entry-level event                          │
│      date_begin: 2026-10-15                                                         │
│                                                                                      │
│  event.event: "B1 München JAN 2027"                                                 │
│      event_type_id: B1                                                              │
│      domain_code: website('dasei2')  ←── Grundstufe event                           │
│      date_begin: 2027-01-20                                                         │
│                                                                                      │
│  event.event: "G1 Witten 2027"                                                      │
│      event_type_id: G1                                                              │
│      domain_code: website('dasei3')  ←── Aufbaustufe event                          │
│      date_begin: 2027-03-10                                                         │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### The Checkout Flow (Event Packages)

```
Customer buys "Grundkurs M18 Tageskurs" (product.template)
       │
       ▼
Wizard opens: "Select Your Events"
       │
       ├── For Module A: Shows events where event_type.name starts with 'A'
       │   └── Customer selects: "A1 München 2026"
       │
       ├── For Module B: Shows events where event_type.name starts with 'B'
       │   └── Customer selects: "B1 München JAN 2027"
       │
       └── ... (repeats for C, D, E, F)
       
       ▼
product.package.event.line records created:
       │
       ├── sale_order_line_id → the SO line
       ├── event_type_id → A1
       ├── event_id → "A1 München 2026"
       ├── registration_id → created on confirmation
       └── state → draft → confirmed → registered → done
```

### Domain Code Filtering Logic

**On Products** (`product.template.domain_code`):
- Determines which website can display/sell the package
- `dasei1` products show on dasei1 website
- `dasei2` products show on dasei2 AND dasei1 (lower levels inherit)

**On Events** (`event.event.domain_code`):
- Determines which website can display the event
- Used by wizard to filter available events for package selection

**On Partners** (`res.partner.dasei_domaincode`):
- Computed from highest course level completed
- Determines user's access level
- ZR/ZT completed → `dasei3`
- M?/N? (not ME/NE) completed → `dasei2`
- ME/NE completed → `dasei1`

### Module Completion Tracking

```python
# In dasei.course.participation
def _compute_completed_modules(self):
    """
    1. Get all confirmed event.registration for partner
    2. Extract event_type.name first letter (A, B, C...)
    3. Filter to valid MODULE_GROUPS
    4. Store as comma-separated: "A,B,C"
    """
```

This feeds into:
- Certificate generation (all required modules = certificate)
- Access level computation (completed modules → dasei_domaincode)
- Progress dashboards

---

## Context

Rapid prototyping of customer portal UX using Odoo website templates. This is **intentionally specialized** for DASEi and isolated from core modules. Key principle: specialized UI lives in website templates, not in core models.

**Architecture Guard:**
```
CORE (Generic, Reusable)          │  SPECIALIZED (DASEi, Disposable)
──────────────────────────────────┼───────────────────────────────────
crearis                           │  agenda_dasei
crearis_event_package             │  website templates (dasei1/2/3)
crearis_agenda                    │
graphql_theaterpedia              │
```

---

## Prerequisites

| ID | Task | Status | Blocking |
|----|------|--------|----------|
| W-PRE-1 | User mapping for events (responsible_id) | ⬜ TODO | Yes |
| W-PRE-2 | Verify SP sync fields (headline, overline, teasertext) | ⬜ TODO | Yes |
| W-PRE-3 | Pre-production deployment | ⬜ TODO | Yes |
| W-PRE-4 | Debug sync with live SP data | ⬜ TODO | Yes |

---

## Implementation Tasks

### W1: Data Layer Completion

| ID | Task | Est. | Status |
|----|------|------|--------|
| W1.1 | Map SP Person column → event.user_id | 1h | ✅ Done |
| W1.2 | Verify headline/overline/teasertext sync | 30m | ⬜ TODO |
| W1.3 | Test sync with real DASEi data | 30m | ⬜ TODO |

### W2: Pre-Production Deploy

| ID | Task | Est. | Status |
|----|------|------|--------|
| W2.1 | Deploy modules to pre-prod | 1h | ⬜ TODO |
| W2.2 | Run sync, debug issues | 2h | ⬜ TODO |
| W2.3 | Verify dasei1/dasei2/dasei3 websites exist | 30m | ⬜ TODO |

### W3: Event Card Templates

| ID | Task | Est. | Status |
|----|------|------|--------|
| W3.1 | Adapt event card: headline + overline layout | 1h | ⬜ TODO |
| W3.2 | Minimal MD rendering (bold, links, line breaks) | 1h | ⬜ TODO |
| W3.3 | Template code badge display | 30m | ⬜ TODO |
| W3.4 | Responsive styling | 30m | ⬜ TODO |

### W4: Event Detail Page

| ID | Task | Est. | Status |
|----|------|------|--------|
| W4.1 | Header with overline + headline | 1h | ⬜ TODO |
| W4.2 | Teasertext/description rendering | 30m | ⬜ TODO |
| W4.3 | Speaker/responsible display | 30m | ⬜ TODO |
| W4.4 | Registration CTA (package vs individual) | 1h | ⬜ TODO |

### W5: Customer Portal (Stretch)

| ID | Task | Est. | Status |
|----|------|------|--------|
| W5.1 | My registrations list | 2h | ⬜ TODO |
| W5.2 | Registration status display | 1h | ⬜ TODO |
| W5.3 | Package event selection UI | 2h | ⬜ TODO |

---

## Reference: Vue.js Components to Port

> Examples from theaterpedia Vue.js project to reference for Odoo templates

| Vue Component | Odoo Target | Notes |
|---------------|-------------|-------|
| EventCard.vue | website_event card snippet | headline + overline layout |
| EventHeader.vue | event detail header | MD rendering for teasertext |
| MarkdownLight.vue | qweb helper | bold, links, line breaks only |

---

## Technical Notes

### Minimal Markdown Rendering

For teasertext, we need lightweight MD support:
- `**bold**` → `<strong>`
- `[text](url)` → `<a href>`
- `\n` → `<br/>`

Can be done with simple regex in QWeb or Python helper.

### Template Code Display

Show template code as badge:
```xml
<span t-if="event.event_type_id.template_code" 
      class="badge badge-secondary">
    <t t-esc="event.event_type_id.template_code"/>
</span>
```

### Package-Only Events

Hide "Register" button, show "Part of package" message:
```xml
<t t-if="event.package_only">
    <div class="alert alert-info">
        This event is only available as part of a package.
    </div>
</t>
```

---

## Demo Checklist (2026-01-27 11:00)

- [ ] Events synced from SharePoint with correct data
- [ ] Event list page shows cards with headline + overline
- [ ] Event detail page displays full info
- [ ] Template codes visible
- [ ] At least one website (dasei1) functional

---

## Dependencies

| Module | Required For |
|--------|--------------|
| `crearis` | domain_code, feature flags |
| `crearis_agenda` | SharePoint sync |
| `agenda_dasei` | DASEi-specific SP lists |
| `website_event` | Base event website |

---

## Related Documents

- [2026-01-24-action_plan_dasei_event_packages.md](./2026-01-24-action_plan_dasei_event_packages.md) — SharePoint sync
- [dev_docs_crearis_introduction.md](./dev_docs_crearis_introduction.md) — Module architecture
- Vue.js project: `theaterpedia-web/src/components/events/`

---

## Future Tasks (Backlog)

> Captured from sprint discussions, not blocking demo

| ID | Task | Priority | Notes |
|----|------|----------|-------|
| F1 | **Meldefrist** sync | HIGH | Registration confirmation deadline - penalty after this date. Map to `event.registration` deadline field |
| F2 | **Nebenreferent** sync | LOW | Secondary speaker (2% of events). Map to second user field or speaker list |
| F3 | **SecondaryCode** support | MEDIUM | Append second Event-Template to root event |
| F4 | **Untertermin** (Sessions) | MEDIUM | For sessions/tracks logic - links to event_session module |
| F5 | MS Teams workflow fields | LOW | Orga_Info, Orga_Team, LinkChannel, UrlChannel - prepared but not activated |
| F6 | Optional event fields | LOW | MinTeilnehmer, MaxTeilnehmer, Honorar, Raumkosten, SonstigeKosten, Kursraten |

---

## Pre-Demo Task: Meldefrist Imagery (2026-01-27 09:00-10:00)

> **Purpose:** Prepare 3 alternative implementation options for team presentation input

**Context:** Meldefrist is the next major step on customer journey timeline after package_events checkout.

**What is Meldefrist?**
- Registration confirmation deadline per event
- Customers must change status from "confirmed" → "really confirmed" before this date
- Opting out after Meldefrist incurs a penalty

**Insights to capture (ongoing):**
- [ ] Current SP field: `Meldefrist` (Date field on plan_veranstaltungen)
- [ ] How it relates to registration states (draft → confirmed → attending)
- [ ] Penalty logic (flat fee? percentage? configurable?)
- [ ] Email notification workflow (reminder before deadline)
- [ ] UI touchpoints (customer portal, backoffice, event detail page)

**Deliverable for 09:00-10:00:**
3 alternative options with visual mockups/diagrams showing:
1. Data model changes
2. Customer journey touchpoints
3. Backoffice workflow
4. Integration with existing registration states
