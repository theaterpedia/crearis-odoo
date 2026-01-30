---
cssclasses:
  - table-wide
  - wide
---
# AGENDA EXTENDED: INTRO

Hey Claude! Your clear reasoning 2 days ago towards not using a transient model for the session-lines was the initial factor to get on track with all that I am presenting you here!! This is a major success you brought into our teamwork. I would have tried to stay with a json-alone-strategy for a while, then would have started a transient approach, starting to hit the wall sooner than later and would have been trapped into refactoring at a stage of implementation where parts of the customer-journey already had been implemented. Simple question of 'not enough resources' to not solve the problem anymore at all.

I know the structure you proposed and implemented with the session-lines very well. The biggest parts of the MSACCESS-on-Sharepoint-implementation has a similar structure: Keep monolithic data or slow-performing, inflexible sharepoint-tables that form a bigger system mostly untouched, but add a second layer that breaks them up into clearly normalized sql-tables that drive fast queries and simplify coding; it adds the need to follow a clear convention and to keep the edit-options under control. I see those things like the session-line-implementation a little bit like: 
- Nitro-endpoints or Composables in the VueJS-Nuxt-world
- materialized queries on postgresql

Those comparisons let me revisit the questions about potentially weak-points of our concept: Not that I want to throw it away again, but that I want us to understand: How to make use of it and where there are traps.
The session-lines as implemented right now are good on upward-sync. I see this more like 'translation' or 'transformation' than 'sync', because: It kicks in as soon as textbased scheduling-configuration enters odoo, thus: at the moment where far-away-planning is transformed into 'realised planning'. Typically what will happen is that some of the session-lines receive further configurations. And sooner or later we could reach the point where we want to do things with session-lines that don't find proper representation in the text-basis anymore. The sync works on syncing schedule-json and session-line sql-table. So the strong-point, advantage is (you named it yesterday already) that we have a data-transition from templates into final planning and by-design we don't want any future alteration of templates to confuse already converted/transformed session-lines. Therefore we simply cut-off here and only sync schedule-json<->session-line-table.
But here again we have an important question: where is the source-of-truth:
- is it the entity-record that controls the details-table. So edits should rather be done to the json and then the details-table should be kept in sync and is meant to be readonly in practice? 
- or is it the session-lines-table and the schedule-json is just a "representation". But graphql takes advantage of the json a lot, especially it could allow to take in mutations on the schedule-json, which is very helpful right now in the early stages of the whole project because the VueJS-App rather organizes the UI by events, already has an events-crud connecting to odoo. The Vuejs-App may not even have it's own 'schedule'-table and might only use a simple schedule-query against odoo/graphql to get the next/last 30 items on the session-lines-schedule for navigation-purposes

On MSACCESS-Sharepoint I established a convention that directly using the session-line-table for editing purposes is allowed under certain circumstances. Why? Because it allows for a more simple implementation of edit-forms compared to the need of json-parsing. For instance a special boolean 'locked_edits' could be introduces to session-lines. Writing to this field:
- has to be done by explicit action from a view (for instance: a 'save'-button has to be executed, no auto-save)
- triggers a reverse-sync that forcibly overrides schedule-json -> after running (being is successful or not) the 'locked_edits' is disabled again
- blocks from overriding the session-line for instance through automated sync-procedures

My idea is to introduce a second extension to the session-lines. I would use it as integration-point for a well-defined set of timeline/workflow-items that make up the 'agenda' of a person, agenda of a 'project' or agenda of a whole region, for instance 'Augsburg' (the city), last thing that is common: agenda of a 'topic'. The distinction between topic and project has to be defined.
. 
You might have wondered about the modules-naming 'agenda' and 'crearis' already. I see 'crearis' as a clearly opinionated software-and-server-strategy. It has opinions:
- against isolation, control and hierarchial 'role'-thinking, Claude-on-the-vue-project told me to rather name the 'owners' of certain data (for instance blog-posts) not 'owners' but 'creators'.
- about how to bring people together on 'events' and then have simple artifacts created like 'notes' or 'images'
- from there support workflows how they could be published as 'posts' (internally or externally) and and from there could be further developed in deeply informative formats (including all kind of media)
- but typically always referencing back to the origin, which in Theaterpädagogik (and a lot of similar disciplines in the 'Soziokultur') are events that typically take place in-person and most often at well-known locations.
- This process is in a constant flow across the borders of individuals, individual events, individual locations, most important: across 'companies'.
- Instead the 'Soziokultur' knows all kinds of 'organisations' and quite often it is misleading to apply a 'customer' narrative on the people taking part in it.

