# Eleanora Implementation Plan

*Created: 2026-01-28*  
*Status: Planning (not started)*  
*Context: Location Management + Schedule Views for Eleanora Allerdings*

---

## Executive Summary

After implementing L1-L10 (location sync) and L16-L32 (schedule views), we identified gaps between the wireframe vision and current implementation. This document outlines the next phase to fully support Eleanora's workflow as DASEi's Location & Room Manager.

**Core Insight:** The wireframes show **session-level rows**, but we implemented **event-level filtering**. Session flattening is the key missing piece.

---

## Current State

### What Works ✅

| Feature | Implementation | Location |
|---------|---------------|----------|
| Location sync | 12 venue partners, 109 events linked | `agenda_dasei` |
| Schedule parsing | `ScheduleParser` with shortcodes | `crearis/models/schedule_mixin.py` |
| JSONB storage | `schedule_data` with sessions array | `event.schedule.mixin` |
| Computed summaries | `has_online_sessions`, `total_hours`, etc. | stored, filterable |
| Online Sessions action | Filter events with online sessions | `action_event_online_sessions` |
| Schedule Config | Test parser in company settings | `view_company_form_schedule_config` |
| Event Schedule Tab | Raw text editor + parse button | `view_event_form_schedule_tab` |

### Gaps vs. Wireframe 🔶

| Wireframe Element | Status | Gap |
|-------------------|--------|-----|
| Sessions table in Event form | ❌ Missing | Shows raw JSON, not O2M table |
| Online Sessions line-by-line | ❌ Missing | Shows events, not sessions |
| Issue tags with colors | ❌ Missing | No `tasks_and_issues` category |
| Location column in tree | ❌ Missing | Can't see venue at a glance |

---

## Implementation Plan

### Task 1: Session Lines Model (~2h)

**Goal:** Create `event.session.line` model that flattens `schedule_data.sessions[]` into searchable records.

#### 1.1 Model Definition

**File:** `crearis/models/event_session_line.py` (NEW)

```python
from odoo import api, fields, models


class EventSessionLine(models.Model):
    _name = 'event.session.line'
    _description = 'Event Session Line'
    _order = 'date, start'
    _rec_name = 'display_name'

    # Core fields (from schedule_data.sessions[])
    event_id = fields.Many2one('event.event', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    
    day = fields.Char('Weekday', size=3)  # MON, TUE, ...
    date = fields.Date('Date', index=True)
    start = fields.Char('Start Time', size=5)  # HH:MM
    end = fields.Char('End Time', size=5)
    duration_h = fields.Float('Duration (h)')
    
    type = fields.Selection([
        ('online', 'Online'),
        ('venue', 'Venue'),
        ('individual', 'Individual'),
        ('tbd', 'TBD'),
    ], string='Type', default='venue')
    
    location_hint = fields.Char('Location Hint')
    room = fields.Char('Room')
    notes = fields.Text('Notes')
    
    # Related fields for reporting/filtering
    event_name = fields.Char(related='event_id.name', store=True, string='Event')
    company_id = fields.Many2one(related='event_id.company_id', store=True, index=True)
    event_date_begin = fields.Datetime(related='event_id.date_begin', store=True)
    address_id = fields.Many2one(related='event_id.address_id', store=True, string='Venue')
    
    # Computed display
    display_name = fields.Char(compute='_compute_display_name', store=True)
    
    @api.depends('event_id.name', 'date', 'start', 'type')
    def _compute_display_name(self):
        for rec in self:
            type_icon = '🌐' if rec.type == 'online' else '📍'
            rec.display_name = f"{type_icon} {rec.date or ''} {rec.start or ''} - {rec.event_id.name or ''}"
```

#### 1.2 Extend Event Model

**File:** `crearis/models/event.py` (MODIFY)

