# Imaginations: Grundkurs Checkout Scenarios

> **Purpose:** Creative UI/UX alternatives for the two-checkout model  
> **For:** Design discussions & wireframing  
> **Date:** December 21, 2025

---

## Introduction

This document presents **three alternative scenarios** for how the Grundkurs booking flow could be implemented. Each scenario makes different tradeoffs between simplicity, user guidance, and technical complexity.

---

## Scenario 1: "Linear Progression"

### Concept

A simple, step-by-step funnel where the customer progresses through clearly defined phases. The website shows different content based on where the customer is in their journey.

### Customer States

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  STATE 1: VISITOR                                                          │
│  ─────────────────                                                          │
│  • Can see: Course overview, session descriptions                          │
│  • Cannot see: Pricing, checkout                                           │
│  • CTA: "Infogespräch vereinbaren" or "Interesse registrieren"             │
│                                                                             │
│                              ↓                                              │
│                                                                             │
│  STATE 2: INTERESTED (after info call)                                     │
│  ─────────────────────────────────────                                      │
│  • Can see: Full Modul A details, pricing                                  │
│  • Cannot see: Continuation modules                                        │
│  • CTA: "Modul A buchen"                                                   │
│                                                                             │
│                              ↓                                              │
│                                                                             │
│  STATE 3: PARTICIPANT (after Modul A booking)                              │
│  ────────────────────────────────────────────                               │
│  • Can see: Their schedule, upcoming sessions                              │
│  • Cannot see: Checkout 2 (yet)                                            │
│  • CTA: "Meine Sessions"                                                   │
│                                                                             │
│                              ↓                                              │
│                                                                             │
│  STATE 4: QUALIFIED (2+ sessions + consultation)                           │
│  ──────────────────────────────────────────────                             │
│  • Can see: Full program, Checkout 2                                       │
│  • Prominent: Bundle discount offer                                        │
│  • CTA: "Zur Weiterbildung aufstufen"                                      │
│                                                                             │
│                              ↓                                              │
│                                                                             │
│  STATE 5: ENROLLED (booked continuation)                                   │
│  ───────────────────────────────────────                                    │
│  • Can see: Complete 2-year schedule                                       │
│  • Access: Learning materials, community                                   │
│  • CTA: "Mein Ausbildungsportal"                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### UI Mockup: Home Page by State

**Visitor View:**
```
┌─────────────────────────────────────────────────────────────────────┐
│  GRUNDKURS THEATERPÄDAGOGIK                                         │
│  Deine Ausbildung in 2 Jahren zum BuT-Zertifikat                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [Hero Image: Workshop Scene]                                       │
│                                                                     │
│  Was dich erwartet:                                                │
│  • 22+ praxisorientierte Workshops                                 │
│  • Blended Learning: Präsenz + Online                              │
│  • Abschluss "Grundlagen Theaterpädagogik (BuT)"                   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │  Interessiert?                                          │       │
│  │  Vereinbare ein unverbindliches Infogespräch           │       │
│  │                                                         │       │
│  │  [   TERMIN VEREINBAREN   ]                            │       │
│  └─────────────────────────────────────────────────────────┘       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Qualified Participant View:**
```
┌─────────────────────────────────────────────────────────────────────┐
│  Hallo [Name]! 🎭                                                   │
│  Du hast bereits 3 Sessions besucht                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │  🎓 WEITERBILDUNG JETZT VERFÜGBAR                       │       │
│  │                                                         │       │
│  │  Du erfüllst alle Voraussetzungen!                     │       │
│  │  • ✓ 3 von 6 Sessions abgeschlossen                    │       │
│  │  • ✓ Beratungsgespräch am 15.11. durchgeführt          │       │
│  │                                                         │       │
│  │  SPARE EUR 880 mit der Komplett-Buchung                │       │
│  │                                                         │       │
│  │  [   WEITERBILDUNG BUCHEN   ]                          │       │
│  └─────────────────────────────────────────────────────────┘       │
│                                                                     │
│  Dein nächster Termin:                                             │
│  A3 - Raumlauf-Animation | Sa 06.12.2026, 10:00                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Technical Requirements

| Requirement | Odoo Feature | Complexity |
|-------------|--------------|------------|
| User state tracking | `res.partner` computed field | Low |
| State-based content | Website snippets + Python | Medium |
| Hidden pricing | Website access rights | Low |
| Progress display | `event.registration` fields | Low |

### Pros & Cons

| ✅ Pros | ❌ Cons |
|---------|---------|
| Clear customer journey | Requires info call for all |
| High-touch sales process | More complex website logic |
| Can qualify leads before booking | Visitors can't see pricing |
| Personalized experience | Requires login earlier |

---

## Scenario 2: "Open Catalog"

### Concept

