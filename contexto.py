# -*- coding: utf-8 -*-
"""Contexto/Plano de geração — estado compartilhado e determinístico.

Constrói uma "espinha" de processos em memória (leve: só ids e atributos) e
define as faixas de ids das demais entidades. Todas as escolhas derivam de RNGs
semeados por (seed, tabela, proposito), de modo que passagens diferentes sobre a
mesma tabela — ou tabelas que precisam concordar em uma referência cruzada —
reproduzem exatamente os mesmos valores sem precisar materializar tudo.
"""
import bisect
import hashlib
import random

import perfil as perfil_mod


def rng(seed, *partes):
    """random.Random semeado de forma estável por (seed, *partes)."""
    chave = "|".join([str(seed)] + [str(p) for p in partes])
    h = hashlib.sha256(chave.encode("utf-8")).digest()
    return random.Random(int.from_bytes(h[:8], "big"))


def _buckets_ordenados(datas):
    """De {'ano-mes-dia': qtd} para (lista_chaves, prefixos_acumulados, total).

    Permite mapear um índice global i -> (ano,mes,dia, offset dentro do bucket).
    """
    itens = sorted(datas.items())
    chaves, acum, s = [], [], 0
    for k, q in itens:
        chaves.append(k)
        acum.append(s)
        s += q
    return chaves, acum, s


_MASK64 = (1 << 64) - 1


def to_int(x):
    """Converte valores de categoria para int, tolerando '14.0', 14.0, '14'."""
    if x is None:
        return None
    if isinstance(x, int):
        return x
    return int(float(x))


def mix64(n):
    """splitmix64 — hash inteiro rápido e determinístico (sem objeto Random)."""
    n = (n + 0x9E3779B97F4A7C15) & _MASK64
    z = n
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _MASK64
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _MASK64
    return z ^ (z >> 31)


class Amostrador:
    """Amostragem ponderada determinística a partir de marginais {valor: peso}."""

    def __init__(self, dist):
        self.valores = list(dist.keys())
        pesos = list(dist.values())
        self.acum = []
        s = 0
        for w in pesos:
            s += w
            self.acum.append(s)
        self.total = s

    def amostra(self, r):
        if self.total <= 0:
            return None
        x = r.randint(1, self.total)
        i = bisect.bisect_left(self.acum, x)
        return self.valores[i]

    def amostra_idx(self, i, salt=0):
        """Amostra determinística indexada por i (sem Random), p/ streaming."""
        if self.total <= 0:
            return None
        x = mix64(i ^ (salt * 0x100000001B3)) % self.total
        j = bisect.bisect_right(self.acum, x)
        return self.valores[j]


