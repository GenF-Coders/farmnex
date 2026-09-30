-- FarmNex Crop Rescue: make the cr_buyer_pool view respect row-level security.
--
-- Supabase's security check flags a normal view as "security definer": it reads
-- the underlying table with the view creator's rights, which could let the public
-- API read cr_demo_buyers through the view. security_invoker = true makes the view
-- use the caller's rights instead. The backend is unaffected (it connects as the
-- database owner). Safe to run twice. Applied to the main DB on 2026-09-30.
--
-- Run after 010_cr_crop_rescue.sql.

BEGIN;

ALTER VIEW cr_buyer_pool SET (security_invoker = true);

COMMIT;
