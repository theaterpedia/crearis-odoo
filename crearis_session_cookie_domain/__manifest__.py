# -*- coding: utf-8 -*-
# Copyright 2026 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Crearis Session Cookie Domain',
    'version': '16.0.0.1.0',
    'summary': 'Adds Domain= attribute to Odoo session_id cookie for cross-subdomain SSO',
    'description': """Crearis Session Cookie Domain

Monkey-patches Odoo's session_id cookie emission so that a configurable
Domain attribute can be set, enabling cross-subdomain SSO across the
dasei.eu surface (service.dasei.eu, uia.dasei.eu, sfr.dasei.eu, etc.).

Driven by ir.config_parameter['session_cookie.domain'] (default: empty =
no Domain attribute, current Odoo behavior preserved). Can also be pinned
at boot time via odoo.conf 'session_cookie_domain = .dasei.eu'.

When a Domain is set, the cookie is also hardened with Secure=True and
SameSite=Lax — required for cross-subdomain Cookies over HTTPS.

Two patch sites in odoo.http:
  - Request._save_session (http.py:1766)
  - HttpDispatcher.handle_error session-expired branch (http.py:2010)
""",
    'category': 'Tools',
    'license': 'LGPL-3',
    'author': 'Theaterpedia / CO@prod',
    'website': 'https://theaterpedia.org/',
    'depends': ['base'],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
