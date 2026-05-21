-- Amplia colunas de texto que estouram na importação de planilhas.
-- Execute no SQL Editor do Supabase (https://supabase.com/dashboard)

ALTER TABLE protocols
  ALTER COLUMN projeto TYPE VARCHAR(500),
  ALTER COLUMN atividade TYPE TEXT,
  ALTER COLUMN orgao_site_consultado TYPE VARCHAR(500);
