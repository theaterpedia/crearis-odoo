## ⭕ update module 'crearis' (project/crearis)

### model event.py
- add field 'units': float, string "U-Einheiten", help ("teaching units, typically 45 mins / unit")

### add entries to both event_stages, event_track_stage
- the module shall add these config-values (and remember the mapping for the sync-task, see below)
- no entries / default-entries to these fields: mail-id, color, create_uid, write_uid

| ID  | Sequence   | Name(de_DE)            | fold | maps to status-group | connected plan_veranstaltung.status-ids |
| --- | ---------- | ---------------------- | ---- | -------------------- | --------------------------------------- |
| 1   |    1       |            Neu         |      |                      |                                         |
| 2   |    16      |           Vorlage      | t    |                      |                                         |
| 3   |    64      |           Entwurf      |      |                      |                                         |
| 4   |    512     |          Bestätigt     |      | angekündigt          |                                         |
| 5   |    4096    | Freigegeben            |      | aktuell              |                                         |
| 6   |    32768   |        Abgeschlossen   | t    | abgeschlossen        |                                         |

### alter the scheme of table event_type
add these fields:
- is_template_code: bool , default false, help("name is shortcode, parent_type")
- template_parent -> is linked to event_type (filter down to records with parent_type: null|empty)
- company_id: Company restriction (null=all)
- template_cimg ``fields.Text('Hero-Image-Link', translate=False, default='', help="xmlid or public url for hero and thumbnail image")``
- template_teasertext: text
- `template_units` | Float | Teaching units
- `template_heading | Text | help: "Website Heading"
- `template_ext | jsonB | help: "Template Extensions"
- template_config | Integer | help: "Bitmask of config-flags"

### add or update config-entries (by id) to table event_type

| ID  | Name (de_DE)         | Sequence |
| --- | -------------------- | -------- |
| 1   | Workshop (4-8 Std.)  | 32       |
| 2   | workshop > Kurz      | 64       |
| 3   | workshop > Mehrtägig | 96       |
| 4   | Kurs (4-10 Monate)   | 256      |
| 5   | kurs > Kurz          | 512      |
| 6   | kurs > Fortlaufend   | 768      |
| 7   | Projekt (5-9 Tage)   | 2048     |
| 8   | projekt > Kurz       | 4096     |
| 9   | projekt > Mehrphasig | 6144     |
| 10  | Konferenz            | 16384    |
| 11  | Auftritt             | 32768    |

## update the edit-form for event-types that is provided alongside events, make it accessible from the crearis-menu (mainly for admins, project-owners -> a config-option)


## ⭕ alter the plan how to create the module 'crearis_agenda' (project/crearis)
## general simplification
For all queries this can be applied: look into the domain_code (text) - fields of the sharepoint-result.
if they have no domain_code or if the domain_code is found on the system, then sync them. To make this fast and easy you could create python helper function: is_local_domaincode(domain_code as string)

## company-settings + setup (see your plan from yesterday)
`ms_agenda_api_key` is a password -> this should be a field on it's own (how to save it securely?)
client_id, tenant_id, base_url, site_id + all the List GUIDs go into a jsonb-field `ms_agenda_api` -> it should be edited using

## sync-logic
See below: Main sync logic (event, partner, event_type) should use the version-field (oversion on sharepoint) like implemented on event_event to detect updates on odoo (and prevent 'stupid sync-loops' that come from roundtripping updates on both sharepoint and odoo)

### sync-settings
These sync-settings need to be centrally configurable per company
#### lang/i18n
the data on sharepoint is not in multilanguage-format.
With the lang-field we decide if we have multilanguage odoo-fields, on which of the languages the content is matched primarily (at the moment: the other fields will be filled as well), lang defaults to "de_DE"

#### sync-levels
We have 3 sync-levels, default is 'init'. Init can run only once. It needs to be processed once in order to proceed to 'slave'. 'Slave' can run regularily. It needs to have run once in order that we can proceed to 'master'
##### init
partners, event-type

##### slave
events, event-registrations

##### master
client and master: the difference is mainly about the question gets answered "who wins on conflicts?" -> if master then odoo wins, if slave then sharepoint wins

#### 2 sync-modes
- sync-mode 'entity': this is version-controlled, has a cid (xmlid) and typically allows for edits on sharepoint, but odoo will be the master because other services will be connected as well. Entitites like event or res.partner form a node in a network of informations.
- sync-mode 'relation': this is a simple step-in-and-take-over-logic that leads to a simple publishing-workflow, it is used for side-tables that accompany entities like events or partners. An example is the event-registration of a partner. This is a relation, connecting two nodes in a network of informations. It would be complicated and overengineering to have those relations fully synchronized, a clear oracle is needed and this is odoo. Only before and after the status-values of the core business workflow the relations can be controlled by sharepoint (or other systems), this is used for instance for preparational logic (drafting and templating).

### Sharepoint-Mapping to plan_veranstaltungscodes
filter out status -1, 1-4

veranstaltungscode-status references event_type.sequence -> but always uses is_template_code=true + company_id has to match (and not null)

