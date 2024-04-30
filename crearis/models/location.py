# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia E.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _, api, models, fields

class ResPartner(models.Model):
    _inherit = "res.partner"

    version = fields.Integer(default=1)  # we tweak this in def write  

    def _compute_cid(self):
        for partner in self:
            prtn_id = partner.id or -1
            if not partner.website_id:
                subnetCode = self.env['ir.config_parameter'].sudo().get_param('crearis.subnetCode')
                partner.cid = '{}.partner-{}.{}'.format(subnetCode, partner.company_type, prtn_id)
            else:
                partner.cid = '{}.partner-{}.{}'.format(partner.website_id.domain_code, partner.company_type, prtn_id)

    cid = fields.Char("Crearis ID", translate=False,compute=_compute_cid)

    is_location_provider = fields.Boolean(string='Has one or more phyiscal locations for creative work', default=False,
        help="Check if the contact serves locations for cultural work: venue, co-working, spots in nature or city")  

    def _default_category(self):
        return self.env['res.partner.category'].browse(self._context.get('category_id'))

    def _write_category_id(self):
        for partner in self:
            partner.is_location_provider = True if 8 in partner.category_id.ids else False

    category_id = fields.Many2many('res.partner.category', column1='partner_id',
                                    column2='category_id', string='Tags', default=_default_category, inverse='_write_category_id')

    def write(self, vals):
        # Code before write: 'self' has the old values
        vals['version'] = self.version + 1
        old_title = self.title
        old_type = self.type
        old_lang = self.lang
        old_name = self.name
        old_street = self.street
        old_street2 = self.street2
        old_zip = self.zip
        old_city = self.city
        old_mobile = self.mobile
        old_email = self.email                                              
        super().write(vals)
        # Code after write: 'self' has the new values

        if not self.env.context.get("_partner_write"): # we check for the flag '_domainuser_write' to prevent endless loops?
            changes = {}
            if self.name != old_name: changes['name'] = self.name
            if self.type != old_type:  changes['type'] = self.type
            if self.title != old_title: changes['title'] = self.title
            if self.street != old_street: changes['street'] = self.street
            if self.street2 != old_street2: changes['street2'] = self.street2
            if self.zip != old_zip: changes['zip'] = self.zip
            if self.city != old_city: changes['city'] = self.city
            if self.mobile != old_mobile: changes['mobile'] = self.mobile
            if self.email != old_email: changes['email'] = self.email

            # TODO  write changes to crearis.version

        return True



# LOCATION-SPACES
# may be be further refined later to allow for finegrained configuration of how these ressources are publicly available
# - set up location spaces independently from domains
# - configure usage of these locations for companies/websites in a separate model (or many2many-relation with additional managed props)

# location-spaces of a company (which is not a crearis.location) typically are available within that company only, 
# they should default to the domain of that company
# - here we provide access to MS-Teams and similar integrations for structured online-conferencing
# -

class Location(models.Model):
    _inherit = "event.track.location"
    _description = "Location"      

    provider_id = fields.Many2one(
        string="Address/Provider",
        comodel_name="res.partner",
        domain=[('is_location_provider','=',True)],
        help="venue, spot, office where the space is located",
        ondelete="restrict",
        index=True,
    )

    description = fields.Char('Description', translate=True, help="Short-Description of the space.", default='')
    # active = fields.Boolean("Active?", default=True)
    type = fields.Selection([("location.venue", "venue"),("location.office", "office"),("location.nature", "nature"),("location.street", "street"),("space.ms-teams", "online (teams)"),("space.online", "online")], default="location.venue", string="Space-Type")
    is_default = fields.Boolean("Default Space?", help="is it the default space at this address?", default=False)
    site_id = fields.Char('MS Site ID', translate=False)
    list_id = fields.Char('MS List ID', translate=False)
    drive_id = fields.Char('MS Drive ID', translate=False)

    company_ids = fields.Many2many(
        string="Companies",
        comodel_name="res.company",
        relation="crearis_company_location_rel",
        column1="loc_id",
        column2="company_id",
        required=False,
        help="Companies that book this location (are allowed to)",
        index=True,
    )

    def name_get(self):
        res = []
        for location in self:
            # event or its tickets are sold out
            if location.provider_id:
                name = _('%(prov_name)s [%(loc_name)s]', loc_name=location.name, prov_name=location.provider_id.name)
            else:
                name = location.name
            res.append((location.id, name))
        return res