# Registration Sync (D4) - Developer Documentation

## Overview

Syncs `plan_veranstaltungsteilnehmer` from SharePoint to `event.registration` in Odoo.

**SharePoint List GUID:** `C9E05737-4C47-4E0F-A6B6-C6D6F3FBE88D`

## Field Mapping

| SharePoint Field | Odoo Field | Notes |
|-----------------|------------|-------|
| `id` | `ms_id` | SharePoint item ID |
| `@odata.etag` | `ms_version` | Change detection |
| `TeilnehmerLookupId` | `partner_id` | Via `res.partner.ms_contact_id` |
| `VeranstaltungLookupId` | `event_id` | Via `event.event.ms_id` |
| `StatusLookupId` | `state` | See mapping below |
| `UE` | (future) | Units attended |

## Status Mapping

```python
STATUS_TO_REGISTRATION_STATE = {
    12: 'new',      # Angebot
    5: 'demo',      # vorbehaltlich
    1: 'draft',     # unbestätigt
    13: 'open',     # bestätigt
    3: 'done',      # vollständig (attended)
    8: 'cancel',    # storniert
    6: 'no_show',   # abwesend
    4: 'partial',   # teilweise
}
```

## Performance: Skipping PDF Generation

**Problem:** Odoo's event module triggers `_update_mail_schedulers()` on registration create/write, which calls `wkhtmltopdf` to generate PDF tickets. With 6000+ registrations, this causes:
- Extreme slowdown (hours instead of seconds)
- Server hangs
- Transaction timeouts

**Solution:** Use `install_mode=True` context flag:

```python
Registration = Registration.with_context(
    mail_create_nosubscribe=True,
    mail_create_nolog=True,
    mail_notrack=True,
    tracking_disable=True,
    install_mode=True,  # Critical: prevents event mail schedulers
)
```

**Why `install_mode`?** The Odoo event module specifically checks for this:

```python
# From odoo/addons/event/models/event_registration.py
if not self.env.context.get('install_mode', False):
    registrations._update_mail_schedulers()
```

Other flags like `import_file` do NOT prevent this.

## Backfilling Confirmation Emails & Tickets

After sync, you can generate confirmation emails/tickets on demand:

```python
# Via shell or server action
self.env['crearis.agenda.sync'].backfill_registration_mails()

# Or for specific registrations
sync = self.env['crearis.agenda.sync']
regs = self.env['event.registration'].search([('event_id', '=', 123)])
sync.backfill_registration_mails(regs)
```

**How it works:**
1. Finds `event.mail` schedulers with `interval_type='after_sub'`
2. Resets `mail_done=False` to allow processing
3. Calls `execute()` which creates `event.mail.registration` records and sends mails

**Alternative:** Let the `event.mail` cron handle it automatically (runs periodically).

## Sync Statistics (2026-01-26)

- Total records: ~6000
- First sync: ~1000 processed, ~600 fully mapped
- Sync time: ~20 seconds (with `install_mode`)

## Dependencies

Registrations depend on:
1. **Events** synced first (need `event.event.ms_id`)
2. **Contacts** synced first (need `res.partner.ms_contact_id`)

Sync order in `sync_all()`:
1. `sync_contacts()` 
2. `sync_events()`
3. `sync_registrations()`

## Troubleshooting

### Registration skipped - "Event not found"
The `VeranstaltungLookupId` doesn't match any `event.event.ms_id`. Either:
- Event not synced yet
- Event was filtered out (e.g., wrong stage)

### Registration skipped - "No partner"
`TeilnehmerLookupId` doesn't match `res.partner.ms_contact_id`. The registration is still created but without partner link.

### Sync hangs on PDF generation
Check that `install_mode=True` is in context. Look for log entries like:
```
wkhtmltopdf: ...
```

## Files

- `agenda_dasei/models/sync_registrations.py` - Main sync logic
- `crearis/models/event_registration.py` - Extended model with `ms_id`, `ms_version`, `ms_synced` fields
