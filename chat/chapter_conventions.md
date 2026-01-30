# Chapter 0: Conventions

**Type**: chapter

---

## Abstract

This chapter defines the document conventions for the crearis whitepaper system. Following these conventions ensures consistent structure, easy navigation, and minimal maintenance overhead as the project evolves.

---

## Master Documents

| Title | Description | Stage | Notes | Version |
|-------|-------------|-------|-------|---------|
| [conventions_document_types](conventions_document_types.md) | All document types and their rules | task | Core reference | |
| [conventions_staging](conventions_staging.md) | 5-stage progression: task→user | task | | |
| [conventions_linking](conventions_linking.md) | When and how to link between docs | task | | |

---

## Quick Reference

### Document Types Overview

| Type | Prefix/Pattern | Long-lasting? | Purpose |
|------|----------------|---------------|---------|
| Index | `index.md` | ✓ | Single entry point, lists chapters |
| Chapter | `chapter_*.md` | ✓ | Thin index: title + abstract + master docs table |
| Master | no prefix, no date | ✓ | Actual content, advances through stages |
| Detail | no prefix, no date | ✓ | Deeper dives, linked from master docs |
| Devdocs | `devdocs_*.md` | ~ | Intermediary, less organized, end-of-impl capture |
| Action Plan | `YYYY-MM-DD-action_plan_*.md` | ✗ | Snapshot, implementation planning |
| Sprint | `YYYY-MM-DD-sprint_*.md` or `YYYY-MM-DD_sprint_*.md` | ✗ | Snapshot, sprint-scoped work |
| Snapshot | `YYYY-MM-DD-*.md` | ✗ | Point-in-time captures, inputs, research |

### The 5 Stages

| Stage | Content | Language |
|-------|---------|----------|
| **task** | Problem statement, questions, todos | EN |
| **draft** | Free-form drafting, exploration | EN |
| **dev** | Code examples, UI imagery, selective | EN |
| **spec** | Complete patterns captured | EN |
| **user** | End-user documentation | DE |

---

## Source References

- [Meta](2026-01-30-agenda_extended_meta.md): Original conventions definition
