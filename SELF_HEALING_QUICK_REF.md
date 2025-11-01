# Self-Healing Quick Reference

## What Was Implemented

Your codebase now has a **fully automated self-healing system** that detects and fixes issues without human intervention.

## Files Created

1. **`scripts/validate_startup.py`** - Validates environment and auto-fixes issues
2. **`scripts/auto_heal.py`** - Dedicated healing module (can run independently)
3. **`scripts/test_self_healing.py`** - Test suite to verify healing works
4. **`docs/SELF_HEALING_SYSTEM.md`** - Complete documentation

## Files Modified

1. **`run_full_app.bat`** - Integrated auto-healing into launcher (lines 185-224)

## What Gets Auto-Fixed

### ✅ Automatically Fixed (No User Action Needed)

1. **Missing .env file** → Creates from .env.example template
2. **Missing directories** → Creates: data/, app/, backend/, frontend/, core/, scripts/
3. **Missing database files** → Creates empty databases
4. **Missing database tables** → Creates with proper schema
5. **Missing database columns** → Adds columns with correct types:
   - `product_catalog.updated_at` (DATETIME)
   - `product_catalog.source_url` (TEXT)
   - `threads.updated_at` (DATETIME)
   - `users.two_factor_enabled` (BOOLEAN)
   - `users.totp_secret` (TEXT)
6. **Missing database indexes** → Creates performance indexes
7. **Database initialization** → Runs init scripts automatically

### ⚠️ Warns But Can't Fix (User Action May Be Needed)

1. **Missing API keys** → User must add to .env
2. **Multiple provider fallbacks** → Optional, warns if only 1 provider configured
3. **Python packages** → Must run: `pip install -r requirements.txt`
4. **Node modules** → Must run: `cd frontend && npm install`

## How to Use

### Automatic (Recommended)
Just run the launcher - it handles everything:
```batch
run_full_app.bat
```

The launcher will:
1. Run validation
2. If issues found → Run auto-heal
3. Re-run validation
4. Start app if successful

### Manual Validation
```bash
python scripts/validate_startup.py
```
Exit codes:
- `0` = All good
- `1` = Critical errors (may be fixed, re-run)
- `2` = Warnings only (can proceed)

### Manual Healing
```bash
# Fix everything
python scripts/auto_heal.py

# Only databases
python scripts/auto_heal.py --db-only

# Only file system
python scripts/auto_heal.py --fs-only

# Quiet mode
python scripts/auto_heal.py --quiet
```

### Test the System
```bash
python scripts/test_self_healing.py
```
This runs 3 tests to verify healing works correctly.

## Example Scenarios

### Scenario 1: New Developer Setup
```
1. Clone repository
2. Run run_full_app.bat
   → Auto-creates .env from template
   → Auto-creates all directories
   → Auto-initializes databases
   → Starts application
3. Done! (Just need to add API keys)
```

### Scenario 2: Database Schema Change
```
1. You add a new column to code: product.source_url
2. Run application
   → Validator detects missing column
   → Auto-healer adds column to database
   → Application starts normally
3. No manual migration needed!
```

### Scenario 3: Corrupted Database
```
1. Someone deletes updated_at column
2. Run application
   → Validator detects missing column
   → Auto-healer adds it back
   → Application starts normally
3. System self-repaired!
```

## Benefits

- **Zero Setup Time**: New devs can start immediately
- **Self-Repairing**: Recovers from common issues automatically
- **Migration-Free**: Schema changes applied automatically
- **Audit Trail**: All actions logged to app_launcher.log
- **Safe**: Only fixes known, safe issues
- **Tested**: All features verified with test suite

## Logs

Check `app_launcher.log` for detailed healing actions:
```batch
type app_launcher.log
```

## Adding New Auto-Fixes

Edit both files to keep in sync:

1. **`validate_startup.py`** - Add detection + fixing in `check_database_schemas()`
2. **`auto_heal.py`** - Add to `schemas` dict in `heal_all_database_schemas()`

Example:
```python
# In auto_heal.py schemas dict:
"app/data.db": {
    "columns": {
        "my_table": [
            ("new_column", "new_column TEXT DEFAULT ''"),
        ]
    }
}
```

## Maintenance

Update the system when you:
- Add new database tables
- Add new columns to existing tables
- Add new required configuration files
- Add new required directories

The system is designed to grow with your codebase!
