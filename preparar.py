# -*- coding: utf-8 -*-
"""PREPARAR — cria/recria a estrutura de sei_simulado a partir do mysqldump.

O arquivo estrutura_apenas_sei_of.sql é um dump de estrutura (511 DROP + CREATE,
sem dados, sem triggers/views/procedures). Recriamos o schema do zero e
executamos as instruções via pymysql (comentários executáveis /*! */ inclusive).
"""
import re

import pymysql

import config
import db


def _statements(sql):
    """Divide o dump em instruções executáveis, ignorando comentários '--'."""
    linhas = []
    for l in sql.splitlines():
        s = l.strip()
        if not s or s.startswith("--"):
            continue
        linhas.append(l)
    texto = "\n".join(linhas)
    # divide por ';' no fim de linha (não há ';' dentro de defs de coluna)
    for bruto in re.split(r";\s*\n", texto):
        stmt = bruto.strip().rstrip(";").strip()
        if stmt:
            yield stmt


def executar():
    nome = config.valida_destino()
    if not config.ESTRUTURA_SQL:
        raise FileNotFoundError("estrutura_apenas_sei_of.sql não encontrado.")

    print(f"== PREPARAR == recriando schema '{nome}' a partir de")
    print(f"   {config.ESTRUTURA_SQL}")

    # 1) recria o database (garante slate limpo => contagem exata de tabelas)
    cfg = dict(config.CONN_DESTINO)
    cfg.pop("database", None)
    conn = pymysql.connect(**cfg)
    cur = conn.cursor()
    cur.execute(f"DROP DATABASE IF EXISTS `{nome}`")
    cur.execute(
        f"CREATE DATABASE `{nome}` "
        f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci"
    )
    conn.commit()
    cur.close()
    conn.close()

    # 2) executa a estrutura dentro do schema recém-criado
    sql = open(config.ESTRUTURA_SQL, encoding="utf-8", errors="replace").read()
    conn = db.conectar_destino()
    cur = conn.cursor()
    cur.execute("SET FOREIGN_KEY_CHECKS=0")
    n_ok = 0
    n_create = 0
    for stmt in _statements(sql):
        up = stmt.lstrip().upper()
        if up.startswith("SET @@SESSION.SQL_LOG_BIN"):
            continue  # pode exigir privilégio; irrelevante para estrutura
        try:
            cur.execute(stmt)
            n_ok += 1
            if up.startswith("CREATE TABLE"):
                n_create += 1
        except Exception as e:
            print(f"  AVISO em: {stmt[:70]!r} -> {e}")
    conn.commit()

    cur.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=%s",
        (nome,),
    )
    total = cur.fetchone()[0]
    cur.close()
    conn.close()
    print(f"Instruções executadas: {n_ok} | CREATE TABLE: {n_create} | "
          f"tabelas em {nome}: {total}")
    return total
