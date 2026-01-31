# Action Plan: Whitepaper Next Steps

**Date**: 2026-01-30  
**Context**: After processing 7 input files into whitepaper structure

---

## Status Summary

### Completed Today
- ✅ Created whitepaper structure (index + 8 chapters)
- ✅ Established conventions (Chapter 0 with master docs)
- ✅ Extracted checkout stepper flow (inside-out architecture)
- ✅ Documented mdc_generator.py YAML export
- ✅ Processed emails → workflow_email_templates.md
- ✅ Processed images → ui_vue_components.md
- ✅ Fetched live product pages → products_dasei_abcd.md
- ✅ Refactored chapters to thin indexes + master docs

### Master Documents Created
| Document | Chapter | Content |
|----------|---------|---------|
| conventions_document_types | 0 | All doc types & rules |
| conventions_staging | 0 | 5-stage progression |
| onboarding_checkout_stepper | 6 | Inside-out, mdc_generator, YAML strategy |
| onboarding_three_transitions | 6 | Discovery→Interest→Commitment |
| workflow_email_templates | 5 | Confirmation, contract, newsletter |
| ui_vue_components | 4 | DataView, Cards, stepper flow |
| architecture_module_boundaries | 7 | crearis vs agenda_dasei |
| products_dasei_abcd | 2 | Course modules A,B,C,D structure |

---

## Next Actions (from Meta document)

### 🚨 BLOCKING: Monday 2026-02-02

**Domain Code Assignment to Events**
- [ ] Investigate: Are domain codes being assigned to `event.event` records?
- [ ] Check: Does SP sync need to be retriggered?
- [ ] Check: Is there logic missing in sync or model?
- **Why blocking**: Domain code system + event grouping requires this data on existing events
- **Context**: See [2026-01-26-action_plan_website_templates.md](2026-01-26-action_plan_website_templates.md) — domain codes control website visibility

---

### Architecture Insight: Courses = Website Experiences

> **Key Principle (2026-01-31)**: Courses should NOT be implemented at model-level. They are "designed" as website experiences with filter-configs on default models.

| Level | Implementation | Example |
|-------|----------------|---------|
| Events | `event.event` model | A1 Kreisanimation München März 2026 |
| Event Types | `event.type` model | A1 Kreisanimation (template) |
| Modules | Website filter + domain_code | "Einstiege ins Theaterspiel" = filter A0-A5 events |
| Courses | Website experience | "Grundlagenbildung" = dasei1→dasei2 journey through A,B,C,D |

**Prototype target**: "Grundlagenbildung" (A),B,C,D as website experience

---

### Immediate: Research & Decisions Needed

1. **agenda.line model architecture** (Chapter 2) ← **PRIORITY: START HERE**
   - [ ] Create master doc: agenda_lines_architecture.md
   - [ ] Define fields, relations, computed properties
   - [ ] Decide: JSON source vs table source

2. **Chatter integration exploration** (Chapter 5)
   - [ ] Create master doc: workflow_chatter_integration.md
   - [ ] Which chatter events → agenda.lines?
   - [ ] Leverage Odoo's existing workflow engine

3. **Meldefrist + Stornierungsfrist as Milestone Examples** (Chapter 2 + Chapter 5)
   - [ ] Create master doc or section: deadlines_meldefrist_stornierung.md
   
   **Meldefrist (Event-level)**:
   - Confirmation deadline per event (A1, A2, A3...)
   - Computed: `event.date_begin - event_type.meldefrist_days_before` (typically 60 days)
   - Participants must confirm or opt-out before this date
   - Batch processed: 2-4 events per 3-month cycle
   - Creates: `agenda.line(type='milestone')` + reminder emails
   
   **Stornierungsfrist (Module/Product-level)**:
   - Cancellation deadline for module purchase
   - Computed: `first_event_attendance_date + 10 days`
   - Before: Customer can cancel, loses only first Kursrate (~EUR 220)
   - After: Module purchase binding, full fee applies
   - Creates: `agenda.line(type='milestone')` on product
   - Syncs: Accounting, consulting, customer portal
   
   **Status**: Meldefrist implemented in SP (not activated). Stornierungsfrist = "10-Tage-Regel" in team doc.

