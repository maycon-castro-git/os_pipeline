import logging

import pandas as pd
import psycopg
from psycopg.types.json import Jsonb

logger = logging.getLogger(__name__)

SQL_UPSERT_CLEAN = """
INSERT INTO clean.os_chamado (
    ticket_id, os_falha, escola, inep, id_externo, status,
    data_criacao, ultima_atualizacao, data_finalizacao, ultima_nota,
    dias_em_aberto, regional, uf, run_id, updated_at
) VALUES (
    %(ticket_id)s, %(os_falha)s, %(escola)s, %(inep)s, %(id_externo)s, %(status)s,
    %(data_criacao)s, %(ultima_atualizacao)s, %(data_finalizacao)s, %(ultima_nota)s,
    %(dias_em_aberto)s, %(regional)s, %(uf)s, %(run_id)s, now()
)
ON CONFLICT (ticket_id) DO UPDATE SET
    os_falha           = EXCLUDED.os_falha,
    escola             = EXCLUDED.escola,
    inep               = EXCLUDED.inep,
    id_externo         = EXCLUDED.id_externo,
    status             = EXCLUDED.status,
    data_criacao       = EXCLUDED.data_criacao,
    ultima_atualizacao = EXCLUDED.ultima_atualizacao,
    data_finalizacao   = EXCLUDED.data_finalizacao,
    ultima_nota        = EXCLUDED.ultima_nota,
    dias_em_aberto     = EXCLUDED.dias_em_aberto,
    regional           = EXCLUDED.regional,
    uf                 = EXCLUDED.uf,
    run_id             = EXCLUDED.run_id,
    updated_at         = now()
"""


def criar_run(conn: psycopg.Connection, run_id: str) -> None:
    conn.execute(
        "INSERT INTO ops.pipeline_runs (run_id, status) VALUES (%s, 'RUNNING')",
        (run_id,),
    )


def finalizar_run(conn, run_id, status, extraidos=None, carregados=None, erro=None) -> None:
    conn.execute(
        """
        UPDATE ops.pipeline_runs
        SET finished_at = now(), status = %s,
            rows_extracted = %s, rows_loaded = %s, error_message = %s
        WHERE run_id = %s
        """,
        (status, extraidos, carregados, erro, run_id),
    )


def salvar_raw(conn: psycopg.Connection, run_id: str, registros: list[dict]) -> None:
    """Guarda a resposta bruta, para reprocessar sem chamar a API de novo."""
    if not registros:
        return
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO raw.os_payload (run_id, payload) VALUES (%s, %s)",
            [(run_id, Jsonb(r)) for r in registros],
        )


def carregar_clean(conn: psycopg.Connection, df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    # Converte NaN/NaT em None para o PostgreSQL aceitar
    linhas = df.astype(object).where(df.notna(), None).to_dict("records")
    with conn.cursor() as cur:
        cur.executemany(SQL_UPSERT_CLEAN, linhas)
    return len(linhas)
