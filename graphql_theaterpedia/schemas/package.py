# -*- coding: utf-8 -*-
# Copyright 2026 theaterpedia.org / crearis.io
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
"""
GraphQL queries for DASEi event packages.

Provides:
- eventPackages: List products with detailed_type='event_package'
- eventsByPackage: Events for a specific package's event types
- agendaLines: Agenda lines with optional filters
"""

import graphene
from graphql import GraphQLError
from odoo.http import request
from odoo import _

from odoo.addons.graphql_theaterpedia.schemas.objects import (
    Product, Event, EventType, AgendaLine
)


class EventPackages(graphene.ObjectType):
    """Result type for eventPackages query"""
    packages = graphene.List(Product)
    total_count = graphene.Int()


class EventsByPackage(graphene.ObjectType):
    """Result type for eventsByPackage query"""
    events = graphene.List(Event)
    total_count = graphene.Int()


class AgendaLines(graphene.ObjectType):
    """Result type for agendaLines query"""
    lines = graphene.List(AgendaLine)
    total_count = graphene.Int()


class PackageQuery(graphene.ObjectType):
    """GraphQL queries for DASEi packages and agenda lines"""
    
    event_packages = graphene.Field(
        EventPackages,
        domain_code=graphene.String(description="Filter by domain code (dasei1, dasei2)"),
        published=graphene.Boolean(default_value=True),
    )
    
    events_by_package = graphene.Field(
        EventsByPackage,
        package_id=graphene.Int(required=True, description="Product template ID"),
        include_past=graphene.Boolean(default_value=False),
    )
    
    event_types_by_package = graphene.List(
        EventType,
        package_id=graphene.Int(required=True, description="Product template ID"),
    )
    
    agenda_lines = graphene.Field(
        AgendaLines,
        event_id=graphene.Int(description="Filter by event ID"),
        event_type_id=graphene.Int(description="Filter by event type ID"),
        line_type=graphene.String(default_value="session", description="session, meeting, milestone, info, action"),
        page_size=graphene.Int(default_value=50),
        current_page=graphene.Int(default_value=1),
    )

    @staticmethod
    def resolve_event_packages(self, info, domain_code=None, published=True):
        """
        List event packages (products with detailed_type='event_package').
        
        Query example:
            eventPackages(domainCode: "dasei1") {
                packages { id name packageEditionCode packageEventTypes { id name } }
                totalCount
            }
        """
        env = info.context['env']
        Product = env['product.template'].sudo()
        
        domain = [('detailed_type', '=', 'event_package')]
        
        if published:
            domain.append(('website_published', '=', True))
        
        # Filter by domain_code if provided
        # This requires the product to have events with matching domain
        # For now, we'll rely on manual categorization or add domain_code to product
        
        packages = Product.search(domain, order='name asc')
        
        return EventPackages(
            packages=packages,
            total_count=len(packages)
        )

    @staticmethod
    def resolve_events_by_package(self, info, package_id, include_past=False):
        """
        Get events for a specific package's event types.
        
        Query example:
            eventsByPackage(packageId: 123) {
                events { id name dateBegin eventType { name } agendaLines { date start end } }
                totalCount
            }
        """
        env = info.context['env']
        Product = env['product.template'].sudo()
        EventEvent = env['event.event'].sudo()
        
        # Find the package
        package = Product.browse(package_id)
        if not package.exists() or package.detailed_type != 'event_package':
            raise GraphQLError(_('Package not found: %s') % package_id)
        
        # Get event type IDs from package
        event_type_ids = package.package_event_type_ids.ids
        if not event_type_ids:
            return EventsByPackage(events=[], total_count=0)
        
        # Build domain for events
        domain = [('event_type_id', 'in', event_type_ids)]
        
        # Filter by package date range if set
        if package.package_date_start:
            domain.append(('date_begin', '>=', package.package_date_start))
        if package.package_date_end:
            domain.append(('date_end', '<=', package.package_date_end))
        
        # Exclude past events unless requested
        if not include_past:
            from datetime import datetime
            domain.append(('date_end', '>=', datetime.now()))
        
        # Exclude cancelled stages
        domain.append(('stage_id.pipe_end', '=', False))
        
        events = EventEvent.search(domain, order='date_begin asc')
        
        return EventsByPackage(
            events=events,
            total_count=len(events)
        )

    @staticmethod
    def resolve_event_types_by_package(self, info, package_id):
        """
        Get event types included in a package.
        
        Query example:
            eventTypesByPackage(packageId: 123) { id name isTemplateCode }
        """
        env = info.context['env']
        Product = env['product.template'].sudo()
        
        package = Product.browse(package_id)
        if not package.exists() or package.detailed_type != 'event_package':
            raise GraphQLError(_('Package not found: %s') % package_id)
        
        return package.package_event_type_ids

    @staticmethod
    def resolve_agenda_lines(self, info, event_id=None, event_type_id=None, 
                             line_type='session', page_size=50, current_page=1):
        """
        Query agenda lines with optional filters.
        
        Query example:
            agendaLines(eventId: 1185, lineType: "session") {
                lines { id date day start end mode locationHint gateState }
                totalCount
            }
        """
        env = info.context['env']
        AgendaLineModel = env['agenda.line'].sudo()
        
        domain = []
        
        if event_id:
            domain.append(('event_id', '=', event_id))
        if event_type_id:
            domain.append(('event_type_id', '=', event_type_id))
        if line_type:
            domain.append(('type', '=', line_type))
        
        # Pagination
        offset = (current_page - 1) * page_size if current_page > 1 else 0
        
        total = AgendaLineModel.search_count(domain)
        lines = AgendaLineModel.search(
            domain, 
            order='date asc, sequence asc',
            limit=page_size,
            offset=offset
        )
        
        return AgendaLines(
            lines=lines,
            total_count=total
        )
