from odoo import models, fields, api
# from json_field import JsonField

class EventEvent(models.Model):
    _inherit = "event.event"

    template_code = fields.Char('Event Template', translate=False, default='')
    teasertext = fields.Char('Teasertext', translate=True, default='')
    edit_mode = fields.Selection(
        string='Type',
        selection=[('locked', 'Locked'), ('blocks', 'edit blocks'), ('content', 'edit content'), ('full', 'edit all')],
        help="Type is used to control the dashboard-editing of the event.",
        default='content')
    # blocks = JsonField('Pruvious Blocks', required=False, default=[])   # a json object represented as dict / list / python primitives, see: https://gist.github.com/danmana/5242f37b7d63daf4698de7c61c8b59fc
    blocks = fields.Json()
