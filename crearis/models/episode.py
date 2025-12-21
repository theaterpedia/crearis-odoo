# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api


class BlogPost(models.Model):
    _inherit = ['blog.post', 'web.options.abstract', "demo.data.mixin"]
    _name = 'blog.post'

    description = fields.Char('Teasertext', translate=True, default='')
    blocks = fields.Json()

    header_type = fields.Selection(
        string='Header',
        selection=[
            ("simple", "simple"),
            ("columns", 'Text-Bild (2 Spalten)'),
            ("banner", "Banner medium"),
            ("cover", "Cover Fullsize"),
            ("bauchbinde", "Bauchbinde")
        ],
        help="What header-type introduces the post?",
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

    cimg = fields.Text(
        'Hero/Preview Image',
        translate=False,
        default='',
        help="xmlid or public url for hero and thumbnail image"
    )

    md = fields.Text('Markdown Content', translate=True, help="Markdown body of the post.", default='')

    version = fields.Integer(default=1)

    homesite_id = fields.Many2one(
        "website",
        string="Homesite (Editing Website)",
        ondelete="restrict",
        help="Editing only allowed from this website.",
        index=True,
    )

    def json_data_store(self):
        """Initialize blocks if empty."""
        if not self.blocks:
            self.blocks = []

    @api.depends("website_id")
    def _compute_cid(self):
        """Compute Crearis ID based on website and post ID."""
        template_code = 'post'

        for post in self:
            domain_code = 'private'
            if post.website_id.domain_code:
                domain_code = post.website_id.domain_code

            if not post.id:
                post.cid = '{}.blog-{}__{}'.format(domain_code, template_code, "-1")
            else:
                post.cid = '{}.blog-{}__{}'.format(domain_code, template_code, post.id)

    cid = fields.Char(
        "Crearis ID",
        translate=False,
        compute=_compute_cid,
        store=True
    )

    def write(self, vals):
        """Override write to increment version and invalidate cache."""
        vals['version'] = self.version + 1
        res = super(BlogPost, self).write(vals)
        
        # Invalidate cache to ensure fresh reads after write
        self.invalidate_recordset()

        return res
