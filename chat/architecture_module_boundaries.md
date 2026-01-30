# Module Boundaries

**Type**: master  
**Stage**: task  
**Original Prompts**: [intro](2026-01-30-agenda_extended_intro.md), [core](2026-01-30-agenda_extended_core.md)

---

## Module Architecture

| Module | Purpose | Depends On |
|--------|---------|------------|
| `crearis` | Core fundamentals, agenda.line model | base, event, product |
| `agenda_dasei` | DASEi-specific: event types, YAML export | crearis |
| `crearis_sharepoint` | MS Graph sync (renamed from crearis_agenda) | crearis |
| `crearis_event_package` | Product-as-module packaging | crearis |

---

## Ownership Matrix

| Concept | Module | Rationale |
|---------|--------|-----------|
| `agenda.line` model | crearis | Core infrastructure |
| Line types (session, meeting, milestone, info, action) | crearis | Generic, reusable |
| Line providers (events, posts, products) | crearis | Generic infrastructure |
| Event type templates (A1, LR, AA...) | agenda_dasei | DASEi-specific codes |
| YAML/MDC export | agenda_dasei | DASEi static site specific |
| MS Graph sync | crearis_sharepoint | Optional integration |
| Course packaging (a,b,c,d products) | crearis_event_package | Optional structure |

---

## Decision Principle

**"Don't struggle with module dependencies early"**

When in doubt about where code belongs:
1. Start in `crearis` (the base)
2. Move to domain module later if clearly specific
3. Refactor is cheap when models are right

---

## Naming Changes

| Old Name | New Name | Reason |
|----------|----------|--------|
| `event.session.line` | `agenda.line` | More general, not tied to sessions |
| `crearis_agenda` | `crearis_sharepoint` | Clearer purpose (MS sync) |

---

## Related Documents

- [chapter_architecture](chapter_architecture.md) — Chapter index
- [agenda_model](agenda_model.md) — Line types and providers detail
