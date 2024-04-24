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

class BlogPost(models.Model):
    _inherit = "blog.post"

    description = fields.Char('Teasertext', translate=True, default='')
    blocks = JsonField('Pruvious Blocks', required=False, default=[])   # a json object represented as dict / list / python primitives, see: https://gist.github.com/danmana/5242f37b7d63daf4698de7c61c8b59fc
    # homesite_id = fields.Integer('Homesite', default=4)
    homesite_id = fields.Many2one(
        "website",
        string="Homesite",
        ondelete="restrict",
        help="Editing only allowed from this website.",
        index=True,
    )
    