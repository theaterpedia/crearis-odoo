# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import os
import json
import logging
import pprint

from odoo import http
from odoo.addons.web.controllers.binary import Binary
from odoo.addons.graphql_base import GraphQLControllerMixin
from odoo.http import request, Response
from odoo.tools.safe_eval import safe_eval
from urllib.parse import urlparse

from ..schema import schema

_logger = logging.getLogger(__name__)


class VSFBinary(Binary):
    @http.route(['/web/image',
                 '/web/image/<string:xmlid>',
                 '/web/image/<string:xmlid>/<string:filename>',
                 '/web/image/<string:xmlid>/<int:width>x<int:height>',
                 '/web/image/<string:xmlid>/<int:width>x<int:height>/<string:filename>',
                 '/web/image/<string:model>/<int:id>/<string:field>',
                 '/web/image/<string:model>/<int:id>/<string:field>/<string:filename>',
                 '/web/image/<string:model>/<int:id>/<string:field>/<int:width>x<int:height>',
                 '/web/image/<string:model>/<int:id>/<string:field>/<int:width>x<int:height>/<string:filename>',
                 '/web/image/<int:id>',
                 '/web/image/<int:id>/<string:filename>',
                 '/web/image/<int:id>/<int:width>x<int:height>',
                 '/web/image/<int:id>/<int:width>x<int:height>/<string:filename>',
                 '/web/image/<int:id>-<string:unique>',
                 '/web/image/<int:id>-<string:unique>/<string:filename>',
                 '/web/image/<int:id>-<string:unique>/<int:width>x<int:height>',
                 '/web/image/<int:id>-<string:unique>/<int:width>x<int:height>/<string:filename>'], type='http',
                auth="public")
    def content_image(self, xmlid=None, model='ir.attachment', id=None, field='raw',
                      filename_field='name', filename=None, mimetype=None, unique=False,
                      download=False, width=0, height=0, crop=False, access_token=None,
                      nocache=False, **kwargs):
        """ Validate width and height, then serve image """
        from odoo.exceptions import UserError
        from odoo.addons.web.controllers.binary import image_guess_size_from_field_name
        from odoo.tools.misc import str2bool
        
        try:
            ICP = request.env['ir.config_parameter'].sudo()
            vsf_image_resize_limit = int(ICP.get_param('vsf_image_resize_limit', 1920))
            
            if int(width) > vsf_image_resize_limit or int(height) > vsf_image_resize_limit:
                return request.not_found()
        except Exception:
            return request.not_found()

        # Sanitize download parameter
        if download and download not in (True, False, '0', '1', 'yes', 'no', 'true', 'false', 'on', 'off'):
            download = False
        
        try:
            record = request.env['ir.binary']._find_record(xmlid, model, id and int(id), access_token)
            stream = request.env['ir.binary']._get_image_stream_from(
                record, field, filename=filename, filename_field=filename_field,
                mimetype=mimetype, width=int(width), height=int(height), crop=crop,
            )
            if request.httprequest.args.get('access_token'):
                stream.public = True
        except UserError as exc:
            if download:
                raise request.not_found() from exc
            if (int(width), int(height)) == (0, 0):
                width, height = image_guess_size_from_field_name(field)
            record = request.env.ref('web.image_placeholder').sudo()
            stream = request.env['ir.binary']._get_image_stream_from(
                record, 'raw', width=int(width), height=int(height), crop=crop,
            )
            stream.public = False

        send_file_kwargs = {'as_attachment': str2bool(download) if download else False}
        if unique:
            send_file_kwargs['immutable'] = True
            send_file_kwargs['max_age'] = http.STATIC_CACHE_LONG
        if nocache:
            send_file_kwargs['max_age'] = None

        return stream.get_response(**send_file_kwargs)


