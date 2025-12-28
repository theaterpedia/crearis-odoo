# 5c: Create Course Templates for M18/N18

*Proposal Document - Created: 2025-12-27*

---

## Overview

This document describes how to create the YAML/MDC templates for future courses (M18, N18) based on the existing M17/N17 course files, with dates shifted exactly one year later.

## Source Files (M17)

Based on the analysis of existing files:
- `einstiege-ins-theaterspiel_m17e.md` - München Tageskurs (E-Variant)
- `einstiege-ins-theaterspiel_m17b.md` - Burgstallmühle Block (B-Variant)
- (N17 files follow the same pattern for Nürnberg)

## Template Strategy

### 1. E-Variant Template (Tageskurs)

The E-Variant is for **Sunday day-courses** with online evening sessions.

### 2. B-Variant Template (Blockseminar)

The B-Variant starts with a **4-day block at Burgstallmühle** seminar house, then continues with day sessions.

---

## Template 1: E-Variant (Tageskurs)

### File: `templates/course_e_variant.mdc.template`

```mdc
---
navigation: false
navigation_highlight: /ausbildung-theaterpaedagogik/einstiege
shortcode: {{SHORTCODE}}
odoo_product_ref: {{ODOO_REF}}
heading: "**Einstiege ins Theaterspiel** {{CITY}} {{START_DATE_SHORT}} - {{END_DATE_SHORT}} // Sonntag & Online"
start: {{START_DATE}}
end: {{END_DATE}}
ctype: course
tag: course
description: Weiterbildung Theaterpädagogik - Kurs {{ODOO_REF}} {{CITY}} {{START_DATE_SHORT}} - {{END_DATE_SHORT}} // Sonntags-Kurs {{CITY}}
title: Einstiege ins Theaterspiel
cssclasses:
  - course
views:
  - product
  - details
details:
 programm:
  title: Programm & Struktur
  header: |
   ## Programm & Struktur
  info:
   struktur: |
    ### Struktur
    - **Basistag** 10 UE
    - **5 Einheiten A1-A5** _110 UE_
    - **SUMME** mind. 120 UE
    *UEs ("Unterrichtseinheiten") sind voll anrechenbar auf die Zertifikate Theaterpädagogik (BuT), eine UE entspricht 45 Min
   beratung: |
    #### Beratung
    - bei Kursanmeldung Beratung zur Frage, ob eher Blockprogramm oder Tageskursverlauf sinnvoll ist
    - im {{ADVICE_MONTH}} {{YEAR}} Beratung zur Fortsetzung Grundlagenbildung Kurse {{COURSE_PREFIX}}18 mit Ziel 'Grundlagen Theaterpädagogik (BuT)'
    - Fortsetzung Aufbaustufe möglich mit Abschluss 'Theaterpädagog:in (BuT)' bis Juli {{YEAR_PLUS_3}}
  agenda:
   style: default
 konditionen:
  title: Kosten & Konditionen
  header: |
   ## Kosten & Konditionen
  info:
   kosten: |
    ### Kosten
    - **A0 Anmeldegebühr (inkl. Basistag)** € 80,00 
    - Frist: {{FEE_DEADLINE}}
    - **5 Kursraten A1-A5** 5 Raten x € 220,00
    - Zahlung: 5 Monatsraten
   storno: |
    ### Widerruf & Storno
    - 14 Tage Widerruf (bei Anmeldungen bis {{CANCEL_DEADLINE}})
    - bis 10 Tage nach Basistag kostenfreies Storno A1-A5        
product:
 header: |
  ## 6 Kurseinheiten
  In 6 prägnanten Einheiten wirst Du beide Wege erleben, verstehen und selber anleiten: Du lernst die Methoden, die Leitungshaltung und typische Abläufe. Egal, welche Vorerfahrungen Du mitbringst sind wir sicher, dass Du dabei viel mitnehmen wirst.
 footer: |
  ## {{MONTH_RANGE}} {{YEAR}} // {{CITY}} **Einstiege ins Theaterspiel**
items: 
 a1_{{ITEM_ID_A1}}:
  ctype: event
  shortcode: a1
  tag: So., {{A1_TAG}} + 2 Abende online
  title: Einführung in die Kreisanimation **Am Anfang war der Kreis**
  image: 
   url: https://res.cloudinary.com/little-papillon/image/upload/w_400/v1594788813/dasei/am_anfang_war_der_kreis_s9qh5y.jpg
   caption: Theaterpädagogik Kreisanimation
  body: |
   Den Einstieg in die elementare Animation bilden die Kreisspiele: Hier kommen Grundregeln und -phänomene von interaktivem Spiel sehr deutlich zum Vorschein. Zunächst beschäftigen wir uns mit den einfachen und offensichtlichen Impulsen entlang der Kreisbahn und quer durch die Kreismitte und lernen dann, zahlreiche Grundanforderungen des Theaterspiels im Kreisspiel zu trainieren.
  start: {{A1_START}}
  ende: {{A1_END}}
  ort: |
   {{VENUE_ADDRESS}}
  ablauf: |
   Fr. 18:00-20:00 _online_
   So. 09:30-19:00
   Di. 18:00-21:00 _online_
  mit: {{A1_TRAINER}}
 a2_{{ITEM_ID_A2}}:
  ctype: event
  shortcode: a2 
  title: Arbeiten mit dem Zwei-Kreise-Modell **die Bühne kommt von selbst**
  tag: So., {{A2_TAG}} + 2 Abende online  
  image: 
   url: https://res.cloudinary.com/little-papillon/image/upload/w_400/v1676100503/dasei/377_dasei2022_I8A6515_p6aee7.jpg
   caption: Foto die Bühne kommt von selbst
  body: |
   Wenn Du gelernt hast, die Interaktion der Gruppe im Kreis freizusetzen, entstehen fast von selbst 'Bühnenmomente'. Mit dem Zwei-Kreise-Modell lernst Du diese Momente gezielt zu gestalten und verbindest das Theaterpotential einfacher Animationen zu einem bühnenreifen Setting: Der Kreis öffnet sich zum Halbkreis und gibt in der Mitte eine Spielfläche frei.
  start: {{A2_START}}
  ende: {{A2_END}}
  ort: |
   {{VENUE_ADDRESS}}
  ablauf: |
   Fr. 18:00-20:00 _online_
   So. 09:30-19:00
   Di. 18:00-21:00 _online_
  mit: {{A2_TRAINER}}
 a0_{{ITEM_ID_A0}}:
  ctype: event
  shortcode: a0
  title: Praxis, Theorie & Ausbildung bei DAS Ei **Basistag Theaterpädagogik**
  tag: Fr., {{A0_TAG}} (oder alternative Terminauswahl)
  image: 
   url: https://res.cloudinary.com/little-papillon/image/upload/w_400/v1676101506/dasei/700_dasei2022_I8A7903_cvtigl.jpg
   caption: Foto Basistag Theaterpädagogik
  body: |
   Am Basistag erlebst Du die grundsätzlichen Zusammenhänge der Theaterpädagogik von DAS Ei konzentriert und ganz praktisch am eigenen Leib. Du erarbeitest Dir ausgehend von drei Zwischenreflexionen ein Grundverständnis der Module
   - Einstiege ins Theaterspiel (Modul A)
   - Szenische Themenarbeit (Modul B)
   - Pädagogische Regie (Modul C)
  start: {{A0_START}}
  ende: {{A0_END}}
  ort: |
   {{VENUE_ADDRESS}}
  ablauf: |
   Fr. 18:00-20:00 _online_
   So. 09:30-19:00
  mit: {{A0_TRAINER}}
 a3_{{ITEM_ID_A3}}:
  ctype: event
  shortcode: a3
  title: Raumlauf-Animation und Impro-Training **Wege entstehen beim Gehen**
  tag: Sa./So. {{A3_TAG}} + online-Abend
  image: 
   url: https://res.cloudinary.com/little-papillon/image/upload/w_400/v1676101054/dasei/wege_entstehen_beim_gehen.jpg
   caption: Foto den Fuß setzen
  body: |
   Nichts kann das Ganz-Auf-Sicht-Gestellt-Sein der Bühnensituation besser vorwegnehmen, als ein einfacher 'Raumlauf'; Jene Übung, in der sich Teilnehmer mit einem konkreten 'Geh-Auftrag' kreuz und quer durch den Raum bewegen. Ein gründliches Verstehen des Geschehens ist nicht nur hilfreich, um den Raumlauf ordentlich anleiten zu können, sondern eröffnet immer neue Einblicke auf das Agieren im Bühnenraum.
  start: {{A3_START}}
  ende: {{A3_END}}
  ort: |
   {{VENUE_ADDRESS}}
  ablauf: |
   Sa. 09:30-18:30
   So. 09:00-15:00
   Di., {{A3_ONLINE_DATE}} 18:00-21:00 _online_
  mit: {{A3_TRAINER}}
 a4_{{ITEM_ID_A4}}:
  ctype: event
  shortcode: a4
  tag: So., {{A4_TAG}} + 2 Abende online
  title: Präsentation einer Geschichte **Szenische Lesung**
  image: 
   url: https://res.cloudinary.com/little-papillon/image/upload/c_crop,h_2200,w_2200,x_1,y_100/c_scale,h_350,w_350/v1676102664/dasei/einstiege.jpg
   caption: Theaterpädagogik Szenische Lesung
  body: |
   Du erarbeitest dir spezifische Techniken, die es dir ermöglichen, unmittelbar in verschiedene Rollen zu schlüpfen. Für das teilnehmende Publikum bringst du auf diese Weise die Magie einer Geschichte zum Vorschein und interagierst als Animationsfigur. Die durch sie vermittelten Erlebnissen, können zum Auftakt eines Theaterstücks werden.
  start: {{A4_START}}
  ende: {{A4_END}}
  ort: |
   {{VENUE_ADDRESS}}
  ablauf: |
   Fr. 18:00-20:00 _online_
   So. 09:30-19:00
   Di. 18:00-21:00 _online_
  mit: {{A4_TRAINER}}
 a5_{{ITEM_ID_A5}}:
  ctype: event
  shortcode: a5
  tag: So., {{A5_TAG}} + 2 Abende online
  title: Stückentwicklung basierend auf Mitspieltheater **Figurenkarussell**
  image: 
   url: https://res.cloudinary.com/little-papillon/image/upload/v1676100144/dasei/figurenkarussell.jpg
   caption: Theaterpädagogik Figurenkarussell
  body: |
   Mithilfe des Figurenkarussells animierst du das teilnehmende Publikum aktiv in das Bühnengeschehen einzusteigen. Mühelos und ohne Umschweife gelingt es so, Zuschauende zu Mitspielenden zu machen. Wurde eine Rolle von einem oder mehreren Teilnehmenden übernommen, dreht sich das Figurenkarussell zur nächsten Figur.
  start: {{A5_START}}
  ende: {{A5_END}}
  ort: |
   {{VENUE_ADDRESS}}
  ablauf: |
   Fr. 18:00-20:00 _online_
   So. 09:30-19:00
   Di. 18:00-21:00 _online_
  mit: {{A5_TRAINER}}
---

<!-- PUBLISH-FROM-HERE -->

```

