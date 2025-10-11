# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org + ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene

from odoo.addons.graphql_vuestorefront.schemas.objects import (
    SortEnum, Post
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


class PostFilterInput(graphene.InputObjectType):
    id = graphene.List(graphene.Int)
    parent = graphene.Boolean()


class PostSortInput(graphene.InputObjectType):
    id = SortEnum()


class Posts(graphene.Interface):
    posts = graphene.List(Post)
    total_count = graphene.Int(required=True)


class PostList(graphene.ObjectType):
    class Meta:
        interfaces = (Posts,)


class PostQuery(graphene.ObjectType):
    post = graphene.Field(
        Post,
        id=graphene.Int(),
        slug=graphene.String(default_value=None),
    )
    posts = graphene.Field(
        Posts,
        filter=graphene.Argument(PostFilterInput, default_value={}),
        current_page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=20),
        search=graphene.String(default_value=False),
        sort=graphene.Argument(PostSortInput, default_value={})
    )

    @staticmethod
    def resolve_post(self, info, id=None, slug=None):
        env = info.context['env']
        Post = env['blog.post']

        domain = env['website'].get_current_website().website_domain()

        if id:
            domain += [('id', '=', id)]
            category = Post.search(domain, limit=1)
        elif slug:
            domain += [('website_slug', '=', slug)]
            category = Post.search(domain, limit=1)
        else:
            category = Post

        return category

    @staticmethod
    def resolve_posts(self, info, filter, current_page, page_size, search, sort):
        env = info.context["env"]
        order = get_search_order(sort)
        domain = env['website'].get_current_website().website_domain()

        if search:
            for srch in search.split(" "):
                domain += [('name', 'ilike', srch)]

        if filter.get('id'):
            domain += [('id', 'in', filter['id'])]

        # Parent if is a Top Category
        if filter.get('parent'):
            domain += [('parent_id', '=', False)]

        # First offset is 0 but first page is 1
        if current_page > 1:
            offset = (current_page - 1) * page_size
        else:
            offset = 0

        posts = Posts.search(
            domain, limit=page_size, offset=offset, order=order)
        return PostList(posts=posts, total_count=10)
