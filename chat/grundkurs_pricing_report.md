# Grundkurs Theaterpädagogik - Overview Report

> **Document Type:** Technical Overview & Business Logic  
> **Version:** 2.0  
> **Date:** 2025-12-21  
> **Related Reports:**  
> - [dasei_team_report_de.md](dasei_team_report_de.md) - German team documentation  
> - [crearis_agenda_code_implementation.md](crearis_agenda_code_implementation.md) - Code implementation  
> - [imaginations_grundlagenkurs.md](imaginations_grundlagenkurs.md) - UI/UX scenarios

---

## 1. Course Overview

### Master Course
**M18 - Grundkurs Theaterpädagogik 2026-2028, München**

| Sequence | Shortcode | Module Title | Period | Sessions | Pricing |
|----------|-----------|--------------|--------|----------|---------|
| 1 | M18E | Einstiege in's Theaterspiel 2026, München (Modul A) | 2026 | A0-A5 | 5 Raten |
| 2 | M18B | Szenische Themenarbeit JAN-MAI 2027, München (Modul B) | JAN-MAI 2027 | B1-B6 | 6-8 Raten |
| 3 | M18C | Pädagogische Regie JUN-DEZ 2027, München (Modul C) | JUN-DEZ 2027 | C1-C6 | 6-8 Raten |
| 4 | M18D | Kolloquium, Zielgruppenpraxis, Projekt JAN-JUL 2028 (Modul D) | JAN-JUL 2028 | D1-D5 | 5 Raten |

### Session Codes (from SharePoint plan_veranstaltungscodes)

| Module | Sessions | Description |
|--------|----------|-------------|
| **Modul A** | A0, A1, A2, A3, A4, A5 | A0=Basistag, A1=Kreisanimation, A2=Zwei-Kreise, A3=Raumlauf, A4=Szenische Lesung, A5=Figurenkarussell |
| **Modul B** | B1, B2, B3, B4, B5, B6, BX, B/ | Szenische Themenarbeit sessions |
| **Modul C** | C1, C2, C3, C4, C5, C6, CX, C/ | Pädagogische Regie sessions |
| **Modul D** | D1, D2, D3, D4, D5 | Kolloquium & Projekt sessions |

### Pricing Base
- **1 Rate = EUR 220,00**
- **Anmeldegebühr (Booking Fee) = EUR 80,00** (non-refundable)

### Price Calculation

| Scenario | Anmeldung | Modul A | Modul B | Modul C | Modul D | Total Raten | Total EUR |
|----------|-----------|---------|---------|---------|---------|-------------|-----------|
| **Komplett (B-D zusammen)** | 80 | 5 | 6 | 6 | 5 | **22** | **EUR 4.920,00** |
| **Einzeln (Module getrennt)** | 80 | 5 | 8 | 8 | 5 | **26** | **EUR 5.800,00** |
| **Nur Modul A** | 80 | 5 | - | - | - | **5** | **EUR 1.180,00** |
| **Stornierung (nach 1. Session)** | 80 | 1 | - | - | - | **1** | **EUR 300,00** |
| **Savings (Komplett vs Einzeln)** | - | - | 2 | 2 | - | **4** | **EUR 880,00** |

---

## 2. Two-Checkout Business Model

### The Customer Journey

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         CUSTOMER JOURNEY TIMELINE                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  PHASE 1: EINSTIEG (Modul A only) ─ DEFAULT ENTRY POINT                         │
│  ═══════════════════════════════════════════════════════                        │
│                                                                                  │
│  [CHECKOUT 1] ──► First Session (A0/A1/A4) ──► 10-day Decision ──► Continue     │
│       │                    │                         │                 │        │
│       │                    │                         ▼                 ▼        │
│       ▼                    │                    [CANCEL]         Sessions       │
│  EUR 80 Anmeldung          │                   Only 1 Rate       A0-A5          │
│  + Payment Plan            │                   = EUR 220         running        │
│  (2 installments)          │                   + EUR 80                         │
│                            │                   = EUR 300 total                  │
│                            │                                                    │
│  ─────────────────────────────────────────────────────────────────────────────  │
│                                                                                  │
│  PHASE 2: QUALIFICATION (during Modul A, 4-6 months in)                         │
│  ══════════════════════════════════════════════════════                         │
│                                                                                  │
│  Requirements for Checkout 2:                                                   │
│  ✓ Minimum 2 sessions completed (attendance marked as 'done')                   │
│  ✓ Consultation completed (30 min online, tracked in partner record)            │
│  ✓ Typically 4-6 months into Modul A                                            │
│                                                                                  │
│  ─────────────────────────────────────────────────────────────────────────────  │
│                                                                                  │
│  PHASE 3: WEITERBILDUNG (Modules B-D) ─ ADD-ON CHECKOUT                         │
│  ══════════════════════════════════════════════════════                         │
│                                                                                  │
│  [CHECKOUT 2] ──► "Jetzt zur Weiterbildung aufstufen (Module B-D)"              │
│       │                                                                         │
│       ▼                                                                         │
│  Monthly Payments (from Jan 1, 2027)                                            │
│  - Komplett: 17 Raten (6+6+5) = EUR 3.740                                       │
│  - Einzeln:  21 Raten (8+8+5) = EUR 4.620                                       │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Checkout 1: Modul A "Einstiege in's Theaterspiel"

