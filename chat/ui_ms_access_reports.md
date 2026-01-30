# MS Access Report Analysis

**Type**: master  
**Stage**: task  
**Original Prompts**: [images](2026-01-30-agenda_extended_images.md)

---

## Purpose

**LOW PRIORITY for reproduction** — These reports are design reference only.

Use to understand:
- General design approach (3-col, lines & squares)
- Data relationships (sub-event grouping)
- Information hierarchy

Actual implementation will use simpler Odoo views + website card patterns.

---

## Key Finding: Sub-Event Logic

**From Agenda_Main report: 2 event types grouped together**

This reveals the sub-event pattern:
- Parent event (e.g., "Block 1") groups child events
- Example: A1+A2 shown as single block in schedule
- Important for agenda.line model design

```
Block 1 (Parent)
├── A1: Am Anfang war der Kreis (Do. 19:00-21:30, Fr. 09:00-18:30)
└── A2: Die Bühne kommt von selbst (Sa. 09:00-18:00, So. 09:00-15:00)
```

---

## Report Types

| Report | Image | Purpose |
|--------|-------|---------|
| **Agenda Main** | ms_access_report-1_agenda_main.png | Event schedule table |
| **Agenda Cover** | ms_access_report-2_agenda_cover.png | Contract cover page |
| **Portfolio Main** | ms_access_report-3_portfolio_main.png | Participant progress table |
| **Portfolio Cover** | ms_access_report-4_portfolio_cover.png | Portfolio cover page |

---

## Design Principles (from user guidance)

> "3-cols-design, sizing and alignment could give some good basic ideas. 
> It is all done in lines and squares, no round stuff, should play well with odoo views."

### Key Aesthetic Rules

1. **Grid-based layout** — 3-column structure
2. **Lines and squares** — No rounded corners, clean geometric
3. **Consistent sizing** — Aligned columns, predictable spacing
4. **Plays with Odoo** — Bootstrap-compatible, table-friendly

---

## Analysis Needed

### Agenda Main (Schedule Table)
- [ ] Column structure (date, event, location, instructor?)
- [ ] Header styling (background, borders)
- [ ] Row alternation pattern
- [ ] Time format presentation
- [ ] Module grouping (A, B, C, D sections?)

### Agenda Cover (Contract)
- [ ] Logo placement
- [ ] Participant info block
- [ ] Course details block  
- [ ] Typography hierarchy
- [ ] Signature/date area

### Portfolio Main (Progress Table)
- [ ] Unit tracking columns
- [ ] Status indicators
- [ ] Progress visualization
- [ ] Note/comment areas

### Portfolio Cover
- [ ] Title hierarchy
- [ ] Summary statistics area
- [ ] Period/date range display

---

## Migration Target: Odoo QWeb Reports

### Template Structure

```xml
<template id="report_agenda_contract">
    <t t-call="web.html_container">
        <t t-foreach="docs" t-as="doc">
            <t t-call="web.external_layout">
                <!-- Cover page -->
                <div class="page">
                    <div class="row">
                        <div class="col-8">
                            <!-- Participant info -->
                        </div>
                        <div class="col-4">
                            <!-- Course summary -->
                        </div>
                    </div>
                </div>
                <!-- Schedule page -->
                <div class="page">
                    <table class="table table-sm">
                        <!-- Event rows -->
                    </table>
                </div>
            </t>
        </t>
    </t>
</template>
```

### CSS Considerations

```css
/* Lines and squares aesthetic */
.report-table {
    border: 1px solid #333;
    border-radius: 0;  /* No rounded corners */
}

.report-table th,
.report-table td {
    border: 1px solid #333;
    padding: 4px 8px;
}

/* 3-column grid */
.report-row {
    display: grid;
    grid-template-columns: 1fr 2fr 1fr;
    gap: 0;
}
```

---

## Questions for Image Review

When reviewing the actual images:

1. **Color scheme**: Black/white only or any accent colors?
2. **Font choices**: Serif or sans-serif? Size hierarchy?
3. **Line weights**: Thin or bold borders? Header emphasis?
4. **Whitespace**: Tight or generous padding?
5. **Module markers**: How are A, B, C, D modules distinguished?

---

## Related Documents

- [workflow_email_templates](workflow_email_templates.md) — Contract email references these reports
- [products_dasei_abcd](products_dasei_abcd.md) — Module structure to display
