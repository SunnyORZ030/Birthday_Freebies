from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response shape for basic health checks."""

    ok: bool


# ========== Write Request/Response Contracts ==========


class FreebieTextInput(BaseModel):
    """Bilingual text input for a freebie offer."""

    name: str = Field(..., min_length=1, description="Display name for the offer")
    item: str = Field(..., min_length=1, description="Description of the free item or reward")
    member: str = Field(..., min_length=1, description="Membership or signup requirement text")
    redemption_window: str = Field(..., min_length=1, alias="window", description="Redemption timing or validity window")
    note: str = Field(default="", description="Optional caveat or additional info")


class FreebieCreateRequest(BaseModel):
    """Request payload to create a new freebie."""

    region_code: str = Field(..., pattern=r"^[a-z0-9_]+$", max_length=50, description="Target region code")
    category: str = Field(..., min_length=1, max_length=50, description="Category code like food, drink, beauty, etc")
    sort_order: int = Field(default=0, description="Display order within region")
    zh: FreebieTextInput = Field(..., description="Chinese (Traditional) texts")
    en: FreebieTextInput = Field(..., description="English texts")


class FreebieUpdateRequest(BaseModel):
    """Request payload to update an existing freebie (all fields optional)."""

    category: str | None = Field(None, min_length=1, max_length=50, description="Updated category code")
    sort_order: int | None = Field(None, description="Updated sort order")
    is_active: bool | None = Field(None, description="Enable/disable the freebie")
    zh: FreebieTextInput | None = Field(None, description="Updated Chinese texts")
    en: FreebieTextInput | None = Field(None, description="Updated English texts")


class FreebieCreatedResponse(BaseModel):
    """Response after successfully creating a freebie."""

    id: str = Field(..., description="Newly created freebie ID")
    region_code: str = Field(..., description="Region code of the created freebie")
    category: str = Field(..., description="Category of the created freebie")
    created_at: str = Field(..., description="ISO 8601 timestamp")


class FreebieUpdatedResponse(BaseModel):
    """Response after successfully updating a freebie."""

    id: str = Field(..., description="Updated freebie ID")
    updated_at: str = Field(..., description="ISO 8601 timestamp")


# ========== Read Request/Response Contracts ==========


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