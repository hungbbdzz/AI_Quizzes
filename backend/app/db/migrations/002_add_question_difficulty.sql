-- ============================================================
-- Add per-question difficulty fields
-- ============================================================

alter table questions
  add column if not exists difficulty_label text,
  add column if not exists difficulty_score float,
  add column if not exists difficulty_version text;
