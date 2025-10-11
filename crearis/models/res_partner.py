# Copyright 2025 Hans Dönitz - Theaterpedia.org
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
import json

class ResPartner(models.Model):
    """Adds Markdown-Field to partner"""

    _inherit = "res.partner"

    # HERO-TYPE, FORMAT, CIMG > are developed and tested in model event
    header_type = fields.Selection(
        string='Header',
        selection=[("simple", "simple"), ("columns", 'Text-Bild (2 Spalten)'), ("banner", "Banner medium"), ("cover", "Cover Fullsize"), ("bauchbinde", "Bauchbinde")],
        help="What header-type introduces the Partner?",
        default="simple")

    header_size = fields.Selection(
        string='Header-Size',
        selection=[("mini", "minimal"), ("medium", 'Medium'), ("prominent", "prominent"), ("full", "full")],
        help="How big is the header?",
        default="mini")

    cimg = fields.Text('Hero-Image-Link', translate=False, default='', help="public url for the hero-image")

    md = fields.Text('Markdown Content', translate=True, help="Markdown content for partner profile.", default='')

    # Format options sections (JSON fields)
    page_options = fields.Json(
        string='Page Options',
        help='JSON object containing page-level formatting options'
    )
    
    aside_options = fields.Json(
        string='Aside Options',
        help='JSON object containing aside/sidebar formatting options'
    )
    
    header_options = fields.Json(
        string='Header Options',
        help='JSON object containing header formatting options'
    )
    
    footer_options = fields.Json(
        string='Footer Options',
        help='JSON object containing footer formatting options'
    )

    # Computed boolean fields for content existence
    page_has_content = fields.Boolean(
        string='Page Has Content',
        compute='_compute_options_content',
        store=False,
        help='True if page_options contains data'
    )
    
    aside_has_content = fields.Boolean(
        string='Aside Has Content',
        compute='_compute_options_content',
        store=False,
        help='True if aside_options contains data'
    )
    
    header_has_content = fields.Boolean(
        string='Header Has Content',
        compute='_compute_options_content',
        store=False,
        help='True if header_options contains data'
    )
    
    footer_has_content = fields.Boolean(
        string='Footer Has Content',
        compute='_compute_options_content',
        store=False,
        help='True if footer_options contains data'
    )

    # Computed boolean fields for unsaved changes (not stored, for UI state)
    page_has_changes = fields.Boolean(
        string='Page Has Changes',
        compute='_compute_options_changes',
        store=False
    )
    
    aside_has_changes = fields.Boolean(
        string='Aside Has Changes',
        compute='_compute_options_changes',
        store=False
    )
    
    header_has_changes = fields.Boolean(
        string='Header Has Changes',
        compute='_compute_options_changes',
        store=False
    )
    
    footer_has_changes = fields.Boolean(
        string='Footer Has Changes',
        compute='_compute_options_changes',
        store=False
    )

    @api.depends('page_options', 'aside_options', 'header_options', 'footer_options')
    def _compute_options_content(self):
        """Compute whether each options section has content"""
        for record in self:
            record.page_has_content = bool(record.page_options and isinstance(record.page_options, dict) and record.page_options)
            record.aside_has_content = bool(record.aside_options and isinstance(record.aside_options, dict) and record.aside_options)
            record.header_has_content = bool(record.header_options and isinstance(record.header_options, dict) and record.header_options)
            record.footer_has_content = bool(record.footer_options and isinstance(record.footer_options, dict) and record.footer_options)

    @api.depends('page_options', 'aside_options', 'header_options', 'footer_options')
    def _compute_options_changes(self):
        """Compute whether each options section has unsaved changes"""
        for record in self:
            # This is primarily for UI state management
            # In a real implementation, you'd compare with stored values
            record.page_has_changes = False
            record.aside_has_changes = False
            record.header_has_changes = False
            record.footer_has_changes = False

    # Action methods for creating/deleting options sections
    def action_create_page_options(self):
        """Create empty page options structure"""
        for record in self:
            if not record.page_options:
                record.page_options = {
                    'background': '',
                    'cssvars': '',
                    'navigation': '',
                    'options_text': ''
                }

    def action_delete_page_options(self):
        """Delete page options"""
        for record in self:
            record.page_options = False

    def action_create_aside_options(self):
        """Create empty aside options structure"""
        for record in self:
            if not record.aside_options:
                record.aside_options = {
                    'postit': '',
                    'toc': '',
                    'list': '',
                    'context': '',
                    'options_text': ''
                }

    def action_delete_aside_options(self):
        """Delete aside options"""
        for record in self:
            record.aside_options = False

    def action_create_header_options(self):
        """Create empty header options structure"""
        for record in self:
            if not record.header_options:
                record.header_options = {
                    'alert': '',
                    'postit': '',
                    'options_text': ''
                }

    def action_delete_header_options(self):
        """Delete header options"""
        for record in self:
            record.header_options = False

    def action_create_footer_options(self):
        """Create empty footer options structure"""
        for record in self:
            if not record.footer_options:
                record.footer_options = {
                    'gallery': '',
                    'postit': '',
                    'slider': '',
                    'repeat': '',
                    'sitemap': '',
                    'options_text': ''
                }

    def action_delete_footer_options(self):
        """Delete footer options"""
        for record in self:
            record.footer_options = False