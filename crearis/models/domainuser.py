from odoo import models, fields, api
from odoo.exceptions import UserError

class DomainUser(models.Model):
    _name = "crearis.domainuser"
    _description = "Domain-Users"
    _order = "domain_id, role, user_id" 
    _rec_name = "cid"      

    domain_id = fields.Many2one(
        "website",
        required=True, 
        string="Domain",
        domain=[('domain_code', 'not like', "X_EMPTY")],
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
    md = fields.Text('Markdown Content', translate=False, help="Markdown content for user profile.", default='')
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

    cid = fields.Char("Crearis ID", translate=False, compute=_compute_cid)

    def json_data_store(self):
        """Store capabilities string as JSON array in settings field."""
        for record in self:
            if not record.capabilities:
                raise UserError("Capabilities field is empty. Please enter capabilities before saving.")
            
            # Split capabilities by comma and clean whitespace
            capabilities_list = [cap.strip() for cap in record.capabilities.split(',') if cap.strip()]
            
            # Update settings, preserving other keys if they exist
            current_settings = record.settings or {}
            current_settings['capabilities'] = capabilities_list
            
            record.settings = current_settings
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Capabilities saved to settings.',
                'type': 'success',
                'sticky': False,
            }
        }

    def write(self, vals):
        # Code before write: 'self' has the old values
        vals['version'] = self.version + 1
        old_role = self.role
        old_name = self.name
        
        res = super(DomainUser, self).write(vals)
        
        # Invalidate cache - try invalidate_recordset() for Odoo 16
        self.invalidate_recordset()

        # Code after write: 'self' has the new values
        new_role = self.role
        new_name = self.name
        if not self.env.context.get("_domainuser_write"): # we check for the flag '_domainuser_write' to prevent endless loops?
            if new_name == old_name and new_role != old_role:
                switch = {
                    'user': "Teilnehmer:in",
                    'team': "Team",
                    'exec': "Manager:in",
                    'spec': "Special"
                }
                self.with_context(_domainuser_write=True).write({"name": switch.get(self.role, 'User')})
        
        return res