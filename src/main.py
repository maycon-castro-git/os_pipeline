import argparse
import logging
import os
import uuid

from db import conectar
from extract import extrair_os
from transform import preparar
from load import criar_run, finalizar_run, salvar_raw, carregar_clean
from quality import verificar, falhas_criticas, salvar_checks, QualityError

os.makedirs("logs", exist_ok=True)

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
    run_id = str(uuid.uuid4())
    logger.info("Iniciando execução %s", run_id)

    # Cria o registro da execução primeiro, para que ele exista mesmo se algo falhar depois
    with conectar() as conn:
        criar_run(conn, run_id)

    try:
        registros = extrair_os(data_inicio, data_fim)

        with conectar() as conn:
            salvar_raw(conn, run_id, registros)

        df = preparar(registros, run_id)

        resultados = verificar(df, extraidos=len(registros))
        with conectar() as conn:
            salvar_checks(conn, run_id, resultados)

        criticas = falhas_criticas(resultados)
        if criticas:
            nomes = ", ".join(r.nome for r in criticas)
            raise QualityError(f"Falha crítica de qualidade: {nomes}")

        with conectar() as conn:
            carregados = carregar_clean(conn, df)
            finalizar_run(conn, run_id, "SUCCESS", len(registros), carregados)

        logger.info("Concluído: %d extraído(s), %d carregado(s)", len(registros), carregados)

    except Exception as e:
        logger.exception("Execução falhou")
        with conectar() as conn:
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