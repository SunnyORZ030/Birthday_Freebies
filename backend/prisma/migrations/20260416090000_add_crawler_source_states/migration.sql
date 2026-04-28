-- CreateTable
CREATE TABLE "crawler_source_states" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid()::text,
    "source_system" TEXT NOT NULL,
    "source_key" TEXT NOT NULL,
    "etag" TEXT,
    "last_modified" TEXT,
    "last_checked_at" TIMESTAMP(3),
    "last_success_at" TIMESTAMP(3),
    "last_changed_at" TIMESTAMP(3),
    "last_content_hash" TEXT,
    "consecutive_failures" INTEGER NOT NULL DEFAULT 0,
    "last_error" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "crawler_source_states_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "crawler_source_states_source_system_source_key_key" ON "crawler_source_states"("source_system", "source_key");
