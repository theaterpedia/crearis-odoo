from odoo import models, fields, api # type: ignore


class EventType(models.Model):
    _inherit = 'event.type'

    # Template system
    is_template_code = fields.Boolean(
        string="Is Template Code",
        default=False,
        help="If True, name is a shortcode and has template_parent"
    )
    template_parent_id = fields.Many2one(
        'event.type',
        string="Template Parent",
        domain=[('is_template_code', '=', False)],
        help="Link to base event type (filter: is_template_code=False)"
    )

    # Template content fields (synced from SharePoint)
    template_cimg = fields.Text(
        string="Hero-Image-Link",
        translate=False,
        default='',
        help="xmlid or public url for hero and thumbnail image"
    )
    template_teasertext = fields.Text(
        string="Teaser Text",
        help="Short description for listings"
    )
    template_units = fields.Float(
        string="Teaching Units",
        digits=(10, 2),
        help="Default units/credits for events of this type"
    )
    template_heading = fields.Text(
        string="Website Heading",
        help="Heading for website display"
    )
    template_ext = fields.Json(
        string="Template Extensions",
        default=dict,
        help="JSONB for additional template settings"
    )
    template_config = fields.Integer(
        string="Config Flags",
        default=0,
        help="Bitmask of configuration flags"
    )

    # Sync tracking
    ms_id = fields.Char(string="SharePoint ID", index=True)
    ms_synced = fields.Boolean(string="Synced from SharePoint", default=False)
    ms_version = fields.Char(string="SharePoint Version", help="oversion for conflict detection")

    # Company isolation
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        help="Empty = available to all companies"
    )


