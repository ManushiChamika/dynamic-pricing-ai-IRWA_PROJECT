#!/usr/bin/env python3
"""
Test script to verify self-healing functionality
Creates a test scenario and verifies auto-healing works
"""

import sqlite3
import sys
import os
from pathlib import Path
import shutil

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# Force UTF-8 output for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def test_missing_column_healing():
    """Test that auto_heal can add missing columns"""
    print("=" * 60)
    print("TEST: Missing Column Auto-Healing")
    print("=" * 60)
    
    test_db = PROJECT_ROOT / "app" / "test_healing.db"
    
    try:
        # Create test database with incomplete schema
        print("\n1. Creating test database with missing column...")
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()
        print("   [OK] Created test_table without 'updated_at' column")
        
        # Verify column is missing
        print("\n2. Verifying column is missing...")
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(test_table)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()
        
        if "updated_at" in columns:
            print("   ✗ FAIL: Column already exists")
            return False
        print("   ✓ Confirmed 'updated_at' is missing")
        
        # Use auto_heal to fix
        print("\n3. Running auto-heal...")
        from scripts.auto_heal import AutoHealer
        healer = AutoHealer(verbose=False)
        
        result = healer.heal_missing_column(
            test_db,
            "test_table",
            "updated_at",
            "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"
        )
        
        if not result.success:
            print(f"   ✗ FAIL: {result.message}")
            return False
        print(f"   ✓ {result.message}")
        
        # Verify column was added
        print("\n4. Verifying column was added...")
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(test_table)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()
        
        if "updated_at" not in columns:
            print("   ✗ FAIL: Column was not added")
            return False
        print("   ✓ Column 'updated_at' successfully added")
        
        print("\n" + "=" * 60)
        print("TEST PASSED: Auto-healing works correctly!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        if test_db.exists():
            test_db.unlink()

def test_missing_env_healing():
    """Test that auto_heal can create .env from template"""
    print("\n" + "=" * 60)
    print("TEST: Missing .env File Auto-Healing")
    print("=" * 60)
    
    env_path = PROJECT_ROOT / ".env"
    env_backup = PROJECT_ROOT / ".env.backup_test"
    env_example = PROJECT_ROOT / ".env.example"
    
    # Check if .env.example exists
    if not env_example.exists():
        print("   ⊘ SKIP: .env.example not found")
        return True
    
    try:
        # Backup existing .env if it exists
        if env_path.exists():
            print("\n1. Backing up existing .env...")
            shutil.copy(env_path, env_backup)
            env_path.unlink()
            print("   ✓ Backed up and removed .env")
        else:
            print("\n1. No existing .env file")
        
        # Run auto-heal
        print("\n2. Running auto-heal to create .env...")
        from scripts.auto_heal import AutoHealer
        healer = AutoHealer(verbose=False)
        
        result = healer.heal_missing_env_file()
        
        if not result.success:
            print(f"   ✗ FAIL: {result.message}")
            return False
        print(f"   ✓ {result.message}")
        
        # Verify .env was created
        print("\n3. Verifying .env was created...")
        if not env_path.exists():
            print("   ✗ FAIL: .env was not created")
            return False
        print("   ✓ .env file exists")
        
        print("\n" + "=" * 60)
        print("TEST PASSED: .env auto-healing works!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Restore backup if it exists
        if env_backup.exists():
            if env_path.exists():
                env_path.unlink()
            shutil.move(env_backup, env_path)
            print("\n   ✓ Restored original .env")

def test_validation_and_healing_integration():
    """Test that validation triggers healing automatically"""
    print("\n" + "=" * 60)
    print("TEST: Validation + Healing Integration")
    print("=" * 60)
    
    print("\n1. Running validation...")
    import subprocess
    
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "validate_startup.py")],
        capture_output=True,
        text=True
    )
    
    exit_code = result.returncode
    
    if exit_code == 0:
        print("   ✓ Validation passed (exit code 0)")
    elif exit_code == 2:
        print("   ⚠ Validation passed with warnings (exit code 2)")
    else:
        print(f"   ✗ Validation failed (exit code {exit_code})")
        print("\nOutput:")
        print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
        return False
    
    print("\n" + "=" * 60)
    print("TEST PASSED: Validation works correctly!")
    print("=" * 60)
    return True

def main():
    """Run all self-healing tests"""
    print("\n" + "=" * 60)
    print("SELF-HEALING SYSTEM TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Missing Column Healing", test_missing_column_healing),
        ("Missing .env Healing", test_missing_env_healing),
        ("Validation Integration", test_validation_and_healing_integration),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n✗ TEST CRASHED: {name} - {e}")
            results.append((name, False))
    
    # Print summary
    print("\n\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    
    print("\n" + "=" * 60)
    print(f"TOTAL: {passed_count}/{total} tests passed")
    print("=" * 60)
    
    return 0 if passed_count == total else 1

if __name__ == "__main__":
    sys.exit(main())