All information is publicly visible. Customers can see the entire 2-year program, but booking is naturally sequential. The checkout flow enforces the rules.

### Customer Experience

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ALL VISITORS SEE:                                                         │
│  ─────────────────                                                          │
│  • Complete 2-year curriculum                                              │
│  • All session descriptions                                                │
│  • All pricing (transparent)                                               │
│  • "Modul A" has [JETZT BUCHEN] button                                     │
│  • Modules B-D have "Buchung nach Modul A möglich" notice                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WEBSITE STRUCTURE:                                                        │
│                                                                             │
│  /grundkurs                                                                │
│      ├── Overview (all 4 modules visible)                                  │
│      ├── /modul-a  → [JETZT BUCHEN]                                        │
│      ├── /modul-b  → "Nach Modul A buchbar"                                │
│      ├── /modul-c  → "Nach Modul A buchbar"                                │
│      └── /modul-d  → "Nach Modul A buchbar"                                │
│                                                                             │
│  CHECKOUT RULES (enforced in cart):                                        │
│                                                                             │
│  • Modul A: Always bookable                                                │
│  • Modules B-D: Only if customer has Modul A registration +               │
│                 is_qualified_for_continuation == True                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### UI Mockup: Modul B Page (Not Yet Qualified)

```
┌─────────────────────────────────────────────────────────────────────┐
│  MODUL B: SZENISCHE THEMENARBEIT                                   │
│  Januar - Mai 2027                                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  SESSIONS:                                                         │
│  B1  Spannende Geschichten          So, 10.01.2027                │
│  B2  Szenisches Erzählen            So, 24.01.2027                │
│  B3  Konflikte entwickeln           Sa-So, 13-14.02.2027          │
│  B4  Improvisation II               So, 28.02.2027                │
│  B5  Textarbeit                     So, 14.03.2027                │
│  B6  Kollektive Stückentwicklung    Sa-So, 27-28.03.2027          │
│                                                                     │
│  PREIS: EUR 1.320 (6 Raten à EUR 220)                              │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │  ℹ️ NOCH NICHT BUCHBAR                                   │       │
│  │                                                         │       │
│  │  Modul B kann nach Abschluss von Modul A gebucht       │       │
│  │  werden. Voraussetzungen:                               │       │
│  │                                                         │       │
│  │  ○ Mind. 2 Sessions in Modul A besucht                 │       │
│  │  ○ Beratungsgespräch durchgeführt                      │       │
│  │                                                         │       │
│  │  Du bist noch nicht für Modul A angemeldet?            │       │
│  │  [   MODUL A BUCHEN   ]                                │       │
│  └─────────────────────────────────────────────────────────┘       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### UI Mockup: Checkout 2 (Qualified Customer)

```
┌─────────────────────────────────────────────────────────────────────┐
│  🎓 WEITERBILDUNG BUCHEN                                           │
│                                                                     │
│  Du bist angemeldet für: Modul A (M18) - 3 Sessions besucht       │
│  Beratung: ✓ Durchgeführt am 15.11.2026                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Wähle deine Buchungsart:                                          │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │ ◉ KOMPLETT-BUCHUNG                     EMPFOHLEN 💰     │       │
│  │   Module B + C + D zusammen                             │       │
│  │                                                         │       │
│  │   Regulär:    EUR 4.620                                │       │
│  │   Du zahlst:  EUR 3.740                                │       │
│  │   ─────────────────────                                │       │
│  │   Ersparnis:  EUR   880 ✨                             │       │
│  │                                                         │       │
│  │   17 monatliche Zahlungen à EUR 220                    │       │
│  │   Start: Januar 2027                                   │       │
│  └─────────────────────────────────────────────────────────┘       │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │ ○ EINZELNE MODULE                                       │       │
│  │                                                         │       │
│  │   ☐ Modul B    EUR 1.760    (8 Raten)                  │       │
│  │   ☐ Modul C    EUR 1.760    (8 Raten)                  │       │
│  │   ☐ Modul D    EUR 1.100    (5 Raten)                  │       │
│  └─────────────────────────────────────────────────────────┘       │
│                                                                     │
│  [        ZUR KASSE - EUR 3.740        ]                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Technical Requirements

| Requirement | Odoo Feature | Complexity |
|-------------|--------------|------------|
| Public catalog | Standard website | None |
| Cart validation | `website_sale` override | Medium |
| Qualification check | `event.registration` lookup | Low |
| Bundle discount | `sale_loyalty` | Low |

### Pros & Cons

| ✅ Pros | ❌ Cons |
|---------|---------|
| Full transparency | No lead capture before Modul A |
| Simple website structure | Less personal guidance |
| Standard Odoo checkout | Customers may be confused by "locked" modules |
| Easy to maintain | Discount logic in cart may surprise |

---

## Scenario 3: "Pathway Builder"

### Concept

