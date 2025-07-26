# Copyright 2025 Hans Dönitz - Theaterpedia.org
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models

class ResPartner(models.Model):
    """Adds Markdown-Field to partner"""

    _inherit = "res.partner"

    body_md = fields.Text("Body (Markdown)", index=True)
    # body_html = fields.Html("Body (HTML)", compute="_compute_body_html", store=True)

    # @api.depends("body_md")
    # def _compute_body_html(self):
    #     for record in self:
    #         record.body_html = markdown(record.body_md) if record.body_md else False