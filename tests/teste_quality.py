import pandas as pd

import quality
from quality import verificar, falhas_criticas


def _df(**campos):
    base = {
        "ticket_id": ["OS-001"],
        "escola": ["Escola Teste"],
        "status": ["ABERTA"],
        "data_criacao": [pd.Timestamp("2026-09-10 08:00")],
        "data_finalizacao": [pd.NaT],
    }
    base.update(campos)
    return pd.DataFrame(base)


def _por_nome(resultados, nome):
    return next(r for r in resultados if r.nome == nome)


def test_dados_validos_nao_geram_falha_critica():
    resultados = verificar(_df(), extraidos=1)
    assert falhas_criticas(resultados) == []


def test_finalizacao_antes_da_criacao_e_critica():
    df = _df(data_finalizacao=[pd.Timestamp("2026-09-09 08:00")])
    resultados = verificar(df, extraidos=1)
    assert _por_nome(resultados, "finalizacao_antes_da_criacao").passou is False
    assert len(falhas_criticas(resultados)) == 1


def test_data_no_futuro_e_critica():
    df = _df(data_criacao=[pd.Timestamp("2099-01-01 08:00")])
    resultados = verificar(df, extraidos=1)
    assert _por_nome(resultados, "data_criacao_no_futuro").passou is False


def test_descarte_alto_gera_warning_nao_critica():
    resultados = verificar(_df(), extraidos=100)  # 99% descartados
    taxa = _por_nome(resultados, "taxa_de_descarte")
    assert taxa.passou is False
    assert taxa.severidade == "WARNING"
    assert falhas_criticas(resultados) == []


def test_dominio_de_status_so_valida_quando_configurado(monkeypatch):
    df = _df(status=["ESTRANHO"])
    resultados = verificar(df, extraidos=1)
    assert not any(r.nome == "status_dentro_do_dominio" for r in resultados)

    monkeypatch.setattr(quality, "STATUS_ESPERADOS", {"ABERTA", "FECHADA"})
    resultados = verificar(df, extraidos=1)
    assert _por_nome(resultados, "status_dentro_do_dominio").passou is False


def test_zero_registros_gera_warning():
    resultados = verificar(_df().iloc[0:0], extraidos=0)
    assert _por_nome(resultados, "registros_extraidos").passou is False
    assert falhas_criticas(resultados) == []