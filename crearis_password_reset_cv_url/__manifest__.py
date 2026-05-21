# -*- coding: utf-8 -*-
# Copyright 2026 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Crearis Password Reset CV URL',
    'version': '16.0.0.1.0',
    'summary': 'Routes password-reset email link through CV (e.g. /auth/reset) instead of the legacy /forgot-password/new-password',
    'description': """Crearis Password Reset CV URL

Overrides graphql_theaterpedia.res_users.api_action_reset_password to
construct the password-reset email URL from an ICP-parameterized path
instead of the hardcoded '/forgot-password/new-password' (CN-Nuxt legacy).

When ICP 'cv.password_reset_base_url' is set (e.g. 'https://my.theaterpedia.org/auth/reset'):
  → reset email links to that URL + '?token=<token>'

When ICP empty (default · no behavior change):
  → reset email continues to use 'website.domain + /forgot-password/new-password?token=...'

Use ICP-empty for the installed-dormant deploy. Flip ICP when CV-side
/auth/reset SPA route ships (per CV@wsl-2 Phase-A action-plan §5 / C4 +
v0.2 §5.3 Phase-C item-2).

Reversible: clear the ICP via Web UI to revert to legacy URL.

Required Phase-C item per CTO architectural-decision-record v0.2 §5.3
(password-reset mail-template customization).
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
