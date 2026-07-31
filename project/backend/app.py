"""
app.py — FastAPI Application Entrypoint.

Configures the FastAPI app, CORS, static file serving (for charts),
and includes all API routes.
"""

from api.routes import router
from config import API_DESCRIPTION, API_TITLE, API_VERSION, CHARTS_DIR, CORS_ORIGINS
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from utils import ensure_directory, get_logger

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title=API_TITLE,
        description=API_DESCRIPTION,
        version=API_VERSION,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Ensure charts directory exists before mounting
    ensure_directory(CHARTS_DIR)

    # Include routes
    app.include_router(router, prefix="/api/v1")

    # Mount static files for serving generated charts to the frontend
    app.mount("/static/charts", StaticFiles(directory=str(CHARTS_DIR)), name="charts")

    # Serve the frontend files from the root
    from config import BASE_DIR
    frontend_dir = BASE_DIR / "frontend"
    if frontend_dir.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
        logger.info("Frontend static files mounted at root.")
    
    logger.info("FastAPI app initialized successfully.")
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    from config import API_HOST, API_PORT

    uvicorn.run("app:app", host=API_HOST, port=API_PORT, reload=True)
