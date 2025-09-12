from datetime import datetime

from fastapi import FastAPI

# Import new configuration and models
from app.config.database import get_db
from app.config.settings import settings

# Import new routers
from app.routes.auth import router as auth_router
from app.routes.user import router as user_router, admin_router

# All security utilities and dependencies are now in app.utils


app = FastAPI(
    title="JDauth FastAPI Application",
    description="Authentication service with JWT tokens",
    version="1.0.0"
)

# Include routers
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(admin_router)


# Legacy endpoints for backward compatibility
@app.get("/test")
def test_route():
    return {"status": "success", "message": "API server is running correctly!", "timestamp": datetime.utcnow().isoformat()}

@app.get("/")
def root():
    return {
        "message": "JDauth FastAPI Application",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/test"
    }
