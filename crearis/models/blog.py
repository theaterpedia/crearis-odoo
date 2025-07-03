from odoo import models, fields

class BlogBlog(models.Model):
    _inherit = "blog.blog"

    template_code = fields.Char('Blog Template', translate=False, default='')