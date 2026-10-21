import argparse
import logging
import os
import uuid

import psycopg
from dotenv import load_dotenv

from extract import extrair_os
from transform import preparar
from load import criar_run, finalizar_run, salvar_raw, carregar_clean

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/pipeline.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("main")


def executar(data_inicio: str, data_fim: str) -> None:
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL não configurado no .env")

    run_id = str(uuid.uuid4())
    logger.info("Iniciando execução %s", run_id)

    with psycopg.connect(dsn) as conn:
        criar_run(conn, run_id)

    try:
        registros = extrair_os(data_inicio, data_fim)
        df = preparar(registros, run_id)

        with psycopg.connect(dsn) as conn:
            salvar_raw(conn, run_id, registros)
            carregados = carregar_clean(conn, df)
            finalizar_run(conn, run_id, "SUCCESS", len(registros), carregados)

        logger.info("Concluído: %d extraído(s), %d carregado(s)", len(registros), carregados)

    except Exception as e:
        logger.exception("Execução falhou")
        with psycopg.connect(dsn) as conn:
            finalizar_run(conn, run_id, "FAILED", erro=str(e))
        raise


def main():
    parser = argparse.ArgumentParser(description="Pipeline de OS do SISOP")
    parser.add_argument("--inicio", required=True, help="Data inicial MM/DD/AAAA")
    parser.add_argument("--fim", required=True, help="Data final MM/DD/AAAA")
    args = parser.parse_args()
    executar(args.inicio, args.fim)


if __name__ == "__main__":
    main()
    