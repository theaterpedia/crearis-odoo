# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    # Microsoft Graph API Credentials
    ms_agenda_tenant_id = fields.Char(string="Tenant ID")
    ms_agenda_client_id = fields.Char(string="Client ID")
    ms_agenda_client_secret = fields.Char(string="Client Secret")
    ms_agenda_site_id = fields.Char(string="Site ID")

    # JSONB for list GUIDs
    ms_agenda_api = fields.Json(
        string="MS Agenda API Config",
        default=lambda self: self._default_ms_agenda_api()
    )

    # Sync configuration
    ms_agenda_sync_level = fields.Selection([
        ('init', 'Init - Full import from SharePoint'),
        ('slave', 'Slave - SharePoint drives updates'),
        ('master', 'Master - Odoo drives updates'),
    ], string="Sync Level", default='init')

    ms_agenda_last_sync = fields.Datetime(string="Last Sync")
    ms_agenda_sync_enabled = fields.Boolean(string="Auto-Sync Enabled", default=False)
    ms_agenda_sync_running = fields.Boolean(string="Sync Running", default=False, help="Lock flag to prevent concurrent sync")

    # Computed accessors for JSONB fields
    ms_list_veranstaltungen = fields.Char(
        compute='_compute_ms_agenda_fields',
        inverse='_inverse_ms_list_veranstaltungen',
        string="List: Veranstaltungen"
    )
    ms_list_veranstaltungscodes = fields.Char(
        compute='_compute_ms_agenda_fields',
        inverse='_inverse_ms_list_veranstaltungscodes',
        string="List: Veranstaltungscodes"
    )
    ms_list_referenten = fields.Char(
        compute='_compute_ms_agenda_fields',
        inverse='_inverse_ms_list_referenten',
        string="List: Referenten"
    )
    ms_list_planungsstatus = fields.Char(
        compute='_compute_ms_agenda_fields',
        inverse='_inverse_ms_list_planungsstatus',
        string="List: Planungsstatus"
    )
    ms_list_contacts = fields.Char(
        compute='_compute_ms_agenda_fields',
        inverse='_inverse_ms_list_contacts',
        string="List: Contacts"
    )
    ms_list_kursteilnehmer = fields.Char(
        compute='_compute_ms_agenda_fields',
        inverse='_inverse_ms_list_kursteilnehmer',
        string="List: Kursteilnehmer"
    )
    ms_list_kurse = fields.Char(
        compute='_compute_ms_agenda_fields',
        inverse='_inverse_ms_list_kurse',
        string="List: Kurse"
    )
    ms_list_veranstaltungsteilnehmer = fields.Char(
        compute='_compute_ms_agenda_fields',
        inverse='_inverse_ms_list_veranstaltungsteilnehmer',
        string="List: Veranstaltungsteilnehmer"
    )
    ms_list_seminarzeiten = fields.Char(
        compute='_compute_ms_agenda_fields',
        inverse='_inverse_ms_list_seminarzeiten',
        string="List: Seminarzeiten"
    )

    ms_agenda_configured = fields.Boolean(
        compute='_compute_ms_agenda_configured',
        store=True,
        string="Agenda Configured"
    )

    @api.model
    def _default_ms_agenda_api(self):
        return {
            'list_veranstaltungen': 'BA5CFB7C-CFE7-4EFD-BA0A-65F9019D5A53',
            'list_veranstaltungscodes': 'E4B1128D-2709-480D-82D0-77F42605FD1A',
            'list_referenten': '4BFD63EA-425C-4164-9550-2A193F7F98C9',
            'list_planungsstatus': '6ADC07D7-8208-4370-AFBF-67B223F2C996',
            'list_contacts': '7a77d6af-3a91-4109-8f56-9dbac73d2fa4',
            'list_kursteilnehmer': '2bf5f8e7-ebca-4a8b-b11e-feaee6a30287',
            'list_kurse': 'AA5F4A45-DB15-4588-BD12-4F38E99ACE0F',
            'list_veranstaltungsteilnehmer': 'C9E05737-4C47-4E0F-A6B6-C6D6F3FBE88D',
            'list_seminarzeiten': '6BBE92C5-82C5-40E7-8C5F-D6CB3018EC23',
        }

    @api.depends('ms_agenda_api')
    def _compute_ms_agenda_fields(self):
        for rec in self:
            api = rec.ms_agenda_api or {}
            rec.ms_list_veranstaltungen = api.get('list_veranstaltungen', '')
            rec.ms_list_veranstaltungscodes = api.get('list_veranstaltungscodes', '')
            rec.ms_list_referenten = api.get('list_referenten', '')
            rec.ms_list_planungsstatus = api.get('list_planungsstatus', '')
            rec.ms_list_contacts = api.get('list_contacts', '')
            rec.ms_list_kursteilnehmer = api.get('list_kursteilnehmer', '')
            rec.ms_list_kurse = api.get('list_kurse', '')
            rec.ms_list_veranstaltungsteilnehmer = api.get('list_veranstaltungsteilnehmer', '')
            rec.ms_list_seminarzeiten = api.get('list_seminarzeiten', '')

    def _inverse_ms_list_veranstaltungen(self):
        for rec in self:
            api = dict(rec.ms_agenda_api or {})
            api['list_veranstaltungen'] = rec.ms_list_veranstaltungen
            rec.ms_agenda_api = api

    def _inverse_ms_list_veranstaltungscodes(self):
        for rec in self:
            api = dict(rec.ms_agenda_api or {})
            api['list_veranstaltungscodes'] = rec.ms_list_veranstaltungscodes
            rec.ms_agenda_api = api

    def _inverse_ms_list_referenten(self):
        for rec in self:
            api = dict(rec.ms_agenda_api or {})
            api['list_referenten'] = rec.ms_list_referenten
            rec.ms_agenda_api = api

    def _inverse_ms_list_planungsstatus(self):
        for rec in self:
            api = dict(rec.ms_agenda_api or {})
            api['list_planungsstatus'] = rec.ms_list_planungsstatus
            rec.ms_agenda_api = api

    def _inverse_ms_list_contacts(self):
        for rec in self:
            api = dict(rec.ms_agenda_api or {})
            api['list_contacts'] = rec.ms_list_contacts
            rec.ms_agenda_api = api

    def _inverse_ms_list_kursteilnehmer(self):
        for rec in self:
            api = dict(rec.ms_agenda_api or {})
            api['list_kursteilnehmer'] = rec.ms_list_kursteilnehmer
            rec.ms_agenda_api = api

    def _inverse_ms_list_kurse(self):
        for rec in self:
            api = dict(rec.ms_agenda_api or {})
            api['list_kurse'] = rec.ms_list_kurse
            rec.ms_agenda_api = api

    def _inverse_ms_list_veranstaltungsteilnehmer(self):
        for rec in self:
            api = dict(rec.ms_agenda_api or {})
            api['list_veranstaltungsteilnehmer'] = rec.ms_list_veranstaltungsteilnehmer
            rec.ms_agenda_api = api

    def _inverse_ms_list_seminarzeiten(self):
        for rec in self:
            api = dict(rec.ms_agenda_api or {})
            api['list_seminarzeiten'] = rec.ms_list_seminarzeiten
            rec.ms_agenda_api = api

    @api.depends('ms_agenda_tenant_id', 'ms_agenda_client_id', 'ms_agenda_site_id')
    def _compute_ms_agenda_configured(self):
        for rec in self:
            rec.ms_agenda_configured = bool(
                rec.ms_agenda_tenant_id and
                rec.ms_agenda_client_id and
                rec.ms_agenda_site_id
            )

    def action_test_ms_connection(self):
        """Test Microsoft Graph API connection"""
        self.ensure_one()
        sync_engine = self.env['crearis.agenda.sync']
        try:
            token = sync_engine._get_access_token(self)
            if token:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Connection Successful',
                        'message': 'Successfully connected to Microsoft Graph API',
                        'type': 'success',
                        'sticky': False,
                    }
                }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Connection Failed',
                    'message': str(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }

    def action_sync_now(self):
        """Trigger manual sync"""
        self.ensure_one()
        sync_engine = self.env['crearis.agenda.sync']
        result = sync_engine.sync_all(self)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sync Complete',
                'message': f"Synced: {result.get('event_types', 0)} types, {result.get('events', 0)} events",
                'type': 'success',
                'sticky': False,
            }
        }
