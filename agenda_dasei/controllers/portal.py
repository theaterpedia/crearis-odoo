# -*- coding: utf-8 -*-
# Copyright 2026 theaterpedia.org / crearis.io
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class DaseiCustomerPortal(CustomerPortal):
    """
    Customer portal for DASEi with 3-tab sidebar:
    - Agenda: Timeline of registered sessions
    - Curriculum: A-B-C-D progress (dasei2 only)
    - Service: Contract info, Q&A
    
    Progressive disclosure based on registration state.
    """
    
    def _prepare_home_portal_values(self, counters):
        """Add agenda line count to portal home."""
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        
        if 'agenda_count' in counters:
            # Count agenda lines from customer's event registrations
            registrations = request.env['event.registration'].sudo().search([
                ('partner_id', '=', partner.id),
                ('state', 'in', ['open', 'done']),
            ])
            event_ids = registrations.mapped('event_id').ids
            values['agenda_count'] = request.env['agenda.line'].sudo().search_count([
                ('event_id', 'in', event_ids),
                ('type', '=', 'session'),
            ])
        
        return values

    def _get_customer_tabs(self, partner):
        """
        Determine which tabs to show based on progressive disclosure.
        
        States:
        - Anmeldung (post-checkout, before confirmation): Service only
        - Angemeldet (confirmed, pending first event): Agenda
        - Einstiege (dasei1 customer): Agenda, Service
        - Grundlagenbildung (dasei2 customer): All 3 tabs
        """
        tabs = []
        
        # Check registrations
        registrations = request.env['event.registration'].sudo().search([
            ('partner_id', '=', partner.id),
        ])
        confirmed_registrations = registrations.filtered(lambda r: r.state in ['open', 'done'])
        
        # Default: Service tab always visible
        tabs.append({
            'id': 'service',
            'name': _('Service'),
            'url': '/my/service',
            'icon': 'fa-headset',
        })
        
        # Agenda tab: visible once confirmed
        if confirmed_registrations:
            tabs.insert(0, {
                'id': 'agenda',
                'name': _('Agenda'),
                'url': '/my/agenda',
                'icon': 'fa-calendar-alt',
            })
        
        # Curriculum tab: dasei2 only (Grundlagenbildung)
        # Check if partner has dasei2 domain code or multi-product registration
        dasei_domaincode = getattr(partner, 'dasei_domaincode', None)
        if dasei_domaincode == 'dasei2' or self._has_curriculum_access(partner):
            tabs.insert(1, {
                'id': 'curriculum',
                'name': _('Curriculum'),
                'url': '/my/curriculum',
                'icon': 'fa-graduation-cap',
            })
        
        return tabs
    
    def _has_curriculum_access(self, partner):
        """Check if partner has access to curriculum tab (multi-product customer)."""
        # TODO: Check for B, C, D product registrations
        return False

    def _prepare_dasei_portal_values(self, active_tab='agenda'):
        """Prepare common values for all DASEi portal pages."""
        partner = request.env.user.partner_id
        values = self._prepare_portal_layout_values()
        
        tabs = self._get_customer_tabs(partner)
        
        values.update({
            'tabs': tabs,
            'active_tab': active_tab,
            'partner': partner,
            'page_name': f'dasei_{active_tab}',
        })
        
        return values

    # =========================================================================
    # Agenda Tab
    # =========================================================================

    @http.route(['/my/agenda'], type='http', auth='user', website=True)
    def portal_my_agenda(self, **kw):
        """Display customer's agenda - upcoming sessions from registered events."""
        values = self._prepare_dasei_portal_values('agenda')
        partner = request.env.user.partner_id
        
        # Get customer's event registrations
        registrations = request.env['event.registration'].sudo().search([
            ('partner_id', '=', partner.id),
            ('state', 'in', ['open', 'done']),
        ])
        event_ids = registrations.mapped('event_id').ids
        
        # Get agenda lines for those events
        agenda_lines = request.env['agenda.line'].sudo().search([
            ('event_id', 'in', event_ids),
            ('type', '=', 'session'),
        ], order='date, start')
        
        # Group by event for display
        from collections import OrderedDict
        grouped_lines = OrderedDict()
        for line in agenda_lines:
            event = line.event_id
            if event.id not in grouped_lines:
                grouped_lines[event.id] = {
                    'event': event,
                    'lines': [],
                }
            grouped_lines[event.id]['lines'].append(line)
        
        values.update({
            'agenda_lines': agenda_lines,
            'grouped_lines': list(grouped_lines.values()),
            'registrations': registrations,
        })
        
        return request.render('agenda_dasei.portal_my_agenda', values)

    # =========================================================================
    # Service Tab
    # =========================================================================

    @http.route(['/my/service'], type='http', auth='user', website=True)
    def portal_my_service(self, **kw):
        """Display customer service page - contracts, Q&A."""
        values = self._prepare_dasei_portal_values('service')
        partner = request.env.user.partner_id
        
        # Get customer's sale orders (contracts)
        orders = request.env['sale.order'].sudo().search([
            ('partner_id', '=', partner.id),
            ('state', 'in', ['sale', 'done']),
        ], order='date_order desc')
        
        values.update({
            'orders': orders,
        })
        
        return request.render('agenda_dasei.portal_my_service', values)

    # =========================================================================
    # Curriculum Tab (dasei2 only)
    # =========================================================================

    @http.route(['/my/curriculum'], type='http', auth='user', website=True)
    def portal_my_curriculum(self, **kw):
        """Display curriculum progress - A-B-C-D modules (dasei2 only)."""
        values = self._prepare_dasei_portal_values('curriculum')
        partner = request.env.user.partner_id
        
        # Check access
        tabs = self._get_customer_tabs(partner)
        if not any(t['id'] == 'curriculum' for t in tabs):
            return request.redirect('/my/agenda')
        
        # Get registrations grouped by module (A, B, C, D)
        registrations = request.env['event.registration'].sudo().search([
            ('partner_id', '=', partner.id),
            ('state', 'in', ['open', 'done']),
        ])
        
        # Group by event type prefix (A, B, C, D)
        modules = {'A': [], 'B': [], 'C': [], 'D': []}
        for reg in registrations:
            event_type_name = reg.event_id.event_type_id.name or ''
            # Extract module letter from type name (e.g., "A1" -> "A")
            if isinstance(event_type_name, dict):
                event_type_name = event_type_name.get('en_US', '')
            if event_type_name and event_type_name[0] in modules:
                modules[event_type_name[0]].append(reg)
        
        values.update({
            'modules': modules,
        })
        
        return request.render('agenda_dasei.portal_my_curriculum', values)
