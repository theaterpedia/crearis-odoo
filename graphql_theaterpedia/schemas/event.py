# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene
from graphene.types.generic import GenericScalar
from graphql import GraphQLError
from odoo.http import request
from odoo import _
from odoo.osv import expression

from odoo.addons.graphql_theaterpedia.schemas.objects import (
    SortEnum, Event, EventStage, EventType, EventEditMode
)

def get_event(env, event_cid):
    Event = env['event.event'].with_context().sudo()
    event = Event.search([('cid', '=', event_cid)], limit=1)

    if not event or not event.exists():
        raise GraphQLError(_('Event not found.'))
    
    return event

def get_search_order(sort):
    sorting = ''
    for field, val in sort.items():
        if sorting:
            sorting += ', '
        if field == 'date':
            sorting += 'date_begin %s' % val.value
        if field == 'stage':
            sorting += 'stage_id %s' % val.value            
        else:
            sorting += '%s %s' % (field, val.value)

    if sorting:
        sorting += ', id ASC'
    else:
        sorting = 'date_begin ASC, id ASC'

    return sorting

def get_search_domain(env, search, **kwargs):
    domains = []
    
    if kwargs.get('homesite_only', False):
        if kwargs['homesite_only']:
            domains.append(env['website'].get_current_website().website_domain())

    if kwargs.get('ids', False):
        domains.append([('id', 'in', kwargs['ids'])])

    if kwargs.get('published', False):
        domains.append([('is_published', '=', kwargs['published'])])

    if kwargs.get('event_type', False):
        domains.append([('event_type_id', '=', kwargs['event_type'])])

    if kwargs.get('address_ids', False):
        address_ids = [address for address in kwargs.get['address_ids']]
        domains.append([('address_id', 'in', address_ids)])        

    if kwargs.get('stages', False):
        stages = [stage.id for stage in kwargs.get['stages']]
        domains.append([('stage_id', 'in', stages)])
    else:
        domains.append([('stage_id', 'in', [2, 3])])

    if kwargs.get('name', False):
        name = kwargs['name']
        for n in name.split(" "):
            domains.append([('name', 'ilike', n)])

    if search:
        for srch in search.split(" "):
            domains.append([
                '|', '|', ('name', 'ilike', srch), ('subtitle', 'like', srch), ('description', 'like', srch)])

    return expression.AND(domains)

def get_event_list(env, current_page, page_size, search, sort, **kwargs):
    Event = env['event.event'].sudo()
    domain = get_search_domain(env, search, **kwargs)

    if current_page > 1:
        offset = (current_page - 1) * page_size
    else:
        offset = 0
    order = get_search_order(sort)
    events = Event.search(domain, order=order)

    dates = events.mapped('date_begin')

    total_count = len(events)
    events = events[offset:offset + page_size]
    if dates:
        return events, total_count, min(dates), max(dates)
    return events, total_count, "no min date", "no max date"

class Events(graphene.Interface):
    events = graphene.List(Event)
    total_count = graphene.Int(required=True)
    min_date = graphene.String()
    max_date = graphene.String()


class EventList(graphene.ObjectType):
    class Meta:
        interfaces = (Events,)

class EventSortInput(graphene.InputObjectType):
    id = SortEnum()
    name = SortEnum()
    date = SortEnum()
    stage = SortEnum()

class EventFilterInput(graphene.InputObjectType):
    ids = graphene.List(graphene.Int)
    published = graphene.Boolean()
    homesite_only = graphene.Boolean()
    event_type = graphene.Int()
    edit_mode = graphene.List(EventEditMode)
    address_id = graphene.List(graphene.Int)
    stages = graphene.List(graphene.Int)
    name = graphene.String()
    min_date = graphene.String()
    max_date = graphene.String()

