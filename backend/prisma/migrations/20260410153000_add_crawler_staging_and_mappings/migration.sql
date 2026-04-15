-- CreateTable
CREATE TABLE "crawler_staging_freebies" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid()::text,
    "source_system" TEXT NOT NULL,
    "source_key" TEXT NOT NULL,
    "region_code" TEXT NOT NULL,
    "category" TEXT NOT NULL,
    "payload_json" JSONB NOT NULL,
    "content_hash" TEXT NOT NULL,
    "fetched_at" TIMESTAMP(3) NOT NULL,
    "normalized_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "promoted_at" TIMESTAMP(3),
    "promoted_freebie_id" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "crawler_staging_freebies_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "crawler_promoted_mappings" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid()::text,
    "source_system" TEXT NOT NULL,
    "source_key" TEXT NOT NULL,
    "freebie_id" TEXT NOT NULL,
    "content_hash" TEXT NOT NULL,
    "last_promoted_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "crawler_promoted_mappings_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "crawler_staging_freebies_source_system_source_key_key" ON "crawler_staging_freebies"("source_system", "source_key");

-- CreateIndex
CREATE UNIQUE INDEX "crawler_promoted_mappings_source_system_source_key_key" ON "crawler_promoted_mappings"("source_system", "source_key");

-- AddForeignKey
ALTER TABLE "crawler_promoted_mappings" ADD CONSTRAINT "crawler_promoted_mappings_freebie_id_fkey" FOREIGN KEY ("freebie_id") REFERENCES "freebies"("id") ON DELETE CASCADE ON UPDATE CASCADE;