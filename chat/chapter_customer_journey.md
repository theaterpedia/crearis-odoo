# Chapter 3: Customer Journeys

**Stage**: task  
**Type**: chapter

---

## Abstract

Six distinct journeys define the user types and their progression through the system. Three customer journeys (Karo→onboarding, Ida→participant, Jolanda→transformation), plus issue-driver edge cases, service-worker backoffice, and instructor roles.

---

## Master Documents

| Title | Description | Stage | Notes | Version |
|-------|-------------|-------|-------|---------|
| [journey_karo_onboarding](journey_karo_onboarding.md) | Customer onboarding to A-module | task | FEB 5th example | |
| [journey_ida_participant](journey_ida_participant.md) | Becoming participant, consulting call | task | OCT 5th example | |
| [journey_jolanda_transformation](journey_jolanda_transformation.md) | D-module, discovering crearis potential | task | MAR 5th example | |
| [journey_issue_driver](journey_issue_driver.md) | Edge cases, problematic patterns | task | No persona name | |
| [journey_service_worker](journey_service_worker.md) | Backoffice: Eleanora, Rosalin, Hans, Zuzana | task | | |
| [journey_instructor](journey_instructor.md) | Instructor role | task | Phase 3 detail | |

---

## Journey Summary

| Journey | Persona | Stage | Key Moment | System State |
|---------|---------|-------|------------|--------------|
| 1. Onboarding | Karo, 22, Augsburg | Pre-A | INFO-Teaser decision | Tabs hidden, Service only |
| 2. Participant | Ida, 37, Nürnberg | Mid-A | Consulting call | Agenda + Service tabs |
| 3. Transformation | Jolanda, 35, Bad Tölz | D-module | Discovers domaincode | Full 3-tab UI |
| 4. Issue-driver | (unnamed) | Any | Repeated issues | Fallback patterns |
| 5. Service-worker | Eleanora et al | Staff | Daily backoffice | Default Odoo views |
| 6. Instructor | (tbd) | Staff | Teaching events | Phase 3 scope |

---

## Onboarding Progression (Karo→Ida→Jolanda)

```
PUBLIC WEBSITE → CHECKOUT STEPPER → ODOO CUSTOMER
     ↓
  Service tab only (hidden header)
     ↓
  Agenda tab appears (still pending, cancellable)
     ↓
  Agenda + Service tabs ("Einstiege")
     ↓
  Agenda + Curriculum + Service tabs ("Grundlagenbildung")
     ↓
VUEJS APP → Full participant features
```

---

## Source References

- [Journeys](2026-01-30-agenda_extended_journeys.md): All 6 journey definitions
- [Core](2026-01-30-agenda_extended_core.md) lines 80-100: 3 transitions flow
