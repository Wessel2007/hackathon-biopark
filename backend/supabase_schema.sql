-- Execute este script no SQL Editor do Supabase (https://supabase.com/dashboard/project/mhejbpthkbcpwjshxzwz/sql)

DROP TABLE IF EXISTS query_history CASCADE;
DROP TABLE IF EXISTS protocols CASCADE;

CREATE TABLE protocols (
    id          BIGSERIAL PRIMARY KEY,
    status      VARCHAR(50)  NOT NULL,
    projeto     VARCHAR(200) NOT NULL,
    protocolo   VARCHAR(100) NOT NULL,
    atividade   VARCHAR(200) NOT NULL,
    orgao_site_consultado VARCHAR(200) NOT NULL,
    atribuido_a VARCHAR(100),
    data_abertura    DATE NOT NULL,
    data_finalizacao DATE,
    situacao    VARCHAR(100),
    anotacoes   TEXT,
    ativo       BOOLEAN NOT NULL DEFAULT TRUE,
    url_consulta VARCHAR(500),
    ultima_consulta      TIMESTAMPTZ,
    observacao_consulta  TEXT,
    criado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE query_history (
    id           BIGSERIAL PRIMARY KEY,
    protocol_id  BIGINT NOT NULL REFERENCES protocols(id) ON DELETE CASCADE,
    status_consultado   VARCHAR(100),
    situacao_consultada VARCHAR(100),
    observacao   TEXT,
    texto_bruto  TEXT,
    houve_mudanca BOOLEAN NOT NULL DEFAULT FALSE,
    erro         TEXT,
    data_consulta TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    data_movimentacao TEXT,
    mudancas_detectadas TEXT,
    fonte_consulta TEXT,
    status_anterior TEXT
);

CREATE INDEX idx_protocols_projeto   ON protocols(projeto);
CREATE INDEX idx_protocols_protocolo ON protocols(protocolo);
CREATE INDEX idx_qh_protocol_id      ON query_history(protocol_id);

-- Trigger para atualizar atualizado_em automaticamente
CREATE OR REPLACE FUNCTION _set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN NEW.atualizado_em = NOW(); RETURN NEW; END;
$$;

CREATE TRIGGER trg_protocols_updated_at
    BEFORE UPDATE ON protocols
    FOR EACH ROW EXECUTE FUNCTION _set_updated_at();

-- Desativa RLS para uso no hackathon (backend usa anon key diretamente)
ALTER TABLE protocols    DISABLE ROW LEVEL SECURITY;
ALTER TABLE query_history DISABLE ROW LEVEL SECURITY;

-- Permissões para a role anon (chave publishable)
GRANT ALL ON TABLE protocols    TO anon;
GRANT ALL ON TABLE query_history TO anon;
GRANT USAGE, SELECT ON SEQUENCE protocols_id_seq      TO anon;
GRANT USAGE, SELECT ON SEQUENCE query_history_id_seq  TO anon;
