# -*- coding: utf-8 -*-
"""Geradores dos módulos de Peticionamento e Intimação Eletrônica (md_pet_*).

Volumes pequenos. As cadeias de join do ETL são respeitadas:
- intimação: md_pet_int_protocolo.id_protocolo aponta para um DOCUMENTO ('G'),
  que já se relaciona a um processo via rel_protocolo_protocolo.
- peticionamento: md_pet_rel_recibo_protoc.id_protocolo aponta para um PROCESSO
  (o ETL faz procedimento.id_procedimento = rp.id_protocolo).
"""
import contexto as C
import fake

_TIPOS_RESP = ["E", "F", "S"]
_SIT_INT = ["1", "2", "3", "4", "5"]
N_TIPOS_INTIMACAO = 3


def _doc_g(ctx, j):
    return ctx.base_docg + (C.mix64(j * 4 + 1) % ctx.n_docg) if ctx.n_docg else 1


def _processo(ctx, j):
    k = ctx.link_processo(j * 11 + 5)
    return ctx.proc_id[k] if k is not None else 1


def _data(ctx, fato, j):
    from datetime import datetime
    if fato in ctx.buckets and ctx.buckets[fato][2] > 0:
        return ctx.data_para(fato, j)
    return datetime(2024, 1, 1, 12, 0, 0)


# -------------------------------------------------------- tipos de intimação
COLS_MD_TIPO_INT = ["id_md_pet_int_tipo_intimacao", "nome",
                    "tipo_resposta_aceita", "sin_ativo"]


def gen_md_pet_int_tipo_intimacao(ctx):
    for t in range(1, N_TIPOS_INTIMACAO + 1):
        yield (t, f"Tipo de intimacao {t}", _TIPOS_RESP[(t - 1) % 3], "S")


# ------------------------------------------------------------- intimação
COLS_MD_INTIMACAO = ["id_md_pet_intimacao", "id_md_pet_int_tipo_intimacao",
                     "sin_tipo_acesso_processo"]
COLS_MD_INT_PROTOCOLO = ["id_md_pet_int_protocolo", "sin_principal",
                         "id_md_pet_intimacao", "id_protocolo"]
COLS_MD_INT_REL_DEST = ["id_md_pet_int_rel_dest", "sin_ativo",
                        "sin_pessoa_juridica", "id_md_pet_intimacao",
                        "id_contato", "id_unidade", "data_cadastro",
                        "sta_situacao_intimacao", "dta_prazo_tacito"]


def _n_intim(ctx):
    return ctx.perfil["fatos"]["intimacao"]["alvo"]


def gen_md_pet_intimacao(ctx):
    for j in range(_n_intim(ctx)):
        tipo = 1 + (C.mix64(j) % N_TIPOS_INTIMACAO)
        yield (j + 1, tipo, "I" if j % 2 == 0 else "P")


def gen_md_pet_int_protocolo(ctx):
    for j in range(_n_intim(ctx)):
        yield (j + 1, "S", j + 1, _doc_g(ctx, j))


def gen_md_pet_int_rel_dest(ctx):
    cats = ctx.perfil["fatos"]["intimacao"]["categorias"]
    a_uni = C.Amostrador(cats.get("id_unidade", {})) if cats.get("id_unidade") else None
    for j in range(_n_intim(ctx)):
        uni = a_uni.amostra_idx(j, 88) if a_uni else None
        uni = int(uni) if uni is not None else ctx.ids_unidade[j % len(ctx.ids_unidade)]
        yield (j + 1, "S", "N", j + 1, 1000 + j, uni,
               _data(ctx, "intimacao", j), _SIT_INT[j % 5], None)


# ------------------------------------------------------------- peticionamento
COLS_MD_RECIBO_PROTOC = ["id_md_pet_rel_recibo_protoc", "id_protocolo",
                         "id_protocolo_relacionado", "id_usuario", "ip_usuario",
                         "data_hora_recebimento_final", "sin_ativo",
                         "sta_tipo_peticionamento", "id_documento",
                         "txt_doc_principal_intimacao"]
COLS_MD_RECIBO_DOCANEXO = ["id_md_pet_rel_recibo_docanexo",
                           "id_md_pet_rel_recibo_protoc", "formato_documento",
                           "id_documento", "id_anexo", "classificacao_documento"]


def _n_pet(ctx):
    return ctx.perfil["fatos"]["peticionamento"]["alvo"]


def gen_md_pet_rel_recibo_protoc(ctx):
    cats = ctx.perfil["fatos"]["peticionamento"]["categorias"]
    a_tipo = C.Amostrador(cats.get("sta_tipo_peticionamento", {})) \
        if cats.get("sta_tipo_peticionamento") else None
    for j in range(_n_pet(ctx)):
        usu = ctx.ids_usuario[C.mix64(j) % len(ctx.ids_usuario)]
        tipo = a_tipo.amostra_idx(j, 99) if a_tipo else None
        tipo = str(tipo)[:1] if tipo is not None else "U"
        yield (j + 1, _processo(ctx, j), None, usu, "0.0.0.0",
               _data(ctx, "peticionamento", j), "S", tipo, _doc_g(ctx, j), None)


def gen_md_pet_rel_recibo_docanexo(ctx):
    for j in range(_n_pet(ctx)):
        yield (j + 1, j + 1, "N", _doc_g(ctx, j), None, "P")
