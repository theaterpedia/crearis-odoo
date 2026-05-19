# -*- coding: utf-8 -*-
# Monkey-patch odoo.http to set Domain= on the session_id cookie.
#
# Driven by ir.config_parameter['session_cookie.domain'] (read at request
# time) with odoo.conf 'session_cookie_domain' as a boot-time fallback used
# when no environment is available (anonymous requests in the
# SessionExpiredException branch).
#
# Toggle semantics: empty value = no Domain = current Odoo behavior. Set to
# '.dasei.eu' to enable cross-subdomain cookies.

import logging

import odoo.http as _http
from odoo.tools import config

_logger = logging.getLogger(__name__)

ICP_KEY = 'session_cookie.domain'
CONF_KEY = 'session_cookie_domain'


def _request_env(request):
    """Best-effort env lookup; tolerates pre-auth / no-DB requests."""
    try:
        return request.env
    except Exception:
        return None


def _get_cookie_domain(env=None):
    """Resolve the Domain= value for session_id.

    Order: ir.config_parameter (when env available) → odoo.conf → ''.
    Empty string means "do not set the Domain attribute" — current
    Odoo behavior, current cookie semantics preserved.
    """
    if env is not None:
        try:
            value = env['ir.config_parameter'].sudo().get_param(ICP_KEY, default='')
            if value:
                return value.strip()
        except Exception:
            _logger.exception("Failed to read ICP %s; falling back to odoo.conf", ICP_KEY)
    return (config.get(CONF_KEY) or '').strip()


def _cookie_kwargs(domain):
    """Build set_cookie kwargs. Hardens Secure+SameSite only when Domain is set."""
    kwargs = {
        'max_age': _http.SESSION_LIFETIME,
        'httponly': True,
    }
    if domain:
        kwargs['domain'] = domain
        kwargs['secure'] = True
        kwargs['samesite'] = 'Lax'
    return kwargs


# --- Patch site 1: Request._save_session (odoo/http.py:1750) ---------------

_orig_save_session = _http.Request._save_session


def _save_session(self):
    sess = self.session
    if not sess.can_save:
        return

    if sess.should_rotate:
        sess['_geoip'] = self.geoip
        _http.root.session_store.rotate(sess, self.env)
    elif sess.is_dirty:
        sess['_geoip'] = self.geoip
        _http.root.session_store.save(sess)

    cookie_sid = self.httprequest.cookies.get('session_id')
    if sess.is_dirty or cookie_sid != sess.sid:
        domain = _get_cookie_domain(_request_env(self))
        self.future_response.set_cookie('session_id', sess.sid, **_cookie_kwargs(domain))


_http.Request._save_session = _save_session


# --- Patch site 2: HttpDispatcher.handle_error (odoo/http.py:1992) ---------

_orig_handle_error = _http.HttpDispatcher.handle_error


def _handle_error(self, exc):
    if isinstance(exc, _http.SessionExpiredException):
        session = self.request.session
        was_connected = session.uid is not None
        session.logout(keep_db=True)
        response = self.request.redirect_query(
            '/web/login', {'redirect': self.request.httprequest.full_path}
        )
        if was_connected:
            _http.root.session_store.rotate(session, self.request.env)
            domain = _get_cookie_domain(_request_env(self.request))
            response.set_cookie('session_id', session.sid, **_cookie_kwargs(domain))
        return response
    return _orig_handle_error(self, exc)


_http.HttpDispatcher.handle_error = _handle_error

_logger.info(
    "crearis_session_cookie_domain loaded: session_id cookie Domain= driven by ICP['%s'] (default empty = current behavior)",
    ICP_KEY,
)
