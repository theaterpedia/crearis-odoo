# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org, Hans Dönitz
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene
from graphene.types import generic
from graphql import GraphQLError
from odoo import _
from odoo.http import request

from odoo.addons.graphql_theaterpedia.schemas.objects import DomainUser


def get_search_order(sort):
    sorting = ''
    for field, val in sort.items():
        if sorting:
            sorting += ', '
        sorting += '%s %s' % (field, val.value)

    if not sorting:
        sorting = 'sequence ASC, id ASC'

    return sorting


class DomainUsers(graphene.Interface):
    domainusers = graphene.List(DomainUser)
    total_count = graphene.Int(required=True)


class DomainUserList(graphene.ObjectType):
    class Meta:
        interfaces = (DomainUsers,)


class AddDomainUserInput(graphene.InputObjectType):
    domain_id = graphene.Int(required=True)
    user_id = graphene.Int(required=True)
    role = graphene.String(required=True)
    title = graphene.String()
    description = graphene.String()
    active = graphene.Boolean()
    
    # Settings
    capabilities = graphene.String()
    custom_md = graphene.Boolean()
    content_options = graphene.String()
    
    # Header (domainuser-specific, not in options)
    header_type = graphene.String()
    header_size = graphene.String()
    cimg = graphene.String()
    
    # Body (only set if custom_md is true)
    md = graphene.String()
    
    # Format options sections (JSON objects)
    page_options = generic.GenericScalar()
    aside_options = generic.GenericScalar()
    header_options = generic.GenericScalar()
    footer_options = generic.GenericScalar()


class UpdateDomainUserInput(graphene.InputObjectType):
    id = graphene.Int(required=True, description="ID of the domain user to update.")
    version = graphene.Int(required=True, description="Current version for optimistic locking.")
    
    role = graphene.String()
    title = graphene.String()
    description = graphene.String()
    active = graphene.Boolean()
    
    # Settings
    capabilities = graphene.String()
    custom_md = graphene.Boolean()
    content_options = graphene.String()
    
    # Header (domainuser-specific)
    header_type = graphene.String()
    header_size = graphene.String()
    cimg = graphene.String()
    
    # Body (only set if custom_md is true)
    md = graphene.String()
    
    # Format options sections (JSON objects)
    page_options = generic.GenericScalar()
    aside_options = generic.GenericScalar()
    header_options = generic.GenericScalar()
    footer_options = generic.GenericScalar()


class AddDomainUser(graphene.Mutation):
    class Arguments:
        domain_user = AddDomainUserInput(required=True)

    Output = DomainUser

    @staticmethod
    def mutate(self, info, domain_user):
        env = info.context["env"]
        DomainUserModel = env['crearis.domainuser'].sudo()
        
        values = {
            'domain_id': domain_user['domain_id'],
            'user_id': domain_user['user_id'],
            'role': domain_user['role'],
        }
        
        # Optional basic fields
        if domain_user.get('title'):
            values['name'] = domain_user['title']
        if domain_user.get('description'):
            values['description'] = domain_user['description']
        if domain_user.get('active') is not None:
            values['active'] = domain_user['active']
        
        # Settings - computed fields
        if domain_user.get('capabilities'):
            values['capabilities'] = domain_user['capabilities']
        if domain_user.get('custom_md') is not None:
            values['custom_md'] = domain_user['custom_md']
        if domain_user.get('content_options'):
            values['content_options'] = domain_user['content_options']
        
        # Header fields (domainuser-specific)
        if domain_user.get('header_type'):
            values['header_type'] = domain_user['header_type']
        if domain_user.get('header_size'):
            values['header_size'] = domain_user['header_size']
        if domain_user.get('cimg'):
            values['cimg'] = domain_user['cimg']
        
        # Body (only if custom_md is true)
        if domain_user.get('custom_md') and domain_user.get('md'):
            values['md'] = domain_user['md']
        
        # Format options sections - set directly as JSON
        if domain_user.get('page_options'):
            values['page_options'] = domain_user['page_options']
        
        if domain_user.get('aside_options'):
            values['aside_options'] = domain_user['aside_options']
        
        if domain_user.get('header_options'):
            values['header_options'] = domain_user['header_options']
        
        if domain_user.get('footer_options'):
            values['footer_options'] = domain_user['footer_options']
        
        new_record = DomainUserModel.create(values)
        new_record.invalidate_recordset()
        
        return new_record


