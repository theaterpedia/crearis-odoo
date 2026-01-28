# Implementation Scenarios: Online Conferencing

*Created: 2026-01-28*  
*Context: Q1 - Where to store conference data and how to integrate*

---

## Current State Analysis

### Existing Stubs Found

**1. `event.track.location` (crearis extension)**

```python
# From crearis/models/location.py
class Location(models.Model):
    _inherit = "event.track.location"
    
    type = fields.Selection([
        ("location.venue", "venue"),
        ("location.office", "office"),
        ("location.nature", "nature"),
        ("location.street", "street"),
        ("space.msteams", "online (teams)"),  # ← MS Teams ready
        ("space.jitsi", "online (jitsi)")
    ])
    
    # MS Teams fields (from view)
    site_id = fields.Char('MS Site ID')
    list_id = fields.Char('MS List ID')
    drive_id = fields.Char('MS Drive ID')
```

**2. `res.company` (schedule config)**

```python
# From crearis/models/res_company.py
online_provider = fields.Selection([
    ('msteams', 'Microsoft Teams'),
    ('zoom', 'Zoom'),
    ('jitsi', 'Jitsi Meet'),
    ('other', 'Other'),
], default='msteams')
```

**3. Product (event_package concept - mentioned but not seen)**

Hans mentioned: "Team + channel already known via product!"

This suggests products store MS Teams team/channel info for automated conference creation.

---

## Related Action Plan Items

| Task | Description | Context |
|------|-------------|---------|
| L32 | Online Sessions View | List all online sessions across events |
| L33 | Room support in shortcodes | `_VENUE:ROOM_` format |
| L35 | MS Teams adapter | Acquire meeting links for online sessions |
| L36 | Store conference URLs | In session data |

---

## Scenario A: Conference per Event (Simple)

**Concept:** One conference link per event, stored on `event.event`.

```
┌─────────────────────────────────────────────────┐
│                  event.event                    │
│  conference_url = "https://teams.microsoft..."  │
│  conference_provider = "msteams"                │
└─────────────────────────────────────────────────┘
```

**Mockup - Event Form:**
```
┌─────────────────────────────────────────────────────────────┐
│ Event: Grundkurs A - März 2026                              │
├─────────────────────────────────────────────────────────────┤
│ Conference:                                                 │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Provider: [MS Teams ▼]                                  │ │
│ │ URL: https://teams.microsoft.com/l/meetup-join/...      │ │
│ │ [🔗 Create Meeting] [📋 Copy Link]                       │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Pros:**
- Simple implementation
- Works for single-session events
- One link shared with all attendees

**Cons:**
- Hybrid events have 4 online sessions → one link for all?
- No per-session conference (different days, different meetings)
- Doesn't match reality: "Tuesday's call is different from Friday's"

**Storage:**
| Entity | Fields |
|--------|--------|
| event.event | `conference_url`, `conference_provider` |

---

## Scenario B: Conference per Session Line (JSONB-driven)

**Concept:** Conference URLs stored inside `schedule_data.sessions[]` JSONB.

```
schedule_data = {
  "sessions": [
    {
      "date": "2026-03-13",
      "type": "online",
      "conference_url": "https://teams.microsoft.com/...",
      "conference_id": "19:meeting_abc..."
    },
    {
      "date": "2026-03-17",
      "type": "online", 
      "conference_url": "https://teams.microsoft.com/...",
      "conference_id": "19:meeting_xyz..."
    }
  ]
}
```

**Mockup - Event Schedule Tab:**
```
┌─────────────────────────────────────────────────────────────┐
│ Parsed Sessions:                                            │
│ ┌─────┬────────────┬─────────────┬───────────┬────────────┐ │
│ │ Day │ Date       │ Time        │ Type      │ Conference │ │
│ ├─────┼────────────┼─────────────┼───────────┼────────────┤ │
│ │ 🌐 FRI │ 2026-03-13 │ 18:00-20:00 │ online   │ [🔗 Link]  │ │
│ │ 📍 SAT │ 2026-03-14 │ 09:00-18:00 │ venue    │ -          │ │
│ │ 🌐 TUE │ 2026-03-17 │ 18:00-21:00 │ online   │ [🔗 Link]  │ │
│ └─────┴────────────┴─────────────┴───────────┴────────────┘ │
│                                                             │
│ [🔄 Acquire All Meeting Links]                              │
└─────────────────────────────────────────────────────────────┘
```

**Pros:**
- Each online session has its own link
- GraphQL-native (just serve the JSONB)
- Write-back to SharePoint as `oschedule_data`
- MS Access / Power Automate can read per-session data

**Cons:**
- Conference URLs in JSONB → not easily searchable
- No foreign key to Teams meeting (just URL string)
- Requires custom adapter logic (not standard Odoo)

**Storage:**
| Entity | Fields |
|--------|--------|
| schedule_data.sessions[] | `conference_url`, `conference_id`, `conference_provider` |

---

## Scenario C: Conference via event.track.location (Track-Based)

**Concept:** Use existing `event.track.location` model. Each track has a location, location has conference integration.

```
┌─────────────────────────────────────────────────────────────┐
│              event.track.location                           │
│  name = "DASEi Online Space"                               │
│  type = "space.msteams"                                    │
│  site_id = "abc123"                                        │
│  team_id = "team-xyz"  (NEW)                               │
│  channel_id = "channel-123"  (NEW)                         │
└─────────────────────────────────────────────────────────────┘
           │
           │ location_id
           ▼
