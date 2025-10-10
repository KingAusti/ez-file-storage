from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
import time
import uuid

from .core.database import engine
from .core.config import settings
from .core.logging import configure_logging, get_logger
from .core.version import get_version_info, get_health_version, VERSION
from .models import user, data_entry, audit_log
from .routers import auth_router, data_entries_router, tags_router

# Configure logging
logger = configure_logging()

# Configure Sentry
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[
            FastApiIntegration(auto_enabling_instrumentations=False),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1 if settings.environment == "production" else 1.0,
        environment=settings.environment,
    )

# Create database tables (only in development)
if settings.environment == "development":
    user.Base.metadata.create_all(bind=engine)
    data_entry.Base.metadata.create_all(bind=engine)
    audit_log.Base.metadata.create_all(bind=engine)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Data Storage API",
    description="A secure data storage application with authentication",
    version=VERSION,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Add GZIP compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id_and_logging(request: Request, call_next):
    """Add request ID and structured logging"""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Add request ID to request state
    request.state.request_id = request_id
    
    # Log request
    logger.info(
        "Request started",
        request_id=request_id,
        method=request.method,
        url=str(request.url),
        client_ip=get_remote_address(request),
        user_agent=request.headers.get("user-agent"),
    )
    
    try:
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            "Request completed",
            request_id=request_id,
            status_code=response.status_code,
            process_time=process_time,
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        
        logger.error(
            "Request failed",
            request_id=request_id,
            error=str(e),
            process_time=process_time,
        )
        
        raise


# Include routers
app.include_router(auth_router)
app.include_router(data_entries_router)
app.include_router(tags_router)


@app.get("/")
def read_root():
    return {"message": "Data Storage API is running", "version": VERSION}


@app.get("/version")
def get_version():
    """Get detailed version information"""
    return get_version_info()


@app.get("/health")
def health_check():
    """Enhanced health check with dependency validation"""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        **get_health_version(),
        "environment": settings.environment,
    }
    
    # Check database connection
    try:
        from .core.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        health_status["database"] = "healthy"
    except Exception as e:
        health_status["database"] = "unhealthy"
        health_status["database_error"] = str(e)
        health_status["status"] = "unhealthy"
    
    # Check Redis connection (if configured)
    try:
        import redis
        r = redis.from_url(settings.redis_url)
        r.ping()
        health_status["redis"] = "healthy"
    except Exception as e:
        health_status["redis"] = "unhealthy"
        health_status["redis_error"] = str(e)
    
    return health_status


@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    # Basic metrics - in production, you'd use prometheus_client
    return {
        "requests_total": 0,  # Would be tracked in production
        "request_duration_seconds": 0,
        "active_connections": 0,
    }
