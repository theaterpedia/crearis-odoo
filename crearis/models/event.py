from odoo import models, fields, api
import psycopg2

class JsonField(fields.Field):
    """
    Represents a postgresql Json column (JSON values are mapped to the Python equivalent type of list/dict).
    """
    type = 'json'  # Odoo type of the field (string)
    column_type = ('json', 'json')  # database column type (ident, spec)

    def convert_to_column(self, value, record, values=None, validate=True):
        """ Convert ``value`` from the ``write`` format to the SQL format. """
        # By default the psycopg2 driver does not know how to map dict/list to postgresql json types
        # We need to convert it to the right db type when inserting in the db
        # see https://www.psycopg.org/docs/extras.html
        if value is None:
            return None
        else:
            return psycopg2.extras.Json(value)

class EventEvent(models.Model):
    _inherit = "event.event"

    template_code = fields.Char('Event Template', translate=False, default='')
    teasertext = fields.Char('Teasertext', translate=True, default='')
    edit_mode = fields.Selection(
        string='Type',
        selection=[('locked', 'Locked'), ('blocks', 'edit blocks'), ('content', 'edit content'), ('full', 'edit all')],
        help="Type is used to control the dashboard-editing of the event.",
        default='content')
    blocks = JsonField('Pruvious Blocks', required=False, default=[])   # a json object represented as dict / list / python primitives, see: https://gist.github.com/danmana/5242f37b7d63daf4698de7c61c8b59fc