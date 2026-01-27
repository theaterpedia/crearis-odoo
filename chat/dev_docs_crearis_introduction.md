# Crearis Module Family - Developer Introduction

> **Last Updated:** 2026-01-25

---

## Overview

The Crearis module family provides website-specific event management, SharePoint integration, and product packaging for Theaterpedia and associated organizations.

---

## Module Hierarchy

```
crearis (base)
├── crearis_event_package      (event bundling + sales)
├── crearis_agenda             (SharePoint sync engine)
│   └── agenda_dasei           (DASEi-specific sync)
└── graphql_theaterpedia       (GraphQL API)
```

---

## Core Modules

### 1. `crearis` (Base Module)

**Purpose:** Foundation module providing website-level feature flags and domain management.

**Key Features:**
- Multi-website support with `domain_code` identifiers
- Feature flag hierarchy (`use_template_codes`, `use_tracks`, `use_products`, etc.)
- Website feed aggregation (hub sites)

**Feature Flags (website-level):**

| Flag | Description | Auto-Computed |
|------|-------------|---------------|
| `use_template_codes` | Enable event template system | No |
| `use_tracks` | Enable event tracks | No |
| `use_products` | Product features enabled | Yes (from sub-features) |
| `use_msteams` | MS Teams integration | No |
| `use_jitsi` | Jitsi Rooms integration | No |

**Note:** `use_products` is computed dynamically - it detects `use_event_packages` (if installed) via `getattr()`.

---

### 2. `crearis_event_package`

**Purpose:** Sell bundled events as a single product.

**Dependencies:** `crearis`, `event_sale`, `sale`

**Key Features:**
- Event package product type (`detailed_type='event_package'`)
- Package event lines for traceability
- Package-only events (not sold individually)
- Event selection wizard

**Owns Feature Flag:** `use_event_packages` (requires `use_template_codes`)

📄 **[Full Documentation](dev_docs_crearis_event_package.md)**

---

### 3. `crearis_agenda`

**Purpose:** SharePoint sync engine for events and registrations.

**Dependencies:** `crearis`, `event`

**Key Features:**
- MS Graph API integration
- Event sync from SharePoint lists
- Registration sync with state mapping
- Company-level SharePoint configuration

**Sysreg Bitmask Mapping:**
- Event stages: 1, 8, 64, 512, 4096, 8192, 12288
- Registration states: 1, 8, 64, 512, 4096, 12288, 16384, 20480

📄 **[Full Documentation](dev_docs_crearis_agenda.md)**

---

### 4. `agenda_dasei`

**Purpose:** DASEi-specific SharePoint sync extensions.

**Dependencies:** `crearis_agenda`

**Key Features:**
- Course model (`dasei.course`) for training cohorts
- Participant sync from `plan_kursteilnehmer`
- StatusLookupId to stage/state mapping
- DASEi submenu structure

📄 **[Full Documentation](dev_docs_agenda_dasei.md)**

---

## Feature Flag Architecture

The feature flag system follows a **hierarchical pattern**:

```
use_template_codes (manual)
    ↓ requires
use_event_packages (manual, from crearis_event_package)
    ↓ computes
use_products (auto-computed)
```

**Design Principle:** Feature flags are defined in the **same module** as their functionality. The base `crearis` module detects optional module flags dynamically.

---

## Database Isolation

All models use `company_id` for multi-company isolation:

```python
company_id = fields.Many2one(
    'res.company',
    required=True,
    default=lambda self: self.env.company,
)
```

Website-level settings cascade from the company's `domain_code` website.

---

## Related Documents

| Document | Description |
|----------|-------------|
| [dev_docs_crearis_event_package.md](dev_docs_crearis_event_package.md) | Event package module details |
| [dev_docs_crearis_agenda.md](dev_docs_crearis_agenda.md) | SharePoint sync engine |
| [dev_docs_agenda_dasei.md](dev_docs_agenda_dasei.md) | DASEi-specific sync |
| [2026-01-24-product_event_package_architecture.md](2026-01-24-product_event_package_architecture.md) | Architecture design |

---

## Quick Reference

### Check if event packages are enabled

```python
# From website context
website = self.env['website'].get_current_website()
if website.use_event_packages:
    # Package functionality available

# Check dynamically (works even if module not installed)
use_packages = getattr(website, 'use_event_packages', False)
```

### Get current company's SharePoint config

```python
company = self.env.company
if company.ms_tenant_id and company.ms_site_id:
    # SharePoint sync configured
```
