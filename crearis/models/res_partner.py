# Copyright 2025 Hans Dönitz - Theaterpedia.org
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models

class ResPartner(models.Model):
    """Adds Markdown-Field to partner"""

    _inherit = "res.partner"

    # HERO-TYPE, FORMAT, CIMG > are develeped and tested in model event
    hero_type = fields.Selection(
        string='Hero',
        selection=[("{}", 'Standard (prominent)'), ("{style:'banner'}", 'Banner prominent'), ("{height: 'full'}", 'Cover'), ("{height: 'full', style:'banner'}", 'Cover/Banner'), ("{height: 'small'}", 'minimal')],
        help="Layout changes the way the person/company is displayed on Websites.",
        default="{}")

    hero_format = fields.Text('Hero-Formatierung', translate=False, default='', help="Image placement and background for the hero section")

    cimg = fields.Text('Hero-Image-Link', translate=False, default='', help="public url for the hero-image")

    body_md = fields.Text("Body (Markdown)", index=True)
    # body_html = fields.Html("Body (HTML)", compute="_compute_body_html", store=True)

    # @api.depends("body_md")
    # def _compute_body_html(self):
    #     for record in self:
    #         record.body_html = markdown(record.body_md) if record.body_md else False