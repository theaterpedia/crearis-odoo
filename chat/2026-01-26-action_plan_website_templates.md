# Action Plan: Website Templates Implementation

**Created**: 2026-01-26  
**Module**: Odoo Website Templates (dasei1, dasei2, dasei3)  
**Status**: 🟡 In Progress  
**Priority**: HIGH (Demo: 2026-01-27 11:00)

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
