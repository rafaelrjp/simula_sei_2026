# -*- coding: utf-8 -*-
"""DUMPAR — gera arquivos .sql por tabela, em ordem referencial.

Saída em saida_sql/NN_<tabela>.sql com INSERT multi-linha em lotes. Prefixados
com USE sei_simulado; SET FOREIGN_KEY_CHECKS=0; para aplicação manual:
    mysql -u root -p sei_simulado < saida_sql\\07_protocolo.sql
ou concatenando todos na ordem numérica.
"""
import os
from datetime import datetime, date
from decimal import Decimal

import config
import tabelas


def _val(v):
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, (int, float, Decimal)):
        return str(v)
    if isinstance(v, (datetime, date)):
        return "'" + v.strftime("%Y-%m-%d %H:%M:%S") + "'"
    s = str(v).replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "")
    return "'" + s + "'"


def _escrever_tabela(f, tabela, colunas, geradores_ctx, tam_lote):
    cols_sql = ", ".join(f"`{c}`" for c in colunas)
    prefixo = f"INSERT INTO `{tabela}` ({cols_sql}) VALUES\n"
    total = 0
    buf = []

    def flush():
        nonlocal buf, total
        if not buf:
            return
        f.write(prefixo)
        f.write(",\n".join(buf))
        f.write(";\n")
        total += len(buf)
        buf = []

    for gen, ctx in geradores_ctx:
        for linha in gen(ctx):
            buf.append("(" + ", ".join(_val(v) for v in linha) + ")")
            if len(buf) >= tam_lote:
                flush()
    flush()
    return total


def executar(ctx):
    os.makedirs(config.SAIDA_SQL_DIR, exist_ok=True)
    # limpa dumps antigos
    for nome in os.listdir(config.SAIDA_SQL_DIR):
        if nome.endswith(".sql"):
            os.remove(os.path.join(config.SAIDA_SQL_DIR, nome))

    # agrupa itens do registro por tabela, preservando ordem de 1ª aparição
    ordem = []
    grupos = {}
    colunas_de = {}
    for rotulo, tabela, colunas, gen in tabelas.REGISTRO:
        if tabela not in grupos:
            grupos[tabela] = []
            ordem.append(tabela)
            colunas_de[tabela] = colunas
        grupos[tabela].append((gen, ctx))

    print(f"== DUMPAR == saida={config.SAIDA_SQL_DIR} seed={ctx.seed}")
    resumo = {}
    for idx, tabela in enumerate(ordem, start=1):
        caminho = os.path.join(config.SAIDA_SQL_DIR, f"{idx:02d}_{tabela}.sql")
        with open(caminho, "w", encoding="utf-8", newline="\n") as f:
            f.write(f"-- simula_sei_2026 dump de {tabela}\n")
            f.write(f"USE `{config.CONN_DESTINO['database']}`;\n")
            f.write("SET FOREIGN_KEY_CHECKS=0;\n\n")
            n = _escrever_tabela(f, tabela, colunas_de[tabela],
                                 grupos[tabela], config.TAM_LOTE)
            f.write("\nSET FOREIGN_KEY_CHECKS=1;\n")
        resumo[tabela] = n
        print(f"  {idx:02d}_{tabela:26s} {n:>10d} linhas")
    print(f"Total: {sum(resumo.values()):,} linhas em {len(ordem)} arquivos")
    return resumo