class EventQuery(graphene.ObjectType):
    event = graphene.Field(
        Event,
        id=graphene.Int(default_value=None),
        slug=graphene.String(default_value=None),
        barcode=graphene.String(default_value=None),
    )
    events = graphene.Field(
        Events,
        filter=graphene.Argument(EventFilterInput, default_value={}),
        current_page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=20),
        search=graphene.String(default_value=False),
        sort=graphene.Argument(EventSortInput, default_value={})
    )

    @staticmethod
    def resolve_event(self, info, id=None, slug=None, barcode=None):
        env = info.context["env"]
        Event = env["event.event"].sudo()

        if id:
            event = Event.search([('id', '=', id)], limit=1)
        elif slug:  
            raise GraphQLError(_('Filter event.slug not yet implemented.'))
        elif barcode:
            event = Event.search([('barcode', '=', barcode)], limit=1)
        else:
            event = Event

        if event:
            website = env['website'].get_current_website()
            request.website = website
            if not event.can_access_from_current_website():
                event = Event

        return event

    @staticmethod
    def resolve_events(self, info, filter, current_page, page_size, search, sort):
        env = info.context["env"]
        events, total_count, min_date, max_date = get_event_list(
            env, current_page, page_size, search, sort, **filter)
        return EventList(events=events, total_count=total_count, min_date=min_date, max_date=max_date)          

class UpdateEventInput(graphene.InputObjectType):
    cid = graphene.String(required=True, description="Crearis ID of the event to update.")
    version = graphene.Int(required=True, description="Current version for optimistic locking.")
    
    heading = graphene.String()
    teasertext = graphene.String()
    description = graphene.String()
    
    # Header (event-specific)
    header_type = graphene.String()
    header_size = graphene.String()
    cimg = graphene.String()
    
    # Body
    md = graphene.String()
    blocks = GenericScalar()
    
    # Format options sections (JSON objects)
    page_options = GenericScalar()
    aside_options = GenericScalar()
    header_options = GenericScalar()
    footer_options = GenericScalar()
    
    note = graphene.String()
    meta_title = graphene.String()
    meta_keywords = graphene.String()
    meta_description = graphene.String()

class UpdateEvent(graphene.Mutation):
    class Arguments:
        event = UpdateEventInput(required=True)

    Output = Event

    @staticmethod
    def mutate(self, info, event):
        env = info.context["env"]
        EventEvent = get_event(env, event['cid'])

        if EventEvent.version != event['version']:
            raise GraphQLError(_('Event version mismatch. Please refresh the event and try again.'))

        if not EventEvent.check_access_rights('write'):
            raise GraphQLError(_('You do not have permission to update this event.'))

        values = {}

        # Basic fields
        if event.get('heading'):
            values['name'] = event['heading']
        if event.get('note'):
            values['note'] = event['note']
        if event.get('teasertext'):
            values['teasertext'] = event['teasertext']
        if event.get('description'):
            values['description'] = event['description']
        if event.get('blocks'):
            values['blocks'] = event['blocks']
        
        # Header fields (event-specific)
        if event.get('header_type') is not None:
            values['header_type'] = event['header_type']
        if event.get('header_size') is not None:
            values['header_size'] = event['header_size']
        if event.get('cimg') is not None:
            values['cimg'] = event['cimg']
        
        # Body
        if event.get('md') is not None:
            values['md'] = event['md']
        
        # Format options sections - set directly as JSON
        # Use False to clear, or a dict to set/update
        if 'page_options' in event:
            values['page_options'] = event['page_options'] if event['page_options'] else False
        
        if 'aside_options' in event:
            values['aside_options'] = event['aside_options'] if event['aside_options'] else False
        
        if 'header_options' in event:
            values['header_options'] = event['header_options'] if event['header_options'] else False
        
        if 'footer_options' in event:
            values['footer_options'] = event['footer_options'] if event['footer_options'] else False
        
        # Meta fields
        if event.get('meta_title'):
            values['website_meta_title'] = event['meta_title']            
        if event.get('meta_keywords'):
            values['website_meta_keywords'] = event['meta_keywords']               
        if event.get('meta_description'):
            values['website_meta_description'] = event['meta_description']

        if values:
            EventEvent.write(values)
            EventEvent.invalidate_recordset()
            EventEvent = EventEvent.browse(EventEvent.id)            

        return EventEvent
    
class EventMutation(graphene.ObjectType):
    update_event = UpdateEvent.Field(description="Update event content.")