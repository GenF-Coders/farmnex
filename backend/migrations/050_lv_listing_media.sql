-- Lot photos/videos and the admin's "Verified by FarmNex" decision.
--
-- Safety: this file only ADDS two new `lv_`-prefixed tables and their indexes, and turns on
-- row-level security for them. It never touches an existing table. Running it twice is a no-op.
-- (The backend's startup create_all may already have made the tables; then only the RLS lines act.)
--
-- Run this once, by hand, in the Supabase SQL editor. Nothing in this repo runs it automatically.

BEGIN;

CREATE TABLE IF NOT EXISTS public.lv_listing_media (
    id              SERIAL PRIMARY KEY,
    public_id       UUID NOT NULL UNIQUE,
    listing_id      INTEGER NOT NULL REFERENCES public.product_listings(id) ON DELETE CASCADE,
    uploaded_by_id  INTEGER NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    kind            VARCHAR(10) NOT NULL,
    storage_path    VARCHAR(1024) NOT NULL,
    content_type    VARCHAR(100) NOT NULL,
    size_bytes      INTEGER NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_lv_listing_media_listing_id ON public.lv_listing_media (listing_id);
CREATE INDEX IF NOT EXISTS ix_lv_listing_media_uploaded_by_id ON public.lv_listing_media (uploaded_by_id);
CREATE INDEX IF NOT EXISTS ix_lv_listing_media_created_at ON public.lv_listing_media (created_at);

CREATE TABLE IF NOT EXISTS public.lv_listing_verifications (
    id              SERIAL PRIMARY KEY,
    listing_id      INTEGER NOT NULL UNIQUE REFERENCES public.product_listings(id) ON DELETE CASCADE,
    status          VARCHAR(10) NOT NULL,
    reason          TEXT,
    reviewed_by_id  INTEGER REFERENCES public.users(id) ON DELETE SET NULL,
    reviewed_at     TIMESTAMPTZ,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE public.lv_listing_media ENABLE ROW LEVEL SECURITY;          -- no policies: only the backend reads/writes
ALTER TABLE public.lv_listing_verifications ENABLE ROW LEVEL SECURITY;  -- no policies: only the backend reads/writes

COMMIT;
