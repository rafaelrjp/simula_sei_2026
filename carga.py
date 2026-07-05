# -*- coding: utf-8 -*-
"""CARGA no banco de destino sei_simulado.

GERAR   = dry-run: percorre os geradores e conta as linhas, sem escrever.
CARREGAR = aplica: insere no banco em lotes, com FK/UNIQUE checks desligados.
Por segurança, recusa tabelas operacionais já preenchidas (salvo force).
"""
import time

import config
import db
import tabelas


def _estimativas(ctx):
    """Total esperado de linhas por rótulo do registro (para a barra/ETA)."""
    docs = ctx.n_docg + ctx.n_docr
    com_anexo = (ctx.perfil["fatos"]["documentos_gerados"].get("com_anexo", 0)
                 + ctx.perfil["fatos"]["documentos_externos"].get("com_anexo", 0))
    situacao = ctx.perfil["fatos"]["situacao"]["alvo"]
    n_int = ctx.perfil["fatos"]["intimacao"]["alvo"]
    n_pet = ctx.perfil["fatos"]["peticionamento"]["alvo"]
    return {
        "catalogo:tipo_procedimento": len(ctx.tipos_proc),
        "catalogo:serie": len(ctx.series),
        "catalogo:hipotese_legal": len(ctx.hipoteses),
        "catalogo:tarefa": len(ctx.tarefas),
        "identidade:usuario": len(ctx.usuarios),
        "identidade:unidade": len(ctx.unidades),
        "protocolo:processos": ctx.n_proc_real,
        "protocolo:documentos": docs,
        "procedimento": ctx.n_proc_real,
        "documento": docs,
        "protocolo_modelo": min(50, ctx.n_proc_real),
        "rel_protocolo_protocolo": docs,
        "anexo": com_anexo,
        "atividade": ctx.n_mov + situacao + ctx.n_ass,
        "assinatura": ctx.n_ass,
        "md:tipo_intimacao": 3,
        "md:intimacao": n_int,
        "md:int_protocolo": n_int,
        "md:int_rel_dest": n_int,
        "md:recibo_protoc": n_pet,
        "md:recibo_docanexo": n_pet,
    }


def _checar_vazias(cur, force):
    if force:
        return
    ocupadas = []
    for t in sorted(tabelas.TABELAS_OPERACIONAIS):
        if db.tabela_existe(cur, config.CONN_DESTINO["database"], t):
            if db.contar(cur, config.CONN_DESTINO["database"], t) > 0:
                ocupadas.append(t)
    if ocupadas:
        raise RuntimeError(
            "Tabelas operacionais NÃO vazias em sei_simulado: "
            + ", ".join(ocupadas)
            + ".\nUse APAGAR antes, ou passe --force para sobrescrever."
        )


def executar(ctx, aplicar, force=False):
    conn = db.conectar_destino()
    cur = conn.cursor()
    modo = "CARREGAR (aplica no banco)" if aplicar else "GERAR (dry-run, sem escrever)"
    print(f"== {modo} == destino={config.CONN_DESTINO['database']} seed={ctx.seed}")

    if aplicar:
        # confere se a estrutura existe
        if not db.tabela_existe(cur, config.CONN_DESTINO["database"], "protocolo"):
            raise RuntimeError(
                "sei_simulado não tem a tabela 'protocolo'. Rode PREPARAR primeiro."
            )
        _checar_vazias(cur, force)

    resumo = {}
    t0 = time.time()
    est = _estimativas(ctx)
    ctx_mgr = db.checks_desligados(cur) if aplicar else _nulo()
    with ctx_mgr:
        for rotulo, tabela, colunas, gen in tabelas.REGISTRO:
            ti = time.time()
            if aplicar:
                n = db.inserir_em_lote(conn, cur, tabela, colunas, gen(ctx),
                                       total=est.get(rotulo), rotulo=rotulo)
            else:
                n = sum(1 for _ in gen(ctx))
                print(f"  {rotulo:28s} -> {tabela:26s} {n:>10d}  ({time.time()-ti:5.1f}s)")
            resumo[rotulo] = n

    cur.close()
    conn.close()
    print(f"Total de linhas: {sum(resumo.values()):,} em {time.time()-t0:.1f}s")
    return resumo


class _nulo:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False