class GraphQLController(http.Controller, GraphQLControllerMixin):

    def _process_request(self, schema, data):
        # Set the vsf_debug_mode value that exist in the settings
        ICP = http.request.env['ir.config_parameter'].sudo()
        vsf_debug_mode = ICP.get_param('vsf_debug_mode', False)
        if vsf_debug_mode:
            try:
                request = http.request.httprequest
                _logger.info('# ------------------------------- GRAPHQL: DEBUG MODE -------------------------------- #')
                _logger.info('')
                _logger.info('# ------------------------------------------------------- #')
                _logger.info('#                          HEADERS                        #')
                _logger.info('# ------------------------------------------------------- #')
                _logger.info('\n%s', pprint.pformat(request.headers.environ))
                _logger.info('')
                _logger.info('# ------------------------------------------------------- #')
                _logger.info('#                     QUERY / MUTATION                    #')
                _logger.info('# ------------------------------------------------------- #')
                _logger.info('\n%s', data.get('query', None))
                _logger.info('')
                _logger.info('# ------------------------------------------------------- #')
                _logger.info('#                         ARGUMENTS                       #')
                _logger.info('# ------------------------------------------------------- #')
                _logger.info('\n%s', request.args.get('variables', None))
                _logger.info('')
                _logger.info('# ------------------------------------------------------------------------------------ #')
            except:
                pass
        return super(GraphQLController, self)._process_request(schema, data)

    def _set_website_context(self):
        """Set website context based on http_request_host header."""
        try:
            request_host = request.httprequest.headers.environ['HTTP_RESQUEST_HOST']
            website = request.env['website'].search([('domain', 'ilike', request_host)], limit=1)
            if website:
                context = dict(request.context)
                context.update({
                    'website_id': website.id,
                    'lang': website.default_lang_id.code,
                })
                request.context = context

                request_uid = http.request.env.uid
                website_uid = website.sudo().user_id.id

                if request_uid != website_uid \
                        and request.env['res.users'].sudo().browse(request_uid).has_group('base.group_public'):
                    request.uid = website_uid
        except:
            pass

    # The GraphiQL route, providing an IDE for developers
    @http.route("/graphiql/vsf", auth="user")
    def graphiql(self, **kwargs):
        self._set_website_context()
        return self._handle_graphiql_request(schema.graphql_schema)

    # The graphql route, for applications.
    # Note csrf=False: you may want to apply extra security
    # (such as origin restrictions) to this route.
    @http.route("/graphql/vsf", auth="public", csrf=False)
    def graphql(self, **kwargs):
        self._set_website_context()
        return self._handle_graphql_request(schema.graphql_schema)

    @http.route('/vsf/categories', type='http', auth='public', csrf=False)
    def vsf_categories(self):
        self._set_website_context()
        website = request.env['website'].get_current_website()

        categories = []

        if website.default_lang_id:
            lang_code = website.default_lang_id.code
            domain = [('website_slug', '!=', False)]

            for category in request.env['product.public.category'].sudo().search(domain):
                category = category.with_context(lang=lang_code)
                categories.append(category.website_slug)

        return Response(
            json.dumps(categories),
            headers={'Content-Type': 'application/json'},
        )
    
    @http.route('/vsf/posts', type='http', auth='public', csrf=False)
    def vsf_posts(self):
        self._set_website_context()

        posts = []
        for post in request.env['blog.post'].sudo():
            posts.append(post.id)

        return Response(
            json.dumps(posts),
            headers={'Content-Type': 'application/json'},
        )

    @http.route('/vsf/products', type='http', auth='public', csrf=False)
    def vsf_products(self):
        self._set_website_context()
        website = request.env['website'].get_current_website()

        products = []

        if website.default_lang_id:
            lang_code = website.default_lang_id.code
            domain = [('website_published', '=', True), ('website_slug', '!=', False)]

            for product in request.env['product.template'].sudo().search(domain):
                product = product.with_context(lang=lang_code)

                url_parsed = urlparse(product.website_slug)
                name = os.path.basename(url_parsed.path)
                path = product.website_slug.replace(name, '')

                products.append({
                    'name': name,
                    'path': '{}:slug'.format(path),
                })

        return Response(
            json.dumps(products),
            headers={'Content-Type': 'application/json'},
        )

    @http.route('/vsf/redirects', type='http', auth='public', csrf=False)
    def vsf_redirects(self):
        redirects = []

        for redirect in request.env['website.rewrite'].sudo().search([]):
            redirects.append({
                'from': redirect.url_from,
                'to': redirect.url_to,
            })

        return Response(
            json.dumps(redirects),
            headers={'Content-Type': 'application/json'},
        )
