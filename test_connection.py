#!/usr/bin/env python3
"""
Simple script to test PostgreSQL connection with your credentials.
Run this after installing dependencies to verify the setup.
"""

import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import psycopg2
    from app.config.settings import settings
    
    print("=== PostgreSQL Connection Test ===")
    print(f"Testing connection to: {settings.postgres_admin_url}")
    
    # Test connection
    conn = psycopg2.connect(settings.postgres_admin_url)
    cursor = conn.cursor()
    cursor.execute('SELECT version()')
    version = cursor.fetchone()[0]
    
    print("✅ PostgreSQL Connection Successful!")
    print(f"Version: {version}")
    
    # Test if we can list databases
    cursor.execute("SELECT datname FROM pg_database WHERE datname IN ('jdauth_db', 'jdauth_test_db')")
    existing_dbs = cursor.fetchall()
    
    if existing_dbs:
        print(f"Existing JDauth databases: {[db[0] for db in existing_dbs]}")
    else:
        print("No JDauth databases found (this is expected on first run)")
    
    cursor.close()
    conn.close()
    
    print("\n✅ Ready to run database setup!")
    
except ImportError:
    print("❌ psycopg2 not installed. Please run:")
    print("   source venv/bin/activate")
    print("   pip install -r requirements.txt")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure PostgreSQL is running")
    print("2. Verify your credentials are correct")
    print("3. Check if the PostgreSQL service is accessible on localhost:5432")
