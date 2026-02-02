
## master-docs: convention changed
dev is a stage, it means 'under active development' but in contrast to stages 'TASK', 'DRAFT', 'SPEC', 'USER' it does not have it's own chapter.
Why? Because for the most part of our process: DEV is the main stage of the master docs. It works on the full scope of the master doc, starts a 'spec' chapter and even is allowed to create 'user' content. This allows for a clear separation of what comes where and prevents from renaming or shifting anything inside the master doc

## 4 master-docs to-be-created
I have decided on how to shapre the first row of 4 master-docs.
I think they should be created around the 'essentials', but that it is good to start planning that already now.
At the moment it not seems urgent to me: The last action-plan (attached) seems very well organised and my additions (one more round of cross-checking is needed before we can execute) clearly can go into separate snapshot-docs for now and then we will insert some lines into the action plan and update some others and are good to go.

But I think that once the essentials are done that all 4 master-docs should be created in a batch.

I want you to create 2 core master-docs and 2 compagnon master-docs that partly overlap with the core master-doc. Both compagnons will span other topics like for instance the sales-loop + crm on products (so they are 'horizontal'?) while the core master doc and focusses on exact details for one functionality (is more 'vertical'?)
- CORE: 'agenda-lines'
- CORE: 'milestones and actions' enhanced event-lifecycle 'inner phase' () -> core functionality and how module crearis_milestones crafts a new experience for event-management
- products, modules and event-packages
- use-case 'dasei' -> how exactly the well-defined models, views are being extended using domaincodes, webcomponents and conventions like the 3-months-cycle

## naming-change
The 'meldefrist' gets renamed to 'milestone', the default-behaviour of the milestone is the 'meldefrist', but other implementations may arise. There is no config 'use_meldefrist'. Milestone is considered 'essential' and will receive support from crearis-vue as well.
This is a check-task to prevent misunderstanding. The check should be executed again before implementing the essentials.

## action-planning around agenda-lines
My idea is to separate 3 batches of work:
1. the real essentials of agenda-lines: almost ready for implementation -> but will cross-checked one last time against the 'negative spec' (things that are not essential and could be moved out to submodules)
2. the milestones-logic > this is drafted by Hans and will get refined by Claude
3. the actions-logic > this will be drafted by Claude (Scenarios) and will get reviewed by Hans

1.) is the 'essentials', will be done right away and builds the foundation against which all other work gets planned

2.) + 3.) will receive further research -> to do this properly we need to have a round with text-creation (de) based on the dasei-customer-journeys as planned + imagination of UI

## draft of my idea
My idea is to create a transient-model (lets call it 'controlling-lines' for a while) that works over agenda-lines! It concentrates especially on those agenda-lines that are current or under current controlling. It targets 2-3 distinct roles (the instructors/managers + the participants). It allows to bring in more data and cross-referencing here so that the different roles can work on specialized experiences. Not everybody will see everything. To start this thinking:
- instructors + managers see milestones + some actions, a condensed set of session-lines and have this organized/batched into bi_weekly controlling-sessions with a view that can bring up some stats
- participants only see the actions and the full set of action-lines

For the beginning instructors and managers are the same, but may be divided later. At dasei we have 3 instructors that are 'instructors only' and mainly are interested to see 'their' events while 4 instructors form a managing-board that meets with the bi-weekly rhythm and has to see everything and edits everything (on behalf-of the 'only-instructors').

## I see these questions: 
- what about the 'system' as provider for agenda-lines? Or is it just providing controlling-lines? Or is that an obscure strategy to allow for company or user (not partner)
- what is the good way to setup the domaincode -  company relation if we take the examples of dasei
- at the moment I think that the 'milestone'-type for agenda-lines exists in 1.) but has a simple hardcoded logic and does not automate the event-stage (see below) -> but the type gets enhanced, receives options by the 'agenda_milestones' module
- do we have the same logic with the agenda-line action-type: a straightforward, simple-to-understand basic implementation -> gets enhanced into an opinionated event-management-philosophy when 'use_milestones' is activated
- I think that some part of the 'magic' with the milestones would come a) from the 'system' (it serves intelligent, pro-active grouping and batching) + b) from visibility and roles (I think that the average customer does not see the milestones, only some of the actions + the team does not see all of the actions but the milestone -> the system 'brokers')
- How does this get reflected on graphql? I am pretty sure that graphql should bring this to life by delivering information-hiding here: Some of odoo-complexity should stay on odoo. But the interesting question is: in which way? Maybe the transient-model-stuff, specialized milestones and actions, system-lines should be mostly hidden, only plain standardized agenda-lines go through graphql. Or it is exactly the other way round: On odoo only a simplified, proof-of-concept UI gets implemented to show the management-surface. But the graphql is focussed on the transient model and crearis-vue does the magic but can rely on odoo to always properly translate this back into plain agenda-lines (crearis-vue is the 'master' of the 'stages' -> because it is the origin of the 'sysreg', has a powerful implementation of the bitmask-values that drive the stages. That allows to create rules for stages and transition-paths and so forth)

---

now we extend the prompt with **further reading**

## details
- look into 2026-02-02-details.md to understand core details of the conception.

## more details, implementation-strategies, origin docs
**important: these 2 documents were written prior to what you have read until now** -> so be careful not to spoil my 'new terminology' with the 'older thoughts'. There will some cleaning-up and aligning of terminology needed but I am confident that you, Claude will master the task

For the most part, I think that both documents have the really good ideas. Once this is well understood and some flaws and over-engineering is stripped out, it will be laid out in the master-doc 'milestones and actions':
- 2026-02-02-additions.md
- 2026-02-02-origin.md
