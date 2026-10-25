from datetime import date

from incremental import calcular_janela


def test_primeira_execucao_usa_data_inicial():
    assert calcular_janela(None, date(2026, 10, 24)) == ("01/01/2026", "10/24/2026")


def test_usa_sobreposicao_de_um_dia():
    assert calcular_janela(date(2026, 10, 20), date(2026, 10, 24)) == ("10/19/2026", "10/24/2026")


def test_inicio_nunca_passa_de_hoje():
    assert calcular_janela(date(2026, 10, 30), date(2026, 10, 24)) == ("10/24/2026", "10/24/2026")

