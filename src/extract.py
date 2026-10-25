import json
import logging
import os
import time

import requests

logger = logging.getLogger(__name__)

MAX_TENTATIVAS = 1
TIMEOUT_SEGUNDOS = 120


class SisopAPIError(Exception):
    """Erro ao consultar a API do SISOP."""


def _interpretar_corpo(resp: requests.Response) -> list[dict]:
    """Aceita JSON padrão ou o texto 'OS[...]' que a API às vezes devolve."""
    try:
        data = resp.json()
    except ValueError:
        texto = resp.text.strip()
        inicio = texto.find("[")
        if inicio == -1:
            raise SisopAPIError(f"Resposta sem array. Trecho: {texto[:300]!r}")
        try:
            return json.loads(texto[inicio:])
        except json.JSONDecodeError as e:
            raise SisopAPIError(f"Array inválido: {e}") from e

    if data.get("status") != "success":
        raise SisopAPIError(f"API retornou erro: {data}")
    return data.get("response", {}).get("Os", [])


def extrair_os(data_inicio: str, data_fim: str) -> list[dict]:
    """
    Busca as OSs no período. Datas no formato MM/DD/AAAA.
    Atenção: o endpoint só responde entre 19h e 9h.
    """
    url = os.getenv("SISOP_API_URL")
    key = os.getenv("SISOP_API_KEY")
    if not url or not key:
        raise SisopAPIError("SISOP_API_URL ou SISOP_API_KEY não configurados no .env")

    headers = {
        "key": key,
        "Content-Type": "application/json",
        "data_inicio": data_inicio,
        "data_fim": data_fim,
    }

    ultimo_erro = None
    for tentativa in range(1, MAX_TENTATIVAS + 1):
        logger.info("Consultando OSs de %s até %s (tentativa %d)", data_inicio, data_fim, tentativa)
        try:
            resp = requests.post(url, headers=headers, timeout=TIMEOUT_SEGUNDOS)
            resp.raise_for_status()
        except requests.RequestException as e:
            ultimo_erro = e
            logger.warning("Falha na requisição: %s", e)
            if tentativa < MAX_TENTATIVAS:
                time.sleep(2 ** tentativa)
            continue

        registros = _interpretar_corpo(resp)
        logger.info("%d OS(s) recebida(s) da API", len(registros))
        return registros

    raise SisopAPIError(
        f"Falha após {MAX_TENTATIVAS} tentativas. Se estiver fora da janela 19h–9h, "
        f"é esperado. Último erro: {ultimo_erro}"
    )