# Chapter 5: Workflows

**Type**: chapter

---

## Abstract

Crearis operates on monthly cycles, not daily task management. Email-based workflows with 2-3 day lags are acceptable. DASEi extends to 3 major cycles per year. The system leverages Odoo's chatter and workflow engine to shape agenda items rather than creating parallel systems.

---

## Master Documents

| Title | Description | Stage | Notes | Version |
|-------|-------------|-------|-------|---------|
| [workflow_monthly_cycle](workflow_monthly_cycle.md) | 4-week pattern: Publish→React→Plan→Prepare | task | | |
| [workflow_yearly_cycles](workflow_yearly_cycles.md) | 3 major cycles at DASEi (Apr/Aug/Dec) | task | | |
| [workflow_chatter_integration](workflow_chatter_integration.md) | Odoo chatter → agenda.lines | task | Key architecture | |
| [workflow_email_templates](workflow_email_templates.md) | Confirmation, contract, newsletter | task | Extracted from production | |

---

## Quick Reference

### Monthly Cycle
| Week | Focus |
|------|-------|
| 1 | Publish (newsletter send) |
| 2 | React (handle responses) |
| 3 | Plan (stats, team talk) |
| 4 | Prepare (website, next cycle) |

### DASEi Yearly Cycles (3x)
- ~April, ~August, ~December
- Batch: payment supervision, website update, planning decisions
- Participants confirm general planning only 3x per year

---

## Source References

- [Core](2026-01-30-agenda_extended_core.md) lines 20-35: Monthly workflow
- [Emails](2026-01-30-agenda_extended_emails.md): Template examples
- [Intro](2026-01-30-agenda_extended_intro.md) lines 55-70: Chatter integration questions
