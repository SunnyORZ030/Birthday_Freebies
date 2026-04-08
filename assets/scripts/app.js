// Use region-based data when available, otherwise fall back to legacy single-region data.
const regionData = window.BIRTHDAY_FREEBIES_DATA_BY_REGION || { bay_area: window.BIRTHDAY_FREEBIES_DATA || [] };

// Load localization dictionaries and value constants from external metadata.
const meta = window.BIRTHDAY_FREEBIES_META || {};
const REGION_LABELS = meta.REGION_LABELS || { bay_area: { en: 'Bay Area (SJSU)', zh: '\u7063\u5340 (SJSU)' } };
const I18N = meta.I18N || { en: { pageTitle: 'Birthday Freebies Tracker', all: 'All' }, zh: { pageTitle: '\u751F\u65E5\u512A\u60E0\u8FFD\u8E64\u8868', all: '\u5168\u90E8' } };
const VALUE_CONSTANTS = meta.CONSTANTS || {};
const CONTENT_REPLACEMENTS_EN = meta.CONTENT_REPLACEMENTS_EN || [];

// Runtime state and normalized constants for source values.
let currentRegion = 'bay_area';
let data = regionData[currentRegion] || [];
const CP_HIGH = VALUE_CONSTANTS.CP_HIGH || '\u9AD8';
const CP_MEDIUM = VALUE_CONSTANTS.CP_MEDIUM || '\u4E2D';
const CP_LOW = VALUE_CONSTANTS.CP_LOW || '\u4F4E';
const DIST_NEAR = VALUE_CONSTANTS.DIST_NEAR || '\u8FD1';
const DIST_MEDIUM = VALUE_CONSTANTS.DIST_MEDIUM || '\u4E2D';
const DIST_FAR = VALUE_CONSTANTS.DIST_FAR || '\u9060';
const BATCH_FLEX = VALUE_CONSTANTS.BATCH_FLEX || '\u6709\u7A7A\u518D\u53BB';
let currentLocale = 'en';

let current = 'all';

// Detect language from browser preferences.
function detectLocale() {
  const raw = ((navigator.languages && navigator.languages[0]) || navigator.language || 'en').toLowerCase();
  return raw.startsWith('zh') ? 'zh' : 'en';
}

// Translate a UI key using the active locale with English fallback.
function t(key) {
  return (I18N[currentLocale] && I18N[currentLocale][key]) || I18N.en[key] || key;
}

// Resolve a region key into the current locale label.
function regionLabel(regionKey) {
  const label = REGION_LABELS[regionKey];
  if (!label) return regionKey;
  return label[currentLocale] || label.en || regionKey;
}

// Apply translated text to static UI elements.
function applyI18nText() {
  document.documentElement.lang = currentLocale === 'zh' ? 'zh-Hant' : 'en';
  document.title = t('pageTitle');
  const ids = ['foodBtn', 'drinkBtn', 'dessertBtn', 'beautyBtn', 'cpHighBtn', 'cpMediumBtn', 'batchFlexBtn', 'thStore', 'thCategory', 'thFreebie', 'thMember', 'thWindow', 'thValue', 'thDistance'];
  ids.forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = t(id);
  });
}

// Keep the "All" button label in sync with the active region count.
function updateAllButtonCount() {
  const allBtn = document.getElementById('allBtn');
  if (allBtn) allBtn.textContent = `${t('all')} (${data.length})`;
}

// Reset active button styling back to the default "All" state.
function resetActiveFilter() {
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  const allBtn = document.getElementById('allBtn');
  if (allBtn) allBtn.classList.add('active');
}

// Handle region dropdown changes and refresh the table.
function changeRegion(regionKey) {
  currentRegion = regionKey;
  data = regionData[currentRegion] || [];
  current = 'all';
  resetActiveFilter();
  updateAllButtonCount();
  render();
}

// Handle filter button clicks and refresh the table.
function filter(key, btn) {
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  current = key;
  render();
}

// Populate region options from available data keys.
function initRegions() {
  const select = document.getElementById('regionSelect');
  const keys = Object.keys(regionData);
  if (!keys.length || !select) return;
  select.innerHTML = keys.map(k => `<option value="${k}">${regionLabel(k)}</option>`).join('');
  if (!regionData[currentRegion]) currentRegion = keys[0];
  select.value = currentRegion;
  data = regionData[currentRegion] || [];
}

