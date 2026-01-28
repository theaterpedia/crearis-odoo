# Workspace Automation - Developer Documentation

*Created: 2026-01-27*  
*Workspace: crearis-odoo*

---

## Overview

This document describes how to automate Odoo development tasks in this workspace, including launching Odoo, running updates, and querying the database via terminal commands.

---

## Workspace Structure

```
/home/persona/crearis/odoo/
├── dev/
│   └── crearis-odoo/          # Project folder (custom modules)
│       ├── .vscode/
│       │   └── crearis-odoo.code-workspace
│       ├── crearis/
│       ├── agenda_dasei/
│       ├── crearis_agenda/
│       ├── crearis_event_package/
│       ├── graphql_theaterpedia/
│       └── .external/         # Git submodules
│           ├── partner-contact/
│           └── rest-framework/
├── versions/
│   └── 16.0/                  # Odoo source (odoo folder in workspace)
│       └── odoo/
│           └── odoo-bin
└── venv/
    └── 16.0/                  # Python virtual environment
        └── bin/python
```

---

## Key Configuration Variables

Defined in `.vscode/crearis-odoo.code-workspace` under `settings`:

| Variable | Value | Description |
|----------|-------|-------------|
| `odoo.module` | `crearis` | Current module being developed |
| `odoo.addonsPaths` | See below | Comma-separated addon paths |
| `odoo.logLevel` | `info` | Odoo log level |
| `odoo.templateDB` | `crearis-odoo` | Template database name |
| `odoo.templateAddons` | `crearis,_meta` | Modules for template DB |

### Addons Paths (resolved)

```
${workspaceFolder:project}/.external/partner-contact,
${workspaceFolder:project}/.external/rest-framework,
./odoo/addons,
${workspaceFolder:project}
```

**Absolute paths:**
```
/home/persona/crearis/odoo/dev/crearis-odoo/.external/partner-contact
/home/persona/crearis/odoo/dev/crearis-odoo/.external/rest-framework
/home/persona/crearis/odoo/versions/16.0/odoo/addons
/home/persona/crearis/odoo/dev/crearis-odoo
```

---

## VS Code Launch Configurations

### 1. Run (No Update)

**Use when:** Python code unchanged, only XML/view changes, or just want to restart.

```json
{
    "name": "Run",
    "type": "debugpy",
    "program": "./odoo/odoo-bin",
    "cwd": "${workspaceFolder:odoo}",
    "args": [
        "--dev=xml",
        "--database=crearis",
        "--addons-path=<paths>",
        "--log-level=info",
        "--limit-time-cpu=0",
        "--limit-time-real=0",
        "--max-cron-threads=1"
    ]
}
```

**Key behavior:**
- `--dev=xml` enables auto-reload of XML views on file save
- Does NOT run `--update`, so Python model changes won't apply until restart
- Fast startup, no module installation

### 2. Run + Update

**Use when:** Python code changed, new fields added, or module structure changed.

```json
{
    "name": "Run + Update",
    "preLaunchTask": "update module",
    "args": [/* same as Run */]
}
```

**Key behavior:**
- Runs `update module` task BEFORE launching Odoo
- The task executes `--update=crearis` with `--stop-after-init`
- Then launches Odoo normally
- **Use this after Python model changes**

### 3. Shell (with Update)

**Use when:** Need interactive Python shell AND want to update module first.

```json
{
    "name": "Shell",
    "args": [
        "shell",
        "--database=crearis",
        "--update=crearis",
        "--addons-path=<paths>"
    ]
}
```

**Note:** This runs `--update` which can be slow. Use "Shell (Fast)" for quick access.

### 4. Shell (Fast) ⭐ RECOMMENDED

**Use when:** Need quick interactive shell without waiting for module updates.

```json
{
    "name": "Shell (Fast)",
    "args": [
        "shell",
        "--database=crearis",
        "--addons-path=<paths>",
        "--no-http",
        "--max-cron-threads=0"
    ]
}
```

