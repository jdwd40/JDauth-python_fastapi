#!/usr/bin/env python3
"""
Database setup script for JDauth FastAPI application.

This script creates the PostgreSQL databases if they don't exist and runs
the initial migrations. It can be run multiple times safely.
"""

import sys
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text
import subprocess
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.config.settings import settings


def create_database_if_not_exists(admin_url: str, db_name: str):
    """Create database if it doesn't exist."""
    print(f"Checking if database '{db_name}' exists...")
    
    try:
        # Connect to PostgreSQL as admin
        conn = psycopg2.connect(admin_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        db_exists = cursor.fetchone()
        
        if not db_exists:
            print(f"Creating database '{db_name}'...")
            cursor.execute(f'CREATE DATABASE "{db_name}"')
            print(f"Database '{db_name}' created successfully.")
        else:
            print(f"Database '{db_name}' already exists.")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"Error creating database: {e}")
        return False
    
    return True


def run_migrations():
    """Run Alembic migrations."""
    print("Running database migrations...")
    try:
        # Run alembic upgrade
        result = subprocess.run(
            ["python", "-m", "alembic", "upgrade", "head"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("Migrations completed successfully.")
            return True
        else:
            print(f"Migration failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error running migrations: {e}")
        return False


def test_connection(database_url: str, db_name: str):
    """Test database connection."""
    print(f"Testing connection to '{db_name}'...")
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"Successfully connected to '{db_name}'. PostgreSQL version: {version}")
        engine.dispose()
        return True
    except Exception as e:
        print(f"Failed to connect to '{db_name}': {e}")
        return False


def main():
    """Main setup function."""
    print("=== JDauth Database Setup ===")
    print(f"Admin URL: {settings.postgres_admin_url}")
    print(f"Main DB URL: {settings.database_url}")
    print(f"Test DB URL: {settings.test_database_url}")
    print()
    
    # Extract database info from URLs
    main_db_name = settings.database_url.split('/')[-1]
    test_db_name = settings.test_database_url.split('/')[-1]
    
    success = True
    
    # Create main database
    if not create_database_if_not_exists(
        settings.postgres_admin_url, 
        main_db_name
    ):
        success = False
    
    # Create test database
    if not create_database_if_not_exists(
        settings.postgres_admin_url, 
        test_db_name
    ):
        success = False
    
    if success:
        # Test connections
        if test_connection(settings.database_url, main_db_name):
            print()
            # Run migrations on main database
            if run_migrations():
                print()
                print("✅ Database setup completed successfully!")
                print()
                print("Next steps:")
                print("1. Run 'python seed_database.py' to add initial data")
                print("2. Start the application with 'uvicorn app.main:app --reload'")
            else:
                print("❌ Migration failed!")
                success = False
        else:
            success = False
    
    if not success:
        print("❌ Database setup failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
