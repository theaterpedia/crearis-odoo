# Copyright 2026 Theaterpedia E.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    'name': 'Crearis Mail Templates (translations & overrides)',
    'summary': 'Central home for German/Czech mail-template translations, '
               'including templates owned by upstream modules',
    'version': '16.0.1.0.0',
    'category': 'Marketing/Email Marketing',
    'author': 'Theaterpedia',
    'website': 'https://theaterpedia.org/',
    'license': 'LGPL-3',
    # ---------------------------------------------------------------------
    # LOAD ORDER -- this module must load LAST of anything owning a
    # mail.template we translate or override. Odoo has no explicit module
    # sequence: load order is derived from the dependency graph, so "last"
    # is expressed by depending on every template-owning module.
    #
    # calendar       -> calendar.calendar_template_meeting_update      (id 9)
    # event          -> event.event_registration_mail_template_badge   (id 13)
    #                   event.event_subscription                       (id 14)
    #                   event.event_reminder                           (id 15)
    # event_session  -> event_session.event_session_*                  (ids 19-21)
    #                   (OCA/Tecnativa, AGPL-3, vendored under
    #                    odoo-custom-addons/event/ -- NEVER edit in place)
    #
    # crearis and crearis_milestones own their own templates and carry their
    # own i18n/, so they are deliberately NOT depended on here. agenda_dasei
    # likewise: its templates are correctly tenant-scoped (see
    # _meta/hcd/tasks_and_ideas/replace-hardcoded-domains-with-website-domain-sst.md)
    # and pulling it in would force a DAS-Ei-specific module on every install.
    # ---------------------------------------------------------------------
    'depends': [
        'calendar',
        'event',
        'event_session',
    ],
    # No data/ on purpose. German for upstream templates lands as i18n/de.po
    # entries referencing the upstream xmlids, so no upstream file is touched
    # and Odoo/OCA upgrades cannot clobber the work.
    #
    # OPEN QUESTION -- verify on the devbox (odoo_sandbox, :8169) before
    # relying on this in production: whether Odoo 16's translation importer
    # applies a term whose `#:` reference points at ANOTHER module's xmlid
    # when loaded from this module's i18n/de.po. If it does not, the fallback
    # is an override <record id="event.event_subscription"> in a data/ file
    # here -- which is a source-value override rather than a translation, and
    # would need a matching decision about which language that source carries.
    'data': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
