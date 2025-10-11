# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene
from graphql import GraphQLError

from odoo import _
from odoo.addons.graphql_theaterpedia.schemas.objects import Partner


class PartnerFilterInput(graphene.InputObjectType):
    ids = graphene.List(graphene.Int, required=True)


class PartnerQuery(graphene.ObjectType):
    partners = graphene.List(
        graphene.NonNull(Partner),
        filter=graphene.Argument(PartnerFilterInput, required=True)
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
        
        return partners