**Key behavior:**
- No `--update` flag = instant startup (~5 seconds vs ~30+ seconds)
- `--no-http` = don't start web server
- `--max-cron-threads=0` = don't start cron workers
- Use this for running diagnostic scripts, data queries, sync commands
- **Tip:** If paste doesn't work well, type commands directly or use smaller chunks

---

## Terminal Commands for Automation

### Python Environment

Always activate the virtual environment first:

```bash
source /home/persona/crearis/venv/16.0/bin/activate
```

Or use full path to Python:

```bash
/home/persona/crearis/venv/16.0/bin/python
```

### Run Odoo (equivalent to "Run" config)

```bash
cd /home/persona/crearis/odoo/versions/16.0

./odoo/odoo-bin \
    --dev=xml \
    --database=crearis \
    --addons-path=/home/persona/crearis/odoo/dev/crearis-odoo/.external/partner-contact,/home/persona/crearis/odoo/dev/crearis-odoo/.external/rest-framework,./odoo/addons,/home/persona/crearis/odoo/dev/crearis-odoo \
    --log-level=info \
    --limit-time-cpu=0 \
    --limit-time-real=0 \
    --max-cron-threads=1
```

### Update Module (equivalent to "Run + Update" pre-task)

```bash
cd /home/persona/crearis/odoo/versions/16.0

./odoo/odoo-bin \
    --database=crearis \
    --update=crearis \
    --addons-path=/home/persona/crearis/odoo/dev/crearis-odoo/.external/partner-contact,/home/persona/crearis/odoo/dev/crearis-odoo/.external/rest-framework,./odoo/addons,/home/persona/crearis/odoo/dev/crearis-odoo \
    --log-level=info \
    --stop-after-init \
    --max-cron-threads=1
```

### Update Specific Module(s)

```bash
./odoo/odoo-bin \
    --database=crearis \
    --update=agenda_dasei,crearis_agenda \
    --addons-path=<paths> \
    --stop-after-init
```

### Initialize Module from Scratch

```bash
./odoo/odoo-bin \
    --database=crearis \
    --init=my_new_module \
    --addons-path=<paths> \
    --stop-after-init
```

---

## Database Queries (psql)

### Connection

Default database: `crearis`

```bash
psql -d crearis
```

Or one-liner:

```bash
psql -d crearis -c "SELECT ..."
```

### Useful Queries

#### Check installed modules

```sql
SELECT name, state, latest_version 
FROM ir_module_module 
WHERE state = 'installed' 
AND name LIKE '%crearis%' OR name LIKE '%dasei%'
ORDER BY name;
```

#### Check websites / domain codes

```sql
SELECT id, name, domain_code, company_id 
FROM website 
ORDER BY domain_code;
```

#### Check event types

```sql
SELECT id, name, is_template_code, company_id 
FROM event_type 
ORDER BY name;
```

#### Check event stages

```sql
SELECT id, name, sequence, pipe_end 
FROM event_stage 
ORDER BY sequence;
```

#### View XML IDs for a module

```sql
SELECT name, model, res_id 
FROM ir_model_data 
WHERE module = 'agenda_dasei' 
ORDER BY model, name;
```

#### Delete cached views for a module (nuclear option)

```sql
-- Step 1: Delete views
DELETE FROM ir_ui_view 
WHERE id IN (
    SELECT res_id FROM ir_model_data 
    WHERE model = 'ir.ui.view' AND module = 'agenda_dasei'
);

-- Step 2: Delete model data references
DELETE FROM ir_model_data 
WHERE model = 'ir.ui.view' AND module = 'agenda_dasei';
```

#### Check for duplicate XML IDs

```sql
SELECT module, name, COUNT(*) 
FROM ir_model_data 
WHERE model = 'ir.ui.view'
GROUP BY module, name 
HAVING COUNT(*) > 1;
```

---

## VS Code Tasks Reference

Available tasks (run via `Ctrl+Shift+P` → "Tasks: Run Task"):

