# -*- coding: utf-8 -*-
# Copyright 2026 theaterpedia.org / crearis.io
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
"""
CheckoutMutation for DASEi checkout flow.

Creates partner, sale.order, product.package.event.line(s), and event.registration(s) 
from NUXT checkout form. Replaces old PowerAutomate/SharePoint integration.

Usage:
    mutation {
        checkout(checkout: {
            product_ref: "M18E",
            path: "muenchen_block",
            contact: { email: "...", vorname: "...", nachname: "..." },
            accept_terms: true,
            accept_privacy: true,
            accept_cancellation: true
        }) {
            success
            error
            order { id name }
            partner { id email }
            registrations
            packageLines
        }
    }

Path options:
- muenchen_block: München events, Blockseminar schedule
- muenchen_day: München events, Tageskurs schedule
- nuernberg_block: Nürnberg events, Blockseminar schedule
- nuernberg_day: Nürnberg events, Tageskurs schedule
"""

import graphene
from graphql import GraphQLError
from odoo.http import request
from odoo import _

from odoo.addons.graphql_theaterpedia.schemas.objects import Order, Partner


class CheckoutContactInput(graphene.InputObjectType):
    """Contact information for checkout"""
    email = graphene.String(required=True)
    vorname = graphene.String(required=True)
    nachname = graphene.String(required=True)
    strasse = graphene.String()
    plz = graphene.String()
    ort = graphene.String()
    mobil = graphene.String()


class CheckoutInput(graphene.InputObjectType):
    """Input for checkout mutation"""
    product_ref = graphene.String(
        required=True, 
        description="Product default_code, e.g. 'M18E'"
    )
    contact = graphene.Field(CheckoutContactInput, required=True)
    path = graphene.String(
        description="Path choice for event prefilling: muenchen_block, muenchen_day, nuernberg_block, nuernberg_day"
    )
    notes = graphene.String(description="Optional booking notes")
    accept_terms = graphene.Boolean(required=True)
    accept_privacy = graphene.Boolean(required=True)
    accept_cancellation = graphene.Boolean(required=True)


class CheckoutResult(graphene.ObjectType):
    """Result of checkout mutation"""
    success = graphene.Boolean()
    order = graphene.Field(Order)
    partner = graphene.Field(Partner)
    registrations = graphene.List(graphene.Int, description="Created event.registration IDs")
    package_lines = graphene.List(graphene.Int, description="Created product.package.event.line IDs")
    error = graphene.String()


