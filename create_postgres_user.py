#!/usr/bin/env python3
"""
Script to create PostgreSQL user for JDauth application.
This script connects as the default postgres user and creates the JD user.
"""

import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import getpass

def create_postgres_user():
    """Create the JD user in PostgreSQL."""
    
    print("=== PostgreSQL User Setup ===")
    print("This script will create the 'JD' user in PostgreSQL.")
    print()
    
    # Get postgres superuser password
    postgres_password = getpass.getpass("Enter password for postgres superuser (or press Enter if no password): ")
    
    # Try connecting as postgres user
    if postgres_password:
        admin_url = f"postgresql://postgres:{postgres_password}@localhost:5432/postgres"
    else:
        admin_url = "postgresql://postgres@localhost:5432/postgres"
    
    try:
        print("Connecting to PostgreSQL as postgres user...")
        conn = psycopg2.connect(admin_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("✅ Connected successfully!")
        
        # Check if JD user exists
        cursor.execute("SELECT 1 FROM pg_user WHERE usename = 'JD'")
        user_exists = cursor.fetchone()
        
        if user_exists:
            print("User 'JD' already exists.")
            
            # Update password
            print("Updating password for user 'JD'...")
            cursor.execute("ALTER USER \"JD\" WITH PASSWORD 'K1ller1921'")
            print("✅ Password updated for user 'JD'")
            
        else:
            # Create user
            print("Creating user 'JD'...")
            cursor.execute("CREATE USER \"JD\" WITH PASSWORD 'K1ller1921' CREATEDB SUPERUSER")
            print("✅ User 'JD' created successfully with CREATEDB and SUPERUSER privileges")
        
        # Grant additional privileges if needed
        cursor.execute("ALTER USER \"JD\" WITH LOGIN")
        
        # Test the new user connection
        cursor.close()
        conn.close()
        
        print("\nTesting connection with new user...")
        test_conn = psycopg2.connect("postgresql://JD:K1ller1921@localhost:5432/postgres")
        test_cursor = test_conn.cursor()
        test_cursor.execute("SELECT current_user")
        current_user = test_cursor.fetchone()[0]
        print(f"✅ Successfully connected as: {current_user}")
        
        test_cursor.close()
        test_conn.close()
        
        print("\n✅ PostgreSQL user setup complete!")
        print("You can now run: python setup_database.py")
        
        return True
        
    except psycopg2.OperationalError as e:
        if "authentication failed" in str(e):
            print("❌ Authentication failed for postgres user.")
            print("\nTry one of these options:")
            print("1. If postgres has no password, try: sudo -u postgres psql")
            print("2. Reset postgres password: sudo -u postgres psql -c \"ALTER USER postgres PASSWORD 'newpassword';\"")
            print("3. Check pg_hba.conf for authentication method")
        else:
            print(f"❌ Connection error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    if create_postgres_user():
        sys.exit(0)
    else:
        print("\n❌ User creation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
