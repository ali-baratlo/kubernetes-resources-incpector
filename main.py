from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from prometheus_client import make_asgi_app
from api import endpoints
from scheduler.scheduler import start_scheduler
from collectors.resource_collector import collect_resources
from utils.logger import logger
from utils.db import client as db_client 
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan manager for the FastAPI application.
    This handles startup and shutdown events.
    """
    logger.info("Application starting up...")

    logger.info("Performing initial resource collection...")
    try:
        collect_resources()
        logger.info("Initial resource collection complete.")
    except Exception as e:
        logger.critical(f"Error during initial resource collection: {e}", exc_info=True)

    start_scheduler()

    yield

    logger.info("Application shutting down...")

app = FastAPI(
    title="Odin - OKD Resource Collector and Inspector",
    description="A tool to collect, inspect, and compare Kubernetes resources from multiple clusters.",
    version="2.0.0",
    lifespan=lifespan
)

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.get("/metrics", include_in_schema=False)
async def metrics_redirect():
    return RedirectResponse(url="/metrics/")

app.include_router(endpoints.router)

app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
