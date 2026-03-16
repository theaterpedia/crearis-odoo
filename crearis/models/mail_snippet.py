# -*- coding: utf-8 -*-
# Copyright 2026 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class MailSnippet(models.Model):
    """Layer-2 Email Snippet for reusable QWeb template blocks.
    
    Snippets are reusable QWeb blocks that can be called from mail templates
    using t-call="crearis.mail_snippet_CODE" syntax.
    
    They provide:
    - Centralized management of email content blocks
    - Scope filtering (general vs domain-specific)
    - Documentation of required variables
    - Backoffice editing via code widget
    """
    _name = 'crearis.mail.snippet'
    _description = 'Layer-2 Email Snippet'
    _order = 'scope, name'

    name = fields.Char(
        string='Name',
        required=True,
        help='Human-readable name, e.g. "Upcoming Events Table"'
    )
    code = fields.Char(
        string='Code',
        required=True,
        help='Technical identifier, e.g. "upcoming_events". '
             'Used in t-call as crearis.mail_snippet_CODE'
    )
    scope = fields.Selection(
        selection=[
            ('general', 'General (all domains)'),
            ('dasei', 'dasei.eu specific'),
            ('theaterpedia', 'theaterpedia.org specific'),
        ],
        default='general',
        string='Scope',
        help='Which domains can use this snippet'
    )
    active = fields.Boolean(default=True)
    
    qweb = fields.Text(
        string='QWeb Template',
        help='The QWeb template code. '
             'Use t-set to define variables, t-out to render.'
    )
    description = fields.Text(
        string='Description',
        help='Usage instructions and documentation'
    )
    required_vars = fields.Char(
        string='Required Variables',
        help='Comma-separated list of required context variables, '
             'e.g. "type_ids, city, limit"'
    )
    
    # Relationship to mail templates using this snippet
    template_ids = fields.Many2many(
        'mail.template',
        'mail_template_snippet_rel',
        'snippet_id',
        'template_id',
        string='Used By Templates',
        help='Mail templates that reference this snippet'
    )
    
    _sql_constraints = [
        ('code_scope_uniq', 'unique(code, scope)', 
         'Snippet code must be unique per scope!')
    ]
