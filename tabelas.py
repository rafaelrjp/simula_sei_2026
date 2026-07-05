# -*- coding: utf-8 -*-
"""Registro das tabelas-alvo em ORDEM REFERENCIAL.

Cada item: (rotulo, nome_tabela, colunas, funcao_geradora).
A mesma tabela pode aparecer em mais de um item (ex.: protocolo recebe
processos e documentos por geradores distintos).
"""
from geradores import base, processos, documentos, atividades, modulos

# Tabelas de dados que o passo APAGAR deve truncar (ordem inversa na limpeza).
TABELAS_DADOS = [
    "tipo_procedimento", "serie", "hipotese_legal", "tarefa", "usuario",
    "unidade", "protocolo", "procedimento", "documento", "protocolo_modelo",
    "rel_protocolo_protocolo", "anexo", "atividade", "assinatura",
    "md_pet_int_tipo_intimacao", "md_pet_intimacao", "md_pet_int_protocolo",
    "md_pet_int_rel_dest", "md_pet_rel_recibo_protoc",
    "md_pet_rel_recibo_docanexo",
]

# Operacionais: a carga recusa se já houver linhas (salvo --force).
TABELAS_OPERACIONAIS = {
    "protocolo", "procedimento", "documento", "rel_protocolo_protocolo",
    "anexo", "atividade", "assinatura",
}

REGISTRO = [
    # (rotulo, tabela, colunas, gerador)
    ("catalogo:tipo_procedimento", "tipo_procedimento", base.COLS_TIPO_PROC, base.gen_tipo_procedimento),
    ("catalogo:serie", "serie", base.COLS_SERIE, base.gen_serie),
    ("catalogo:hipotese_legal", "hipotese_legal", base.COLS_HIPOTESE, base.gen_hipotese_legal),
    ("catalogo:tarefa", "tarefa", base.COLS_TAREFA, base.gen_tarefa),
    ("identidade:usuario", "usuario", base.COLS_USUARIO, base.gen_usuario),
    ("identidade:unidade", "unidade", base.COLS_UNIDADE, base.gen_unidade),

    ("protocolo:processos", "protocolo", processos.COLS_PROTOCOLO, processos.gen_protocolo_processo),
    ("protocolo:documentos", "protocolo", processos.COLS_PROTOCOLO, documentos.gen_protocolo_documento),
    ("procedimento", "procedimento", processos.COLS_PROCEDIMENTO, processos.gen_procedimento),
    ("documento", "documento", documentos.COLS_DOCUMENTO, documentos.gen_documento),
    ("protocolo_modelo", "protocolo_modelo", base.COLS_PROTOCOLO_MODELO, base.gen_protocolo_modelo),
    ("rel_protocolo_protocolo", "rel_protocolo_protocolo", documentos.COLS_REL, documentos.gen_rel_protocolo_protocolo),
    ("anexo", "anexo", documentos.COLS_ANEXO, documentos.gen_anexo),
    ("atividade", "atividade", atividades.COLS_ATIVIDADE, atividades.gen_atividade),
    ("assinatura", "assinatura", atividades.COLS_ASSINATURA, atividades.gen_assinatura),

    ("md:tipo_intimacao", "md_pet_int_tipo_intimacao", modulos.COLS_MD_TIPO_INT, modulos.gen_md_pet_int_tipo_intimacao),
    ("md:intimacao", "md_pet_intimacao", modulos.COLS_MD_INTIMACAO, modulos.gen_md_pet_intimacao),
    ("md:int_protocolo", "md_pet_int_protocolo", modulos.COLS_MD_INT_PROTOCOLO, modulos.gen_md_pet_int_protocolo),
    ("md:int_rel_dest", "md_pet_int_rel_dest", modulos.COLS_MD_INT_REL_DEST, modulos.gen_md_pet_int_rel_dest),
    ("md:recibo_protoc", "md_pet_rel_recibo_protoc", modulos.COLS_MD_RECIBO_PROTOC, modulos.gen_md_pet_rel_recibo_protoc),
    ("md:recibo_docanexo", "md_pet_rel_recibo_docanexo", modulos.COLS_MD_RECIBO_DOCANEXO, modulos.gen_md_pet_rel_recibo_docanexo),
]
