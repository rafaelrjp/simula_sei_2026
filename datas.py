# -*- coding: utf-8 -*-
"""Geração de datas concretas a partir das partes agregadas do DW.

O DW não guarda data real, apenas (ano, mês, dia-da-semana). Aqui, dado um
bucket (ano, mes, dia_semana) e uma quantidade, produzimos datas concretas cujo
YEAR/MONTH/WEEKDAY batem exatamente com o bucket. QUARTER decorre do mês.

Convenção MySQL WEEKDAY: 0=segunda-feira ... 6=domingo (== datetime.weekday()).
"""
import calendar
from datetime import datetime


def _dias_do_mes_no_weekday(ano, mes, dia_semana):
    """Lista de days-of-month (1..N) cujo weekday == dia_semana."""
    ndias = calendar.monthrange(ano, mes)[1]
    return [d for d in range(1, ndias + 1)
            if datetime(ano, mes, d).weekday() == dia_semana]


def datas_para_bucket(ano, mes, dia_semana, qtd, rng):
    """Gera `qtd` datetimes dentro de (ano, mes) caindo no `dia_semana`.

    Distribui as ocorrências entre os dias válidos de forma equilibrada
    (round-robin) e sorteia hora/minuto/segundo com o rng determinístico.
    Se o mês não tiver aquele dia-da-semana (impossível: todo mês tem 4-5),
    cai no primeiro dia do mês como salvaguarda.
    """
    if qtd <= 0:
        return
    dias = _dias_do_mes_no_weekday(ano, mes, dia_semana)
    if not dias:
        dias = [1]
    n = len(dias)
    for i in range(qtd):
        dia = dias[i % n]
        yield datetime(
            ano, mes, dia,
            rng.randint(8, 18),      # horário comercial plausível
            rng.randint(0, 59),
            rng.randint(0, 59),
        )


def uma_data(ano, mes, dia_semana, rng):
    """Retorna um único datetime coerente com o bucket."""
    dias = _dias_do_mes_no_weekday(ano, mes, dia_semana) or [1]
    dia = rng.choice(dias)
    return datetime(ano, mes, dia,
                    rng.randint(8, 18), rng.randint(0, 59), rng.randint(0, 59))


if __name__ == "__main__":
    import random
    rng = random.Random(1)
    amostra = list(datas_para_bucket(2024, 2, 2, 10, rng))  # quarta-feira fev/24
    for d in amostra:
        assert d.year == 2024 and d.month == 2 and d.weekday() == 2, d
    print("datas.py OK — exemplo (quartas de fev/2024):")
    for d in amostra[:5]:
        print("  ", d.strftime("%Y-%m-%d %H:%M:%S"), "weekday=", d.weekday())
