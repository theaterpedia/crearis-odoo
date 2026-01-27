# Quick Reference Docs (Sprint Context)

*Created: 2026-01-27*  
*Purpose: 3-day context retention before FORK*  
*Action: REVIEW and DEEPEN before Fork A starts*

---

## DOC-3: package_only Field Behavior

**Location**: `crearis_event_package/models/event_event.py`

### What it does
- `package_only = True` → Event cannot be sold individually (no tickets)
- `package_only = False` → Normal event, individual ticket sales allowed

### Auto-set Logic
When event created AND:
1. `use_event_packages` enabled on website/company
2. Event's `event_type_id` is in any `product.template.package_event_type_ids`

→ Then `package_only` defaults to `True`

### Constraints
- Cannot enable `package_only` if `event_ticket_ids` not empty
- UI shows warning when event is in active package purchases

### View Location
`crearis_event_package/views/event_event_views.xml` - Tickets page

---

## DOC-4: cid/slug/cidSlug Architecture (SPEC)

**Location**: `crearis/models/event.py`, `crearis/models/blog.py`

### The Three Fields

| Field | Purpose | Example | Editable |
|-------|---------|---------|----------|
| `cid` | Stable xmlid-style identifier | `dasei.event-a1__123` | NEVER after creation |
| `slug` | SEO-friendly URL segment | `am_anfang_war_der_kreis` | Manual only (via button) |
| `cid_slug` | Combined permalink | `dasei.event-a1__123__am_anfang_war_der_kreis` | No (computed) |

### CID Format (SPEC)

**With use_template_codes=True:**
```
{domain}.event-{template_code}__{id}
→ dasei.event-a1__123
```

**With use_template_codes=False:**
```
{domain}.event__{id}
→ dasei.event__123
```

**OLD format (deprecated, DO NOT USE):**
```
dasei.event-evnt__123  ❌
```

### Slug Behavior (SPEC)
- Auto-generated on creation from `name`
- **Does NOT auto-update** when name changes (preserves permalinks!)
- Editable via explicit "Edit Slug" button in UI
- Normalization: lowercase, umlauts → ascii, special chars → underscore

### cidSlug Format
```
{cid}__{slug}
→ dasei.event-a1__123__am_anfang_war_der_kreis
```

### GraphQL Interface (SPEC)
```graphql
type Event {
  cid: String!      # "dasei.event-a1__123"
  slug: String!     # "am_anfang_war_der_kreis"
  cidSlug: String!  # "dasei.event-a1__123__am_anfang_war_der_kreis"
}
```

### Implementation Reference
- `_compute_cid()` - `{domain}.event-{template_code}__{id}`
- `_compute_slug()` - slugify name, only on creation
- `_compute_cid_slug()` - `{cid}__{slug}`
- `action_regenerate_slug()` - manual re-slug from current name

---

## DOC-5: Sysreg Bitmask System (Pattern)

**Location**: Various models (`event.stage`, registration states)

### Why Sysreg?

1. **VueJS sister project** uses sysreg full-scope for state management
2. **GraphQL layer** will expose sysreg for frontend state handling
3. **Future logic** for categories vs flags distinction

### Base Sysreg Values (ALL ENTITIES)

| Value | Bits | Name | Label DE | Scope |
|-------|------|------|----------|-------|
| 1 | 0-2 | new | Neu | Category |
| 8 | 3-5 | demo | Demo | Category |
| 64 | 6-8 | draft | Entwurf | Category |
| 512 | 9-11 | confirmed | Bestätigt | Category |
| 4096 | 12-14 | released | Freigegeben | Category |
| 32768 | 15 | archived | Archiviert | Single bit |
| 65536 | 16 | trash | Papierkorb | Single bit |

**Categories (1-4096)**: Mutually exclusive workflow stages  
**Flags (32768+)**: Can combine with categories via bitmask

### Entity-Specific Extensions

Entities can ADD values within categories or define pipe_end states:

