# -*- coding: utf-8 -*-
# Monkey-patches Register.mutate + ChangePassword.mutate in graphql_theaterpedia
# to add the missing request.session.authenticate() call so both mutations issue
# Set-Cookie on success (required for CV-side proxy-everything SSO flow).
#
# UpdatePassword.mutate already calls request.session.authenticate() upstream;
# no patch needed for that one.

import logging

import odoo
from graphql import GraphQLError
from odoo import _
from odoo.http import request
from odoo.addons.auth_signup.models.res_users import SignupError

from odoo.addons.graphql_theaterpedia.schemas import sign as _sign
from odoo.addons.website_mass_mailing.controllers.main import MassMailController

_logger = logging.getLogger(__name__)


# --- Patch: Register.mutate -------------------------------------------------
#
# Original (graphql_theaterpedia/schemas/sign.py:65-89):
#   - calls env['res.users'].sudo().signup(data)
#   - returns the user without session.authenticate()
#   - therefore NO Set-Cookie is issued
#
# Patched: same logic + auto-login at the end (immediately before return).

_orig_register_mutate = _sign.Register.mutate


def _register_mutate_with_autologin(self, info, name, email, password, subscribe_newsletter):
    env = info.context['env']
    website = env['website'].get_current_website()
    request.website = website

    email = email.lower()

    data = {
        'name': name,
        'login': email,
        'password': password,
    }

    if env['res.users'].sudo().search([('login', '=', data['login'])], limit=1):
        raise GraphQLError(_('Another user is already registered using this email address.'))

    env['res.users'].sudo().signup(data)

    # Subscribe Newsletter — preserve existing behavior
    if website and website.vsf_mailing_list_id and subscribe_newsletter:
        MassMailController().subscribe(website.vsf_mailing_list_id.id, email, 'email')

    user = env['res.users'].sudo().search([('login', '=', data['login'])], limit=1)

    # === PATCH: auto-login so Set-Cookie is issued ===
    try:
        request.session.authenticate(request.session.db, email, password)
    except odoo.exceptions.AccessDenied:
        # Auth failed immediately after signup — should be impossible;
        # surface as graphql error rather than silently returning unauthenticated user.
        raise GraphQLError(_('Auto-login after registration failed.'))

    return user


_sign.Register.mutate = staticmethod(_register_mutate_with_autologin)


# --- Patch: ChangePassword.mutate ------------------------------------------
#
# Original (graphql_theaterpedia/schemas/sign.py:131-149):
#   - calls ResUsers.signup(data, token) — validates token, sets new password
#   - returns the user without session.authenticate()
#   - therefore NO Set-Cookie is issued
#
# Patched: same logic + auto-login at the end.

_orig_change_password_mutate = _sign.ChangePassword.mutate


def _change_password_mutate_with_autologin(self, info, token, new_password):
    env = info.context['env']

    data = {
        'password': new_password,
    }

    ResUsers = env['res.users'].sudo()

    try:
        login, password = ResUsers.signup(data, token)
        user = ResUsers.search([('login', '=', login)], limit=1)

        # === PATCH: auto-login so Set-Cookie is issued ===
        try:
            request.session.authenticate(request.session.db, login, password)
        except odoo.exceptions.AccessDenied:
            raise GraphQLError(_('Auto-login after password change failed.'))

        return user
    except odoo.exceptions.UserError as e:
        raise GraphQLError(e.args[0])
    except SignupError:
        raise GraphQLError(_('Could not change your password.'))
    except GraphQLError:
        raise
    except Exception as e:
        raise GraphQLError(str(e))


_sign.ChangePassword.mutate = staticmethod(_change_password_mutate_with_autologin)


_logger.info(
    "crearis_auth_resolver_patches loaded: Register.mutate + ChangePassword.mutate now call "
    "request.session.authenticate() post-signup (Set-Cookie issued on success)"
)
