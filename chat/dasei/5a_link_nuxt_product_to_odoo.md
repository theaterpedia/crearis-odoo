# 5a: Link Nuxt Product Page to Odoo Product

*Proposal Document - Created: 2025-12-27*

---

## Overview

This document describes how to link the Nuxt.js website product pages (course markdown files) to Odoo products, enabling the website to display product data fetched from the Odoo backend.

## Current State

### Nuxt Product Files
Course products are defined as `.mdc` files under `/content/agenda/`:
- `einstiege-ins-theaterspiel_m17e.md` (Tageskurs München)
- `einstiege-ins-theaterspiel_m17b.md` (Blockseminar)
- etc.

Each file contains YAML frontmatter with:
```yaml
shortcode: m17e
ctype: course
title: Einstiege ins Theaterspiel
items:
  a1_1178:
    ctype: event
    shortcode: a1
    ...
```

### Odoo Products
The `agenda_dasei` module defines course products in `product.template` with:
- `course_program`: M/N/ZR/ZT
- `course_year`: e.g., "17", "18"
- `course_type`: block/day/profile
- `ms_contact_id`: SharePoint sync ID

## Proposed Solution

### Step 1: Add Odoo Product Reference to Markdown Files

Add `odoo_product_ref` field to frontmatter that uses convention-based mapping:

```yaml
---
shortcode: m17e
odoo_product_ref: M17E  # Maps to product.template.default_code
...
---
```

**Mapping Convention:**
| Markdown shortcode | odoo_product_ref | Meaning |
|-------------------|------------------|---------|
| `m17e` | `M17E` | München 2025, Tageskurs (E) |
| `m17b` | `M17B` | München 2025, Block (B) |
| `n17e` | `N17E` | Nürnberg 2025, Tageskurs |
| `m18e` | `M18E` | München 2026, Tageskurs |

### Step 2: Create/Configure Odoo Products

In Odoo, create products with matching `default_code`:

```python
# Via Odoo shell or data file
env['product.template'].create({
    'name': 'Einstiege ins Theaterspiel - München Tageskurs 2025',
    'default_code': 'M17E',
    'type': 'service',
    'course_program': 'M',
    'course_year': '17',
    'course_type': 'day',
    'list_price': 1180.00,  # A0 (80) + 5x A1-A5 (5x220)
})
```

### Step 3: Extend Nuxt DataView Components

#### 3a. Create Odoo Product Fetcher Composable

Create `/composables/useOdooProduct.ts`:

```typescript
// Fetch product data from Odoo GraphQL API
export const useOdooProduct = async (productRef: string) => {
  const config = useRuntimeConfig()
  
  // GraphQL endpoint (via VSF/odoogap integration)
  const query = `
    query GetProduct($ref: String!) {
      product(filter: { defaultCode: { eq: $ref } }) {
        id
        name
        defaultCode
        listPrice
        description
        courseProgram
        courseYear
        courseType
        # Event items linked to this product
        events {
          id
          name
          dateBegin
          dateEnd
          location
          schedule
          teasertext
        }
      }
    }
  `
  
  const { data } = await useFetch(config.public.odooGraphqlUrl, {
    method: 'POST',
    body: { query, variables: { ref: productRef } }
  })
  
  return data.value?.product
}
```

#### 3b. Modify DataView.vue to Support Odoo Source

```vue
<script lang="ts" setup>
const props = defineProps({
  src: { type: String, required: true },
  // New: data source selection
  dataSource: {
    type: String as PropType<'markdown' | 'odoo' | 'hybrid'>,
    default: 'markdown'
  }
})

// Fetch markdown content
const { data: mdData } = await useAsyncData('md', () => queryContent(props.src).findOne())

// If hybrid mode, also fetch from Odoo
let odooData = null
if (props.dataSource !== 'markdown' && mdData.value?.odoo_product_ref) {
  odooData = await useOdooProduct(mdData.value.odoo_product_ref)
}

// Merge data (Odoo overrides markdown for dynamic fields)
const productData = computed(() => {
  if (!odooData) return mdData.value
  return {
    ...mdData.value,
    // Override with Odoo data where available
    items: odooData.events?.length ? mapOdooEventsToItems(odooData.events) : mdData.value?.items,
    listPrice: odooData.listPrice,
    // Keep markdown static content
    product: mdData.value?.product,
    details: mdData.value?.details,
  }
})
</script>
```