---

## Template 2: B-Variant (Blockseminar)

### File: `templates/course_b_variant.mdc.template`

```mdc
---
navigation: false
navigation_highlight: /ausbildung-theaterpaedagogik/einstiege
shortcode: {{SHORTCODE}}
odoo_product_ref: {{ODOO_REF}}
heading: "**Einstiege ins Theaterspiel** Burgstallmühle {{START_DATE_SHORT}} - {{END_DATE_SHORT}} // Blockseminarverlauf"
start: {{START_DATE}}
end: {{END_DATE}}
ctype: course
tag: course
description: Weiterbildung Theaterpädagogik - Kurs {{ODOO_REF}} Burgstallmühle {{START_DATE_SHORT}} - {{END_DATE_SHORT}} // Blockseminarverlauf Burgstallmühle
title: Einstiege ins Theaterspiel
cssclasses:
  - course
views:
  - product
  - details
details:
 programm:
  title: Programm & Struktur
  header: |
   ## Programm & Struktur
  info:
   struktur: |
    ### Struktur
    - **Basistag** 10 UE
    - **5 Einheiten A1-A5** _110 UE_
    - **SUMME** mind. 120 UE
   beratung: |
    #### Beratung
    - bei Kursanmeldung Beratung zur Frage, ob eher Blockprogramm oder Tageskursverlauf sinnvoll ist
    - im {{ADVICE_MONTH}} {{YEAR}} Beratung zur Fortsetzung Grundlagenbildung Kurse {{COURSE_PREFIX}}18
    - Fortsetzung Aufbaustufe möglich mit Abschluss Theaterpädagog:in (BuT) bis Juli {{YEAR_PLUS_3}}  
 konditionen:
  title: Kosten & Konditionen
  header: |
   ## Kosten & Konditionen
  info:
   kosten: |
    ### Kosten
    - **A0 Anmeldegebühr (inkl. Basistag)** € 80,00 
    - Frist: {{FEE_DEADLINE}}
    - **5 Kursraten A1-A5** 5 Raten x € 220,00
    - Zahlung: {{PAYMENT_SCHEDULE}}
   storno: |
    ### Widerruf & Storno
    -14-tägiges Widerrufsrecht ab Datum der Anmeldung
    -bis {{CANCEL_FREE_DEADLINE}} kostenfreies Storno
    -danach Bezahlung {{BLOCK_UNITS}} obligatorisch, bis {{CANCEL_PARTIAL_DEADLINE}} kostenfreies Storno der Teilnahme {{REMAINING_UNITS}}
product:
 header: |
  ## 6 Kurseinheiten in 3 Blocks
  In 6 prägnanten Einheiten wirst Du beide Wege erleben, verstehen und selber anleiten: Du lernst die Methoden, die Leitungshaltung und typische Abläufe. Egal, welche Vorerfahrungen Du mitbringst sind wir sicher, dass Du dabei viel mitnehmen wirst.
 footer: |
  ## {{MONTH_RANGE}} {{YEAR}} // München, Nürnberg **Einstiege ins Theaterspiel**
items: 
 a4_{{ITEM_ID_A4}}:
  ctype: event
  shortcode: a4
  tag: Do., {{BLOCK_START_TAG}} bis So., {{BLOCK_END_TAG}} (Seminarhaus)
  title: Präsentation einer Geschichte **Szenische Lesung**
  image: 
   url: https://res.cloudinary.com/little-papillon/image/upload/c_crop,h_2200,w_2200,x_1,y_100/c_scale,h_350,w_350/v1676102664/dasei/einstiege.jpg
   caption: Theaterpädagogik Szenische Lesung
  body: |
   Du erarbeitest dir spezifische Techniken, die es dir ermöglichen, unmittelbar in verschiedene Rollen zu schlüpfen. Für das teilnehmende Publikum bringst du auf diese Weise die Magie einer Geschichte zum Vorschein und interagierst als Animationsfigur. Die durch sie vermittelten Erlebnissen, können zum Auftakt eines Theaterstücks werden.
  start: {{A4_START}}
  ende: {{A4_END}}
  ort: |
   Burgstallmühle 1
   91572 Bechhofen
  ablauf: |
   Do. 19:00-21:30
   Fr. 09:00-18:30
  mit: {{A4_TRAINER}}
 a5_{{ITEM_ID_A5}}:
  ctype: event
  shortcode: a5
  tag: "(Fortsetzung: Do., {{BLOCK_START_TAG}} bis So., {{BLOCK_END_TAG}})"
  title: Stückentwicklung basierend auf Mitspieltheater **Figurenkarussell**
  image: 
   url: https://res.cloudinary.com/little-papillon/image/upload/v1676100144/dasei/figurenkarussell.jpg
   caption: Theaterpädagogik Figurenkarussell
  body: |
   Mithilfe des Figurenkarussells animierst du das teilnehmende Publikum aktiv in das Bühnengeschehen einzusteigen. Mühelos und ohne Umschweife gelingt es so, Zuschauende zu Mitspielenden zu machen. Wurde eine Rolle von einem oder mehreren Teilnehmenden übernommen, dreht sich das Figurenkarussell zur nächsten Figur.
  start: {{A5_START}}
  ende: {{A5_END}}
  ort: |
   Burgstallmühle 1
   91572 Bechhofen
  ablauf: |
   Sa. 09:00-18:00
   So. 09:00-15:00
   Di. 18:00-21:00 _online_
  mit: {{A5_TRAINER}}
 a1_{{ITEM_ID_A1}}:
  ctype: event
  shortcode: a1
  tag: So., {{A1_TAG}} + 2 Abende online
  title: Einführung in die Kreisanimation **Am Anfang war der Kreis**
  image: 
   url: https://res.cloudinary.com/little-papillon/image/upload/w_400/v1594788813/dasei/am_anfang_war_der_kreis_s9qh5y.jpg
   caption: Theaterpädagogik Kreisanimation
  body: |
   Den Einstieg in die elementare Animation bilden die Kreisspiele: Hier kommen Grundregeln und -phänomene von interaktivem Spiel sehr deutlich zum Vorschein. Zunächst beschäftigen wir uns mit den einfachen und offensichtlichen Impulsen entlang der Kreisbahn und quer durch die Kreismitte und lernen dann, zahlreiche Grundanforderungen des Theaterspiels im Kreisspiel zu trainieren.
  start: {{A1_START}}
  ende: {{A1_END}}
  ort: |
   {{DAY_VENUE_ADDRESS}}
  ablauf: |
   Fr. 18:00-20:00 _online_
   So. 09:30-19:00
   Di. 18:00-21:00 _online_
  mit: {{A1_TRAINER}}
 a2_{{ITEM_ID_A2}}:
  ctype: event
  shortcode: a2 
  title: Arbeiten mit dem Zwei-Kreise-Modell **die Bühne kommt von selbst**
  tag: So., {{A2_TAG}} + 2 Abende online  
  image: 
   url: https://res.cloudinary.com/little-papillon/image/upload/w_400/v1676100503/dasei/377_dasei2022_I8A6515_p6aee7.jpg
   caption: Foto die Bühne kommt von selbst
  body: |
   Wenn Du gelernt hast, die Interaktion der Gruppe im Kreis freizusetzen, entstehen fast von selbst 'Bühnenmomente'. Mit dem Zwei-Kreise-Modell lernst Du diese Momente gezielt zu gestalten und verbindest das Theaterpotential einfacher Animationen zu einem bühnenreifen Setting: Der Kreis öffnet sich zum Halbkreis und gibt in der Mitte eine Spielfläche frei.
  start: {{A2_START}}
  ende: {{A2_END}}
  ort: |
   {{DAY_VENUE_ADDRESS}}
  ablauf: |
   Fr. 18:00-20:00 _online_
   So. 09:30-19:00
   Di. 18:00-21:00 _online_
  mit: {{A2_TRAINER}}
 a0_{{ITEM_ID_A0}}:
  ctype: event
  shortcode: a0
  title: Praxis, Theorie & Ausbildung bei DAS Ei **Basistag Theaterpädagogik**
  tag: Fr., {{A0_TAG}} (oder alternative Terminauswahl)
  image: 
   url: https://res.cloudinary.com/little-papillon/image/upload/w_400/v1676101506/dasei/700_dasei2022_I8A7903_cvtigl.jpg
   caption: Foto Basistag Theaterpädagogik
  body: |
   Am Basistag erlebst Du die grundsätzlichen Zusammenhänge der Theaterpädagogik von DAS Ei konzentriert und ganz praktisch am eigenen Leib. Du erarbeitest Dir ausgehend von drei Zwischenreflexionen ein Grundverständnis der Module
   - Einstiege ins Theaterspiel (Modul A)
   - Szenische Themenarbeit (Modul B)
   - Pädagogische Regie (Modul C)
  start: {{A0_START}}
  ende: {{A0_END}}
  ort: |
   {{DAY_VENUE_ADDRESS}}
  ablauf: |
   Fr. 18:00-20:00 _online_
   So. 09:30-19:00
  mit: {{A0_TRAINER}}
 a3_{{ITEM_ID_A3}}:
  ctype: event
  shortcode: a3
  title: Raumlauf-Animation und Impro-Training **Wege entstehen beim Gehen**
  tag: Sa./So. {{A3_TAG}} + online-Abend
  image: 
   url: https://res.cloudinary.com/little-papillon/image/upload/w_400/v1676101054/dasei/wege_entstehen_beim_gehen.jpg
   caption: Foto den Fuß setzen
  body: |
   Nichts kann das Ganz-Auf-Sicht-Gestellt-Sein der Bühnensituation besser vorwegnehmen, als ein einfacher 'Raumlauf'; Jene Übung, in der sich Teilnehmer mit einem konkreten 'Geh-Auftrag' kreuz und quer durch den Raum bewegen. Ein gründliches Verstehen des Geschehens ist nicht nur hilfreich, um den Raumlauf ordentlich anleiten zu können, sondern eröffnet immer neue Einblicke auf das Agieren im Bühnenraum.
  start: {{A3_START}}
  ende: {{A3_END}}
  ort: |
   {{DAY_VENUE_ADDRESS}}
  ablauf: |
   Sa. 09:30-18:30
   So. 09:00-15:00
   Di., {{A3_ONLINE_DATE}} 18:00-21:00 _online_
  mit: {{A3_TRAINER}}
---

<!-- PUBLISH-FROM-HERE -->

```

