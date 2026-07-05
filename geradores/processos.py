# -*- coding: utf-8 -*-
"""Geradores de protocolo (processos 'P') e procedimento, a partir da espinha.

Um subconjunto dos processos é marcado como restrito (sta_nivel_acesso_global
<> 0 + id_hipotese_legal) para reproduzir os fatos de processos restritos / com
hipótese de restrição. O dimensionamento usa o alvo de 'processos_com_hipotese'
e a distribuição de hipóteses legais observada nesse fato.
"""
from datetime import timedelta

import contexto as C


def _prepara_restritos(ctx):
    """Calcula, uma vez, quais índices de processo são restritos e sua hipótese.

    Guarda em ctx._restr (dict idx->id_hipotese) e ctx._concl (set idx concluído).
    """
    if getattr(ctx, "_restr", None) is not None:
        return
    r = C.rng(ctx.seed, "processos", "restritos")
    n = ctx.n_proc_real
    alvo = ctx.perfil["fatos"]["processos_com_hipotese"]["alvo"]
    alvo = min(alvo, n)

    dist = ctx.perfil["fatos"]["processos_com_hipotese"]["categorias"].get(
        "id_hipotese_legal", {})
    amos = C.Amostrador(dist) if dist else None

    idxs = list(range(n))
    r.shuffle(idxs)
    restr = {}
    for k in idxs[:alvo]:
        h = amos.amostra(r) if amos else None
        if h is None and ctx.ids_hipotese:
            h = r.choice(ctx.ids_hipotese)
        restr[k] = C.to_int(h) if h is not None else None
    ctx._restr = restr

    # conclusão: ~60% dos processos concluídos (para limbo/desempenho)
    rc = C.rng(ctx.seed, "processos", "conclusao")
    ctx._concl = {k for k in range(n) if rc.random() < 0.60}


COLS_PROTOCOLO = ["id_protocolo", "id_unidade_geradora", "id_usuario_gerador",
                  "protocolo_formatado", "sta_protocolo", "id_protocolo_agrupador",
                  "dta_geracao", "sta_estado", "descricao", "sta_nivel_acesso_local",
                  "sta_nivel_acesso_global", "protocolo_formatado_pesquisa",
                  "codigo_barras", "id_hipotese_legal", "sta_grau_sigilo",
                  "sta_nivel_acesso_original", "protocolo_formatado_pesq_inv",
                  "dta_inclusao", "id_protocolo_federacao", "sin_eliminado"]


def gen_protocolo_processo(ctx):
    import fake
    _prepara_restritos(ctx)
    r = C.rng(ctx.seed, "protocolo_processo", "fmt")
    for k in range(ctx.n_proc_real):
        pid = ctx.proc_id[k]
        dt = ctx.proc_dt[k]
        pf = fake.protocolo_formatado(r, pid)
        hip = ctx._restr.get(k)
        nivel_global = "1" if hip is not None else "0"
        yield (pid, ctx.proc_unidade[k], ctx.proc_usuario[k], pf, "P", 0,
               dt, ctx.proc_estado[k], None, "0", nivel_global, pf, None,
               hip, None, None, pf[::-1][:50], dt, None, "N")


COLS_PROCEDIMENTO = ["id_procedimento", "id_tipo_procedimento", "sin_ciencia",
                     "id_plano_trabalho", "dta_conclusao", "dta_eliminacao",
                     "id_tipo_prioridade"]


def gen_procedimento(ctx):
    _prepara_restritos(ctx)
    r = C.rng(ctx.seed, "procedimento", "conclusao")
    for k in range(ctx.n_proc_real):
        dta_concl = None
        if k in ctx._concl:
            dta_concl = ctx.proc_dt[k] + timedelta(days=r.randint(1, 400))
        yield (ctx.proc_id[k], ctx.proc_tipo[k], "N", None, dta_concl, None, None)
