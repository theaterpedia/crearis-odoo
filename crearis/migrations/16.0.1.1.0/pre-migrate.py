# -*- coding: utf-8 -*-
# Migration: Event stages cleanup and sysreg sequences
# Version: 16.0.1.0.5 → 16.0.1.1.0

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Clean up duplicate event stages and update to sysreg-compatible sequences.
    
    Sysreg bitmask architecture:
    | Sysreg | Name      | Odoo ID |
    |--------|-----------|---------|
    | 1      | new       | 1       |
    | 8      | planned   | 2       |
    | 64     | booked    | 30      |
    | 512    | announced | 3       |
    | 4096   | current   | 31      |
    | 8192   | completed | 4       |
    | 12288  | cancelled | 5       |
    """
    if not version:
        return

    _logger.info("Starting event stages migration to sysreg sequences")

    # Step 1: Check if any events use the old duplicate stages (24-29)
    cr.execute("""
        SELECT stage_id, COUNT(*) as cnt 
        FROM event_event 
        WHERE stage_id IN (24, 25, 26, 27, 28, 29) 
        GROUP BY stage_id
    """)
    events_on_old_stages = cr.fetchall()
    
    if events_on_old_stages:
        _logger.warning(
            "Events found on old stages, migrating to new stages: %s",
            events_on_old_stages
        )
        # Map old stages to new equivalents
        stage_mapping = {
            24: 1,     # planning → new
            25: 3,     # published → announced
            26: 31,    # running → current (if exists, else announced)
            27: 4,     # completed → completed
            28: 5,     # cancelled → cancelled
            29: 4,     # archived → completed
        }
        for old_id, new_id in stage_mapping.items():
            cr.execute(
                "UPDATE event_event SET stage_id = %s WHERE stage_id = %s",
                (new_id, old_id)
            )
            _logger.info("Migrated events from stage %s to %s", old_id, new_id)

    # Step 2: Delete old xmlid records for duplicate stages
    cr.execute("""
        DELETE FROM ir_model_data 
        WHERE model = 'event.stage' 
        AND module = 'crearis' 
        AND res_id IN (24, 25, 26, 27, 28, 29)
    """)
    deleted_xmlids = cr.rowcount
    _logger.info("Deleted %s old xmlid records", deleted_xmlids)

    # Step 3: Delete old duplicate stages
    cr.execute("DELETE FROM event_stage WHERE id IN (24, 25, 26, 27, 28, 29)")
    deleted_stages = cr.rowcount
    _logger.info("Deleted %s old duplicate stages", deleted_stages)

    # Step 4: Update base Odoo stages to sysreg sequences
    sequence_updates = [
        (1, 1),      # new
        (8, 2),      # planned (was booked)
        (512, 3),    # announced
        (8192, 4),   # completed (was done/ended)
        (12288, 5),  # cancelled
    ]
    for sequence, stage_id in sequence_updates:
        cr.execute(
            "UPDATE event_stage SET sequence = %s WHERE id = %s",
            (sequence, stage_id)
        )
    _logger.info("Updated base stage sequences to sysreg values")

    # Step 5: Update stage names to English base (JSON object format for translated fields)
    # IMPORTANT: Odoo 16 translated fields use JSONB objects like {"en_US": "value"}
    # Using a plain JSON string like "new" causes array corruption on subsequent updates
    name_updates = [
        ('{"en_US": "new"}', 1),
        ('{"en_US": "planned"}', 2),
        ('{"en_US": "announced"}', 3),
        ('{"en_US": "completed"}', 4),
        ('{"en_US": "cancelled"}', 5),
    ]
    for name, stage_id in name_updates:
        cr.execute(
            "UPDATE event_stage SET name = %s::jsonb WHERE id = %s",
            (name, stage_id)
        )
    _logger.info("Updated base stage names to English")

    # Step 6: Update crearis stages (30, 31) if they exist
    cr.execute("SELECT id FROM event_stage WHERE id IN (30, 31)")
    existing_crearis_stages = [r[0] for r in cr.fetchall()]
    
    if 30 in existing_crearis_stages:
        cr.execute(
            "UPDATE event_stage SET name = %s::jsonb, sequence = %s WHERE id = %s",
            ('{"en_US": "booked"}', 64, 30)
        )
        _logger.info("Updated crearis.event_stage_booked (id=30)")
    
    if 31 in existing_crearis_stages:
        cr.execute(
            "UPDATE event_stage SET name = %s::jsonb, sequence = %s WHERE id = %s",
            ('{"en_US": "current"}', 4096, 31)
        )
        _logger.info("Updated crearis.event_stage_current (id=31)")

    _logger.info("Event stages migration completed successfully")
