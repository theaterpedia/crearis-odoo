# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api
from odoo.exceptions import UserError
import json


class DomainUser(models.Model):
    _name = "crearis.domainuser"
    _inherit = ['web.options.abstract', "demo.data.mixin"]
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
    
    domain_code = fields.Char(
        string='Domain Code',
        related='domain_id.domain_code',
        readonly=True,
        store=False,
        help='Domain code from the website'
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
            return dict(self._fields['role'].selection).get(self.role, "Teilnehmer:in")
        else:
            return "Teilnehmer:in"

    name = fields.Char('Title', translate=True, default=_default_title, required=True)

    active = fields.Boolean("Active?", default=True)
    description = fields.Text(
        'Description', 
        translate=True, 
        help="Kurzbeschreibung / Teasertext / Suchmaschine",
        default=''
    )

    # Domain-user specific header fields (not in options JSON)
    header_type = fields.Selection(
        string='Header',
        selection=[
            ("simple", "simple"),
            ("columns", 'Text-Bild (2 Spalten)'),
            ("banner", "Banner medium"),
            ("cover", "Cover Fullsize"),
            ("bauchbinde", "Bauchbinde")
        ],
        help="What header-type introduces the role?",
        default="simple"
    )

    header_size = fields.Selection(
        string='Header-Size',
        selection=[
            ("mini", "minimal"),
            ("medium", 'Medium'),
            ("prominent", "prominent"),
            ("full", "full")
        ],
        help="How big is the header?",
        default="mini"
    )
    
    cimg = fields.Text('Hero/Preview Image', translate=False, default='', help="xmlid or public url for hero and thumbnail image")
    md = fields.Text('Markdown Content', translate=True, help="Custom Markdown body for the user on this domain.", default='')

    settings = fields.Json(
        string='Settings',
        help='JSON structure containing security and content settings',
        default={}
    )

    # SCL: MS Teams meeting data (D3, R5)
    # Only relevant for exec role users
    # Keys: videocall_url, videocall_id, phonecall_id, phonecall_conference_id, passkey
    # NOTE: login_info_html is computed, not stored - use get_teams_login_html()
    teams_meeting_data = fields.Json(
        string='Teams Meeting Data',
        help='MS Teams meeting credentials for consulting calls. '
             'Keys: videocall_url, videocall_id, phonecall_id, phonecall_conference_id, passkey',
        default={}
    )
    
    # Text proxy for editing Json field in form view (Odoo 16 workaround)
    teams_meeting_data_text = fields.Text(
        string='Teams Data (JSON)',
        compute='_compute_teams_meeting_data_text',
        inverse='_inverse_teams_meeting_data_text',
    )
    
    @api.depends('teams_meeting_data')
    def _compute_teams_meeting_data_text(self):
        for rec in self:
            data = rec.teams_meeting_data or {}
            rec.teams_meeting_data_text = json.dumps(data, indent=2) if data else '{}'
    
    def _inverse_teams_meeting_data_text(self):
        for rec in self:
            text = (rec.teams_meeting_data_text or '').strip()
            if not text or text == '{}':
                rec.teams_meeting_data = {}
            else:
                try:
                    rec.teams_meeting_data = json.loads(text)
                except json.JSONDecodeError:
                    rec.teams_meeting_data = {}

    def get_teams_login_html(self):
        """Compute HTML from teams_meeting_data fields (no manual duplication)."""
        self.ensure_one()
        data = self.teams_meeting_data or {}
        if isinstance(data, str):
            import json
            try:
                data = json.loads(data.replace('\n', '\\n').replace('\r', ''))
            except (json.JSONDecodeError, TypeError):
                data = {}
        
        if not data:
            return ''
        
        parts = []
        videocall_url = data.get('videocall_url', '')
        videocall_id = data.get('videocall_id', '')
        passkey = data.get('passkey', '')
        phonecall_id = data.get('phonecall_id', '')
        phonecall_conference_id = data.get('phonecall_conference_id', '')
        
        if videocall_url:
            parts.append(f'<a href="{videocall_url}">Zum Meeting beitreten</a>')
        if videocall_id:
            parts.append(f'Besprechungs-ID: {videocall_id}')
        if passkey:
            parts.append(f'Passcode: {passkey}')
        
        if phonecall_id:
            parts.append('<hr style="margin: 10px 0;"/>')
            parts.append('Oder per Telefon einwählen:')
            parts.append(f'<a href="tel:{phonecall_id.replace(" ", "").replace(",", ",")}">{phonecall_id}</a>')
            if phonecall_conference_id:
                parts.append(f'Telefonkonferenz-ID: {phonecall_conference_id}')
        
        return '<br/>'.join(parts)

    version = fields.Integer(default=1)

    # ==================== SECURITY SECTION ====================
    
    capabilities = fields.Char(
        string='Capabilities',
        compute='_compute_capabilities',
        inverse='_inverse_capabilities',
        store=False,
        help='User capabilities | Comma-separated list of capabilities/permissions for this user on this domain'
    )

    # ==================== CONTENT SECTION ====================
    
    custom_md = fields.Boolean(
        string='Custom Markdown',
        compute='_compute_custom_md',
        inverse='_inverse_custom_md',
        store=False,
        help='Enable custom markdown | Allow custom markdown content for this domain user'
    )
    
    content_options = fields.Text(
        string='Content Options',
        compute='_compute_content_options',
        inverse='_inverse_content_options',
        store=False,
        translate=False,
        help='Additional content options | Miscellaneous content-related options as key-value pairs or JSON'
    )

    # ==================== COMPUTE METHODS ====================

    @api.depends('settings')
    def _compute_capabilities(self):
        """Compute capabilities from settings JSON."""
        for record in self:
            capabilities = record.get_setting('security', 'capabilities', [])
            if isinstance(capabilities, list):
                record.capabilities = ', '.join(str(v) for v in capabilities)
            else:
                record.capabilities = str(capabilities) if capabilities else ''

    def _inverse_capabilities(self):
        """Store capabilities back to settings JSON."""
        for record in self:
            if record.capabilities:
                value_list = [v.strip() for v in record.capabilities.split(',') if v.strip()]
                record.set_setting('security', 'capabilities', value_list)
            else:
                record.remove_setting('security', 'capabilities')

    @api.depends('settings')
    def _compute_custom_md(self):
        """Compute custom_md from settings JSON."""
        for record in self:
            record.custom_md = record.get_setting('content', 'custom_md', False)

    def _inverse_custom_md(self):
        """Store custom_md back to settings JSON and clear md field if False."""
        for record in self:
            if record.custom_md:
                record.set_setting('content', 'custom_md', record.custom_md)
            else:
                record.remove_setting('content', 'custom_md')
                record.write({'md': ''})

    @api.depends('settings')
    def _compute_content_options(self):
        """Compute content_options from settings JSON."""
        for record in self:
            record.content_options = record.get_setting('content', 'options', '')

    def _inverse_content_options(self):
        """Store content_options back to settings JSON."""
        for record in self:
            if record.content_options:
                record.set_setting('content', 'options', record.content_options)
            else:
                record.remove_setting('content', 'options')

    # ==================== OVERRIDE CUSTOM HEADER INVERSE ====================
    
    def _inverse_custom_header(self):
        """Override to also clear domainuser-specific header fields."""
        # Call parent method to handle format_options
        super()._inverse_custom_header()
        
        # Additionally clear domainuser-specific header fields if custom_header is False
        for record in self:
            if not record.custom_header:
                record.write({
                    'header_type': 'simple',
                    'header_size': 'mini',
                    'cimg': ''
                })

    # ==================== HELPER METHODS FOR SETTINGS ====================

    def get_setting(self, section, option_name, default=None):
        """
        Helper method to get a specific setting value from any section.
        
        Args:
            section (str): Section name ('security', 'content')
            option_name (str): Name of the setting
            default: Default value if setting doesn't exist
            
        Returns:
            The setting value or default
        """
        self.ensure_one()
        if not self.settings or not isinstance(self.settings, dict):
            return default
        section_settings = self.settings.get(section, {})
        return section_settings.get(option_name, default)

    def set_setting(self, section, option_name, value):
        """
        Helper method to set a specific setting value in any section.
        Only sets the value if it's not empty/False.
        
        Args:
            section (str): Section name ('security', 'content')
            option_name (str): Name of the setting
            value: Value to set
        """
        self.ensure_one()
        if not value and not isinstance(value, bool):
            return
            
        current_settings = self.settings or {}
        if section not in current_settings:
            current_settings[section] = {}
        current_settings[section][option_name] = value
        self.settings = current_settings

    def remove_setting(self, section, option_name):
        """
        Helper method to remove a specific setting from a section.
        Also removes empty sections to keep settings clean.
        
        Args:
            section (str): Section name ('security', 'content')
            option_name (str): Name of the setting to remove
        """
        self.ensure_one()
        if not self.settings or not isinstance(self.settings, dict):
            return
            
        current_settings = self.settings.copy()
        if section in current_settings and option_name in current_settings[section]:
            del current_settings[section][option_name]
            
            if not current_settings[section]:
                del current_settings[section]
                
            self.settings = current_settings

    # ==================== EXISTING METHODS ====================
    
    @api.depends("domain_id","role")
    def _compute_cid(self):
        for domainuser in self:
            if not domainuser.id:
                domainuser.cid = '{}.user-{}.{}'.format(domainuser.domain_id.domain_code, domainuser.role, "-1")
            else:
                domainuser.cid = '{}.user-{}.{}'.format(domainuser.domain_id.domain_code, domainuser.role, domainuser.id)

    cid = fields.Char("Crearis ID", translate=False, compute=_compute_cid)

    def write(self, vals):
        vals['version'] = self.version + 1
        old_role = self.role
        old_name = self.name
        
        res = super(DomainUser, self).write(vals)
        self.invalidate_recordset()

        new_role = self.role
        new_name = self.name
        if not self.env.context.get("_domainuser_write"):
            if new_name == old_name and new_role != old_role:
                switch = {
                    'user': "Teilnehmer:in",
                    'team': "Team",
                    'exec': "Manager:in",
                    'spec': "Special"
                }
                self.with_context(_domainuser_write=True).write({"name": switch.get(self.role, 'User')})
        
        return res