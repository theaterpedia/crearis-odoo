from odoo import models, fields, api # type: ignore
# from json_field import JsonField

# Default shortcodes for schedule parsing
DEFAULT_SCHEDULE_SHORTCODES = {
    '_online_': {'type': 'online', 'name': 'Online'},
}


class Company(models.Model):
    _inherit = "res.company"

    domain_code = fields.Many2one(
        'website', string='Domain Code', 
        required=False, domain="[('domain_code','!=','')]")

    use_msteams = fields.Boolean('MS Teams', readonly=False, default=False)
    use_jitsi = fields.Boolean('Jitsi Rooms', readonly=False, default=False)
    use_template_codes = fields.Boolean('Template Codes', readonly=False, default=False)
    use_tracks = fields.Boolean('Use Tracks', readonly=False, default=False)
    use_products = fields.Boolean('Use Products', readonly=False, default=False)
    use_overline = fields.Boolean('Use Overline', readonly=False, default=False)
    use_teasertext = fields.Boolean('Use Teasertext', readonly=False, default=False)

    # =========================
    # SCHEDULE CONFIGURATION
    # =========================
    
    schedule_shortcodes = fields.Json(
        string='Schedule Shortcodes',
        help='Mapping of shortcodes to location config. Format: {"_CODE_": {"type": "online|venue", "name": "...", "raum_id": N}}',
        default=lambda self: DEFAULT_SCHEDULE_SHORTCODES.copy()
    )
    
    schedule_locale = fields.Selection([
        ('de', 'German'),
        ('en', 'English'),
    ], default='de', string='Schedule Locale',
       help='Default locale for parsing schedule text (weekday codes, date format)')
    
    online_provider = fields.Selection([
        ('msteams', 'Microsoft Teams'),
        ('zoom', 'Zoom'),
        ('jitsi', 'Jitsi Meet'),
        ('other', 'Other'),
    ], default='msteams', string='Online Provider',
       help='Default video conference provider for online sessions') 