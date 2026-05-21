# -*- coding: utf-8 -*-
# Routes password-reset email URL through an ICP-parameterized base
# (e.g. CV's /auth/reset) instead of the legacy /forgot-password/new-password.

import logging

from odoo.http import request
from odoo import models, _
from odoo.addons.auth_signup.models.res_partner import now
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

ICP_KEY = 'cv.password_reset_base_url'


class ResUsers(models.Model):
    _inherit = 'res.users'

    def api_action_reset_password(self):
        """Override of graphql_theaterpedia.res_users.api_action_reset_password
        to construct the reset URL from ICP 'cv.password_reset_base_url' when set.

        Reads the ICP at request-time. Empty ICP = no behavior change
        (continues to use website.domain + '/forgot-password/new-password').
        """
        cv_base_url = self.env['ir.config_parameter'].sudo().get_param(ICP_KEY, default='')
        if not cv_base_url:
            # No CV override — delegate to upstream graphql_theaterpedia implementation
            return super().api_action_reset_password()

        # CV-override path: use the ICP value as the URL base
        if self.filtered(lambda user: not user.active):
            raise UserError(_("You cannot perform this action on an archived user."))

        create_mode = bool(self.env.context.get('create_user'))
        expiration = False if create_mode else now(days=+1)
        self.mapped('partner_id').signup_prepare(signup_type="reset", expiration=expiration)

        template = self.env.ref('graphql_theaterpedia.website_reset_password_email')
        assert template._name == 'mail.template'

        email_values = {
            'email_cc': False,
            'auto_delete': True,
            'recipient_ids': [],
            'partner_ids': [],
            'scheduled_date': False,
        }

        for user in self:
            token = user.signup_token
            # CV-side URL: the ICP value is the full URL prefix (e.g.
            # 'https://my.theaterpedia.org/auth/reset'); we append '?token=<token>'.
            signup_url = '%s?token=%s' % (cv_base_url.rstrip('/'), token or '')
            if not user.email:
                raise UserError(_("Cannot send email: user %s has no email address.", user.name))
            email_values['email_to'] = user.email
            with self.env.cr.savepoint():
                force_send = not create_mode
                template.with_context(lang=user.lang, signup_url=signup_url).send_mail(
                    user.id, force_send=force_send, raise_exception=True, email_values=email_values)
            _logger.info(
                "Password reset email sent for user <%s> to <%s> · CV-routed via %s",
                user.login, user.email, ICP_KEY)
