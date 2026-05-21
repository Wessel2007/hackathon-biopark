-- Execute no SQL Editor do Supabase:
-- https://supabase.com/dashboard/project/mhejbpthkbcpwjshxzwz/sql

ALTER TABLE query_history
  ADD COLUMN IF NOT EXISTS screenshot_base64 TEXT;
