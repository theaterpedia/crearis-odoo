
### use_milestones: config-option
use_milestones has these effects (what if it is set true)
- only then agenda-lines of type 'milestone' are allowed
- the field 'milestone' gets added to backoffice-views, it defines when to transition from stage 'draft' to 'confirmed'
- the 'bi_weekly' option is forced true (see below) -> it creates a bi_weekly controlling-session 
- if the bi_weekly runs the controlling-session brings up all events that have their 'milestone', 'info-mail' or 'wrap-up' within 1-3 weeks after the controlling-session + those events that have a flag 'forced controlling' activated
- gathers together all events-related decision-points into a bi_weekly rhythm

I think that use_milestone could be set either on the company- or on the domaincode-level. But if it is set on the company-level it cannot be deactivated on the domaincode-level.

What if use_milestones is set false? (how does the default=false work?)
The info-mail and the opening-reminder still are being processed. But the difference is this: No connection is forced/automated in the way that sending the info-mail is a logical consequence of advancing the stage of the event. 
So in default there are simple guards active, that require a minimum configuration of the event. If those requirements are not met (the event has no sufficient status, or crucial info for the info-mail is missing) then the info-mail will not be sent + no line representing the info-mail-content will show up in the participant app + a warning/issue will be reported by automation.

So with use_milestones activated the process gets more planning and automation. Without it is more flexible and allows on-the-fly creation and execution, unstructured working is supported, still identifying a minimum of possible automation-errors.

### On frontrunners and followers
2a.) frontrunners are agenda-lines that trigger the gathering of required information so that as the milestone 'meldefrist' gets processed by the human we have quality feedback from 90% of the participants that supports the decision whether the planned event will really have enough participants. So the 'meldefrist' means that an email with reverification-link has to be sent 7 days before the meldefrist, so that participants have time enough if anything has to be decided on their side (Maybe even this will need consulting).
2b.) followers are like agenda-lines that draw on the outcome of a milestone. But here I think it is better to implement it as "binding to the stage":  In a later implementation for instance we could implement the re-disposal of customer registrations as consequence of event-cancellation as a 'follower' to entering the stage 'canceled'.
3.)  

### Event-stages and graphql
NOTE: The event-stages are the way the whole process is getting 'summarized' for external systems like for instance crearis-vue: They might not sync all the agenda-lines, only need the ability to read them out if needed for single events via graphql. Mostly for those systems it is enough to know at what stage the event is + I think that it would be the default to publish all online-sessions before and after in-presence-events as soon as they last minimally 60mins. That would allow that the crearis-vue app has a 'calender-option' where the agenda of a whole region like Augsburg could be published and supervised -> this would bring a substantial offloading to the crearis-odoo we are implementing right now: No cross-company controlling or transient modelling is needed.