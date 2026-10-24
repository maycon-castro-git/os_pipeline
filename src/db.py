import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO_ENV = RAIZ / ".env"

load_dotenv(ARQUIVO_ENV, override=True)


def conectar() -> psycopg.Connection:
    """Abre a conexão com o PostgreSQL usando as variáveis do .env."""
    host = os.getenv("DB_HOST")
    if not host:
        raise RuntimeError(
            f"DB_HOST não encontrado. Confira se existe o arquivo {ARQUIVO_ENV} "
            "com as variáveis DB_HOST, DB_PORT, DB_NAME, DB_USER e DB_PASSWORD."
        )
    return psycopg.connect(
        host=host,
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        sslmode="require",
        connect_timeout=10,
    )
