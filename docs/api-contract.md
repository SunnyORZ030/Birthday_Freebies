# API Contract

This document defines the stable runtime contract for the FastAPI backend.

## Base URL

- Local: `http://localhost:3001`

## Error Envelope

This envelope is used for API errors currently defined by this service.

```json
{
  "error": {
    "code": "invalid_request",
    "message": "Request validation failed.",
    "details": [
      {
        "field": "region",
        "message": "String should match pattern '^[a-z0-9_]+$'",
        "type": "string_pattern_mismatch"
      }
    ]
  }
}
```

Fields:

- `error.code`: machine-readable error identifier
- `error.message`: human-readable summary
- `error.details`: optional array of field-level validation issues

Current error codes:

- `invalid_request`: request validation failed, usually a 422 response
- `business_error`: write request failed validation at the service layer, usually a 400 response
- `not_found`: requested freebie or region was not found, usually a 404 response
- `internal_error`: unexpected server error, usually a 500 response

## GET /health

Purpose: basic server health probe.

Success response `200`:

```json
{
  "ok": true
}
```

## GET /api/regions

Purpose: list regions for frontend dropdown and filtering.

Success response `200`:

```json
{
  "regions": [
    {
      "code": "bay_area",
      "name": "Bay Area"
    }
  ]
}
```

Error response:

- `500`: internal error envelope

## GET /api/freebies

Purpose: list freebies grouped by region.

Query params:

- `region` (optional): lowercase region code filter
- Validation: pattern `^[a-z0-9_]+$`, max length `50`

Success response `200`:

```json
{
  "dataByRegion": {
    "bay_area": [
      {
        "name": "Starbucks",
        "name_en": "Starbucks",
        "cat": "drink",
        "u": false,
        "item": "Any handcrafted drink",
        "item_en": "Any handcrafted drink",
        "member": "Membership required",
        "member_en": "Membership required",
        "window": "On birthday",
        "window_en": "On birthday",
        "note": "Terms may vary by store",
        "note_en": "Terms may vary by store"
      }
    ]
  }
}
```

Error responses:

- `422`: validation error envelope (invalid query parameters)
- `500`: internal error envelope

## POST /api/freebies

Purpose: create a new freebie with bilingual text rows.

Request body:

```json
{
  "region_code": "bay_area",
  "category": "drink",
  "sort_order": 0,
  "zh": {
    "name": "星巴克",
    "item": "任意手工製飲品",
    "member": "需要會員卡",
    "window": "生日當天",
    "note": "各分店條款可能不同"
  },
  "en": {
    "name": "Starbucks",
    "item": "Any handcrafted drink",
    "member": "Membership required",
    "window": "On birthday",
    "note": "Terms may vary by store"
  }
}
```

Notes:

- `region_code` must match `^[a-z0-9_]+$` and refer to an existing region.
- `zh.window` and `en.window` map to the service's `redemption_window` field.
- `note` is optional and defaults to an empty string.

Success response `201`:

```json
{
  "id": "freebie-123",
  "region_code": "bay_area",
  "category": "drink",
  "created_at": "2026-04-10T20:00:00"
}
```

Error responses:

- `400`: business error envelope (for example, invalid write-time data)
- `422`: validation error envelope
- `404`: not found envelope when the target region does not exist
- `500`: internal error envelope

## PUT /api/freebies/{freebie_id}

Purpose: update an existing freebie's metadata and/or bilingual text rows.

Path params:

- `freebie_id`: freebie UUID

Request body:

```json
{
  "category": "drink",
  "sort_order": 2,
  "is_active": true,
  "en": {
    "name": "Starbucks Updated",
    "item": "Any handcrafted drink",
    "member": "Membership required",
    "window": "On birthday",
    "note": "Updated note"
  }
}
```

Notes:

- All fields are optional.
- `zh` and `en` can be sent independently.
- If no updateable fields are provided, the service returns a `400` business error.

Success response `200`:

```json
{
  "id": "freebie-123",
  "updated_at": "2026-04-10T20:00:00"
}
```

Error responses:

- `400`: business error envelope
- `404`: not found envelope when the freebie does not exist
- `422`: validation error envelope
- `500`: internal error envelope

## DELETE /api/freebies/{freebie_id}

Purpose: delete a freebie and its localized text rows.

Path params:

- `freebie_id`: freebie UUID

Success response `204`:

- No content
- The operation is idempotent; deleting a missing freebie still returns `204`

Error responses:

- `500`: internal error envelope

## Contract Stability Notes

- Response keys are stable and should be treated as API contract.
- Frontend should not infer hidden fields or rely on database column names.
- New fields may be added in the future, but existing keys and meanings should remain backward-compatible.