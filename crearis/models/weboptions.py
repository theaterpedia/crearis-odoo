# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api


class WebOptionsAbstract(models.AbstractModel):
    """
    Abstract model for managing format_options with page and hero options.
    Can be inherited by any model that needs these capabilities.
    """
    _name = 'web.options.abstract'
    _description = 'Web Options Abstract Model'

    format_options = fields.Json(
        string='Format Options',
        help='JSON structure containing page and hero options: {"page": {...}, "hero": {...}}'
    )

    # Computed properties for hero options
    hero_options = fields.Json(
        compute='_compute_hero_options',
        store=False,
        string='Hero Options'
    )
    
    # Computed properties for page options
    page_options = fields.Json(
        compute='_compute_page_options',
        store=False,
        string='Page Options'
    )

    # Editable proxy fields for page options
    page_prop1 = fields.Char(
        string='Page Property 1',
        compute='_compute_page_prop1',
        inverse='_inverse_page_prop1',
        store=False,
        help='First page property'
    )
    
    page_prop2 = fields.Char(
        string='Page Property 2',
        compute='_compute_page_prop2',
        inverse='_inverse_page_prop2',
        store=False,
        help='Second page property (comma-separated values)'
    )

    # Editable proxy field for hero option
    hero_prop3 = fields.Boolean(
        string='Hero Property 3',
        compute='_compute_hero_prop3',
        inverse='_inverse_hero_prop3',
        store=False,
        help='Boolean hero property'
    )

    @api.depends('format_options')
    def _compute_hero_options(self):
        """Extract hero options from format_options JSON."""
        for record in self:
            if record.format_options and isinstance(record.format_options, dict):
                record.hero_options = record.format_options.get('hero', {})
            else:
                record.hero_options = {}

    @api.depends('format_options')
    def _compute_page_options(self):
        """Extract page options from format_options JSON."""
        for record in self:
            if record.format_options and isinstance(record.format_options, dict):
                record.page_options = record.format_options.get('page', {})
            else:
                record.page_options = {}

    @api.depends('format_options')
    def _compute_page_prop1(self):
        """Compute page_prop1 from format_options."""
        for record in self:
            record.page_prop1 = record.get_page_option('prop1', '')

    def _inverse_page_prop1(self):
        """Store page_prop1 back to format_options."""
        for record in self:
            record.set_page_option('prop1', record.page_prop1 or '')

    @api.depends('format_options')
    def _compute_page_prop2(self):
        """Compute page_prop2 from format_options (array as comma-separated string)."""
        for record in self:
            prop2_value = record.get_page_option('prop2', [])
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
                record.set_page_option('prop2', value_list)
            else:
                record.set_page_option('prop2', [])

    @api.depends('format_options')
    def _compute_hero_prop3(self):
        """Compute hero_prop3 from format_options."""
        for record in self:
            record.hero_prop3 = record.get_hero_option('prop3', False)

    def _inverse_hero_prop3(self):
        """Store hero_prop3 back to format_options."""
        for record in self:
            record.set_hero_option('prop3', record.hero_prop3)

    def get_hero_option(self, option_name, default=None):
        """
        Helper method to get a specific hero option value.
        
        Args:
            option_name (str): Name of the hero option
            default: Default value if option doesn't exist
            
        Returns:
            The option value or default
            
        Usage:
            record.get_hero_option('prop3', False)
        """
        self.ensure_one()
        if not self.format_options or not isinstance(self.format_options, dict):
            return default
        hero = self.format_options.get('hero', {})
        return hero.get(option_name, default)

    def get_page_option(self, option_name, default=None):
        """
        Helper method to get a specific page option value.
        
        Args:
            option_name (str): Name of the page option
            default: Default value if option doesn't exist
            
        Returns:
            The option value or default
            
        Usage:
            record.get_page_option('prop1', '')
            record.get_page_option('prop2', [])
        """
        self.ensure_one()
        if not self.format_options or not isinstance(self.format_options, dict):
            return default
        page = self.format_options.get('page', {})
        return page.get(option_name, default)

    def set_hero_option(self, option_name, value):
        """
        Helper method to set a specific hero option value.
        
        Args:
            option_name (str): Name of the hero option
            value: Value to set
            
        Usage:
            record.set_hero_option('prop3', False)
        """
        self.ensure_one()
        current_options = self.format_options or {}
        if 'hero' not in current_options:
            current_options['hero'] = {}
        current_options['hero'][option_name] = value
        self.format_options = current_options

    def set_page_option(self, option_name, value):
        """
        Helper method to set a specific page option value.
        
        Args:
            option_name (str): Name of the page option
            value: Value to set
            
        Usage:
            record.set_page_option('prop1', 'value1')
            record.set_page_option('prop2', ['val1', 'val2'])
        """
        self.ensure_one()
        current_options = self.format_options or {}
        if 'page' not in current_options:
            current_options['page'] = {}
        current_options['page'][option_name] = value
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