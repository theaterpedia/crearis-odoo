---
cssclasses:
  - table-wide
  - wide
---
# AGENDA EXTENDED: CORE

## **the role of Crearis (on odoo)** odoo owns the core-workflow and helps to stay organized across all the chatter

What does Crearis on Odoo solve and what is solved elsewhere?

This is not on crearis-odoo: creative work, image-galleries, creative online-sessions, session-protocols, blog-post-creation, emotions and in-person-meetings (for instance: we don't need much of odoo:field-service, live-payments) -> those things are at the core of crearis-vue (the vuejs-compagnon-implementation)

**Instead on crearis-odoo: we rather find 'solid stuff'**: countable things that are on the 'outside of the box'. They concentrate on planning & disposition, templates, schedules, locations, agreements, reminders & preview-infos, issues, Q-and-A, accounting, sales and customer relationship-management with information-email-campaigns, website-updating
The default Odoo-code (without of crearis) delivers good examples for workflow-defaults, sophisticated email-sending and the 'chatter' log/protocoll of interactions on each of these items

## agenda-basic: monthly workflow!!
Most of the people that work with crearis/agenda are capable of keeping track on what comes the next 3-7 days. They would love to see this supported, but they don't need another 'calender' like outlook or taskmanagement-approaches of smartphones. After v1 of the system is well established it could be a good idea to create some easy interfacing into 2-3 of these systems like for instance having contacts synced. The same is valid in comparison to social media workflows.

The big focus of the system is a monthly workflow! It should not be seen as 10-30 tasks, interactions per day per average customer or participant, but more than 1 interaction per week. One core example on this is: Monthy email-newsletter: It is getting aggregated and published 1st week through, then working on reactions the next week and having some kind of stats 1 week after publication. This goes into reporting, forms basis of a planning-session in a team-talk the 3rd week with website-work on the 4th week laying the ground for repeating the cycle the next month. What the monthly cycle-focus means: It is typically fine to rely on Email-workflows, allowing for 2-3 day-long lags. Chat-style-interactions are fine to speed this up where needed. But agenda does not want to 'push' the people into 'do this exactly now'. Instead it tries to find a pace where 'things fall into place' because of timely planning and dense and well-timed information instead of spam-botting on and on again. In an edge-case-configuration it might be possible to have people like the issue-driver covered with specialized info-services. For the start he/she simply will 'fail' and drop out of the courses (which happens regularily and is fine).

At dasei we extend this to 3 main cycles per year. So for instance accounting supervises payments 3 times per year + we have bigger website-updates 3 times per year + planning decisions on underbooked events + status-updates of events from 'announced' to 'current' are batch-processed 3 times per year. So every participant, every instructor by default has to confirm the general planning only 3 times per year.


## THE CUSTOM UI: 3 Tabs = 3 core definitions, perspectives, states

**MORE ON THIS SEE BELOW: SPEC: THE SIDEBAR  CORE  DEFINITION**

### definition "agenda"
vertically organized timeline-view of future activities, infos, tasks, events, documents.
can be turned into a log-view of past-time program and activities.
can be filtered to just show the timeline of a single event

agenda-item / agenda-line - Types and Providers: see distinct definition

### definition "curriculum"
This is the view that goes most far into the content. It gives access to the most important parts of each of the products and only is needed for 'participants', especially useful if they are in the middle of the process of the 'aufbaustufe', but makes sense already from activating the 'grundstufe' onwards.
To give you a synonym: It provides a portfolio-view. For instance it allows to register externally achieved grades or individually organized projects that are required to fully meet the criteria for the final diploma.
We implement it against the 'grundstufe': Here curriculum shows an accordion with 4 sections=products (only one is open at a time): per each of A, B, C, D >> a group of 7-14 lines  (A1=line, A2=line ...) describes the status of one product (for the given participant)
Implementation-styles (should be configurable per domaincode / company)
- easiest could be visualised using a simple 3-state-logic (checked-semichecked-open) gives status per line
- alternatively using a point-system (which are the teaching-units of dasei)

To prevent you from duplicating information this is important to consider: typically the curriculum only provides a different view on the same set of entities as 'agenda'. This rule-of-thumb has edge-cases to consider:
- (seldom): 'externally earned grades' (from participation in courses of other organisations) it can be the case that those entities don't have any representation on the "agenda"
- (quite typical): a lot of 'agenda-lines' do not lead to any form of represantion, count or whatever on the curriculum, they simply were 'process' no 'results'

### definition "service" (synonymous: "contract")
At the beginning this is classical customer-journey-stuff: 
- 2-3 agreements for onboarding-sessions (dates, videoconferencing), email-supported have to be done as smooth as possible from both sides -> if successful this builds first level of trust
- checkout into 'einstiege-ins-theaterspiel' starts you-pay-we-deliver-game with the possibity for both sides to opt-out again until 10-days of first real in-presence-event
- if not canceled auto-advances into recurring-contract with a guarenteed limit
- guaranteed limit / evaluation-> is a date at which a voluntarily-agreed pattern runs: 
	- defaults optimistically to 'stop' needed from either party of the contract to prevent auto-renewal
	- alternatively could be set to run 'conservatively': 'proceed' needed from both parties of the contract to prevent automatic finalization with loss of privileges for the customer

Once the evaluation-phase is over the customers typically opt-in into a real-contract to take part in the program for 1.5 years based on monthly payments. This is almost an 'open-end-contract' and it is much more accurate to talk about 'participants' here than about 'customers'. Typically the core balance payments-against-regularily-provided-events is not critical anymore. Much more important is the question whether the agreed process really works out: Whether participating in the program delivers the expected results. This involves deeper measures of quality-control with a lot of self-controlled participation of the 'customer'. For a user in participant-state the 'Contract' instance:
- Q-and-A
- issues-getting-resolved-count
- self-service-downloads of tax-reports and similar docs


## Where does Odoo sit in the Onboarding-Flow, what is the special role?
As seen from the planning- and managing-perspective Odoo is not taken for the far-away planning and scenarios and is not the host for 'creative documentation-work' in the after-event-workflow. Odoo is at the core of the event, when everything is in the 'hot' phase.
From a customer-perspective this is quite similar: Odoo lives in sandwich-position between frontrunning public website and compagnon-vuejs-login (which is what Jolanda starts to discover: the vuejs-App allows for a lot)

Onboarding runs on a clear track of 3 transitions: From public-facing-website -> odoo-customer -> odoo-participant -> vuejs app-login
This is 3 transitions:
1. transition: product-route on http://dasei.eu -> product-checkout-route on https://dasei.eu  (stepper-ui) -> odoo-controller/api -> email-verification -> odoo-core ultra-easy ui
2. transition: regularily login to odoo-core ultra-easy ui -> advance to odoo-core ui (tabbed) + build email-information-flow, verify payments and other contract-requirements work-out fine
3. transition: all core workflows on odoo succeed -> advance to 'participant'-status -> login to vuejs-app -> participate in content-creation, more sophisticated access to ms_teams_functionality ...

**This all lives on the same IP**
- runs with a single-sign-on-strategy
- will leverage clever NGINX-based routing
- clever usage of website-domainnames and subdomains will help to understand how things belong together or are separated
- we want a safety-option implemented to not allow other actors access controllers, apis

**This all is integrated by odoo-driven information-status**:
- the build-process of the static website can partly be prepared and controlled from inside odoo -> ==yaml-builder-example==
- odoo knows about the main design-options for each of the entities that drive the website-rendering (events, partners, posts) -> this does not influence the static-public-website. It harmonizes the logged-in-experience
allows for a lot of customizations
the static website runs on the same theming, same vuejs-components as does the vuejs-project, but it allows for deeper customization and integrations for the public experience

**This all is integrated by design:**
- responsive design targets consistent break-points (in v1, not at the moment)
- some design-features 'limited support' on odoo -> in v1 (target: MAY 2026) we accept a medium-grade design-shift, especially with these design-specs:
	- vuejs-project + static website run on edge-level theming-capabilities that go beyond odoos defaults (oklch-colors with 'relative color-system' for example)
	- page-header-patterns (overlays, sizing ...) of vuejs-project are almost unreachable on odoo and not so important, they shape how deep-content is being displayed, emotions ... and not accounting or curriculum-status -> but the vuejs-implementation learned a lot from odoos banner- + cover-component for the page-header
	- we don't want to break (at least not very much) bootstrap-defaults, odoos spacings, paddings, typography
- dasei is happy to see that odoo does not use rounded corners -> this fits the core-design of dasei


## design of views, web-components, websites/webviews
### make use of default odoo where possible
- the views implement the core-logic via backoffice (odoo-defaults) and do not require custom webcomponents-implementation especially for instructors and team
- prerequisite-question here: **sidebar-widget for odoo-default-views possible?** Is it possible to add a left-side fixed column to odoo views? It should control/filter the contents of the main-column just in the same  -> see the images under refs with 'sidebar' in the name

### extended views / special implementation for dasei
(tbd)

### web-design fundamentals
- Theming is done using odoo-website-theme-color-system
- try to add configurable components where this makes a lot of sense
- support and implement the odoo responsive design system with 'mobile' (iPhone as default) | 'tablet' (horizontal) | 'desktop' (default to rather small 1150-1366px) is the way to go
	- this translates into: 1-view-col, 2-view-cols, 3-view-cols -> the default is to think everything as 2-view-col-design and for mobile make it intelligently switch and for desktop
- for the responsive design we leave 'strategic gaps' where we don't care about whether things will look good there
	- outside gaps: no viewport-widths below 380px or larger than 1460px to be considered right now (the <380px will be solved using a 'dense'-flag typography)
	- inner gaps: don't implement things that target the viewport width from 430px to 820px (the viewport-width 768-820 will be targeted with the same 'dense'-flag later)

**IMPORTANT NOTE**: the numbers given here are quite accurate but **could differ a little bit** -> this will see one round of refactoring + harmonization after v1-launch -> until then: rather stick with bootstrap/odoo-defaults then breaking everything


### Special webdesign required for sidebar-design for web-components
As already asked for the default-odoo-views, the same applies to webcomponents, website-views.
Sidebar-Navigation is realized in dashboard-style (admin-theme), horizontal navbar is not needed very much but may be visible if this is a much needed odoo-requirement -> a lot of 'general' things are moved into the account-dropdown
The navigation-column is rather wide (to fill the 380px) compared to average admin-theme-designs -> see

## SPEC: THE SIDEBAR  CORE  DEFINITION
To understand this the provided images should be processed (refs)

**This is Core SPEC because it defines how the sidebar/tabs are intelligently used to advance USERS from 'vague customer' to 'well organised participant'!**

The navigation-column-items can be either single-liners (like classic navigation) or 'small-cards' / 'tiles' with up to three rows
Sidebar-Navigation has a tabbed header with 3-4 tabs (iconized), **those 3-4 header-tabs hold the main-navigation!!** -> this is special: other than a lot of dashboard-design where there is a 2-level-grouping inside the sidebar organized vertically (sometimes with collapse-features) the agenda-design decides to only allow 3-4 main sections. As 2nd line of the header a filter-dropdown can be added to filter a section to special values.

The 3 tabs we need are: **Agenda | Curriculum | Service**

In the onboarding-phase this will be simplified (no 'Events' tab) to: 
**STEP 1: Anmeldung zu "Einstiege ins Theaterspiel"**
TABS: Service (-> but the Tabs-Header is being hidden)

**STEP 2: angemeldet zu "Einstiege ins Theaterspiel"** (but defacto it is still in 'pending' state because it can easily be canceled again)
TABS: Agenda (-> but the Tabs-Header is being hidden)
- the Agenda shows both completed and open items
- on the Agenda is an Action-Item 'Anmeldung stornieren' (which is enabled for 10 days after participation in the first event)
- on the Agenda is a 'completed' Item 'Anmeldung bestätigt' -> Click on it brings up the contract-details

**STEP 3: "Einstiege ins Theaterspiel"**
TABS: Agenda | Service
(no filter-Options)
- the Agenda shows both completed and open items
- we have: "optional upgrade" on the AGENDA -> and 'reserved seat' - functionality that previews (read-only) how to proceed with modules B, C, D -> customer can cancel this

**STEP 4: "Grundlagenbildung"** (modules A, B, C, D)
TABS: Agenda | Curriculum | Service
(no filter-Options)
-> Agenda
-> Curriculum shows accordion with 4 sections=products (only one is open at a time): per A, B, C, D >> a group of 7-14 lines  (A1=line, A2=line ...) describes one product -> simple 3-state-logic (checked-semichecked-open) gives status per line

