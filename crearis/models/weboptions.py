# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api


class WebOptionsAbstract(models.AbstractModel):
    """
    Abstract model for managing format_options with page, aside, header, and footer options.
    Can be inherited by any model that needs these capabilities.
    
    Structure:
    {
        "page": {"background": "primary", "cssvars": "...", "navigation": "...", "options": "...", "prop2": ["val1", "val2"], "prop3": true},
        "aside": {"postit": "...", "toc": "...", "list": "alike", "context": "...", "options": "..."},
        "header": {"alert": "...", "postit": "...", "options": "..."},
        "footer": {"gallery": "alike", "postit": "...", "slider": "events", "repeat": "...", "sitemap": "medium", "options": "..."}
    }
    """
    _name = 'web.options.abstract'
    _description = 'Web Options Abstract Model'

    format_options = fields.Json(
        string='Format Options',
        help='JSON structure containing page, aside, header, and footer options'
    )

    # Computed properties for each section (Json fields for accessing entire sections)
    page_options_json = fields.Json(
        compute='_compute_page_options_json',
        store=False,
        string='Page Options (JSON)'
    )
    
    aside_options_json = fields.Json(
        compute='_compute_aside_options_json',
        store=False,
        string='Aside Options (JSON)'
    )
    
    header_options_json = fields.Json(
        compute='_compute_header_options_json',
        store=False,
        string='Header Options (JSON)'
    )
    
    footer_options_json = fields.Json(
        compute='_compute_footer_options_json',
        store=False,
        string='Footer Options (JSON)'
    )

    # ==================== PAGE OPTIONS ====================
    
    page_background = fields.Selection(
        string='Background',
        selection=[
            ('primary', 'Primary'),
            ('secondary', 'Secondary'),
            ('accent', 'Accent'),
            ('neutral', 'Neutral'),
            ('positive', 'Positive'),
            ('negative', 'Negative'),
            ('warning', 'Warning')
        ],
        compute='_compute_page_background',
        inverse='_inverse_page_background',
        store=False,
        help='Background color scheme | Sets the primary background color theme for the entire page, affecting overall visual hierarchy and mood'
    )
    
    page_cssvars = fields.Text(
        string='CSS Variables',
        compute='_compute_page_cssvars',
        inverse='_inverse_page_cssvars',
        store=False,
        translate=False,
        help='Custom CSS variables | Define custom CSS variables for page-level styling. Format: --variable-name: value; (one per line)'
    )
    
    page_navigation = fields.Text(
        string='Navigation',
        compute='_compute_page_navigation',
        inverse='_inverse_page_navigation',
        store=False,
        translate=False,
        help='Navigation configuration | JSON or text configuration for page navigation behavior, including menu items, breadcrumbs, and navigation style'
    )
    
    page_options_text = fields.Text(
        string='Options (Page)',
        compute='_compute_page_options_text',
        inverse='_inverse_page_options_text',
        store=False,
        translate=False,
        help='Additional page options | Miscellaneous page-level options as key-value pairs or JSON for controlling layout, spacing, and other page behaviors'
    )

    # Example properties (demonstrating array and boolean types)
    page_prop2 = fields.Char(
        string='Example Property 2 (Array)',
        compute='_compute_page_prop2',
        inverse='_inverse_page_prop2',
        store=False,
        help='Example array property | Demonstrates how to store array values as comma-separated strings'
    )
    
    page_prop3 = fields.Boolean(
        string='Example Property 3 (Boolean)',
        compute='_compute_page_prop3',
        inverse='_inverse_page_prop3',
        store=False,
        help='Example boolean property | Demonstrates how to store boolean values'
    )

    # ==================== ASIDE OPTIONS ====================
    
    aside_postit = fields.Text(
        string='Post-it (Aside)',
        compute='_compute_aside_postit',
        inverse='_inverse_aside_postit',
        store=False,
        translate=False,
        help='Sticky note content | Content for a sticky note or callout box in the sidebar, useful for highlighting important information'
    )
    
    aside_toc = fields.Text(
        string='Table of Contents',
        compute='_compute_aside_toc',
        inverse='_inverse_aside_toc',
        store=False,
        translate=False,
        help='TOC configuration | Configuration for automatic table of contents generation in the sidebar, including heading levels and styling'
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
        store=False,
        help='Sidebar list type | Type of content list to display in the sidebar (e.g., related posts, upcoming events, featured products)'
    )
    
    aside_context = fields.Text(
        string='Context',
        compute='_compute_aside_context',
        inverse='_inverse_aside_context',
        store=False,
        translate=False,
        help='Contextual information | Additional context or metadata to display in the sidebar, such as author info, tags, or related categories'
    )
    
    aside_options_text = fields.Text(
        string='Options (Aside)',
        compute='_compute_aside_options_text',
        inverse='_inverse_aside_options_text',
        store=False,
        translate=False,
        help='Additional aside options | Miscellaneous sidebar options as key-value pairs or JSON for controlling sidebar behavior and appearance'
    )

    # ==================== HEADER OPTIONS ====================
    
    header_alert = fields.Text(
        string='Alert',
        compute='_compute_header_alert',
        inverse='_inverse_header_alert',
        store=False,
        translate=False,
        help='Header alert message | Display an alert or notification banner at the top of the page, useful for announcements or warnings'
    )
    
    header_postit = fields.Text(
        string='Post-it (Header)',
        compute='_compute_header_postit',
        inverse='_inverse_header_postit',
        store=False,
        translate=False,
        help='Header note content | Sticky note or callout content within the header area, for highlighting key messages or CTAs'
    )
    
    header_options_text = fields.Text(
        string='Options (Header)',
        compute='_compute_header_options_text',
        inverse='_inverse_header_options_text',
        store=False,
        translate=False,
        help='Additional header options | Miscellaneous header options as key-value pairs or JSON for controlling header layout, sticky behavior, and styling'
    )

    # ==================== FOOTER OPTIONS ====================
    
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
        store=False,
        help='Footer gallery type | Type of content gallery to display in the footer area (e.g., partner logos, recent posts, media gallery)'
    )
    
    footer_postit = fields.Text(
        string='Post-it (Footer)',
        compute='_compute_footer_postit',
        inverse='_inverse_footer_postit',
        store=False,
        translate=False,
        help='Footer note content | Sticky note or callout content within the footer area, useful for disclaimers or calls-to-action'
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
        store=False,
        help='Footer slider type | Type of content slider/carousel to display in the footer (e.g., testimonials, featured content, sponsors)'
    )
    
    footer_repeat = fields.Text(
        string='Repeat',
        compute='_compute_footer_repeat',
        inverse='_inverse_footer_repeat',
        store=False,
        translate=False,
        help='Repeating content | Configuration for repeating content or patterns in the footer, such as newsletter signup or social links'
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
        store=False,
        help='Sitemap size | Size and detail level of the footer sitemap/navigation menu (none, small, medium, or large)'
    )
    
    footer_options_text = fields.Text(
        string='Options (Footer)',
        compute='_compute_footer_options_text',
        inverse='_inverse_footer_options_text',
        store=False,
        translate=False,
        help='Additional footer options | Miscellaneous footer options as key-value pairs or JSON for controlling footer layout, columns, and styling'
    )

    # ==================== COMPUTE METHODS FOR JSON SECTIONS ====================

    @api.depends('format_options')
    def _compute_page_options_json(self):
        """Extract page options from format_options JSON."""
        for record in self:
            if record.format_options and isinstance(record.format_options, dict):
                record.page_options_json = record.format_options.get('page', {})
            else:
                record.page_options_json = {}

    @api.depends('format_options')
    def _compute_aside_options_json(self):
        """Extract aside options from format_options JSON."""
        for record in self:
            if record.format_options and isinstance(record.format_options, dict):
                record.aside_options_json = record.format_options.get('aside', {})
            else:
                record.aside_options_json = {}

    @api.depends('format_options')
    def _compute_header_options_json(self):
        """Extract header options from format_options JSON."""
        for record in self:
            if record.format_options and isinstance(record.format_options, dict):
                record.header_options_json = record.format_options.get('header', {})
            else:
                record.header_options_json = {}

    @api.depends('format_options')
    def _compute_footer_options_json(self):
        """Extract footer options from format_options JSON."""
        for record in self:
            if record.format_options and isinstance(record.format_options, dict):
                record.footer_options_json = record.format_options.get('footer', {})
            else:
                record.footer_options_json = {}

    # ==================== PAGE COMPUTE/INVERSE ====================

    @api.depends('format_options')
    def _compute_page_background(self):
        for record in self:
            record.page_background = record.get_option('page', 'background', False)

    def _inverse_page_background(self):
        for record in self:
            if record.page_background:
                record.set_option('page', 'background', record.page_background)
            else:
                record.remove_option('page', 'background')

    @api.depends('format_options')
    def _compute_page_cssvars(self):
        for record in self:
            record.page_cssvars = record.get_option('page', 'cssvars', '')

    def _inverse_page_cssvars(self):
        for record in self:
            if record.page_cssvars:
                record.set_option('page', 'cssvars', record.page_cssvars)
            else:
                record.remove_option('page', 'cssvars')

    @api.depends('format_options')
    def _compute_page_navigation(self):
        for record in self:
            record.page_navigation = record.get_option('page', 'navigation', '')

    def _inverse_page_navigation(self):
        for record in self:
            if record.page_navigation:
                record.set_option('page', 'navigation', record.page_navigation)
            else:
                record.remove_option('page', 'navigation')

    @api.depends('format_options')
    def _compute_page_options_text(self):
        for record in self:
            record.page_options_text = record.get_option('page', 'options', '')

    def _inverse_page_options_text(self):
        for record in self:
            if record.page_options_text:
                record.set_option('page', 'options', record.page_options_text)
            else:
                record.remove_option('page', 'options')

    @api.depends('format_options')
    def _compute_page_prop2(self):
        """Compute page_prop2 from format_options (array as comma-separated string)."""
        for record in self:
            prop2_value = record.get_option('page', 'prop2', [])
            if isinstance(prop2_value, list):
                record.page_prop2 = ', '.join(str(v) for v in prop2_value)
            else:
                record.page_prop2 = str(prop2_value) if prop2_value else ''

    def _inverse_page_prop2(self):
        """Store page_prop2 back to format_options (parse comma-separated to array)."""
        for record in self:
            if record.page_prop2:
                # Split by comma and clean whitespace
                value_list = [v.strip() for v in record.page_prop2.split(',') if v.strip()]
                record.set_option('page', 'prop2', value_list)
            else:
                record.remove_option('page', 'prop2')

    @api.depends('format_options')
    def _compute_page_prop3(self):
        """Compute page_prop3 from format_options."""
        for record in self:
            record.page_prop3 = record.get_option('page', 'prop3', False)

    def _inverse_page_prop3(self):
        """Store page_prop3 back to format_options."""
        for record in self:
            if record.page_prop3:
                record.set_option('page', 'prop3', record.page_prop3)
            else:
                record.remove_option('page', 'prop3')

    # ==================== ASIDE COMPUTE/INVERSE ====================

    @api.depends('format_options')
    def _compute_aside_postit(self):
        for record in self:
            record.aside_postit = record.get_option('aside', 'postit', '')

    def _inverse_aside_postit(self):
        for record in self:
            if record.aside_postit:
                record.set_option('aside', 'postit', record.aside_postit)
            else:
                record.remove_option('aside', 'postit')

    @api.depends('format_options')
    def _compute_aside_toc(self):
        for record in self:
            record.aside_toc = record.get_option('aside', 'toc', '')

    def _inverse_aside_toc(self):
        for record in self:
            if record.aside_toc:
                record.set_option('aside', 'toc', record.aside_toc)
            else:
                record.remove_option('aside', 'toc')

    @api.depends('format_options')
    def _compute_aside_list(self):
        for record in self:
            record.aside_list = record.get_option('aside', 'list', False)

    def _inverse_aside_list(self):
        for record in self:
            if record.aside_list:
                record.set_option('aside', 'list', record.aside_list)
            else:
                record.remove_option('aside', 'list')

    @api.depends('format_options')
    def _compute_aside_context(self):
        for record in self:
            record.aside_context = record.get_option('aside', 'context', '')

    def _inverse_aside_context(self):
        for record in self:
            if record.aside_context:
                record.set_option('aside', 'context', record.aside_context)
            else:
                record.remove_option('aside', 'context')

    @api.depends('format_options')
    def _compute_aside_options_text(self):
        for record in self:
            record.aside_options_text = record.get_option('aside', 'options', '')

    def _inverse_aside_options_text(self):
        for record in self:
            if record.aside_options_text:
                record.set_option('aside', 'options', record.aside_options_text)
            else:
                record.remove_option('aside', 'options')

    # ==================== HEADER COMPUTE/INVERSE ====================

    @api.depends('format_options')
    def _compute_header_alert(self):
        for record in self:
            record.header_alert = record.get_option('header', 'alert', '')

    def _inverse_header_alert(self):
        for record in self:
            if record.header_alert:
                record.set_option('header', 'alert', record.header_alert)
            else:
                record.remove_option('header', 'alert')

    @api.depends('format_options')
    def _compute_header_postit(self):
        for record in self:
            record.header_postit = record.get_option('header', 'postit', '')

    def _inverse_header_postit(self):
        for record in self:
            if record.header_postit:
                record.set_option('header', 'postit', record.header_postit)
            else:
                record.remove_option('header', 'postit')

    @api.depends('format_options')
    def _compute_header_options_text(self):
        for record in self:
            record.header_options_text = record.get_option('header', 'options', '')

    def _inverse_header_options_text(self):
        for record in self:
            if record.header_options_text:
                record.set_option('header', 'options', record.header_options_text)
            else:
                record.remove_option('header', 'options')

    # ==================== FOOTER COMPUTE/INVERSE ====================

    @api.depends('format_options')
    def _compute_footer_gallery(self):
        for record in self:
            record.footer_gallery = record.get_option('footer', 'gallery', False)

    def _inverse_footer_gallery(self):
        for record in self:
            if record.footer_gallery:
                record.set_option('footer', 'gallery', record.footer_gallery)
            else:
                record.remove_option('footer', 'gallery')

    @api.depends('format_options')
    def _compute_footer_postit(self):
        for record in self:
            record.footer_postit = record.get_option('footer', 'postit', '')

    def _inverse_footer_postit(self):
        for record in self:
            if record.footer_postit:
                record.set_option('footer', 'postit', record.footer_postit)
            else:
                record.remove_option('footer', 'postit')

    @api.depends('format_options')
    def _compute_footer_slider(self):
        for record in self:
            record.footer_slider = record.get_option('footer', 'slider', False)

    def _inverse_footer_slider(self):
        for record in self:
            if record.footer_slider:
                record.set_option('footer', 'slider', record.footer_slider)
            else:
                record.remove_option('footer', 'slider')

    @api.depends('format_options')
    def _compute_footer_repeat(self):
        for record in self:
            record.footer_repeat = record.get_option('footer', 'repeat', '')

    def _inverse_footer_repeat(self):
        for record in self:
            if record.footer_repeat:
                record.set_option('footer', 'repeat', record.footer_repeat)
            else:
                record.remove_option('footer', 'repeat')

    @api.depends('format_options')
    def _compute_footer_sitemap(self):
        for record in self:
            record.footer_sitemap = record.get_option('footer', 'sitemap', False)

    def _inverse_footer_sitemap(self):
        for record in self:
            if record.footer_sitemap:
                record.set_option('footer', 'sitemap', record.footer_sitemap)
            else:
                record.remove_option('footer', 'sitemap')

    @api.depends('format_options')
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
        """
        Helper method to get a specific option value from any section.
        
        Args:
            section (str): Section name ('page', 'aside', 'header', 'footer')
            option_name (str): Name of the option
            default: Default value if option doesn't exist
            
        Returns:
            The option value or default
            
        Usage:
            record.get_option('page', 'background', False)
            record.get_option('footer', 'sitemap', False)
        """
        self.ensure_one()
        if not self.format_options or not isinstance(self.format_options, dict):
            return default
        section_options = self.format_options.get(section, {})
        return section_options.get(option_name, default)

    def set_option(self, section, option_name, value):
        """
        Helper method to set a specific option value in any section.
        Only sets the value if it's not empty/False.
        
        Args:
            section (str): Section name ('page', 'aside', 'header', 'footer')
            option_name (str): Name of the option
            value: Value to set
            
        Usage:
            record.set_option('page', 'background', 'primary')
            record.set_option('footer', 'sitemap', 'medium')
        """
        self.ensure_one()
        if not value:  # Don't set empty values
            return
            
        current_options = self.format_options or {}
        if section not in current_options:
            current_options[section] = {}
        current_options[section][option_name] = value
        self.format_options = current_options

    def remove_option(self, section, option_name):
        """
        Helper method to remove a specific option from a section.
        Also removes empty sections to keep format_options clean.
        
        Args:
            section (str): Section name ('page', 'aside', 'header', 'footer')
            option_name (str): Name of the option to remove
            
        Usage:
            record.remove_option('page', 'background')
            record.remove_option('footer', 'sitemap')
        """
        self.ensure_one()
        if not self.format_options or not isinstance(self.format_options, dict):
            return
            
        current_options = self.format_options.copy()
        if section in current_options and option_name in current_options[section]:
            del current_options[section][option_name]
            
            # Remove empty section
            if not current_options[section]:
                del current_options[section]
                
            self.format_options = current_options

    def action_save_format_options(self):
        """
        Save the current format_options to the database.
        The inverse functions already update format_options, 
        but this method provides explicit feedback.
        
        Returns:
            dict: Action to display success notification
        """
        self.ensure_one()
        
        # The inverse functions have already updated format_options
        # We just need to trigger a write to save it
        self.write({'format_options': self.format_options})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Format options saved successfully.',
                'type': 'success',
                'sticky': False,
            }
        }