---

## Generated Files for M18/N18

### M18E - München Tageskurs 2026

**File:** `einstiege-ins-theaterspiel_m18e.md`

**Variable Values (M17E +1 year):**

| Variable | M17E Value | M18E Value (+1 year) |
|----------|------------|---------------------|
| SHORTCODE | m17e | m18e |
| ODOO_REF | M17E | M18E |
| CITY | München | München |
| START_DATE | 2025-10-10 | 2026-10-09 |
| END_DATE | 2025-12-09 | 2026-12-08 |
| START_DATE_SHORT | 10.10 - 9.12.2025 | 9.10 - 8.12.2026 |
| YEAR | 2025 | 2026 |
| YEAR_PLUS_3 | 2028 | 2029 |
| VENUE_ADDRESS | Schwanthalerstraße 91<br>80336 München | Schwanthalerstraße 91<br>80336 München |
| FEE_DEADLINE | 1.10.2025 | 1.10.2026 |
| CANCEL_DEADLINE | 1. Okt 2025 | 1. Okt 2026 |
| ADVICE_MONTH | Okt | Okt |
| MONTH_RANGE | OKT - DEZ | OKT - DEZ |

**Event Dates (all +1 year):**

| Event | M17E Dates | M18E Dates |
|-------|-----------|------------|
| A1 | 2025-10-10 to 2025-10-14 | 2026-10-09 to 2026-10-13 |
| A2 | 2025-10-24 to 2025-10-28 | 2026-10-23 to 2026-10-27 |
| A0 | 2025-10-31 to 2025-11-02 | 2026-10-30 to 2026-11-01 |
| A3 | 2025-12-06 to 2025-12-16 | 2026-12-05 to 2026-12-15 |
| A4 | 2026-06-27 to 2025-06-30 | 2027-06-26 to 2027-06-29 |
| A5 | 2026-07-24 to 2026-07-28 | 2027-07-23 to 2027-07-27 |

