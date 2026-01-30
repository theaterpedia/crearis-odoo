# Chapter 2: Agenda Model

**Stage**: task  
**Type**: chapter

---

## Abstract

The agenda model extends session-lines into a unified timeline system. Line-items come from 3 providers (events, posts, products) and have 5 types (session, meeting, milestone, info, action). Source-of-truth questions and bidirectional sync patterns are critical architectural decisions.

---

## Master Documents

| Title | Description | Stage | Notes | Version |
|-------|-------------|-------|-------|---------|
| [agenda_lines_architecture](agenda_lines_architecture.md) | Rename session.line → agenda.line, type field | task | | |
| [agenda_line_providers](agenda_line_providers.md) | Events, Posts, Products as providers | task | | |
| [agenda_line_types](agenda_line_types.md) | session, meeting, milestone, info, action | task | | |
| [agenda_sync_patterns](agenda_sync_patterns.md) | JSON ↔ SQL sync, locked_edits, reverse-sync | task | | |
| [products_dasei_abcd](products_dasei_abcd.md) | DASEi course modules A,B,C,D structure | task | From website | |

---

## Key Decisions

### 1. Naming & Module Ownership
- **Rename**: `event.session.line` → `agenda.line` 
- **Rationale**: Distinguishes from all known Odoo models, explains crearis/agenda relationship
- **Module rename**: `crearis_agenda` → `crearis_sharepoint` (agenda is core of crearis)
- **Ownership**: `agenda.line` lives in **crearis** module (fundamental)
- **Extensions**: crearis_event_package and agenda_dasei can extend the model

### 2. Line-Item Providers
| Provider | Relation | Notes |
|----------|----------|-------|
| Events | Primary | Entity #1, events drive everything |
| Posts | Secondary | Own lifecycle, chatter works |
| Products | Secondary | A,B,C,D modules |
| ~~Companies~~ | Excluded | They "have" agendas, not "are" agendas |
| ~~Users/Partners~~ | Excluded | They are actors, not providers |

### 3. Line Types
| Type | Mode | Description |
|------|------|-------------|
| session | online/venue | In-presence slot (default) |
| meeting | online/venue | Outside event, prep/planning |
| milestone | — | Status documentation, stats/checks |
| info | — | Email sent, or portal news |
| action | — | Text, document, decision, Q&A |

### 4. Source of Truth
**Open question**: Is schedule_json or session-line-table the source?
- Option A: JSON is source → table is readonly, edits via JSON
- Option B: Table is source → JSON is representation for GraphQL
- **Proposed**: Bidirectional with `locked_edits` flag for controlled table-edits

### 5. Sub-Event Grouping (from MS Access reports)
**Finding**: 2 event types grouped together as parent-child

```
Block 1 (Parent event)
├── A1: Am Anfang war der Kreis
└── A2: Die Bühne kommt von selbst
```

This implies agenda.line needs:
- `parent_line_id` or grouping field
- Display logic for collapsed/expanded views
- See [ui_ms_access_reports](ui_ms_access_reports.md) for visual reference

---

## Source References

- [Intro](2026-01-30-agenda_extended_intro.md) lines 70-100: Naming and line-item-providers
- [Intro](2026-01-30-agenda_extended_intro.md) lines 25-45: Sync pattern discussion
- [Images](2026-01-30-agenda_extended_images.md): MS Access report sub-event grouping