class Checkout(graphene.Mutation):
    """
    Complete checkout: create partner, sale.order, and event registrations.
    
    Replaces the old PowerAutomate/SharePoint flow.
    """
    class Arguments:
        checkout = CheckoutInput(required=True)

    Output = CheckoutResult

    @staticmethod
    def mutate(self, info, checkout):
        env = info.context['env']
        website = env['website'].get_current_website()
        request.website = website
        
        # Validate terms acceptance
        if not all([
            checkout.accept_terms,
            checkout.accept_privacy,
            checkout.accept_cancellation,
        ]):
            return CheckoutResult(
                success=False,
                error=_('All terms must be accepted')
            )
        
        # Find product by default_code
        Product = env['product.template'].sudo()
        product = Product.search([
            ('default_code', '=ilike', checkout.product_ref)
        ], limit=1)
        
        if not product:
            return CheckoutResult(
                success=False,
                error=_('Product not found: %s') % checkout.product_ref
            )
        
        # Get or create partner
        contact = checkout.contact
        Partner = env['res.partner'].sudo()
        partner = Partner.search([('email', '=ilike', contact.email)], limit=1)
        
        if not partner:
            partner_vals = {
                'name': f"{contact.vorname} {contact.nachname}".strip(),
                'email': contact.email,
            }
            # Add partner_firstname fields if available
            if hasattr(Partner, 'firstname'):
                partner_vals['firstname'] = contact.vorname
                partner_vals['lastname'] = contact.nachname
            # Add optional fields
            if contact.mobil:
                partner_vals['phone'] = contact.mobil
            if contact.strasse:
                partner_vals['street'] = contact.strasse
            if contact.plz:
                partner_vals['zip'] = contact.plz
            if contact.ort:
                partner_vals['city'] = contact.ort
                
            partner = Partner.create(partner_vals)
        
        # Create sale order
        SaleOrder = env['sale.order'].sudo()
        order = SaleOrder.create({
            'partner_id': partner.id,
            'partner_invoice_id': partner.id,
            'partner_shipping_id': partner.id,
            'website_id': website.id,
            'note': checkout.notes or '',
            'order_line': [(0, 0, {
                'product_id': product.product_variant_id.id,
                'product_uom_qty': 1,
                'price_unit': product.list_price,
            })],
        })
        
        # Confirm order (draft → sent)
        order.action_quotation_sent()
        
        # Create product.package.event.line records if product is event_package
        registration_ids = []
        package_line_ids = []
        
        if product.detailed_type == 'event_package' and product.package_event_type_ids:
            PackageEventLine = env['product.package.event.line'].sudo()
            EventEvent = env['event.event'].sudo()
            EventRegistration = env['event.registration'].sudo()
            
            # Parse path for city filter
            path = checkout.path or ''
            city_filter = None
            if 'muenchen' in path.lower():
                city_filter = 'München'
            elif 'nuernberg' in path.lower():
                city_filter = 'Nürnberg'
            
            sale_order_line = order.order_line[0] if order.order_line else False
            sequence = 10
            
            for event_type in product.package_event_type_ids:
                # Build domain for finding events
                domain = [
                    ('event_type_id', '=', event_type.id),
                    ('stage_id.pipe_end', '=', False),  # Not cancelled/done
                ]
                if product.package_date_start:
                    domain.append(('date_begin', '>=', product.package_date_start))
                if product.package_date_end:
                    domain.append(('date_end', '<=', product.package_date_end))
                
                # Apply city filter from path
                if city_filter:
                    domain.append(('address_id.city', 'ilike', city_filter))
                
                # Find next available event
                event = EventEvent.search(domain, order='date_begin asc', limit=1)
                
                # Create package event line
                package_line_vals = {
                    'sale_order_line_id': sale_order_line.id if sale_order_line else False,
                    'event_type_id': event_type.id,
                    'sequence': sequence,
                    'state': 'selected' if event else 'pending',
                }
                
                if event:
                    package_line_vals['event_id'] = event.id
                    
                    # Create registration for selected event
                    existing_reg = EventRegistration.search([
                        ('partner_id', '=', partner.id),
                        ('event_id', '=', event.id),
                    ], limit=1)
                    
                    if not existing_reg:
                        registration = EventRegistration.create({
                            'partner_id': partner.id,
                            'event_id': event.id,
                            'sale_order_id': order.id,
                            'sale_order_line_id': sale_order_line.id if sale_order_line else False,
                        })
                        registration_ids.append(registration.id)
                        package_line_vals['registration_id'] = registration.id
                        package_line_vals['state'] = 'registered'
                
                package_line = PackageEventLine.create(package_line_vals)
                package_line_ids.append(package_line.id)
                sequence += 10
        
        # Send checkout confirmation email (T2)
        # Template: agenda_dasei.mail_template_checkout_confirmation
        try:
            mail_template = env.ref('agenda_dasei.mail_template_checkout_confirmation', raise_if_not_found=False)
            if mail_template:
                mail_template.send_mail(order.id, force_send=False)  # Queue, don't block
        except Exception as e:
            # Log but don't fail checkout if email fails
            import logging
            _logger = logging.getLogger(__name__)
            _logger.warning("Checkout email send failed for order %s: %s", order.name, str(e))
        
        return CheckoutResult(
            success=True,
            order=order,
            partner=partner,
            registrations=registration_ids,
            package_lines=package_line_ids,
        )


class CheckoutMutation(graphene.ObjectType):
    checkout = Checkout.Field(description="Complete checkout with partner, order, and registrations")