---

### M18B - Burgstallmühle Blockseminar 2026

**File:** `einstiege-ins-theaterspiel_m18b.md`

**Variable Values (M17B +1 year):**

| Variable | M17B Value | M18B Value (+1 year) |
|----------|------------|---------------------|
| SHORTCODE | m17b | m18b |
| ODOO_REF | M17B | M18B |
| START_DATE | 2025-09-25 | 2026-09-24 |
| END_DATE | 2025-12-16 | 2026-12-15 |
| BLOCK_START_TAG | 25.9. | 24.9. |
| BLOCK_END_TAG | 28.9 | 27.9 |
| FEE_DEADLINE | 18.9.2025 | 17.9.2026 |
| CANCEL_FREE_DEADLINE | 16.9.2025 | 15.9.2026 |
| BLOCK_UNITS | A4/A5 (25.9 bis 28.9.2025) | A4/A5 (24.9 bis 27.9.2026) |
| CANCEL_PARTIAL_DEADLINE | 5.10.2025 | 4.10.2026 |
| REMAINING_UNITS | A3-A5 | A3-A5 |
| PAYMENT_SCHEDULE | 2 Raten 18. Sept, 2 Raten 6. Okt, 1 Rate 10. Nov 2025 | 2 Raten 17. Sept, 2 Raten 5. Okt, 1 Rate 9. Nov 2026 |
| DAY_VENUE_ADDRESS | Schwanthalerstraße 91<br>80336 München | Schwanthalerstraße 91<br>80336 München |

