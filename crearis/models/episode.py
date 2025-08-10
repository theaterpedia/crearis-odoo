from odoo import models, fields, api # type: ignore
# from json_field import JsonField

class BlogPost(models.Model):
    _inherit = "blog.post"

    description = fields.Char('Teasertext', translate=True, default='')
    # blocks = JsonField('Pruvious Blocks', required=False, default=[])   # a json object represented as dict / list / python primitives, see: https://gist.github.com/danmana/5242f37b7d63daf4698de7c61c8b59fc
    blocks = fields.Json()
    # homesite_id = fields.Integer('Homesite', default=4)

    hero_type = fields.Selection(
        string='Hero',
        selection=[("{}", 'Standard (prominent)'), ("{style:'banner'}", 'Banner prominent'), ("{height: 'full'}", 'Cover'), ("{height: 'full', style:'banner'}", 'Cover/Banner'), ("{height: 'small'}", 'minimal')],
        help="Layout changes the way the event is displayed on Websites.",
        default="{}")

    hero_format = fields.Text('Hero-Formatierung', translate=False, default='', help="Image placement and background for the hero section")

    cimg = fields.Text('Hero-Image-Link', translate=False, default='', help="public url for the hero-image")

    body_md = fields.Text("Body (Markdown)", index=True)

    version = fields.Integer(default=1)  # we tweak this in def write 

    homesite_id = fields.Many2one(
        "website",
        string="Homesite (Editing Website)",
        ondelete="restrict",
        help="Editing only allowed from this website.",
        index=True,
    )

    def json_data_store(self):
        if not self.blocks:
            self.blocks = []


    # ----------------------------------
    # crearis-interface

    @api.depends("website_id")
    def _compute_cid(self):
        template_code = 'post'

        domain_code = 'private'
        if self.website_id.domain_code:
            domain_code = self.website_id.domain_code

        for post in self:
            if not post.id:
                post.cid = '{}.blog-{}__{}'.format(domain_code, template_code, "-1")
            else:
                post.cid = '{}.blog-{}__{}'.format(domain_code, template_code, post.id)

    cid = fields.Char("Crearis ID", translate=False,compute=_compute_cid, store=True)

    def write(self, vals):
        # Code before write: 'self' has the old values
        vals['version'] = self.version + 1
        super().write(vals)
        # Code after write: 'self' has the new values

        return True
