import uuid
import time

from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from pydantic import BaseModel, EmailStr, ConfigDict
from sqlalchemy.orm import Session

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST
)

from app.database import Base, engine, get_db
from app.models import Registration
from app.messaging import publish_registration


# Initialize Prometheus metrics

HTTP_REQUESTS = Counter(
    "queuescale_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

HTTP_REQUEST_DURATION = Histogram(
    "queuescale_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "queuescale_http_requests_in_progress",
    "Number of HTTP requests currently being processed"
)


# Initialize FastAPI

app = FastAPI(
    title="QueueScale API",
    description="Intelligent Queue-Based Traffic Management and Auto-Scaling System",
    version="0.2.0"
)


@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)


# Prometheus HTTP instrumentation

@app.middleware("http")
async def prometheus_metrics_middleware(request: Request, call_next):

    if request.url.path == "/metrics":
        return await call_next(request)

    method = request.method
    start_time = time.perf_counter()

    HTTP_REQUESTS_IN_PROGRESS.inc()

    response_status = "500"
    endpoint = request.url.path

    try:
        response = await call_next(request)

        response_status = str(response.status_code)

        route = request.scope.get("route")
        if route is not None:
            endpoint = route.path

        return response

    finally:
        duration = time.perf_counter() - start_time

        HTTP_REQUESTS.labels(
            method=method,
            endpoint=endpoint,
            status=response_status
        ).inc()

        HTTP_REQUEST_DURATION.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

        HTTP_REQUESTS_IN_PROGRESS.dec()


# Prometheus metrics endpoint

@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# Request schema

class RegistrationCreate(BaseModel):
    student_name: str
    email: EmailStr
    event_name: str


# Response schema

class RegistrationResponse(BaseModel):
    request_id: str
    student_name: str
    email: str
    event_name: str
    status: str

    model_config = ConfigDict(from_attributes=True)


# Root endpoint

@app.get("/")
def root():
    return {
        "message": "Welcome to QueueScale API",
        "status": "running"
    }


# Health check endpoint

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "queuescale-api"
    }


# Submit a registration

@app.post(
    "/registrations",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED
)
def create_registration(
    request: RegistrationCreate,
    db: Session = Depends(get_db)
):
    registration = Registration(
        request_id=str(uuid.uuid4()),
        student_name=request.student_name,
        email=request.email,
        event_name=request.event_name,
        status="QUEUED"
    )

    db.add(registration)
    db.commit()
    db.refresh(registration)

    message = {
        "request_id": registration.request_id,
        "student_name": registration.student_name,
        "email": registration.email,
        "event_name": registration.event_name
    }

    try:
        publish_registration(message)

    except Exception as exc:
        registration.status = "FAILED"
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "message": "Registration saved, but message publishing failed",
                "request_id": registration.request_id
            }
        ) from exc

    return registration


# Check registration status

@app.get(
    "/registrations/{request_id}",
    response_model=RegistrationResponse
)
def get_registration(
    request_id: str,
    db: Session = Depends(get_db)
):
    registration = (
        db.query(Registration)
        .filter(Registration.request_id == request_id)
        .first()
    )

    if registration is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration not found"
        )

    return registration
