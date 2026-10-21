from quality import verificar, falhas_criticas, salvar_checks, QualityError


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

        # O raw é gravado antes das checagens: se algo falhar, dá para reprocessar.
        with psycopg.connect(dsn) as conn:
            salvar_raw(conn, run_id, registros)

        df = preparar(registros, run_id)

        resultados = verificar(df, extraidos=len(registros))
        with psycopg.connect(dsn) as conn:
            salvar_checks(conn, run_id, resultados)

        criticas = falhas_criticas(resultados)
        if criticas:
            nomes = ", ".join(r.nome for r in criticas)
            raise QualityError(f"Falha crítica de qualidade: {nomes}")

        with psycopg.connect(dsn) as conn:
            carregados = carregar_clean(conn, df)
            finalizar_run(conn, run_id, "SUCCESS", len(registros), carregados)

        logger.info("Concluído: %d extraído(s), %d carregado(s)", len(registros), carregados)

    except Exception as e:
        logger.exception("Execução falhou")
        with psycopg.connect(dsn) as conn:
            finalizar_run(conn, run_id, "FAILED", erro=str(e))
        raise