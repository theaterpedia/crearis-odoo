# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # SharePoint sync fields
    ms_contact_id = fields.Char(string="SP Contact ID", index=True)
    ms_contact_status = fields.Integer(string="Contact Status (plan_contacts_status)")
    ms_kursteilnehmer_id = fields.Char(string="SP Kursteilnehmer ID", index=True)
    ms_kurs_level = fields.Char(string="Highest Kurs", help="Highest evaluated Kurs code (ME, MB, ZR, etc)")
    ms_version = fields.Char(string="SharePoint oversion")

    # Computed highest domaincode for login routing
    dasei_domaincode = fields.Char(
        compute='_compute_dasei_domaincode',
        store=True,
        string="DASEi Domaincode",
        help="Highest domaincode from status or domainuser records"
    )

    @api.depends('ms_contact_status', 'ms_kurs_level')
    def _compute_dasei_domaincode(self):
        """Compute highest domaincode from contact status, kurs level, or domainuser records"""
        CODE_PRIORITY = {
            'dasei': 100,   # Vereinsmitglied (status 8, 9, 10)
            'dasei3': 30,   # Aufbaustufe (ZR, ZT)
            'dasei2': 20,   # Grundstufe (M?/N? except ME/NE)
            'dasei1': 10,   # Einstiege (ME, NE)
            'dasei0': 1,    # Quick entry
        }

        for partner in self:
            all_codes = []

            # Get domaincode from contact status
            status_code = partner._status_to_domaincode(
                partner.ms_contact_status,
                partner.ms_kurs_level
            )
            if status_code:
                all_codes.append(status_code)

            # TODO: Get from domainuser records when dasei.domainuser model is implemented
            # if partner.domainuser_ids:
            #     du_codes = partner.domainuser_ids.mapped('domain_code')
            #     all_codes.extend([c for c in du_codes if c])

            if not all_codes:
                partner.dasei_domaincode = False
                continue

            # Find highest priority code
            highest = max(all_codes, key=lambda c: CODE_PRIORITY.get(c, 0))
            partner.dasei_domaincode = highest

    def _status_to_domaincode(self, status, kurs_level=None):
        """Map contacts.Status (plan_contacts_status ID) to domaincode

        For status=1, kurs_level overrides if provided (from kursteilnehmer evaluation)
        """
        if not status:
            return False

        # For status=1 (active), use kurs_level if available
        if status == 1 and kurs_level:
            return self._kurs_to_domaincode(kurs_level)

        STATUS_MAP = {
            1: 'dasei1',   # Active participant (default, may be overridden)
            2: 'dasei2',   # Former participant level 2
            3: 'dasei3',   # Former participant level 3
            4: 'dasei1',   # Aborted participation
            5: 'dasei0',   # Quick entry
            8: 'dasei',    # Vereinsmitglied (member role)
            9: 'dasei',    # Vereinsmitglied (participant role)
            10: 'dasei',   # Partner role
        }
        return STATUS_MAP.get(status, False)

    def _kurs_to_domaincode(self, kurs):
        """Map Kurs code to domaincode

        ZR/ZT → dasei3 (highest)
        M?/N? (except ME/NE) → dasei2
        ME/NE → dasei1
        """
        if not kurs:
            return False

        if kurs in ('ZR', 'ZT'):
            return 'dasei3'
        if kurs.startswith(('M', 'N')) and kurs not in ('ME', 'NE'):
            return 'dasei2'
        if kurs in ('ME', 'NE'):
            return 'dasei1'

        return False

    def _evaluate_kurs_level(self, kurs):
        """Evaluate single Kurs value to (domaincode, priority)"""
        if not kurs:
            return None, 0
        if kurs in ('ZR', 'ZT'):
            return 'dasei3', 3
        if kurs.startswith(('M', 'N')) and kurs not in ('ME', 'NE'):
            return 'dasei2', 2
        if kurs in ('ME', 'NE'):
            return 'dasei1', 1
        return None, 0

    def should_sync_vereinsmitglied(self):
        """Status 8,9,10 only sync domainuser if no existing entries"""
        self.ensure_one()
        # TODO: Implement when dasei.domainuser model exists
        # return len(self.domainuser_ids) == 0
        return True
