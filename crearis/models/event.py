from odoo import models, fields, api
# from json_field import JsonField

class EventEvent(models.Model):
    _inherit = "event.event"
    _rec_name = "rectitle"

    teasertext = fields.Text('Teasertext', translate=True, default='')
    schedule = fields.Text('Schedule', translate=True, default='')
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
        tracking=True, domain="[('type','in',['space.ms-teams','space.online']),('company_ids','in',company_id)]")

    address_id = fields.Many2one(
        'res.partner', string='Venue', default=lambda self: self.env.company.partner_id.id,
        tracking=True, domain="[('is_location_provider','=',True),'|',('company_id','=',False),('company_id','=',company_id)]")

    domain_code = fields.Many2one('website', string='Domain', default=lambda self: self.env.company.domain_code, required=True, tracking=True)

    @api.depends("event_type_id", "name")
    def _compute_rectitle(self):
        useTemplates=lambda self: self.env.company.use_templates
        for event in self:
            if useTemplates:
                typeCode = event.event_type_id.name if event.event_type_id and event.event_type_id.name else 'ERROR'
                event.rectitle = '{} {}'.format(typeCode, event.name)
            else:
                event.rectitle = '{} {}'.format(event.name)

    rectitle = fields.Char(translate=False,compute=_compute_rectitle)
    
    # ----------------------------------
    # Proxy-Fields for Company-based settings
    @api.depends("domain_code")
    def _compute_use_channels(self):
        for event in self:
            event.use_channels = event.domain_code.use_channels

    @api.depends("domain_code")
    def _compute_use_rooms(self):
        for event in self:
            event.use_rooms = event.domain_code.use_rooms
    
    @api.depends("domain_code")
    def _compute_use_company_templates(self):
        for event in self:
            event.use_company_templates = event.domain_code.use_company_templates

    @api.depends("domain_code")
    def _compute_use_tracks(self):
        for event in self:
            event.use_tracks = event.domain_code.use_tracks

    @api.depends("domain_code")
    def _compute_use_products(self):
        for event in self:
            event.use_products = event.domain_code.use_products

    @api.depends("domain_code")
    def _compute_use_overline(self):
        for event in self:
            event.use_overline = event.domain_code.use_overline
    
    #TODO: _009 implement use_teasertext
    @api.depends("domain_code")
    def _compute_use_teasertext(self):
        for event in self:
            event.use_teasertext = event.domain_code.use_overline
    
    use_channels = fields.Boolean(compute=_compute_use_channels)
    use_rooms = fields.Boolean(compute=_compute_use_rooms)
    use_company_templates = fields.Boolean(compute=_compute_use_company_templates)
    use_tracks = fields.Boolean(compute=_compute_use_tracks)
    use_products = fields.Boolean(compute=_compute_use_products)
    use_overline = fields.Boolean(compute=_compute_use_overline)
    use_teasertext = fields.Boolean(compute=_compute_use_teasertext)


    # ----------------------------------
    # crearis-interface

    @api.depends("website_id")
    def _compute_cid(self):
        event_code = 'default'
        domain_code = 'default'
        for event in self:
            if not event.id:
                event.cid = '{}.event-{}.{}'.format(domain_code, event_code, "-1")
            else:
                event.cid = '{}.event-{}.{}'.format(domain_code, event_code, event.id)
    
    cid = fields.Char("Crearis ID", translate=False,compute=_compute_cid)

    def write(self, vals):
        # Code before write: 'self' has the old values
        vals['version'] = self.version + 1
        super().write(vals)
        # Code after write: 'self' has the new values

        return True
