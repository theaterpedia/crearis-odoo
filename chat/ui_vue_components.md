# Vue Component Architecture

**Type**: master  
**Stage**: task

---

## Component Hierarchy

```
DataView (page or tab component)
├── DataViewProduct (course overview with slider)
│   ├── Heading (h3 with shortcode)
│   ├── MdBlock (product.header markdown)
│   ├── Slider > Slide (for each item)
│   │   └── Columns > Column (image + content)
│   └── ButtonTmp (CTA → details page)
│
├── DataViewDetails (checkout stepper)
│   ├── MdBlock (details.*.header sections)
│   ├── Contact form
│   ├── Checkbox section (AGB, Datenschutz)
│   └── handle_checkout() → POST
│
└── DataViewTabs (tabbed container)
    └── Tab[] → DataView (recursive)
```

---

## Key Components

| Component | Purpose | Data Source |
|-----------|---------|-------------|
| `DataView` | Router between product/details views | ContentQuery (YAML) |
| `DataViewProduct` | Course slider with event items | `data.items`, `data.product` |
| `DataViewDetails` | Checkout stepper flow | `data.details` |
| `DataViewTabs` | Tab container | `tabs[]` prop |
| `CardsGallery` | Event/post card grid | ContentList query |
| `CardEvent` | Event card (image + heading) | `data.image`, `data.heading` |
| `Catalog` | Wrapper from @crearis/ui | slot content |

---

## Data Flow

```
YAML frontmatter (Nuxt Content)
       │
       ▼
 ContentQuery/ContentList
       │
       ▼
   DataView (selects view type)
       │
       ├── view='product' → DataViewProduct
       │                    (slider, items, CTA)
       │
       └── view='details' → DataViewDetails
                            (stepper, checkout)
```

---

## CardsGallery Query Logic

```typescript
// Preset-based filtering
preset === 'agenda' 
  → filter: ctype !== 'course'
  → sort: start ASC (upcoming first)
  
preset === 'blog'
  → filter: path !== '/blog/_dir'
  → sort: date DESC (newest first)
```

---

## Card Design

```css
/* CardEvent.vue */
.card {
  min-width: 21rem;  /* 336px fixed width */
  max-width: 21rem;
  box-shadow: 0px 4px 6px 1px rgba(0,0,0,0.1);
  background-color: var(--color-card-bg);
}

.c-hero:hover::after {
  background-color: var(--color-primary-bg);  /* accent on hover */
}
```

---

## Heading Pattern

Format: `overline // **title**`

Example: `MÜ 4.-6.4 // Kurzbeschreibung **Am Anfang war der Kreis**`

---

## Source Files

Vue components in [files/agenda_extended/](files/agenda_extended/):
- `DataView.vue` — Main router component
- `DataViewProduct.vue` — Product/course view
- `DataViewDetails.vue` — Checkout stepper (438 lines)
- `DataViewTabs.vue` — Tab container
- `CardsGallery.vue` — Card grid with query
- `CardEvent.vue` — Event card component
- `Catalog.vue` — Wrapper from @crearis/ui