| Entity | Extended Values | Notes |
|--------|----------------|-------|
| event.stage | 8192 (completed), 12288 (cancelled) | pipe_end stages |
| event.registration | 12288 (cancel), 16384 (no_show), 20480 (partial) | attendance outcomes |

### Two Implementation Strategies

**Strategy A: Separate Model (Event Stages)**
```python
# event.stage model uses sequence field AS sysreg
class EventStage(models.Model):
    _name = 'event.stage'
    sequence = fields.Integer()  # THIS IS the sysreg value
    
# Lookup by sysreg (sequence)
stage = EventStage.search([('sequence', '=', 64)], limit=1)
event.stage_id = stage
```

**Strategy B: Selection Field (Registration States)**
```python
# Selection field with sysreg mapping dict
state = fields.Selection([
    ('draft', 'Draft'),      # sysreg 64
    ('open', 'Confirmed'),   # sysreg 512
    ('done', 'Attended'),    # sysreg 4096
])

# Mapping dict for sync
REGISTRATION_STATE_SYSREG = {
    'new': 1, 'demo': 8, 'draft': 64, 'open': 512,
    'done': 4096, 'cancel': 12288, 'no_show': 16384, 'partial': 20480
}
```

### Sync Value
- SharePoint `StatusLookupId` → map to `sysreg` → find Odoo record/state
- Decoupled from Odoo sequences and XML IDs

### GraphQL Exposure
```graphql
type EventStage {
  sysreg: Int!  # Frontend uses this for state logic
  name: String!
}
```

---

## DOC-6: Event Stages Sysreg Mapping

**Location**: `crearis/data/event_stage_data.xml`

### The 7 Event Stages (VERIFIED 2026-01-27)

| Sysreg | Sysreg Name | Stage EN | Stage DE | SP IDs (AGENDA_DASEI) | Notes |
|--------|-------------|----------|----------|----------------------|-------|
| 1 | new | new | neu | 4 | Initial entry |
| 8 | demo | planned | vorgemerkt | 9, 2, 1, 21, 22 | Internal pre-planning |
| 64 | draft | booked | geplant | 13, 11, 12, 31, 35 | Internally confirmed |
| 512 | confirmed | announced | angekündigt | 14, 17, 3, 10, 25 | "published-far-in-the-future" |
| 4096 | released | current | aktuell | 19, 15, 16, 18, 33 | "published-hot" |
| 8192 | completed | completed | vollständig | 30 | Base Odoo "done" |
| 12288 | cancelled | cancelled | gestrichen | 7, 36 | pipe_end=True |
| 32768 | archived | — | — | — | Via Odoo `active=False` |
| 65536 | trash | — | — | 34 | Via Odoo `active=False` |

### SharePoint Mapping (plan_planungsstatus)
In `agenda_dasei/models/sync_events.py`:
```python
# Map SharePoint StatusLookupId to sysreg stage value
# Primary IDs are first, alternates follow
SP_STATUS_TO_STAGE_SYSREG = {
    4: 1,      # → new
    9: 8,      # → planned (demo)
    13: 64,    # → booked (draft)
    14: 512,   # → announced (confirmed)
    19: 4096,  # → current (released)
    30: 8192,  # → completed
    7: 12288,  # → cancelled
    # ... alternates
}
```

### Database Verification
```sql
SELECT id, name, sequence FROM event_stage ORDER BY sequence;
-- id=1: new (1), id=2: planned (8), id=30: booked (64),
-- id=3: announced (512), id=31: current (4096),
-- id=4: completed (8192), id=5: cancelled (12288)
```

### i18n
Translations in `crearis/i18n/de.po` and `cs.po` - uses JSONB format.

### Notes for agenda_dasei

**Sync exclusions:**
- We do NOT sync sysreg 1, 8 (SP IDs: 4, 2, 1, 9, 21, 22) — SharePoint has pre-planning strategies (templating, scenarios) that would confuse Odoo
- We do NOT sync archived (32768) or trash (65536) at the moment

