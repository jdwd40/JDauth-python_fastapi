"""
JDauth FastAPI Application - Main Application Assembly

This module assembles all components of the JDauth FastAPI application
including configuration, database, routes, middleware, and startup logic.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

# Import configuration and database
from app.config.settings import settings
from app.config.database import engine, Base

# Import routers
from app.routes.auth import router as auth_router
from app.routes.user import router as user_router, admin_router

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting JDauth FastAPI application...")
    
    try:
        # Create database tables if they don't exist
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    logger.info("Application startup completed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down JDauth FastAPI application...")
    
    # Close database connections
    engine.dispose()
    logger.info("Database connections closed")
    
    logger.info("Application shutdown completed")


# Initialize FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Authentication service with JWT tokens and MVC architecture",
    version="2.0.0",
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,  # Disable docs in production
    redoc_url="/redoc" if settings.debug else None,
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],  # Configure as needed
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Configure trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.localhost"]  # Configure as needed
)


# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database exceptions."""
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Database error occurred",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Include API routers
app.include_router(auth_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(admin_router, prefix="/api")


# Health check endpoints
@app.get("/health", tags=["Health"])
def health_check() -> Dict[str, Any]:
    """
    Application health check endpoint.
    
    Returns:
        Health status information including database connectivity
    """
    try:
        # Test database connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "service": "JDauth FastAPI",
            "version": "2.0.0",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "JDauth FastAPI",
                "version": "2.0.0",
                "database": "disconnected",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.get("/", tags=["Root"])
def root() -> Dict[str, Any]:
    """
    Root endpoint with application information.
    
    Returns:
        Application information and available endpoints
    """
    return {
        "message": "JDauth FastAPI Application",
        "version": "2.0.0",
        "description": "Authentication service with JWT tokens and MVC architecture",
        "docs": "/docs" if settings.debug else "Documentation disabled in production",
        "health": "/health",
        "api_routes": {
            "authentication": "/api/auth",
            "user_management": "/api/user",
            "admin": "/api/users"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


# Legacy compatibility endpoint
@app.get("/test", tags=["Legacy"])
def test_route() -> Dict[str, Any]:
    """
    Legacy test endpoint for backward compatibility.
    
    Returns:
        Test status message
    """
    return {
        "status": "success",
        "message": "API server is running correctly!",
        "timestamp": datetime.utcnow().isoformat(),
        "note": "This is a legacy endpoint. Use /health for health checks."
    }