class Contexto:
    def __init__(self, perfil, seed):
        self.perfil = perfil
        self.seed = seed
        self.dims = perfil["dimensoes"]

        # universo de catálogos
        self.usuarios = perfil["dimensoes"]["usuarios"]      # [[id, sta_tipo],...]
        self.unidades = perfil["dimensoes"]["unidades"]      # [id, ...]
        self.series = perfil["dimensoes"]["series"]          # [[id, nome], ...]
        self.tipos_proc = perfil["dimensoes"]["tipos_proc"]  # [[id, nome], ...]
        self.hipoteses = perfil["dimensoes"]["hipoteses"]    # [[id, nome], ...]
        self.tarefas = perfil["dimensoes"]["tarefas"]        # [id, ...]

        self.ids_unidade = [u for u in self.unidades]
        self.ids_usuario = [u[0] for u in self.usuarios]
        self.ids_serie = [s[0] for s in self.series]
        self.ids_tipo_proc = [t[0] for t in self.tipos_proc]
        self.ids_hipotese = [h[0] for h in self.hipoteses]

        # ---- volumes-alvo ----
        f = perfil["fatos"]
        self.n_proc = f["processos"]["alvo"]
        self.n_docg = f["documentos_gerados"]["alvo"]
        self.n_docr = f["documentos_externos"]["alvo"]
        self.n_mov = f["movimentacao"]["alvo"]
        self.n_ass = f["assinaturas"]["alvo"]

        # ---- faixas de id de protocolo (superclasse de proc/doc) ----
        self.base_proc = 1
        self.base_docg = self.base_proc + self.n_proc
        self.base_docr = self.base_docg + self.n_docg
        self.fim_protocolo = self.base_docr + self.n_docr

        # ---- buckets de data por fato ----
        self.buckets = {}
        for nome, meta in f.items():
            if meta.get("datas"):
                self.buckets[nome] = _buckets_ordenados(meta["datas"])

        # ---- espinha de processos em memória ----
        self._montar_espinha()

    # ------------------------------------------------------------------
    def _bucket_por_indice(self, nome_fato, i):
        """(ano, mes, dia, offset) do i-ésimo registro do fato."""
        chaves, acum, total = self.buckets[nome_fato]
        pos = bisect.bisect_right(acum, i) - 1
        ano, mes, dia = map(int, chaves[pos].split("-"))
        offset = i - acum[pos]
        return ano, mes, dia, offset

    def total_fato(self, nome_fato):
        if nome_fato in self.buckets:
            return self.buckets[nome_fato][2]
        return self.perfil["fatos"][nome_fato]["alvo"]

    # ------------------------------------------------------------------
    def _montar_espinha(self):
        """Cria arrays paralelos dos processos (id, data, categorias)."""
        import datas as datas_mod
        meta = self.perfil["fatos"]["processos"]
        r_at = rng(self.seed, "processos", "attr")
        r_dt = rng(self.seed, "processos", "data")

        amos = {c: Amostrador(meta["categorias"][c])
                for c in meta["categorias"]}

        self.proc_id = []
        self.proc_dt = []
        self.proc_tipo = []
        self.proc_unidade = []
        self.proc_usuario = []
        self.proc_estado = []

        pid = self.base_proc
        if "processos" in self.buckets:
            chaves, acum, total = self.buckets["processos"]
            for k, ini in zip(chaves, acum):
                ano, mes, dia = map(int, k.split("-"))
                q = self.perfil["fatos"]["processos"]["datas"][k]
                for dt in datas_mod.datas_para_bucket(ano, mes, dia, q, r_dt):
                    self.proc_id.append(pid)
                    self.proc_dt.append(dt)
                    self.proc_tipo.append(int(amos["id_tipo_procedimento"].amostra(r_at)))
                    self.proc_unidade.append(int(amos["id_unidade_geradora"].amostra(r_at)))
                    self.proc_usuario.append(int(amos["id_usuario_gerador"].amostra(r_at)))
                    self.proc_estado.append(str(amos["sta_estado"].amostra(r_at)))
                    pid += 1
        self.n_proc_real = len(self.proc_id)

    # ------------------------------------------------------------------
    def processo_aleatorio(self, r):
        """Índice de um processo da espinha (para vincular documentos etc.)."""
        if self.n_proc_real == 0:
            return None
        return r.randrange(self.n_proc_real)

    # --------- helpers determinísticos O(1) por índice (streaming) --------
    def _dias_validos(self, ano, mes, dia_semana):
        chave = (ano, mes, dia_semana)
        cache = getattr(self, "_cache_dias", None)
        if cache is None:
            cache = self._cache_dias = {}
        if chave not in cache:
            import datas as datas_mod
            cache[chave] = datas_mod._dias_do_mes_no_weekday(ano, mes, dia_semana) or [1]
        return cache[chave]

    def data_para(self, nome_fato, i):
        """datetime determinística do i-ésimo registro do fato (sem Random)."""
        from datetime import datetime
        ano, mes, dia, offset = self._bucket_por_indice(nome_fato, i)
        dias = self._dias_validos(ano, mes, dia)
        d = dias[offset % len(dias)]
        h = 8 + (mix64(i) % 11)
        mi = mix64(i + 1) % 60
        se = mix64(i + 2) % 60
        return datetime(ano, mes, d, h, mi, se)

    def link_processo(self, i):
        """Índice de processo vinculado ao i-ésimo documento (determinístico)."""
        if self.n_proc_real == 0:
            return None
        return mix64(i * 3 + 7) % self.n_proc_real


def carregar_contexto(seed):
    perfil = perfil_mod.carregar_perfil()
    seed = seed if seed is not None else perfil["parametros"]["seed"]
    return Contexto(perfil, seed)