class UpdateDomainUser(graphene.Mutation):
    class Arguments:
        domain_user = UpdateDomainUserInput(required=True)

    Output = DomainUser

    @staticmethod
    def mutate(self, info, domain_user):
        env = info.context["env"]
        DomainUserModel = env['crearis.domainuser'].sudo()
        
        record = DomainUserModel.browse(domain_user['id'])
        
        if not record.exists():
            raise GraphQLError(_('Domain User not found.'))
        
        if record.version != domain_user['version']:
            raise GraphQLError(_('Version mismatch. Please refresh and try again.'))

        values = {}
        
        # Basic fields
        if domain_user.get('role'):
            values['role'] = domain_user['role']
        if domain_user.get('title'):
            values['name'] = domain_user['title']
        if domain_user.get('description') is not None:
            values['description'] = domain_user['description']
        if domain_user.get('active') is not None:
            values['active'] = domain_user['active']
        
        # Settings - computed fields
        if domain_user.get('capabilities') is not None:
            values['capabilities'] = domain_user['capabilities']
        if domain_user.get('custom_md') is not None:
            values['custom_md'] = domain_user['custom_md']
        if domain_user.get('content_options') is not None:
            values['content_options'] = domain_user['content_options']
        
        # Header fields (domainuser-specific)
        if domain_user.get('header_type') is not None:
            values['header_type'] = domain_user['header_type']
        if domain_user.get('header_size') is not None:
            values['header_size'] = domain_user['header_size']
        if domain_user.get('cimg') is not None:
            values['cimg'] = domain_user['cimg']
        
        # Body
        if domain_user.get('md') is not None:
            values['md'] = domain_user['md']
        
        # Format options sections - set directly as JSON
        # Use False to clear, or a dict to set/update
        if 'page_options' in domain_user:
            values['page_options'] = domain_user['page_options'] if domain_user['page_options'] else False
        
        if 'aside_options' in domain_user:
            values['aside_options'] = domain_user['aside_options'] if domain_user['aside_options'] else False
        
        if 'header_options' in domain_user:
            values['header_options'] = domain_user['header_options'] if domain_user['header_options'] else False
        
        if 'footer_options' in domain_user:
            values['footer_options'] = domain_user['footer_options'] if domain_user['footer_options'] else False

        if values:
            record.write(values)
            record.invalidate_recordset()
            record = DomainUserModel.browse(record.id)

        return record


class DeleteDomainUserInput(graphene.InputObjectType):
    id = graphene.Int(required=True, description="ID of the domain user to delete.")


class DeleteDomainUser(graphene.Mutation):
    class Arguments:
        domain_user = DeleteDomainUserInput(required=True)

    ok = graphene.Boolean()

    @staticmethod
    def mutate(self, info, domain_user):
        env = info.context["env"]
        DomainUserModel = env['crearis.domainuser'].sudo()
        
        record = DomainUserModel.browse(domain_user['id'])
        
        if not record.exists():
            raise GraphQLError(_('Domain User not found.'))
        
        record.unlink()
        
        return DeleteDomainUser(ok=True)


class DomainUserQuery(graphene.ObjectType):
    domainuser = graphene.Field(
        DomainUser,
        id=graphene.Int(),
        cid=graphene.String(),
    )
    domainusers = graphene.Field(
        DomainUsers,
        current_page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=20),
        domain_id=graphene.Int(),
        role=graphene.String(),
        active=graphene.Boolean(),
    )

    @staticmethod
    def resolve_domainuser(self, info, id=None, cid=None):
        env = info.context['env']
        DomainUserModel = env['crearis.domainuser'].sudo()

        if id:
            domainuser = DomainUserModel.search([('id', '=', id)], limit=1)
        elif cid:
            domainuser = DomainUserModel.search([('cid', '=', cid)], limit=1)
        else:
            domainuser = DomainUserModel

        if domainuser and hasattr(domainuser, 'can_access_from_current_website'):
            if not domainuser.can_access_from_current_website():
                website = env['website'].get_current_website()
                request.website = website
                if not domainuser.can_access_from_current_website():
                    domainuser = DomainUserModel

        return domainuser

    @staticmethod
    def resolve_domainusers(self, info, current_page, page_size, domain_id=None, role=None, active=None):
        env = info.context["env"]
        DomainUserModel = env['crearis.domainuser'].sudo()

        # Build domain
        domain = []
        
        if domain_id:
            domain.append(('domain_id', '=', domain_id))
        else:
            # Default to current website
            website = env['website'].get_current_website()
            if website:
                domain.append(('domain_id', '=', website.id))
        
        if role:
            domain.append(('role', '=', role))
        
        if active is not None:
            domain.append(('active', '=', active))

        # Calculate offset
        if current_page > 1:
            offset = (current_page - 1) * page_size
        else:
            offset = 0

        # Get records
        domainusers = DomainUserModel.search(domain, limit=page_size, offset=offset, order='role, user_id')
        total_count = DomainUserModel.search_count(domain)

        return DomainUserList(domainusers=domainusers, total_count=total_count)


class DomainUserMutation(graphene.ObjectType):
    add_domain_user = AddDomainUser.Field(description="Create a new domain user")
    update_domain_user = UpdateDomainUser.Field(description="Update an existing domain user")
    delete_domain_user = DeleteDomainUser.Field(description="Delete a domain user")
