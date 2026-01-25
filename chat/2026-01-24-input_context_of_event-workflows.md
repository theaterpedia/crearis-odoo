
## Original Draft from June 2025 (German)

Verwaltungs- und Zahlungsabläufe **ODOO-Sales+ -Invoicing mit AGENDA**
AGENDA erhält durch diese Maßnahmen Multidomain-Fähigkeiten für 2-5 Domains innerhalb einer Domain (eine Sharepoint-Präsenz -> eine AGENDA-Instanz -> eine ODOO-Regio via ID-Sharding)

Angebote, Verträge, Rechnungen, Mahnungen und Zahlungen werden direkt in Odoo erfasst und teilweise in Access gespiegelt, Sparkasse-Daten werden ebenfalls direkt in Odoo importiert
lediglich der Jahresabschluss wird in Kursverwaltung importiert und durch ein paar lokale Einstellungen ergänzt
das Mapping von Kürzeln via Odoo-Journals zur Automatisierung der Zuordnung von Bestandsbuchungen wird teilweise neu konzipiert

die exportierten Daten in AGENDA auf readonly setzen und mit Odoo synchronisieren, Edits erfolgen in Zukunft via Odoo
weitere Config-Tabellen (z.B. Räume) mgl. rasch ebenfalls via Odoo-Logik anlegen und in AGENDA synchronisieren

XML-ID-basierte Synchronisation der Sharepoint-Tabellen contacts (user) + event + event-user

Sharepoint-basierte Tabellen werden ausrangiert, vor- oder nachgelagert oder als ferngesteuerte Replikation verwendet (ohne Edit-Option)
- User, Partner (Sharepoint) haben Single-Source-of-truth in Odoo -> dort wird die Zuordnung zu Companies gemacht und dadurch die Verteilung auf mehrere AGENDA-Instanzen konfiguriert
- Kurse, Events + Event-Templates bieten via Sharepoint/AGENDA feinstufige Vorplanung + Templating > dies wird dann in ODOO: Product - Event - Track - Session übersetzt -> bei Wechsel in AGENDA-Status 'angekündigt' werden sie exportiert + readonly > dies wird durch die lokale Tabelle tblAgenda dargestellt

Umstellung dasei.eu-Anmeldung auf odoo -> stößt Workflow an


## 🔶 ??:?? AGENDA -> ODOO, Teil 1

Veranstaltung + Template -> Event, Track, Session
Kurs -> Product
- Verträge -> Odoo-Orders

Odoo-Customer

## 🔶 ??:?? ODOO -> AGENDA, Teil 1
-> Ziel: Buchungen + Bestands-Konten-Ausgleich, Konfiguration von Kontenzuordnungen werden direkt auf Odoo gemacht, lediglich zum Jahresabschluss werden Details in AGENDA ergänzt

AGENDA-Bestandskonten + AGENDA-Stammdaten + AGENDA-Bestandsbuchungen (account.payment + payment.move) werden bei Startup jeweils generiert, integrieren eine lokale Konfiguration für die allgemeinen Konten etc. mit den dynamischen Daten (User) von Odoo > möglichst keine neuen AGENDA-Tabellen hinzufügen, sondern die bestehende Logik einfach aus Odoo heraus generieren
Erstellung/Setup von Accounts und Konfigurationen etc. in Odoo so dokumentieren, dass ich die Zusammenhänge auch mit 1 Jahr Abstand nachvollziehen kann
Strukturen wie Odoo-Journals etc. erzeugen
semi-automatische Synchronisation (Button-Click), User-XML-IDs verwenden zur Absicherung der Zuordnungen

## 🔶 ??:?? ODOO -> AGENDA, Teil 2
Bereich Verträge, Rechnungen in AGENDA neu anlegen
a) Hyperlink-Button auf Odoo
b) Readonly-Reporting für:
- Payments
- Sales-Orders = Verträge
- Invoices = Rechnungen (inkl. Zahlungs-Status)
- (später: Quotations = Angebote > vorläufig noch auslassen)