**SP ID mapping:**
- The "SP IDs" column maps to `plan_veranstaltungen.status` (⚠️ TODO: verify field name — may have obscure/automated name)
- First value is the "Hauptstatus" (primary status)
- Non-Hauptstatus values indicate data issues → should resolve to Odoo tags

**Stage behavior:**
- **completed** (Durchgeführt): `fold=True` by default
- **cancelled** (Abgesagt): `fold=True` by default
- **archived/trash**: Implemented via Odoo `active=False` (not stages but flags) — GraphQL can translate if needed, but standard is to hide them

### 🔴 Late-Round Task: Non-Hauptstatus → Tags

When SP status is not in the Hauptstatus list, create an Odoo tag to flag the data issue for review.

---

## DOC-8: Registration States Sysreg Mapping

**Location**: `crearis/models/event_registration.py`

### Extended States (VERIFIED 2026-01-27)

Registration states use the **SAME sysreg bitmask** as event stages!

| State | SP ID | Sysreg | Label EN | Label DE | SP Title | Description |
|-------|-------|--------|----------|----------|----------|-------------|
| new | 12 | 1 | offer | Angebot | __Angebot | — |
| demo | 5 | 8 | proposal | vorbehaltlich | (vorbehaltlich) | tendenziell angemeldet |
| draft | 1 | 64 | unconfirmed | unbestätigt | (angemeldet) | angemeldet (noch ohne Rückbestätigung) |
| open | 13 | 512 | confirmed | bestätigt | : angemeldet | angemeldet (mit Rückbestätigung) |
| done | 3 | 4096 | attended | vollständig | : vollständig | vollständige Teilnahme ohne relevante Fehlzeiten |
| cancel | 8 | 12288 | canceled | storniert | (storniert) | Teilnahme wurde rechtzeitig im Voraus abgesagt |
| no_show | 6 | 16384 | absent | abwesend | : abwesend | Abmeldung nach der Meldefrist z.B. wegen Krankheit |
| partial | 4 | 20480 | partial | teilweise | : teilweise | Teilnahme nur am Kernprogramm mit relevanten Fehlzeiten |

**SP Title conventions:**
- `(...)` = parentheses indicate "not yet final" states
- `: ...` = colon prefix indicates "final/attendance" states  
- `__...` = underscore prefix indicates "pre-workflow" states

### Full SharePoint plan_teilnahmestatus Table

| SP ID | SP Title | Sync? | Odoo State | Notes |
|-------|----------|-------|------------|-------|
| 1 | (angemeldet) | ✅ | draft | angemeldet (noch ohne Rückbestätigung) |
| 3 | : vollständig | ✅ | done | vollständige Teilnahme ohne relevante Fehlzeiten |
| 4 | : teilweise | ✅ | partial | Teilnahme nur am Kernprogramm mit relevanten Fehlzeiten |
| 5 | (vorbehaltlich) | ✅ | demo | tendenziell angemeldet |
| 6 | : abwesend | ✅ | no_show | Abmeldung nach der Meldefrist z.B. wegen Krankheit |
| 8 | (storniert) | ✅ | cancel | Teilnahme wurde rechtzeitig im Voraus abgesagt |
| 9 | _A_Variante | ❌ | — | SP-only: scenario variant |
| 10 | _B_Variante | ❌ | — | SP-only: scenario variant |
| 11 | _C_Variante | ❌ | — | SP-only: scenario variant |
| 12 | __Angebot | ✅ | new | Pre-registration offer |
| 13 | : angemeldet | ✅ | open | angemeldet (mit Rückbestätigung) |
| 14 | XXXX_(Leitung) | ❌ | — | SP-only: vorläufig unbenutzt |
| 15 | XXXX : Leitung | ❌ | — | SP-only: vorläufig unbenutzt |
| 16 | XXXX : geleitet | ❌ | — | SP-only: vorläufig unbenutzt |

