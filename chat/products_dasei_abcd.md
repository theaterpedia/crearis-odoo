# DASEi Products A,B,C,D

**Type**: master  
**Stage**: task

---

## Overview

DASEi's "Grundlagen Theaterpädagogik (BuT)" is a 2-year program structured as 4 modules (A,B,C,D). Module A can be taken standalone as "Einstiege ins Theaterspiel".

---

## Module Structure

| Module | Name | Units | UE | Focus |
|--------|------|-------|-----|-------|
| **A** | Einstiege ins Theaterspiel | A0-A5 (6 units) | 120 | Elementare & Szenische Animation |
| **B** | Szenische Themenarbeit | B1-B7 (7 units) | 154 | Theatre pedagogy "off stage" |
| **C** | Pädagogische Regie | C0-C7 (8 units) | 174 | Directing with non-actors |
| **D** | Kolloquium & Praxis | D1-D4 (4 units) | 150 | Practice project, examination |
| | **Total** | | **600 UE** | |

---

## Module A: Einstiege ins Theaterspiel

### Event Types (Shortcodes)

| Code | Title | Description | Format |
|------|-------|-------------|--------|
| **AA** | Online-Teaser | Info session, free | Online 2h |
| **A0** | Basistag | Trial day, orientation | 1 day + online |
| **A1** | Am Anfang war der Kreis | Circle animation intro | 1 day + online |
| **A2** | Die Bühne kommt von selbst | Two-circle model | Weekend + online |
| **A3** | Wege entstehen beim Gehen | Walk animation, impro | 1 day + online |
| **A4** | Szenische Lesung | Scenic reading, storytelling | 1 day + online |
| **A5** | Figurenkarussell | Character carousel, participation | 1 day + online |

### Course Variants

| Code | Location | Format | Duration |
|------|----------|--------|----------|
| M18E | München | Tageskursverlauf (day course) | März-Dez 2026 |
| M18B | Burgstallmühle/München | Blockseminarverlauf (block) | Mai-Dez 2026 |
| N18E | Nürnberg | Tageskursverlauf | März-Dez 2026 |
| N18B | Burgstallmühle/Nürnberg | Blockseminarverlauf | — |

---

## Pricing Model

### Einstiege ins Theaterspiel (Module A)

| Item | Price |
|------|-------|
| Anmeldegebühr (incl. Basistag) | € 80,00 |
| 5 Kursraten (A1-A5) | 5 × € 220,00 = € 1.100,00 |
| **Total Module A** | **€ 1.180,00** |

### Full Grundlagenbildung (A+B+C+D)

| Phase | Units | Rates | Total |
|-------|-------|-------|-------|
| Module A | A0-A5 | 5 × € 220 | € 1.100 |
| Module B | B1-B7 | 7 × € 220 | € 1.540 |
| Module C | C0-C7 | 8 × € 220 | € 1.760 |
| Module D | D1-D4 | 4 × € 220 | € 880 |
| | | **24 rates** | **€ 5.280** |
| + Anmeldegebühr | | | € 80 |
| **Total** | | | **€ 5.360** |

### Payment Schedule

- Basistag + Module A: Separate contract ("Einstiege ins Theaterspiel")
- From 1.1.2027: Monthly standing order € 220,00 until 1.7.2028
- Cancellation: € 330 until 1.4.2027, then € 660

---

## Customer Journey Entry Points

1. **INFO-Teaser** (AA) — Free online info session
2. **Basistag** (A0) — Paid trial day (€80 with registration)
3. **10-day window** — Can withdraw after Basistag within 10 days
4. **Counseling session** — Around unit 3, discuss continuation
5. **Module A completion** — Decision point for B+C+D

---

## Website Structure

### Product Pages

| URL | Content |
|-----|---------|
| `/ausbildung-theaterpaedagogik/kurs_einstiege_ins_theaterspiel` | Module A product view with event slider |
| `/ausbildung-theaterpaedagogik/grundlagenbildung` | Full A+B+C+D overview with pricing |
| `/details?src=/agenda/einstiege-ins-theaterspiel-m18e` | Checkout stepper for specific course |

### Navigation

```
Ausbildung Theaterpädagogik
├── Überblick
├── Kurs 2026: Einstiege ins Theaterspiel (Module A)
└── Kurs 2026-2028: Grundlagen (A+B+C+D)
```

---

## Product Configuration in Odoo

### product.template fields needed

| Field | Example | Purpose |
|-------|---------|---------|
| `default_code` | m18e | Course code (lowercase) |
| `course_type` | block, day | Block vs Tageskurs |
| `course_program` | M, N | Location code |
| `course_year` | 2026 | Start year |
| `course_event_ids` | JSON | Linked events with order |

### Example course_event_ids

```json
{
  "a0": {"event_id": 1234, "order": 0},
  "a1": {"event_id": 1235, "order": 1},
  "a2": {"event_id": 1236, "order": 2},
  "a3": {"event_id": 1237, "order": 3},
  "a4": {"event_id": 1238, "order": 4},
  "a5": {"event_id": 1239, "order": 5}
}
```

---

## Related Documents

- [onboarding_checkout_stepper](onboarding_checkout_stepper.md) — How products become YAML
- [onboarding_three_transitions](onboarding_three_transitions.md) — Customer journey stages
- [workflow_email_templates](workflow_email_templates.md) — Contract email with timetable
