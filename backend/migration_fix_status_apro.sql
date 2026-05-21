-- Corrige registros com status 'APRO' (qualquer capitalização) para 'APROVADO'
-- Execute no SQL Editor do Supabase

UPDATE protocols
SET status = 'APROVADO'
WHERE UPPER(TRIM(status)) IN ('APRO', 'APRO.');