| Task | Description |
|------|-------------|
| `drop db` | Drop database `crearis` |
| `remove filestore` | Delete filestore for `crearis` |
| `create db from template` | Create `crearis` from template |
| `copy filestore` | Copy template filestore |
| `~Init DB From Template` | Full init from template (sequence) |
| `~Init DB` | Full init without demo data |
| `update module` | Update `crearis` module |
| `~Init Template DB` | Rebuild template database |
| `~Run Pre-Commit` | Run pre-commit checks |

Tasks starting with `~` are compound tasks that run multiple steps in sequence.

---

## Common Workflows

### 1. Quick restart (XML only changes)

1. Stop Odoo (Ctrl+C or stop debug)
2. Press F5 with "Run" config selected

### 2. Python code changed

1. Stop Odoo
2. Press F5 with "Run + Update" config selected
3. Or run terminal: `./odoo/odoo-bin --update=crearis --stop-after-init ...` then restart

### 3. New module or major changes

```bash
# Drop and recreate from template
psql -d postgres -c "DROP DATABASE IF EXISTS crearis;"
psql -d postgres -c "CREATE DATABASE crearis TEMPLATE \"crearis-odoo\";"
rm -rf ~/.local/share/Odoo/filestore/crearis
cp -r ~/.local/share/Odoo/filestore/crearis-odoo ~/.local/share/Odoo/filestore/crearis

# Initialize
./odoo/odoo-bin --database=crearis --init=crearis --addons-path=<paths> --stop-after-init
```

### 4. Fix broken views / module state

```bash
# Delete cached views
psql -d crearis -c "DELETE FROM ir_ui_view WHERE id IN (SELECT res_id FROM ir_model_data WHERE model = 'ir.ui.view' AND module = 'my_module');"
psql -d crearis -c "DELETE FROM ir_model_data WHERE model = 'ir.ui.view' AND module = 'my_module';"

# Re-update
./odoo/odoo-bin --database=crearis --update=my_module --stop-after-init ...
```

### 5. Check if module will load without running server

```bash
./odoo/odoo-bin \
    --database=crearis \
    --update=crearis \
    --addons-path=<paths> \
    --stop-after-init \
    --log-level=warning
```

If no errors, module is valid.

---

## Troubleshooting

### "Invalid xmlid" errors on startup

**Cause:** View inheritance conflict, often after updating external modules.

**Fix:**
1. Check for duplicate XML IDs: `SELECT module, name, COUNT(*) FROM ir_model_data WHERE model='ir.ui.view' GROUP BY module, name HAVING COUNT(*) > 1;`
2. Rename conflicting XML IDs in your module
3. Add `mode="extension"` to view inheritance if appropriate
4. Delete cached views and re-update

### Module won't update

**Cause:** Python syntax error or import error.

**Fix:**
1. Check Odoo logs for traceback
2. Run `python -m py_compile my_module/models/file.py` to check syntax
3. Fix error and retry

### "FATAL: database does not exist"

**Fix:**
```bash
psql -d postgres -c "CREATE DATABASE crearis;"
./odoo/odoo-bin --database=crearis --init=base,crearis --addons-path=<paths> --stop-after-init
```

---

## Environment Variables

For automation scripts:

```bash
export ODOO_DB="crearis"
export ODOO_ADDONS="/home/persona/crearis/odoo/dev/crearis-odoo/.external/partner-contact,/home/persona/crearis/odoo/dev/crearis-odoo/.external/rest-framework,/home/persona/crearis/odoo/versions/16.0/odoo/addons,/home/persona/crearis/odoo/dev/crearis-odoo"
export ODOO_BIN="/home/persona/crearis/odoo/versions/16.0/odoo/odoo-bin"

# Then use:
$ODOO_BIN --database=$ODOO_DB --addons-path=$ODOO_ADDONS --update=crearis --stop-after-init
```

---

*Last updated: 2026-01-27*
