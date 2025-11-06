#!/usr/bin/env python3
"""
Startup Validation and Self-Healing System
==========================================
This script validates the application environment and automatically fixes common issues.
Exit codes:
  0 = All checks passed
  1 = Critical errors that cannot be auto-fixed
  2 = Warnings but system can run
"""

import sys
import os
import sqlite3
from pathlib import Path
from typing import List, Tuple, Optional
import subprocess
import shutil

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# ANSI color codes for terminal output
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def log_info(msg: str) -> None:
    print(f"{Colors.BLUE}[INFO] {msg}{Colors.RESET}")

def log_ok(msg: str) -> None:
    print(f"{Colors.GREEN}[OK] {msg}{Colors.RESET}")

def log_warn(msg: str) -> None:
    print(f"{Colors.YELLOW}[WARNING] {msg}{Colors.RESET}")

def log_error(msg: str) -> None:
    print(f"{Colors.RED}[ERROR] {msg}{Colors.RESET}")

def log_healing(msg: str) -> None:
    print(f"{Colors.BOLD}{Colors.BLUE}[HEALING] {msg}{Colors.RESET}")

def print_section(title: str) -> None:
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print(f"          {title.center(40)}           ")
    print(f"{'='*60}{Colors.RESET}\n")

# ============================================
# Validation and Healing Functions
# ============================================

