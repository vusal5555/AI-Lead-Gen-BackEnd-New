from fastapi import FastAPI
from app.api.routes import leads
from app.config import get_settings
from fastapi.middleware.cors import CORSMiddleware


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    version="1.0.0",
    description="API for managing leads and sales outreach using AI.",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """
    Simple health check endpoint.
    Useful for monitoring and load balancers.
    """
    return {
        "status": "healthy",
        "app": settings.app_name,
        "environment": settings.app_env,
    }


app.include_router(leads.router, prefix="/api/leads", tags=["leads"])


@app.get("/")
async def root():
    return {
        "message": "Welcome to AI Sales Outreach API",
        "docs": "/docs",
        "health": "/health",
    }