┌─────────────────────────────────────────────────────────────┐
│                    event.track                              │
│  event_id = 123                                            │
│  name = "FR 18:00 - Intro Session"                         │
│  location_id = (DASEi Online Space)                        │
│  conference_url = "https://teams.microsoft.com/..."        │
└─────────────────────────────────────────────────────────────┘
```

**Mockup - Track Location Configuration:**
```
┌─────────────────────────────────────────────────────────────┐
│ Event Track Location: DASEi Online Space                    │
├─────────────────────────────────────────────────────────────┤
│ Name: [DASEi Online Space          ]                       │
│ Type: [Online (Teams) ▼]                                   │
│                                                             │
│ ┌─ MS Teams Configuration ─────────────────────────────┐   │
│ │ Site ID:    [abc-123-def                          ]  │   │
│ │ Team ID:    [19:team-xyz@thread.tacv2             ]  │   │
│ │ Channel ID: [19:channel-123@thread.tacv2          ]  │   │
│ │ Drive ID:   [drives/b!xyz...                      ]  │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                             │
│ Companies: [DASEi] [x]                                     │
└─────────────────────────────────────────────────────────────┘
```

**Pros:**
- Uses standard Odoo event.track architecture
- Conference config reusable across events
- Clean separation: location has MS Teams config, track has meeting URL
- website_event_track integration (agenda views)

**Cons:**
- Requires creating tracks (heavy)
- Overkill for simple "FR online, SA venue" patterns
- Existing `event.track.location` was "half-dormant"

**Storage:**
| Entity | Fields |
|--------|--------|
| event.track.location | `type`, `site_id`, `team_id`, `channel_id` |
| event.track | `location_id`, `conference_url` |

---

## Scenario D: Conference via Product (Adapter Pattern)

**Concept:** Products define conference adapters. Events inherit via `event_product_id`.

Hans said: "Team + channel already known via product!"

```
┌─────────────────────────────────────────────────────────────┐
│                    product.template                         │
│  name = "D2 Werkstatt Regie"                               │
│  ms_team_id = "19:team-werkstatt@..."                      │
│  ms_channel_id = "19:channel-regie@..."                    │
│  conference_adapter = "msteams"                            │
└─────────────────────────────────────────────────────────────┘
           │
           │ event_product_id
           ▼
┌─────────────────────────────────────────────────────────────┐
│                    event.event                              │
│  name = "D2 Werkstatt Regie - März 2026"                   │
│  event_product_id → (D2 Werkstatt Regie)                   │
│  # Conference acquired via product's team/channel          │
└─────────────────────────────────────────────────────────────┘
```

**Mockup - Product Configuration:**
```
┌─────────────────────────────────────────────────────────────┐
│ Product: D2 Werkstatt Regie                                 │
├─────────────────────────────────────────────────────────────┤
│ [Sales] [Inventory] [Conference] [...]                     │
│                                                             │
│ Conference Adapter: [MS Teams ▼]                           │
│                                                             │
│ ┌─ MS Teams Settings ──────────────────────────────────┐   │
│ │ Team:    [Werkstatt Regie              ] [🔍 Lookup] │   │
│ │ Channel: [Termine & Ankündigungen      ] [🔍 Lookup] │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                             │
│ ✓ Auto-create meetings for online sessions                 │
│ ✓ Post schedule updates to channel                         │
└─────────────────────────────────────────────────────────────┘
```

**Pros:**
- Centralized config per product type
- "Werkstatt Regie" events always use same team/channel
- Power Automate can watch product's channel
- Matches DASEi's SP structure (product ↔ team mapping)

**Cons:**
- Requires event_package implementation
- Products don't naturally map to MS Teams
- Some events might need different channels

**Storage:**
| Entity | Fields |
|--------|--------|
| product.template | `ms_team_id`, `ms_channel_id`, `conference_adapter` |
| event.event | `event_product_id` (links to product) |
| schedule_data.sessions[] | `conference_url` (acquired from product) |

---

## Scenario E: Hybrid (Recommended)

**Concept:** Combine JSONB storage (B) with Product-based adapter (D).

```
┌─────────────────────────────────────────────────────────────┐
│                    product.template                         │
│  ms_team_id, ms_channel_id, conference_adapter             │
└─────────────────────────────────────────────────────────────┘
           │
           │ provides adapter config
           ▼
