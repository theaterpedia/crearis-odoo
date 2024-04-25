from odoo import models, fields, api

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
    name = fields.Char('Title', translate=True, default='Teilnehmer:in', required=True)
    active = fields.Boolean("Active?", default=True)
    description = fields.Char('Description', translate=True, help="Short-Description of title/role of this user on this domain.", default='')
    capabilities = fields.Char('Capabilities', translate=False, help="Pruvious-Capabilities of this user on this domain.", default='')
    settings = fields.Json(default={})

    def json_data_store(self):  # see: from minutes 4:00 https://www.youtube.com/watch?v=MCmzTHcG5ec
        self.settings = {"capabilities":[self.capabilities]}
