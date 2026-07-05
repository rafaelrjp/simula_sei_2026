# -*- coding: utf-8 -*-
"""Geradores de documentos: protocolo ('G'/'R') + documento + rel + anexo.

Cada documento é gerado por streaming (funções O(1) por índice, sem materializar
milhões de linhas). Passagens diferentes (protocolo/documento/rel/anexo) sobre o
mesmo documento concordam nas referências porque tudo deriva do índice i.
"""
import contexto as C
import fake


def _grupos(ctx):
    """Config dos dois grupos de documentos."""
    return [
        dict(nome="documentos_gerados", sta="G",
             base=ctx.base_docg, n=ctx.n_docg,
             rel_base=1, anexo_base=1),
        dict(nome="documentos_externos", sta="R",
             base=ctx.base_docr, n=ctx.n_docr,
             rel_base=ctx.n_docg + 1,
             anexo_base=ctx.perfil["fatos"]["documentos_gerados"].get("com_anexo", 0) + 1),
    ]


def _amostradores(ctx, g):
    cats = ctx.perfil["fatos"][g["nome"]]["categorias"]
    a_uni = C.Amostrador(cats.get("id_unidade_geradora", {})) if cats.get("id_unidade_geradora") else None
    a_usu = C.Amostrador(cats.get("id_usuario_gerador", {})) if cats.get("id_usuario_gerador") else None
    a_ser = C.Amostrador(cats.get("id_serie", {})) if cats.get("id_serie") else None
    return a_uni, a_usu, a_ser


def _unidade(ctx, a_uni, i):
    v = a_uni.amostra_idx(i, 11) if a_uni else None
    return int(v) if v is not None else ctx.ids_unidade[i % len(ctx.ids_unidade)]


def _usuario(ctx, a_usu, i):
    v = a_usu.amostra_idx(i, 22) if a_usu else None
    return int(v) if v is not None else ctx.ids_usuario[i % len(ctx.ids_usuario)]


def _serie(ctx, a_ser, i):
    v = a_ser.amostra_idx(i, 33) if a_ser else None
    return int(v) if v is not None else ctx.ids_serie[C.mix64(i) % len(ctx.ids_serie)]


def _hit(i, k, n):
    """True em exatamente k dos n índices (0..n-1), espalhados uniformemente."""
    if k <= 0 or n <= 0:
        return False
    return ((i + 1) * k) // n - (i * k) // n == 1


def _eh_cancelado(ctx, i):
    alvo = ctx.perfil["fatos"]["documentos_cancelados"]["alvo"]
    return _hit(i, alvo, ctx.n_docg)


def _restr_doc(ctx, i, n):
    """(nivel_global, id_hipotese) — documento restrito reproduz f_documentos_restritos."""
    alvo = ctx.perfil["fatos"]["documentos_restritos"]["alvo"]
    if _hit(i, alvo, n) and ctx.ids_hipotese:
        h = ctx.ids_hipotese[C.mix64(i) % len(ctx.ids_hipotese)]
        return "1", int(h)
    return "0", None


def _tem_anexo(ctx, g, i):
    com = ctx.perfil["fatos"][g["nome"]].get("com_anexo", 0)
    return _hit(i, com, g["n"])


# ------------------------------------------------------------- protocolo
def gen_protocolo_documento(ctx):
    r = C.rng(ctx.seed, "protocolo_doc", "fmt")
    for g in _grupos(ctx):
        a_uni, a_usu, _ = _amostradores(ctx, g)
        for i in range(g["n"]):
            did = g["base"] + i
            dt = ctx.data_para(g["nome"], i)
            uni = _unidade(ctx, a_uni, i)
            usu = _usuario(ctx, a_usu, i)
            pf = fake.protocolo_formatado(r, did)
            estado = "2" if (g["sta"] == "G" and _eh_cancelado(ctx, i)) else "0"
            nivel, hip = _restr_doc(ctx, i, g["n"])
            yield (did, uni, usu, pf, g["sta"], 0, dt, estado, None, "0",
                   nivel, pf, None, hip, None, None, pf[::-1][:50], dt, None, "N")


# ------------------------------------------------------------- documento
def gen_documento(ctx):
    for g in _grupos(ctx):
        a_uni, a_usu, a_ser = _amostradores(ctx, g)
        for i in range(g["n"]):
            did = g["base"] + i
            k = ctx.link_processo(g["base"] + i)
            id_proc = ctx.proc_id[k] if k is not None else did
            uni = _unidade(ctx, a_uni, i)
            ser = _serie(ctx, a_ser, i)
            yield (did, None, uni, None, ser, id_proc, "N", None, None, None,
                   "T", None, "N", "N", None, "H")


# --------------------------------------------------- rel_protocolo_protocolo
def gen_rel_protocolo_protocolo(ctx):
    for g in _grupos(ctx):
        a_uni, a_usu, _ = _amostradores(ctx, g)
        for i in range(g["n"]):
            did = g["base"] + i
            k = ctx.link_processo(g["base"] + i)
            if k is None:
                continue
            proc_id = ctx.proc_id[k]
            dt = ctx.data_para(g["nome"], i)
            uni = _unidade(ctx, a_uni, i)
            usu = _usuario(ctx, a_usu, i)
            yield (proc_id, did, usu, uni, "1", dt, 1, "N", g["rel_base"] + i)


# ------------------------------------------------------------- anexo
def gen_anexo(ctx):
    r = C.rng(ctx.seed, "anexo")
    aid = 1  # contador global único (evita colisão de PK entre grupos)
    for g in _grupos(ctx):
        a_uni, a_usu, _ = _amostradores(ctx, g)
        for i in range(g["n"]):
            if not _tem_anexo(ctx, g, i):
                continue
            did = g["base"] + i
            dt = ctx.data_para(g["nome"], i)
            uni = _unidade(ctx, a_uni, i)
            usu = _usuario(ctx, a_usu, i)
            yield (aid, fake.nome_anexo(r, aid), did, "S", uni, usu,
                   r.randint(1024, 5 * 1048576), dt, None, None,
                   fake.hash_falso(aid))
            aid += 1


COLS_PROTOCOLO_DOC = None  # usa COLS_PROTOCOLO de processos
COLS_DOCUMENTO = ["id_documento", "numero", "id_unidade_responsavel",
                  "id_documento_edoc", "id_serie", "id_procedimento",
                  "sin_bloqueado", "id_conjunto_estilos", "id_tipo_conferencia",
                  "id_tipo_formulario", "sta_documento", "nome_arvore",
                  "sin_arquivamento", "sin_versoes", "din_valor", "sta_editor"]
COLS_REL = ["id_protocolo_1", "id_protocolo_2", "id_usuario", "id_unidade",
            "sta_associacao", "dth_associacao", "sequencia", "sin_ciencia",
            "id_rel_protocolo_protocolo"]
COLS_ANEXO = ["id_anexo", "nome", "id_protocolo", "sin_ativo", "id_unidade",
              "id_usuario", "tamanho", "dth_inclusao", "id_base_conhecimento",
              "id_projeto", "hash"]
