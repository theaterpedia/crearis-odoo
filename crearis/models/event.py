import logging
from odoo import models, fields, api # type: ignore

_logger = logging.getLogger(__name__)


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
    
    # Milestone configuration
    milestone_days_before = fields.Integer(
        string="Milestone Days Before",
        default=60,
        help="Default days before event start for deadline milestone (Meldefrist)"
    )

    # Schedule Template (Phase 5)
    schedule_template = fields.Json(
        string="Schedule Template",
        default=dict,
        help="Template for generating agenda lines. Structure: {sessions: [{day, start, end, mode, ...}]}"
    )
    schedule_template_note = fields.Text(
        string="Template Notes",
        help="Human-readable schedule pattern description (e.g., 'FR-SA-SO Block + Online vor/nach')"
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

    def name_get(self):
        """Ensure display_name returns the translated name properly."""
        result = []
        for record in self:
            name = record.name or ''
            result.append((record.id, name))
        return result


class EventEvent(models.Model):
    _name = 'event.event'  # Add this line - it was missing!
    _inherit = ["event.event", "web.options.abstract", "demo.data.mixin", "event.schedule.mixin"]
    _rec_name = "rectitle"

    # Teaching units
    units = fields.Float(
        string="Units",
        digits=(10, 2),
        help="Number of teaching units/credits for this event (e.g., 2.5 UE)"
    )

    teasertext = fields.Text('Teasertext', translate=True, default='')
    schedule = fields.Text('Schedule', translate=False, default='')
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
        tracking=True, domain="[('is_event_location','=',True),'|',('company_id','=',False),('company_id','=',company_id)]")
    
    # SharePoint location sync
    sp_raum_id = fields.Integer(
        string="SP Raum ID",
        index=True,
        help="SharePoint plan_raeume LookupId for location sync")

    # Session lines (flattened from schedule_data)
    # Renamed: session_line_ids → agenda_line_ids (2026-02-02)
    agenda_line_ids = fields.One2many(
        'agenda.line', 'event_id',
        string='Agenda Lines',
        help='Agenda lines: sessions, milestones, and other schedule items'
    )
    
    # Backward compatibility alias
    session_line_ids = fields.One2many(
        'agenda.line', 'event_id',
        string='Session Lines (deprecated)',
        help='DEPRECATED: Use agenda_line_ids instead'
    )

    domain_code = fields.Many2one(
        'website',
        string='Homedomain',
        help="Owner-domain for this event. Determines feature flags and data prefixes. "
             "Defaults to the company's default website. "
             "When template codes are active, initially set by event type on creation.",
        default=lambda self: self.env.company.domain_code,
        required=True,
        tracking=True,
    )

    website_id = fields.Many2one(
        string='Restrict to Website',
        help="Publishing scope: leave empty to show on ALL websites (typical). "
             "Set a value to restrict this event to one website only. "
             "This is NOT the owner-domain — see 'Homedomain' for that.",
    )

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
    
    @api.depends('domain_code', 'domain_code.use_milestones')
    def _compute_use_milestones(self):
        for event in self:
            if event.domain_code and hasattr(event.domain_code, 'use_milestones'):
                event.use_milestones = event.domain_code.use_milestones
            else:
                event.use_milestones = event.company_id.use_milestones if event.company_id else False
    
    owner_company = fields.Integer('Owner (Company)', compute=_compute_owner_company)
    use_msteams = fields.Boolean('MS Teams', compute=_compute_use_msteams)
    use_jitsi = fields.Boolean('Jitsi Rooms', compute=_compute_use_jitsi)
    use_template_codes = fields.Boolean('Use Codes', compute=_compute_use_template_codes)
    use_tracks = fields.Boolean(compute=_compute_use_tracks)
    use_products = fields.Boolean(compute=_compute_use_products)
    use_overline = fields.Boolean(compute=_compute_use_overline)
    use_teasertext = fields.Boolean(compute=_compute_use_teasertext)
    use_milestones = fields.Boolean('Use Milestones', compute=_compute_use_milestones)

    # ----------------------------------
    # Milestone Status (for E2 view)
    # ----------------------------------
    
    current_milestone_key = fields.Selection([
        ('deadline', 'Deadline'),
        ('info_mail', 'Info Mail'),
        ('wrap_up', 'Wrap-Up'),
    ], string='Current Milestone', compute='_compute_current_milestone_key', store=True,
       help="Which milestone type is currently active based on event stage")
    
    @api.depends('stage_id', 'stage_id.pipe_end')
    def _compute_current_milestone_key(self):
        """
        Determine current milestone based on event stage.
        
        Stage mapping (from 2026-02-02-details.md):
        - draft (sysreg 64) → deadline (Meldefrist)
        - confirmed (sysreg 512) → info_mail
        - released (sysreg 4096) → wrap_up
        - completed (sysreg 8192) → None
        """
        for event in self:
            if not event.stage_id:
                event.current_milestone_key = 'deadline'
                continue
            
            # Check stage by pipe_end (completed stages)
            if event.stage_id.pipe_end:
                event.current_milestone_key = False
                continue
            
            # Map stage sequence to milestone
            # Lower sequence = earlier stage
            seq = event.stage_id.sequence or 0
            if seq < 20:  # draft stages
                event.current_milestone_key = 'deadline'
            elif seq < 40:  # confirmed stages
                event.current_milestone_key = 'info_mail'
            else:  # released stages
                event.current_milestone_key = 'wrap_up'

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

    # =========================
    # Template Code Hook
    # =========================

    def _resolve_domain_code_for_template(self, event_type_id, vals):
        """Hook: resolve domain_code from event_type template code.

        Called when event_type_id is set during create() or write().
        Override in extending modules to map template codes to websites.

        Implementing modules should set vals['domain_code'] directly.
        The base implementation is a no-op.

        Args:
            event_type_id: int - event.type record ID being set
            vals: dict - mutable create/write vals
        """
        pass

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('event_type_id'):
                self._resolve_domain_code_for_template(vals['event_type_id'], vals)
        return super().create(vals_list)

    def write(self, vals):
        # Note: template-code hook intentionally fires on create() only.
        # domain_code is NOT auto-changed when event_type changes on existing records.
        # Users can set domain_code manually if needed.

        # Skip version increment when sync is updating metadata only
        if not self.env.context.get('skip_version_increment'):
            for rec in self:
                vals['version'] = rec.version + 1

        # Perform the write operation
        res = super(EventEvent, self).write(vals)

        # Invalidate cache to ensure fresh reads after write
        self.invalidate_recordset()

        return res

    # =========================
    # Agenda Line Sync (renamed from Session Line Sync)
    # =========================
    
    def _sync_agenda_lines(self):
        """
        Sync agenda_line_ids from schedule_data.sessions[] JSONB.
        
        Called after parsing schedule_raw → schedule_data.
        Clears and recreates session-type lines (no incremental update).
        Preserves milestone and other non-session lines.
        """
        AgendaLine = self.env['agenda.line']
        
        for event in self:
            # Clear existing SESSION lines only (preserve milestones, etc.)
            event.agenda_line_ids.filtered(
                lambda l: l.type == 'session' and l.source == 'json'
            ).unlink()
            
            # Get sessions from schedule_data
            sessions = (event.schedule_data or {}).get('sessions', [])
            if not sessions:
                continue
            
            # Get default provider from company
            default_provider = event.company_id.online_provider or 'msteams'
            
            # Create agenda lines for sessions
            for idx, sess in enumerate(sessions):
                vals = {
                    'event_id': event.id,
                    'sequence': idx * 10,
                    'type': 'session',
                    'source': 'json',
                    'locked_edits': True,
                    'day': sess.get('day'),
                    'date': sess.get('date'),
                    'start': sess.get('start'),
                    'end': sess.get('end'),
                    'duration_h': sess.get('duration_h', 0),
                    'mode': sess.get('type', 'venue'),  # Note: JSONB 'type' → model 'mode'
                    'location_hint': sess.get('location_hint'),
                    'room': sess.get('room'),
                    'notes': sess.get('notes'),
                    # Conference fields from JSONB (if present)
                    'conference_url': sess.get('conference_url'),
                    'conference_id': sess.get('conference_id'),
                    'conference_provider': sess.get('conference_provider') or (
                        default_provider if sess.get('type') == 'online' else False
                    ),
                }
                AgendaLine.create(vals)
    
    # Backward compatibility
    def _sync_session_lines(self):
        """DEPRECATED: Use _sync_agenda_lines instead."""
        return self._sync_agenda_lines()
    
    # =========================
    # Phase 5: Template-based Agenda Generation
    # =========================
    
    def _generate_agenda_from_template(self):
        """
        Generate agenda lines from event type's schedule_template.
        
        Algorithm (D8 Consecutive Days pattern):
        1. Anchor: First in-presence slot → anchored to date_begin
        2. In-presence block: Consecutive days from date_begin
        3. Pre-event online: Find matching weekday BEFORE date_begin
        4. Post-event online: Find next matching weekday AFTER last slot
        """
        from datetime import datetime, timedelta
        AgendaLine = self.env['agenda.line']
        
        for event in self:
            if not event.event_type_id or not event.date_begin:
                continue
            
            template = event.event_type_id.schedule_template or {}
            sessions = template.get('sessions', [])
            if not sessions:
                continue
            
            # Clear existing template-sourced lines
            event.agenda_line_ids.filtered(
                lambda l: l.type == 'session' and l.source == 'template'
            ).unlink()
            
            # Get event anchor date
            anchor_date = event.date_begin.date() if hasattr(event.date_begin, 'date') else event.date_begin
            
            # Separate online and venue sessions
            venue_sessions = [s for s in sessions if s.get('mode') != 'online']
            online_sessions = [s for s in sessions if s.get('mode') == 'online']
            
            # Map weekday codes to integers
            WEEKDAYS = {'MON': 0, 'TUE': 1, 'WED': 2, 'THU': 3, 'FRI': 4, 'SAT': 5, 'SUN': 6,
                        'MO': 0, 'DI': 1, 'MI': 2, 'DO': 3, 'FR': 4, 'SA': 5, 'SO': 6}
            
            # Resolve venue sessions (consecutive days from anchor)
            resolved = []
            for idx, sess in enumerate(venue_sessions):
                session_date = anchor_date + timedelta(days=idx)
                resolved.append({
                    **sess,
                    'resolved_date': session_date,
                    'sequence': (idx + 1) * 10,
                })
            
            # Resolve online sessions
            for sess in online_sessions:
                day_code = sess.get('day', '').upper()
                target_weekday = WEEKDAYS.get(day_code)
                if target_weekday is None:
                    continue
                
                position = sess.get('position', 'before')  # 'before' or 'after'
                
                if position == 'before':
                    # Find matching weekday BEFORE anchor
                    days_back = (anchor_date.weekday() - target_weekday) % 7
                    if days_back == 0:
                        days_back = 7  # Full week back
                    session_date = anchor_date - timedelta(days=days_back)
                    sequence = 5  # Before venue sessions
                else:
                    # Find matching weekday AFTER last resolved date
                    last_date = resolved[-1]['resolved_date'] if resolved else anchor_date
                    days_forward = (target_weekday - last_date.weekday()) % 7
                    if days_forward == 0:
                        days_forward = 7  # Full week forward
                    session_date = last_date + timedelta(days=days_forward)
                    sequence = len(resolved) * 10 + 50
                
                resolved.append({
                    **sess,
                    'resolved_date': session_date,
                    'sequence': sequence,
                })
            
            # Sort by date and create agenda lines
            resolved.sort(key=lambda x: (x['resolved_date'], x.get('start', '00:00')))
            
            for idx, sess in enumerate(resolved):
                session_date = sess['resolved_date']
                weekday_names = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
                
                vals = {
                    'event_id': event.id,
                    'sequence': (idx + 1) * 10,
                    'type': 'session',
                    'source': 'template',
                    'locked_edits': True,
                    'day': weekday_names[session_date.weekday()],
                    'date': session_date,
                    'start': sess.get('start'),
                    'end': sess.get('end'),
                    'duration_h': sess.get('duration_h', 0),
                    'mode': sess.get('mode', 'venue'),
                    'location_hint': sess.get('location_hint'),
                    'room': sess.get('room'),
                    'notes': sess.get('notes'),
                    'teaching_units': sess.get('teaching_units', 0),
                }
                AgendaLine.create(vals)
        
        return True
    
    def action_regenerate_from_template(self):
        """Action button: Regenerate agenda lines from event type template."""
        self._generate_agenda_from_template()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Template Applied',
                'message': f'Regenerated {len(self.agenda_line_ids.filtered(lambda l: l.source == "template"))} sessions from template.',
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_unlock_for_editing(self):
        """Action button: Unlock template-generated lines for manual editing."""
        self.agenda_line_ids.filtered(
            lambda l: l.source == 'template'
        ).write({'locked_edits': False, 'source': 'manual'})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Unlocked',
                'message': 'Agenda lines are now editable.',
                'type': 'info',
                'sticky': False,
            }
        }

    # ----------------------------------
    # Kanban Actions
    # ----------------------------------
    
    def action_show_template_info(self):
        """
        Dummy action for template code badge click in kanban view.
        Shows info about the event template/type.
        """
        self.ensure_one()
        template_name = self.event_type_id.name if self.event_type_id else 'Unknown'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': f'Template: {template_name}',
                'message': f'Event "{self.name}" uses template code "{template_name}". '
                           f'Click on the event card to see full details.',
                'type': 'info',
                'sticky': False,
            }
        }
