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

class DomainUser(models.Model):
    _name = "crearis.domain.user"
    _description = "Domain-Users"
    _order = "domain_id, role, user_id"        

    domain_id = fields.Many2one(
        "website",
        required=True, 
        string="Domain",
        ondelete="cascade",
        help="Domain/Website the chosen user can access to.",
        index=True,
    )
    user_id = fields.Many2one(
        "res.users",
        required=True, 
        string="User",
        ondelete="cascade",
        help="User that access to the chosen domain/website.",
        index=True,
    )
    role = fields.Selection(
        selection=[
         ("user","User"),
         ("team","Team"),
         ("exec","Manager"),
         ("spec", "Special")],
        default='user')
    title = fields.Char('Title', translate=True, default='')
    description = fields.Char('Description', translate=True, help="Short-Description of title/role of this user on this domain.", default='')
    capabilities = fields.Char('Capabilities', translate=False, help="Pruvious-Capabilities of this user on this domain.", default='')   
    capas = JsonField('Capas', required=False, default=[]) 
