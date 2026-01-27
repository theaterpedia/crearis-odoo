# Implementation Plan: Registration States (sysreg-compatible)

**Date**: 2026-01-26  
**Module**: `crearis` (base), `agenda_dasei` (sync mapping)  
**Status**: ✅ Phase 1 Complete (R1-R5), 🟡 Phase 2-3 Pending  
**Related**: B3 in [action_plan_event_package_integration.md](./2026-01-24-action_plan_event_package_integration.md)

---

## Overview

Extend Odoo's `event.registration` state field with additional states and sysreg compatibility.

### Current Odoo States (Base)

| Value | Label EN |
|-------|----------|
| draft | Unconfirmed |
| open | Confirmed |
| done | Attended |
| cancel | Cancelled |

### Target States (sysreg-compatible)

| Odoo State | Sysreg | SP ID | EN | DE | Notes |
|------------|--------|-------|----|----|-------|
| new | 1 | 12 | offer | Angebot | NEW - pre-registration offer |
| demo | 8 | 5 | proposal | vorbehaltlich | NEW - tentative registration |
| draft | 64 | 1 | unconfirmed | unbestätigt | EXISTS - rename label |
| open | 512 | 13 | confirmed | bestätigt | EXISTS - keep |
| done | 4096 | 3 | attended | vollständig | EXISTS - rename label |
| cancel | 12288 | 8 | canceled | storniert | EXISTS - keep |
| no_show | 16384 | 6 | absent | abwesend | NEW - registered but didn't attend |
| partial | 20480 | 4 | partial | teilweise | NEW - partial attendance |

---

## Implementation Tasks

### Phase 1: Model Extension (crearis module) ✅ COMPLETE

#### R1: Create `event_registration.py` in crearis/models ✅

```python
# crearis/models/event_registration.py

from odoo import models, fields, api

# Sysreg values for registration states
REGISTRATION_STATE_SYSREG = {
    'new': 1,
    'demo': 8,
    'draft': 64,
    'open': 512,
    'done': 4096,
    'cancel': 12288,
    'no_show': 16384,
    'partial': 20480,
}

class EventRegistration(models.Model):
    _inherit = 'event.registration'

    # Override state field with extended selection
    state = fields.Selection(
        selection_add=[
            ('new', 'Offer'),
            ('demo', 'Proposal'),
            # draft, open, done, cancel exist in base
            ('no_show', 'Absent'),
            ('partial', 'Partial'),
        ],
        ondelete={
            'new': 'set default',
            'demo': 'set default',
            'no_show': 'set default',
            'partial': 'set default',
        }
    )

    # Computed sysreg value
    state_sysreg = fields.Integer(
        string='State (sysreg)',
        compute='_compute_state_sysreg',
        store=True,
        help='Sysreg bitmask value for state'
    )

    @api.depends('state')
    def _compute_state_sysreg(self):
        for reg in self:
            reg.state_sysreg = REGISTRATION_STATE_SYSREG.get(reg.state, 0)
```

#### R2: Register model in `__init__.py` ✅

Add `from . import event_registration` to `crearis/models/__init__.py`

#### R3: Add i18n translations ✅

Update `crearis/i18n/de.po` and `crearis/i18n/cs.po` with:
- new → Angebot / Nabídka
- demo → vorbehaltlich / s výhradou
- draft → unbestätigt / nepotvrzený
- open → bestätigt / potvrzený
- done → vollständig / úplný
- cancel → storniert / zrušený
- no_show → abwesend / nepřítomný
- partial → teilweise / částečný

#### R4: Add state workflow constraints (optional)

Define valid state transitions:
```
new → demo → draft → open → done
                  ↘ cancel
              open → no_show
              open → partial
```

---

### Phase 2: Sync Mapping (agenda_dasei module) ✅ COMPLETE

#### R5: Create SharePoint → Odoo state mapping ✅

Implemented in `agenda_dasei/models/sync_registrations.py`:

# SharePoint plan_teilnahmestatus.ID → Odoo state
SP_TEILNAHMESTATUS_TO_STATE = {
    1: 'draft',      # (angemeldet)
    3: 'done',       # : vollständig
    4: 'partial',    # : teilweise
    5: 'demo',       # (vorbehaltlich)
    6: 'no_show',    # : abwesend
    8: 'cancel',     # (storniert)
    12: 'new',       # __Angebot
    13: 'open',      # : angemeldet
}

# IDs to skip (not synced)
SP_TEILNAHMESTATUS_SKIP = [9, 10, 11, 14, 15, 16]
```

#### R6: Implement bidirectional sync

- SharePoint → Odoo: Map `StatusLookupId` to `state`
- Odoo → SharePoint: Map `state` back to `StatusLookupId`

#### R7: Handle "Bescheinigung" flag

SP field `Bescheinigung` (Yes/No) indicates certificate eligibility:
- Only `done` (3) and `partial` (4) have `Bescheinigung=Yes`
- Consider adding `certificate_eligible` computed field in Odoo

---

### Phase 3: GraphQL Extension

#### R8: Expose state_sysreg in GraphQL

Add to `EventRegistration` GraphQL type:
```graphql
type EventRegistration {
  state: String!
  stateSysreg: Int!
  # ... other fields
}
```

---

## Dependencies

| Task | Depends On |
|------|------------|
| R2 | R1 |
| R3 | R1 |
| R4 | R1 |
| R5 | R1 (states must exist) |
| R6 | R5, D38 (registration sync architecture) |
| R7 | R5 |
| R8 | R1 |

---

## SharePoint Reference: plan_teilnahmestatus

| ID | Title | Bescheinigung | Sync? |
|----|-------|---------------|-------|
| 1 | (angemeldet) | No | ✅ → draft |
| 3 | : vollständig | Yes | ✅ → done |
| 4 | : teilweise | Yes | ✅ → partial |
| 5 | (vorbehaltlich) | No | ✅ → demo |
| 6 | : abwesend | No | ✅ → no_show |
| 8 | (storniert) | No | ✅ → cancel |
| 9 | _A_Variante | No | ❌ skip |
| 10 | _B_Variante | No | ❌ skip |
| 11 | _C_Variante | No | ❌ skip |
| 12 | __Angebot | No | ✅ → new |
| 13 | : angemeldet | No | ✅ → open |
| 14 | XXXX_(Leitung) | No | ❌ skip |
| 15 | XXXX : Leitung | No | ❌ skip |
| 16 | XXXX : geleitet | No | ❌ skip |

---

## Testing Checklist

- [ ] New states appear in registration form dropdown
- [ ] State transitions work correctly
- [ ] `state_sysreg` computed correctly for all states
- [ ] German/Czech translations display properly
- [ ] SharePoint sync maps states correctly (both directions)
- [ ] Skipped SP status IDs don't create registrations
- [ ] GraphQL returns `stateSysreg` value

---

## Notes

- State is a Selection field (not a separate model like event.stage)
- `selection_add` extends the base selection without replacing it
- `ondelete` handles module uninstall gracefully
- sysreg values follow the bitmask pattern (powers of 2 for categories)