---

### N18E - Nürnberg Tageskurs 2026

**File:** `einstiege-ins-theaterspiel_n18e.md`

Same structure as M18E but with:
- SHORTCODE: n18e
- ODOO_REF: N18E
- CITY: Nürnberg
- VENUE_ADDRESS: (Nürnberg venue - TBD from N17E)

---

### N18B - Burgstallmühle Blockseminar (Nürnberg variant) 2026

**File:** `einstiege-ins-theaterspiel_n18b.md`

Same structure as M18B but with:
- SHORTCODE: n18b
- ODOO_REF: N18B
- Day sessions in Nürnberg instead of München

---

## Generation Script

### Node.js Template Generator

```javascript
// scripts/generate_course.js
const fs = require('fs');
const path = require('path');

function addYearToDate(dateStr, years = 1) {
  const date = new Date(dateStr);
  date.setFullYear(date.getFullYear() + years);
  return date.toISOString().split('T')[0];
}

function generateCourse(templatePath, outputPath, variables) {
  let template = fs.readFileSync(templatePath, 'utf8');
  
  for (const [key, value] of Object.entries(variables)) {
    const regex = new RegExp(`\\{\\{${key}\\}\\}`, 'g');
    template = template.replace(regex, value);
  }
  
  fs.writeFileSync(outputPath, template);
  console.log(`Generated: ${outputPath}`);
}

// Example usage for M18E
const m18e_vars = {
  SHORTCODE: 'm18e',
  ODOO_REF: 'M18E',
  CITY: 'München',
  START_DATE: '2026-10-09',
  END_DATE: '2026-12-08',
  START_DATE_SHORT: '9.10 - 8.12.2026',
  YEAR: '2026',
  YEAR_PLUS_3: '2029',
  VENUE_ADDRESS: 'Schwanthalerstraße 91\n   80336 München',
  FEE_DEADLINE: '1.10.2026',
  CANCEL_DEADLINE: '1. Okt 2026',
  ADVICE_MONTH: 'Okt',
  MONTH_RANGE: 'OKT - DEZ',
  COURSE_PREFIX: 'M',
  // Event dates
  A1_START: '2026-10-09T18:00',
  A1_END: '2026-10-13T21:00',
  A1_TAG: '11.10. ganztags',
  A1_TRAINER: 'Hans Dönitz',
  // ... more event variables
  ITEM_ID_A1: '2178',  // Increment from M17E
  ITEM_ID_A2: '2190',
  ITEM_ID_A0: '2328',
  ITEM_ID_A3: '2346',
  ITEM_ID_A4: '2294',
  ITEM_ID_A5: '2294',
};

generateCourse(
  'templates/course_e_variant.mdc.template',
  'content/agenda/einstiege-ins-theaterspiel_m18e.md',
  m18e_vars
);
```

---

## Implementation Checklist

- [ ] Create `templates/` directory in Nuxt project
- [ ] Save E-Variant template as `course_e_variant.mdc.template`
- [ ] Save B-Variant template as `course_b_variant.mdc.template`
- [ ] Create generation script `scripts/generate_course.js`
- [ ] Generate M18E file with +1 year dates
- [ ] Generate M18B file with +1 year dates
- [ ] Generate N18E file (need N17E source for Nürnberg venue)
- [ ] Generate N18B file
- [ ] Verify all `odoo_product_ref` fields are set
- [ ] Create corresponding Odoo products (M18E, M18B, N18E, N18B)

---

## Date Calculation Notes

The M17 courses use these patterns (dates for 2025):
- **E-Variant (Tageskurs):** Oct-Dec same year, then A4/A5 in following summer
- **B-Variant (Block):** Sept start with 4-day block at Burgstallmühle, then Oct-Dec

For M18/N18 (2026), shift all dates by exactly +1 year, accounting for:
- Weekday alignment (find nearest equivalent weekend)
- Block seminar at Burgstallmühle should be Thu-Sun

---

*This document provides templates for code automation to generate future course files.*
