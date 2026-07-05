# -*- coding: utf-8 -*-
"""Geradores de atividade (movimentação + abertas) e assinatura.

Ordem de ids de atividade:
  [1 .. n_mov]                      -> movimentações (tarefa 32)
  [n_mov+1 .. n_mov+n_abertas]      -> atividades abertas (situação/limbo)
  [base_ass+1 .. base_ass+n_ass]    -> atividades-âncora das assinaturas
A tabela assinatura referencia essas últimas por id, recomputando a mesma base.
"""
from datetime import timedelta

import contexto as C
import fake

TAREFA_MOV = 32


def _n_abertas(ctx):
    return ctx.perfil["fatos"]["situacao"]["alvo"]


def _base_ass_ativ(ctx):
    return ctx.n_mov + _n_abertas(ctx)


COLS_ATIVIDADE = ["id_atividade", "id_protocolo", "id_unidade", "dth_abertura",
                  "dth_conclusao", "id_tarefa", "id_unidade_origem",
                  "id_usuario_conclusao", "sin_inicial", "id_usuario_visualizacao",
                  "id_usuario_atribuicao", "dta_prazo", "tipo_visualizacao",
                  "id_usuario", "id_usuario_origem"]


def gen_atividade(ctx):
    r = C.rng(ctx.seed, "atividade")
    cats = ctx.perfil["fatos"]["movimentacao"]["categorias"]
    a_dest = C.Amostrador(cats.get("id_unidade_destino_movimentacao", {})) \
        if cats.get("id_unidade_destino_movimentacao") else None
    a_orig = C.Amostrador(cats.get("id_unidade_origem_movimentacao", {})) \
        if cats.get("id_unidade_origem_movimentacao") else None

    # 1) movimentações (tarefa 32, unidade destino <> origem)
    for i in range(ctx.n_mov):
        k = ctx.link_processo(i * 5 + 1)
        proc_id = ctx.proc_id[k]
        dt = ctx.data_para("movimentacao", i)
        dest = a_dest.amostra_idx(i, 44) if a_dest else None
        orig = a_orig.amostra_idx(i, 55) if a_orig else None
        dest = int(dest) if dest is not None else ctx.proc_unidade[k]
        orig = int(orig) if orig is not None else ctx.ids_unidade[i % len(ctx.ids_unidade)]
        if dest == orig:
            orig = ctx.ids_unidade[(ctx.ids_unidade.index(orig) + 1) % len(ctx.ids_unidade)] \
                if orig in ctx.ids_unidade else ctx.ids_unidade[0]
        usu = ctx.proc_usuario[k]
        yield (i + 1, proc_id, dest, dt, dt + timedelta(hours=r.randint(1, 240)),
               TAREFA_MOV, orig, usu, "N", usu, None, None, 1, usu, usu)

    # 2) atividades abertas (dth_conclusao NULL) -> situação/limbo
    base_ab = ctx.n_mov
    n_ab = _n_abertas(ctx)
    if "situacao" in ctx.buckets:
        for j in range(n_ab):
            k = ctx.link_processo(j * 7 + 3)
            proc_id = ctx.proc_id[k]
            dt = ctx.data_para("situacao", j)
            uni = ctx.proc_unidade[k]
            yield (base_ab + j + 1, proc_id, uni, dt, None, 1, uni, None,
                   "N", None, None, None, 1, None, uni)

    # 3) atividades-âncora das assinaturas (sobre o documento assinado)
    base_ass = _base_ass_ativ(ctx)
    _, a_uni_ass = _amostradores_ass(ctx)   # construído UMA vez
    for j in range(ctx.n_ass):
        if ctx.n_docg == 0:
            break
        # documento DISTINTO por assinatura -> ak1_assinatura(id_documento,
        # id_usuario) único (n_ass <= n_docg garante j%n_docg sem repetição)
        doc_id = ctx.base_docg + (j % ctx.n_docg)
        dt = ctx.data_para("assinaturas", j)
        v = a_uni_ass.amostra_idx(j, 66) if a_uni_ass else None
        uni = int(v) if v is not None else ctx.ids_unidade[j % len(ctx.ids_unidade)]
        yield (base_ass + j + 1, doc_id, uni, dt, dt, 5, uni, None,
               "N", None, None, None, 1, None, uni)


# ------------------------------------------------------------- assinatura
def _amostradores_ass(ctx):
    cats = ctx.perfil["fatos"]["assinaturas"]["categorias"]
    return (
        C.Amostrador(cats.get("assinatura_usuario_id", {})) if cats.get("assinatura_usuario_id") else None,
        C.Amostrador(cats.get("assinatura_unidade_id", {})) if cats.get("assinatura_unidade_id") else None,
    )


COLS_ASSINATURA = ["id_assinatura", "id_documento", "id_usuario", "id_unidade",
                   "nome", "tratamento", "cpf", "id_atividade",
                   "sta_forma_autenticacao", "sin_ativo",
                   "numero_serie_certificado", "p7s_base64",
                   "id_tarja_assinatura", "agrupador", "modulo_origem"]


def gen_assinatura(ctx):
    r = C.rng(ctx.seed, "assinatura")
    a_usu, a_uni = _amostradores_ass(ctx)
    base_ass = _base_ass_ativ(ctx)
    for j in range(ctx.n_ass):
        if ctx.n_docg == 0:
            break
        doc_id = ctx.base_docg + (j % ctx.n_docg)   # casa com a âncora
        usu = a_usu.amostra_idx(j, 77) if a_usu else None
        usu = int(usu) if usu is not None else ctx.ids_usuario[j % len(ctx.ids_usuario)]
        uni = a_uni.amostra_idx(j, 66) if a_uni else None
        uni = int(uni) if uni is not None else ctx.ids_unidade[j % len(ctx.ids_unidade)]
        nome = fake.nome_pessoa(r)
        yield (j + 1, doc_id, usu, uni, nome, nome, None, base_ass + j + 1,
               "1", "S", None, None, 0, None, "SEI")
