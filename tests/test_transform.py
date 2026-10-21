import pandas as pd
import pytest

from transform import preparar

RUN_ID = "11111111-1111-1111-1111-111111111111"


def _registro(**campos):
    """Registro base no formato da API, com campos sobrescritos conforme o teste."""
    base = {
        "Protocolo": "OS-001",
        "OS Falha": "Sem conexão",
        "Escola": "Escola Teste",
        "INEP": "12345678",
        "ID Externo": "EXT-1",
        "Status": "aberta",
        "Data de Criacao": "10/09/2026 08:00",
        "Ultima Atualizacao": "10/09/2026 09:00",
        "Finalizado em": "N/D",
        "Ultima Nota": "Técnico acionado",
    }
    base.update(campos)
    return base


def test_lista_vazia_retorna_dataframe_vazio():
    df = preparar([], RUN_ID)
    assert df.empty


def test_converte_datas_no_formato_da_api():
    df = preparar([_registro()], RUN_ID)
    assert df.loc[0, "data_criacao"] == pd.Timestamp("2026-09-10 08:00")
    assert pd.isna(df.loc[0, "data_finalizacao"])


def test_status_fica_em_maiusculas():
    df = preparar([_registro(Status="aberta")], RUN_ID)
    assert df.loc[0, "status"] == "ABERTA"


def test_registro_sem_escola_e_rejeitado():
    df = preparar([_registro(Escola="")], RUN_ID)
    assert df.empty


def test_registro_sem_data_de_criacao_e_rejeitado():
    df = preparar([_registro(**{"Data de Criacao": "N/D"})], RUN_ID)
    assert df.empty


def test_duplicado_por_protocolo_fica_o_mais_recente():
    antigo = _registro(**{"Ultima Atualizacao": "10/09/2026 09:00", "Status": "aberta"})
    novo = _registro(**{"Ultima Atualizacao": "11/09/2026 09:00", "Status": "fechada"})
    df = preparar([antigo, novo], RUN_ID)
    assert len(df) == 1
    assert df.loc[0, "status"] == "FECHADA"


def test_dias_em_aberto_com_finalizacao():
    df = preparar(
        [_registro(**{"Finalizado em": "11/09/2026 08:00"})],
        RUN_ID,
    )
    assert df.loc[0, "dias_em_aberto"] == pytest.approx(1.0)


def test_regional_e_uf_padrao():
    df = preparar([_registro()], RUN_ID)
    assert df.loc[0, "regional"] == "Nordeste I"
    assert df.loc[0, "uf"] == "MA"