import logging
from dataclasses import dataclass

import pandas as pd
import psycopg

logger = logging.getLogger(__name__)

STATUS_ESPERADOS: set[str] | None = {"CONCLUÍDO", "PARALISADOS"}

TOLERANCIA_FUTURO = pd.Timedelta(days=1)
TAXA_DESCARTE_MAXIMA = 0.05  # 5%


class QualityError(Exception):
    """Falha crítica de qualidade: a carga não é executada."""

@dataclass
class ResultadoCheck:
    nome: str
    severidade: str          
    passou: bool
    linhas_com_falha: int = 0
    detalhe: str = ""


def verificar(df: pd.DataFrame, extraidos: int) -> list[ResultadoCheck]:
    """
    Roda as checagens sobre o DataFrame já transformado.
    'extraidos' é o total de registros que a API devolveu, antes da transformação.
    """
    resultados: list[ResultadoCheck] = []
    agora = pd.Timestamp.now()

    fim_antes = df["data_finalizacao"].notna() & (df["data_finalizacao"] < df["data_criacao"])
    resultados.append(ResultadoCheck(
        nome="finalizacao_antes_da_criacao",
        severidade="CRITICAL",
        passou=not fim_antes.any(),
        linhas_com_falha=int(fim_antes.sum()),
    ))

    futuro = df["data_criacao"] > agora + TOLERANCIA_FUTURO
    resultados.append(ResultadoCheck(
        nome="data_criacao_no_futuro",
        severidade="CRITICAL",
        passou=not futuro.any(),
        linhas_com_falha=int(futuro.sum()),
    ))

    obrigatorio_nulo = (
        df[["ticket_id", "escola", "status"]].eq("").any(axis=1)
        | df["data_criacao"].isna()
    )
    resultados.append(ResultadoCheck(
        nome="campos_obrigatorios_preenchidos",
        severidade="CRITICAL",
        passou=not obrigatorio_nulo.any(),
        linhas_com_falha=int(obrigatorio_nulo.sum()),
    ))

    if extraidos > 0:
        descartados = extraidos - len(df)
        taxa = descartados / extraidos
        resultados.append(ResultadoCheck(
            nome="taxa_de_descarte",
            severidade="WARNING",
            passou=taxa <= TAXA_DESCARTE_MAXIMA,
            linhas_com_falha=descartados,
            detalhe=f"{taxa:.1%} descartados (limite {TAXA_DESCARTE_MAXIMA:.0%})",
        ))

    if STATUS_ESPERADOS is not None:
        fora = ~df["status"].isin(STATUS_ESPERADOS)
        resultados.append(ResultadoCheck(
            nome="status_dentro_do_dominio",
            severidade="WARNING",
            passou=not fora.any(),
            linhas_com_falha=int(fora.sum()),
            detalhe=f"valores fora do domínio: {sorted(df.loc[fora, 'status'].unique())}" if fora.any() else "",
        ))

    resultados.append(ResultadoCheck(
        nome="registros_extraidos",
        severidade="WARNING",
        passou=extraidos > 0,
        detalhe="API não retornou OS neste período" if extraidos == 0 else "",
    ))

    for r in resultados:
        nivel = logging.WARNING if not r.passou else logging.INFO
        logger.log(nivel, "Check %-35s %-9s %s", r.nome, "OK" if r.passou else "FALHOU", r.detalhe)

    return resultados


def falhas_criticas(resultados: list[ResultadoCheck]) -> list[ResultadoCheck]:
    return [r for r in resultados if r.severidade == "CRITICAL" and not r.passou]


def salvar_checks(conn: psycopg.Connection, run_id: str, resultados: list[ResultadoCheck]) -> None:
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO ops.data_quality_checks
                (run_id, check_name, severity, passed, failed_rows)
            VALUES (%s, %s, %s, %s, %s)
            """,
            [(run_id, r.nome, r.severidade, r.passou, r.linhas_com_falha) for r in resultados],
        )