```python
# Add to event.event
session_line_ids = fields.One2many(
    'event.session.line', 'event_id', 
    string='Session Lines',
    help='Flattened session records from schedule_data'
)

def _sync_session_lines(self):
    """Sync session_line_ids from schedule_data.sessions[]"""
    SessionLine = self.env['event.session.line']
    for event in self:
        # Clear existing lines
        event.session_line_ids.unlink()
        
        sessions = (event.schedule_data or {}).get('sessions', [])
        for idx, sess in enumerate(sessions):
            SessionLine.create({
                'event_id': event.id,
                'sequence': idx * 10,
                'day': sess.get('day'),
                'date': sess.get('date'),
                'start': sess.get('start'),
                'end': sess.get('end'),
                'duration_h': sess.get('duration_h', 0),
                'type': sess.get('type', 'venue'),
                'location_hint': sess.get('location_hint'),
                'room': sess.get('room'),
                'notes': sess.get('notes'),
            })
```

#### 1.3 Auto-Sync on Parse

**File:** `crearis/models/schedule_mixin.py` (MODIFY)

```python
def action_parse_schedule(self):
    """Parse schedule_raw and populate schedule_data + session_lines."""
    for record in self:
        if record.schedule_raw:
            # ... existing parsing ...
            record.schedule_data = result
            
            # Sync session lines if model supports it
            if hasattr(record, '_sync_session_lines'):
                record._sync_session_lines()
```

#### 1.4 Views

**File:** `crearis/views/event_session_line_views.xml` (NEW)

```xml
<!-- Tree view for Online Sessions -->
<record id="view_event_session_line_tree" model="ir.ui.view">
    <field name="name">event.session.line.tree</field>
    <field name="model">event.session.line</field>
    <field name="arch" type="xml">
        <tree decoration-info="type == 'online'" decoration-muted="type == 'individual'">
            <field name="date"/>
            <field name="start"/>
            <field name="end"/>
            <field name="duration_h" sum="Total Hours"/>
            <field name="type"/>
            <field name="event_name"/>
            <field name="address_id"/>
            <field name="location_hint"/>
        </tree>
    </field>
</record>

<!-- Search view -->
<record id="view_event_session_line_search" model="ir.ui.view">
    <field name="name">event.session.line.search</field>
    <field name="model">event.session.line</field>
    <field name="arch" type="xml">
        <search>
            <field name="event_name"/>
            <field name="date"/>
            <filter name="online" string="Online" domain="[('type', '=', 'online')]"/>
            <filter name="venue" string="Venue" domain="[('type', '=', 'venue')]"/>
            <filter name="this_week" string="This Week" domain="[
                ('date', '>=', (context_today() - datetime.timedelta(days=context_today().weekday())).strftime('%Y-%m-%d')),
                ('date', '&lt;', (context_today() + datetime.timedelta(days=7-context_today().weekday())).strftime('%Y-%m-%d'))
            ]"/>
            <filter name="next_month" string="Next 30 Days" domain="[
                ('date', '>=', context_today().strftime('%Y-%m-%d')),
                ('date', '&lt;', (context_today() + datetime.timedelta(days=30)).strftime('%Y-%m-%d'))
            ]"/>
            <group expand="0" string="Group By">
                <filter name="group_date" string="Date" context="{'group_by': 'date'}"/>
                <filter name="group_type" string="Type" context="{'group_by': 'type'}"/>
                <filter name="group_event" string="Event" context="{'group_by': 'event_id'}"/>
                <filter name="group_venue" string="Venue" context="{'group_by': 'address_id'}"/>
            </group>
        </search>
    </field>
</record>

<!-- Action: All Online Sessions -->
<record id="action_online_session_lines" model="ir.actions.act_window">
    <field name="name">Online Sessions</field>
    <field name="res_model">event.session.line</field>
    <field name="view_mode">tree,form</field>
    <field name="domain">[('type', '=', 'online')]</field>
    <field name="context">{'search_default_next_month': 1}</field>
</record>

<!-- Menu entry under Events -->
<menuitem id="menu_online_sessions"
    name="Online Sessions"
    parent="event.event_main_menu"
    action="action_online_session_lines"
    sequence="25"/>
```

