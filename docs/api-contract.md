# API Contract

This document defines the stable runtime contract for the FastAPI backend.

## Base URL

- Local: `http://localhost:3001`

## Error Envelope

This envelope is used for API errors currently defined by this service (422 and 500):

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

## Contract Stability Notes

- Response keys are stable and should be treated as API contract.
- Frontend should not infer hidden fields or rely on database column names.
- New fields may be added in the future, but existing keys and meanings should remain backward-compatible.