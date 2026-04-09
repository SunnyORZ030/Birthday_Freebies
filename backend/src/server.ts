import "dotenv/config";

import http from "node:http";
import { URL } from "node:url";

import { PrismaPg } from "@prisma/adapter-pg";
import { Pool } from "pg";

import { PrismaClient } from "./generated/client.ts";

type ApiEntry = {
  name: string;
  name_en: string;
  cat: string;
  u: boolean;
  item: string;
  item_en: string;
  member: string;
  member_en: string;
  window: string;
  window_en: string;
  note: string;
  note_en: string;
};

type ApiResponse = {
  dataByRegion: Record<string, ApiEntry[]>;
};

type RegionsResponse = {
  regions: Array<{ code: string; name: string }>;
};

// The API reads from the same PostgreSQL database used by Prisma migrations and seed data.
const PORT = Number(process.env.PORT || 3001);
const DATABASE_URL = process.env.DATABASE_URL;

if (!DATABASE_URL) {
  throw new Error("DATABASE_URL is required to start the backend server.");
}

const pool = new Pool({ connectionString: DATABASE_URL });
const adapter = new PrismaPg(pool);
const prisma = new PrismaClient({ adapter });

// Serialize JSON responses and apply permissive CORS so the static frontend can call this API.
function writeJson(res: http.ServerResponse, statusCode: number, payload: unknown): void {
  res.statusCode = statusCode;
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.end(JSON.stringify(payload));
}

// Pick one localized text row from the freebie_texts relation.
function textByLocale(
  texts: { locale: string; name: string; item: string; member: string; redemptionWindow: string; note: string }[],
  locale: string,
): { name: string; item: string; member: string; redemptionWindow: string; note: string } | null {
  return texts.find((text) => text.locale === locale) || null;
}

// Return freebies grouped by region so the frontend can keep its current region selector.
async function getFreebiesData(regionCode: string | null): Promise<ApiResponse> {
  const rows = await prisma.freebie.findMany({
    where: {
      isActive: true,
      region: regionCode ? { code: regionCode } : undefined,
    },
    include: {
      region: {
        select: {
          code: true,
        },
      },
      texts: {
        select: {
          locale: true,
          name: true,
          item: true,
          member: true,
          redemptionWindow: true,
          note: true,
        },
      },
    },
    orderBy: [{ regionId: "asc" }, { sortOrder: "asc" }, { createdAt: "asc" }],
  });

  const dataByRegion: Record<string, ApiEntry[]> = {};

  for (const row of rows) {
    const zh = textByLocale(row.texts, "zh");
    const en = textByLocale(row.texts, "en");

    const entry: ApiEntry = {
      name: zh?.name || en?.name || "",
      name_en: en?.name || zh?.name || "",
      cat: row.category,
      u: false,
      item: zh?.item || en?.item || "",
      item_en: en?.item || zh?.item || "",
      member: zh?.member || en?.member || "",
      member_en: en?.member || zh?.member || "",
      window: zh?.redemptionWindow || en?.redemptionWindow || "",
      window_en: en?.redemptionWindow || zh?.redemptionWindow || "",
      note: zh?.note || en?.note || "",
      note_en: en?.note || zh?.note || "",
    };

    if (!dataByRegion[row.region.code]) {
      dataByRegion[row.region.code] = [];
    }
    dataByRegion[row.region.code].push(entry);
  }

  return { dataByRegion };
}

// Expose region metadata so the frontend can build the dropdown from the database.
async function getRegionsData(): Promise<RegionsResponse> {
  const regions = await prisma.region.findMany({
    select: {
      code: true,
      name: true,
    },
    orderBy: {
      code: "asc",
    },
  });

  return { regions };
}

const server = http.createServer(async (req, res) => {
  const method = req.method || "GET";

  // Handle browser preflight requests from the static site.
  if (method === "OPTIONS") {
    res.statusCode = 204;
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type");
    res.end();
    return;
  }

  const url = new URL(req.url || "/", `http://${req.headers.host || "localhost"}`);

  try {
    // Lightweight health check for local development and startup verification.
    if (method === "GET" && url.pathname === "/health") {
      writeJson(res, 200, { ok: true });
      return;
    }

    // Main data endpoint consumed by the frontend.
    if (method === "GET" && url.pathname === "/api/freebies") {
      const region = url.searchParams.get("region");
      const payload = await getFreebiesData(region);
      writeJson(res, 200, payload);
      return;
    }

    // Region metadata endpoint used to populate the dropdown.
    if (method === "GET" && url.pathname === "/api/regions") {
      const payload = await getRegionsData();
      writeJson(res, 200, payload);
      return;
    }

    // Keep unknown routes explicit so local debugging is straightforward.
    writeJson(res, 404, { error: "Not found" });
  } catch (error) {
    // Surface unexpected failures in the server log and return a generic error to clients.
    console.error("Request failed:", error);
    writeJson(res, 500, { error: "Internal server error" });
  }
});

// Start the local API server.
server.listen(PORT, () => {
  console.log(`Backend API server ready on http://localhost:${PORT}`);
});

// Clean shutdown so the Prisma connection pool closes cleanly.
process.on("SIGINT", async () => {
  await prisma.$disconnect();
  await pool.end();
  server.close(() => process.exit(0));
});

// Handle container or process manager termination signals.
process.on("SIGTERM", async () => {
  await prisma.$disconnect();
  await pool.end();
  server.close(() => process.exit(0));
});