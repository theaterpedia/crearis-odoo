# Revisiting "Keep It Simple" - JSONB vs Sessions

*Created: 2026-01-28*  
*Context: Q3 - Did I overrun concerns with the quick decision?*

---

## The Decision Moment

When you said "keep it simple" and decided **not** to implement full sessions right away, I had raised several questions that were left unanswered:

> **My Questions (earlier today):**
>
> 1. **Location sync status:** Is the location sync part now considered done, or do you still need the actual `event.track.location` records created/linked?
>
> 2. **Schedule → event.track:** The parser produces `sessions[]` with `session_type`, `start_time`, `end_time`. Do you want me to implement the actual `event.track` creation from these sessions?
>
> 3. **Website templates priority:** Should I focus on frontend, or is there still backend work blocking?
>
> 4. **GraphQL readiness:** Does the GraphQL schema already expose locations/tracks/sessions?

Your quick "no" to full sessions was reasonable, but let me analyze whether we should **reconsider** or **stay the course**.

---

## What We Built (Current State)

```
SharePoint plan_veranstaltungen
         │
         │ sync
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    event.event                              │
│  sp_textinfo (raw text) ─▶ ScheduleParser ─▶ schedule_data │
│                                                             │
│  schedule_data = {                                         │
│    "sessions": [                                           │
│      {"day": "FRI", "start": "18:00", "type": "online"}   │
│    ],                                                      │
│    "summary": {"has_online": true, "total_hours": 11}     │
│  }                                                         │
│                                                             │
│  Computed fields (stored):                                 │
│  - has_online_sessions                                     │
│  - total_hours, online_hours, venue_hours                  │
│  - session_count                                           │
└─────────────────────────────────────────────────────────────┘
```

**What works:**
- ✅ Parsing text → structured JSONB
- ✅ Shortcode support (`_online_`, `_TANZEREI_`)
- ✅ Summary fields for filtering
- ✅ Test parser in company config
- ✅ Schedule tab in event form

**What's missing:**
- ❌ Session-level list view (shows events, not sessions)
- ❌ Session table in event form (shows raw JSON)
- ❌ Searchable session records
- ❌ Conference URLs per session

---

## Option A: Stay the Course (JSONB + session.line)

**Approach:** Keep JSONB as source of truth, add `event.session.line` for display/search.

```
schedule_data (JSONB)
       │
       │ sync on parse
       ▼
event.session.line (O2M)
       │
       └─▶ Tree views, search, grouping
```

**Pros:**
- JSONB serves GraphQL directly
- Write-back to SharePoint as JSON
- Lightweight display model
- No commitment to heavy framework
- Can promote to tracks later

**Cons:**
- Data duplication (JSONB + records)
- Need to keep in sync
- Two places to update if manual edits needed

**Effort:** ~2h (implement session.line model + views)

---

## Option B: Revert to event.track

**Approach:** Generate `event.track` records directly from parsing.

```
schedule_data (JSONB) ─▶ event.track records
```

**Pros:**
- Standard Odoo model
- Existing views/actions
- Website agenda integration
- Speaker support (if needed later)

**Cons:**
- Track implies "talk" with speaker
- Heavy for simple time slots
- Can't easily serialize back to JSONB
- SharePoint write-back becomes complex
- Overkill for "FR 18:00-20:00 online"

**Effort:** ~3h (rework parsing to create tracks + views)

---

## Option C: Revert to OCA event.session

**Approach:** Install OCA `event_session`, parse into real sessions.

```
schedule_data (JSONB) ─▶ event.session records
```

**Pros:**
- Full session framework
- Separate registration per session
- Mail scheduling per session

**Cons:**
- Way too heavy for our use case
- We don't need per-session registration
- `_inherits` complexity
- Dependency on OCA module

**Effort:** ~4h (install, adapt, integrate)

**Verdict:** ❌ Not recommended. Massive overkill.

---

## Analysis: Was "Keep It Simple" Right?

### What You Wanted

From the original Eleanora requirements + Hans' answers:

> **Q4 - Eleanora's view:** Event-level + click-open-inspect
> - Main view: events with tags/flags
> - Click to expand: see session details
> - **Special view: "All online sessions" line-by-line**

The key phrase is **"line-by-line"**. This requires searchable session records.

### What JSONB Alone Can't Do

```sql
-- This doesn't work with JSONB alone:
SELECT * FROM event_session_line 
WHERE type = 'online' 
  AND date BETWEEN '2026-03-01' AND '2026-03-31'
ORDER BY date, start;
```

JSONB requires complex `jsonb_array_elements()` queries. Standard Odoo tree views can't filter inside JSONB arrays.

### The Middle Path

Your "keep it simple" was right to avoid:
- OCA `event.session` (heavy)
- Full `event.track` integration (heavy)

But we still need **something** for Eleanora's "line-by-line" view.

**`event.session.line`** is that middle path:
- Lightweight (no registration, no workflow)
- Synced from JSONB (JSONB remains source of truth)
- Searchable (standard tree views work)
- Optional (can be deleted/rebuilt anytime)

---

## Recommendation: Keep the Course

**Don't revert.** The JSONB approach is correct for:
- GraphQL serving
- SharePoint write-back
- Flexible schema evolution
- MS Access/Power Automate consumption

**Do add** `event.session.line` as planned:
- Display layer on top of JSONB
- Enables Eleanora's views
- No architectural change needed

### Decision Matrix

| Question | Answer |
|----------|--------|
| Should we revert JSONB parsing? | **No** |
| Should we use OCA event.session? | **No** |
| Should we use event.track? | **Not now** (keep promotion path) |
| Should we add event.session.line? | **Yes** |

---

## Answering the Unanswered Questions

### Q1: Location sync status

**Status:** ✅ Done for events (109 events have `address_id`).

**Not done:** `event.track.location` records. These are dormant and not needed now.

**Recommendation:** Leave `event.track.location` dormant. We use `res.partner` for venues.

### Q2: Schedule → event.track

**Answer:** No. Keep JSONB → `event.session.line` path. Tracks are for conferences.

**Promotion path:** Add "Create Tracks" button later if needed.

### Q3: Website templates priority

**Answer:** Backend first. Eleanora's views are internal Odoo UI, not website.

Frontend (GraphQL → VueJS) can consume `schedule_data` directly - already works.

### Q4: GraphQL readiness

**Status:** Likely needs work. GraphQL should expose `schedule_data` as nested JSON.

**Recommendation:** Defer to after Eleanora views. Internal UI first.

---

## Conclusion

The "keep it simple" decision was **correct**. The JSONB + lightweight session.line approach:

1. **Serves GraphQL** - JSONB is native JSON
2. **Serves SharePoint** - Write-back as `oschedule_data`
3. **Serves Eleanora** - `event.session.line` for list views
4. **Avoids overengineering** - No OCA sessions, no forced tracks
5. **Keeps promotion path** - Can create tracks later if needed

**No revert needed.** Proceed with `event.session.line` implementation.

---

*Ready for discussion.*
