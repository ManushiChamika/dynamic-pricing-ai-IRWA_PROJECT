# Self-Healing System Documentation

## Overview

The Dynamic Pricing AI codebase now has a comprehensive self-healing system that automatically detects and fixes common issues without human intervention.

## Components

### 1. `scripts/validate_startup.py`
**Purpose**: Validates the application environment and auto-fixes issues during validation

**Features**:
- Checks Python version (3.8+)
- Validates .env file exists (creates from template if missing)
- Checks API key configuration
- Validates database files exist
- **Auto-fixes database schemas** (adds missing columns, tables)
- Creates missing directories
- Checks Python dependencies
- Auto-initializes databases

**Exit Codes**:
- `0` = All checks passed
- `1` = Critical errors (some may be fixed, re-run to verify)
- `2` = Warnings only (system can run)

**Usage**:
```bash
python scripts/validate_startup.py
```

### 2. `scripts/auto_heal.py`
**Purpose**: Dedicated auto-healing module that can be run independently

**Features**:
- Creates missing databases
- Adds missing tables
- Adds missing columns
- Creates missing indexes
- Creates .env from template
- Creates missing directories
- Installs Python packages (optional)
- Installs Node.js packages (optional)

**Usage**:
```bash
# Run all healing operations
python scripts/auto_heal.py

# Quiet mode (less verbose)
python scripts/auto_heal.py --quiet

# Only heal databases
python scripts/auto_heal.py --db-only

# Only heal file system
python scripts/auto_heal.py --fs-only
```

### 3. `run_full_app.bat` Integration
**Purpose**: Launcher automatically runs validation and healing

**Behavior**:
1. Runs `validate_startup.py`
2. If validation fails, automatically runs `auto_heal.py`
3. Re-runs validation after healing
4. Only prompts user if issues remain after auto-healing

## Auto-Fixable Issues

### Database Issues ✅
- **Missing database files** → Creates empty database
- **Missing tables** → Creates tables with proper schema
- **Missing columns** → Adds columns with proper type/defaults
  - `product_catalog.updated_at`
  - `product_catalog.source_url`
  - `threads.updated_at`
  - `users.two_factor_enabled`
  - `users.totp_secret`
- **Missing indexes** → Creates performance indexes

### File System Issues ✅
- **Missing .env file** → Copies from .env.example
- **Missing directories** → Creates: data/, app/, backend/, frontend/, core/, scripts/

### Schema Auto-Fixes

The system knows the expected schema for all databases:

#### app/data.db
- Tables: `product_catalog`, `market_ticks`, `price_proposals`, `ingestion_jobs`
- Columns: Ensures `updated_at`, `source_url` exist

#### data/auth.db
- Tables: `users`, `session_tokens`
- Columns: Ensures `two_factor_enabled`, `totp_secret` exist

#### data/chat.db
- Tables: `threads`, `messages`, `summaries`
- Columns: Ensures `updated_at` exists in threads

#### data/market.db
- Tables: `market_data`, `pricing_list`

## Non-Auto-Fixable Issues ⚠️

These require manual intervention:

1. **Missing API keys** → Configure in .env
2. **Missing Python packages** → Run: `pip install -r requirements.txt`
3. **Missing Node modules** → Run: `cd frontend && npm install`
4. **File permission errors** → Fix OS permissions
5. **Corrupt database files** → Restore from backup or recreate

## How It Works

### Detection Flow
```
validate_startup.py
├─ Check Python version
├─ Check .env exists → Auto-create if missing
├─ Check API keys → Warn if missing
├─ Check databases exist
├─ Check database schemas
│  ├─ For each table
│  │  ├─ Check exists → Auto-create if missing
│  │  └─ Check columns → Auto-add if missing
│  └─ Log all actions
├─ Check directories → Auto-create if missing
└─ Return status code
```

### Healing Flow
```
auto_heal.py
├─ File System Healing
│  ├─ Create .env from template
│  └─ Create missing directories
├─ Database Healing
│  ├─ Create missing databases
│  ├─ Create missing tables
│  ├─ Add missing columns
│  └─ Create missing indexes
└─ Report summary
```

