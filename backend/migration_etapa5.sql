-- Etapa 5: Comparar com histórico
-- Execute este script no SQL Editor do Supabase

ALTER TABLE query_history ADD COLUMN IF NOT EXISTS data_movimentacao TEXT;
ALTER TABLE query_history ADD COLUMN IF NOT EXISTS mudancas_detectadas TEXT;
