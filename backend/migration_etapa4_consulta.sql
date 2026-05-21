-- Etapa 4: Persistência completa do resultado de consulta
-- Execute este script no SQL Editor do Supabase

ALTER TABLE query_history ADD COLUMN IF NOT EXISTS fonte_consulta  TEXT;
ALTER TABLE query_history ADD COLUMN IF NOT EXISTS status_anterior TEXT;
