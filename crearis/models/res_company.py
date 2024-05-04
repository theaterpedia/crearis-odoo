from odoo import models, fields, api
# from json_field import JsonField

class Company(models.Model):
    _inherit = "res.company"

    domain_code = fields.Many2one(
        'website', string='Domain Code', 
        required=False, domain="[('domain_code','!=','')]")

    use_spaces = fields.Boolean('Use Spaces', readonly=False, default=False)
    use_rooms = fields.Boolean('Use Rooms', readonly=False, default=False)
    use_template_codes = fields.Boolean('Template Codes', readonly=False, default=False)
    use_tracks = fields.Boolean('Use Tracks', readonly=False, default=False)
    use_products = fields.Boolean('Use Products', readonly=False, default=False)
    use_overline = fields.Boolean('Use Overline', readonly=False, default=False)
    use_teasertext = fields.Boolean('Use Teasertext', readonly=False, default=False) 