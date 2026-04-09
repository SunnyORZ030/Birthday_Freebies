-- CreateTable
CREATE TABLE "regions" (
    "id" TEXT NOT NULL,
    "code" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "regions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "freebies" (
    "id" TEXT NOT NULL,
    "region_id" TEXT NOT NULL,
    "category" TEXT NOT NULL,
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "sort_order" INTEGER NOT NULL DEFAULT 0,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "freebies_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "freebie_texts" (
    "id" TEXT NOT NULL,
    "freebie_id" TEXT NOT NULL,
    "locale" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "item" TEXT NOT NULL,
    "member" TEXT NOT NULL,
    "redemption_window" TEXT NOT NULL,
    "note" TEXT NOT NULL DEFAULT '',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "freebie_texts_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "regions_code_key" ON "regions"("code");

-- CreateIndex
CREATE UNIQUE INDEX "freebie_texts_freebie_id_locale_key" ON "freebie_texts"("freebie_id", "locale");

-- AddForeignKey
ALTER TABLE "freebies" ADD CONSTRAINT "freebies_region_id_fkey" FOREIGN KEY ("region_id") REFERENCES "regions"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "freebie_texts" ADD CONSTRAINT "freebie_texts_freebie_id_fkey" FOREIGN KEY ("freebie_id") REFERENCES "freebies"("id") ON DELETE CASCADE ON UPDATE CASCADE;
