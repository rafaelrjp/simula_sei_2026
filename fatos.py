# -*- coding: utf-8 -*-
"""Metadados dos fatos do DW usados como fonte de volumes/distribuições.

Para cada fato relevante definimos:
  tabela      : nome da tabela no DW (sei_dw_bd_4_260626)
  ano/mes/dia : nomes das colunas com as partes de data (ano, mês, dia-da-semana)
                (None quando o fato não tem partes de data agregáveis)
  categorias  : colunas categóricas cuja distribuição queremos preservar

As colunas foram extraídas de information_schema (ver plano). Convenção do DW:
ano=YEAR, mes=MONTH, trimestre=QUARTER, dia_semana=WEEKDAY (0=segunda..6=domingo).
"""

# fatos-mestre: geram a espinha operacional
MESTRES = {
    "processos": dict(
        tabela="f_processos_unico__",
        ano="id_ano_inclusao_protocolo_fk",
        mes="id_mes_inclusao_protocolo_fk",
        dia="id_dia_semana_inclusao_protocolo_fk",
        categorias=["id_tipo_procedimento", "id_unidade_geradora",
                    "id_usuario_gerador", "sta_estado"],
    ),
    "documentos_gerados": dict(
        tabela="f_documentos_gerados_unico__",
        ano="ano_inclusao", mes="mes_inclusao", dia="dia_inclusao_semana",
        categorias=["id_unidade_geradora", "id_usuario_gerador", "id_serie"],
        tem_anexo="nome_anexo",   # coluna que indica presença de anexo
    ),
    "documentos_externos": dict(
        tabela="f_documentos_externos_unico__",
        ano="ano_inclusao", mes="mes_inclusao", dia="dia_inclusao_semana",
        categorias=["id_unidade_geradora", "id_usuario_gerador"],
        tem_anexo="nome_anexo_arquivo",
    ),
    "movimentacao": dict(
        tabela="f_movimentacao_de_processos_unico__",
        ano="ano_inclusao", mes="mes_inclusao", dia="dia_inclusao_semana",
        categorias=["movimentacao_tipo_processo_id",
                    "id_unidade_destino_movimentacao",
                    "id_unidade_origem_movimentacao"],
    ),
    "assinaturas": dict(
        tabela="f_assinaturas_unico__",
        ano="ano_id", mes="mes_id", dia="dia_inclusao_semana",
        categorias=["assinatura_tipo_documento_id", "assinatura_usuario_id",
                    "assinatura_unidade_id", "assinatura_tipo_processo_id"],
    ),
}

# fatos-derivados: reproduzidos por atribuição/seleção sobre a espinha
DERIVADOS = {
    "processos_restritos": dict(
        tabela="f_processos_restritos_unico__",
        ano="ano_inclusao_protocolo", mes="mes_inclusao_protocolo",
        dia="id_dia_da_semana",
        categorias=["id_tipo_procedimento", "id_unidade_geradora",
                    "id_hipotese_legal"],
    ),
    "processos_com_hipotese": dict(
        tabela="f_processos_com_hipotese_de_restricao_unico__",
        ano="ano_inclusao_protocolo", mes="mes_inclusao_protocolo",
        dia="id_dia_da_semana",
        categorias=["id_unidade_geradora", "id_hipotese_legal"],
    ),
    "documentos_cancelados": dict(
        tabela="f_documentos_cancelados_unico__",
        ano="ano_inclusao", mes="mes_inclusao", dia="dia_inclusao_semana",
        categorias=["id_unidade_geradora", "id_serie"],
    ),
    "documentos_restritos": dict(
        tabela="f_documentos_restritos_unico__",
        ano="ano_inclusao_protocolo", mes="mes_inclusao_protocolo",
        dia="id_dia_da_semana",
        categorias=["id_unidade_geradora", "id_hipotese_legal"],
    ),
    "situacao": dict(
        tabela="f_situacao_dos_processos_unico__",
        ano="ano_inclusao_protocolo", mes="mes_inclusao_protocolo",
        dia="id_dia_da_semana",
        categorias=["situacao_id", "id_unidade", "id_tipo_procedimento"],
    ),
    "limbo": dict(
        tabela="f_limbo_unico__",
        ano="id_ano_inclusao_protocolo_fk", mes="id_mes_inclusao_protocolo_fk",
        dia="id_dia_semana_inclusao_protocolo_fk",
        categorias=["id_tipo_procedimento", "id_unidade_geradora"],
    ),
    "desempenho": dict(
        tabela="f_desempenho_processos_unico__",
        ano="id_ano_inclusao_protocolo_fk", mes="id_mes_inclusao_protocolo_fk",
        dia="id_dia_semana_inclusao_protocolo_fk",
        categorias=["id_tipo_procedimento", "id_unidade_geradora"],
    ),
    "peticionamento": dict(
        tabela="f_peticionamento_eletronico_unico__",
        ano="ano_recebimento", mes="mes_recebimento", dia="id_dia_semana",
        categorias=["id_tipo_procedimento", "sta_tipo_peticionamento"],
    ),
    "intimacao": dict(
        tabela="f_intimacao_eletronica_unico__",
        ano="ano_intimacao", mes="mes_intimacao", dia="dia_semana_intimacao",
        categorias=["id_tipo_procedimento", "id_unidade"],
    ),
    # sem partes de data agregáveis (só dth_abertura texto): apenas total
    "sem_andamento_180": dict(
        tabela="f_180_sem_andamento_formal_unico__",
        ano=None, mes=None, dia=None,
        categorias=["id_tipo_procedimento", "id_unidade_andamento_ult90"],
    ),
}

TODOS = {**MESTRES, **DERIVADOS}

# Dimensões do DW -> universo de IDs de catálogo (para integridade referencial)
DIMENSOES = {
    "usuarios":   dict(tabela="d_usuarios_unico__",
                       cols=["id_usuario", "sta_tipo"]),
    "unidades":   dict(tabela="d_unidades_unico__", cols=None),  # só IDs
    "series":     dict(tabela="d_tipo_documento_unico_unico__",
                       col_id="id_serie"),
    "tipos_proc": dict(tabela="d_tipo_procedimento_unico__",
                       col_id="id_tipo_procedimento"),
    "hipoteses":  dict(tabela="d_hipotese_legal_unico__",
                       col_id="id_hipotese_legal"),
    "tarefas":    dict(tabela="d_tarefas_de_atividades_unico__",
                       col_id="id_tarefa"),
}

# tarefa de movimentação (remessa entre unidades) no SEI
TAREFA_MOVIMENTACAO = 32
