from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response shape for basic health checks."""

    ok: bool


class RegionItem(BaseModel):
    """Single region entry used by /api/regions."""

    code: str = Field(..., description="Stable region code such as bay_area")
    name: str = Field(..., description="Display label for the region")


class RegionsResponse(BaseModel):
    """Top-level response payload for region listing."""

    regions: list[RegionItem]


class FreebieItem(BaseModel):
    """Frontend-compatible freebie item shape."""

    name: str
    name_en: str
    cat: str
    u: bool
    item: str
    item_en: str
    member: str
    member_en: str
    window: str
    window_en: str
    note: str
    note_en: str


class FreebiesResponse(BaseModel):
    """Top-level response payload grouped by region code."""

    dataByRegion: dict[str, list[FreebieItem]]


class ApiError(BaseModel):
    """Standardized error payload for all non-2xx responses."""

    code: str
    message: str
    details: list[dict[str, Any]] | None = None


class ErrorResponse(BaseModel):
    """Envelope wrapper for API errors."""

    error: ApiError