from typing import Annotated

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.contracts import ErrorResponse, FreebiesResponse, HealthResponse, RegionsResponse
from app.db import get_connection_url
from app.services.freebies_service import get_freebies_by_region_service, get_regions_service

# Main API app used by uvicorn.
app = FastAPI(title="Birthday Freebies API")

# Allow local frontend pages to call this API without extra proxy configuration.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _error_payload(code: str, message: str, details: list[dict[str, str]] | None = None) -> dict:
    # Keep all API errors in one stable envelope shape for frontend handling.
    return ErrorResponse(error={"code": code, "message": message, "details": details}).model_dump()


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    details: list[dict[str, str]] = []
    for err in exc.errors():
        loc = [str(part) for part in err.get("loc", []) if part != "query"]
        details.append(
            {
                "field": ".".join(loc) if loc else "request",
                "message": str(err.get("msg", "Invalid request")),
                "type": str(err.get("type", "validation_error")),
            }
        )
    return JSONResponse(
        status_code=422,
        content=_error_payload(
            code="invalid_request",
            message="Request validation failed.",
            details=details,
        ),
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(_request: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=_error_payload(
            code="internal_error",
            message="Unexpected server error.",
        ),
    )


# Basic health probe for startup checks and quick diagnostics.
@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(ok=True)


# Regions endpoint used by the frontend region dropdown.
@app.get(
    "/api/regions",
    response_model=RegionsResponse,
    responses={500: {"model": ErrorResponse}},
)
def get_regions() -> RegionsResponse:
    return RegionsResponse(regions=get_regions_service(get_connection_url()))


# Main freebies endpoint. Returns entries grouped by region to match existing UI state.
@app.get(
    "/api/freebies",
    response_model=FreebiesResponse,
    responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def get_freebies(
    region: Annotated[
        str | None,
        Query(
            pattern=r"^[a-z0-9_]+$",
            max_length=50,
            description="Optional region code filter (lowercase letters, digits, underscore).",
        ),
    ] = None,
) -> FreebiesResponse:
    try:
        data_by_region = get_freebies_by_region_service(get_connection_url(), region)
    except ValueError:
        # Convert service-layer validation failures into the same 422 contract payload.
        raise RequestValidationError(
            [
                {
                    "loc": ("query", "region"),
                    "msg": "Region must match ^[a-z0-9_]+$ and be at most 50 characters.",
                    "type": "string_pattern_mismatch",
                }
            ]
        )
    return FreebiesResponse(dataByRegion=data_by_region)