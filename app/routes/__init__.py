"""
Routes package for JDauth FastAPI application.

This package contains all API route definitions organized by functionality.
"""

# Import routers - these will be available after implementation
try:
    from .auth import router as auth_router
    from .user import router as user_router, admin_router
    
    __all__ = ["auth_router", "user_router", "admin_router"]
except ImportError:
    # During development, routes may not be fully implemented
    __all__ = []
