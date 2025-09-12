# Database Setup Guide

This guide explains how to set up PostgreSQL databases for the JDauth FastAPI application.

## Prerequisites

1. **PostgreSQL installed and running**
   ```bash
   # On Ubuntu/Debian
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   
   # Start PostgreSQL service
   sudo systemctl start postgresql
   sudo systemctl enable postgresql
   ```

2. **Python virtual environment**
   ```bash
   # Install python3-venv if not already installed
   sudo apt install python3.12-venv
   
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

## Quick Setup

1. **Configure environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your PostgreSQL credentials
   ```

2. **Run database setup**
   ```bash
   python setup_database.py
   ```

3. **Seed with initial data**
   ```bash
   python seed_database.py
   ```

4. **Start the application**
   ```bash
   uvicorn app.main:app --reload
   ```

## Detailed Setup

### 1. PostgreSQL Configuration

Make sure PostgreSQL is running and you have admin access:

```bash
# Test PostgreSQL connection
sudo -u postgres psql -c "SELECT version();"

# If needed, set password for postgres user
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'your_password';"
```

### 2. Environment Configuration

Copy and modify the environment file:

```bash
cp env.example .env
```

Update the `.env` file with your settings (or use the defaults):

```env
# Database URLs (configured for your PostgreSQL setup)
DATABASE_URL=postgresql://JD:K1ller1921@localhost:5432/jdauth_db
TEST_DATABASE_URL=postgresql://JD:K1ller1921@localhost:5432/jdauth_test_db

# Admin connection for database creation
POSTGRES_ADMIN_URL=postgresql://JD:K1ller1921@localhost:5432/postgres

# Security (generate a secure secret key!)
SECRET_KEY=your_secure_secret_key_here
```

### 3. Database Setup Script

The `setup_database.py` script will:
- Create the `jdauth_db` database if it doesn't exist
- Create the `jdauth_test_db` database if it doesn't exist  
- Run Alembic migrations to create tables
- Use your existing PostgreSQL user (JD) with full access

```bash
python setup_database.py
```

### 4. Database Seeding Script

The `seed_database.py` script will:
- Populate the main database with initial users
- Populate the test database with test users
- Can be run multiple times safely (won't create duplicates)

```bash
python seed_database.py
```

## What Gets Created

### Main Database (`jdauth_db`)
- **admin:admin123** - Administrator account
- **testuser:testpass123** - Sample user
- **demouser:demopass123** - Demo user

### Test Database (`jdauth_test_db`)
- **testuser1:testpass1** - Test user 1
- **testuser2:testpass2** - Test user 2
- **testadmin:testadminpass** - Test admin user
- **testguest:testguestpass** - Test guest user

⚠️ **Important**: Change these default passwords in production!

## Database Schema

The initial migration creates a `users` table with:
- `id` (Primary Key)
- `username` (Unique)
- `hashed_password`
- `created_at` (Timestamp)
- `updated_at` (Timestamp)

## Alembic Migrations

To create new migrations after schema changes:

```bash
# Generate migration
alembic revision --autogenerate -m "description of changes"

# Apply migrations
alembic upgrade head

# Downgrade (if needed)
alembic downgrade -1
```

## Testing the Setup

1. **Test database connection**:
   ```bash
   python -c "
   from app.config.database import engine
   from sqlalchemy import text
   with engine.connect() as conn:
       result = conn.execute(text('SELECT version()'))
       print('Database connected:', result.fetchone()[0])
   "
   ```

2. **Test API endpoints**:
   ```bash
   # Start the server
   uvicorn app.main:app --reload
   
   # Test registration
   curl -X POST "http://localhost:8000/register" \
        -H "Content-Type: application/json" \
        -d '{"username": "newuser", "password": "newpass123"}'
   
   # Test login
   curl -X POST "http://localhost:8000/login" \
        -H "Content-Type: application/json" \
        -d '{"username": "admin", "password": "admin123"}'
   ```

## Troubleshooting

### Common Issues

1. **PostgreSQL not running**:
   ```bash
   sudo systemctl status postgresql
   sudo systemctl start postgresql
   ```

2. **Permission denied**:
   ```bash
   # Make sure the postgres user can create databases
   sudo -u postgres psql -c "ALTER USER postgres CREATEDB;"
   ```

3. **Connection refused**:
   - Check if PostgreSQL is listening on port 5432
   - Verify `pg_hba.conf` allows local connections
   - Check firewall settings

4. **Alembic command not found**:
   ```bash
   # Make sure virtual environment is activated
   source venv/bin/activate
   pip install alembic
   ```

### Reset Database

To completely reset the databases:

```bash
# Connect as postgres admin
sudo -u postgres psql

# Drop databases
DROP DATABASE IF EXISTS jdauth_db;
DROP DATABASE IF EXISTS jdauth_test_db;
DROP USER IF EXISTS jdauth_user;

# Exit and run setup again
python setup_database.py
python seed_database.py
```

## Security Notes

- Change default passwords before production use
- Use strong, unique secret keys
- Consider using environment-specific configuration
- Regularly update dependencies
- Use SSL connections in production
- Implement proper backup strategies