An interactive configurator that lets customers design their learning pathway. Similar to configuring a product with options, but for education.

### Customer Experience

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  INTERACTIVE PATHWAY BUILDER                                               │
│  ──────────────────────────────                                             │
│                                                                             │
│  Customer answers questions to build their path:                           │
│                                                                             │
│  SCHRITT 1: Was ist dein Ziel?                                             │
│  ○ Theaterpädagogik kennenlernen (nur Modul A)                            │
│  ○ Grundlagen-Zertifikat erwerben (komplette Ausbildung)                  │
│  ○ Noch unsicher (erst Modul A, später entscheiden)                       │
│                                                                             │
│  SCHRITT 2: Wann möchtest du starten?                                      │
│  ○ München 2026 (M18)                                                      │
│  ○ Berlin 2027 (B19)                                                       │
│  ○ Noch nicht sicher → Interesse registrieren                             │
│                                                                             │
│  SCHRITT 3: Dein Ergebnis                                                  │
│  → Personalisierte Empfehlung + Preisübersicht                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### UI Mockup: Pathway Builder

```
┌─────────────────────────────────────────────────────────────────────┐
│  DEIN WEG IN DIE THEATERPÄDAGOGIK                                  │
│  ─────────────────────────────────                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ◉ SCHRITT 1    ○ SCHRITT 2    ○ ERGEBNIS                          │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │                                                         │       │
│  │  WAS MÖCHTEST DU ERREICHEN?                            │       │
│  │                                                         │       │
│  │  ┌───────────────────────────────────────────────┐     │       │
│  │  │  🎭 REINSCHNUPPERN                            │     │       │
│  │  │  Modul A: Einstiege in's Theaterspiel         │     │       │
│  │  │  6 Sessions • EUR 1.180 • 1 Jahr              │     │       │
│  │  │  Ideal für: Einsteiger, Neugierige            │     │       │
│  │  └───────────────────────────────────────────────┘     │       │
│  │                                                         │       │
│  │  ┌───────────────────────────────────────────────┐     │       │
│  │  │  🎓 AUSBILDUNG KOMPLETT              💰 SPARE │     │       │
│  │  │  Module A + B + C + D                  EUR 880│     │       │
│  │  │  22 Sessions • EUR 4.920 • 2 Jahre            │     │       │
│  │  │  Ideal für: Zukünftige Theaterpädagog:innen   │     │       │
│  │  │                                               │     │       │
│  │  │  Modul A buchen, später aufstufen möglich!    │     │       │
│  │  └───────────────────────────────────────────────┘     │       │
│  │                                                         │       │
│  │  ┌───────────────────────────────────────────────┐     │       │
│  │  │  ❓ NOCH UNSICHER?                            │     │       │
│  │  │  Starte mit Modul A und entscheide später    │     │       │
│  │  │  Keine Verpflichtung zur Weiterbildung        │     │       │
│  │  └───────────────────────────────────────────────┘     │       │
│  │                                                         │       │
│  └─────────────────────────────────────────────────────────┘       │
│                                                                     │
│                                         [   WEITER →   ]           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### UI Mockup: Result Page (Komplette Ausbildung Selected)

```
┌─────────────────────────────────────────────────────────────────────┐
│  DEIN PERSÖNLICHER AUSBILDUNGSPLAN                                 │
│  ─────────────────────────────────────                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🎯 Ziel: Grundlagen-Zertifikat (BuT)                              │
│  📍 Standort: München (M18)                                        │
│  ⏱️ Zeitraum: Oktober 2026 - Juli 2028                             │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │ DEIN PLAN                                                 │     │
│  │                                                           │     │
│  │ 2026   ████████░░░░░░░░░░░░░░░░  Modul A (6 Sessions)   │     │
│  │ 2027   ████████████████████░░░░  Modul B+C (12 Sessions)│     │
│  │ 2028   ████████░░░░░░░░░░░░░░░░  Modul D (5 Sessions)   │     │
│  └───────────────────────────────────────────────────────────┘     │
│                                                                     │
│  💰 KOSTENÜBERSICHT                                                │
│                                                                     │
│  Schritt 1: Jetzt buchen                                           │
│  ├─ Anmeldegebühr:        EUR    80                                │
│  └─ 1. Zahlung Modul A:   EUR   630                                │
│                           ─────────                                │
│                           EUR   710                                │
│                                                                     │
│  Schritt 2: Nach Modul A (4-6 Monate später)                       │
│  ├─ 2. Zahlung Modul A:   EUR   470                                │
│  └─ Weiterbildung B+C+D:  EUR 3.740  ← EUR 880 Ersparnis!         │
│                           ─────────                                │
│                           EUR 4.210                                │
│                                                                     │
│  GESAMT: EUR 4.920 (22 Raten + Anmeldung)                          │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │                                                         │       │
│  │  ✓ Jetzt wird nur Modul A gebucht (EUR 710)            │       │
│  │  ✓ Weiterbildung nach Beratungsgespräch möglich        │       │
│  │  ✓ 10-Tage-Garantie nach erster Session                │       │
│  │                                                         │       │
│  │  [     MODUL A BUCHEN - EUR 710     ]                  │       │
│  │                                                         │       │
│  │  Nach 2+ Sessions und einem Beratungsgespräch          │       │
│  │  schalten wir die Weiterbildung für dich frei.         │       │
│  │                                                         │       │
│  └─────────────────────────────────────────────────────────┘       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Technical Requirements