### Asymmetric Sync Strategy (agenda_dasei)

**SP → Odoo (mode 1/2):**
- Only sync IDs: 1, 3, 4, 5, 6, 8, 12, 13 (the 8 main states)
- Skip IDs: 9, 10, 11, 14, 15, 16 (scenario/special states)
- **Effect**: Filters down ~80% of records — no pre-planning scenarios or late-after-event states

**Odoo → SP (mode 3, future):**
- Odoo CAN set ANY state including skipped ones
- **Use case**: Setting a state on Odoo triggers SharePoint business logic
- Example: Setting a scenario variant state triggers SP workflows

**Rationale:**
- Odoo = standardized Theaterpädagogik business logic (generic)
- SharePoint = DASEi-specific scenarios (specialized)
- Registration "scenarios" offloaded to SharePoint

### 🟡 Wishlist: Bescheinigung Field (PRIO 3)

SP has `Bescheinigung` (Yes/No) column for certificate eligibility:
- Only IDs 3 (: vollständig) and 4 (: teilweise) have `Bescheinigung=Yes`
- Maps to `done` and `partial` — the "attendance confirmed" outcomes
- **Future**: Add `certificate_eligible` computed field to Odoo

### SharePoint Mapping Code
```python
STATUS_TO_REGISTRATION_STATE = {
    12: 'new',      # __Angebot
    5: 'demo',      # (vorbehaltlich)
    1: 'draft',     # (angemeldet)
    13: 'open',     # : angemeldet
    3: 'done',      # : vollständig
    8: 'cancel',    # (storniert)
    6: 'no_show',   # : abwesend
    4: 'partial',   # : teilweise
}

# IDs to skip (SP-only scenarios/special states)
SP_TEILNAHMESTATUS_SKIP = [9, 10, 11, 14, 15, 16]
```

---

## DOC-11: Referent → User Mapping

**Location**: `agenda_dasei/models/sync_referenten.py`

### Flow
```
SharePoint plan_referenten
    ↓
    PersonLookupId → ms_contact_id → res.partner
    ↓
    res.partner.user_ids[0] → res.users
    ↓
event.event.user_id = matched user
```

### Key Fields
- **SharePoint**: `Hauptreferent` column with `PersonLookupId`
- **Filter**: `ms_referenten_filter` on company (SharePoint list filter)
- **Target**: `event.event.user_id` (responsible user)

### Sync Logic
1. Fetch referenten from SP with PersonLookupId expanded
2. Match to partner via `ms_contact_id`
3. If partner has portal user → set as event.user_id
4. If no match → log warning, leave user_id empty

### Why?
Events need a responsible user for:
- Notifications
- Dashboard filtering

---

## DOC-12: Altering System Stages (Migration Pattern)

**Location**: `crearis/migrations/16.0.1.1.0/pre-migrate.py`, `crearis/data/event_stage_data.xml`

### The Challenge

Odoo 16 has base event stages (ids 1-5) that we needed to:
1. **Rename** - change English names (done → completed)
2. **Re-sequence** - use sysreg bitmask values (1, 8, 64, 512, 4096, 8192, 12288)
3. **Add custom stages** - "booked" (id 30), "current" (id 31)
4. **Delete duplicates** - old stages (ids 24-29) from previous attempts
5. **Migrate translations** - preserve German/Czech in po-files

### Issues Solved (~5 problems)

**Issue 1: JSONB Name Format**
```sql
-- WRONG: causes array corruption on subsequent updates
UPDATE event_stage SET name = '"new"' WHERE id = 1;

-- CORRECT: proper translated field format
UPDATE event_stage SET name = '{"en_US": "new"}'::jsonb WHERE id = 1;
```
Odoo 16 translated fields use JSONB objects like `{"en_US": "value"}`.
Using plain JSON strings causes ORM corruption.

