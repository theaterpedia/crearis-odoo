# Document Staging

**Type**: master  
**Stage**: task  
**Original Prompts**: [meta](2026-01-30-agenda_extended_meta.md)

---

## The 5 Stages

Master and detail documents progress through 5 stages. Each stage **appends** content rather than replacing.

| Stage | Focus | Content Added | Language |
|-------|-------|---------------|----------|
| **task** | Problem definition | Questions, todos, blockers | EN |
| **draft** | Exploration | Free-form ideas, research, options | EN |
| **dev** | Implementation | Code examples, UI mockups, selective patterns | EN |
| **spec** | Documentation | Complete patterns, all major cases | EN |
| **user** | End-user | User-facing documentation | DE |

---

## Stage Progression

### task → draft

**Trigger**: Ready to explore solutions  
**Action**: Add `## Draft` section below task section  
**Task section**: Keep updated with current status

### draft → dev

**Trigger**: Starting implementation  
**Action**: Add `## Dev` section  
**Draft section**: Review, simplify → becomes abstract-like  
**Content**: Code examples, UI screenshots, selective patterns

### dev → spec

**Trigger**: Implementation stable, patterns clear  
**Action**: Add `## Spec` section  
**Content**: Complete patterns, all major cases covered  
**Note**: Not API-complete, but all patterns captured

### spec → user

**Trigger**: Ready for end-users  
**Action**: Add `## User` section  
**Language**: German  
**Audience**: End-users, not developers

---

## Document Structure by Stage

### At task stage:
```markdown
# Document Title

**Type**: master  
**Stage**: task

---

## Overview
What this document covers.

## Questions
- Open question 1?
- Open question 2?

## Current Status
What we know, what's decided.
```

### At draft stage:
```markdown
# Document Title

**Type**: master  
**Stage**: draft

---

## Overview
(updated)

## Questions
(some answered, some remaining)

## Current Status
(updated)

---

## Draft

### Option A
Exploration of first approach...

### Option B
Alternative approach...

### Research Notes
Findings from investigation...
```

### At dev stage:
```markdown
# Document Title

**Type**: master  
**Stage**: dev

---

## Overview
(refined, serves as abstract)

## Current Status
(implementation status)

---

## Draft
(simplified, key decisions highlighted)

---

## Dev

### Implementation

```python
# Code example
class MyModel(models.Model):
    ...
```

### UI Design
![Screenshot](files/subfolder/screenshot.png)

### Patterns
Key patterns used...
```

### At spec stage:
```markdown
# Document Title

**Type**: master  
**Stage**: spec

---

## Overview
(polished abstract)

---

## Spec

### Pattern 1: Name
Complete description with code...

### Pattern 2: Name
Complete description with code...

### Edge Cases
How to handle X, Y, Z...
```

### At user stage:
```markdown
# Dokumenttitel

**Type**: master  
**Stage**: user

---

## Überblick
Deutsche Zusammenfassung für Endbenutzer.

---

## Benutzerhandbuch

### Erste Schritte
Wie man beginnt...

### Häufige Aufgaben
Schritt-für-Schritt Anleitungen...
```

---

## Stage in Chapter Tables

Chapter docs track stage per master document:

| Title | Description | Stage | Notes | Version |
|-------|-------------|-------|-------|---------|
| [doc_name](doc_name.md) | What it covers | **task** | Blocking | |
| [other_doc](other_doc.md) | Other topic | **draft** | In progress | |

Update stage column when document advances.

---

## Version Column (Future)

The version column is reserved for code versions:
- Empty during early development
- Will contain version tags when code stabilizes
- Helps track which code version a spec documents
