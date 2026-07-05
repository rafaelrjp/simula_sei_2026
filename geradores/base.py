# -*- coding: utf-8 -*-
"""Geradores das entidades base: usuário, unidade e catálogos.

Catálogos (serie, tipo_procedimento, hipotese_legal, tarefa) reutilizam os
rótulos institucionais das dimensões do DW — dado não-pessoal, cuja cópia é
permitida pelo escopo. Usuário e unidade são 100% sintéticos (nomes/siglas
inventados), preservando apenas os IDs e o sta_tipo do usuário.
"""
from datetime import datetime

import fake

_DT0 = datetime(2018, 1, 1, 0, 0, 0)


# ---------------------------------------------------------------- usuario
COLS_USUARIO = ["id_usuario", "sin_ativo", "sigla", "nome", "id_contato",
                "id_orgao", "idx_usuario", "sta_tipo", "senha", "id_origem",
                "nome_registro_civil", "nome_social", "id_usuario_federacao",
                "sin_gov_br", "dth_termo_uso", "dth_politica_privacidade"]


def gen_usuario(ctx):
    import contexto
    r = contexto.rng(ctx.seed, "usuario")
    for id_usuario, sta_tipo in ctx.usuarios:
        sigla = fake.sigla_usuario(r, id_usuario)
        nome = fake.nome_pessoa(r)
        yield (id_usuario, "S", sigla, nome, id_usuario, 0, None,
               str(sta_tipo), None, None, nome, None, None, "N", None, None)


# ---------------------------------------------------------------- unidade
COLS_UNIDADE = ["id_unidade", "sin_ativo", "sigla", "descricao",
                "sin_mail_pendencia", "id_orgao", "sin_envio_processo",
                "sin_arquivamento", "sin_ouvidoria", "sin_protocolo",
                "codigo_sei", "id_contato", "idx_unidade", "id_origem",
                "id_unidade_federacao"]


def gen_unidade(ctx):
    import contexto
    r = contexto.rng(ctx.seed, "unidade")
    for id_unidade in ctx.unidades:
        sigla = fake.sigla_unidade(r, id_unidade)
        yield (id_unidade, "S", sigla, fake.descricao_unidade(r), "N", 0,
               "S", "S", "N", "S", None, id_unidade, None, None, None)


# ---------------------------------------------------------------- serie
COLS_SERIE = ["nome", "descricao", "sin_ativo", "id_modelo_edoc",
              "id_grupo_serie", "id_serie", "sin_interessado",
              "sin_destinatario", "sta_numeracao", "sin_assinatura_publicacao",
              "id_modelo", "sta_aplicabilidade", "sin_interno",
              "id_tipo_formulario", "sin_usuario_externo", "sin_valor_monetario"]


def gen_serie(ctx):
    vistos = set()
    for id_serie, nome in ctx.series:
        nome = (nome or f"Serie {id_serie}")[:100]
        # ak1_serie = UNIQUE(nome, sin_ativo): garante nome único
        if nome in vistos:
            nome = f"{nome[:88]} ({id_serie})"
        vistos.add(nome)
        yield (nome, nome[:250], "S", None, None, id_serie, "N", "N",
               "S", "N", None, "1", "N", None, "N", "N")


# ------------------------------------------------------- tipo_procedimento
COLS_TIPO_PROC = ["id_tipo_procedimento", "nome", "descricao", "sin_ativo",
                  "sta_nivel_acesso_sugestao", "sin_interno", "sin_ouvidoria",
                  "sin_individual", "id_hipotese_legal_sugestao",
                  "sta_grau_sigilo_sugestao", "id_plano_trabalho",
                  "sin_ouvidoria_anonimo"]


def gen_tipo_procedimento(ctx):
    for id_tp, nome in ctx.tipos_proc:
        nome = (nome or f"Tipo {id_tp}")[:100]
        yield (id_tp, nome, nome[:250], "S", "0", "N", "N", "N",
               None, None, None, "N")


# --------------------------------------------------------- hipotese_legal
COLS_HIPOTESE = ["id_hipotese_legal", "nome", "base_legal", "descricao",
                 "sta_nivel_acesso", "sin_ativo"]


def gen_hipotese_legal(ctx):
    for id_h, nome in ctx.hipoteses:
        nome = (nome or f"Hipotese {id_h}")[:50]
        yield (id_h, nome, "Base legal simulada"[:50], nome, "1", "S")


# ---------------------------------------------------------------- tarefa
COLS_TAREFA = ["id_tarefa", "nome", "sin_historico_resumido",
               "sin_historico_completo", "sin_fechar_andamentos_abertos",
               "sin_lancar_andamento_fechado", "sin_permite_processo_fechado",
               "id_tarefa_modulo", "sin_consulta_processual"]


def gen_tarefa(ctx):
    for id_t in ctx.tarefas:
        yield (id_t, f"Tarefa {id_t}", "S", "S", "N", "N", "N", None, "N")


# ------------------------------------------------------- protocolo_modelo
COLS_PROTOCOLO_MODELO = ["id_protocolo_modelo", "id_grupo_protocolo_modelo",
                         "id_unidade", "id_usuario", "id_protocolo",
                         "descricao", "dth_alteracao", "idx_protocolo_modelo"]


def gen_protocolo_modelo(ctx):
    """Poucos modelos genéricos, ligados a processos aleatórios da espinha."""
    import contexto
    r = contexto.rng(ctx.seed, "protocolo_modelo")
    n = min(50, max(0, ctx.n_proc_real))
    for i in range(n):
        k = ctx.processo_aleatorio(r)
        yield (i + 1, None, ctx.proc_unidade[k], ctx.proc_usuario[k],
               ctx.proc_id[k], f"Modelo simulado {i+1}", _DT0, None)
