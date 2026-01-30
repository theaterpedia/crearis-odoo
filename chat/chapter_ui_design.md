# Chapter 4: UI Design

**Type**: chapter

---

## Abstract

The UI centers on a 3-tab sidebar navigation (Agenda | Curriculum | Service) that progressively reveals as users advance. Responsive design targets 3 breakpoints with strategic gaps. Odoo defaults are respected where possible; custom components only where necessary.

---

## Master Documents

| Title | Description | Stage | Notes | Version |
|-------|-------------|-------|-------|---------|
| [ui_sidebar_spec](ui_sidebar_spec.md) | 3-tab sidebar, tiles, progressive disclosure | task | Core spec | |
| [ui_responsive_breakpoints](ui_responsive_breakpoints.md) | mobile/tablet/desktop, strategic gaps | task | | |
| [ui_odoo_integration](ui_odoo_integration.md) | Sidebar widget question, bootstrap respect | task | | |
| [ui_vue_components](ui_vue_components.md) | Vue component architecture from dasei.eu | task | DataView, Cards | |
| [ui_ms_access_reports](ui_ms_access_reports.md) | MS Access report migration, 3-col design | task | Lines & squares | |

---

## Quick Reference

### The 3-Tab Sidebar
| Tab | Purpose |
|-----|---------|
| **Agenda** | Timeline of activities |
| **Curriculum** | Portfolio/progress (A,B,C,D) |
| **Service** | Contract, Q&A, issues |

### Progressive Disclosure
| State | Visible Tabs |
|-------|--------------|
| Anmeldung | Service |
| Angemeldet | Agenda |
| Einstiege | Agenda, Service |
| Grundlagenbildung | All 3 tabs |

### Responsive Breakpoints
| Viewport | Columns |
|----------|---------|
| <430px | 1 (mobile) |
| 820-1150px | 2 (tablet) |
| 1150-1366px | 3 (desktop) |

---

## Source References

- [Core](2026-01-30-agenda_extended_core.md) lines 35-55: 3 tab definitions
- [Core](2026-01-30-agenda_extended_core.md) lines 105-150: Responsive specs
- [Images](2026-01-30-agenda_extended_images.md): UI reference images
