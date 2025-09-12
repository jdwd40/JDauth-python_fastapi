# JDauth FastAPI API Documentation

This document provides comprehensive API documentation for the JDauth FastAPI authentication service.

## Table of Contents

1. [Overview](#overview)
2. [Base URL](#base-url)
3. [Authentication](#authentication)
4. [Error Handling](#error-handling)
5. [API Endpoints](#api-endpoints)
6. [Data Models](#data-models)
7. [Examples](#examples)
8. [Rate Limiting](#rate-limiting)
9. [Security](#security)

## Overview

JDauth FastAPI is a modern authentication service built with FastAPI, PostgreSQL, and JWT tokens. It provides secure user registration, authentication, and profile management with a clean MVC architecture.

**Key Features**:
- JWT-based authentication
- Secure password hashing
- PostgreSQL database
- Rate limiting
- CORS support
- Comprehensive error handling
- OpenAPI/Swagger documentation

## Base URL

```
Development: http://localhost:8000
Production: https://your-domain.com
```

All API endpoints are prefixed with `/api`:
```
http://localhost:8000/api
```

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```http
Authorization: Bearer <your_jwt_token>
```

### Token Lifecycle

- **Expiration**: 30 minutes (configurable)
- **Refresh**: Use `/api/auth/refresh` endpoint
- **Format**: `Bearer <token>`

## Error Handling

The API returns consistent error responses in JSON format:

```json
{
    "error": true,
    "message": "Error description",
    "status_code": 400,
    "timestamp": "2025-09-12T21:00:00Z"
}
```

### HTTP Status Codes

- `200` - Success
- `201` - Created successfully
- `400` - Bad request (validation error)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not found
- `422` - Unprocessable entity (validation error)
- `429` - Too many requests (rate limited)
- `500` - Internal server error

## API Endpoints

### Authentication Endpoints

#### POST /api/auth/register

Register a new user account.

**Request Body**:
```json
{
    "username": "string (3-50 characters)",
    "password": "string (8+ characters)"
}
```

**Response (201 Created)**:
```json
{
    "message": "User registered successfully",
    "user_id": 123
}
```

**Response (400 Bad Request)**:
```json
{
    "error": true,
    "message": "Username already exists",
    "status_code": 400,
    "timestamp": "2025-09-12T21:00:00Z"
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "johndoe",
       "password": "securepassword123"
     }'
```

#### POST /api/auth/login

Authenticate user and receive JWT token.

**Request Body**:
```json
{
    "username": "string",
    "password": "string"
}
```

**Response (200 OK)**:
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800
}
```

**Response (401 Unauthorized)**:
```json
{
    "error": true,
    "message": "Invalid username or password",
    "status_code": 401,
    "timestamp": "2025-09-12T21:00:00Z"
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "johndoe",
       "password": "securepassword123"
     }'
```

#### POST /api/auth/refresh

Refresh an existing JWT token.

**Headers**:
```http
Authorization: Bearer <current_token>
```

**Response (200 OK)**:
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800
}
```

**Response (401 Unauthorized)**:
```json
{
    "error": true,
    "message": "Invalid or expired token",
    "status_code": 401,
    "timestamp": "2025-09-12T21:00:00Z"
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/api/auth/refresh" \
     -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### GET /api/auth/health

Check authentication service health.

**Response (200 OK)**:
```json
{
    "service": "authentication",
    "status": "healthy",
    "endpoints": [
        "/auth/register",
        "/auth/login",
        "/auth/refresh"
    ]
}
```

### User Management Endpoints

#### GET /api/user/profile

Get current user's profile information.

**Headers**:
```http
Authorization: Bearer <token>
```

**Response (200 OK)**:
```json
{
    "id": 123,
    "username": "johndoe",
    "created_at": "2025-09-12T20:00:00Z"
}
```

**Response (401 Unauthorized)**:
```json
{
    "error": true,
    "message": "Not authenticated",
    "status_code": 401,
    "timestamp": "2025-09-12T21:00:00Z"
}
```

**Example**:
```bash
curl -X GET "http://localhost:8000/api/user/profile" \
     -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### PUT /api/user/profile

Update current user's profile.

**Headers**:
```http
Authorization: Bearer <token>
```

**Request Body**:
```json
{
    "username": "string (optional, 3-50 characters)",
    "password": "string (optional, 8+ characters)"
}
```

**Response (200 OK)**:
```json
{
    "id": 123,
    "username": "newusername",
    "created_at": "2025-09-12T20:00:00Z"
}
```

**Response (400 Bad Request)**:
```json
{
    "error": true,
    "message": "Username already exists",
    "status_code": 400,
    "timestamp": "2025-09-12T21:00:00Z"
}
```

**Example**:
```bash
curl -X PUT "http://localhost:8000/api/user/profile" \
     -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
     -H "Content-Type: application/json" \
     -d '{
       "username": "newusername"
     }'
```

#### GET /api/user/protected

Example protected endpoint requiring authentication.

**Headers**:
```http
Authorization: Bearer <token>
```

**Response (200 OK)**:
```json
{
    "message": "Hello, johndoe! This is a protected endpoint.",
    "user_id": 123,
    "access_level": "authenticated"
}
```

**Example**:
```bash
curl -X GET "http://localhost:8000/api/user/protected" \
     -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### GET /api/user/health

Check user service health.

**Response (200 OK)**:
```json
{
    "service": "user_management",
    "status": "healthy",
    "endpoints": [
        "/user/profile",
        "/user/protected",
        "/users"
    ]
}
```

### Admin Endpoints

#### GET /api/users

Get paginated list of all users (admin only).

**Headers**:
```http
Authorization: Bearer <admin_token>
```

**Query Parameters**:
- `skip` (integer, optional): Number of users to skip (default: 0)
- `limit` (integer, optional): Maximum users to return (default: 100, max: 100)

**Response (200 OK)**:
```json
[
    {
        "id": 123,
        "username": "user1",
        "created_at": "2025-09-12T20:00:00Z"
    },
    {
        "id": 124,
        "username": "user2",
        "created_at": "2025-09-12T20:01:00Z"
    }
]
```

**Response (403 Forbidden)**:
```json
{
    "error": true,
    "message": "Admin access required",
    "status_code": 403,
    "timestamp": "2025-09-12T21:00:00Z"
}
```

**Example**:
```bash
curl -X GET "http://localhost:8000/api/users?skip=0&limit=10" \
     -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### System Endpoints

#### GET /health

Application health check.

**Response (200 OK)**:
```json
{
    "status": "healthy",
    "service": "JDauth FastAPI",
    "version": "2.0.0",
    "database": "connected",
    "timestamp": "2025-09-12T21:00:00Z"
}
```

**Response (503 Service Unavailable)**:
```json
{
    "status": "unhealthy",
    "service": "JDauth FastAPI",
    "version": "2.0.0",
    "database": "disconnected",
    "timestamp": "2025-09-12T21:00:00Z"
}
```

#### GET /

Root endpoint with application information.

**Response (200 OK)**:
```json
{
    "message": "JDauth FastAPI Application",
    "version": "2.0.0",
    "description": "Authentication service with JWT tokens and MVC architecture",
    "docs": "/docs",
    "health": "/health",
    "api_routes": {
        "authentication": "/api/auth",
        "user_management": "/api/user",
        "admin": "/api/users"
    },
    "timestamp": "2025-09-12T21:00:00Z"
}
```

## Data Models

### User Registration Request

```json
{
    "username": "string",     // 3-50 characters, alphanumeric + underscore
    "password": "string"      // 8+ characters, any printable characters
}
```

### Login Request

```json
{
    "username": "string",
    "password": "string"
}
```

### Token Response

```json
{
    "access_token": "string",    // JWT token
    "token_type": "bearer",      // Always "bearer"
    "expires_in": 1800          // Expiration time in seconds
}
```

### User Response

```json
{
    "id": 123,                           // User ID
    "username": "string",                // Username
    "created_at": "2025-09-12T20:00:00Z" // ISO 8601 timestamp
}
```

### User Update Request

```json
{
    "username": "string",    // Optional, 3-50 characters
    "password": "string"     // Optional, 8+ characters
}
```

### Error Response

```json
{
    "error": true,                       // Always true for errors
    "message": "string",                 // Human-readable error message
    "status_code": 400,                  // HTTP status code
    "timestamp": "2025-09-12T21:00:00Z"  // ISO 8601 timestamp
}
```

## Examples

### Complete Authentication Flow

```bash
# 1. Register a new user
curl -X POST "http://localhost:8000/api/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "johndoe",
       "password": "securepassword123"
     }'

# Response: {"message": "User registered successfully", "user_id": 123}

# 2. Login to get token
curl -X POST "http://localhost:8000/api/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "johndoe",
       "password": "securepassword123"
     }'

# Response: {"access_token": "eyJ...", "token_type": "bearer", "expires_in": 1800}

# 3. Use token to access protected endpoint
curl -X GET "http://localhost:8000/api/user/profile" \
     -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Response: {"id": 123, "username": "johndoe", "created_at": "2025-09-12T20:00:00Z"}

# 4. Update profile
curl -X PUT "http://localhost:8000/api/user/profile" \
     -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
     -H "Content-Type: application/json" \
     -d '{
       "username": "john_doe_updated"
     }'

# 5. Refresh token
curl -X POST "http://localhost:8000/api/auth/refresh" \
     -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### JavaScript/Frontend Integration

```javascript
class AuthAPI {
    constructor(baseURL = 'http://localhost:8000/api') {
        this.baseURL = baseURL;
        this.token = localStorage.getItem('auth_token');
    }

    async register(username, password) {
        const response = await fetch(`${this.baseURL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });
        return response.json();
    }

    async login(username, password) {
        const response = await fetch(`${this.baseURL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });
        const data = await response.json();
        
        if (response.ok) {
            this.token = data.access_token;
            localStorage.setItem('auth_token', this.token);
        }
        
        return data;
    }

    async getProfile() {
        const response = await fetch(`${this.baseURL}/user/profile`, {
            headers: {
                'Authorization': `Bearer ${this.token}`,
            },
        });
        return response.json();
    }

    async updateProfile(updates) {
        const response = await fetch(`${this.baseURL}/user/profile`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(updates),
        });
        return response.json();
    }

    async refreshToken() {
        const response = await fetch(`${this.baseURL}/auth/refresh`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`,
            },
        });
        const data = await response.json();
        
        if (response.ok) {
            this.token = data.access_token;
            localStorage.setItem('auth_token', this.token);
        }
        
        return data;
    }

    logout() {
        this.token = null;
        localStorage.removeItem('auth_token');
    }
}

// Usage
const auth = new AuthAPI();

// Register
await auth.register('johndoe', 'securepassword123');

// Login
await auth.login('johndoe', 'securepassword123');

// Get profile
const profile = await auth.getProfile();

// Update profile
await auth.updateProfile({ username: 'john_updated' });
```

### Python Client Example

```python
import requests
from typing import Optional, Dict, Any

class JDAuthClient:
    def __init__(self, base_url: str = "http://localhost:8000/api"):
        self.base_url = base_url
        self.token: Optional[str] = None
    
    def register(self, username: str, password: str) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/auth/register",
            json={"username": username, "password": password}
        )
        return response.json()
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password}
        )
        data = response.json()
        
        if response.status_code == 200:
            self.token = data["access_token"]
        
        return data
    
    def get_profile(self) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.base_url}/user/profile", headers=headers)
        return response.json()
    
    def update_profile(self, **updates) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        response = requests.put(
            f"{self.base_url}/user/profile",
            json=updates,
            headers=headers
        )
        return response.json()
    
    def refresh_token(self) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(f"{self.base_url}/auth/refresh", headers=headers)
        data = response.json()
        
        if response.status_code == 200:
            self.token = data["access_token"]
        
        return data

# Usage
client = JDAuthClient()

# Register
client.register("johndoe", "securepassword123")

# Login
client.login("johndoe", "securepassword123")

# Get profile
profile = client.get_profile()

# Update profile
client.update_profile(username="john_updated")
```

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Registration**: Limited to prevent spam accounts
- **Login**: Protected against brute force attacks
- **Token Refresh**: Limited to prevent token abuse

Rate limit responses return HTTP 429:

```json
{
    "error": true,
    "message": "Too many requests. Please try again later.",
    "status_code": 429,
    "timestamp": "2025-09-12T21:00:00Z"
}
```

## Security

### Security Features

1. **JWT Tokens**: Secure, stateless authentication
2. **Password Hashing**: bcrypt with salt
3. **Input Validation**: All inputs validated and sanitized
4. **SQL Injection Protection**: Parameterized queries
5. **CORS Configuration**: Controlled cross-origin access
6. **Rate Limiting**: Brute force protection
7. **Secure Headers**: Security-focused HTTP headers

### Security Best Practices

1. **Token Storage**: Store tokens securely (not in localStorage for sensitive apps)
2. **HTTPS**: Always use HTTPS in production
3. **Token Expiration**: Implement proper token refresh logic
4. **Input Validation**: Validate all inputs on client side too
5. **Error Handling**: Don't expose sensitive information in errors

### Security Headers

The API includes security headers:

- `Content-Type`: Proper content type specification
- CORS headers for controlled access
- TrustedHost middleware for host validation

## Interactive Documentation

The API provides interactive documentation via Swagger/OpenAPI:

- **Swagger UI**: Available at `/docs` (development only)
- **ReDoc**: Available at `/redoc` (development only)

These interfaces allow you to:
- Explore all endpoints
- Test API calls directly
- View request/response schemas
- Understand authentication requirements

---

For more detailed information about implementation, see the [Testing Guide](TESTING_GUIDE.md) and the source code in the repository.
