from odoo import models, fields, api

class EventWorkflow(models.Model):
    _name = "crearis.event.workflow"
    _description = "Agenda-types built with Track- or Session-templates + pre- and after-event-workflows"
    _order = "write_date, cid" 

    name = fields.Char('Title', translate=True, required=True, index=True)
    description = fields.Char('Title', translate=True)
    is_default = fields.Boolean('Default', default=False, help="This is the default Agenda-Type for this Domain")
    is_public = fields.Boolean('Public', default=False, help="This Agenda-Type is visible to the public")
    notes = fields.Text('Note', translate=True, help="Optional note with help/info about usage", default='')

    domain_id = fields.Manyone(
        "website",
        required=False, 
        string="Scope",
        ondelete="cascade",
        help="Use this Agenda-Type only on this Domain",
        index=True
    )


class EventWorkflowStep(models.Model):
    _name = "crearis.event.workflow.step"
    _description = "a Line on the Agenda, either a Track or a Session, Task, automated or manual"
    _order = "write_date, cid" 

    name = fields.Char('Title', translate=True, required=True, index=True)
    description = fields.Char('Title', translate=True)
    is_team_only = fields.Boolean('Team-Only', default=False, help="This Step is only visible to the Team")
    notes = fields.Text('Note', translate=True, help="Optional note with help/info about usage", default='')
    workflow_ids = fields.Many2many(
        "crearis.event.workflow",
        "crearis_event_workflow_step_rel",
        "step_id",
        "workflow_id",
        string="Agenda-Types",
        help="Agenda-Types that use this Step",
        index=True
    )
    event_type = fields.Manyone(
        "event.type",
        required=False, 
        string="Event Type",
        ondelete="cascade",
        help="Use this Step on this Event",
        index=True
    )    
    event = fields.Manyone(
        "event.event",
        required=False, 
        string="Event",
        ondelete="cascade",
        help="Use this Step on this Event",
        index=True
    )
    day = fields.Integer('Day', default=0, help="Day of the Event, 0=pre-event (default), 1=first day, 2=second day, -10=x days before event ...")
    duration = fields.Integer('Duration', default=0, help="Duration in minutes")
    start = fields.Datetime('Start', help="Start of this Step")
    type = fields.Selection(
        string='Type',
        selection=[('track.location', 'Track (Location)'), ('track.online', 'Track (Online)'), ('session', 'Session'), ('logic.task', 'Task'), ('logic.mile', 'Milestone'), ('logic.auto', 'Automation')],
        help="Type of Step",
        default='track.location')
    