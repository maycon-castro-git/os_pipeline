CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS clean;
CREATE SCHEMA IF NOT EXISTS ops;

-- Camada raw: resposta da API como recebida, para reprocessar sem gastar cota
CREATE TABLE IF NOT EXISTS raw.os_payload (
    payload_id  BIGSERIAL PRIMARY KEY,
    run_id      UUID        NOT NULL,
    loaded_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    payload     JSONB       NOT NULL
);

-- Camada clean: um registro por chamado
CREATE TABLE IF NOT EXISTS clean.os_chamado (
    ticket_id           TEXT        PRIMARY KEY,
    os_falha            TEXT,
    escola              TEXT        NOT NULL,
    inep                TEXT,
    id_externo          TEXT,
    status              TEXT        NOT NULL,
    data_criacao        TIMESTAMP   NOT NULL,
    ultima_atualizacao  TIMESTAMP,
    data_finalizacao    TIMESTAMP,
    ultima_nota         TEXT,
    dias_em_aberto      NUMERIC(10,2),
    regional            TEXT,
    uf                  TEXT,
    run_id              UUID        NOT NULL,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_datas CHECK (data_finalizacao IS NULL OR data_finalizacao >= data_criacao)
);

CREATE INDEX IF NOT EXISTS idx_os_escola       ON clean.os_chamado (escola);
CREATE INDEX IF NOT EXISTS idx_os_data_criacao ON clean.os_chamado (data_criacao);

-- Operação: uma linha por execução
CREATE TABLE IF NOT EXISTS ops.pipeline_runs (
    run_id          UUID        PRIMARY KEY,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at     TIMESTAMPTZ,
    status          TEXT        NOT NULL DEFAULT 'RUNNING'
                    CHECK (status IN ('RUNNING', 'SUCCESS', 'FAILED')),
    rows_extracted  INTEGER,
    rows_loaded     INTEGER,
    error_message   TEXT
);

-- Operação: uma linha por checagem por execução
CREATE TABLE IF NOT EXISTS ops.data_quality_checks (
    check_id     BIGSERIAL   PRIMARY KEY,
    run_id

