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

### Immediate: Research & Decisions Needed

1. **agenda.line model architecture** (Chapter 2) ← **PRIORITY: START HERE**
   - [ ] Create master doc: agenda_lines_architecture.md
   - [ ] Define fields, relations, computed properties
   - [ ] Decide: JSON source vs table source

2. **Chatter integration exploration** (Chapter 5)
   - [ ] Create master doc: workflow_chatter_integration.md
   - [ ] Which chatter events → agenda.lines?
   - [ ] Leverage Odoo's existing workflow engine

3. **SharePoint table cross-check** (Chapter 7) — **DEFERRED**
   - Revisit only after Odoo planning is sound
   - User will provide more schema then
   - Not a distraction right now

4. **Backoffice sidebar navigation** (Chapter 4)
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

### Reference Files (not yet deeply analyzed)
- ref_sharepoint_plan_veranstaltungen.md
- ref_sharepoint_raeume.md
- ref_dasei_shortcodes.md
- dev_docs_schedule_location.md
- dev_docs_quick_reference.md