| Item | Amount | Notes |
|------|--------|-------|
| Anmeldegebühr | EUR 80,00 | Non-refundable, immediate payment |
| Modul A (5 Raten) | EUR 1.100,00 | Split into 2 installments |
| **Total Checkout 1** | **EUR 1.180,00** | |

**Payment Schedule Modul A (Year 1 - 2 One-Time Payments):**
- Payment 1: EUR 80 + ~EUR 550 (upon booking)
- Payment 2: ~EUR 550 (mid-course, calculated individually per customer)

**Cancellation Policy:**
- After first session (A0, A1, or A4): 10 days to decide
- If cancelled: Only 1 Rate (EUR 220) + Anmeldegebühr (EUR 80) = **EUR 300 total**
- Entry sessions (triggers 10-day rule): A0 (Basistag), A1 (Kreisanimation), A4 (Szenische Lesung)

### Checkout 2: Modules B-D "Weiterbildung"

| Booking Type | Modul B | Modul C | Modul D | Total | EUR |
|--------------|---------|---------|---------|-------|-----|
| **Komplett (B+C+D together)** | 6 Raten | 6 Raten | 5 Raten | 17 | EUR 3.740,00 |
| **Einzeln (separate bookings)** | 8 Raten | 8 Raten | 5 Raten | 21 | EUR 4.620,00 |

**Payment Schedule Modules B-D (from Jan 1, 2027 - Monthly):**
- Monthly payments of EUR 220,00 each
- Tracked in Odoo with payment schedule per customer
- Duration: 17 months (Komplett) or varies per module (Einzeln)

---

## 3. Odoo Data Model

### 3.1 Product Structure

```
product.category: "Theaterpädagogik Ausbildungen"
    │
    └── product.category: "Grundkurs Module"

product.product: "Anmeldegebühr Grundkurs"
    detailed_type: 'service'
    list_price: 80.00
    default_code: "ANMELD-GK"

product.product: "M18E" (detailed_type='event')
    name: "Einstiege in's Theaterspiel 2026, München (Modul A)"
    list_price: 1100.00  (5 Raten - fixed, no discount applies)
    default_code: "M18E"

product.product: "M18B" (detailed_type='event')
    name: "Szenische Themenarbeit JAN-MAI 2027, München (Modul B)"
    list_price: 1760.00  (8 Raten - full price, discount via loyalty)
    default_code: "M18B"

product.product: "M18C" (detailed_type='event')
    name: "Pädagogische Regie JUN-DEZ 2027, München (Modul C)"
    list_price: 1760.00  (8 Raten - full price, discount via loyalty)
    default_code: "M18C"

product.product: "M18D" (detailed_type='event')
    name: "Kolloquium, Zielgruppenpraxis, Projekt JAN-JUL 2028 (Modul D)"
    list_price: 1100.00  (5 Raten - fixed, no discount applies)
    default_code: "M18D"
```

### 3.2 Event Structure with Sessions

```
event.type: "Grundkurs Modul A" (synced from SharePoint via crearis_agenda)
    use_sessions: True
    ms_shortcode: "A"

event.event: "M18E - Einstiege in's Theaterspiel 2026"
    event_type_id: "Grundkurs Modul A"
    use_sessions: True
    │
    ├── event.session: "A0 - Basistag Theaterpädagogik"
    │       event_type_id.ms_shortcode: "A0"
    │       date_begin: 2026-10-31
    │       is_entry_session: True  # Triggers 10-day cancellation rule
    │
    ├── event.session: "A1 - Einführung in die Kreisanimation"
    │       event_type_id.ms_shortcode: "A1"
    │       date_begin: 2026-10-12
    │       is_entry_session: True
    │
    ├── event.session: "A2 - Arbeiten mit dem Zwei-Kreise-Modell"
    │       event_type_id.ms_shortcode: "A2"
    │       date_begin: 2026-10-26
    │
    ├── event.session: "A3 - Raumlauf-Animation und Impro-Training"
    │       event_type_id.ms_shortcode: "A3"
    │       date_begin: 2026-12-06
    │
    ├── event.session: "A4 - Präsentation einer Geschichte"
    │       event_type_id.ms_shortcode: "A4"
    │       date_begin: 2027-06-28
    │       is_entry_session: True
    │
    └── event.session: "A5 - Stückentwicklung Figurenkarussell"
            event_type_id.ms_shortcode: "A5"
            date_begin: 2027-07-26
```

