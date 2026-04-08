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
1. Added [assets/data/i18n-data.js](assets/data/i18n-data.js) to store:
- Region labels
- I18N dictionaries
- Shared constants
- English replacement mappings

2. Updated [index.html](index.html):
- Load [assets/data/i18n-data.js](assets/data/i18n-data.js) after [assets/data/freebies-data.js](assets/data/freebies-data.js)
- Replace large inline metadata blocks with references to window.BIRTHDAY_FREEBIES_META
- Preserve existing filtering, sorting, and rendering behavior
- Improve section comments for readability

3. Updated [scripts/add_bilingual_fields.js](scripts/add_bilingual_fields.js) and [README.md](README.md) as part of this version.

4. Reorganized runtime files into an `assets` structure:
- Moved [assets/data/freebies-data.js](assets/data/freebies-data.js) and [assets/data/i18n-data.js](assets/data/i18n-data.js) into `assets/data`.
- Updated [index.html](index.html) script paths to load data from the new location.
- Updated [scripts/add_bilingual_fields.js](scripts/add_bilingual_fields.js) to write to the new data path.

5. Extracted inline JavaScript app logic from [index.html](index.html) to [assets/scripts/app.js](assets/scripts/app.js).

6. Extracted inline CSS from [index.html](index.html) to [assets/styles/main.css](assets/styles/main.css) and switched to external stylesheet loading.

### Compatibility
1. Backward-safe fallbacks are retained in [index.html](index.html), so missing metadata keys still degrade gracefully.
2. No data schema break for existing entries in [assets/data/freebies-data.js](assets/data/freebies-data.js).
3. Page behavior remains unchanged after moving runtime logic into [assets/scripts/app.js](assets/scripts/app.js).
4. Visual behavior remains unchanged after moving styles into [assets/styles/main.css](assets/styles/main.css).