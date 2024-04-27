from odoo import models, fields, api

class DomainUser(models.Model):
    _name = "crearis.domainuser"
    _description = "Domain-Users"
    _order = "domain_id, role, user_id" 
    _rec_name = "cid"      

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
         ("user","Teilnehmer:in"),
         ("team","Team"),
         ("exec","Manager:in"),
         ("spec", "Special")],
        default='user')
    
    def _default_title(self):
        if self.role:
            return self.role.description
        else:
            return "Teilnehmer:in"

    name = fields.Char('Title', translate=False, default=_default_title, required=True)

    active = fields.Boolean("Active?", default=True)
    description = fields.Char('Description', translate=True, help="Short-Description of title/role of this user on this domain.", default='')
    capabilities = fields.Char('Capabilities', translate=False, help="Pruvious-Capabilities of this user on this domain.", default='')
    settings = fields.Json(default={})
    version = fields.Integer(default=1)  # we tweak this in def write  
    
    @api.depends("domain_id","role")
    def _compute_cid(self):
        for domainuser in self:
            if not domainuser.id:
                domainuser.cid = '{}.user-{}.{}'.format(domainuser.domain_id.domain_code, domainuser.role, "-1")
            else:
                domainuser.cid = '{}.user-{}.{}'.format(domainuser.domain_id.domain_code, domainuser.role, domainuser.id)

    cid = fields.Char("Crearis ID", translate=False,compute=_compute_cid)

    def json_data_store(self):  # see: from minutes 4:00 https://www.youtube.com/watch?v=MCmzTHcG5ec
        self.settings = {"capabilities":[self.capabilities]}

    def write(self, vals):
        # Code before write: 'self' has the old values
        vals['version'] = self.version + 1
        old_role = self.role
        old_name = self.name
        super().write(vals)
        # Code after write: 'self' has the new values
        new_role = self.role
        new_name = self.name
        if not self.env.context.get("_domainuser_write"): # we check for the flag '_domainuser_write' to prevent endless loops?
            if new_name == old_name and new_role != old_role:
                switch={
                    'user': "Teilnehmer:in",
                    'team': "Team",
                    'exec': "Manager:in",
                    'spec': "Special"
                    }
                self.with_context(_domainuser_write=True).write({"name": switch.get(self.role,'User')})

        return True