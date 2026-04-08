# Changelog

## Unreleased

### Title
Refactor metadata structure and improve maintainability

### Summary
1. Extracted localization and display metadata from HTML into a separate file for cleaner structure.
2. Updated script loading flow to include metadata file before app logic.
3. Kept runtime behavior unchanged while improving readability and maintainability.
4. Added and refined inline comments across HTML/CSS/JS sections.

### Changes
1. Added [i18n-data.js](i18n-data.js) to store:
- Region labels
- I18N dictionaries
- Shared constants
- English replacement mappings

2. Updated [index.html](index.html):
- Load [i18n-data.js](i18n-data.js) after [freebies-data.js](freebies-data.js)
- Replace large inline metadata blocks with references to window.BIRTHDAY_FREEBIES_META
- Preserve existing filtering, sorting, and rendering behavior
- Improve section comments for readability

3. Updated [scripts/add_bilingual_fields.js](scripts/add_bilingual_fields.js) and [README.md](README.md) as part of this version.

### Compatibility
1. Backward-safe fallbacks are retained in [index.html](index.html), so missing metadata keys still degrade gracefully.
2. No data schema break for existing entries in [freebies-data.js](freebies-data.js).
