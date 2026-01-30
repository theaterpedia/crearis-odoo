# Document Types & Conventions

**Type**: master  
**Stage**: task  
**Original Prompts**: [meta](2026-01-30-agenda_extended_meta.md)

---

## Whitepaper Structure

```
chat/
├── index.md                          # Single entry point
├── chapter_conventions.md            # Chapter 0
├── chapter_philosophy.md             # Chapter 1
├── chapter_*.md                      # More chapters...
│
├── conventions_document_types.md     # Master doc (this file)
├── onboarding_checkout_stepper.md    # Master doc
├── workflow_email_templates.md       # Master doc
│
├── devdocs_quick_reference.md        # Intermediary docs
├── dev_docs_*.md                     # Intermediary docs
│
├── 2026-01-30-action_plan_*.md       # Snapshot: action plans
├── 2026-01-30-agenda_extended_*.md   # Snapshot: inputs
│
└── files/                            # Source files, images
    └── agenda_extended/              # Organized by batch
```

---

## Document Types

### 1. Index (`index.md`)

**Purpose**: Single entry point to the whitepaper  
**Content**: Only chapter links + quick metadata  
**Updates**: When chapters are added/removed

```markdown
# Crearis Agenda Whitepaper

## Chapters
| # | Chapter | Description | Stage |
|---|---------|-------------|-------|
| 0 | [chapter_conventions](chapter_conventions.md) | Document conventions | task |
| 1 | [chapter_philosophy](chapter_philosophy.md) | Why crearis, why Odoo | task |
...
```

---

### 2. Chapter (`chapter_*.md`)

**Purpose**: Thin index for a topic area  
**Content**: Title + Abstract + Master docs table + Quick reference  
**Updates**: When master docs are added/removed or stages change  
**Length**: ~50-80 lines max

```markdown
# Chapter N: Topic Name

**Type**: chapter

---

## Abstract
One paragraph summary of this chapter's scope.

---

## Master Documents
| Title | Description | Stage | Notes | Version |
|-------|-------------|-------|-------|---------|
| [master_doc_name](master_doc_name.md) | What it covers | task | | |

---

## Quick Reference
Brief summary tables/lists for at-a-glance info.

---

## Source References
Links to input documents, external sources.
```

---

### 3. Master Document (no prefix)

**Purpose**: Actual content that advances through stages  
**Naming**: Descriptive, NO date prefix, NO 'devdocs', NO 'chapter'  
**Content**: Grows stage-by-stage (task → draft → dev → spec → user)  
**Links TO**: Other master/detail docs, devdocs, sprint docs  
**Links FROM**: Chapter docs only

```markdown
# Document Title

**Type**: master  
**Stage**: task

---

## Task Section
Current status, questions, todos.
(This section stays at top, updated frequently)

---

## Draft Section (added when advancing to draft)
Free-form exploration, ideas, research.

---

## Dev Section (added when advancing to dev)
Code examples, selective patterns, UI imagery.

---

## Spec Section (added when advancing to spec)
Complete patterns, all major cases covered.
Draft content becomes abstract.

---

## User Section (added when advancing to user)
German language, end-user focused.
```

---

### 4. Detail Document (no prefix)

**Purpose**: Deeper dives into specific topics  
**Naming**: Same as master docs  
**Content**: Can be converted to/from master freely  
**Links**: Only linked FROM master docs

A master doc can be "promoted" to detail or vice versa based on scope.

---

### 5. Devdocs (`devdocs_*.md` or `dev_docs_*.md`)

**Purpose**: Intermediary documentation, less organized  
**When created**: Typically end-of-implementation to capture status  
**Content**: Long-lasting info but not audited, terminology may vary  
**Links**: FROM master/detail docs only (not the reverse)

```markdown
# Devdocs: Topic

Quick reference, implementation notes, status capture.
Not systematically maintained.
```

---

### 6. Action Plan (`YYYY-MM-DD-action_plan_*.md`)

**Purpose**: Implementation planning snapshots  
**Lifespan**: Valid for planning period, then historical  
**Content**: Steps, decisions, timelines  
**Links**: Don't link TO whitepaper (refs will break)

---

### 7. Sprint (`YYYY-MM-DD-sprint_*.md` or `YYYY-MM-DD_sprint_*.md`)

**Purpose**: Sprint-scoped work tracking  
**Lifespan**: Sprint duration  
**Content**: Tasks, progress, blockers  
**Links**: Don't link TO whitepaper

---

### 8. Snapshot/Input (`YYYY-MM-DD-*.md`)

**Purpose**: Point-in-time captures, external inputs, research  
**Lifespan**: Historical reference  
**Content**: Varies (prompts, research, imports)  
**Links**: Referenced FROM master docs

---

## Linking Rules

### DO link from:
- Master docs → other master/detail docs
- Master docs → devdocs, sprint docs, snapshots
- Chapter docs → master docs (table only)
- Index → chapter docs (table only)

### DON'T link from:
- Devdocs → whitepaper (refs break as whitepaper evolves)
- Sprint docs → whitepaper
- Snapshots → whitepaper

### Instead of backlinks:
Use terminology consistently (e.g., "agenda.line", "checkout stepper").  
Reader can search whitepaper for terms.  
Assume "re-research needed" rather than relying on outdated refs.

---

## Files Folder

```
chat/files/
└── agenda_extended/           # Batch name = subfolder
    ├── DataViewDetails.vue    # Original filename preserved
    ├── checkout-stepper.png
    └── ...
```

**Purpose**: Source files from other systems, images  
**Organization**: By batch/package in subfolders  
**Naming**: Keep original filenames within subfolder

---

## Future: Static Docs

The whitepaper is designed to become md-driven static docs (mkdocs, vitepress).

**Requirements met**:
- Single folder structure
- Relative links only
- No filesystem-specific paths
- Clear hierarchy