4. **SharePoint table cross-check** (Chapter 7) — **DEFERRED**
   - Revisit only after Odoo planning is sound
   - User will provide more schema then
   - Not a distraction right now

5. **Backoffice sidebar navigation** (Chapter 4)
   - [ ] Create master doc: ui_sidebar_spec.md
   - [ ] "Next actions" functionality investigation
   - [x] MS Access report analysis → [ui_ms_access_reports.md](ui_ms_access_reports.md)

---

### Decisions Made (2026-01-30)

| Question | Answer |
|----------|--------|
| agenda.line vs checkout controller first? | **agenda.line model** |
| SharePoint analysis now? | **No** — defer until Odoo planning solid |
| German content timing? | **After essentials** |
| MS Access report analysis? | **Yes** — 3-col design, lines & squares aesthetic |

---

### Implementation Planning (3 Rounds)

Per Meta document guidance:

| Round | Name | Focus | Timing |
|-------|------|-------|--------|
| **1** | Essentials | Blocking tasks, whitepaper-driven | Next 2-4 weeks |
| **2** | Unlock DASEi | Full A,B,C,D business cycle | After essentials |
| **3** | Build Details | Refinements after production testing | Future |

#### Round 1 Essentials (Blocking Tasks)
- [ ] agenda.line model implementation (crearis module)
- [ ] Checkout controller `/api/v1/checkout` 
- [ ] YAML export extension (odoo_product_id)
- [ ] Basic email templates in Odoo

#### Round 2 Unlock DASEi
- [ ] Full A,B,C,D product configuration
- [ ] Contract PDF generation (replace MS Access)
- [ ] Payment plan / invoice integration
- [ ] Event registration workflow

---

### Content Creation (Before Round 2)

Per Meta document:
> After creating essentials, before 'unlock dasei' → create German text with example interactions for all customer stories

**Input Sources for German Text**:
- [dasei_team_report_de.md](dasei_team_report_de.md) — Key terminology, pricing, 10-Tage-Regel, customer path
- [workflow_email_templates.md](../_meta/Whitepaper/workflow_email_templates.md) — Email patterns
- [products_dasei_abcd.md](../_meta/Whitepaper/products_dasei_abcd.md) — Module structure

**Journeys to document**:
- [ ] Karo's journey (first contact → INFO-Teaser)
- [ ] Ida's journey (Basistag → Module A)
- [ ] Jolanda's journey (Module A → full Grundlagenbildung)
- [ ] Issue-driver scenario
- [ ] Service-worker scenario
- [ ] Instructor scenario

---

## Questions for User

1. **Priority**: Start with agenda.line model or checkout controller?
2. **SharePoint tables**: Should I analyze ref_sharepoint_*.md files now?
3. **German content**: Create example interactions now or after essentials?
4. **MS Access reports**: Want me to analyze the report images for migration?

---

## Files to Reference

### Input Files (processed)
- 2026-01-30-agenda_extended_intro.md ✓
- 2026-01-30-agenda_extended_meta.md ✓
- 2026-01-30-agenda_extended_core.md ✓
- 2026-01-30-agenda_extended_journeys.md ✓
- 2026-01-30-agenda_extended_emails.md ✓
- 2026-01-30-agenda_extended_images.md ✓
- 2026-01-30-agenda_extended_urls_and_code.md ✓
- dasei_team_report_de.md ✓ (German terminology, pricing, customer path)

### Reference Files (not yet deeply analyzed)
- ref_sharepoint_plan_veranstaltungen.md
- ref_sharepoint_raeume.md
- ref_dasei_shortcodes.md
- dev_docs_schedule_location.md
- dev_docs_quick_reference.md
