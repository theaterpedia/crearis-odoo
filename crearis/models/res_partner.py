# Copyright 2025 Hans Dönitz - Theaterpedia.org
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models

class ResPartner(models.Model):
    """Adds Markdown-Field to partner"""

    _inherit = "res.partner"

    # HERO-TYPE, FORMAT, CIMG > are develeped and tested in model event
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

    format_options = fields.Json()
    
    cimg = fields.Text('Hero-Image-Link', translate=False, default='', help="public url for the hero-image")

    body_md = fields.Text("Body (Markdown)", index=True)
    # body_html = fields.Html("Body (HTML)", compute="_compute_body_html", store=True)

    # @api.depends("body_md")
    # def _compute_body_html(self):
    #     for record in self:
    #         record.body_html = markdown(record.body_md) if record.body_md else False