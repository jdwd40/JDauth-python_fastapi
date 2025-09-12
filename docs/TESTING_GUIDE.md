# JDauth FastAPI Testing Guide

This guide provides comprehensive information about testing the JDauth FastAPI application, including unit tests, integration tests, end-to-end tests, performance tests, and security tests.

## Table of Contents

1. [Testing Architecture](#testing-architecture)
2. [Test Categories](#test-categories)
3. [Running Tests](#running-tests)
4. [Test Coverage](#test-coverage)
5. [End-to-End Testing](#end-to-end-testing)
6. [Performance Testing](#performance-testing)
7. [Security Testing](#security-testing)
8. [Database Testing](#database-testing)
9. [CI/CD Integration](#cicd-integration)
10. [Best Practices](#best-practices)

## Testing Architecture

The JDauth FastAPI application follows a comprehensive testing strategy with multiple layers:

```
┌─────────────────────────────────────────────────────────────┐
│                    End-to-End Tests                         │
│  Complete user workflows, security, performance            │
├─────────────────────────────────────────────────────────────┤
│                  Integration Tests                          │
│  Service interactions, database operations                  │
├─────────────────────────────────────────────────────────────┤
│                     Unit Tests                              │
│  Services, Controllers, Routes, Utilities                   │
└─────────────────────────────────────────────────────────────┘
```

## Test Categories

### 1. Unit Tests (`tests/test_services/`, `tests/test_controllers/`, `tests/test_routes/`)

**Purpose**: Test individual components in isolation
**Coverage**: Services, controllers, route handlers, utilities
**Characteristics**:
- Fast execution
- Isolated from external dependencies
- High test coverage target (>95%)

### 2. Integration Tests (`tests/test_integration/`)

**Purpose**: Test component interactions
**Coverage**: Service layer interactions, database operations
**Characteristics**:
- Test component boundaries
- Use test database
- Verify data flow between layers

### 3. End-to-End Tests (`tests/test_e2e/`)

**Purpose**: Test complete user workflows
**Coverage**: Full authentication flows, user journeys
**Characteristics**:
- Test entire application stack
- Simulate real user interactions
- Validate business requirements

### 4. Performance Tests (`tests/test_e2e/test_performance_load.py`)

**Purpose**: Validate performance under load
**Coverage**: Response times, concurrent users, memory usage
**Characteristics**:
- Benchmark API performance
- Test scalability
- Monitor resource usage

### 5. Security Tests (`tests/test_e2e/test_security.py`)

**Purpose**: Validate security measures
**Coverage**: Authentication, authorization, input validation
**Characteristics**:
- Test security vulnerabilities
- Validate access controls
- Test input sanitization

## Running Tests

### Prerequisites

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Install all dependencies including test dependencies
pip install -r requirements.txt

# Ensure PostgreSQL is running and test database exists
# (The application will create tables automatically)
```

### Basic Test Execution

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test categories
pytest tests/test_services/        # Unit tests for services
pytest tests/test_controllers/     # Unit tests for controllers
pytest tests/test_routes/          # Unit tests for routes
pytest tests/test_integration/     # Integration tests
pytest tests/test_e2e/            # End-to-end tests

# Run specific test files
pytest tests/test_e2e/test_auth_flow.py
pytest tests/test_e2e/test_performance_load.py
pytest tests/test_e2e/test_security.py

# Run specific test methods
pytest tests/test_e2e/test_auth_flow.py::TestE2EAuthenticationFlow::test_complete_user_registration_and_login_flow
```

### Test Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run performance tests
pytest tests/test_e2e/test_performance_load.py

# Run security tests
pytest tests/test_e2e/test_security.py
```

## Test Coverage

### Coverage Requirements

- **Overall Coverage**: >85%
- **Service Layer**: >95%
- **Controller Layer**: >90%
- **Route Layer**: >85%

### Generating Coverage Reports

```bash
# Generate coverage report (configured in pytest.ini)
pytest --cov=app --cov-report=html --cov-report=term-missing

# View HTML coverage report
open htmlcov/index.html  # On macOS
xdg-open htmlcov/index.html  # On Linux

# Coverage with specific minimum threshold
pytest --cov=app --cov-fail-under=90
```

### Coverage Configuration

Coverage settings are configured in `pytest.ini`:

```ini
[tool:pytest]
addopts = 
    -v
    --tb=short
    --cov=app
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=90
```

## End-to-End Testing

### Authentication Flow Tests

**File**: `tests/test_e2e/test_auth_flow.py`

**Test Scenarios**:
- Complete user registration and login flow
- Token refresh workflow
- User profile update flow
- Multi-user concurrent sessions
- Error handling scenarios
- Data validation scenarios

**Example Test**:
```python
def test_complete_user_registration_and_login_flow(self, db_session):
    """Test complete flow: registration → login → access protected endpoint."""
    # 1. Register user
    # 2. Login user
    # 3. Access protected endpoint
    # 4. Verify user profile
```

### Database Integration Tests

**File**: `tests/test_e2e/test_database_integration.py`

**Test Scenarios**:
- Connection pooling under load
- Transaction rollback scenarios
- Concurrent user operations
- Data consistency across operations
- Database performance under load

## Performance Testing

### Performance Test Categories

**File**: `tests/test_e2e/test_performance_load.py`

#### 1. Response Time Benchmarks
- API endpoint response times
- Performance regression detection
- Baseline performance metrics

#### 2. Concurrent Load Testing
- Multiple simultaneous users
- Session handling under load
- Success rate monitoring

#### 3. Memory Usage Testing
- Memory consumption patterns
- Memory leak detection
- Resource usage monitoring

#### 4. Sustained Load Testing
- Performance over time
- Throughput measurement
- System stability

### Performance Metrics

**Target Performance Metrics**:
- Registration: < 2.0s
- Login: < 1.0s
- Protected endpoints: < 0.5s
- Profile operations: < 0.5s
- Token refresh: < 0.5s

**Load Testing Targets**:
- Concurrent users: 10-20
- Success rate: >90%
- Memory increase: <50MB under load

## Security Testing

### Security Test Categories

**File**: `tests/test_e2e/test_security.py`

#### 1. Authentication Security
- JWT token validation
- Password hashing verification
- Session hijacking prevention
- Token tampering detection

#### 2. Input Validation Security
- SQL injection prevention
- XSS (Cross-Site Scripting) protection
- Input sanitization
- Path traversal prevention

#### 3. Rate Limiting
- Brute force attack protection
- Registration rate limiting
- API endpoint throttling

#### 4. Security Headers
- CORS configuration
- Security header validation
- Content-Type enforcement

### Security Test Examples

```python
# JWT Security Test
def test_jwt_token_security_validation(self):
    # Test valid token
    # Test tampered token
    # Test expired token
    # Test malformed token

# SQL Injection Test
def test_sql_injection_prevention(self):
    sql_payloads = [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "' UNION SELECT * FROM users --"
    ]
    # Test each payload in registration and login
```

## Database Testing

### Database Test Configuration

**Test Database**: `jdauth_test_db`
**Connection**: Configured in `app/config/settings.py`
**Isolation**: Each test uses isolated transactions

### Database Test Features

- **Automatic Setup**: Test tables created automatically
- **Transaction Rollback**: Each test is isolated
- **Connection Pooling**: Tests validate connection handling
- **Data Consistency**: Verify ACID properties

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: jdauth_test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
        
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        
    - name: Run tests
      run: |
        pytest --cov=app --cov-fail-under=85
      env:
        DATABASE_URL: postgresql://postgres:testpass@localhost/jdauth_test_db
```

### Test Pipeline Stages

1. **Unit Tests**: Fast, run on every commit
2. **Integration Tests**: Medium speed, run on PR
3. **E2E Tests**: Slower, run on main branch
4. **Performance Tests**: Run nightly or on release
5. **Security Tests**: Run on security-related changes

## Best Practices

### Writing Tests

1. **Follow AAA Pattern**:
   ```python
   def test_example(self):
       # Arrange
       user_data = {"username": "test", "password": "pass123"}
       
       # Act
       response = client.post("/register", json=user_data)
       
       # Assert
       assert response.status_code == 201
   ```

2. **Use Descriptive Names**:
   ```python
   def test_user_registration_with_duplicate_username_returns_400(self):
       # Clear what the test does and expects
   ```

3. **Test Edge Cases**:
   - Empty inputs
   - Maximum length inputs
   - Invalid data types
   - Boundary conditions

4. **Use Fixtures Effectively**:
   ```python
   @pytest.fixture
   def sample_user(self):
       return {"username": "testuser", "password": "testpass123"}
   ```

### Test Data Management

1. **Use Factories**: Leverage `factory-boy` for test data
2. **Avoid Hard-coded Data**: Use parameterized tests
3. **Clean Up**: Ensure tests don't leave artifacts
4. **Isolation**: Each test should be independent

### Performance Testing Best Practices

1. **Baseline Measurements**: Establish performance baselines
2. **Realistic Load**: Use realistic user scenarios
3. **Monitor Resources**: Track CPU, memory, database connections
4. **Gradual Load**: Increase load gradually in tests

### Security Testing Best Practices

1. **Test All Inputs**: Validate all user inputs
2. **Authentication Edge Cases**: Test token edge cases
3. **Authorization**: Verify access controls
4. **Keep Updated**: Update security tests with new threats

## Troubleshooting

### Common Issues

1. **Database Connection Issues**:
   ```bash
   # Check PostgreSQL is running
   pg_isready -h localhost -p 5432
   
   # Verify test database exists
   psql -h localhost -U postgres -l
   ```

2. **Test Isolation Issues**:
   ```bash
   # Run tests with fresh database
   pytest --create-db
   ```

3. **Performance Test Failures**:
   - Check system load during tests
   - Verify database performance
   - Consider adjusting thresholds

4. **Security Test Issues**:
   - Update security payloads
   - Check for false positives
   - Verify input validation

### Debug Mode

```bash
# Run tests with debug output
pytest -v --tb=long

# Run single test with debugging
pytest -v -s tests/test_e2e/test_auth_flow.py::test_name

# Run with Python debugger
pytest --pdb
```

## Continuous Improvement

### Test Metrics to Monitor

1. **Test Coverage**: Maintain >85% overall coverage
2. **Test Execution Time**: Keep test suite fast
3. **Test Reliability**: Minimize flaky tests
4. **Performance Baselines**: Track performance trends

### Regular Maintenance

1. **Update Dependencies**: Keep test libraries current
2. **Review Test Cases**: Add tests for new features
3. **Performance Baselines**: Update performance expectations
4. **Security Tests**: Add tests for new vulnerabilities

---

For more information about specific test implementations, see the individual test files in the `tests/` directory.
