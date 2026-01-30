# Email Templates

**Type**: master  
**Stage**: task  
**Original Prompts**: [emails](2026-01-30-agenda_extended_emails.md)

---

## Overview

Email templates for the three customer transitions plus newsletter.

---

## 1. Event Confirmation (INFO-Teaser)

**Trigger**: After INFO-Teaser registration  
**Subject pattern**: `Bestätigung: {EVENT_TYPE} {WEEKDAY} {DATE} {TIME}`

**Content structure**:
1. Personal greeting with full name
2. Event details (date, time, type) + what to expect
3. Preparation link (course overview PDF)
4. Meeting details (Teams URL, ID, passcode)
5. Detailed agenda table (time slots 18:00-20:00)
6. "What's next" section (Basistag dates + locations)
7. CTA link to full info
8. Fallback phone dial-in

**Key fields**: 
- `partner.name`
- `event.date_begin`, `event.name`, `event.event_type_id`
- `event.meeting_url`, `event.meeting_id`, `event.meeting_passcode`
- Next Basistag events query

---

## 2. Course Contract Email

**Trigger**: After course registration confirmed  
**Subject**: `Einstiege ins Theaterspiel: Vertrag, Seminarplan, Rechnung`

**Attachments**:
- Contract + timetable (PDF, currently MS Access report)
- Invoice + payment plan

**Content structure**:
1. Welcome, request to verify contract
2. Payment options note (installments vs one-time)
3. Course start/end dates highlighted
4. "Expect email 7 days before each event"
5. Counseling session scheduling (1-month window)
6. Module B-D preview (reserved slots)
7. Date conflict flexibility note

**Key fields**:
- `partner.name`
- `registration.course_start_date`, `registration.course_end_date`
- `registration.payment_plan`
- Linked events for the course
- Counseling window dates

---

## 3. Newsletter (Monthly)

**Trigger**: Monthly (manual or scheduled)  
**Subject**: `DAS Ei - INFOS`

**Sections**:
- Tagline (Theaterpedia, Episoden, Offenes Programm...)
- Seasonal intro
- Feature announcement (conference, major event)
- Content release (episodes, multimedia)
- Special offers (Stipendien)
- Events listing with dates + prices
- Unsubscribe link

**CTA pattern**: `dasei.eu/r/{code}/m/{id}` (tracking links)

**Event listing format**: `{DATE_RANGE} - {TITLE} ({LOCATION})`

**Price note**: `Die Teilnahme an einem Kurs im Offenen Programm kostet EUR 190,00`

---

## MS Access Report Templates (Legacy)

From images: `ms_access_report-1_agenda_main.png`, `ms_access_report-2_agenda_cover.png`

These show the contract/timetable format still generated from MS Access:
- Cover page with participant name, course details
- Main page with event schedule table
- Module overview (A, B, C, D progression)

**Migration path**: Generate these as PDF from Odoo using QWeb reports.

---

## Source Files

- [2026-01-30-agenda_extended_emails.md](2026-01-30-agenda_extended_emails.md) — Original email examples
- [files/agenda_extended/ms_access_report-*.png](files/agenda_extended/) — Report screenshots
