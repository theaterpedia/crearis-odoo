# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org + ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene
from odoo.http import request

from odoo.addons.graphql_theaterpedia.schemas.objects import (
    Blog
)

def get_search_order(sort):
    sorting = ''
    for field, val in sort.items():
        if sorting:
            sorting += ', '
        sorting += '%s %s' % (field, val.value)

    if not sorting:
        sorting = 'sequence ASC, id ASC'

    return sorting

class Blogs(graphene.Interface):
    blogs = graphene.List(Blog)
    total_count = graphene.Int(required=True)


class BlogList(graphene.ObjectType):
    class Meta:
        interfaces = (Blogs,)


class BlogQuery(graphene.ObjectType):
    blog = graphene.Field(
        Blog,
        id=graphene.Int(),
        # slug=graphene.String(default_value=None),
    )
    blogs = graphene.Field(
        Blogs,
        current_page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=20),
        # search=graphene.String(default_value=False),
    )

    @staticmethod
    def resolve_blog(self, info, id=None, slug=None):
        env = info.context['env']
        Blog = env['blog.blog'].sudo()

        if id:
            blog = Blog.search([('id', '=', id)], limit=1)
        # elif slug:
        #    blog = Blog.search([('website_slug', '=', slug)], limit=1)
        else:
            blog = Blog

        if blog:
            website = env['website'].get_current_website()
            request.website = website
            if not blog.can_access_from_current_website():
                blog = Blog

        return blog             

    @staticmethod
    def resolve_blogs(self, info, current_page, page_size, search):
        env = info.context["env"]
        domain = env['website'].get_current_website().website_domain()

        if search:
            for srch in search.split(" "):
                domain += [('name', 'ilike', srch)]

        # First offset is 0 but first page is 1
        if current_page > 1:
            offset = (current_page - 1) * page_size
        else:
            offset = 0

        blogs = Blogs.search(
            domain, limit=page_size, offset=offset)
        return BlogList(blogs=blogs, total_count=10)
