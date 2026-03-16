# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene
from graphql import GraphQLError

from odoo import _
from odoo.addons.graphql_theaterpedia.schemas.objects import Partner


class PartnerFilterInput(graphene.InputObjectType):
    ids = graphene.List(graphene.Int, required=True)
    include_demo = graphene.Boolean(
        required=False,
        description="Include demo data records. If not specified, uses system config parameter."
    )


class PartnerQuery(graphene.ObjectType):
    partners = graphene.List(
        graphene.NonNull(Partner),
        filter=graphene.Argument(PartnerFilterInput, required=True)
    )
    
    # P8: ir.rule-aware Partner query - respects origin_domain_code isolation
    partners_for_domain = graphene.List(
        graphene.NonNull(Partner),
        domain_code=graphene.String(required=True, description="Domain code to filter partners"),
        include_legacy=graphene.Boolean(
            default_value=True, 
            description="Include legacy partners (origin_domain_code = NULL)"
        ),
    )

    @staticmethod
    def resolve_partners(self, info, filter):
        env = info.context["env"]
        ResPartner = env['res.partner'].sudo()
        
        partner_ids = filter.get('ids', [])
        
        if not partner_ids:
            raise GraphQLError(_('No partner IDs provided.'))
        
        # Search for partners with the provided IDs
        partners = ResPartner.browse(partner_ids).exists()
        
        if not partners:
            raise GraphQLError(_('No partners found with the provided IDs.'))
        
        # Determine if we should include demo data
        # Priority: query parameter > config parameter
        include_demo = filter.get('include_demo')
        
        if include_demo is None:
            # Not specified in query, use config parameter
            ICP = env['ir.config_parameter'].sudo()
            include_demo = ICP.get_param('crearis.graphql.include_demo', 'True') == 'True'
        
        # Filter out demo data if requested
        if not include_demo:
            # Get all XML IDs for these partners
            xml_id_data = env['ir.model.data'].sudo().search([
                ('model', '=', 'res.partner'),
                ('res_id', 'in', partners.ids)
            ])
            
            # Find demo partner IDs (XML IDs starting with _demo)
            demo_ids = set(
                data.res_id for data in xml_id_data 
                if data.complete_name.split('.')[-1].startswith('_demo')
            )
            
            # Filter them out
            if demo_ids:
                partners = partners.filtered(lambda p: p.id not in demo_ids)
            
            if not partners:
                raise GraphQLError(_('No non-demo partners found with the provided IDs.'))
        
        return partners

    # P8: Resolve partners for domain - respects origin_domain_code isolation
    @staticmethod
    def resolve_partners_for_domain(self, info, domain_code, include_legacy=True):
        env = info.context["env"]
        ResPartner = env['res.partner'].sudo()
        
        # Build domain filter
        if include_legacy:
            # Include partners from this domain OR legacy (NULL origin)
            domain = [
                '|',
                ('origin_domain_code', '=', False),
                ('origin_domain_code', '=', domain_code),
            ]
        else:
            # Only partners from this specific domain
            domain = [('origin_domain_code', '=', domain_code)]
        
        return ResPartner.search(domain)