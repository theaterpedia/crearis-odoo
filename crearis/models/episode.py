from odoo import models, fields, api
# from json_field import JsonField

class BlogPost(models.Model):
    _inherit = "blog.post"

    description = fields.Char('Teasertext', translate=True, default='')
    # blocks = JsonField('Pruvious Blocks', required=False, default=[])   # a json object represented as dict / list / python primitives, see: https://gist.github.com/danmana/5242f37b7d63daf4698de7c61c8b59fc
    blocks = fields.Json()
    # homesite_id = fields.Integer('Homesite', default=4)
    homesite_id = fields.Many2one(
        "website",
        string="Homesite",
        ondelete="restrict",
        help="Editing only allowed from this website.",
        index=True,
    )

    def json_data_store(self):
        if not self.blocks:
            self.blocks = []
