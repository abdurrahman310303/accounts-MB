from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import startup_db, shutdown_db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
allowed_origins = [
    "http://localhost:3000",  # Local development
    "http://localhost:5173",  # Vite dev server
    "https://accounts-mb.vercel.app",  # Your Vercel deployment
    "https://accounts-mb-git-main-abdurrahman310303.vercel.app",  # Vercel git branch
    "*",  # Allow all origins for now (change this for production security)
]

# Add environment-based origins
import os
if os.getenv("FRONTEND_URL"):
    allowed_origins.append(os.getenv("FRONTEND_URL"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize database and other services"""
    logger.info("Starting up Financial Tracker API...")
    await startup_db()
    logger.info("Startup completed successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources"""
    logger.info("Shutting down Financial Tracker API...")
    await shutdown_db()
    logger.info("Shutdown completed")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.api_title,
        "version": settings.api_version
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint for API-only backend"""
    return {
        "message": "Finance Tracker API Backend",
        "version": settings.api_version,
        "docs": "/docs",
        "health": "/health",
        "api": "/api"
    }

# API info endpoint
@app.get("/api")
async def api_info():
    """API information endpoint"""
    return {
        "message": "Financial Tracker API",
        "version": settings.api_version,
        "docs": "/docs",
        "health": "/health"
    }

# Include routers
from app.routers import accounts, transactions, categories, teams

app.include_router(accounts.router, prefix="/api/v1")
app.include_router(transactions.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(teams.router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
