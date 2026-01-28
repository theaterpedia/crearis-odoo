# Triage: Unresolved Items & Ideas

**Created**: 2026-01-28  
**Purpose**: Collect unresolved tasks from action plans and dev-docs for triage  
**Context**: Pre-cleanup before Customer Journey / Website Templates work  
**Next Action**: Prioritize items into: NOW / NEXT-SPRINT / BACKLOG / DROP

---

## Summary

| Category | Count | Status |
|----------|-------|--------|
| **Blocking / High Priority** | 5 | Need decision |
| **crearis module** | 12 | Mixed completion |
| **agenda_dasei module** | 40+ | Mostly not started |
| **GraphQL backlog** | 23 | Defer to Fork A |
| **Dev-docs gaps** | 6 | Need update |
| **Obsolete / Superseded** | 8+ | Candidates for DROP |

---

## 🔴 BLOCKING / HIGH PRIORITY

Items that block other work or need immediate decision:

### B-1: Production Deploy (S9b.2 - S9b.7)
**Source**: Sprint plan Phase 3b  
**Status**: ❌ Not done (was target JAN 30)  
**Blockers**: External modules update, domain codes setup  
**Decision**: Is THU 30 still realistic? Reschedule?

### B-2: DB2 - event.user_id mapping
**Source**: DASEi action plan DB2  
**Status**: 🟡 Investigation done (S7.5), not implemented  
**Issue**: Most events show user_id=2 (Administrator), need Hauptreferent mapping  
**Decision**: Implement before or after production?

### B-3: Session Lines Testing
**Source**: Just implemented (today)  
**Status**: ✅ Code done, ❌ Not tested in UI  
**Decision**: Verify Schedule tab + Online Sessions menu before moving on

### ~~B-4: Website Templates Action Plan Missing~~ ✅ EXISTS
**Source**: Sprint plan references `2026-01-26-action_plan_website_templates.md`  
**Status**: ✅ File exists - was missed in initial search  
**Content**: Detailed 3-layer architecture (Products → Event Types → Events), W1-W5 tasks

### B-5: Special Shortcodes (PENDING)
**Source**: ref_dasei_shortcodes.md  
**Status**: 🔲 TODO - `_anfrage_`, `_individuell_`, `_reihe_`  
**Impact**: ~30 events with unparseable schedules  
**Decision**: Implement before production or mark as known gap?

---

## 🟡 CREARIS MODULE — Unresolved Tasks

### From action_plan_event_package_integration.md:

| ID | Task | Status | Notes |
|----|------|--------|-------|
| T-CID-1 to T-CID-6 | cid/slug architecture | ✅ DONE | Sprint S5.2 |
| T-UI-1 | Template code visualization | ✅ DONE | Sprint S5.4 |
| T11-T14 | Feature flag hierarchy | ✅ DONE | Sprint S5.5 |
| T8 | Add domain_code to product.template | ❌ Not done | For event packages |
| T9 | Filter package_event_type_ids by domain | ❌ Not done | Package wizard |
| T10 | Event filtering in wizard by domain_code | ❌ Not done | Package wizard |
| T15 | Review SharePoint sync fields on EventType | ❌ Not done | ms_id, ms_synced, ms_version |
| T16 | EventType hierarchy view (template grouping) | ❌ Not done | Nice-to-have |
| T17 | EventType GraphQL template_parent resolver | ❌ Not done | GraphQL backlog |
| T18 | template_config bitmask documentation | ❌ Not done | Dev-docs |
| T19-T23 | Package module completion | ❌ Not done | Wizard, cid, state machine |
| T24-T27 | Sales & registration flow | ❌ Not done | Auto-registration creation |
| T28-T31 | Views & UI improvements | ❌ Not done | EventType tree, dashboard |
| T32-T34 | Security & access rules | ❌ Not done | Package line security |
| T35-T37 | Data & migration | ❌ Not done | Demo data, import strategy |
| T38-T42 | Registration extensions | ⏳ Partial | States done, units/comments not verified |
| T43-T45 | CID review for blog/user/partner | ❌ Not done | Late round |

### Summary for crearis:
- **Done**: cid/slug, feature flags, template viz, registration states
- **Partial**: Registration extensions (states done, fields not verified)
- **Not done**: Domain code on products, wizard improvements, EventType views, security

---

## 🟠 AGENDA_DASEI MODULE — Unresolved Tasks

### Phase 1: SharePoint List Infrastructure (D1-D8)
| ID | Task | Status |
|----|------|--------|
| D1 | Add plan_kurse GUID | ❌ Not done |
| D2 | Add plan_veranstaltungsteilnehmer GUID | ❌ Not done |
| D3 | Create sync_plan_kurse.py | ❌ Not done |
| D4 | Create sync_plan_veranstaltungsteilnehmer.py | ❌ Not done |
| D5 | Register sync models | ❌ Not done |
| D6 | Add cron jobs | ❌ Not done |
| D7 | Add access rights | ❌ Not done |
| D8 | Test SP connection | ❌ Not done |

### Phase 2: Course → Domaincode Mapping (D9-D18)
**Status**: ❌ Not started  
**Question**: Is this still the right approach? Courses as websites?

### Phase 3: Module → Product Mapping (D19-D32)
**Status**: ❌ Not started  
**Depends on**: Phase 2

### Phase 4: Registration Sync (D33-D48)
**Status**: ⏳ D33 (mapping) done, rest not started  
**Blocking**: D38 marked "STOP: provide architecture before implementing"

