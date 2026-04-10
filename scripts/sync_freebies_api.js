#!/usr/bin/env node

// Batch sync utility that reads freebies data files and POSTs normalized payloads to the FastAPI write endpoint.
// Use this when you want to bootstrap or resync database rows from a source dataset without manual API calls.

const fs = require('fs');
const path = require('path');
const vm = require('vm');

function parseArgs(argv) {
  // Keep runtime configuration simple so the script can be reused for local imports and future crawler output.
  const options = {
    input: 'assets/data/freebies-data.js',
    baseUrl: 'http://localhost:3001',
    region: null,
    dryRun: false,
    limit: null,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--input' && argv[index + 1]) {
      options.input = argv[++index];
      continue;
    }
    if (arg === '--base-url' && argv[index + 1]) {
      options.baseUrl = argv[++index].replace(/\/$/, '');
      continue;
    }
    if (arg === '--region' && argv[index + 1]) {
      options.region = argv[++index];
      continue;
    }
    if (arg === '--limit' && argv[index + 1]) {
      options.limit = Number(argv[++index]);
      continue;
    }
    if (arg === '--dry-run') {
      options.dryRun = true;
      continue;
    }
    if (arg === '--help' || arg === '-h') {
      printHelpAndExit();
    }
  }

  if (options.limit !== null && (!Number.isInteger(options.limit) || options.limit <= 0)) {
    throw new Error('--limit must be a positive integer');
  }

  return options;
}

function printHelpAndExit() {
  console.log(`Usage: node scripts/sync_freebies_api.js [options]\n\nOptions:\n  --input <path>     Source file (default: assets/data/freebies-data.js)\n  --base-url <url>   API base URL (default: http://localhost:3001)\n  --region <code>    Limit sync to one region code\n  --limit <n>        Limit number of entries per region\n  --dry-run          Print payloads without sending requests\n  -h, --help         Show this help message`);
  process.exit(0);
}

function loadDataFile(inputPath) {
  const resolvedPath = path.resolve(process.cwd(), inputPath);
  if (!fs.existsSync(resolvedPath)) {
    throw new Error(`Input file not found: ${resolvedPath}`);
  }

  // JSON is the simplest interchange format for other tools, but we also support the current JS data file.
  if (resolvedPath.endsWith('.json')) {
    const raw = fs.readFileSync(resolvedPath, 'utf8');
    const parsed = JSON.parse(raw);
    return normalizeRegionMap(parsed);
  }

  // Execute the data file in a sandbox so we can read the exported window globals safely.
  const source = fs.readFileSync(resolvedPath, 'utf8');
  const sandbox = { window: {} };
  vm.createContext(sandbox);
  vm.runInContext(source, sandbox, { timeout: 1000 });

  const dataByRegion = sandbox.window.BIRTHDAY_FREEBIES_DATA_BY_REGION || {
    bay_area: sandbox.window.BIRTHDAY_FREEBIES_DATA || [],
  };

  return normalizeRegionMap(dataByRegion);
}

function normalizeRegionMap(input) {
  // Preserve the existing top-level shape: a region-keyed object of arrays.
  if (Array.isArray(input)) {
    return { bay_area: input };
  }
  if (input && typeof input === 'object') {
    return input;
  }
  throw new Error('Source data must be an object keyed by region code or an array of freebies.');
}

function toStringOrEmpty(value) {
  return typeof value === 'string' ? value : '';
}

function buildPayload(regionCode, entry, sortOrder) {
  // Translate source fields into the FastAPI write contract.
  const category = entry.cat || entry.category || 'uncategorized';
  const itemSortOrder = Number.isInteger(entry.sort_order) ? entry.sort_order : sortOrder;

  return {
    region_code: regionCode,
    category,
    sort_order: itemSortOrder,
    zh: {
      name: toStringOrEmpty(entry.name),
      item: toStringOrEmpty(entry.item),
      member: toStringOrEmpty(entry.member),
      window: toStringOrEmpty(entry.window),
      note: toStringOrEmpty(entry.note),
    },
    en: {
      name: toStringOrEmpty(entry.name_en || entry.name),
      item: toStringOrEmpty(entry.item_en || entry.item),
      member: toStringOrEmpty(entry.member_en || entry.member),
      window: toStringOrEmpty(entry.window_en || entry.window),
      note: toStringOrEmpty(entry.note_en || entry.note),
    },
  };
}

async function postJson(url, payload) {
  // POST one normalized freebie at a time so failures are easy to identify and retry.
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(payload),
  });

  const text = await response.text();
  const parsed = text ? safeJsonParse(text) : null;

  if (!response.ok) {
    const detail = parsed ? JSON.stringify(parsed) : text || response.statusText;
    throw new Error(`POST ${url} failed (${response.status}): ${detail}`);
  }

  return parsed ?? text;
}

function safeJsonParse(text) {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const dataByRegion = loadDataFile(options.input);
  const regionEntries = Object.entries(dataByRegion).filter(([regionCode]) => !options.region || regionCode === options.region);

  if (regionEntries.length === 0) {
    console.log('No regions matched the provided filters.');
    return;
  }

  let createdCount = 0;
  let skippedCount = 0;
  const apiBase = options.baseUrl;

  for (const [regionCode, entries] of regionEntries) {
    if (!Array.isArray(entries)) {
      console.warn(`Skipping region ${regionCode}: expected an array of freebies.`);
      skippedCount += 1;
      continue;
    }

    // Limit is useful for smoke testing or incremental syncs while the data model is still changing.
    const limitedEntries = options.limit ? entries.slice(0, options.limit) : entries;
    for (let index = 0; index < limitedEntries.length; index += 1) {
      const payload = buildPayload(regionCode, limitedEntries[index], index + 1);
      if (options.dryRun) {
        // Dry-run prints the exact payload shape without mutating the database.
        console.log(JSON.stringify(payload, null, 2));
        continue;
      }

      const result = await postJson(`${apiBase}/api/freebies`, payload);
      createdCount += 1;
      console.log(`${regionCode} #${index + 1}: ${result.id}`);
    }
  }

  if (options.dryRun) {
    console.log(`Dry run complete for ${regionEntries.length} region(s).`);
    return;
  }

  console.log(`Sync complete. Created ${createdCount} freebie(s), skipped ${skippedCount} region(s).`);
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
