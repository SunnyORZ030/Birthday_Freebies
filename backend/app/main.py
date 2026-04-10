from typing import Annotated

from fastapi import FastAPI, HTTPException, Path, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.contracts import (
    ErrorResponse,
    FreebieCreateRequest,
    FreebieCreatedResponse,
    FreebieUpdatedResponse,
    FreebieUpdateRequest,
    FreebiesResponse,
    HealthResponse,
    RegionsResponse,
)
from app.db import get_connection_url
from app.services.freebies_service import (
    create_freebie_service,
    delete_freebie_service,
    get_freebies_by_region_service,
    get_regions_service,
    update_freebie_service,
    FreebieCreationError,
)

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


@app.exception_handler(FreebieCreationError)
async def handle_freebie_creation_error(_request: Request, exc: FreebieCreationError) -> JSONResponse:
    # Determine status code based on error message.
    error_msg = str(exc)
    if "not found" in error_msg.lower():
        status_code = 404
        code = "not_found"
    else:
        status_code = 400
        code = "business_error"
    
    return JSONResponse(
        status_code=status_code,
        content=_error_payload(
            code=code,
            message=error_msg,
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


# Create a new freebie with bilingual texts.
@app.post(
    "/api/freebies",
    response_model=FreebieCreatedResponse,
    responses={
        400: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    status_code=201,
)
def create_freebie(req: FreebieCreateRequest) -> FreebieCreatedResponse:
    """
    Create a new freebie offer with Chinese and English texts.
    
    Returns 201 on success with the new freebie ID and created timestamp.
    Returns 400 if region does not exist.
    Returns 422 if request validation fails.
    Returns 500 on unexpected errors.
    """
    result = create_freebie_service(
        get_connection_url(),
        region_code=req.region_code,
        category=req.category,
        sort_order=req.sort_order,
        zh_text={
            "name": req.zh.name,
            "item": req.zh.item,
            "member": req.zh.member,
            "redemption_window": req.zh.redemption_window,
            "note": req.zh.note,
        },
        en_text={
            "name": req.en.name,
            "item": req.en.item,
            "member": req.en.member,
            "redemption_window": req.en.redemption_window,
            "note": req.en.note,
        },
    )
    return FreebieCreatedResponse(**result)


# Update an existing freebie.
@app.put(
    "/api/freebies/{freebie_id}",
    response_model=FreebieUpdatedResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def update_freebie(
    freebie_id: Annotated[str, Path(description="Unique freebie identifier (UUID)")],
    req: FreebieUpdateRequest,
) -> FreebieUpdatedResponse:
    """
    Update an existing freebie's metadata and/or texts.
    Only provided fields are updated; omitted fields are left unchanged.
    
    Returns 200 on success.
    Returns 404 if freebie does not exist.
    Returns 400 if no updateable fields are provided.
    Returns 422 if request validation fails.
    Returns 500 on unexpected errors.
    """
    result = update_freebie_service(
        get_connection_url(),
        freebie_id=freebie_id,
        category=req.category,
        sort_order=req.sort_order,
        is_active=req.is_active,
        zh_text={
            "name": req.zh.name,
            "item": req.zh.item,
            "member": req.zh.member,
            "redemption_window": req.zh.redemption_window,
            "note": req.zh.note,
        } if req.zh else None,
        en_text={
            "name": req.en.name,
            "item": req.en.item,
            "member": req.en.member,
            "redemption_window": req.en.redemption_window,
            "note": req.en.note,
        } if req.en else None,
    )
    return FreebieUpdatedResponse(**result)


# Delete a freebie.
@app.delete(
    "/api/freebies/{freebie_id}",
    responses={
        204: {},
        500: {"model": ErrorResponse},
    },
    status_code=204,
)
def delete_freebie(
    freebie_id: Annotated[str, Path(description="Unique freebie identifier (UUID)")],
) -> None:
    """
    Delete a freebie and its associated texts.
    
    Returns 204 (No Content) on success, whether or not the freebie existed.
    Returns 500 on unexpected errors.
    """
    delete_freebie_service(get_connection_url(), freebie_id)
    # Delete is idempotent; always return 204.