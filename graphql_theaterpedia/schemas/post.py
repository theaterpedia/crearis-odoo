# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org + ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene
from graphene.types.generic import GenericScalar
from odoo.http import request
from graphql import GraphQLError
from odoo import _
from odoo.addons.graphql_theaterpedia.schemas.objects import (
    SortEnum, Post, Blog
)

def get_post(env, cid):
    BlogPost = env['blog.post'].with_context().sudo()
    post = BlogPost.search([('cid', '=', cid)], limit=1)

    #TODO _07 check_access_rights('read') for post
    # Validate if the blog-post exists and if the user has access to this address
    if not post or not post.exists():
        raise GraphQLError(_('BlogPost not found.'))

    return post

def get_search_order(sort):
    sorting = ''
    for field, val in sort.items():
        if sorting:
            sorting += ', '
        sorting += '%s %s' % (field, val.value)

    return sorting
    
class PostFilterInput(graphene.InputObjectType):
    blogs = graphene.List(graphene.Int)
    is_published = graphene.Boolean()

class Posts(graphene.Interface):
    posts = graphene.List(Post)
    total_count = graphene.Int(required=True)

class PostSortInput(graphene.InputObjectType):
    id = SortEnum()

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
        page_size=graphene.Int(default_value=10),
        search=graphene.String(default_value=False),
        sort=graphene.Argument(PostSortInput, default_value={})        
    )

    @staticmethod
    def resolve_post(self, info, cid=None, slug=None):
        env = info.context['env']
        Post = env['blog.post'].sudo()

        if cid:
            post = Post.search([('cid', '=', cid)], limit=1)
        elif slug:
            post = Post.search([('website_slug', '=', slug)], limit=1)
        else:
            post = Post

        if post:
            website = env['website'].get_current_website()
            request.website = website
            if not post.can_access_from_current_website():
                post = Post

        return post             

    @staticmethod
    def resolve_posts(self, info, filter, current_page, page_size, sort, search):
        env = info.context["env"]
        domain = [] # env['website'].get_current_website().website_domain()
        order = get_search_order(sort)

        website = env['website'].get_current_website()

        if not website.is_hubsite:
            website_ids = [website_id for website_id in website.post_domain_ids.ids]
            # add the local website-id
            website_ids.append(website.id)
            print('domainCode:', website.domain_code, ' | website_ids:', website_ids, ' | is_hubsite:', website.is_hubsite)
            domain += [('website_id', 'in', website_ids)]

        # Filter by blogs or default to all
        if filter.get('blogs', False):
            blog_ids = [blog_id for blog_id in filter['blogs']]
            domain += [('blog_id', 'in', blog_ids)]

        # Filter by is_published
        if filter.get('is_published', False):
            domain += [('is_published', '=', 'true')]

        if search:
            for srch in search.split(" "):
                domain += [('name', 'ilike', srch)]

        # First offset is 0 but first page is 1
        if current_page > 1:
            offset = (current_page - 1) * page_size
        else:
            offset = 0

        BlogPosts = env["blog.post"]
        total_count = BlogPosts.search_count(domain)
        posts = BlogPosts.search(
            domain, limit=page_size, offset=offset, order=order)
        return PostList(posts=posts, total_count=total_count)
    
class AddBlogPostInput(graphene.InputObjectType):
    heading = graphene.String(required=True)
    """ partner-id """
    author_id = graphene.Int(required=True)
    blog_id = graphene.Int(required=True)
    teasertext = graphene.String()
    blocks = GenericScalar()
    md = graphene.String()
    public = graphene.Boolean()
    publish_date = graphene.Date() 
    # meta_title = graphene.String()
    meta_keywords = graphene.String()
    meta_description = graphene.String()    

class UpdatePostInput(graphene.InputObjectType):
    cid = graphene.String(required=True, description="Crearis ID of the event to update.")
    version = graphene.Int(required=True, description="old Version of the event to update.")
    heading = graphene.String()
    """ partner-id """
    author_id = graphene.Int()
    teasertext = graphene.String()
    blocks = GenericScalar()
    md = graphene.String()
    public = graphene.Boolean()
    publish_date = graphene.Date()
    # meta_title = graphene.String()
    meta_keywords = graphene.String()
    meta_description = graphene.String()

class AddPost(graphene.Mutation):
    class Arguments:
        post = AddBlogPostInput()

    Output = Post

    @staticmethod
    def mutate(self, info, post):
        env = info.context["env"]
        BlogPost = env['blog.post'].sudo().with_context(tracking_disable=True)

        values = {
            'name': post.get('heading'),
            'author_id': post.get('author_id'),
            'blog_id': post.get('blog_id'),
            'description': post.get('teasertext'),
            'blocks': post.get('blocks'),
            'is_published': post.get('public'),
            'published_date': post.get('publish_date'),
            'md': post.get('md'),
            'website_meta_keywords': post.get('meta_keywords'),
            'website_meta_description': post.get('meta_description'),               
        }
        #             'website_meta_title': post.get('meta_title'),

        # Create post entry
        post = BlogPost.create(values)

        # Invalidate cache to ensure fresh reads
        new_post.invalidate_cache()
        new_post = BlogPost.browse(new_post.id)        

        return post
    
class UpdatePost(graphene.Mutation):
    class Arguments:
        post = UpdatePostInput(required=True)

    Output = Post

    @staticmethod
    def mutate(self, info, post):
        env = info.context["env"]
        BlogPost = get_post(env, post['cid'])
        # print the current version
        # print("Current Blog Post Version:", BlogPost.version)
        # print the cid
        # print("Current Blog Post CID:", BlogPost.cid)

        if BlogPost.version != post['version']:
            raise GraphQLError(_('Blog post version mismatch. Please refresh the blog post and try again.'))

        values = {
            'name': post.get('heading'),
            # 'author_id': post.get('author_id'),
            'description': post.get('teasertext'),
            'blocks': post.get('blocks'),
            'is_published': post.get('public'),
            'published_date': post.get('publish_date'),
            'md': post.get('md'),
            'website_meta_keywords': post.get('meta_keywords'),
            'website_meta_description': post.get('meta_description'),            
        }
        #             'website_meta_title': post.get('meta_title'),

        if post.get('heading'):
            values.update({'name': post['heading']})
        # if post.get('author_id'):
        #    values.update({'author_id': post['author_id']})
        if post.get('teasertext'):
            values.update({'description': post['teasertext']})
        if post.get('blocks'):
            values.update({'blocks': post['blocks']})
        if post.get('public'):
            values.update({'is_published': post['public']})
        if post.get('publish_date'):
            values.update({'published_date': post['publish_date']})
        if post.get('md'):
            values.update({'md': post['md']})
        if post.get('meta_title'):
            values.update({'website_meta_title': post['meta_title']})            
        if post.get('meta_keywords'):
            values.update({'website_meta_keywords': post['meta_keywords']})               
        if post.get('meta_description'):
            values.update({'website_meta_description': post['meta_description']})                 

        if values:
            BlogPost.write(values)

            # Invalidate cache to ensure fresh reads
            BlogPost.invalidate_cache()
            BlogPost = BlogPost.browse(BlogPost.id)            

        # print the updated blogPost: Version, subtitle
        # print("Updated Blog Post Version:", BlogPost.version)
        # print("Updated Blog Post Subtitle:", BlogPost.subtitle)

        return BlogPost
    
class BlogPostMutation(graphene.ObjectType):
    add_post = AddPost.Field(description='Add new blogpost and make it active.')
    update_post = UpdatePost.Field(description="Update a blogpost and make it active.")
