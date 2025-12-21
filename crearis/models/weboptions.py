# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api


class WebOptionsAbstract(models.AbstractModel):
    """
    Abstract model for managing web options with separate JSON fields for page, aside, header, and footer.
    Can be inherited by any model that needs these capabilities.
    """
    _name = 'web.options.abstract'
    _description = 'Web Options Abstract Model'

    # ==================== JSON FIELDS FOR EACH SECTION ====================
    
    page_options = fields.Json(
        string='Page Options',
        help='JSON structure containing page options: background, cssvars, navigation, etc.',
        default=False
    )
    
    aside_options = fields.Json(
        string='Aside Options',
        help='JSON structure containing aside/sidebar options: postit, toc, list, context, etc.',
        default=False
    )
    
    header_options = fields.Json(
        string='Header Options',
        help='JSON structure containing header options: alert, postit, etc.',
        default=False
    )
    
    footer_options = fields.Json(
        string='Footer Options',
        help='JSON structure containing footer options: gallery, slider, sitemap, etc.',
        default=False
    )

    # ==================== BUTTON STATE COMPUTED FIELDS ====================
    
    page_has_content = fields.Boolean(
        string='Page Has Content',
        compute='_compute_page_has_content',
        store=True,  # Changed from False to True
        help='Whether page_options has any content'
    )
    
    aside_has_content = fields.Boolean(
        string='Aside Has Content',
        compute='_compute_aside_has_content',
        store=True,  # Changed from False to True
        help='Whether aside_options has any content'
    )
    
    header_has_content = fields.Boolean(
        string='Header Has Content',
        compute='_compute_header_has_content',
        store=True,  # Changed from False to True
        help='Whether header_options has any content'
    )
    
    footer_has_content = fields.Boolean(
        string='Footer Has Content',
        compute='_compute_footer_has_content',
        store=True,  # Changed from False to True
        help='Whether footer_options has any content'
    )

    # ==================== CHANGE DETECTION COMPUTED FIELDS ====================
    
    page_has_changes = fields.Boolean(
        string='Page Has Unsaved Changes',
        compute='_compute_page_has_changes',
        store=False
    )
    
    aside_has_changes = fields.Boolean(
        string='Aside Has Unsaved Changes',
        compute='_compute_aside_has_changes',
        store=False
    )
    
    header_has_changes = fields.Boolean(
        string='Header Has Unsaved Changes',
        compute='_compute_header_has_changes',
        store=False
    )
    
    footer_has_changes = fields.Boolean(
        string='Footer Has Unsaved Changes',
        compute='_compute_footer_has_changes',
        store=False
    )

    # ==================== INDIVIDUAL FIELD ACCESSORS ====================
    # These provide backward compatibility and easy access to individual options

    # PAGE OPTIONS
    page_background = fields.Selection(
        string='Background',
        selection=[
            ('primary', 'Primary'),
            ('secondary', 'Secondary'),
            ('accent', 'Accent'),
            ('neutral', 'Neutral'),
            ('muted', 'Muted'),
            ('positive', 'Positive'),
            ('negative', 'Negative'),
            ('warning', 'Warning')
        ],
        compute='_compute_page_background',
        inverse='_inverse_page_background',
        store=False
    )
    
    page_cssvars = fields.Text(
        string='CSS Variables',
        compute='_compute_page_cssvars',
        inverse='_inverse_page_cssvars',
        store=False
    )
    
    page_navigation = fields.Text(
        string='Navigation',
        compute='_compute_page_navigation',
        inverse='_inverse_page_navigation',
        store=False
    )
    
    page_options_text = fields.Text(
        string='Options (Page)',
        compute='_compute_page_options_text',
        inverse='_inverse_page_options_text',
        store=False
    )

    # ASIDE OPTIONS
    aside_postit = fields.Text(
        string='Post-it (Aside)',
        compute='_compute_aside_postit',
        inverse='_inverse_aside_postit',
        store=False
    )
    
    aside_toc = fields.Text(
        string='Table of Contents',
        compute='_compute_aside_toc',
        inverse='_inverse_aside_toc',
        store=False
    )
    
    aside_list = fields.Selection(
        string='List Type',
        selection=[
            ('alike', 'Alike'),
            ('product', 'Product'),
            ('events', 'Events'),
            ('posts', 'Posts'),
            ('partners', 'Partners'),
            ('companies', 'Companies'),
            ('media', 'Media')
        ],
        compute='_compute_aside_list',
        inverse='_inverse_aside_list',
        store=False
    )
    
    aside_context = fields.Text(
        string='Context',
        compute='_compute_aside_context',
        inverse='_inverse_aside_context',
        store=False
    )
    
    aside_options_text = fields.Text(
        string='Options (Aside)',
        compute='_compute_aside_options_text',
        inverse='_inverse_aside_options_text',
        store=False
    )

    # HEADER OPTIONS
    header_alert = fields.Text(
        string='Alert',
        compute='_compute_header_alert',
        inverse='_inverse_header_alert',
        store=False
    )
    
    header_postit = fields.Text(
        string='Post-it (Header)',
        compute='_compute_header_postit',
        inverse='_inverse_header_postit',
        store=False
    )
    
    header_options_text = fields.Text(
        string='Options (Header)',
        compute='_compute_header_options_text',
        inverse='_inverse_header_options_text',
        store=False
    )

    # FOOTER OPTIONS
    footer_gallery = fields.Selection(
        string='Gallery Type',
        selection=[
            ('alike', 'Alike'),
            ('product', 'Product'),
            ('events', 'Events'),
            ('posts', 'Posts'),
            ('partners', 'Partners'),
            ('companies', 'Companies'),
            ('media', 'Media')
        ],
        compute='_compute_footer_gallery',
        inverse='_inverse_footer_gallery',
        store=False
    )
    
    footer_postit = fields.Text(
        string='Post-it (Footer)',
        compute='_compute_footer_postit',
        inverse='_inverse_footer_postit',
        store=False
    )
    
    footer_slider = fields.Selection(
        string='Slider Type',
        selection=[
            ('alike', 'Alike'),
            ('product', 'Product'),
            ('events', 'Events'),
            ('posts', 'Posts'),
            ('partners', 'Partners'),
            ('companies', 'Companies'),
            ('media', 'Media')
        ],
        compute='_compute_footer_slider',
        inverse='_inverse_footer_slider',
        store=False
    )
    
    footer_repeat = fields.Text(
        string='Repeat',
        compute='_compute_footer_repeat',
        inverse='_inverse_footer_repeat',
        store=False
    )
    
    footer_sitemap = fields.Selection(
        string='Sitemap',
        selection=[
            ('none', 'None'),
            ('small', 'Small'),
            ('medium', 'Medium'),
            ('large', 'Large')
        ],
        compute='_compute_footer_sitemap',
        inverse='_inverse_footer_sitemap',
        store=False
    )
    
    footer_options_text = fields.Text(
        string='Options (Footer)',
        compute='_compute_footer_options_text',
        inverse='_inverse_footer_options_text',
        store=False
    )

    # ==================== HAS CONTENT COMPUTE METHODS ====================

    @api.depends('page_options')
    def _compute_page_has_content(self):
        for record in self:
            record.page_has_content = bool(record.page_options and isinstance(record.page_options, dict) and record.page_options)

    @api.depends('aside_options')
    def _compute_aside_has_content(self):
        for record in self:
            record.aside_has_content = bool(record.aside_options and isinstance(record.aside_options, dict) and record.aside_options)

    @api.depends('header_options')
    def _compute_header_has_content(self):
        for record in self:
            record.header_has_content = bool(record.header_options and isinstance(record.header_options, dict) and record.header_options)

    @api.depends('footer_options')
    def _compute_footer_has_content(self):
        for record in self:
            record.footer_has_content = bool(record.footer_options and isinstance(record.footer_options, dict) and record.footer_options)

    # ==================== CHANGE DETECTION COMPUTE METHODS ====================

    @api.depends('page_options')
    def _compute_page_has_changes(self):
        for record in self:
            if not record.id:
                record.page_has_changes = False
                continue
            # Compare current with database value
            db_record = record.browse(record.id)
            old_value = db_record.page_options or {}
            new_value = record.page_options or {}
            record.page_has_changes = old_value != new_value

    @api.depends('aside_options')
    def _compute_aside_has_changes(self):
        for record in self:
            if not record.id:
                record.aside_has_changes = False
                continue
            db_record = record.browse(record.id)
            old_value = db_record.aside_options or {}
            new_value = record.aside_options or {}
            record.aside_has_changes = old_value != new_value

    @api.depends('header_options')
    def _compute_header_has_changes(self):
        for record in self:
            if not record.id:
                record.header_has_changes = False
                continue
            db_record = record.browse(record.id)
            old_value = db_record.header_options or {}
            new_value = record.header_options or {}
            record.header_has_changes = old_value != new_value

    @api.depends('footer_options')
    def _compute_footer_has_changes(self):
        for record in self:
            if not record.id:
                record.footer_has_changes = False
                continue
            db_record = record.browse(record.id)
            old_value = db_record.footer_options or {}
            new_value = record.footer_options or {}
            record.footer_has_changes = old_value != new_value

    # ==================== PAGE FIELD COMPUTE/INVERSE ====================

    @api.depends('page_options')
    def _compute_page_background(self):
        for record in self:
            record.page_background = record.get_option('page', 'background', False)

    def _inverse_page_background(self):
        for record in self:
            if record.page_background:
                record.set_option('page', 'background', record.page_background)
            else:
                record.remove_option('page', 'background')

    @api.depends('page_options')
    def _compute_page_cssvars(self):
        for record in self:
            record.page_cssvars = record.get_option('page', 'cssvars', '')

    def _inverse_page_cssvars(self):
        for record in self:
            if record.page_cssvars:
                record.set_option('page', 'cssvars', record.page_cssvars)
            else:
                record.remove_option('page', 'cssvars')

    @api.depends('page_options')
    def _compute_page_navigation(self):
        for record in self:
            record.page_navigation = record.get_option('page', 'navigation', '')

    def _inverse_page_navigation(self):
        for record in self:
            if record.page_navigation:
                record.set_option('page', 'navigation', record.page_navigation)
            else:
                record.remove_option('page', 'navigation')

    @api.depends('page_options')
    def _compute_page_options_text(self):
        for record in self:
            record.page_options_text = record.get_option('page', 'options', '')

    def _inverse_page_options_text(self):
        for record in self:
            if record.page_options_text:
                record.set_option('page', 'options', record.page_options_text)
            else:
                record.remove_option('page', 'options')

    # ==================== ASIDE FIELD COMPUTE/INVERSE ====================

    @api.depends('aside_options')
    def _compute_aside_postit(self):
        for record in self:
            record.aside_postit = record.get_option('aside', 'postit', '')

    def _inverse_aside_postit(self):
        for record in self:
            if record.aside_postit:
                record.set_option('aside', 'postit', record.aside_postit)
            else:
                record.remove_option('aside', 'postit')

    @api.depends('aside_options')
    def _compute_aside_toc(self):
        for record in self:
            record.aside_toc = record.get_option('aside', 'toc', '')

    def _inverse_aside_toc(self):
        for record in self:
            if record.aside_toc:
                record.set_option('aside', 'toc', record.aside_toc)
            else:
                record.remove_option('aside', 'toc')

    @api.depends('aside_options')
    def _compute_aside_list(self):
        for record in self:
            record.aside_list = record.get_option('aside', 'list', False)

    def _inverse_aside_list(self):
        for record in self:
            if record.aside_list:
                record.set_option('aside', 'list', record.aside_list)
            else:
                record.remove_option('aside', 'list')

    @api.depends('aside_options')
    def _compute_aside_context(self):
        for record in self:
            record.aside_context = record.get_option('aside', 'context', '')

    def _inverse_aside_context(self):
        for record in self:
            if record.aside_context:
                record.set_option('aside', 'context', record.aside_context)
            else:
                record.remove_option('aside', 'context')

    @api.depends('aside_options')
    def _compute_aside_options_text(self):
        for record in self:
            record.aside_options_text = record.get_option('aside', 'options', '')

    def _inverse_aside_options_text(self):
        for record in self:
            if record.aside_options_text:
                record.set_option('aside', 'options', record.aside_options_text)
            else:
                record.remove_option('aside', 'options')

    # ==================== HEADER FIELD COMPUTE/INVERSE ====================

    @api.depends('header_options')
    def _compute_header_alert(self):
        for record in self:
            record.header_alert = record.get_option('header', 'alert', '')

    def _inverse_header_alert(self):
        for record in self:
            if record.header_alert:
                record.set_option('header', 'alert', record.header_alert)
            else:
                record.remove_option('header', 'alert')

    @api.depends('header_options')
    def _compute_header_postit(self):
        for record in self:
            record.header_postit = record.get_option('header', 'postit', '')

    def _inverse_header_postit(self):
        for record in self:
            if record.header_postit:
                record.set_option('header', 'postit', record.header_postit)
            else:
                record.remove_option('header', 'postit')

    @api.depends('header_options')
    def _compute_header_options_text(self):
        for record in self:
            record.header_options_text = record.get_option('header', 'options', '')

    def _inverse_header_options_text(self):
        for record in self:
            if record.header_options_text:
                record.set_option('header', 'options', record.header_options_text)
            else:
                record.remove_option('header', 'options')

    # ==================== FOOTER FIELD COMPUTE/INVERSE ====================

    @api.depends('footer_options')
    def _compute_footer_gallery(self):
        for record in self:
            record.footer_gallery = record.get_option('footer', 'gallery', False)

    def _inverse_footer_gallery(self):
        for record in self:
            if record.footer_gallery:
                record.set_option('footer', 'gallery', record.footer_gallery)
            else:
                record.remove_option('footer', 'gallery')

    @api.depends('footer_options')
    def _compute_footer_postit(self):
        for record in self:
            record.footer_postit = record.get_option('footer', 'postit', '')

    def _inverse_footer_postit(self):
        for record in self:
            if record.footer_postit:
                record.set_option('footer', 'postit', record.footer_postit)
            else:
                record.remove_option('footer', 'postit')

    @api.depends('footer_options')
    def _compute_footer_slider(self):
        for record in self:
            record.footer_slider = record.get_option('footer', 'slider', False)

    def _inverse_footer_slider(self):
        for record in self:
            if record.footer_slider:
                record.set_option('footer', 'slider', record.footer_slider)
            else:
                record.remove_option('footer', 'slider')

    @api.depends('footer_options')
    def _compute_footer_repeat(self):
        for record in self:
            record.footer_repeat = record.get_option('footer', 'repeat', '')

    def _inverse_footer_repeat(self):
        for record in self:
            if record.footer_repeat:
                record.set_option('footer', 'repeat', record.footer_repeat)
            else:
                record.remove_option('footer', 'repeat')

    @api.depends('footer_options')
    def _compute_footer_sitemap(self):
        for record in self:
            record.footer_sitemap = record.get_option('footer', 'sitemap', False)

    def _inverse_footer_sitemap(self):
        for record in self:
            if record.footer_sitemap:
                record.set_option('footer', 'sitemap', record.footer_sitemap)
            else:
                record.remove_option('footer', 'sitemap')

    @api.depends('footer_options')
    def _compute_footer_options_text(self):
        for record in self:
            record.footer_options_text = record.get_option('footer', 'options', '')

    def _inverse_footer_options_text(self):
        for record in self:
            if record.footer_options_text:
                record.set_option('footer', 'options', record.footer_options_text)
            else:
                record.remove_option('footer', 'options')

    # ==================== HELPER METHODS ====================

    def get_option(self, section, option_name, default=None):
        """Get a specific option value from a section."""
        self.ensure_one()
        section_field = f'{section}_options'
        options = getattr(self, section_field, None)
        if not options or not isinstance(options, dict):
            return default
        return options.get(option_name, default)

    def set_option(self, section, option_name, value):
        """Set a specific option value in a section."""
        self.ensure_one()
        if not value:
            return
            
        section_field = f'{section}_options'
        current_options = getattr(self, section_field, None) or {}
        current_options[option_name] = value
        setattr(self, section_field, current_options)

    def remove_option(self, section, option_name):
        """Remove a specific option from a section."""
        self.ensure_one()
        section_field = f'{section}_options'
        current_options = getattr(self, section_field, None)
        if not current_options or not isinstance(current_options, dict):
            return
            
        if option_name in current_options:
            del current_options[option_name]
            # If section is now empty, set to False instead of empty dict
            setattr(self, section_field, current_options if current_options else False)

    # ==================== BUTTON ACTION METHODS ====================

    def action_create_page_options(self):
        """Create page_options with default values."""
        self.ensure_one()
        self.page_options = {
            'background': 'primary',
            'cssvars': '',
            'navigation': '',
            'options': ''
        }
        return {'type': 'ir.actions.act_window_close'}

    def action_delete_page_options(self):
        """Delete all page_options content."""
        self.ensure_one()
        self.page_options = False
        return {'type': 'ir.actions.act_window_close'}

    def action_create_aside_options(self):
        """Create aside_options with default values."""
        self.ensure_one()
        self.aside_options = {
            'postit': '',
            'toc': '',
            'list': False,
            'context': '',
            'options': ''
        }
        return {'type': 'ir.actions.act_window_close'}

    def action_delete_aside_options(self):
        """Delete all aside_options content."""
        self.ensure_one()
        self.aside_options = False
        return {'type': 'ir.actions.act_window_close'}

    def action_create_header_options(self):
        """Create header_options with default values."""
        self.ensure_one()
        self.header_options = {
            'alert': '',
            'postit': '',
            'options': ''
        }
        return {'type': 'ir.actions.act_window_close'}

    def action_delete_header_options(self):
        """Delete all header_options content."""
        self.ensure_one()
        self.header_options = False
        return {'type': 'ir.actions.act_window_close'}

    def action_create_footer_options(self):
        """Create footer_options with default values."""
        self.ensure_one()
        self.footer_options = {
            'gallery': False,
            'postit': '',
            'slider': False,
            'repeat': '',
            'sitemap': 'medium',
            'options': ''
        }
        return {'type': 'ir.actions.act_window_close'}

    def action_delete_footer_options(self):
        """Delete all footer_options content."""
        self.ensure_one()
        self.footer_options = False
        return {'type': 'ir.actions.act_window_close'}