### Step 4: API Configuration

#### SharePoint API Site (Current Installation)
```
Site: https://dasei.sharepoint.com/sites/api
```

> **Note:** This is different from the sync site (`https://dasei.sharepoint.com/sites/dasei-website`). Once confirmed working, PowerAutomate flows will be refactored to use the new api-site.

#### PowerAutomate Flow URL (New API)
```
https://default430c53e6651e45efa53c004ea96dd2.16.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/e24e854998a44b8990cb883f006b0612/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=dW-If8W3p85RTFP0mE2PD-r0sgu9opFXOmmwKuJ7xwU
```

### Step 5: Odoo GraphQL Schema Extension

Extend the VSF GraphQL schema to expose course products:

```python
# In graphql_theaterpedia module
class ProductQuery(graphene.ObjectType):
    product = graphene.Field(
        ProductType,
        filter=graphene.Argument(ProductFilterInput)
    )
    
    def resolve_product(self, info, filter=None):
        domain = []
        if filter and filter.get('defaultCode'):
            domain.append(('default_code', '=', filter['defaultCode']['eq']))
        
        product = info.context['env']['product.template'].search(domain, limit=1)
        return product if product else None


class ProductType(graphene.ObjectType):
    id = graphene.Int()
    name = graphene.String()
    default_code = graphene.String()
    list_price = graphene.Float()
    course_program = graphene.String()
    course_year = graphene.String()
    course_type = graphene.String()
    events = graphene.List(EventType)
    
    def resolve_events(self, info):
        # Get linked events via event_type or direct relation
        # Implementation depends on how events are linked to products
        pass
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Nuxt.js Website                                   │
│  ┌──────────────────┐         ┌─────────────────────────────────┐  │
│  │ Markdown (.mdc)  │         │ DataView Components              │  │
│  │ - Static content │ ──────► │ - Reads markdown                 │  │
│  │ - odoo_product_  │         │ - Fetches Odoo via GraphQL       │  │
│  │   ref: M17E      │         │ - Merges data (Odoo overrides)   │  │
│  └──────────────────┘         └─────────────────────────────────┘  │
└───────────────────────────────────────┬─────────────────────────────┘
                                        │ GraphQL Query
                                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Odoo Backend                                 │
│  ┌─────────────────────┐    ┌──────────────────────────────────┐   │
│  │ product.template    │    │ event.event                       │   │
│  │ - default_code:M17E │◄──►│ - Linked via event_type or        │   │
│  │ - course_program: M │    │   product relation                │   │
│  │ - list_price: 1180  │    │ - date_begin, date_end            │   │
│  └─────────────────────┘    │ - schedule, teasertext            │   │
│            ▲                 └──────────────────────────────────┘   │
│            │ Sync (master mode)                                      │
└────────────┼────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       SharePoint                                     │
│  Site: https://dasei.sharepoint.com/sites/api                       │
│  - plan_veranstaltungen (events)                                    │
│  - contacts (course products as records starting with _)            │
└─────────────────────────────────────────────────────────────────────┘
```

## Migration Path

### Phase 1: Alpha (Current)
- `dataSource: 'markdown'` - All data from markdown files
- Odoo products created but not yet used by website

### Phase 2: Hybrid
- `dataSource: 'hybrid'` - Markdown for static content, Odoo for dynamic (dates, prices)
- crearis_agenda in `slave` mode - SharePoint drives updates

### Phase 3: Production
- `dataSource: 'odoo'` (optional) - Full Odoo-driven content
- crearis_agenda in `master` mode - Odoo drives updates to both website and SharePoint

## Implementation Checklist

- [ ] Add `odoo_product_ref` field to all course markdown files
- [ ] Create corresponding products in Odoo with matching `default_code`
- [ ] Create `useOdooProduct` composable in Nuxt
- [ ] Extend DataView.vue with `dataSource` prop
- [ ] Extend graphql_theaterpedia with product query
- [ ] Link events to products in Odoo
- [ ] Test hybrid mode
- [ ] Switch crearis_agenda to `master` mode

---

*This document instructs code automation on the Nuxt project.*