def check_python_version() -> Tuple[bool, Optional[str]]:
    """Check Python version is 3.8+"""
    log_info("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        log_ok(f"Python {version.major}.{version.minor}.{version.micro}")
        return True, None
    else:
        log_error(f"Python {version.major}.{version.minor} is too old (need 3.8+)")
        return False, "Upgrade Python to 3.8 or higher"

def check_env_file() -> Tuple[bool, Optional[str]]:
    """Check .env file exists, auto-create from template if missing"""
    log_info("Checking environment file...")
    env_path = PROJECT_ROOT / ".env"
    env_example_path = PROJECT_ROOT / ".env.example"
    
    if env_path.exists():
        log_ok(f".env file found at {env_path}")
        return True, None
    
    # Auto-heal: create from example
    if env_example_path.exists():
        log_healing("Creating .env from .env.example template...")
        try:
            shutil.copy(env_example_path, env_path)
            log_ok(".env file created successfully")
            return True, "Created .env from template - please configure API keys"
        except Exception as e:
            log_error(f"Failed to create .env: {e}")
            return False, f"Manually copy .env.example to .env and configure it"
    
    log_error(".env file not found and no .env.example template available")
    return False, "Create .env file with required API keys"

def check_api_keys() -> Tuple[bool, Optional[str]]:
    """Check API key configuration"""
    log_info("Checking API key configuration...")
    env_path = PROJECT_ROOT / ".env"
    
    if not env_path.exists():
        log_warn("No .env file to check for API keys")
        return True, "Configure API keys in .env for full functionality"
    
    providers = {
        "GEMINI_API_KEY": "Gemini API (Primary)",
        "OPENAI_API_KEY": "OpenAI API",
        "ANTHROPIC_API_KEY": "Anthropic API",
    }
    
    configured = []
    with open(env_path, 'r') as f:
        env_content = f.read()
    
    for key, name in providers.items():
        if key in env_content:
            # Check if not empty/placeholder
            for line in env_content.split('\n'):
                if line.startswith(key) and '=' in line:
                    value = line.split('=', 1)[1].strip()
                    if value and value not in ['your-api-key-here', 'sk-...', '']:
                        configured.append(name)
                        break
    
    if configured:
        for provider in configured:
            log_ok(f"{provider} configured")
        if len(configured) == 1:
            return True, f"Only {configured[0]} configured - consider adding fallback providers"
        return True, None
    else:
        log_warn("No API keys configured")
        return True, "Configure at least one API key (GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY)"

def check_database_files() -> Tuple[bool, Optional[str]]:
    """Check database files exist and are readable"""
    log_info("Checking database files...")
    
    databases = {
        "app_data": PROJECT_ROOT / "app" / "data.db",
        "market": PROJECT_ROOT / "data" / "market.db",
        "auth": PROJECT_ROOT / "data" / "auth.db",
        "chat": PROJECT_ROOT / "data" / "chat.db",
    }
    
    all_ok = True
    for name, path in databases.items():
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            log_ok(f"{name}: {path} ({size_mb:.2f} MB)")
        else:
            log_warn(f"{name}: {path} does not exist - will be created on first run")
            # Auto-heal: Create parent directory if needed
            path.parent.mkdir(parents=True, exist_ok=True)
    
    return True, None

def validate_database_schema(db_path: Path, table_name: str, expected_columns: List[str]) -> Tuple[bool, List[str]]:
    """Validate and auto-fix database schema"""
    if not db_path.exists():
        return True, []  # Will be created later
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if not cursor.fetchone():
            conn.close()
            return False, [f"Table {table_name} does not exist"]
        
        # Get actual columns
        cursor.execute(f"PRAGMA table_info({table_name})")
        actual_columns = {row[1] for row in cursor.fetchall()}
        
        # Find missing columns
        missing_columns = [col for col in expected_columns if col not in actual_columns]
        
        conn.close()
        return True, missing_columns
    except Exception as e:
        return False, [f"Error checking schema: {e}"]

def auto_fix_database_schema(db_path: Path, table_name: str, column_name: str, column_def: str) -> bool:
    """Automatically add missing column to database"""
    try:
        log_healing(f"Adding column '{column_name}' to {table_name} in {db_path.name}...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_def}")
        conn.commit()
        conn.close()
        
        log_ok(f"Successfully added {column_name} to {table_name}")
        return True
    except Exception as e:
        log_error(f"Failed to add column: {e}")
        return False

def check_database_schemas() -> Tuple[bool, Optional[str]]:
    """Check and auto-fix database schemas"""
    log_info("Checking database schemas...")
    
    issues_fixed = 0
    critical_errors = []
    
    # Define expected schemas (flexible - only check critical columns)
    schemas = {
        "app/data.db": {
            "market_ticks": ["id", "sku"],  # Actual schema: id, sku, market, our_price, ts, etc.
            "product_catalog": ["sku", "owner_id", "current_price", "updated_at"],  # Actual schema uses sku as key
            "ingestion_jobs": ["id", "status"],  # May not have owner_id/url yet
            "price_proposals": ["id"],  # May have different schema
        },
        "data/market.db": {
            "market_data": ["id", "owner_id", "product_name", "price"],
        },
        "data/auth.db": {
            "users": ["id", "email", "hashed_password", "is_active", "two_factor_enabled"],
        },
        "data/chat.db": {
            "threads": ["id", "title", "created_at", "updated_at"],
            "messages": ["id", "thread_id", "role", "content", "created_at"],
        },
    }
    
    # Column definitions for auto-fixing
    column_definitions = {
        "updated_at": "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP",
        "two_factor_enabled": "two_factor_enabled BOOLEAN DEFAULT 0 NOT NULL",
        "source_url": "source_url TEXT",
    }
    
    for db_rel_path, tables in schemas.items():
        db_path = PROJECT_ROOT / db_rel_path
        
        for table_name, expected_columns in tables.items():
            is_valid, missing_or_errors = validate_database_schema(db_path, table_name, expected_columns)
            
            if not is_valid:
                log_error(f"{db_rel_path}.{table_name}: {missing_or_errors[0]}")
                critical_errors.append(f"{table_name} validation failed")
                continue
            
            if missing_or_errors:
                # Try to auto-fix missing columns
                for col in missing_or_errors:
                    if col in column_definitions:
                        success = auto_fix_database_schema(db_path, table_name, col, column_definitions[col])
                        if success:
                            issues_fixed += 1
                        else:
                            critical_errors.append(f"Failed to add {col} to {table_name}")
                    else:
                        log_warn(f"{db_rel_path}.{table_name}: Missing column '{col}' (no auto-fix available)")
                        critical_errors.append(f"{table_name}.{col} missing")
            else:
                log_ok(f"{db_rel_path}.{table_name} schema valid")
    
    if issues_fixed > 0:
        log_ok(f"Auto-fixed {issues_fixed} schema issue(s)")
    
    if critical_errors:
        return False, f"Schema errors: {', '.join(critical_errors[:3])}"
    
    return True, None

def check_critical_directories() -> Tuple[bool, Optional[str]]:
    """Check critical directories exist, create if missing"""
    log_info("Checking critical directories...")
    
    critical_dirs = [
        PROJECT_ROOT / "backend",
        PROJECT_ROOT / "frontend",
        PROJECT_ROOT / "core",
        PROJECT_ROOT / "data",
        PROJECT_ROOT / "app",
        PROJECT_ROOT / "scripts",
    ]
    
    for dir_path in critical_dirs:
        if dir_path.exists() and dir_path.is_dir():
            log_ok(f"Directory: {dir_path.name}/")
        else:
            log_healing(f"Creating missing directory: {dir_path.name}/")
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                log_ok(f"Created: {dir_path.name}/")
            except Exception as e:
                log_error(f"Failed to create {dir_path.name}/: {e}")
                return False, f"Cannot create required directory: {dir_path.name}"
    
    return True, None

def check_python_dependencies() -> Tuple[bool, Optional[str]]:
    """Check critical Python dependencies"""
    log_info("Checking Python dependencies...")
    
    critical_deps = {
        "fastapi": "FastAPI web framework",
        "uvicorn": "ASGI server",
        "aiosqlite": "Async SQLite driver",
        "pydantic": "Data validation",
    }
    
    missing = []
    for module, description in critical_deps.items():
        try:
            __import__(module)
            log_ok(f"{module} ({description})")
        except ImportError:
            missing.append(module)
            log_warn(f"{module} not found")
    
    if missing:
        return True, f"Missing packages: {', '.join(missing)} - run: pip install -r requirements.txt"
    
    return True, None

def auto_initialize_databases() -> bool:
    """Initialize databases if they don't exist"""
    log_info("Initializing databases if needed...")
    
    try:
        # Initialize chat database
        from core.chat_db import init_chat_db
        init_chat_db()
        
        # Initialize auth database
        from core.auth_db import init_db as init_auth_db
        init_auth_db()
        
        log_ok("Database initialization complete")
        return True
    except Exception as e:
        log_warn(f"Database initialization failed: {e}")
        return False

# ============================================
# Main Validation Flow
# ============================================

def main():
    print_section("Dynamic Pricing AI - Startup Validation")
    
    warnings = []
    errors = []
    healing_actions = []
    
    # Run all checks
    checks = [
        check_python_version,
        check_env_file,
        check_api_keys,
        check_database_files,
        check_database_schemas,
        check_critical_directories,
        check_python_dependencies,
    ]
    
    for check in checks:
        success, message = check()
        if not success:
            errors.append(message)
        elif message:
            warnings.append(message)
    
    # Try to auto-initialize databases
    auto_initialize_databases()
    
    # Print summary
    print_section("Validation Summary")
    
    if errors:
        log_error(f"{len(errors)} critical error(s) found:")
        for i, err in enumerate(errors, 1):
            print(f"  {i}. {err}")
        print(f"\n{Colors.RED}[ERROR] Critical errors prevent startup{Colors.RESET}")
        print(f"{Colors.BLUE}[INFO] Some issues may have been auto-fixed - try running again{Colors.RESET}")
        return 1
    
    if warnings:
        log_warn(f"{len(warnings)} warning(s) found:")
        for i, warn in enumerate(warnings, 1):
            print(f"  {i}. {warn}")
        print(f"\n{Colors.YELLOW}[WARNING] System can run but has warnings{Colors.RESET}")
        log_info("Consider addressing warnings for production deployment")
        return 2
    
    log_ok("All checks passed - system ready!")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[INFO] Validation cancelled by user")
        sys.exit(1)
    except Exception as e:
        log_error(f"Unexpected error during validation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
