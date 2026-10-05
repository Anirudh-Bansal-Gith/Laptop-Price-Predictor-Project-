"""FastAPI application entrypoint and server lifecycle definition.

Configures middleware, CORS allowances, dependency lifespan events,
diagnostic health check endpoints, and router registrations.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.dependencies import get_model, load_model_on_startup
from api.routers.predict import router as predict_router
from api.schemas import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager to preload ML models upon startup."""
    load_model_on_startup()
    yield


app = FastAPI(
    title="Laptop Price Predictor API",
    description="High-performance REST API microservice for estimating laptop market valuations from hardware attributes.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Cross-Origin Resource Sharing (CORS) policy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(predict_router, prefix="/api/v1")


@app.get("/health", response_model=HealthResponse, tags=["Diagnostics"])
async def health_check() -> HealthResponse:
    """Return operational health and ML model cache status."""
    active_model = get_model()
    return HealthResponse(
        status="ok",
        model_loaded=active_model is not None,
    )


@app.get("/", tags=["Root"])
async def root_info() -> dict:
    """Return service index and API navigation links."""
    return {
        "service": "Laptop Price Predictor API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "predict_endpoint": "/api/v1/predict",
    }