// Map internal category code to localized text.
function catLabel(c) {
  return { food:t('cat_food'), drink:t('cat_drink'), dessert:t('cat_dessert'), beauty:t('cat_beauty') }[c] || c;
}

// Map CP value tier to localized text.
function cpLabel(cp) {
  return { [CP_HIGH]:t('cpHigh'), [CP_MEDIUM]:t('cpMedium'), [CP_LOW]:t('cpLow') }[cp] || cp;
}

// Map CP value tier to CSS class suffix.
function cpClass(cp) {
  return { [CP_HIGH]:'high', [CP_MEDIUM]:'medium', [CP_LOW]:'low' }[cp] || 'medium';
}

// Map distance tier to localized text.
function distLabel(dist) {
  return { [DIST_NEAR]:t('distNear'), [DIST_MEDIUM]:t('distMedium'), [DIST_FAR]:t('distFar') }[dist] || dist;
}

// Map distance tier to CSS class suffix.
function distClass(dist) {
  return { [DIST_NEAR]:'near', [DIST_MEDIUM]:'medium', [DIST_FAR]:'far' }[dist] || 'medium';
}

// Convert known Chinese phrases to English when explicit English fields are missing.
function localizeContentText(text) {
  if (typeof text !== 'string') return text;
  if (currentLocale !== 'en') return text;
  let output = text;
  CONTENT_REPLACEMENTS_EN.forEach(([from, to]) => {
    output = output.split(from).join(to);
  });
  return output;
}

// Read locale-specific field when available, then fall back gracefully.
function getLocalizedField(entry, fieldName) {
  const localeSuffix = currentLocale === 'zh' ? '_zh' : '_en';
  const preferred = entry[fieldName + localeSuffix];
  if (typeof preferred === 'string' && preferred.length > 0) return preferred;
  const base = entry[fieldName];
  if (currentLocale === 'en') return localizeContentText(base);
  return base;
}

// Filter, sort, and render all rows for the current UI state.
function render() {
  // Prioritize high value and closer distance at the top of the list.
  const cpRank = { [CP_HIGH]: 3, [CP_MEDIUM]: 2, [CP_LOW]: 1 };
  const distRank = { [DIST_NEAR]: 3, [DIST_MEDIUM]: 2, [DIST_FAR]: 1 };

  // Apply the active filter key from the filter buttons.
  const rows = data.filter(d => {
    if (current === 'all') return true;
    if (current === 'cp-high') return d.cp === CP_HIGH;
    if (current === 'cp-medium') return d.cp === CP_MEDIUM;
    if (current === '4/1' || current === '4/2') return d.batch === current;
    if (current === 'batch-flex') return d.batch === BATCH_FLEX;
    if (current === 'updated') return d.u;
    return d.cat === current;
  }).sort((a, b) => {
    const cpDiff = (cpRank[b.cp] || 0) - (cpRank[a.cp] || 0);
    if (cpDiff !== 0) return cpDiff;
    return (distRank[b.dist] || 0) - (distRank[a.dist] || 0);
  });

  const tbody = document.getElementById('tbody');
  // Render a friendly empty state when no rows match.
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:2rem;color:var(--color-text-tertiary)">${t('noResults')}</td></tr>`;
    return;
  }

  // Build table rows as HTML for fast UI updates.
  tbody.innerHTML = rows.map(d => {
    return `<tr class="${d.u ? 'updated-row' : ''}">
      <td>
        <div class="store-name">${getLocalizedField(d, 'name')}</div>
        <div class="note">${getLocalizedField(d, 'note') || ''}</div>
      </td>
      <td><span class="badge cat-${d.cat}">${catLabel(d.cat)}</span></td>
      <td style="max-width:190px;font-size:12px">${getLocalizedField(d, 'item')}</td>
      <td style="font-size:12px">${getLocalizedField(d, 'member')}</td>
      <td style="white-space:nowrap;font-size:12px">${getLocalizedField(d, 'window')}</td>
      <td><span class="badge cp-${cpClass(d.cp)}">${cpLabel(d.cp)}</span></td>
      <td class="dist-${distClass(d.dist)}">${distLabel(d.dist)}</td>
    </tr>`;
  }).join('');
}

// Initial page bootstrapping sequence.
currentLocale = detectLocale();
applyI18nText();
initRegions();
updateAllButtonCount();
render();