## 🔶 ??:?? INTEGRATION AGENDA <-> ODOO finalisieren
Bisherige Tabelle Bestands-Buchungen in Access beibehalten, jedoch nur durch besondere Input-Anweisung laden. Standardmäßig wird ein Klon der Tabelle geladen, der read-only ist und als Facade auf Odoo-Daten fungiert. Die gesamte Jahresabschluss-Logik etc. basiert auf diesem Klon.
Die bisherige Tabelle Bestands-Buchungen zur Vorkonfiguration eines Buchungs-Imports verwenden -> den Import dann per Befehl umsetzen und in der Tabelle tracken (doppelten Import verhindern). Die Prepare-Tabelle läuft nur auf Zuzanas Rechner und muss nicht synchronisiert werden.

---

## English Translation

> **Context:** AGENDA is an MS Access database that operates on SharePoint tables being imported/synced. It provides: (1) an accounting solution with complete tax reporting, and (2) email-based workflows for both single events and per-user course planning (PDF reports sent via email). Zuzana is responsible for accounting.

---

### Administration and Payment Workflows: ODOO Sales + Invoicing with AGENDA

Through these measures, AGENDA gains **multi-domain capabilities** for 2-5 domains within a single domain (one SharePoint presence → one AGENDA instance → one Odoo region via ID sharding).

**Key changes:**
- Quotations, contracts, invoices, reminders, and payments are recorded directly in Odoo and partially mirrored in Access
- Bank data (Sparkasse) is also imported directly into Odoo
- Only the annual financial closing is imported into the AGENDA course management system and supplemented with a few local settings
- The mapping of abbreviations via Odoo Journals for automating inventory booking assignments is partially redesigned

**Data flow principles:**
- Exported data in AGENDA is set to read-only and synchronized with Odoo; future edits happen via Odoo
- Additional config tables (e.g., rooms) can quickly be created via Odoo logic and synchronized to AGENDA

**Synchronization approach:**
- XML-ID-based synchronization of SharePoint tables: contacts (users) + events + event-user

**SharePoint-based tables** are being retired, either pre/post-processed or used as remote-controlled replication (without edit capability):
- **Users, Partners (SharePoint):** Single source of truth is now Odoo → company assignments are made there, configuring distribution across multiple AGENDA instances
- **Courses, Events + Event Templates:** Via SharePoint/AGENDA they offer fine-grained pre-planning + templating → this is then translated into Odoo: **Product → Event → Track → Session** → when status changes to "announced" in AGENDA, they are exported + read-only → represented by the local table `tblAgenda`

**Trigger:** Switching dasei.eu registration to Odoo → initiates workflow

---

### 🔶 Phase 1: AGENDA → ODOO

| AGENDA Concept | Odoo Model |
|----------------|------------|
| Veranstaltung (Event) + Template | `event.event`, `event.track`, `event.session` |
| Kurs (Course) | `product.template` |
| Verträge (Contracts) | `sale.order` |
| Teilnehmer (Participants) | `res.partner` (Customer) |

---

### 🔶 Phase 2: ODOO → AGENDA, Part 1

**Goal:** Bookings + inventory account reconciliation. Account mapping configuration is done directly in Odoo; only for the annual closing are details supplemented in AGENDA.

**Implementation:**
- AGENDA inventory accounts + AGENDA master data + AGENDA inventory bookings (`account.payment` + `account.move`) are generated at startup
- They integrate local configuration for general accounts etc. with dynamic data (users) from Odoo
- Avoid adding new AGENDA tables where possible; instead, generate existing logic from Odoo
- Document the creation/setup of accounts and configurations in Odoo so that the relationships can be understood even after 1 year
- Create structures like Odoo Journals etc.
- Semi-automatic synchronization (button-click), using User XML-IDs to secure the mappings

---

### 🔶 Phase 3: ODOO → AGENDA, Part 2

**New section in AGENDA for contracts & invoices:**

a) **Hyperlink button** to open records in Odoo

b) **Read-only reporting** for:
- Payments
- Sales Orders = Contracts
- Invoices (including payment status)
- *(Later: Quotations → skip for now)*

---

### 🔶 Phase 4: Finalize AGENDA ↔ ODOO Integration

**Inventory bookings table strategy:**
- Keep the existing inventory bookings table in Access, but only load it via special input command
- By default, load a **clone of the table** that is read-only and acts as a **façade over Odoo data**
- All annual closing logic etc. is based on this clone

**Import workflow:**
- Use the legacy inventory bookings table to pre-configure a booking import
- Execute the import via command and track it in the table (prevent duplicate imports)
- The preparation table runs only on **Zuzana's computer** and does not need to be synchronized