### Phase 5-7: Loyalty, Bundles, Testing (D49-D68)
**Status**: ❌ Not started  
**Note**: May be deferred to later sprint

### Other DASEi Tasks:
| ID | Task | Status |
|----|------|--------|
| DA1 | Menu restructuring | ✅ Done (S7.3) |
| DB1 | Move out event stages | ✅ Done |
| DB2 | User mapping | 🟡 Investigated, not implemented |
| DL1 | Non-Hauptstatus → tags | ❌ Not done |
| DPa1 | Extract product templates A/B/C/D | ❌ Interactive task |

---

## 🔵 GRAPHQL BACKLOG — Defer to Fork A

All items from `2026-01-28-action_plan_graphql.md`:

| ID | Task | Category |
|----|------|----------|
| G1-G7 | Event package schema extensions | Schema |
| G8-G9 | EventType template system | Schema |
| G10-G11 | Registration extensions | Schema |
| G12-G13 | Domain code / multi-tenant | Filtering |
| G14 | Package edition_code | Schema |
| G15-G18 | Cross-domain package safety | Critical for VueJS |
| G19-G23 | CID / Slug / CidSlug | Permalinks |

**Recommendation**: Keep as-is, defer to Fork A (FEB 3-7)

---

## 📝 DEV-DOCS GAPS

Items that need documentation updates:

### 1. dev_docs_crearis_introduction.md
**Last Updated**: 2026-01-25  
**Gaps**:
- Missing: Schedule parsing (L1-L32 work)
- Missing: Session lines model
- Missing: Location sync
- Update: Module hierarchy diagram incomplete

### 2. dev_docs_quick_reference.md
**Purpose**: 3-day context retention  
**Gaps**:
- DOC-7, DOC-9, DOC-10 mentioned but not filled in
- Missing: Session lines reference
- Missing: Schedule shortcodes reference
- Needs: Code snippets validation

### 3. dev_docs_agenda_dasei.md
**Status**: Not provided in full, appears summarized  
**Needs**: Review for completeness

### 4. dev_docs_crearis_agenda.md
**Status**: Not provided in full, appears summarized  
**Needs**: Review for completeness

### 5. Missing: dev_docs_schedule_parser.md
**Content**: ScheduleParser, shortcodes, session lines, hybrid JSONB architecture  
**Recommendation**: Create new document

### 6. ~~Missing: 2026-01-26-action_plan_website_templates.md~~ ✅ EXISTS
**Referenced by**: Sprint plan  
**Status**: ✅ File exists with detailed content  
**Content**: 3-layer architecture, W1-W5 tasks, Meldefrist backlog

---

## ⚪ CANDIDATES FOR DROP / OBSOLETE

Items that may be superseded or no longer relevant:

### 1. Course → Website mapping (D9-D18)
**Original idea**: SharePoint Kurse → Odoo websites  
**Question**: Is this still correct? Or do courses map to something else?  
**Risk**: May conflict with actual domain_code architecture

### 2. Module → Product sync (D19-D32)
**Original idea**: SharePoint modules → Odoo products automatically  
**Question**: With event packages working, is this still needed?  
**Alternative**: Manual product setup + SharePoint as source-of-truth for events only

### 3. Loyalty program (D49-D54)
**Status**: Not started, may be out of scope for current sprint  
**Decision**: Defer to future sprint?

### 4. Package bundles (D55-D60)
**Status**: Not started  
**Decision**: Part of Customer Journey or separate?

### 5. Old sync fields (T15)
**Fields**: ms_id, ms_synced, ms_version on EventType  
**Question**: Are these used? Or superseded by event-level sync?

### 6. KursLookupId resolution (D15)
**Context**: Bug from 2025-01-23  
**Question**: Still relevant? Or fixed by different approach?

### 7. Duplicate tasks
**Example**: T1-T7 (crearis plan) duplicated in GraphQL plan as G1-G7  
**Action**: Consolidate into GraphQL plan only

### 8. Registration states impl_plan
**File**: 2026-01-26-impl_plan_registration_states.md  
**Status**: States implemented, plan may be obsolete  
**Action**: Mark as DONE or archive

---

## 🎯 TRIAGE DECISIONS NEEDED

### Immediate (Before Website Templates):

1. **B-1**: Reschedule production deploy?
2. **B-3**: Test session lines in UI now?
3. **B-4**: Create website templates action plan?
4. **B-5**: Implement special shortcodes or accept gap?

### Next Sprint:

1. Course/module sync (D9-D32) — keep or redesign?
2. Registration sync (D33-D48) — priority?
3. User mapping (DB2) — implement?

### Backlog (Future):

1. Loyalty/bundles (D49-D60)
2. EventType views (T16, T28)
3. Security review (T32-T34)

### Wishlist (Nice-to-have):

1. **Kanban Template Code Badge** — Show template code (A1, B2, etc.) as clickable badge in bottom-left of kanban card, next to activity icons. When clicked, show info notification. Current xpath for `oe_kanban_bottom_left` doesn't work reliably. Low priority, visual enhancement only.

### Drop Candidates:

1. Duplicate GraphQL tasks (T1-T7 → G1-G7)
2. Old impl plans that are done
3. Course → website mapping (if superseded)

---

## Next Steps

1. **YOU DECIDE**: Which blocking items to resolve first
2. **Update action plans**: Mark done items, remove obsolete
3. **Create website templates plan**: If proceeding with customer journey
4. **Update dev-docs**: After decisions made

---

*Generated by triage analysis on 2026-01-28*
