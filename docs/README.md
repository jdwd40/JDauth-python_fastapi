# JDauth-python_fastapi

A simple FastAPI application demonstrating user registration and JWT based authentication backed by a SQLite database.

## Setup

1. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
2. Update the `DATABASE_URL` and `SECRET_KEY` in `app/main.py` to match your environment.
3. Run the application
   ```bash
   uvicorn app.main:app --reload
   ```

## Current Implementation Status

### ✅ Completed Features
- **User Registration** (`/register`) - Creates new users with hashed passwords
- **JWT Authentication** (`/login`) - Returns JWT tokens for valid credentials  
- **Password Security** - Uses bcrypt for password hashing
- **Database Integration** - SQLAlchemy with SQLite backend
- **Protected Routes** (`/protected`) - JWT token validation
- **Token Management** - 30-minute token expiration

### 📁 Current Structure
- `app/main.py` - Complete authentication server (145 lines)
- `requirements.txt` - All necessary dependencies
- SQLite database (`jdauth.db`) for user storage

### ⚠️ Production Considerations
- Using placeholder SECRET_KEY (line 45) - needs secure random key
- Currently SQLite but can be switched to Postgres
- No user profile/additional fields beyond username/password

## API Endpoints

- `POST /register` – register a new user
- `POST /login` – obtain a JWT access token
- `GET /protected` – an endpoint protected by JWT authentication
- `GET /test` – health check endpoint

The core authentication flow is fully functional - you can register users, login to get JWT tokens, and access protected endpoints. It's a solid foundation that just needs production hardening and any additional features you want to add.
