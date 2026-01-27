# Sprint Plan: DASEi Launch — Design Sprint

**Sprint Start**: 2026-02-08 (SUN)  
**Demo Target**: 2026-02-10 (TUE) 11:00  
**Status**: 🔴 Not Started  
**Prerequisite**: Current sprint (JAN 26 - FEB 7) completed  
**Goal**: UI design and polish for dasei1/dasei2 customer-facing launch

---

## Context

This is a focused **3-day design sprint** following the main development sprint. By this point:
- dasei1 + dasei2 should be technically running (deployed THU JAN 30)
- GraphQL/VueJS decision should be made (Fork A completed)
- Content work should be in progress (Fork B)

---

## Timeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SPRINT: FEB 8-10 (Design & Demo)                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  SUN 08: Design conceptualization (few hours)                               │
│  MON 09: Design implementation                                              │
│  TUE 10: Demo prep → 11:00 TEAM PRESENTATION                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  POST-DEMO: FEB 10-13 (Full Implementation)                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  2-3 days full-run implementation                                           │
│  Final architecture decision based on demo feedback                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Production Goals (THU JAN 30)

### Minimum Viable Production

| Feature | Status | Notes |
|---------|--------|-------|
| dasei1 website accessible | 🔴 | Einstiege portal |
| dasei2 website accessible | 🔴 | Grundstufe portal |
| Event sync working | 🔴 | SharePoint → Odoo |
| Event locations configured | 🔴 | Down-sync from SP |
| Basic event listing | 🔴 | Visitors can see events |
| Registration flow | 🔴 | Basic signup works |
| Customer redirect from dasei.eu | 🔴 | Transition path |

### Nice-to-Have for THU

| Feature | Status | Notes |
|---------|--------|-------|
| Event packages purchasable | 🔴 | Modul A, B, C, D |
| Partner login routing | 🔴 | Based on dasei_domaincode |
| Styled templates | 🔴 | Rough UI adaptation |

---

## Architecture Decision: Pending

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  OPTION A: Full Odoo                                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  • Website templates only                                                   │
│  • QWeb for all UI                                                          │
│  • Simplest, fastest to production                                          │
│  • Limited interactivity                                                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  OPTION B: Partly VueJS                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  • Odoo for backend + some pages                                            │
│  • VueJS widgets for interactive components                                 │
│  • GraphQL for data fetching                                                │
│  • Medium complexity                                                        │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  OPTION C: Major VueJS (Advanced)                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  • Odoo as headless backend                                                 │
│  • Full VueJS SPA frontend                                                  │
│  • GraphQL API layer                                                        │
│  • Most flexible, highest effort                                            │
│  • Realistic? TBD after Fork A exploration                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Decision Point**: After THU production deploy + Fork A exploration

---

## Sprint Tasks (FEB 8-10)

### SUN FEB 8: Design Conceptualization

- [ ] **D1**: Review production state, identify gaps
- [ ] **D2**: Sketch dasei1 landing page layout
- [ ] **D3**: Sketch dasei2 dashboard/events view
- [ ] **D4**: Define customer journey from dasei.eu
- [ ] **D5**: Decide: Odoo templates vs VueJS components
- [ ] **D6**: Create wireframes/mockups

### MON FEB 9: Design Implementation

- [ ] **I1**: Implement dasei1 landing template
- [ ] **I2**: Implement dasei2 events listing
- [ ] **I3**: Event detail page styling
- [ ] **I4**: Registration form styling
- [ ] **I5**: Navigation/header components
- [ ] **I6**: Mobile responsiveness check

### TUE FEB 10: Demo Prep

- [ ] **P1**: Test all user flows
- [ ] **P2**: Prepare demo script
- [ ] **P3**: Document known issues
- [ ] **P4**: Backup production state
- [ ] **P5**: 11:00 PRESENTATION

---

## Fork Tracks (FEB 3-7)

### Fork A: GraphQL → VueJS

| Task | Description | Status |
|------|-------------|--------|
| FA1 | Review graphql_theaterpedia schema | 🔴 |
| FA2 | Add event package queries | 🔴 |
| FA3 | Test with Vue client prototype | 🔴 |
| FA4 | Evaluate complexity vs benefit | 🔴 |

### Fork B: Content Work

| Task | Description | Status |
|------|-------------|--------|
| FB1 | Event descriptions/teasertext | 🔴 |
| FB2 | Module A-D product descriptions | 🔴 |
| FB3 | Welcome/info pages content | 🔴 |
| FB4 | Email templates | 🔴 |

---

## Blocking Questions

| ID | Question | Status | Resolution |
|----|----------|--------|------------|
| BQ1 | Full-odoo vs partly-vuejs vs major-vuejs? | 🔴 Open | Decide after Fork A |
| BQ2 | dasei.eu redirect strategy? | 🔴 Open | DNS vs iframe vs proxy |
| BQ3 | User authentication flow? | 🔴 Open | Odoo login vs external |

---

## Dependencies from Current Sprint

From [2026-01-26_sprint_agenda_dasei.md](2026-01-26_sprint_agenda_dasei.md):

- [x] Event packages module working
- [x] 4 Grundkurs products created
- [ ] Event locations sync
- [ ] SharePoint-drives-updates mode tested
- [ ] Website templates foundation

---

## Progress Log

| Date | Task | Status | Notes |
|------|------|--------|-------|
| 2026-01-27 | Sprint plan created | ✅ | Timeline defined |

---

## Post-Demo Implementation (FEB 10-13)

To be planned after demo feedback. Estimated 2-3 days full implementation.

**Possible focus areas:**
- Production hardening
- Missing features from demo feedback
- Performance optimization
- Content completion
- User testing fixes

---

*Created: 2026-01-27*  
*Last Updated: 2026-01-27*
