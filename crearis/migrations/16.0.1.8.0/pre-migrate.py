# -*- coding: utf-8 -*-
# Copyright 2025 Hans Dönitz - Theaterpedia.org
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""
Layer 2 (DB) Migration: Add partner_id to domainuser

This pre-migration:
1. Adds partner_id column to crearis_domainuser if not exists
2. Populates partner_id from user_id.partner_id for existing records
3. Runs BEFORE ORM applies required=True constraint

After this migration, all domainuser records will have a partner_id,
allowing the ORM to add the NOT NULL constraint.
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    _logger.info("Layer 2 pre-migration: Populating domainuser.partner_id from user_id.partner_id")

    # Add partner_id column if not exists (nullable initially)
    cr.execute("""
        ALTER TABLE crearis_domainuser
        ADD COLUMN IF NOT EXISTS partner_id INTEGER
    """)

    # Populate partner_id from user_id → res_users.partner_id
    cr.execute("""
        UPDATE crearis_domainuser du
        SET partner_id = u.partner_id
        FROM res_users u
        WHERE du.user_id = u.id
        AND du.partner_id IS NULL
    """)

    # Count how many records were updated
    cr.execute("""
        SELECT COUNT(*) FROM crearis_domainuser WHERE partner_id IS NOT NULL
    """)
    count = cr.fetchone()[0]
    _logger.info("Layer 2 pre-migration: %d domainuser records now have partner_id", count)

    # Check for any orphans (domainuser with user_id but no partner_id populated)
    cr.execute("""
        SELECT COUNT(*) FROM crearis_domainuser
        WHERE user_id IS NOT NULL AND partner_id IS NULL
    """)
    orphans = cr.fetchone()[0]
    if orphans:
        _logger.warning(
            "Layer 2 pre-migration: %d domainuser records have user_id but NULL partner_id - "
            "these users may lack partner records", orphans
        )