#### 1.5 Update Event Form Schedule Tab

Replace raw JSON display with O2M table:

```xml
<!-- In event_schedule_views.xml, update the schedule tab -->
<page string="Schedule" name="schedule">
    <group>
        <field name="schedule_raw" widget="text"/>
        <button name="action_parse_schedule" string="Parse Schedule" type="object" class="btn-primary"/>
    </group>
    <group string="Parsed Sessions">
        <field name="session_line_ids" nolabel="1">
            <tree editable="bottom" decoration-info="type == 'online'">
                <field name="sequence" widget="handle"/>
                <field name="day"/>
                <field name="date"/>
                <field name="start"/>
                <field name="end"/>
                <field name="duration_h"/>
                <field name="type"/>
                <field name="location_hint"/>
            </tree>
        </field>
    </group>
    <group>
        <field name="total_hours"/>
        <field name="online_hours"/>
        <field name="venue_hours"/>
        <field name="session_count"/>
    </group>
</page>
```

#### 1.6 Migration: Populate Existing Events

```python
# Run once after module update
events = env['event.event'].search([('schedule_data', '!=', False)])
events._sync_session_lines()
env.cr.commit()
```

---

### Task 2: Issue Tags (~30min)

**Goal:** Add `tasks_and_issues` tag category with `location_issue` tag for Eleanora to flag problems.

#### 2.1 Data File

**File:** `agenda_dasei/data/event_tag_issues.xml` (NEW)

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Tag Category: Tasks & Issues -->
    <record id="event_tag_category_issues" model="event.tag.category">
        <field name="name">Tasks &amp; Issues</field>
        <field name="sequence">50</field>
    </record>
    
    <!-- Issue Tags -->
    <record id="event_tag_location_issue" model="event.tag">
        <field name="name">Location Issue</field>
        <field name="category_id" ref="event_tag_category_issues"/>
        <field name="color">1</field>  <!-- Red -->
    </record>
    
    <record id="event_tag_schedule_issue" model="event.tag">
        <field name="name">Schedule Issue</field>
        <field name="category_id" ref="event_tag_category_issues"/>
        <field name="color">2</field>  <!-- Orange -->
    </record>
    
    <record id="event_tag_needs_confirmation" model="event.tag">
        <field name="name">Needs Confirmation</field>
        <field name="category_id" ref="event_tag_category_issues"/>
        <field name="color">3</field>  <!-- Yellow -->
    </record>
    
    <record id="event_tag_cancellation_pending" model="event.tag">
        <field name="name">Cancellation Pending</field>
        <field name="category_id" ref="event_tag_category_issues"/>
        <field name="color">9</field>  <!-- Purple -->
    </record>
</odoo>
```

#### 2.2 Update Manifest

**File:** `agenda_dasei/__manifest__.py` (MODIFY)

```python
'data': [
    # ... existing ...
    'data/event_tag_issues.xml',
],
```

#### 2.3 Quick-Tag Buttons (Optional Enhancement)

Add buttons to Event form for quick tagging:

```xml
<button name="action_add_location_issue_tag" string="🏷️ Location Issue" type="object" class="btn-link"/>
```

```python
def action_add_location_issue_tag(self):
    tag = self.env.ref('agenda_dasei.event_tag_location_issue')
    self.tag_ids = [(4, tag.id)]
```

---

### Task 3: Tree View Enhancements (~15min)

**Goal:** Add location column and enable grouping by venue.

#### 3.1 Update Event Tree View

**File:** `crearis/views/event_schedule_views.xml` (MODIFY)

Update `view_event_tree_schedule`:

```xml
<record id="view_event_tree_schedule" model="ir.ui.view">
    <field name="name">event.event.tree.schedule</field>
    <field name="model">event.event</field>
    <field name="inherit_id" ref="event.view_event_tree"/>
    <field name="arch" type="xml">
        <xpath expr="//field[@name='date_begin']" position="after">
            <field name="address_id" string="Venue" optional="show"/>
        </xpath>
        <xpath expr="//field[@name='seats_reserved']" position="after">
            <field name="has_online_sessions" widget="boolean" optional="show"/>
            <field name="session_count" optional="hide"/>
            <field name="total_hours" optional="hide"/>
        </xpath>
    </field>
