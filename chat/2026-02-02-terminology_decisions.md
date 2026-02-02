# Terminology Decisions

**Date**: 2026-02-02  
**Context**: Cross-check between Jan 31 action plan and Feb 2 architecture snapshot  
**Status**: DECIDED

---

## 1. Milestone Labels: Company-Level Configuration

### Decision
Milestone labels are **configurable per company** — not hardcoded.

### Three Milestone Types

| Internal Key | Default Label (German) | Purpose |
|--------------|----------------------|---------|
| `activation` | "Aktivierung" | Registration opens (draft → confirmed) |
| `deadline` | "Meldefrist" | Schedule locks (confirmed → released) |
| `completion` | "Abschluss" | Wrap-up (released → completed) |

### Configuration Model

```python
# In res.company (crearis module)
milestone_label_activation = fields.Char(
    string="Activation Label",
    default="Aktivierung",
    help="Label shown for the activation milestone in communications"
)
milestone_label_deadline = fields.Char(
    string="Deadline Label", 
    default="Meldefrist",
    help="Label shown for the registration deadline milestone"
)
milestone_label_completion = fields.Char(
    string="Completion Label",
    default="Abschluss",
    help="Label shown for the completion milestone in communications"
)
```

### View Label Resolution

Views pull labels from company config:

```xml
<!-- Example: Dynamic label in form view -->
<field name="milestone_deadline_date" 
       string="company_id.milestone_label_deadline"/>
```

**Implementation note**: If complex, we can start with static labels and add dynamic resolution later.

---

## 2. Database Field Naming

### Decision
Use neutral English names in database, German defaults in `agenda_dasei`.

| Old Name (Jan 31) | New Name | Notes |
|-------------------|----------|-------|
| `meldefrist_days_before` | `milestone_days_before` | Generic, not German-specific |
| `use_meldefrist` | `use_milestones` | Boolean to enable milestone layer |

### Migration Path
- `agenda_dasei` data files set the German defaults
- `agenda_dasei/__manifest__.py` can set `use_milestones=True` as domain default

---

## 3. Master Doc Cross-Reference Strategy

### Structure

```
agenda-lines.md (Core)
├── Model: agenda.line
├── Providers: event, post, product
├── Fields: including gate_state (brief intro)
├── Views: schedule tab, tree views
└── → FORWARDS TO milestones-and-actions.md for gate pattern details

milestones-and-actions.md (Complete Concept)
├── Full gate pattern explanation
├── Three milestone types
├── Gated transitions (all 3)
├── Role split (instructor vs manager)
├── Controlling model (use_milestones=True)
└── Frontrunner/follower scheduling
```

### Key Principle
- `agenda-lines.md` = **WHAT** (the model, fields, views)
- `milestones-and-actions.md` = **HOW** (the workflow, gates, actions)

The gate pattern is in `crearis` module (essentials), but the **explanation** lives in `milestones-and-actions.md` because that's where the concept is fully developed.

---

## 4. Module Responsibility

| Aspect | Module | Notes |
|--------|--------|-------|
| `gate_state` field | `crearis` | Part of essentials |
| `milestone_days_before` field | `crearis` | Part of essentials |
| `use_milestones` config | `crearis` | Boolean, default False |
| Company label config | `crearis` | With neutral defaults |
| German label defaults | `agenda_dasei` | Data file override |
| Controlling model | `crearis_milestones` | Only when use_milestones=True |
| Frontrunner scheduling | `crearis_milestones` | Only when use_milestones=True |

---

## 5. Conflicts Resolved

### From Jan 31 Action Plan

| Phase | Item | Resolution |
|-------|------|------------|
| 4.3 | `meldefrist_days_before` | → `milestone_days_before` |
| 4.4 | `meldefrist_template_id` | → `milestone_template_id` |
| 4.5 | Meldefrist cron | → Generic milestone reminder cron |
| 7.4 | "Meldefrist milestone display" | → Dynamic label from company config |

### New Additions

| Item | Module | Notes |
|------|--------|-------|
| `gate_state` field | `crearis` | NEW - not in Jan 31 plan |
| Company label config | `crearis` | NEW - configurable labels |
| Stage = GATED | `crearis` | NEW - all 3 transitions are gated |

---

## 6. agenda_dasei Mapping

The `agenda_dasei` module provides German defaults:

```xml
<!-- agenda_dasei/data/company_defaults.xml -->
<record id="default_company_milestone_labels" model="res.company">
    <field name="milestone_label_activation">Aktivierung</field>
    <field name="milestone_label_deadline">Meldefrist</field>
    <field name="milestone_label_completion">Abschluss</field>
</record>

<!-- Enable milestones for DASEi domain -->
<function model="ir.config_parameter" name="set_param">
    <value>crearis.use_milestones</value>
    <value>True</value>
</function>
```

---

## Summary

| Decision | Choice |
|----------|--------|
| Field naming | English neutral (`milestone_*`) |
| Label display | Company config (German defaults in `agenda_dasei`) |
| Gate pattern docs | Brief in agenda-lines.md, full in milestones-and-actions.md |
| Gate pattern code | In `crearis` (essentials) |
| Enhanced workflow | In `crearis_milestones` (optional layer) |
