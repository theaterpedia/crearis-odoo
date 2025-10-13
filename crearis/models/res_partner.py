# -*- coding: utf-8 -*-
# Copyright 2025 Hans Dönitz - Theaterpedia.org
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models


class ResPartner(models.Model):
    """Adds Markdown-Field and Web Options to partner"""

    _inherit = ["res.partner", "web.options.abstract", "demo.data.mixin"]
    _name = "res.partner"

    # HERO-TYPE, FORMAT, CIMG > are developed and tested in model event
    header_type = fields.Selection(
        string='Header',
        selection=[
            ("simple", "simple"),
            ("columns", 'Text-Bild (2 Spalten)'),
            ("banner", "Banner medium"),
            ("cover", "Cover Fullsize"),
            ("bauchbinde", "Bauchbinde")
        ],
        help="What header-type introduces the Partner?",
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
        string='Hero-Image-Link',
        translate=False,
        default='',
        help="public url for the hero-image"
    )

    md = fields.Text(
        string='Markdown Content',
        translate=True,
        help="Markdown content for partner profile.",
        default=''
    )