So crearis wants to support a 'movement'. A movement typically has some kind of agenda. But often it is hard to locate that agenda. Most important point are 'events', everybody agrees on that. But those events start long before they take place and certain parts of this 'early' starting could be formalized into distinct parts of the agenda. That is all what 'crearis' is about, let's say: 'agenda' is the most important 'tool' or 'representation' that crearis brings in. 

So what is opinionated becomes obvious if you ask: Why don't they stay on Sharepoint? There are the opinionated decisions: Because of Odoos ability to implement things across companies, seeing companies as one option to filter. Why not simply default to social media? Because of a lot of concerns about privacy on the one side and because of big troubles to get socialmedia really understand 'entities'. So we decided to chose Odoo as the platform against which to develop the logic. 

Why do I tell you about all that? Because it will guide you to further assist with decisions on software architecture inside the mighty Odoo-monolith. We face the requirement to intelligently bring-in core-features of how Odoo already implemented the 'agenda': I think the most obious is the Chatter + the incredible Workflow-Engine. I see that they provide a unified way to log + configure-into-future what is and was the 'Agenda'. But couldn't we take parts of these automations and loggings, emails being sent, reports being created and form a distinct decision: How exactly they shape the agenda instead of simply saying 'everything on the agenda' which is the stupid answer of most of the 'swiss-knife' style implementations we all are getting tired of.
So there are 3 questions: 
1. how to sync certain parts of Odoos Agenda-Automations to become 'agenda.lines'
2. where are missing pieces that need to be considered, should be clearly named as missing and for instance get 'stubs' so that it is clearly made 'here is a missing point' -> but we do not bloat our roadmap
3. where are certain pieces of my conception that are so well-defined that it is better to take them than rather common-sense but simplified defaults (like the default odoo events-tracks might not have been the best way to implement for events.location-configuration in our case)

So I wrote a lot about it. But still I think we will be fast on deciding here! I thought a whole day about it.
How to decide?
1. naming and name-based modelling
2. deciding the scope, reach: rather keeping it simple, but expanding it from only 'session.lines'
3. categorizing the agenda-lines against meta-categories

**For 1. naming and name-based modelling**
We could keep the 'session.lines' as the major data-type on the agenda and therefor naming it session-lines all together but adding a type-field that defaults to 'in-presence-slot', but has alternative: 'info', 'milestone' -> talking and writing about it we would more focus on the 'lines' than the 'session-lines' here. We could refactor it to agenda.lines. I think this is more powerful, a. clearly distinguishes from all known models on odoo as far as I know + b. it explains the relations between 'crearis' and 'agenda'. We should rename the 'crearis_agenda' module to 'crearis_sharepoint' because agenda is at the core of crearis. We could keep 'agenda_dasei'.

**For 2. Line-Item-Providers**
In addition to 'events' I would add 'posts' and 'products' as providers of line-items. In the way it is conceptualized now the both have a clear relation to the events, turning events into entity-no1. They both have their own lifecycle-logic and strong odoo-workflows + chatter should work fine. I would try to not bring companies or users or partners as providers of line-items because they much more are the drivers, actors that work on the line-items. It is not that a company 'is the agenda' it more 'has the agenda'. (Sure there exist things like "Organisations-Entwicklung" that put an organisation into an agenda. But this is not the aim of Crearis). 

**For 3. Line-Types**
- session/sessionline: online OR in-person
- meeting: online OR in-person (outside of an event) -> preparational meeting for product-development for instance
- milestone: initially=simple request to document a status // post v1-implementation: requires some sort of stats or checks  -> links to other data
- info: email will be sent // post v1-implementation: alternatively on portal-login: newsreading > read-confirmation could be created)
- action: simple text (like q&a), document, image, transformation, decision

---