</record>
```

#### 3.2 Add Location Group Filter

**File:** `crearis/views/event_schedule_views.xml` (MODIFY)

Update search view to add venue grouping:

```xml
<record id="view_event_search_schedule" model="ir.ui.view">
    <field name="name">event.event.search.schedule</field>
    <field name="model">event.event</field>
    <field name="inherit_id" ref="event.view_event_search"/>
    <field name="arch" type="xml">
        <xpath expr="//group" position="inside">
            <filter name="group_by_venue" string="Venue" context="{'group_by': 'address_id'}"/>
        </xpath>
    </field>
</record>
```

---

## File Summary

| File | Action | Module |
|------|--------|--------|
| `crearis/models/event_session_line.py` | CREATE | crearis |
| `crearis/models/__init__.py` | MODIFY | crearis |
| `crearis/models/event.py` | MODIFY | crearis |
| `crearis/models/schedule_mixin.py` | MODIFY | crearis |
| `crearis/views/event_session_line_views.xml` | CREATE | crearis |
| `crearis/views/event_schedule_views.xml` | MODIFY | crearis |
| `crearis/__manifest__.py` | MODIFY | crearis |
| `crearis/security/ir.model.access.csv` | MODIFY | crearis |
| `agenda_dasei/data/event_tag_issues.xml` | CREATE | agenda_dasei |
| `agenda_dasei/__manifest__.py` | MODIFY | agenda_dasei |

---

## Further Recommendations

### Short-Term (Next Sprint)

1. **Filter Presets for Eleanora**
   - "offene Tasks" = events with `tasks_and_issues` tags
   - "Stornierungen" = events in cancellation stage
   - "Nächste 30 Tage" = date filter
   - Save as shared filter actions

2. **Session-to-Track Promotion** (Optional)
   - Button: "Create Tracks from Sessions"
   - Converts `session_line_ids` → `event.track` records
   - For events needing detailed speaker/location per session

3. **Auto-Flag from Parser**
   - When `_anfrage_` generates `issue_schedule` flag
   - Auto-add `event_tag_schedule_issue` tag
   - Visual indicator in tree view

### Medium-Term

4. **Booking Overview Report**
   - Group sessions by venue + date range
   - PDF template with venue contact info
   - "Email to Location Partner" button

5. **Session Calendar View**
   - `event.session.line` in calendar
   - Color by type (online=blue, venue=green)
   - Filter by venue for room scheduling

6. **SharePoint Write-Back**
   - Serialize `schedule_data` → `oschedule_data` SP field
   - MS Access can read flattened sessions
   - Power Automate triggers on changes

### Architecture Notes

**Why stored O2M instead of computed?**
- Enables SQL filtering, grouping, aggregation
- Works with standard tree/kanban views
- Can add per-session fields later (conference_url, track_id)
- Performance: no JSONB parsing on every list render

**Why not use event.track directly?**
- `event.track` is heavy (speakers, stages, proposals, website integration)
- Session lines are lightweight display/reporting records
- Can promote to tracks when needed (progressive enhancement)

**Sync Strategy:**
- Parse → update `schedule_data` → sync `session_line_ids`
- Lines are always regenerated (not edited manually)
- Future: allow manual line edits → write back to JSONB

---

## Validation Checklist

After implementation, verify:

- [ ] Event form shows sessions table (not raw JSON)
- [ ] "Online Sessions" menu shows session rows, not events
- [ ] Group by Venue works in event tree
- [ ] Issue tags appear with colors in tree
- [ ] Quick-tag buttons work
- [ ] Migration populates existing events

---

*Ready for implementation on approval.*
