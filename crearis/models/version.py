from odoo import models, fields, api

class Version(models.Model):
    _name = "crearis.version"
    _description = "Versions-Table to track Odoo-changesets via Redis"
    _order = "write_date, cid" 

    name = fields.Char('Title', translate=False)
    cid = fields.Char('Crearis ID', translate=False, required=True)
    version = fields.Integer(default=0)
    vtype = fields.Selection(
        string="Version Type",
        selection=[
         ("7","7 days"),
         ("m","main"),
         ("i","incremental"),
         ("d", "delete"),
         ("r", "reload")],
        default='7')
    domain_ids = fields.Many2many(
        "website",
        required=False, 
        string="Domains",
        ondelete="cascade",
        help="Domain/Website the chosen user can access to.",
        index=True
    )
    note = fields.Char('Note', translate=True, help="Optional note with info about changes.", default='')
    author_id = fields.Many2one(
        "res.users",
        string="Author",
        help="Author of the change to the data.",
        index=True,
    ) 
    Vals = fields.Json(string="Values")
    version = fields.Integer(default=1)  # we tweak this in def write  

