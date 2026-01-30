# Chapter 7: Architecture

**Type**: chapter

---

## Abstract

Module boundaries define what belongs in crearis (core) vs agenda_dasei (domain-specific) vs optional integrations. The principle is "don't struggle with dependencies early" — start in crearis, move to domain modules when clearly specific.

---

## Master Documents

| Title | Description | Stage | Notes | Version |
|-------|-------------|-------|-------|---------|
| [architecture_module_boundaries](architecture_module_boundaries.md) | crearis vs agenda_dasei vs sharepoint | task | Key decisions | |
| [architecture_model_design](architecture_model_design.md) | agenda.line, providers, types | task | | |
| [architecture_api_design](architecture_api_design.md) | Controllers, GraphQL integration | task | | |

---

## Quick Reference

### Module Ownership
| Module | Purpose |
|--------|---------|
| `crearis` | Core: agenda.line, line types, providers |
| `agenda_dasei` | DASEi: event types, YAML/MDC export |
| `crearis_sharepoint` | Optional: MS Graph sync |
| `crearis_event_package` | Optional: product packaging |

### Naming Decisions
| Old | New | Reason |
|-----|-----|--------|
| event.session.line | agenda.line | More general |
| crearis_agenda | crearis_sharepoint | Clearer purpose |

---

## Source References

- [Core](2026-01-30-agenda_extended_core.md): Line types, providers
- [Intro](2026-01-30-agenda_extended_intro.md): Module questions