**Issue 2: Duplicate Stage IDs**
Production had old stages (24-29) from previous module attempts.
Migration must check and migrate events before deleting:
```python
# Map old → new before delete
stage_mapping = {24: 1, 25: 3, 26: 31, 27: 4, 28: 5, 29: 4}
for old_id, new_id in stage_mapping.items():
    cr.execute("UPDATE event_event SET stage_id = %s WHERE stage_id = %s", (new_id, old_id))
```

**Issue 3: XMLID Cleanup**
Must delete `ir_model_data` records for old stages before deleting stages:
```python
cr.execute("""
    DELETE FROM ir_model_data 
    WHERE model = 'event.stage' 
    AND module = 'crearis' 
    AND res_id IN (24, 25, 26, 27, 28, 29)
""")
```

**Issue 4: po-file References**
Translations must use correct XMLID format:
```po
#: model:event.stage,name:event.event_stage_new
msgid "new"
msgstr "neu"

#: model:event.stage,name:crearis.event_stage_booked
msgid "booked"
msgstr "geplant"
```
Note: Base Odoo stages use `event.event_stage_*`, custom stages use `crearis.event_stage_*`.

**Issue 5: Sequence vs Sysreg**
The `sequence` field is used for kanban ordering AND as sysreg value:
```python
sequence_updates = [
    (1, 1),      # new: sysreg 1
    (8, 2),      # planned: sysreg 8
    (512, 3),    # announced: sysreg 512
    (8192, 4),   # completed: sysreg 8192
    (12288, 5),  # cancelled: sysreg 12288
]
```

### The Final 7 Stages

| Stage | ID | XMLID | Sysreg/Seq | German |
|-------|-----|-------|------------|--------|
| new | 1 | event.event_stage_new | 1 | neu |
| planned | 2 | event.event_stage_booked | 8 | vorgemerkt |
| booked | 30 | crearis.event_stage_booked | 64 | geplant |
| announced | 3 | event.event_stage_announced | 512 | angekündigt |
| current | 31 | crearis.event_stage_current | 4096 | aktuell |
| completed | 4 | event.event_stage_done | 8192 | vollständig |
| cancelled | 5 | event.event_stage_cancelled | 12288 | gestrichen |

### Migration Script Structure (pre-migrate.py)

```python
def migrate(cr, version):
    # Step 1: Check events on old stages
    # Step 2: Migrate events to new stages
    # Step 3: Delete old XMLIDs
    # Step 4: Delete old stages
    # Step 5: Update sequences to sysreg values
    # Step 6: Update names to JSONB format
    # Step 7: Create/update custom stages (30, 31)
```

### Key Lessons

1. **Always use JSONB objects** for translated fields: `{"en_US": "value"}`
2. **Clean XMLIDs before deleting** records
3. **Migrate dependent records first** (events) before deleting stages
4. **Use pre-migrate** (not post) for schema changes before XML data loads
5. **Test on production copy** - dev database often lacks duplicate IDs

### Git History
- `a672032` - Initial event_stage_data.xml with sysreg values
- `5f18552` - pre-migrate.py with plain JSON names (buggy)
- `6ae8ab6` - Fixed to JSONB object format `{"en_US": "..."}`

---

## Review Checklist (Before Fork)

- [ ] DOC-3: package_only constraints clear?
- [ ] DOC-4: cid vs slug vs cid_slug purpose understood?
  - Note: T-CID-5 (blog.post slug) → DEFERRED to Fork A (GraphQL phase)
- [ ] DOC-5: Sysreg pattern - why bitmasks?
- [x] DOC-6: Event stage SP mapping → VERIFIED 2026-01-27 (see full table above)
- [x] DOC-8: Registration states → VERIFIED 2026-01-27 (sysreg matches stages)
- [ ] DOC-11: Referent flow - partner → user clear?
- [x] DOC-12: Stage migration pattern - JSONB format critical!

---

*To deepen: Add code snippets, edge cases, error handling after Fork review*