---

## 4. Loyalty Program Implementation

### 4.1 Program: "Grundkurs Weiterbildung Komplett"

This loyalty program applies when customer books **all three continuation modules (B+C+D)** together in Checkout 2.

```python
# loyalty.program
grundkurs_komplett_m18 = {
    'name': 'Grundkurs Weiterbildung Komplett (M18)',
    'program_type': 'promotion',
    'trigger': 'auto',
    'applies_on': 'current',
    'date_to': '2027-01-31',  # Valid until end of B-D enrollment period
    'company_id': company.id,
    
    # Rule: All 3 continuation modules must be in cart
    'rule_ids': [(0, 0, {
        'product_ids': [(6, 0, [m18b.id, m18c.id, m18d.id])],
        'minimum_qty': 3,
        'reward_point_amount': 1,
        'reward_point_mode': 'order',
    })],
    
    # Reward: EUR 880 discount (4 Raten) on B+C only
    'reward_ids': [(0, 0, {
        'reward_type': 'discount',
        'discount': 880.00,
        'discount_mode': 'per_order',
        'discount_applicability': 'specific',
        'discount_product_ids': [(6, 0, [m18b.id, m18c.id])],  # B and C only
        'required_points': 1,
        'description': 'Weiterbildung Komplett-Rabatt (-4 Raten)',
    })],
}
```

### 4.2 Using Product Tags for Flexibility

```python
# product.tag for each edition
tag_grundkurs_m18_weiterbildung = {
    'name': 'Grundkurs M18 Weiterbildung',
}

# Apply to continuation modules only (B, C, D)
m18b.all_product_tag_ids = [(4, tag_id)]
m18c.all_product_tag_ids = [(4, tag_id)]
m18d.all_product_tag_ids = [(4, tag_id)]

# Loyalty rule using tag
'rule_ids': [(0, 0, {
    'product_tag_id': tag_grundkurs_m18_weiterbildung.id,
    'minimum_qty': 3,  # Must have all 3 tagged products
    ...
})]
```

---

## 5. Checkout UI Design

### 5.1 Checkout 1: Modul A (Default Entry Point)

URL Pattern: `/shop/checkout/grundkurs/modul-a/m18e`

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  🎭 EINSTIEGE IN'S THEATERSPIEL                                                 │
│     M18E - München 2026 // Sonntag & Online                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  📅 PROGRAMM - Sessions in diesem Modul                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ A0  Basistag Theaterpädagogik           Fr-So, 31.10-02.11.2026   10 UE│   │
│  │ A1  Einführung Kreisanimation           So, 12.10 + Online        22 UE│   │
│  │ A2  Zwei-Kreise-Modell                  So, 26.10 + Online        22 UE│   │
│  │ A3  Raumlauf-Animation                  Sa-So, 06-07.12 + Online  22 UE│   │
│  │ A4  Szenische Lesung                    So, 28.06.2027 + Online   22 UE│   │
│  │ A5  Figurenkarussell                    So, 26.07.2027 + Online   22 UE│   │
│  │ ─────────────────────────────────────────────────────────────────────  │   │
│  │                                         SUMME mind. 120 UE             │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  💰 KOSTEN                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ Anmeldegebühr (einmalig, nicht erstattbar)              EUR    80,00   │   │
│  │ Kursgebühr Modul A (5 Raten à EUR 220)                  EUR 1.100,00   │   │
│  │ ─────────────────────────────────────────────────────────────────────  │   │
│  │ GESAMT                                                  EUR 1.180,00   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  📋 ZAHLUNGSPLAN (2 Einmalzahlungen)                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ 1. Zahlung (bei Anmeldung)                              EUR   630,00   │   │
│  │ 2. Zahlung (Mitte November 2026)                        EUR   550,00   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ℹ️ STORNIERUNGSBEDINGUNGEN                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ Nach Ihrer ersten Einheit (A0, A1 oder A4) haben Sie 10 Tage Zeit,     │   │
│  │ sich zu entscheiden. Bei Stornierung innerhalb dieser Frist:           │   │
│  │ → Nur 1 Rate (EUR 220) + Anmeldegebühr (EUR 80) = EUR 300 gesamt       │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  🎓 WEITERBILDUNGSMÖGLICHKEIT                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ Nach erfolgreicher Teilnahme an mind. 2 Sessions + Beratungsgespräch   │   │
│  │ können Sie zur Weiterbildung (Module B-D) aufstufen.                   │   │
│  │ → Abschluss: "Grundlagen Theaterpädagogik (BuT)" bis Juli 2028         │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ☐ Ich akzeptiere die AGB und Stornierungsbedingungen                          │
│                                                                                  │
│  [        JETZT ANMELDEN - EUR 630,00 (1. Zahlung)        ]                     │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Checkout 2: Weiterbildung (Modules B-D) - Add-On

