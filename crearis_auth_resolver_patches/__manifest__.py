# -*- coding: utf-8 -*-
# Copyright 2026 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Crearis Auth Resolver Patches',
    'version': '16.0.0.1.0',
    'summary': 'Adds auto-login to graphql_theaterpedia Register + ChangePassword mutations',
    'description': """Crearis Auth Resolver Patches

Monkey-patches two graphql_theaterpedia resolvers to add the missing
auto-login step:

- Register.mutate — after signup(), call request.session.authenticate()
  so a Set-Cookie response header is issued (was returning the user but
  no session was started).
- ChangePassword.mutate — after signup(data, token), call
  request.session.authenticate() so reset-password-confirm auto-logs the
  user in (was returning the user with the new password but no session).

UpdatePassword (logged-in change) already auto-logs-in via the upstream
resolver — no patch needed.

The patches preserve all existing behavior (newsletter subscription,
error-handling, return shape) and only add the session.authenticate()
call after the signup-side work is done. ~10 LOC per patch.

Required for CV-side proxy-everything SSO flow (per
2026-05-20 CTO architectural-decision-record v0.2 §5.3 +
2026-05-21 CV@wsl-2 Phase-A action-plan §3 + §5).
""",
    'category': 'Tools',
    'license': 'LGPL-3',
    'author': 'Theaterpedia / CO@prod',
    'website': 'https://theaterpedia.org/',
    'depends': ['graphql_theaterpedia'],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
