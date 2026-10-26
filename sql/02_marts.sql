CREATE SCHEMA IF NOT EXISTS marts;

CREATE OR REPLACE VIEW marts.os_chamados AS
SELECT
    ticket_id,
    os_falha,
    escola,
    status,
    data_criacao,
    data_finalizacao,
    dias_em_aberto,
    regional,
    uf,
    DATE_TRUNC('month', data_criacao)::date AS mes_criacao
FROM clean.os_chamado;

CREATE OR REPLACE VIEW marts.execucoes AS
SELECT started_at, finished_at, status, rows_extracted, rows_loaded
FROM ops.pipeline_runs;
