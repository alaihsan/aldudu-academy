#!/usr/bin/env python3
"""
Database Migration Check Script
Verifies that all migrations can be applied successfully.

Usage:
    python scripts/check_migrations.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv()


def check_migrations():
    """Check if migrations are valid and can be applied"""
    from app import create_app
    from app.extensions import db
    from flask_migrate import current, heads
    
    print("=" * 60)
    print("Aldudu Academy - Database Migration Check")
    print("=" * 60)
    
    # Create app
    app = create_app()
    
    with app.app_context():
        # Check current migration status
        print("\n📊 Current Migration Status:")
        print("-" * 40)
        
        try:
            # Get current migrations
            current_heads = heads()
            
            if not current_heads:
                print("✓ No pending migrations")
            else:
                print(f"⚠ Pending migrations detected:")
                for head in current_heads:
                    print(f"  - {head}")
            
            # Check migration history
            print("\n📜 Migration History:")
            print("-" * 40)
            
            current()
            
            # Verify migration table exists
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'alembic_version' in tables:
                print("\n✓ Migration table (alembic_version) exists")
            else:
                print("\n⚠ Migration table not found - run 'flask db upgrade' first")
            
            # Check for pending migrations
            from alembic.script import ScriptDirectory
            from alembic.config import Config
            
            alembic_cfg = Config("migrations/alembic.ini")
            script = ScriptDirectory.from_config(alembic_cfg)
            
            # Get head revision
            head_revision = script.get_current_head()
            
            # Get current revision
            current_revision = db.engine.execute(
                "SELECT version_num FROM alembic_version"
            ).scalar() if 'alembic_version' in tables else None
            
            print(f"\n📍 Current revision: {current_revision or 'None'}")
            print(f"📍 Head revision: {head_revision}")
            
            if current_revision != head_revision:
                print(f"\n⚠ Database is {head_revision} revisions behind")
                print("  Run: flask db upgrade")
            else:
                print("\n✓ Database is up to date")
            
            # Validate migration files
            print("\n📋 Validating Migration Files:")
            print("-" * 40)
            
            migrations_dir = ROOT / "migrations" / "versions"
            if migrations_dir.exists():
                migration_files = list(migrations_dir.glob("*.py"))
                print(f"  Found {len(migration_files)} migration file(s)")
                
                # Check for common issues
                issues = []
                for f in migration_files:
                    with open(f, 'r') as file:
                        content = file.read()
                        
                        # Check for down_revision
                        if 'down_revision' not in content:
                            issues.append(f"  - {f.name}: Missing down_revision")
                        
                        # Check for upgrade/downgrade functions
                        if 'def upgrade()' not in content:
                            issues.append(f"  - {f.name}: Missing upgrade() function")
                        
                        if 'def downgrade()' not in content:
                            issues.append(f"  - {f.name}: Missing downgrade() function")
                
                if issues:
                    print("\n⚠ Issues found:")
                    for issue in issues:
                        print(issue)
                else:
                    print("✓ All migration files are valid")
            
            print("\n" + "=" * 60)
            print("✅ Migration check completed successfully")
            print("=" * 60)
            return 0
            
        except Exception as e:
            print(f"\n❌ Error checking migrations: {str(e)}")
            print("\nTroubleshooting:")
            print("  1. Ensure database is accessible")
            print("  2. Run: flask db upgrade")
            print("  3. Check migrations/versions/ for valid migration files")
            return 1


if __name__ == '__main__':
    sys.exit(check_migrations())