┌─────────────────────────────────────────────────────────────┐
│                    event.event                              │
│  event_product_id → (product)                              │
│  schedule_data.sessions[] ← conference URLs populated here │
└─────────────────────────────────────────────────────────────┘
           │
           │ synced to
           ▼
┌─────────────────────────────────────────────────────────────┐
│                 event.session.line                          │
│  conference_url (display in views)                         │
└─────────────────────────────────────────────────────────────┘
```

**Flow:**
1. Product has team/channel config
2. Event linked to product
3. On "Acquire Meeting Links" action:
   - For each online session in `schedule_data`
   - Call MS Graph API using product's team/channel
   - Create meeting, store URL in session
4. `event.session.line` displays the URL

**Mockup - Acquisition Flow:**
```
┌─────────────────────────────────────────────────────────────┐
│ Event: D2 Werkstatt Regie - März 2026                       │
├─────────────────────────────────────────────────────────────┤
│ Product: D2 Werkstatt Regie                                │
│ Conference Adapter: MS Teams (via product)                 │
│                                                             │
│ Online Sessions:                                            │
│ ┌────────────┬─────────────┬───────────────────────────────┐│
│ │ Date       │ Time        │ Conference                    ││
│ ├────────────┼─────────────┼───────────────────────────────┤│
│ │ 2026-03-13 │ 18:00-20:00 │ ⚠️ No link                    ││
│ │ 2026-03-17 │ 18:00-21:00 │ ⚠️ No link                    ││
│ └────────────┴─────────────┴───────────────────────────────┘│
│                                                             │
│ [🔄 Acquire Meeting Links from MS Teams]                    │
│                                                             │
│ After acquisition:                                          │
│ ┌────────────┬─────────────┬───────────────────────────────┐│
│ │ Date       │ Time        │ Conference                    ││
│ ├────────────┼─────────────┼───────────────────────────────┤│
│ │ 2026-03-13 │ 18:00-20:00 │ ✅ [Join Meeting]             ││
│ │ 2026-03-17 │ 18:00-21:00 │ ✅ [Join Meeting]             ││
│ └────────────┴─────────────┴───────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

**Storage Summary:**
| Entity | Fields | Purpose |
|--------|--------|---------|
| `res.company` | `online_provider` | Default for company |
| `product.template` | `ms_team_id`, `ms_channel_id`, `conference_adapter` | Per-product config |
| `event.event` | `event_product_id` | Links to product |
| `schedule_data.sessions[]` | `conference_url`, `conference_id` | Per-session URLs |
| `event.session.line` | `conference_url` | Searchable/displayable |
| `event.track.location` | `type`, MS Teams fields | **Future:** if promoting to tracks |

---

## Implementation Recommendation

### Phase 1: JSONB Storage (Now)

- Add `conference_url` to `schedule_data.sessions[]` schema
- Add `conference_url` field to `event.session.line`
- Display in Schedule Tab and Online Sessions view

### Phase 2: Product Adapter Config (Next Sprint)

- Add `conference_adapter`, `ms_team_id`, `ms_channel_id` to `product.template`
- Inherit config on event via `event_product_id`

### Phase 3: MS Graph Integration (Future)

- Implement `_acquire_conference_links()` method
- Call MS Graph API to create online meetings
- Store URLs in `schedule_data.sessions[]`
- Sync to SharePoint via `oschedule_data`

### Phase 4: Track Promotion (Optional)

- "Create Tracks from Sessions" button
- Full `event.track` + `event.track.location` integration
- For events needing speaker/stage management

---

## Where to Store What (Summary Table)

| Data | Entity | Rationale |
|------|--------|-----------|
| Default online provider | `res.company` | Company-wide default |
| Team/channel mapping | `product.template` | Product = recurring event type = team |
| Adapter selection | `product.template` | Different products might use Zoom vs Teams |
| Per-session conference URL | `schedule_data.sessions[]` | JSONB for GraphQL, SP write-back |
| Searchable conference URL | `event.session.line` | O2M for Odoo views |
| MS Teams site/list IDs | `event.track.location` | Only if using tracks (dormant for now) |

---

*Ready for discussion.*
