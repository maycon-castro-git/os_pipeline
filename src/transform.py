import logging
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)

REGIONAL_PADRAO = "Nordeste I"
UF_PADRAO = "MA"

MAPA_COLUNAS = {
    "Protocolo": "ticket_id",
    "OS Falha": "os_falha",
    "Escola": "escola",
    "INEP": "inep",
    "ID Externo": "id_externo",
    "Status": "status",
    "Data de Criacao": "data_criacao",
    "Ultima Atualizacao": "ultima_atualizacao",
    "Finalizado em": "data_finalizacao",
    "Ultima Nota": "ultima_nota",
}

COLUNAS_FINAIS = [
    "ticket_id", "os_falha", "escola", "inep", "id_externo", "status",
    "data_criacao", "ultima_atualizacao", "data_finalizacao", "ultima_nota",
    "dias_em_aberto", "regional", "uf",
]


def _texto(valor) -> str:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ""
    return str(valor).strip()


def _parse_datas(serie: pd.Series) -> pd.Series:
    """Formato da API: dd/mm/aaaa HH:MM, com fallback para dd/mm/aaaa."""
    limpa = serie.map(_texto).replace({"None": None, "N/D": None, "": None})
    com_hora = pd.to_datetime(limpa, format="%d/%m/%Y %H:%M", errors="coerce")
    so_data = pd.to_datetime(limpa, format="%d/%m/%Y", errors="coerce")
    return com_hora.fillna(so_data)


def preparar(registros: list[dict], run_id: str) -> pd.DataFrame:
    """Converte os registros da API no formato da tabela clean.os_chamado."""
    if not registros:
        return pd.DataFrame(columns=COLUNAS_FINAIS + ["run_id"])

    df = pd.DataFrame(registros).rename(columns=MAPA_COLUNAS)

    for coluna in MAPA_COLUNAS.values():
        if coluna not in df.columns:
            df[coluna] = None

    # Datas
    for coluna in ["data_criacao", "ultima_atualizacao", "data_finalizacao"]:
        df[coluna] = _parse_datas(df[coluna])

    # Textos
    for coluna in ["ticket_id", "escola", "status", "os_falha", "inep", "id_externo", "ultima_nota"]:
        df[coluna] = df[coluna].map(_texto)
    df["status"] = df["status"].str.upper()

    # Rejeita registros sem os campos mínimos e registra quantos foram
    valido = (
        (df["ticket_id"] != "")
        & (df["escola"] != "")
        & (df["status"] != "")
        & df["data_criacao"].notna()
    )
    rejeitados = int((~valido).sum())
    if rejeitados:
        logger.warning("%d registro(s) rejeitado(s) por falta de campos obrigatórios", rejeitados)
    df = df[valido].copy()

    # Duplicados de Protocolo: fica o registro com atualização mais recente
        antes = len(df)
    df = (
        df.sort_values("ultima_atualizacao", na_position="first")
        .drop_duplicates(subset="ticket_id", keep="last")
        .reset_index(drop=True)
         )
    if len(df) < antes:
        logger.warning("%d registro(s) duplicado(s) por Protocolo removido(s)", antes - len(df))

    # Campos derivados
    agora = datetime.now()
    fim = df["data_finalizacao"].fillna(pd.Timestamp(agora))
    df["dias_em_aberto"] = ((fim - df["data_criacao"]).dt.total_seconds() / 86400).round(2)
    df["regional"] = REGIONAL_PADRAO
    df["uf"] = UF_PADRAO
    df["run_id"] = run_id

    logger.info("Status encontrados nesta carga: %s", sorted(df["status"].unique()))

    return df[COLUNAS_FINAIS + ["run_id"]]