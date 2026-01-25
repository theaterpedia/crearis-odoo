# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

"""
DASEi Course Model

Represents annual training cohorts (K26, K27, etc.) synced from SharePoint plan_kurse.
Used for:
- Grouping participants via plan_kursteilnehmer
- Domain code mapping for website filtering
- Course-level reporting and analytics
"""

from odoo import models, fields


class DaseiCourse(models.Model):
    _name = 'dasei.course'
    _description = 'DASEi Course'
    _order = 'year desc, code'
    _rec_name = 'code'

    name = fields.Char(string="Course Name", required=True)
    code = fields.Char(string="Course Code", index=True, help="e.g., K26, K27")
    year = fields.Integer(string="Year")
    location = fields.Char(string="Location", help="e.g., Witten, Kassel, Online")
    date_start = fields.Datetime(string="Start Date")
    date_end = fields.Datetime(string="End Date")
    
    # Company isolation
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        required=True,
        index=True,
    )
    
    # SharePoint sync fields
    ms_item_id = fields.Char(string="SharePoint Item ID", index=True)
    ms_etag = fields.Char(string="SharePoint ETag")
    
    # Related domain code (optional mapping to website)
    domain_code_id = fields.Many2one(
        'website',
        string="Domain Code",
        help="Maps this course to a specific website/domain"
    )
    
    # Computed stats
    participant_count = fields.Integer(
        string="Participants",
        compute='_compute_participant_count',
    )
    
    def _compute_participant_count(self):
        Participation = self.env['dasei.course.participation']
        for course in self:
            course.participant_count = Participation.search_count([
                ('course_id', '=', course.id)
            ])
