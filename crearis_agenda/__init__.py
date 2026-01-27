# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from . import models


def _reset_sync_lock(cr, registry):
    """Reset sync running flag on server startup to prevent stuck locks."""
    cr.execute("UPDATE res_company SET ms_agenda_sync_running = false WHERE ms_agenda_sync_running = true")
