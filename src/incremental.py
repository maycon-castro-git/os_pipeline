from datetime import date, timedelta

FORMATO_API = "%m/%d/%Y"
DATA_INICIAL_PADRAO = date(2026, 1, 1)
SOBREPOSICAO_DIAS = 1


def calcular_janela(ultima_carga: date | None, hoje: date) -> tuple[str, str]:

    if ultima_carga is None:
        inicio = DATA_INICIAL_PADRAO
    else:
        inicio = ultima_carga - timedelta(days=SOBREPOSICAO_DIAS)

    if inicio > hoje:
        inicio = hoje

    return inicio.strftime(FORMATO_API), hoje.strftime(FORMATO_API)


