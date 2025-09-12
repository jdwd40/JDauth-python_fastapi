#!/usr/bin/env python3
"""
Database seeding script for JDauth FastAPI application.

This script populates the databases with initial data:
- Main database: Creates an admin user and some sample users
- Test database: Creates test users for automated testing
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

from app.config.settings import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def seed_main_database():
    """Seed the main database with initial data."""
    print("Seeding main database...")
    
    try:
        engine = create_engine(settings.database_url)
        Session = sessionmaker(bind=engine)
        
        with Session() as session:
            # Check if users already exist
            result = session.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            
            if user_count > 0:
                print(f"Main database already has {user_count} users. Skipping seeding.")
                return True
            
            # Create initial users
            users_data = [
                {
                    'username': 'admin',
                    'password': 'admin123',  # Change this in production!
                    'description': 'Default administrator account'
                },
                {
                    'username': 'testuser',
                    'password': 'testpass123',
                    'description': 'Sample test user'
                },
                {
                    'username': 'demouser',
                    'password': 'demopass123',
                    'description': 'Demo user for testing'
                }
            ]
            
            print("Creating initial users:")
            for user_data in users_data:
                hashed_password = hash_password(user_data['password'])
                
                session.execute(
                    text("""
                        INSERT INTO users (username, hashed_password, created_at, updated_at)
                        VALUES (:username, :hashed_password, :created_at, :updated_at)
                    """),
                    {
                        'username': user_data['username'],
                        'hashed_password': hashed_password,
                        'created_at': datetime.now(timezone.utc),
                        'updated_at': datetime.now(timezone.utc)
                    }
                )
                print(f"  ✅ Created user: {user_data['username']} - {user_data['description']}")
            
            session.commit()
            print(f"Successfully created {len(users_data)} users in main database.")
            
        engine.dispose()
        return True
        
    except Exception as e:
        print(f"Error seeding main database: {e}")
        return False


def seed_test_database():
    """Seed the test database with test data."""
    print("Seeding test database...")
    
    try:
        engine = create_engine(settings.test_database_url)
        Session = sessionmaker(bind=engine)
        
        # First, create tables in test database
        from app.config.database import Base
        from app.models.user import User  # Import User model so Base.metadata knows about it
        
        # Create all tables in test database
        print("Creating tables in test database...")
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully in test database.")
        
        with Session() as session:
            # Check if test users already exist
            result = session.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            
            if user_count > 0:
                print(f"Test database already has {user_count} users. Skipping seeding.")
                return True
            
            # Create test users
            test_users_data = [
                {
                    'username': 'testuser1',
                    'password': 'testpass1',
                    'description': 'Test user 1 for automated testing'
                },
                {
                    'username': 'testuser2', 
                    'password': 'testpass2',
                    'description': 'Test user 2 for automated testing'
                },
                {
                    'username': 'testadmin',
                    'password': 'testadminpass',
                    'description': 'Test admin user for permission testing'
                },
                {
                    'username': 'testguest',
                    'password': 'testguestpass',
                    'description': 'Test guest user with limited permissions'
                }
            ]
            
            print("Creating test users:")
            for user_data in test_users_data:
                hashed_password = hash_password(user_data['password'])
                
                session.execute(
                    text("""
                        INSERT INTO users (username, hashed_password, created_at, updated_at)
                        VALUES (:username, :hashed_password, :created_at, :updated_at)
                    """),
                    {
                        'username': user_data['username'],
                        'hashed_password': hashed_password,
                        'created_at': datetime.now(timezone.utc),
                        'updated_at': datetime.now(timezone.utc)
                    }
                )
                print(f"  ✅ Created test user: {user_data['username']} - {user_data['description']}")
            
            session.commit()
            print(f"Successfully created {len(test_users_data)} test users.")
            
        engine.dispose()
        return True
        
    except Exception as e:
        print(f"Error seeding test database: {e}")
        return False


def main():
    """Main seeding function."""
    print("=== JDauth Database Seeding ===")
    print()
    
    success = True
    
    # Seed main database
    if not seed_main_database():
        success = False
    
    print()
    
    # Seed test database
    if not seed_test_database():
        success = False
    
    print()
    
    if success:
        print("✅ Database seeding completed successfully!")
        print()
        print("Main database users:")
        print("  - admin:admin123 (administrator)")
        print("  - testuser:testpass123 (sample user)")
        print("  - demouser:demopass123 (demo user)")
        print()
        print("Test database users:")
        print("  - testuser1:testpass1 (test user 1)")
        print("  - testuser2:testpass2 (test user 2)")
        print("  - testadmin:testadminpass (test admin)")
        print("  - testguest:testguestpass (test guest)")
        print()
        print("⚠️  IMPORTANT: Change default passwords in production!")
    else:
        print("❌ Database seeding failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
