# JDauth-python_fastapi

A simple FastAPI application demonstrating user registration and JWT based authentication backed by a Postgres database.

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

The API exposes the following endpoints:

- `POST /register` – register a new user.
- `POST /login` – obtain a JWT access token.
- `GET /protected` – an endpoint protected by JWT authentication.