| SharePoint Field | Type   | Odoo Field            | Type       | Notes                                                                                             |
| ---------------- | ------ | --------------------- | ---------- | ------------------------------------------------------------------------------------------------- |
| `id`             | Number | `ms_id`               | Integer    | Primary key for sync                                                                              |
| `Title`          | Text   | `name`                | Char       | Event type code                                                                                   |
| `heading`        | Text   | `template_heading`    | Text       | Teaser text                                                                                       |
| `UE`             | Number | `template_units`      | Float      | Teaching units                                                                                    |
| `TeaserText`     | Text   | `template_teasertext` | Text       | Teaser text                                                                                       |
| `Status`         | Number | `sequence`            | Integer    | Internal status                                                                                   |
| `oevent_type_id` | Number | -                     | -          | Written back after create                                                                         |
|                  |        | is_template_code      | True       |                                                                                                   |
| cimg             | Text   | template_cimg         | Text       |                                                                                                   |
|                  |        | template_parent       | link by id | find the basic event_type (without company_id, is_template_code=false) that has the same sequence |
| -                | -      | `company_id`          | M2O        | **NEW**: Company restriction (null=all)                                                           |

### behaviour of event_stages
if company has crearis_agenda activated then on event_stage block transitioning back from stage-sequence >= 512, only upwards is allowed + it is allowed to delete the event

### sync-logic of event_stages
add 3 event_tag-entries + 1 event_tag_category-entry:
map the '#' extensions of the status-field from sharepoint:plan_planungsstatus: ORGA, TEAM, USER to 3 corresponding odoo event_tag-entries.
All 3 entries have the event_tag_category 'status' (needs to be created as well) 
-> example: plan_veranstaltungen.status.id:3 ``[angekündigt #ORGA#]`` maps to event_stage.id:4 + event_tag (status-category: 'ORGA' )
this should be done both ways: If a record is synced odoo -> sharepoint both stage + tags shall be evaluated

### apply a templating-logic on record-creation on model event_event
Events are the core entities of the system.
The crearis_agenda-implementation extends the life-cycle of event into 3 major phases:
- sunrise (early planning)
- core
- sunset (documentation, templating)

The sunrise and partially sunset-phase are offloaded from odoo (onto sharepoint and other systems) or are getting simplified on odoo.

Core ist what is fully under control of the odoo-system. Here we have the most complicated and interrelated workflows. 
Sunset is things like documentation and reusability (transform an entity into a template). During sunrise is quick actions, setting dates and default content using templates and automations. This is mainly handled on sharepoint. 
Now what shall happen on odoo: When new entities are 'found' after 'sunrise' on the sharepoint-table this is typically at the point where on sharepoint they transition to status [angekündigt] or variations of this status.
This initial transition into [angekündigt] itself is a process executed on record-creation on the odoo-side: Empty fields will receive content, templates, types will be applied exactly with the data-state on the transition-date. This is a one-time-only-process. So if afterwards templates will be altered again, the entities that went through the transition on odoo will not be affected by it. As soon as the record is created on the odoo-system it gets cross-registered on sharepoint (oevent_id).
There are fields prepared on the sharepoint-table to receive the outcomes of the transition. If on the initial sync there are other values found on these fields than 'null', empty or 0 they will overwrite the outcomes of the odoo-side default-transition with the template-values. This allows to add field-specific delta to the templating, for instance to adapt the 'units' because the event is planned for 4 days instead of 2.5 days (that are defined for a specific template).

Event-types do not use this templating (they are the templates themselves): This means they should be kept in sync across all shared fields.

## ⭕ agenda_dasei
Start implementing the special module 'agenda_dasei'. It serves as a reference on how to adapt crearis_agenda to the needs of a single company.
The most important thing for now is that it writes back the 'highest' domaincode for the partner ('dasei3' is higher than 'dasei2' // 'dasei' is higher than all the rest), because we want to use that to build 'login'-button-workflows

company: use_agenda_dasei
dasei0
dasei1
dasei2
dasei3
dasei

## ⭕ map plan_kurse and plan_kursteilnehmer to products and product-templates
this is the business-convention of dasei:
- ME/NE-courses are 'Einstiege' (just Modul A)
- rest of M/N-courses are 'Grundstufe' (Module B, C, D)
- Z-Courses are 'Aufbaustufe' (separated in two Variants ZR / ZT)

## ⭕ map partner-statusses to domain-codes of dasei
1 -> at least 'participant' dasei1 -> but we need to further evaluate sharepoint 'plan_kursteilnehmer' + 'plan_kurse'
2 -> 'participant' dasei2
3 -> 'participant' dasei3
4 -> 'participant' dasei1
5 -> 'participant' dasei0
8 -> role 'member' of 'dasei' -> should only sync if no entries are made yet, otherwise manual config
9 -> role 'participant' of 'dasei' -> should only sync if no entries are made yet, otherwise manual config
10 -> role 'partner' of 'dasei' -> should only sync if no entries are made yet, otherwise manual config
