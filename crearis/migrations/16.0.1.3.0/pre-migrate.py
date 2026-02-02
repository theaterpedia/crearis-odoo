# -*- coding: utf-8 -*-
# Migration: Rename event.session.line → agenda.line
# Version: 16.0.1.3.0
# Date: 2026-02-02

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Rename event.session.line model to agenda.line.
    
    This migration:
    1. Renames the SQL table
    2. Updates ir.model and ir.model.data references
    3. Adds new columns for extended functionality
    """
    if not version:
        return
    
    _logger.info("Starting migration: event.session.line → agenda.line")
    
    # Step 1: Rename the table
    cr.execute("""
        ALTER TABLE IF EXISTS event_session_line 
        RENAME TO agenda_line
    """)
    _logger.info("Renamed table event_session_line → agenda_line")
    
    # Step 2: Update ir.model (name is JSONB for translations)
    cr.execute("""
        UPDATE ir_model 
        SET model = 'agenda.line', name = '{"en_US": "Agenda Line"}'::jsonb
        WHERE model = 'event.session.line'
    """)
    
    # Step 3: Update ir.model.fields references
    cr.execute("""
        UPDATE ir_model_fields 
        SET relation = 'agenda.line'
        WHERE relation = 'event.session.line'
    """)
    
    # Step 4: Update ir.model.data (XML IDs)
    cr.execute("""
        UPDATE ir_model_data 
        SET name = REPLACE(name, 'event_session_line', 'agenda_line')
        WHERE name LIKE '%event_session_line%'
    """)
    
    # Step 5: Add new columns if they don't exist
    # Type field (expanding from just mode)
    cr.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agenda_line' AND column_name = 'type'
            ) THEN
                ALTER TABLE agenda_line ADD COLUMN type VARCHAR DEFAULT 'session';
            END IF;
        END $$;
    """)
    
    # Rename 'type' to 'mode' (the old 'type' was actually mode)
    cr.execute("""
        DO $$ 
        BEGIN
            -- Check if old 'type' column exists and new 'mode' doesn't
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agenda_line' AND column_name = 'type'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agenda_line' AND column_name = 'mode'
            ) THEN
                -- The existing 'type' column contains mode values, rename it
                ALTER TABLE agenda_line RENAME COLUMN type TO mode;
                -- Add new 'type' column for line type
                ALTER TABLE agenda_line ADD COLUMN type VARCHAR DEFAULT 'session';
            END IF;
        END $$;
    """)
    
    # Source field
    cr.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agenda_line' AND column_name = 'source'
            ) THEN
                ALTER TABLE agenda_line ADD COLUMN source VARCHAR DEFAULT 'json';
            END IF;
        END $$;
    """)
    
    # locked_edits field
    cr.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agenda_line' AND column_name = 'locked_edits'
            ) THEN
                ALTER TABLE agenda_line ADD COLUMN locked_edits BOOLEAN DEFAULT TRUE;
            END IF;
        END $$;
    """)
    
    # Provider fields
    cr.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agenda_line' AND column_name = 'provider_type'
            ) THEN
                ALTER TABLE agenda_line ADD COLUMN provider_type VARCHAR DEFAULT 'event';
            END IF;
            
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agenda_line' AND column_name = 'post_id'
            ) THEN
                ALTER TABLE agenda_line ADD COLUMN post_id INTEGER;
            END IF;
            
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agenda_line' AND column_name = 'product_id'
            ) THEN
                ALTER TABLE agenda_line ADD COLUMN product_id INTEGER;
            END IF;
        END $$;
    """)
    
    # Gate pattern fields (for milestones)
    cr.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agenda_line' AND column_name = 'gate_state'
            ) THEN
                ALTER TABLE agenda_line ADD COLUMN gate_state VARCHAR DEFAULT 'pending';
            END IF;
            
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agenda_line' AND column_name = 'milestone_key'
            ) THEN
                ALTER TABLE agenda_line ADD COLUMN milestone_key VARCHAR;
            END IF;
            
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agenda_line' AND column_name = 'milestone_days_before'
            ) THEN
                ALTER TABLE agenda_line ADD COLUMN milestone_days_before INTEGER;
            END IF;
            
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agenda_line' AND column_name = 'milestone_template_id'
            ) THEN
                ALTER TABLE agenda_line ADD COLUMN milestone_template_id INTEGER;
            END IF;
        END $$;
    """)
    
    # DateTime fields
    cr.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agenda_line' AND column_name = 'date_start'
            ) THEN
                ALTER TABLE agenda_line ADD COLUMN date_start TIMESTAMP;
            END IF;
            
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agenda_line' AND column_name = 'date_end'
            ) THEN
                ALTER TABLE agenda_line ADD COLUMN date_end TIMESTAMP;
            END IF;
            
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agenda_line' AND column_name = 'teaching_units'
            ) THEN
                ALTER TABLE agenda_line ADD COLUMN teaching_units NUMERIC(4,1);
            END IF;
        END $$;
    """)
    
    # Set existing records as type='session', provider_type='event'
    cr.execute("""
        UPDATE agenda_line 
        SET type = 'session', provider_type = 'event'
        WHERE type IS NULL OR provider_type IS NULL
    """)
    
    _logger.info("Migration complete: agenda.line model ready")
