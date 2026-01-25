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
        """
        Compute stable content ID (cid) for blog posts.
        
        Format: {domain}.blog-post__{id}
        Example: dasei.blog-post__42
        
        CID is stable and NEVER changes after creation.
        """
        for post in self:
            domain_code = post.website_id.domain_code if post.website_id else 'private'
            post.cid = '{}.blog-post__{}'.format(domain_code, post.id or 0)

    @api.depends("name")
    def _compute_slug(self):
        """
        Compute SEO-friendly slug from post name.
        
        Only auto-generates on creation (when slug is empty).
        Does NOT auto-update when name changes to preserve permalinks.
        """
        import re
        for post in self:
            if not post.slug and post.name:
                slug = post.name.lower()
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
                slug = re.sub(r'[^a-z0-9]+', '_', slug)
                slug = slug.strip('_')
                post.slug = slug
            elif not post.slug:
                post.slug = ''

    @api.depends("cid", "slug")
    def _compute_cid_slug(self):
        """
        Compute combined permalink: {cid}__{slug}
        
        Example: dasei.blog-post__42__mein_erster_blogpost
        """
        for post in self:
            if post.cid and post.slug:
                post.cid_slug = '{}_{}'.format(post.cid, post.slug)
            else:
                post.cid_slug = post.cid or ''

    cid = fields.Char(
        "Crearis ID",
        translate=False,
        compute=_compute_cid,
        store=True
    )
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
        for post in self:
            if post.name:
                slug = post.name.lower()
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
                slug = re.sub(r'[^a-z0-9]+', '_', slug)
                slug = slug.strip('_')
                post.slug = slug
        return True

    def write(self, vals):
        """Override write to increment version and invalidate cache."""
        vals['version'] = self.version + 1
        res = super(BlogPost, self).write(vals)
        
        # Invalidate cache to ensure fresh reads after write
        self.invalidate_recordset()

        return res
