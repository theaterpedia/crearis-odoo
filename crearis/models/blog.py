from odoo import models, fields, api
import psycopg2

class BlogBlog(models.Model):
    _inherit = "blog.blog"

    template_code = fields.Char('Blog Template', translate=False, default='')