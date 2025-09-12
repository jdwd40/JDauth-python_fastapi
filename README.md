# JDauth FastAPI - Authentication Service

A modern, secure authentication service built with FastAPI, PostgreSQL, and JWT tokens. Features a clean MVC architecture with comprehensive testing, security measures, and production-ready configuration.

## 🚀 Features

- **🔐 Secure Authentication**: JWT tokens with bcrypt password hashing
- **🏗️ MVC Architecture**: Clean separation of concerns with services, controllers, and routes
- **🗄️ PostgreSQL Database**: Robust database with Alembic migrations
- **🧪 Comprehensive Testing**: Unit, integration, E2E, performance, and security tests
- **📊 Test Coverage**: >90% test coverage with detailed reporting
- **⚡ High Performance**: Optimized for speed and scalability
- **🛡️ Security First**: Input validation, SQL injection prevention, rate limiting
- **📚 Full Documentation**: API docs, testing guides, and deployment instructions
- **🔄 Production Ready**: Health checks, logging, error handling, and monitoring

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Security](#security)
- [Documentation](#documentation)
- [Deployment](#deployment)
- [Contributing](#contributing)

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Git

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd JDauth-python_fastapi
   ```

2. **Set up virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL databases**:
   ```bash
   # Create main database
   createdb jdauth_db
   
   # Create test database
   createdb jdauth_test_db
   ```

5. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env with your database credentials
   ```

6. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

7. **Start the application**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

8. **Access the application**:
   - API: http://localhost:8000
   - Health Check: http://localhost:8000/health
   - API Documentation: http://localhost:8000/docs (development only)

## 🏗️ Architecture

JDauth follows a clean MVC (Model-View-Controller) architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                      │
├─────────────────────────────────────────────────────────────┤
│  Routes Layer (API Endpoints)                              │
│  ├── /api/auth/* (Authentication routes)                   │
│  ├── /api/user/* (User management routes)                  │
│  └── /api/users/* (Admin routes)                           │
├─────────────────────────────────────────────────────────────┤
│  Controllers Layer (Business Logic)                        │
│  ├── AuthController (Registration, login, token refresh)   │
│  └── UserController (Profile management, user operations)  │
├─────────────────────────────────────────────────────────────┤
│  Services Layer (Data Access)                              │
│  ├── AuthService (Authentication logic)                    │
│  └── UserService (User CRUD operations)                    │
├─────────────────────────────────────────────────────────────┤
│  Models Layer (Database Models)                            │
│  └── User (SQLAlchemy model)                               │
├─────────────────────────────────────────────────────────────┤
│  Schemas Layer (Data Validation)                           │
│  ├── UserCreate, UserUpdate, UserResponse                  │
│  └── LoginRequest, TokenResponse                           │
├─────────────────────────────────────────────────────────────┤
│  Utilities & Configuration                                 │
│  ├── Database configuration & connection pooling           │
│  ├── Security utilities (JWT, password hashing)           │
│  ├── Dependencies (authentication, database sessions)      │
│  └── Settings (environment-based configuration)            │
└─────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
JDauth-python_fastapi/
├── app/                          # Application code
│   ├── config/                   # Configuration
│   │   ├── database.py           # Database setup
│   │   └── settings.py           # Environment settings
│   ├── controllers/              # Business logic layer
│   │   ├── auth_controller.py    # Authentication controller
│   │   └── user_controller.py    # User management controller
│   ├── models/                   # Database models
│   │   └── user.py               # User model
│   ├── routes/                   # API endpoints
│   │   ├── auth.py               # Authentication routes
│   │   └── user.py               # User routes
│   ├── schemas/                  # Data validation schemas
│   │   ├── auth.py               # Authentication schemas
│   │   └── user.py               # User schemas
│   ├── services/                 # Data access layer
│   │   ├── auth_service.py       # Authentication service
│   │   └── user_service.py       # User service
│   ├── utils/                    # Utilities
│   │   ├── dependencies.py       # FastAPI dependencies
│   │   └── security.py           # Security utilities
│   └── main.py                   # Application entry point
├── tests/                        # Test suite
│   ├── test_controllers/         # Controller tests
│   ├── test_routes/              # Route tests
│   ├── test_services/            # Service tests
│   ├── test_integration/         # Integration tests
│   ├── test_e2e/                 # End-to-end tests
│   ├── conftest.py               # Test configuration
│   └── factories.py              # Test data factories
├── alembic/                      # Database migrations
├── docs/                         # Documentation
│   ├── API_DOCUMENTATION.md      # API documentation
│   ├── TESTING_GUIDE.md          # Testing guide
│   └── llm-tasks.md              # Development tasks
├── requirements.txt              # Python dependencies
├── pytest.ini                   # Test configuration
├── alembic.ini                   # Migration configuration
└── README.md                     # This file
```

## 📡 API Endpoints

### Authentication

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh JWT token
- `GET /api/auth/health` - Authentication service health

### User Management

- `GET /api/user/profile` - Get current user profile
- `PUT /api/user/profile` - Update user profile
- `GET /api/user/protected` - Protected endpoint example
- `GET /api/user/health` - User service health

### Admin

- `GET /api/users` - List all users (admin only)

### System

- `GET /health` - Application health check
- `GET /` - Application information
- `GET /docs` - API documentation (development only)

For detailed API documentation with examples, see [API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md).

## 🧪 Testing

JDauth includes a comprehensive test suite with multiple testing layers:

### Test Categories

- **Unit Tests**: Test individual components (services, controllers, routes)
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete user workflows
- **Performance Tests**: Test performance under load
- **Security Tests**: Test security measures and vulnerabilities

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_services/        # Unit tests
pytest tests/test_integration/     # Integration tests
pytest tests/test_e2e/            # E2E tests

# Run with coverage
pytest --cov=app --cov-report=html

# Run performance tests
pytest tests/test_e2e/test_performance_load.py

# Run security tests
pytest tests/test_e2e/test_security.py
```

### Test Coverage

Current test coverage: **>90%**

- Service Layer: >95%
- Controller Layer: >90%
- Route Layer: >85%

For detailed testing information, see [TESTING_GUIDE.md](docs/TESTING_GUIDE.md).

## 🛡️ Security

JDauth implements comprehensive security measures:

### Security Features

- **JWT Authentication**: Secure, stateless token-based authentication
- **Password Security**: bcrypt hashing with salt
- **Input Validation**: Comprehensive input validation and sanitization
- **SQL Injection Prevention**: Parameterized queries with SQLAlchemy
- **Rate Limiting**: Protection against brute force attacks
- **CORS Configuration**: Controlled cross-origin access
- **Security Headers**: Security-focused HTTP headers
- **XSS Protection**: Input sanitization and output encoding

### Security Testing

The application includes comprehensive security tests:

- JWT token security validation
- Password hashing verification
- SQL injection prevention tests
- XSS protection tests
- Rate limiting tests
- Input validation tests

### Security Best Practices

- Use HTTPS in production
- Store JWT tokens securely
- Implement proper token refresh logic
- Validate inputs on both client and server
- Monitor for security vulnerabilities
- Keep dependencies updated

## 📚 Documentation

### Available Documentation

- **[API Documentation](docs/API_DOCUMENTATION.md)**: Complete API reference with examples
- **[Testing Guide](docs/TESTING_GUIDE.md)**: Comprehensive testing documentation
- **[Task Breakdown](docs/llm-tasks.md)**: Development task documentation

### Interactive API Documentation

In development mode, interactive API documentation is available:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🚀 Deployment

### Environment Configuration

1. **Copy environment template**:
   ```bash
   cp env.example .env
   ```

2. **Configure environment variables**:
   ```bash
   # Database
   DATABASE_URL=postgresql://user:password@localhost:5432/jdauth_db
   TEST_DATABASE_URL=postgresql://user:password@localhost:5432/jdauth_test_db
   
   # Security
   SECRET_KEY=your_secure_secret_key_change_in_production
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   
   # Application
   APP_NAME=JDauth FastAPI
   DEBUG=False
   ```

### Production Deployment

#### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Docker Compose

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/jdauth_db
      - SECRET_KEY=your_production_secret_key
      - DEBUG=False
    depends_on:
      - db

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=jdauth_db
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

#### Manual Deployment

1. **Set up production server** (Ubuntu/Debian):
   ```bash
   # Install dependencies
   sudo apt update
   sudo apt install python3.9 python3.9-venv postgresql nginx
   
   # Create application user
   sudo useradd -m -s /bin/bash jdauth
   sudo su - jdauth
   ```

2. **Deploy application**:
   ```bash
   # Clone and set up
   git clone <repository-url>
   cd JDauth-python_fastapi
   python3.9 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Configure environment
   cp env.example .env
   # Edit .env with production values
   
   # Run migrations
   alembic upgrade head
   ```

3. **Set up systemd service**:
   ```bash
   # Create service file
   sudo nano /etc/systemd/system/jdauth.service
   ```
   
   ```ini
   [Unit]
   Description=JDauth FastAPI
   After=network.target
   
   [Service]
   User=jdauth
   Group=jdauth
   WorkingDirectory=/home/jdauth/JDauth-python_fastapi
   Environment=PATH=/home/jdauth/JDauth-python_fastapi/venv/bin
   EnvironmentFile=/home/jdauth/JDauth-python_fastapi/.env
   ExecStart=/home/jdauth/JDauth-python_fastapi/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

4. **Configure Nginx**:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

### Production Checklist

- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] SSL/TLS certificates installed
- [ ] Firewall configured
- [ ] Monitoring set up
- [ ] Backup strategy implemented
- [ ] Log rotation configured
- [ ] Health checks enabled
- [ ] Rate limiting configured
- [ ] Security headers enabled

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Run tests**: `pytest`
5. **Ensure code coverage**: `pytest --cov=app --cov-fail-under=90`
6. **Commit changes**: `git commit -m 'Add amazing feature'`
7. **Push to branch**: `git push origin feature/amazing-feature`
8. **Open a Pull Request**

### Development Guidelines

- Follow PEP 8 style guidelines
- Write tests for new features
- Maintain test coverage >90%
- Update documentation for API changes
- Use descriptive commit messages

### Running Development Environment

```bash
# Set up development environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests in watch mode
pytest --watch
```

## 📊 Performance

### Benchmarks

- **Registration**: < 2.0s average response time
- **Login**: < 1.0s average response time
- **Protected Endpoints**: < 0.5s average response time
- **Concurrent Users**: Supports 10+ concurrent users
- **Memory Usage**: < 50MB increase under load

### Optimization Features

- Database connection pooling
- Efficient query patterns
- JWT token caching
- Response compression
- Static file serving optimization

## 🔧 Monitoring

### Health Checks

- **Application Health**: `GET /health`
- **Database Health**: Included in health check
- **Service Health**: Individual service health endpoints

### Logging

The application includes structured logging:

```python
import logging

logger = logging.getLogger(__name__)
logger.info("User registered successfully", extra={"user_id": user.id})
```

### Metrics

Key metrics to monitor:

- Response times
- Error rates
- Database connection pool usage
- Memory usage
- CPU usage
- Active user sessions

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- SQLAlchemy for robust ORM capabilities
- Pydantic for data validation
- pytest for comprehensive testing framework
- PostgreSQL for reliable database backend

## 📞 Support

For support, please:

1. Check the [documentation](docs/)
2. Search existing issues
3. Create a new issue with detailed information
4. Contact the development team

---

**JDauth FastAPI** - Secure, scalable, and production-ready authentication service.
