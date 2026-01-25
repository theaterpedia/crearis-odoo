# Action Plan: GraphQL Updates

**Date**: 2026-01-28  
**Purpose**: Collect GraphQL-related tasks for future implementation  
**Module**: `graphql_theaterpedia`  
**Status**: 📋 Backlog (to be worked on after current sprint)

---

## Overview

This action plan collects GraphQL schema updates and API improvements that arise during the `crearis` and `agenda_dasei` work but are not immediately blocking. These tasks are scheduled for later implementation.

---

## Task Collection

### 🔷 Schema Extensions (from crearis_event_package)

> Migrated from [2026-01-24-action_plan_event_package_integration.md](./2026-01-24-action_plan_event_package_integration.md)

- [ ] **G1**: Extend `EventType` GraphQL object with template_code fields (`is_template_code`, `template_parent_id`, `template_cimg`, `template_teasertext`, `template_units`, `template_heading`)
- [ ] **G2**: Add `company_id` to `EventType` GraphQL for multi-tenant filtering
- [ ] **G3**: Create new `ProductPackage` GraphQL type (or extend `Product`) for `event_package` detailed_type
- [ ] **G4**: Add `package_event_type_ids` relation to Product GraphQL
- [ ] **G5**: Create `PackageEventLine` GraphQL type for traceability queries
- [ ] **G6**: Add GraphQL query `eventPackages` to fetch products of type `event_package`
- [ ] **G7**: Add GraphQL query `availableEventsForPackage(productId, eventTypeId)` for wizard support

### 🔷 EventType Template System

- [ ] **G8**: Create EventType GraphQL resolver for template_parent relationship
- [ ] **G9**: Add `template_config` bitmask documentation to GraphQL introspection

### 🔷 Registration Extensions

- [ ] **G10**: Add `units` and new states (`no_show`, `partial`) to GraphQL `EventRegistration` type
- [ ] **G11**: Update registration mutation resolvers for new states

### 🔷 Domain Code & Multi-Tenant

- [ ] **G12**: Ensure GraphQL respects company/domain isolation in all queries
- [ ] **G13**: Add domain_code filtering to event and product queries

### 🔷 Package Edition Support

- [ ] **G14**: Add package-level `edition_code` to GraphQL

---

### 🔷 Cross-Domain Package Safety (from T0 resolution)

> Critical for VueJS frontend to correctly handle packaged vs autonomous events

- [ ] **G15**: Add `package_only` field to `EventType` GraphQL object
- [ ] **G16**: Ensure event queries filter by `domain_code` context parameter
- [ ] **G17**: Add query parameter `includePackageOnly` (default False) for public event listings
- [ ] **G18**: Document GraphQL contract for VueJS: which fields control display logic

### 🔷 Future Tasks (Placeholder)

### 🔷 CID / Slug / CidSlug (from B1 resolution)

> Permalink architecture for events and posts

- [ ] **G19**: Expose `cid` field in EventType GraphQL (already exists, verify format)
- [ ] **G20**: Add `slug` field to EventType GraphQL
- [ ] **G21**: Add `cidSlug` computed field to EventType GraphQL (`{cid}__{slug}`)
- [ ] **G22**: Same fields for BlogPost GraphQL type
- [ ] **G23**: Document GraphQL permalink contract for VueJS routing

---

## Dependencies

| Task | Depends On |
|------|------------|
| G1-G7 | `crearis_event_package` module completion |
| G10-G11 | Registration state extensions in `crearis` |
| G12-G13 | Domain code implementation |

---

## Related Files

- [graphql_theaterpedia/schemas/objects.py](../graphql_theaterpedia/schemas/objects.py) - GraphQL types
- [graphql_theaterpedia/schemas/queries.py](../graphql_theaterpedia/schemas/queries.py) - Query resolvers
- [crearis_event_package/](../crearis_event_package/) - Package module

---

## Notes

- This is a **backlog** action plan — tasks here are not blocking current work
- GraphQL updates should be done in batches after the underlying models are stable
- Schema changes require frontend coordination (notify Vue Storefront team)
