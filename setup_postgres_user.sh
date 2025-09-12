#!/bin/bash

# Script to create PostgreSQL user for JDauth application
# This script uses sudo to connect as the postgres system user

echo "=== PostgreSQL User Setup ==="
echo "Creating PostgreSQL user 'JD' with password 'K1ller1921'"
echo

# Check if postgres system user can connect
echo "Attempting to create user as postgres system user..."

# Create the user using sudo -u postgres
sudo -u postgres psql -c "
DO \$\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'JD') THEN
      CREATE USER \"JD\" WITH PASSWORD 'K1ller1921' CREATEDB SUPERUSER LOGIN;
      RAISE NOTICE 'User JD created successfully';
   ELSE
      ALTER USER \"JD\" WITH PASSWORD 'K1ller1921' CREATEDB SUPERUSER LOGIN;
      RAISE NOTICE 'User JD already exists, password updated';
   END IF;
END
\$\$;
"

# Check if the command was successful
if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL user setup completed!"
    echo
    echo "Testing connection..."
    
    # Test the connection
    python3 -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://JD:K1ller1921@localhost:5432/postgres')
    cursor = conn.cursor()
    cursor.execute('SELECT current_user')
    user = cursor.fetchone()[0]
    print(f'✅ Successfully connected as: {user}')
    cursor.close()
    conn.close()
    print('✅ Ready to run: python setup_database.py')
except Exception as e:
    print(f'❌ Connection test failed: {e}')
    "
else
    echo "❌ Failed to create PostgreSQL user"
    echo "You may need to:"
    echo "1. Make sure you have sudo access"
    echo "2. Ensure PostgreSQL is properly installed"
    echo "3. Try running: sudo -u postgres createuser --interactive JD"
fi
