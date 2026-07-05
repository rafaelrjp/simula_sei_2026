# -*- coding: utf-8 -*-
"""Geração de textos 100% sintéticos e determinísticos.

Regras (do escopo do projeto):
- Nada de dado real: nomes, siglas, nomes de arquivo são inventados.
- Sem CPF/CNPJ válidos, sem senha, sem conteúdo de documento/anexo.
- E-mails sempre no domínio reservado example.invalid.
- Tudo reprodutível pelo rng (semente).
"""
import hashlib

import config

_PRENOMES = [
    "Ana", "Bruno", "Carla", "Diego", "Elisa", "Fabio", "Gabi", "Heitor",
    "Ingrid", "Joao", "Katia", "Lucas", "Maria", "Nina", "Otavio", "Paula",
    "Rafael", "Sofia", "Tiago", "Ursula", "Vitor", "Wagner", "Ximena", "Yara",
    "Zeca", "Bianca", "Caio", "Denise", "Eduardo", "Flavia",
]
_SOBRENOMES = [
    "Alves", "Barbosa", "Cardoso", "Dias", "Esteves", "Ferreira", "Gomes",
    "Henriques", "Ibrahim", "Junqueira", "Klein", "Lima", "Moraes", "Nunes",
    "Oliveira", "Pereira", "Queiroz", "Rocha", "Santos", "Teixeira", "Uchoa",
    "Vasconcelos", "Werneck", "Xavier", "Yamamoto", "Zambrano",
]
# Rótulos genéricos de unidade (nada institucional real)
_UNID_TIPOS = [
    "Coordenacao", "Divisao", "Secao", "Nucleo", "Gerencia", "Setor",
    "Assessoria", "Delegacia", "Grupo", "Escritorio",
]
_UNID_TEMAS = [
    "Administrativa", "Tecnica", "Operacional", "Regional", "Especial",
    "Financeira", "Juridica", "Logistica", "Planejamento", "Documental",
]


def _r(rng, seq):
    return seq[rng.randrange(len(seq))]


def nome_pessoa(rng):
    return f"{_r(rng, _PRENOMES)} {_r(rng, _SOBRENOMES)}"


def sigla_usuario(rng, id_usuario):
    """Sigla fictícia estável derivada do id (não vaza login real)."""
    p = _r(rng, _PRENOMES).lower()
    s = _r(rng, _SOBRENOMES).lower()
    return f"{p}.{s}{id_usuario % 1000:03d}"


def email(rng, sigla):
    return f"{sigla}@{config.DOMINIO_EMAIL}"


def sigla_unidade(rng, id_unidade):
    letras = "".join(_r(rng, _UNID_TEMAS)[0] for _ in range(3)).upper()
    return f"{letras}{id_unidade % 1000:03d}"


def descricao_unidade(rng):
    return f"{_r(rng, _UNID_TIPOS)} {_r(rng, _UNID_TEMAS)}"


def protocolo_formatado(rng, seq):
    """Número de processo/documento fictício no formato NNNNN.NNNNNNNN/AAAA-DD.

    O miolo usa o `seq` completo (id do protocolo, único) para garantir
    unicidade — a coluna protocolo_formatado tem UNIQUE KEY. Imita o formato
    SEI, mas não corresponde a nenhum protocolo real.
    """
    orgao = 10000 + (seq % 90000)
    ano = 2018 + (seq % 9)
    dv = seq % 100
    return f"{orgao:05d}.{seq:08d}/{ano}-{dv:02d}"


def nome_anexo(rng, seq, extensao=None):
    """Nome de arquivo fictício — nunca cita usuário/pessoa."""
    prefixos = ["documento", "anexo", "arquivo", "peca", "comprovante",
                "formulario", "relatorio", "oficio", "despacho", "planilha"]
    ext = extensao or _r(rng, ["pdf", "pdf", "pdf", "docx", "png", "jpg", "txt"])
    return f"{_r(rng, prefixos)}_{seq:08d}.{ext}"


def hash_falso(seq):
    """Hash md5 determinístico e sem significado (para colunas hash)."""
    return hashlib.md5(f"simulado-{seq}".encode()).hexdigest()