URL Pattern: `/shop/checkout/grundkurs/weiterbildung/m18`

**Preconditions (checked before showing this page):**
- ✅ Customer has active Modul A registration
- ✅ Minimum 2 sessions marked as 'done' in event.registration
- ✅ Consultation completed (partner.grundkurs_consultation_done = True)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  🎓 JETZT ZUR WEITERBILDUNG AUFSTUFEN                                           │
│     Grundkurs Theaterpädagogik M18 - Module B, C & D                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ✅ Voraussetzungen erfüllt                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ • 3 von 6 Sessions in Modul A abgeschlossen (A0, A1, A2)               │   │
│  │ • Beratungsgespräch am 15.11.2026 durchgeführt                         │   │
│  │ • Berechtigt zur Buchung der Weiterbildung                             │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ─────────────────────────────────────────────────────────────────────────────  │
│                                                                                  │
│  WÄHLEN SIE IHRE BUCHUNGSOPTION:                                               │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ ◉ KOMPLETT-BUCHUNG (empfohlen)                     💰 Sie sparen EUR 880│   │
│  │                                                                         │   │
│  │   ☑ Modul B: Szenische Themenarbeit (Jan-Mai 2027)                     │   │
│  │     Sessions: B1, B2, B3, B4, B5, B6                    6 Raten        │   │
│  │   ☑ Modul C: Pädagogische Regie (Jun-Dez 2027)                         │   │
│  │     Sessions: C1, C2, C3, C4, C5, C6                    6 Raten        │   │
│  │   ☑ Modul D: Kolloquium & Projekt (Jan-Jul 2028)                       │   │
│  │     Sessions: D1, D2, D3, D4, D5                        5 Raten        │   │
│  │   ─────────────────────────────────────────────────────────────────    │   │
│  │   GESAMT: 17 Raten = EUR 3.740,00                                      │   │
│  │   Monatliche Zahlung ab 01.01.2027: EUR 220,00                         │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ ○ EINZELBUCHUNG (Module separat wählbar)                                │   │
│  │                                                                         │   │
│  │   ☐ Modul B: Szenische Themenarbeit (Jan-Mai 2027)      8 Raten        │   │
│  │       = EUR 1.760,00                                                   │   │
│  │   ☐ Modul C: Pädagogische Regie (Jun-Dez 2027)          8 Raten        │   │
│  │       = EUR 1.760,00                                                   │   │
│  │   ☐ Modul D: Kolloquium & Projekt (Jan-Jul 2028)        5 Raten        │   │
│  │       = EUR 1.100,00                                                   │   │
│  │   ─────────────────────────────────────────────────────────────────    │   │
│  │   Max. Einzelpreis (alle 3): 21 Raten = EUR 4.620,00                   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  📅 ZAHLUNGSÜBERSICHT (bei Komplett-Buchung)                                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ 2027                           │ 2028                                  │   │
│  │ Jan: EUR 220  Jul: EUR 220     │ Jan: EUR 220  Mai: EUR 220           │   │
│  │ Feb: EUR 220  Aug: EUR 220     │ Feb: EUR 220                          │   │
│  │ Mär: EUR 220  Sep: EUR 220     │ Mär: EUR 220                          │   │
│  │ Apr: EUR 220  Okt: EUR 220     │ Apr: EUR 220                          │   │
│  │ Mai: EUR 220  Nov: EUR 220     │                                       │   │
│  │ Jun: EUR 220  Dez: EUR 220     │ Gesamt: 17 Zahlungen                  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ☐ Ich akzeptiere die AGB für die Weiterbildung                                │
│                                                                                  │
│  [     WEITERBILDUNG BUCHEN - Komplett EUR 3.740,00     ]                       │
│                                                                                  │
│  ───────────────────────────────────────────────────────────────────────────   │
│  💡 Vergleich: Komplett-Buchung spart EUR 880 (4 Raten)                        │
│     gegenüber Einzelbuchung aller drei Module                                   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Entity Relationship Diagram

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           GRUNDKURS DATA MODEL                                    │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐         │
│  │ product.product │       │  event.event    │       │ event.session   │         │
│  │ (Modul)         │       │ (Modul Edition) │       │ (Workshop)      │         │
│  ├─────────────────┤       ├─────────────────┤       ├─────────────────┤         │
│  │ M18E            │◄──────│ M18E - 2026     │◄──────│ A0 - Basistag   │         │
│  │ M18B            │ ticket│ use_sessions=T  │session│ A1 - Kreis...   │         │
│  │ M18C            │       │                 │       │ A2 - Zwei...    │         │
│  │ M18D            │       └─────────────────┘       │ ...             │         │
│  └─────────────────┘               │                 └─────────────────┘         │
│          │                         │                         │                   │
│          │                         ▼                         │                   │
│          │                 ┌─────────────────┐               │                   │
│          │                 │event.event.ticket               │                   │
│          └────────────────►│ product_id      │               │                   │
│                            │ event_id        │               │                   │
│                            │ price           │               │                   │
│                            └─────────────────┘               │                   │
│                                    │                         │                   │
│                                    ▼                         ▼                   │
│  ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐         │
│  │  sale.order     │◄──────│sale.order.line  │       │event.registration         │
│  │ (Buchung)       │       │                 │──────►│ partner_id      │         │
│  ├─────────────────┤       ├─────────────────┤       │ session_id      │         │
│  │ partner_id      │       │ product_id:M18E │       │ state (done)    │         │
│  │ checkout_type:  │       │ event_id        │       └─────────────────┘         │
│  │  - modul_a      │       │ event_ticket_id │               │                   │
│  │  - weiterbildung│       └─────────────────┘               │                   │
│  └─────────────────┘               │                         │                   │
│          │                         │                         │                   │
│          ▼                         ▼                         ▼                   │
│  ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐         │
│  │ loyalty.card    │       │ account.payment │       │ res.partner     │         │
│  │ (Rabatt)        │       │ .schedule       │       │                 │         │
│  ├─────────────────┤       ├─────────────────┤       ├─────────────────┤         │
│  │ program_id      │       │ partner_id      │       │ grundkurs_      │         │
│  │ points          │       │ amount: 220     │       │  consultation_  │         │
│  │                 │       │ date_due        │       │  done: Bool     │         │
│  └─────────────────┘       │ state           │       │ grundkurs_      │         │
│                            └─────────────────┘       │  sessions_done  │         │
│                                                      └─────────────────┘         │
│                                                                                   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Yearly Course Naming Convention