| Requirement | Odoo Feature | Complexity |
|-------------|--------------|------------|
| Interactive wizard | Custom website snippet | High |
| Pathway storage | `res.partner` fields | Low |
| Dynamic pricing | JavaScript calculator | Medium |
| Lead capture | CRM integration | Low |
| Timeline visualization | Custom JavaScript | Medium |

### Pros & Cons

| ✅ Pros | ❌ Cons |
|---------|---------|
| Highly engaging | Most complex to build |
| Shows commitment savings upfront | Requires JavaScript development |
| Good for different customer intents | More maintenance |
| Lead qualification built-in | May overwhelm some users |
| Beautiful UX | Harder to A/B test |

---

## Comparison Matrix

| Feature | Scenario 1: Linear | Scenario 2: Open | Scenario 3: Pathway |
|---------|-------------------|------------------|---------------------|
| **Complexity** | Medium | Low | High |
| **Time to implement** | 3-4 weeks | 1-2 weeks | 6-8 weeks |
| **Lead capture** | Excellent | Poor | Good |
| **Transparency** | Low (by design) | High | High |
| **Personalization** | High | Low | Very High |
| **Mobile UX** | Good | Good | Challenging |
| **Maintenance** | Medium | Low | High |
| **Standard Odoo** | 60% | 90% | 40% |

---

## Recommendation

### For MVP (Now)

**Start with Scenario 2: Open Catalog**

- Fastest to implement
- Uses standard Odoo checkout
- Full price transparency builds trust
- Qualification logic in checkout is standard pattern

### For V2 (After Launch)

**Add elements from Scenario 3: Pathway Builder**

- Interactive goal selection on landing page
- Timeline visualization for enrolled participants
- Personalized recommendations in customer portal

### Hybrid Approach

```
┌─────────────────────────────────────────────────────────────────────┐
│  RECOMMENDED IMPLEMENTATION                                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PHASE 1 (MVP):                                                    │
│  • Scenario 2 checkout flow                                        │
│  • Public catalog with clear "not yet bookable" notices            │
│  • Standard Odoo loyalty program for bundle discount               │
│                                                                     │
│  PHASE 2 (Enhancement):                                            │
│  • Add pathway builder on landing page                             │
│  • Personalized dashboard for participants                         │
│  • Progress visualization                                          │
│                                                                     │
│  PHASE 3 (Polish):                                                 │
│  • Full Scenario 3 interactive experience                          │
│  • A/B testing different checkout flows                            │
│  • Mobile app for session check-in                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Appendix: Mobile Considerations

### Checkout on Mobile

All scenarios must work well on mobile. Key considerations:

```
┌─────────────────────┐
│ MODUL A BUCHEN      │
├─────────────────────┤
│                     │
│ ▼ Was ist Modul A?  │
│                     │
│ 📅 6 Sessions       │
│ ⏱️ 1 Jahr (2026)    │
│ 📍 München + Online │
│                     │
│ ─────────────────── │
│ Anmeldung   EUR  80 │
│ Kursgebühr  EUR 1100│
│ ─────────────────── │
│ GESAMT      EUR 1180│
│                     │
│ ┌─────────────────┐ │
│ │ Jetzt zahlen:   │ │
│ │ EUR 630         │ │
│ │                 │ │
│ │ [  BUCHEN  ]    │ │
│ └─────────────────┘ │
│                     │
│ ⓘ 10 Tage Garantie │
│                     │
└─────────────────────┘
```

### Collapsible Session Details

```
┌─────────────────────┐
│ SESSIONS            │
├─────────────────────┤
│ ▼ A0 Basistag       │
│   31.10-02.11.2026  │
│   Fr-So, München    │
│   24 UE             │
├─────────────────────┤
│ ▶ A1 Kreisanimation │
├─────────────────────┤
│ ▶ A2 Zwei-Kreise    │
├─────────────────────┤
│ ▶ A3 Raumlauf       │
├─────────────────────┤
│ ▶ A4 Szen. Lesung   │
├─────────────────────┤
│ ▶ A5 Figurenkaruss. │
└─────────────────────┘
```

---

*Design Scenarios for Grundkurs Checkout*  
*December 2025*
