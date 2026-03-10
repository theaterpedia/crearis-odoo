# -*- coding: utf-8 -*-
# Copyright 2026 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

"""
CRM Lead extension for S2L (Two-Lanes) email-only consulting inquiries.

Direction 4 architecture: crm.lead serves as native home for email-only lane.
- is_consulting_inquiry: flags leads from consulting flow
- consulting_domain_code: links to domainuser for exec assignment

Staff can create leads directly in Odoo (inside-out trigger).
GraphQL mutation CreateEmailInquiry creates leads from external website.
Both appear in controlling.dashboard.
"""

from datetime import timedelta
from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # ─── S2L Consulting Fields ───────────────────────────────────────────────
    is_consulting_inquiry = fields.Boolean(
        string='Consulting Inquiry',
        default=False,
        help='True if created via S2L email-only consulting flow',
    )

    consulting_domain_code = fields.Selection(
        selection=[
            ('dasei1', 'Einstiege'),
            ('dasei2', 'Grundlagen'),
            ('dasei3', 'Aufbaustufe'),
            ('external', 'External'),
        ],
        string='Consulting Domain',
        help='Source domain for exec assignment via domainuser',
    )

    # ─── Auto-assign exec on create ──────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)

        for lead in leads:
            if lead.is_consulting_inquiry and not lead.user_id:
                lead._assign_exec_from_domainuser()

        return leads

    def _assign_exec_from_domainuser(self):
        """Assign exec user based on domain_code via domainuser model."""
        self.ensure_one()
        if not self.consulting_domain_code:
            return

        DomainUser = self.env['crearis.domainuser'].sudo()
        Website = self.env['website'].sudo()

        # Find website by domain_code
        website = Website.search([
            ('domain_code', '=', self.consulting_domain_code)
        ], limit=1)

        if not website:
            return

        # Find exec domainuser for this domain
        exec_du = DomainUser.search([
            ('domain_id', '=', website.id),
            ('role', '=', 'exec'),
            ('active', '=', True),
        ], limit=1)

        if exec_du and exec_du.user_id:
            self.user_id = exec_du.user_id

    # ─── Convenience Actions ─────────────────────────────────────────────────
    def action_generate_checkout_url(self):
        """Generate personalized checkout URL and post to chatter."""
        self.ensure_one()

        # Build URL based on domain
        base_url = '/ausbildung-theaterpaedagogik'
        route_map = {
            'dasei1': '/kurs_einstiege_ins_theaterspiel',
            'dasei2': '/grundlagenbildung',
            'dasei3': '/aufbaustufe',
        }

        route = route_map.get(self.consulting_domain_code, '/aufbaustufe')
        url = f"{base_url}{route}"
        if self.partner_id:
            url += f"?partner_id={self.partner_id.id}"

        # Post URL to chatter
        self.message_post(
            body=f'<p>🔗 Checkout-URL generiert:</p>'
                 f'<p><a href="{url}">{url}</a></p>',
            subtype_xmlid='mail.mt_note',
        )

        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    def action_mark_converted(self):
        """Mark lead as won after checkout completion."""
        won_stage = self.env['crm.stage'].search([
            ('is_won', '=', True)
        ], limit=1)
        if won_stage:
            self.stage_id = won_stage
