import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

import "dotenv/config";
import { PrismaPg } from "@prisma/adapter-pg";
import { Pool } from "pg";
import { PrismaClient } from "../src/generated/client.ts";

// Seed data is still stored in the browser dataset file, so we read and normalize
// it here instead of duplicating the source of truth.
type RawEntry = {
  name?: string;
  name_en?: string;
  cat?: string;
  item?: string;
  item_en?: string;
  member?: string;
  member_en?: string;
  window?: string;
  window_en?: string;
  note?: string;
  note_en?: string;
};

type RegionDataset = Record<string, RawEntry[]>;

// Execute the browser-style data file in a sandbox so we can reuse its window globals.
function readDataFromBrowserFile(dataFilePath: string): RegionDataset {
  const source = fs.readFileSync(dataFilePath, "utf8");
  const sandbox: { window: Record<string, unknown> } = { window: {} };

  vm.createContext(sandbox);
  vm.runInContext(source, sandbox);

  const byRegion = sandbox.window.BIRTHDAY_FREEBIES_DATA_BY_REGION as
    | RegionDataset
    | undefined;
  const legacy = sandbox.window.BIRTHDAY_FREEBIES_DATA as RawEntry[] | undefined;

  if (byRegion && typeof byRegion === "object") {
    return byRegion;
  }

  if (Array.isArray(legacy)) {
    return { bay_area: legacy };
  }

  throw new Error("Unable to find freebie data on window.BIRTHDAY_FREEBIES_DATA_BY_REGION");
}

// Convert a region code like `bay_area` into a readable fallback name.
function formatRegionName(regionCode: string): string {
  return regionCode
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

  // Normalize optional text fields to empty strings before writing to the database.
function textValue(value: string | undefined): string {
  return typeof value === "string" ? value : "";
}

async function run(): Promise<void> {
    // Seed requires a live PostgreSQL connection from backend/.env.
  const connectionString = process.env.DATABASE_URL;
  if (!connectionString) {
    throw new Error("DATABASE_URL is required to run seed.");
  }

    // Prisma 7 uses a database driver adapter for runtime connections.
  const pool = new Pool({ connectionString });
  const adapter = new PrismaPg(pool);
  const prisma = new PrismaClient({ adapter });

    // Resolve the dataset path relative to this script so it works from any cwd.
  const currentDir = path.dirname(fileURLToPath(import.meta.url));
  const dataPath = path.resolve(currentDir, "../../assets/data/freebies-data.js");
  const datasetByRegion = readDataFromBrowserFile(dataPath);

  console.log(`Seeding regions from ${dataPath}`);

  for (const [regionCode, entries] of Object.entries(datasetByRegion)) {
      // Upsert regions so rerunning the seed keeps the same primary keys stable.
    const region = await prisma.region.upsert({
      where: { code: regionCode },
      update: { name: formatRegionName(regionCode) },
      create: {
        code: regionCode,
        name: formatRegionName(regionCode),
      },
    });

    // Keep this seed idempotent by replacing one region's freebies each run.
    await prisma.freebie.deleteMany({ where: { regionId: region.id } });

    // Write one freebie row plus zh/en localized text rows for each source entry.
    for (const [index, entry] of entries.entries()) {
      await prisma.freebie.create({
        data: {
          regionId: region.id,
          category: textValue(entry.cat),
          isActive: true,
          sortOrder: index,
          texts: {
            create: [
              {
                locale: "zh",
                name: textValue(entry.name),
                item: textValue(entry.item),
                member: textValue(entry.member),
                redemptionWindow: textValue(entry.window),
                note: textValue(entry.note),
              },
              {
                locale: "en",
                name: textValue(entry.name_en || entry.name),
                item: textValue(entry.item_en || entry.item),
                member: textValue(entry.member_en || entry.member),
                redemptionWindow: textValue(entry.window_en || entry.window),
                note: textValue(entry.note_en || entry.note),
              },
            ],
          },
        },
      });
    }

    console.log(`Seeded region=${regionCode}, entries=${entries.length}`);
  }

  // Always release the database connection pool before exiting.
  await prisma.$disconnect();
  await pool.end();
  console.log("Seeding completed.");
}

// Fail fast with a visible error if any import step breaks.
run().catch(async (error) => {
  console.error("Seeding failed:", error);
  process.exitCode = 1;
});