| Year | Code | Full Name |
|------|------|-----------|
| 2026-2028 | M18 | M18 - Grundkurs Theaterpädagogik 2026-2028, München |
| 2027-2029 | M19 | M19 - Grundkurs Theaterpädagogik 2027-2029, München |
| 2028-2030 | M20 | M20 - Grundkurs Theaterpädagogik 2028-2030, München |

### Module Codes per Year

| Year | Modul A | Modul B | Modul C | Modul D |
|------|---------|---------|---------|---------|
| M18 | M18E | M18B | M18C | M18D |
| M19 | M19E | M19B | M19C | M19D |
| M20 | M20E | M20B | M20C | M20D |

---

## 8. Implementation Summary

### Required Odoo Modules

```python
'depends': [
    'event',               # Base event management
    'event_sale',          # Event + Sales integration
    'event_session',       # OCA: Sessions within events
    'sale_loyalty',        # Loyalty programs for sales
    'website_sale',        # E-commerce
    'website_sale_loyalty',# Loyalty in web shop
    'crearis',             # Base crearis module
    'crearis_agenda',      # SharePoint sync (creates event.type from plan_veranstaltungscodes)
]
```

### Minimal Custom Fields Needed

| Model | Field | Type | Purpose |
|-------|-------|------|---------|
| `event.session` | `is_entry_session` | Boolean | Marks A0/A1/A4 for 10-day rule |
| `res.partner` | `grundkurs_consultation_done` | Boolean | Tracks consultation requirement |
| `res.partner` | `grundkurs_sessions_completed` | Integer | Computed: count of 'done' registrations |
| `sale.order` | `checkout_type` | Selection | 'modul_a' or 'weiterbildung' |

---

*Report Version: 2.0*  
*Last Updated: 2025-12-21*  
*Course: M18 - Grundkurs Theaterpädagogik 2026-2028, München*  
*Pricing: 1 Rate = EUR 220,00 | Anmeldegebühr = EUR 80,00*
