# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models

# Module grouping from event_type Title (e.g., A1->A, B2->B)
MODULE_GROUPS = {
    'A': 'Modul A - Grundlagen Spielen',
    'B': 'Modul B - Grundlagen Anleiten',
    'C': 'Modul C - Theaterprojekt',
    'D': 'Modul D - Konzeption',
    'E': 'Modul E - Gruppenarbeit',
    'F': 'Modul F - Feedback',
    'G': 'Modul G - Vertiefung',
    'H': 'Modul H - Bewegungstheater',
    'J': 'Modul J - Abenteuertheater',
    'L': 'Modul L - Zusatzqualifikation',
    'T': 'Modul T - Tagesseminare',
    'R': 'Modul R - Trainings',
    'Z': 'Modul Z - Specials',
}


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # SharePoint sync fields
    ms_contact_id = fields.Char(
        string='MS Contact ID',
        index=True,
        help='SharePoint contacts list item ID for this product'
    )
    ms_etag = fields.Char(string='MS ETag')

    # Course program fields
    course_program = fields.Selection([
        ('M', 'München'),
        ('N', 'Nürnberg'),
        ('ZR', 'Profil Theaterpädagogische Regie'),
        ('ZT', 'Profil Theaterpädagogisches Training'),
    ], string='Course Program', help='Course program location/type')

    course_year = fields.Char(
        string='Course Year/Cohort',
        help='Year or cohort identifier (e.g., 18 for 2018, 2026-2028 for ZR/ZT)'
    )

    course_type = fields.Selection([
        ('block', 'Blockprogramm'),
        ('day', 'Tageskurs'),
        ('profile', 'Aufbaustufe'),
    ], string='Course Type')

    @api.model
    def _parse_course_fullname(self, fullname):
        """Parse SharePoint FullName into course attributes.
        
        Examples:
        - '_M18_Blockprogramm München' -> program=M, year=18, type=block
        - '_N18_Tageskurs Nürnberg' -> program=N, year=18, type=day
        - '_Profil ZR 2026-2028' -> program=ZR, year=2026-2028, type=profile
        """
        result = {
            'course_program': False,
            'course_year': False,
            'course_type': False,
        }
        
        if not fullname or not fullname.startswith('_'):
            return result

        name = fullname[1:]  # Remove leading underscore
        
        # Check for ZR/ZT profiles
        if name.startswith('Profil ZR'):
            result['course_program'] = 'ZR'
            result['course_type'] = 'profile'
            # Extract year like "2026-2028"
            parts = name.split()
            if len(parts) >= 3:
                result['course_year'] = parts[2]
        elif name.startswith('Profil ZT'):
            result['course_program'] = 'ZT'
            result['course_type'] = 'profile'
            parts = name.split()
            if len(parts) >= 3:
                result['course_year'] = parts[2]
        # Check for M/N programs
        elif name.startswith('M') or name.startswith('N'):
            # Extract program letter and year
            result['course_program'] = name[0]
            # Year is typically 2 digits after the letter
            if len(name) > 1:
                year_part = ''
                for char in name[1:]:
                    if char.isdigit():
                        year_part += char
                    else:
                        break
                if year_part:
                    result['course_year'] = year_part
            
            # Determine type from name
            if 'Blockprogramm' in name:
                result['course_type'] = 'block'
            elif 'Tageskurs' in name:
                result['course_type'] = 'day'
        
        return result