### Launcher Integration
```
run_full_app.bat
├─ Run validate_startup.py
├─ If failed (exit 1):
│  ├─ Run auto_heal.py
│  ├─ Retry validate_startup.py
│  └─ Continue if now passes
├─ If warnings (exit 2):
│  └─ Prompt user to continue
└─ Start application
```

## Examples

### Example 1: Missing Column
```
[INFO] Checking database schemas...
[HEALING] Adding column 'updated_at' to product_catalog in data.db...
[OK] Successfully added updated_at to product_catalog
[OK] app/data.db.product_catalog schema valid
```

### Example 2: Missing .env
```
[INFO] Checking environment file...
[HEALING] Creating .env from .env.example template...
[OK] .env file created successfully
[WARNING] Configure API keys in .env for full functionality
```

### Example 3: Complete Auto-Heal
```
$ python scripts/auto_heal.py

Running comprehensive auto-healing...
[AUTO-HEAL] === File System Healing ===
[AUTO-HEAL] Creating .env from .env.example
[AUTO-HEAL] === Database Healing ===
[AUTO-HEAL] Adding column updated_at to product_catalog in data.db
[AUTO-HEAL] Adding column two_factor_enabled to users in auth.db
[AUTO-HEAL] Creating table market_ticks in data.db

============================================================
                    HEALING SUMMARY
============================================================

FILESYSTEM:
  ✓ Created .env from template - Copied .env.example to .env
  ✓ Directory data/ already exists
  ✓ Directory app/ already exists

DATABASES:
  ✓ Added updated_at to product_catalog - ALTER TABLE product_catalog ADD COLUMN updated_at DATETIME
  ✓ Added two_factor_enabled to users - ALTER TABLE users ADD COLUMN two_factor_enabled BOOLEAN DEFAULT 0
  ✓ Created table market_ticks - Created market_ticks

============================================================
Total: 6 successful, 0 failed, 4 actions taken
============================================================
```

## Adding New Auto-Fixes

To add a new auto-fixable issue:

### 1. Add to validate_startup.py
```python
def check_new_feature() -> Tuple[bool, Optional[str]]:
    """Check and auto-fix new feature"""
    log_info("Checking new feature...")
    
    if issue_detected:
        log_healing("Fixing issue...")
        # Auto-fix code here
        log_ok("Issue fixed")
        return True, None
    
    log_ok("Feature OK")
    return True, None
```

### 2. Add to auto_heal.py
```python
def heal_new_issue(self) -> HealingResult:
    """Fix new issue"""
    try:
        self.log("Fixing new issue...")
        # Fix code here
        return HealingResult(True, "Fixed", "Action taken")
    except Exception as e:
        return HealingResult(False, f"Failed: {e}")
```

### 3. Update schema definitions
Edit the `schemas` dict in `auto_heal.py`:
```python
schemas = {
    "app/data.db": {
        "columns": {
            "new_table": [
                ("new_column", "new_column TEXT DEFAULT ''"),
            ]
        }
    }
}
```

## Testing

### Test Auto-Healing
```bash
# Backup databases first
cp app/data.db app/data.db.backup

# Remove a column to test (requires manual SQL)
sqlite3 app/data.db "ALTER TABLE product_catalog DROP COLUMN updated_at"

# Run auto-heal
python scripts/auto_heal.py

# Verify fix
sqlite3 app/data.db "PRAGMA table_info(product_catalog)"
```

### Test Validation
```bash
# Remove .env to test
mv .env .env.backup

# Run validation (should auto-create .env)
python scripts/validate_startup.py

# Verify
ls -la .env
```

## Benefits

1. **Reduced Setup Time**: New developers don't need to manually fix schema issues
2. **Database Migration**: Automatically applies schema changes without migration scripts
3. **Resilience**: System recovers from common configuration issues
4. **Zero Downtime**: Fixes issues during startup before application runs
5. **Audit Trail**: All healing actions are logged

## Limitations

- Cannot fix corrupt database files (requires backup restore)
- Cannot configure API keys (security reasons)
- Cannot fix network/firewall issues
- Cannot fix OS-level permission problems
- Limited to predefined schema fixes

## Maintenance

The self-healing system requires updates when:
- New database tables are added
- New columns are added to existing tables
- New configuration files are required
- New directories are needed

Update both `validate_startup.py` and `auto_heal.py` to keep schemas in sync.
