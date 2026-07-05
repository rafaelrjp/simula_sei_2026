# -*- coding: utf-8 -*-
"""PERFIL — extrai do DW o perfil agregado (volumes + distribuições).

Salva perfil_agregado.json com, por fato:
  - total_dw          : contagem bruta no DW (na janela de anos)
  - alvo              : total após aplicar a massa (inteiro)
  - datas             : { "ano-mes-diasemana": qtd }  (já escalado, soma == alvo)
  - categorias        : { coluna: { valor: qtd_bruta_dw } }  (pesos p/ amostragem)
E as dimensões (universo de IDs de catálogo) para integridade referencial.

Datas: ano=YEAR, mes=MONTH, dia=WEEKDAY (0=segunda..6=domingo). Escala por massa
usa arredondamento por maior-resto para preservar o total.
"""
import json

import config
import db
import fatos


# ---------------------------------------------------------------------------
# util
# ---------------------------------------------------------------------------

def _maior_resto(pares, alvo):
    """Distribui `alvo` inteiros proporcionalmente aos pesos de `pares`
    [(chave, peso), ...] usando o método do maior resto. Retorna dict."""
    soma = sum(p for _, p in pares)
    if soma <= 0 or alvo <= 0:
        return {k: 0 for k, _ in pares}
    exatos = [(k, alvo * p / soma) for k, p in pares]
    base = {k: int(v) for k, v in exatos}
    resto = alvo - sum(base.values())
    # ordena por parte fracionária desc e distribui o que faltou
    fracs = sorted(exatos, key=lambda kv: kv[1] - int(kv[1]), reverse=True)
    for i in range(resto):
        base[fracs[i % len(fracs)][0]] += 1
    return base


def _clausula_anos(meta, anos, ref):
    """WHERE ... para filtrar a janela de anos, ou '' se não aplicável."""
    if anos == "todos" or meta.get("ano") is None:
        return ""
    n = int(anos)
    minimo = ref - (n - 1)
    return f" WHERE `{meta['ano']}` >= {minimo}"


# ---------------------------------------------------------------------------
# consultas ao DW
# ---------------------------------------------------------------------------

def _ano_referencia(cur):
    """Maior ano observado entre os fatos-mestre com data."""
    ref = 0
    for meta in fatos.MESTRES.values():
        if meta.get("ano"):
            cur.execute(f"SELECT MAX(`{meta['ano']}`) FROM `{meta['tabela']}`")
            v = cur.fetchone()[0]
            if v:
                ref = max(ref, int(v))
    return ref


def _perfil_fato(cur, meta, massa, anos, ref):
    tab = meta["tabela"]
    where = _clausula_anos(meta, anos, ref)

    cur.execute(f"SELECT COUNT(*) FROM `{tab}`{where}")
    total = int(cur.fetchone()[0])
    alvo = int(round(total * massa))

    datas = {}
    if meta.get("ano") and alvo > 0:
        cur.execute(
            f"SELECT `{meta['ano']}`,`{meta['mes']}`,`{meta['dia']}`,COUNT(*) "
            f"FROM `{tab}`{where} "
            f"GROUP BY 1,2,3"
        )
        pares = []
        for ano, mes, dia, qtd in cur.fetchall():
            if ano is None or mes is None or dia is None:
                continue
            pares.append((f"{int(ano)}-{int(mes)}-{int(dia)}", int(qtd)))
        datas = {k: v for k, v in _maior_resto(pares, alvo).items() if v > 0}

    categorias = {}
    for col in meta.get("categorias", []):
        cur.execute(
            f"SELECT `{col}`,COUNT(*) FROM `{tab}`{where} "
            f"GROUP BY 1 ORDER BY 2 DESC"
        )
        d = {}
        for val, qtd in cur.fetchall():
            if val is None:
                continue
            d[str(val)] = int(qtd)
        if d:
            categorias[col] = d

    resultado = dict(total_dw=total, alvo=alvo, datas=datas,
                     categorias=categorias)

    # fração com anexo (para dimensionar a tabela anexo)
    col_anexo = meta.get("tem_anexo")
    if col_anexo:
        cur.execute(
            f"SELECT COUNT(*) FROM `{tab}`{where} "
            f"{'AND' if where else 'WHERE'} `{col_anexo}` IS NOT NULL "
            f"AND `{col_anexo}` <> ''"
        )
        com = int(cur.fetchone()[0])
        resultado["com_anexo"] = int(round(com * massa))

    return resultado


def _dimensoes(cur):
    dims = {}
    # usuarios: [ [id, sta_tipo], ... ]
    cur.execute("SELECT id_usuario, sta_tipo FROM d_usuarios_unico__")
    dims["usuarios"] = [[int(i), str(t)] for i, t in cur.fetchall()]
    # unidades: [id, ...]
    cur.execute("SELECT id_unidade FROM d_unidades_unico__")
    dims["unidades"] = [int(r[0]) for r in cur.fetchall()]
    # series: [ [id, nome], ... ]
    cur.execute("SELECT id_serie, tipo_documento FROM d_tipo_documento_unico_unico__")
    dims["series"] = [[int(i), n] for i, n in cur.fetchall()]
    # tipos de procedimento: [ [id, nome], ... ]
    cur.execute("SELECT id_tipo_procedimento, nome FROM d_tipo_procedimento_unico__")
    dims["tipos_proc"] = [[int(i), n] for i, n in cur.fetchall()]
    # hipoteses: [ [id, nome], ... ]
    cur.execute("SELECT id_hipotese_legal, nome FROM d_hipotese_legal_unico__")
    dims["hipoteses"] = [[int(i), n] for i, n in cur.fetchall()]
    # tarefas: [ id, ... ]
    cur.execute("SELECT id_tarefa FROM d_tarefas_de_atividades_unico__")
    dims["tarefas"] = [int(r[0]) for r in cur.fetchall()]
    return dims


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def construir_perfil(massa, anos, seed, salvar=True, verbose=True):
    conn = db.conectar_dw()
    cur = conn.cursor()
    try:
        ref = _ano_referencia(cur)
        perfil = {
            "parametros": {"massa": massa, "anos": anos, "seed": seed,
                           "ano_referencia": ref},
            "fatos": {},
            "dimensoes": _dimensoes(cur),
        }
        for nome, meta in fatos.TODOS.items():
            p = _perfil_fato(cur, meta, massa, anos, ref)
            perfil["fatos"][nome] = p
            if verbose:
                print(f"  {nome:24s} dw={p['total_dw']:>10d} "
                      f"alvo={p['alvo']:>9d}  buckets_data={len(p['datas'])}")
    finally:
        cur.close()
        conn.close()

    if salvar:
        with open(config.PERFIL_JSON, "w", encoding="utf-8") as f:
            json.dump(perfil, f, ensure_ascii=False)
        if verbose:
            print(f"Perfil salvo em {config.PERFIL_JSON}")
    return perfil


def carregar_perfil():
    with open(config.PERFIL_JSON, encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    import sys
    massa = float(sys.argv[1]) if len(sys.argv) > 1 else 0.005
    anos = sys.argv[2] if len(sys.argv) > 2 else "todos"
    print(f"Construindo perfil massa={massa} anos={anos} ...")
    construir_perfil(massa, anos, config.SEED_PADRAO)
