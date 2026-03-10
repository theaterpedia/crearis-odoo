# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from . import website
from . import weboptions
from . import demo_mixin
from . import res_partner
from . import blog
from . import json_field
from . import episode
from . import domainuser
from . import version
from . import location
from . import res_company
from . import schedule_mixin  # Must be before event (provides event.schedule.mixin)
from . import agenda_line  # Renamed from event_session_line (2026-02-02)
from . import event
from . import event_registration
from . import calendar_event
from . import crm_lead  # S2L: email-only consulting inquiries
from . import config_template
# from . import event_workflow
from . import res_config_settings

