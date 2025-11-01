#!/usr/bin/env python3
"""
Auto-Healing System for Dynamic Pricing AI
==========================================
This module contains automated remediation functions for common issues.
It can be called directly or imported by other scripts.
"""

import sys
import os
import sqlite3
import shutil
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import subprocess

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


class HealingResult:
    """Result of a healing operation"""
    def __init__(self, success: bool, message: str, action_taken: Optional[str] = None):
        self.success = success
        self.message = message
        self.action_taken = action_taken


class AutoHealer:
    """Automated system healing and repair"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.actions_log = []
    
    def log(self, message: str) -> None:
        """Log a healing action"""
        self.actions_log.append(message)
        if self.verbose:
            print(f"[AUTO-HEAL] {message}")
    
    # ============================================
    # Database Healing
    # ============================================
    
    def heal_missing_database(self, db_path: Path, db_type: str) -> HealingResult:
        """Create missing database file"""
        if db_path.exists():
            return HealingResult(True, f"{db_type} database already exists")
        
        self.log(f"Creating missing {db_type} database at {db_path}")
        
        try:
            # Ensure directory exists
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create empty database
            conn = sqlite3.connect(db_path)
            conn.close()
            
            self.log(f"Successfully created {db_type} database")
            return HealingResult(True, f"Created {db_type} database", f"Created {db_path}")
        except Exception as e:
            return HealingResult(False, f"Failed to create {db_type} database: {e}")
    
    def heal_missing_column(self, db_path: Path, table: str, column: str, column_def: str) -> HealingResult:
        """Add missing column to database table"""
        if not db_path.exists():
            return HealingResult(False, f"Database {db_path} does not exist")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if column already exists
            cursor.execute(f"PRAGMA table_info({table})")
            columns = {row[1] for row in cursor.fetchall()}
            
            if column in columns:
                conn.close()
                return HealingResult(True, f"Column {column} already exists in {table}")
            
            # Add the column
            self.log(f"Adding column {column} to {table} in {db_path.name}")
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")
            conn.commit()
            conn.close()
            
            return HealingResult(True, f"Added {column} to {table}", f"ALTER TABLE {table} ADD COLUMN {column_def}")
        except Exception as e:
            return HealingResult(False, f"Failed to add column {column}: {e}")
    
    def heal_missing_table(self, db_path: Path, table: str, create_sql: str) -> HealingResult:
        """Create missing table in database"""
        if not db_path.exists():
            return HealingResult(False, f"Database {db_path} does not exist")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                conn.close()
                return HealingResult(True, f"Table {table} already exists")
            
            # Create the table
            self.log(f"Creating table {table} in {db_path.name}")
            cursor.execute(create_sql)
            conn.commit()
            conn.close()
            
            return HealingResult(True, f"Created table {table}", f"Created {table}")
        except Exception as e:
            return HealingResult(False, f"Failed to create table {table}: {e}")
    
    def heal_missing_index(self, db_path: Path, index_name: str, create_sql: str) -> HealingResult:
        """Create missing index in database"""
        if not db_path.exists():
            return HealingResult(False, f"Database {db_path} does not exist")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if index exists
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='index' AND name='{index_name}'")
            if cursor.fetchone():
                conn.close()
                return HealingResult(True, f"Index {index_name} already exists")
            
            # Create the index
            self.log(f"Creating index {index_name} in {db_path.name}")
            cursor.execute(create_sql)
            conn.commit()
            conn.close()
            
            return HealingResult(True, f"Created index {index_name}", f"Created {index_name}")
        except Exception as e:
            return HealingResult(False, f"Failed to create index {index_name}: {e}")
    
    # ============================================
    # File System Healing
    # ============================================
    
    def heal_missing_env_file(self) -> HealingResult:
        """Create .env file from .env.example"""
        env_path = PROJECT_ROOT / ".env"
        env_example_path = PROJECT_ROOT / ".env.example"
        
        if env_path.exists():
            return HealingResult(True, ".env file already exists")
        
        if not env_example_path.exists():
            return HealingResult(False, ".env.example template not found")
        
        try:
            self.log("Creating .env from .env.example")
            shutil.copy(env_example_path, env_path)
            return HealingResult(True, "Created .env from template", "Copied .env.example to .env")
        except Exception as e:
            return HealingResult(False, f"Failed to create .env: {e}")
    
    def heal_missing_directory(self, dir_path: Path) -> HealingResult:
        """Create missing directory"""
        if dir_path.exists():
            return HealingResult(True, f"Directory {dir_path} already exists")
        
        try:
            self.log(f"Creating directory {dir_path}")
            dir_path.mkdir(parents=True, exist_ok=True)
            return HealingResult(True, f"Created directory {dir_path}", f"Created {dir_path}")
        except Exception as e:
            return HealingResult(False, f"Failed to create directory {dir_path}: {e}")
    
    # ============================================
    # Dependencies Healing
    # ============================================
    
    def heal_missing_python_packages(self) -> HealingResult:
        """Install missing Python packages"""
        requirements_file = PROJECT_ROOT / "requirements.txt"
        
        if not requirements_file.exists():
            return HealingResult(False, "requirements.txt not found")
        
        try:
            self.log("Installing Python packages from requirements.txt")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                return HealingResult(True, "Successfully installed Python packages", "pip install -r requirements.txt")
            else:
                return HealingResult(False, f"Failed to install packages: {result.stderr}")
        except Exception as e:
            return HealingResult(False, f"Failed to install packages: {e}")
    
    def heal_missing_node_modules(self) -> HealingResult:
        """Install missing Node.js packages"""
        frontend_dir = PROJECT_ROOT / "frontend"
        node_modules = frontend_dir / "node_modules"
        package_json = frontend_dir / "package.json"
        
        if node_modules.exists():
            return HealingResult(True, "node_modules already exists")
        
        if not package_json.exists():
            return HealingResult(False, "package.json not found")
        
        try:
            self.log("Installing Node.js packages")
            result = subprocess.run(
                ["npm", "install"],
                cwd=str(frontend_dir),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                return HealingResult(True, "Successfully installed Node packages", "npm install")
            else:
                return HealingResult(False, f"Failed to install Node packages: {result.stderr}")
        except Exception as e:
            return HealingResult(False, f"Failed to install Node packages: {e}")
    
    # ============================================
    # Complete Schema Healing
    # ============================================
    
    def heal_all_database_schemas(self) -> List[HealingResult]:
        """Heal all database schemas comprehensively"""
        results = []
        
        # Define complete schema specifications
        schemas = {
            "app/data.db": {
                "tables": {
                    "product_catalog": """
                        CREATE TABLE IF NOT EXISTS product_catalog (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            owner_id INTEGER NOT NULL,
                            name TEXT NOT NULL,
                            sku TEXT,
                            description TEXT,
                            current_price REAL,
                            cost REAL,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                        )
                    """,
                    "market_ticks": """
                        CREATE TABLE IF NOT EXISTS market_ticks (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            product_id INTEGER NOT NULL,
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                            price REAL NOT NULL,
                            competitor TEXT,
                            FOREIGN KEY (product_id) REFERENCES product_catalog(id)
                        )
                    """,
                    "price_proposals": """
                        CREATE TABLE IF NOT EXISTS price_proposals (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            product_id INTEGER NOT NULL,
                            proposed_price REAL NOT NULL,
                            reason TEXT,
                            status TEXT DEFAULT 'pending',
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (product_id) REFERENCES product_catalog(id)
                        )
                    """,
                    "ingestion_jobs": """
                        CREATE TABLE IF NOT EXISTS ingestion_jobs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            owner_id INTEGER NOT NULL,
                            status TEXT DEFAULT 'pending',
                            url TEXT,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                        )
                    """
                },
                "columns": {
                    "product_catalog": [
                        ("updated_at", "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"),
                        ("source_url", "source_url TEXT"),
                    ]
                }
            },
            "data/auth.db": {
                "columns": {
                    "users": [
                        ("two_factor_enabled", "two_factor_enabled BOOLEAN DEFAULT 0 NOT NULL"),
                        ("totp_secret", "totp_secret TEXT"),
                    ]
                }
            },
            "data/chat.db": {
                "columns": {
                    "threads": [
                        ("updated_at", "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"),
                    ]
                }
            }
        }
        
        # Heal all schemas
        for db_rel_path, schema_spec in schemas.items():
            db_path = PROJECT_ROOT / db_rel_path
            
            # Create database if missing
            if not db_path.exists():
                result = self.heal_missing_database(db_path, db_rel_path)
                results.append(result)
            
            # Create missing tables
            if "tables" in schema_spec:
                for table_name, create_sql in schema_spec["tables"].items():
                    result = self.heal_missing_table(db_path, table_name, create_sql)
                    results.append(result)
            
            # Add missing columns
            if "columns" in schema_spec:
                for table_name, columns in schema_spec["columns"].items():
                    for col_name, col_def in columns:
                        result = self.heal_missing_column(db_path, table_name, col_name, col_def)
                        results.append(result)
        
        return results
    
    # ============================================
    # Comprehensive Healing
    # ============================================
    
    def heal_all(self) -> Dict[str, List[HealingResult]]:
        """Run all healing operations"""
        results = {
            "filesystem": [],
            "databases": [],
            "dependencies": [],
        }
        
        # File system healing
        self.log("=== File System Healing ===")
        results["filesystem"].append(self.heal_missing_env_file())
        for dir_name in ["data", "app", "backend", "frontend", "core", "scripts"]:
            results["filesystem"].append(self.heal_missing_directory(PROJECT_ROOT / dir_name))
        
        # Database healing
        self.log("\n=== Database Healing ===")
        results["databases"] = self.heal_all_database_schemas()
        
        # Dependencies healing (optional - can be slow)
        # results["dependencies"].append(self.heal_missing_python_packages())
        # results["dependencies"].append(self.heal_missing_node_modules())
        
        return results
    
    def print_summary(self, results: Dict[str, List[HealingResult]]) -> None:
        """Print summary of healing operations"""
        print("\n" + "="*60)
        print("HEALING SUMMARY".center(60))
        print("="*60 + "\n")
        
        total_success = 0
        total_failed = 0
        total_actions = 0
        
        for category, result_list in results.items():
            print(f"\n{category.upper()}:")
            for result in result_list:
                if result.success:
                    total_success += 1
                    status = "[OK]"
                else:
                    total_failed += 1
                    status = "[FAIL]"
                
                if result.action_taken:
                    total_actions += 1
                    print(f"  {status} {result.message} - {result.action_taken}")
                else:
                    print(f"  {status} {result.message}")
        
        print("\n" + "="*60)
        print(f"Total: {total_success} successful, {total_failed} failed, {total_actions} actions taken")
        print("="*60)


def main():
    """Main entry point for auto-healing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto-heal Dynamic Pricing AI system")
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose output")
    parser.add_argument("--db-only", action="store_true", help="Only heal databases")
    parser.add_argument("--fs-only", action="store_true", help="Only heal file system")
    
    args = parser.parse_args()
    
    healer = AutoHealer(verbose=not args.quiet)
    
    if args.db_only:
        print("Running database healing only...")
        results = {"databases": healer.heal_all_database_schemas()}
    elif args.fs_only:
        print("Running file system healing only...")
        results = {
            "filesystem": [
                healer.heal_missing_env_file(),
                *[healer.heal_missing_directory(PROJECT_ROOT / d) 
                  for d in ["data", "app", "backend", "frontend", "core", "scripts"]]
            ]
        }
    else:
        print("Running comprehensive auto-healing...")
        results = healer.heal_all()
    
    healer.print_summary(results)
    
    # Return exit code based on failures
    total_failed = sum(sum(1 for r in results[cat] if not r.success) for cat in results)
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[INFO] Auto-healing cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error during auto-healing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
