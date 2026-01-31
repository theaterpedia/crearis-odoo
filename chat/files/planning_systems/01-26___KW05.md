---
created: 2026-01-15T09:44:54+01:00
title: "**week**"
id: kw05
description: .
entity: week
status: new
start:
end:
---

> [!summary] .
> 
`VIEW[## _{id}_ {title}][text(renderMarkdown)]`
`VIEW[{description}][text(renderMarkdown)]`

## 🔶 Meta
- [ ] Arbeitszeiten und Termine diese Woche ^schedule
- [ ] Dokumentstruktur anlegen ^structure
- [ ] Protokoll Vorwoche abschließen ^oldlog
- [ ] Tasks aus Zyklus einplanen / aus Vorwoche
- [ ] die Woche durchdenken, Pomodoro-Grundlagen, Ziele definieren

# MO 26.1
**🔶 0X:00 XYZ**
# DI 27.1
# MI 28.1
# DO 29.1 - HAUS
**🔶 11:00-13:00 ODER ~15:30-17:30 Haus-Bespr. Zuza** -> je nachdem wann Zuza Termin mit Melanie hat
# FR 30.1 - ein Zeitslot: HAUS
# SA 31.1 - ein Zeitslot: HAUS
# SO 1.2

# THEMEN
## **HAUS**
```dataviewjs
dv.view('agenda', {versions: ['#kw05'], project: 'haus', show: ['normal'], showDetails: true})
```
## **CREARIS**
```dataviewjs
dv.view('agenda', {versions: ['#v040','#kw04'], project: 'crearis', show: ['normal'], showDetails: false})
```
## **DASEi**
-> direkt mit base arbeiten: myn und all
```dataviewjs
dv.view('agenda', {versions: ['#kw05'], project: 'dasei', show: ['normal'], showDetails: true})
```
## **GTMD**
-> direkt in Projekt Agenda arbeiten und die Abläufe weiter ausdenken, möglichst bald automatisieren
```dataviewjs
dv.view('agenda', {versions: ['#kw05'], project: 'gtmd', show: ['normal'], showDetails: true})
```

