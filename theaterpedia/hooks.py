# -*- coding: utf-8 -*-
# Copyright 2026 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

# Languages required for Theaterpedia deployment
REQUIRED_LANGUAGES = ['de_DE', 'cs_CZ']


def post_init_hook(cr, registry):
    """Activate required languages for Theaterpedia deployment."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    _activate_languages(env)


def _activate_languages(env):
    """Activate de_DE (German) and cs_CZ (Czech) languages.

    These are required for:
    - de_DE: Primary UI and content language (schedule parsing, event fields)
    - cs_CZ: Czech border region participants (DASEi cross-border events)
    """
    Lang = env['res.lang']

    for lang_code in REQUIRED_LANGUAGES:
        existing = Lang.search([('code', '=', lang_code), ('active', '=', True)], limit=1)
        if existing:
            _logger.info("theaterpedia: Language %s already active", lang_code)
            continue

        lang = Lang._activate_lang(lang_code)
        if lang:
            _logger.info("theaterpedia: Activated language %s", lang_code)
        else:
            # Try to create if not in base data (unlikely for de_DE/cs_CZ)
            _logger.warning(
                "theaterpedia: Could not activate language %s — "
                "check if it exists in base/data/res.lang.csv",
                lang_code
            )
