# Three Customer Transitions

**Type**: master  
**Stage**: task

---

## Overview

Three key transitions mark the customer journey from stranger to participant:

| # | Transition | From | To | Key Action |
|---|------------|------|-----|------------|
| 1 | Discovery → Interest | Website visitor | INFO-Teaser registrant | "Anmeldung zum Info-Teaser" |
| 2 | Interest → Commitment | INFO-Teaser attendee | Course registrant | "Anmeldung Einstiege" |
| 3 | Trial → Continuation | Basistag participant | Full course commitment | "Weiter mit Modul A" |

---

## Transition 1: Discovery → Interest

**Trigger**: User finds DASEi via search, social, referral

**Actions**:
- Browse course information on website
- View checkout stepper (product view)
- Register for INFO-Teaser (free online event)

**System creates**:
- `res.partner` (if new)
- `event.registration` for INFO-Teaser event

**Emails sent**:
- Confirmation with meeting details (Teams link)
- Reminder 1 day before

---

## Transition 2: Interest → Commitment

**Trigger**: After INFO-Teaser, user decides to try

**Actions**:
- Complete checkout stepper (details view)
- Select Basistag date
- Provide contact details
- Accept AGB/Datenschutz

**System creates**:
- `event.registration` for Basistag
- Link to course product (reservation)

**Emails sent**:
- Basistag confirmation with preparation info
- Course overview PDF attachment

---

## Transition 3: Trial → Continuation

**Trigger**: After Basistag, user confirms continuation

**Window**: 10 days after Basistag to withdraw

**Actions**:
- Counseling session (scheduled)
- Contract signing
- First installment payment

**System creates**:
- Full course registration
- Contract document (PDF)
- Invoice with payment plan
- `event.registration` for all course events

**Emails sent**:
- Contract + timetable + invoice
- Individual event reminders (7 days before each)

---

## Dropout Points

| Point | Trigger | System Action |
|-------|---------|---------------|
| After INFO-Teaser | No follow-up | Mark as "info only" |
| Before Basistag | Cancellation request | Cancel registration |
| Within 10 days after Basistag | Withdrawal | Refund minus admin fee |
| After confirmation | Storno request | Apply cancellation policy |

---

## Related Documents

- [onboarding_checkout_stepper](onboarding_checkout_stepper.md) — Technical stepper integration
- [workflow_email_templates](workflow_email_templates.md) — Email content for each transition
