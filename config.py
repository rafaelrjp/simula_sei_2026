# -*- coding: utf-8 -*-
"""Configuração central do simula_sei_2026.

Lê as credenciais a partir do arquivo acesso_bds.txt (formato PHP define()),
o mesmo usado pelo restante do projeto, para não duplicar segredos.
"""
import os
import re

# ----------------------------------------------------------------------------
# Caminhos
# ----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.dirname(BASE_DIR)  # E:\__dev_script_sei

# Arquivo de credenciais (PHP define()). Procura em locais conhecidos.
_ACESSO_CANDIDATOS = [
    os.path.join(WORKSPACE_DIR, "projeto-simula-sei", "acesso_bds.txt"),
    os.path.join(BASE_DIR, "acesso_bds.txt"),
    os.path.join(WORKSPACE_DIR, "acesso_bds.txt"),
]

# Estrutura do SEI (511 CREATE TABLE), usada pelo passo PREPARAR.
_ESTRUTURA_CANDIDATOS = [
    os.path.join(WORKSPACE_DIR, "projeto-simula-sei", "estrutura_apenas_sei_of.sql"),
    os.path.join(BASE_DIR, "estrutura_apenas_sei_of.sql"),
]

# Diretórios de saída
PERFIL_JSON = os.path.join(BASE_DIR, "perfil_agregado.json")
SAIDA_SQL_DIR = os.path.join(BASE_DIR, "saida_sql")

# ----------------------------------------------------------------------------
# Parâmetros default
# ----------------------------------------------------------------------------
SEED_PADRAO = 20260704          # semente determinística default
TAM_LOTE = 5000                 # linhas por executemany / INSERT multi-linha
DOMINIO_EMAIL = "example.invalid"

# Nome de schema de destino EXIGIDO (trava de segurança).
NOME_DESTINO_ACEITO = "sei_simulado"

# ----------------------------------------------------------------------------
# Parsing do acesso_bds.txt
# ----------------------------------------------------------------------------

def _primeiro_existente(candidatos):
    for c in candidatos:
        if os.path.isfile(c):
            return c
    return None


def _ler_defines(caminho):
    txt = open(caminho, encoding="utf-8", errors="replace").read()
    defs = {}
    for chave, valor in re.findall(r"define\(\s*'([^']+)'\s*,\s*'([^']*)'\s*\)", txt):
        defs[chave] = valor
    return defs


def _monta_conn(defs, sufixo):
    return {
        "host": defs[f"DB_HOST_{sufixo}"],
        "user": defs[f"DB_USER_{sufixo}"],
        "password": defs[f"DB_PASS_{sufixo}"],
        "database": defs[f"DB_NAME_{sufixo}"],
        "charset": "utf8mb4",
    }


_ACESSO = _primeiro_existente(_ACESSO_CANDIDATOS)
if not _ACESSO:
    raise FileNotFoundError(
        "acesso_bds.txt não encontrado. Locais tentados:\n  " +
        "\n  ".join(_ACESSO_CANDIDATOS)
    )

_DEFS = _ler_defines(_ACESSO)

# Conexões nomeadas
CONN_DW = _monta_conn(_DEFS, "BASE_DW")
CONN_ESTRUTURA = _monta_conn(_DEFS, "BD_SEI_ESTRUTURA")
CONN_DESTINO = _monta_conn(_DEFS, "BD_SEI_DESTINO")

ESTRUTURA_SQL = _primeiro_existente(_ESTRUTURA_CANDIDATOS)


def valida_destino():
    """Trava de segurança: o destino tem de ser literalmente sei_simulado."""
    nome = CONN_DESTINO.get("database", "")
    if nome != NOME_DESTINO_ACEITO:
        raise RuntimeError(
            f"Destino recusado: '{nome}'. Só é aceito o schema "
            f"'{NOME_DESTINO_ACEITO}' (ver acesso_bds.txt / DB_NAME_BD_SEI_DESTINO)."
        )
    return nome


if __name__ == "__main__":
    print("acesso_bds.txt :", _ACESSO)
    print("estrutura.sql  :", ESTRUTURA_SQL)
    print("DW      ->", {k: v for k, v in CONN_DW.items() if k != "password"})
    print("ESTRUT  ->", {k: v for k, v in CONN_ESTRUTURA.items() if k != "password"})
    print("DESTINO ->", {k: v for k, v in CONN_DESTINO.items() if k != "password"})
    valida_destino()
    print("Destino validado OK:", NOME_DESTINO_ACEITO)
