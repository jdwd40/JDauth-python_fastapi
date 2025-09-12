"""
Test configuration and fixtures for the JDauth FastAPI application.
"""

import pytest
import asyncio
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.config.database import Base, get_db
from app.config.settings import settings
from app.main import app


# Test database configuration
TEST_DATABASE_URL = settings.test_database_url

# Create test engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    echo=False,  # Set to True for SQL query debugging
)

# Test session factory
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Set up test database tables before running tests and clean up after."""
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    yield
    # Drop all tables after tests
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """
    Create a fresh database session for each test.
    This ensures test isolation by rolling back transactions.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> TestClient:
    """
    Create a test client with dependency overrides.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up dependency overrides
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "password": "testpassword123"
    }


@pytest.fixture
def sample_user_update_data():
    """Sample user update data for testing."""
    return {
        "username": "updated_user",
        "password": "updated_password123"
    }


@pytest.fixture
def multiple_users_data():
    """Multiple users data for pagination testing."""
    return [
        {"username": "user1", "password": "password1"},
        {"username": "user2", "password": "password2"},
        {"username": "user3", "password": "password3"},
        {"username": "user4", "password": "password4"},
        {"username": "user5", "password": "password5"},
    ]


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
