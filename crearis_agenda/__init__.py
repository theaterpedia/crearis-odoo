# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from . import models


def _reset_sync_lock(cr, registry):
    """Reset sync lock timestamp on module install/upgrade to prevent stuck locks."""
    cr.execute("UPDATE res_company SET ms_agenda_sync_started = NULL WHERE ms_agenda_sync_started IS NOT NULL")
