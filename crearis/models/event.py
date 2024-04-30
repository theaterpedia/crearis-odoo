from odoo import models, fields, api
# from json_field import JsonField

class EventEvent(models.Model):
    _inherit = "event.event"
    _rec_name = "rectitle"

    template_code = fields.Char('Event Template', translate=False, default='')
    teasertext = fields.Char('Teasertext', translate=True, default='')
    edit_mode = fields.Selection(
        string='Type',
        selection=[('locked', 'Locked'), ('blocks', 'edit blocks'), ('content', 'edit content'), ('full', 'edit all')],
        help="Type is used to control the dashboard-editing of the event.",
        default='content')
    # blocks = JsonField('Pruvious Blocks', required=False, default=[])   # a json object represented as dict / list / python primitives, see: https://gist.github.com/danmana/5242f37b7d63daf4698de7c61c8b59fc
    blocks = fields.Json()
    version = fields.Integer(default=1)  # we tweak this in def write  

    space_id = fields.Many2one(
        'event.track.location', string='Home-Space', 
        tracking=True, domain="[('type','in',['space.ms-teams','space.online']),('website','in',domain_ids)]")

    address_id = fields.Many2one(
        'res.partner', string='Venue', default=lambda self: self.env.company.partner_id.id,
        tracking=True, domain="[('is_location_provider','=',True),'|',('company_id','=',False),('company_id','=',company_id)]")

    @api.depends("template_code", "name")
    def _compute_rectitle(self):
        for event in self:
            if event.template_code:
                event.rectitle = '{} {}'.format(event.template_code, event.name)
            else:
                event.rectitle = event.name

    rectitle = fields.Char(translate=False,compute=_compute_rectitle)
    
    @api.depends("website_id","template_code")
    def _compute_cid(self):
        for event in self:
            if not event.id:
                event.cid = '{}.event-{}.{}'.format(event.website_id.domain_code, event.template_code, "-1")
            else:
                event.cid = '{}.event-{}.{}'.format(event.website_id.domain_code, event.template_code, event.id)
    
    cid = fields.Char("Crearis ID", translate=False,compute=_compute_cid)

    def write(self, vals):
        # Code before write: 'self' has the old values
        vals['version'] = self.version + 1
        super().write(vals)
        # Code after write: 'self' has the new values

        return True