class EventEvent(models.Model):
    _name = 'event.event'  # Add this line - it was missing!
    _inherit = ["event.event", "web.options.abstract", "demo.data.mixin"]
    _rec_name = "rectitle"

    # Teaching units
    units = fields.Float(
        string="Units",
        digits=(10, 2),
        help="Number of teaching units/credits for this event (e.g., 2.5 UE)"
    )

    teasertext = fields.Text('Teasertext', translate=True, default='')
    schedule = fields.Text('Schedule', translate=True, default='')
    edit_mode = fields.Selection(
        string='Type',
        selection=[('locked', 'Locked'), ('blocks', 'edit blocks'), ('content', 'edit content'), ('full', 'edit all')],
        help="Type is used to control the dashboard-editing of the event.",
        default='content')

    header_type = fields.Selection(
        string='Header',
        selection=[("simple", "simple"), ("columns", 'Text-Bild (2 Spalten)'), ("banner", "Banner medium"), ("cover", "Cover Fullsize"), ("bauchbinde", "Bauchbinde")],
        help="What header-type introduces the event?",
        default="simple")

    header_size = fields.Selection(
        string='Header-Size',
        selection=[("mini", "minimal"), ("medium", 'Medium'), ("prominent", "prominent"), ("full", "full")],
        help="How big is the header?",
        default="mini")
    
    cimg = fields.Text('Hero/Preview Image', translate=False, default='', help="xmlid or public url for hero and thumbnail image")
    md = fields.Text('Markdown Content', translate=True, help="Markdown body of the event.", default='')

    blocks = fields.Json()
    version = fields.Integer(default=1)

    address_id = fields.Many2one(
        'res.partner', string='Venue', default=lambda self: self.env.company.partner_id.id,
        tracking=True, domain="[('is_location_provider','=',True),'|',('company_id','=',False),('company_id','=',company_id)]")

    domain_code = fields.Many2one('website', string='Domain', default=lambda self: self.env.company.domain_code, required=True, tracking=True)

    space_id = fields.Many2one(
        'event.track.location', string='Home-Space', 
        tracking=True, domain="[('type','in',['space.msteams','space.jitsi']),('company_ids','in',owner_company)]")

    @api.depends("event_type_id", "name")
    def _compute_rectitle(self):
        for event in self:
            foreignDomain = event.domain_code.domain_code + ':' if event.domain_code.company_id != self.env.company else ''
            if event.use_template_codes:
                typeCode = event.event_type_id.name if event.event_type_id and event.event_type_id.name else 'ERROR '
                event.rectitle = '{}{} {}'.format(foreignDomain.lower(), typeCode.upper(), event.name)
            else:
                event.rectitle = '{} {}'.format(foreignDomain.lower(), event.name).lstrip()

    rectitle = fields.Char(translate=False, compute=_compute_rectitle)
    
    # ----------------------------------
    # Proxy-Fields for Company-based settings
    @api.depends("domain_code")
    def _compute_owner_company(self):
        for event in self:
            event.owner_company = event.domain_code.company_id 
    
    @api.depends("domain_code")
    def _compute_use_msteams(self):
        for event in self:
            event.use_msteams = event.domain_code.use_msteams

    @api.depends("domain_code")
    def _compute_use_jitsi(self):
        for event in self:
            event.use_jitsi = event.domain_code.use_jitsi
    
    @api.depends("domain_code")
    def _compute_use_template_codes(self):
        for event in self:
            event.use_template_codes = event.domain_code.use_template_codes

    @api.depends("domain_code")
    def _compute_use_tracks(self):
        for event in self:
            event.use_tracks = event.domain_code.use_tracks

    @api.depends("domain_code")
    def _compute_use_products(self):
        for event in self:
            event.use_products = event.domain_code.use_products

    @api.depends("domain_code")
    def _compute_use_overline(self):
        for event in self:
            event.use_overline = event.domain_code.use_overline
    
    @api.depends("domain_code")
    def _compute_use_teasertext(self):
        for event in self:
            event.use_teasertext = event.domain_code.use_overline
    
    owner_company = fields.Integer('Owner (Company)', compute=_compute_owner_company)
    use_msteams = fields.Boolean('MS Teams', compute=_compute_use_msteams)
    use_jitsi = fields.Boolean('Jitsi Rooms', compute=_compute_use_jitsi)
    use_template_codes = fields.Boolean('Use Codes', compute=_compute_use_template_codes)
    use_tracks = fields.Boolean(compute=_compute_use_tracks)
    use_products = fields.Boolean(compute=_compute_use_products)
    use_overline = fields.Boolean(compute=_compute_use_overline)
    use_teasertext = fields.Boolean(compute=_compute_use_teasertext)

    # ----------------------------------
    # crearis-interface

    @api.depends("domain_code", "event_type_id")
    def _compute_cid(self):
        """
        Compute stable content ID (cid) for events.
        
        Format: {domain}.event-{template_code}__{id}
        Examples:
          - dasei.event-a1__123 (with template codes)
          - dasei.event__123 (without template codes)
        
        CID is stable and NEVER changes after creation.
        """
        for event in self:
            domain_code = event.domain_code.domain_code if event.domain_code else 'unknown'
            
            if event.use_template_codes and event.event_type_id:
                template_code = event.event_type_id.name or ''
                cid_format = '{}.event-{}__{}'
                event.cid = cid_format.format(domain_code, template_code, event.id or 0)
            else:
                cid_format = '{}.event__{}'
                event.cid = cid_format.format(domain_code, event.id or 0)

    @api.depends("name")
    def _compute_slug(self):
        """
        Compute SEO-friendly slug from event name.
        
        Only auto-generates on creation (when slug is empty).
        Does NOT auto-update when name changes to preserve permalinks.
        Manual edit via "Edit Slug" button in UI.
        """
        import re
        for event in self:
            if not event.slug and event.name:
                # Convert to lowercase, replace spaces/special chars with underscore
                slug = event.name.lower()
                slug = re.sub(r'[äàáâ]', 'a', slug)
                slug = re.sub(r'[öòóô]', 'o', slug)
                slug = re.sub(r'[üùúû]', 'u', slug)
                slug = re.sub(r'[ß]', 'ss', slug)
                slug = re.sub(r'[ěéèê]', 'e', slug)
                slug = re.sub(r'[íìîï]', 'i', slug)
                slug = re.sub(r'[čćç]', 'c', slug)
                slug = re.sub(r'[řŕ]', 'r', slug)
                slug = re.sub(r'[šś]', 's', slug)
                slug = re.sub(r'[žźż]', 'z', slug)
                slug = re.sub(r'[ňń]', 'n', slug)
                slug = re.sub(r'[ýÿ]', 'y', slug)
                slug = re.sub(r'[ťt]', 't', slug)
                slug = re.sub(r'[ďd]', 'd', slug)
                slug = re.sub(r'[^a-z0-9]+', '_', slug)
                slug = slug.strip('_')
                event.slug = slug
            elif not event.slug:
                event.slug = ''

    @api.depends("cid", "slug")
    def _compute_cid_slug(self):
        """
        Compute combined permalink: {cid}__{slug}
        
        Example: dasei.event-a1__123__am_anfang_war_der_kreis
        """
        for event in self:
            if event.cid and event.slug:
                event.cid_slug = '{}_{}'.format(event.cid, event.slug)
            else:
                event.cid_slug = event.cid or ''

    cid = fields.Char("Crearis ID", translate=False, compute=_compute_cid, store=True)
    slug = fields.Char(
        "URL Slug",
        translate=False,
        compute=_compute_slug,
        store=True,
        readonly=False,
        help="SEO-friendly URL segment. Auto-generated from name, manually editable."
    )
    cid_slug = fields.Char(
        "CID+Slug",
        translate=False,
        compute=_compute_cid_slug,
        store=True,
        help="Combined permalink: {cid}__{slug}"
    )

    def action_regenerate_slug(self):
        """
        Manually regenerate slug from name.
        Called via "Regenerate" button in UI.
        """
        import re
        for event in self:
            if event.name:
                slug = event.name.lower()
                slug = re.sub(r'[äàáâ]', 'a', slug)
                slug = re.sub(r'[öòóô]', 'o', slug)
                slug = re.sub(r'[üùúû]', 'u', slug)
                slug = re.sub(r'[ß]', 'ss', slug)
                slug = re.sub(r'[ěéèê]', 'e', slug)
                slug = re.sub(r'[íìîï]', 'i', slug)
                slug = re.sub(r'[čćç]', 'c', slug)
                slug = re.sub(r'[řŕ]', 'r', slug)
                slug = re.sub(r'[šś]', 's', slug)
                slug = re.sub(r'[žźż]', 'z', slug)
                slug = re.sub(r'[ňń]', 'n', slug)
                slug = re.sub(r'[ýÿ]', 'y', slug)
                slug = re.sub(r'[ťt]', 't', slug)
                slug = re.sub(r'[ďd]', 'd', slug)
                slug = re.sub(r'[^a-z0-9]+', '_', slug)
                slug = slug.strip('_')
                event.slug = slug
        return True

    # SharePoint sync fields
    ms_id = fields.Char(string="SharePoint ID", index=True)
    ms_version = fields.Char(string="SP etag", help="Last seen SharePoint etag")
    ms_pushed_version = fields.Integer(string="Pushed Version", help="Odoo version at last push to SP")
    ms_synced = fields.Boolean(string="Synced from SharePoint", default=False)

    def write(self, vals):
        # Skip version increment when sync is updating metadata only
        if not self.env.context.get('skip_version_increment'):
            for rec in self:
                vals['version'] = rec.version + 1

        # Perform the write operation
        res = super(EventEvent, self).write(vals)

        # Invalidate cache to ensure fresh reads after write
        self.invalidate_recordset()

        return res
