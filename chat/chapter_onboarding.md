# Chapter 6: Onboarding

**Type**: chapter

---

## Abstract

Onboarding follows 3 clear transitions: public website → Odoo customer → Odoo participant → VueJS app. The checkout stepper on dasei.eu hands off to Odoo controllers. Contract states progress from pending (cancellable) through evaluation to full participant.

---

## Master Documents

| Title | Description | Stage | Notes | Version |
|-------|-------------|-------|-------|---------|
| [onboarding_three_transitions](onboarding_three_transitions.md) | Discovery→Interest→Commitment | task | Core flow | |
| [onboarding_checkout_stepper](onboarding_checkout_stepper.md) | Vue stepper + mdc_generator | task | Inside-out architecture | |
| [onboarding_contract_states](onboarding_contract_states.md) | Pending→evaluation→participant | task | | |
| [onboarding_infrastructure](onboarding_infrastructure.md) | Same IP, SSO, NGINX routing | task | | |

---

## Quick Reference

### The 3 Transitions
1. **Discovery → Interest**: Website visitor → INFO-Teaser registrant
2. **Interest → Commitment**: Attendee → Course registrant (checkout stepper)
3. **Trial → Continuation**: Basistag participant → Full course commitment

### Contract States
| State | Cancellation |
|-------|--------------|
| Pending | Easy cancel before first event |
| Active (10-day) | Cancel until day 10 after Basistag |
| Evaluation | Either party can stop |
| Participant | Full program, monthly payments |

---

## Source References

- [Journeys](2026-01-30-agenda_extended_journeys.md): Karo, Ida, Jolanda stories
- [Intro](2026-01-30-agenda_extended_intro.md): Infrastructure notes
