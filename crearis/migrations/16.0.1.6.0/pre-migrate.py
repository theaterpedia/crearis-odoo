# -*- coding: utf-8 -*-
# Migration: schedule field translate=True → translate=False
# Version: 16.0.1.6.0
# Date: 2026-02-13
#
# The schedule field contains language-independent time/date strings
# (e.g., "FR 19:00-21:30\nSA 09:00-18:00") that should NOT be translated.
# Odoo 16 stores translate=True fields as JSONB {"de_DE": "...", "en_US": "..."}.
# This migration converts them back to plain text.

import json
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Convert schedule column from JSONB (translate=True) to plain text (translate=False)."""
    if not version:
        return

    _logger.info("Starting migration: schedule translate=True → translate=False")

    # Check current column type
    cr.execute("""
        SELECT data_type FROM information_schema.columns
        WHERE table_name = 'event_event' AND column_name = 'schedule'
    """)
    row = cr.fetchone()
    if not row:
        _logger.info("schedule column not found, skipping")
        return

    col_type = row[0]
    _logger.info(f"schedule column type: {col_type}")

    if col_type == 'jsonb':
        # Extract text value from JSONB: prefer de_DE, fallback en_US, fallback first value
        # Step 1: Create a temporary text column
        cr.execute("ALTER TABLE event_event ADD COLUMN schedule_tmp text")

        # Step 2: Extract best text value from JSONB
        cr.execute("""
            UPDATE event_event
            SET schedule_tmp = COALESCE(
                schedule->>'de_DE',
                schedule->>'en_US',
                (SELECT value FROM jsonb_each_text(schedule) LIMIT 1),
                ''
            )
            WHERE schedule IS NOT NULL
        """)

        # Step 3: Drop the JSONB column and rename
        cr.execute("ALTER TABLE event_event DROP COLUMN schedule")
        cr.execute("ALTER TABLE event_event RENAME COLUMN schedule_tmp TO schedule")

        # Count migrated
        cr.execute("SELECT count(*) FROM event_event WHERE schedule IS NOT NULL AND schedule != ''")
        count = cr.fetchone()[0]
        _logger.info(f"Migrated {count} schedule values from JSONB to text")

    elif col_type in ('text', 'character varying'):
        _logger.info("schedule is already text type, skipping conversion")
    else:
        _logger.warning(f"Unexpected schedule column type: {col_type}")
