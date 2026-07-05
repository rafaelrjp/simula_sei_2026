# -*- coding: utf-8 -*-
"""VALIDAR — confere o sei_simulado contra o perfil-alvo.

Compara volumes das tabelas base e a distribuição (ano×mês×dia-da-semana) de
protocolo(P) contra o perfil. Não roda os SQLs de ETL diretamente porque eles
têm prefixos fixos `sei.` (apontam para o schema real), não para sei_simulado.
"""
import config
import db


def _cont(cur, sql, params=None):
    cur.execute(sql, params or ())
    return cur.fetchone()[0]


def executar(ctx):
    perfil = ctx.perfil
    fat = perfil["fatos"]
    conn = db.conectar_destino()
    cur = conn.cursor()
    print(f"== VALIDAR == destino={config.CONN_DESTINO['database']}")

    checagens = [
        ("processos (protocolo P)",
         "SELECT COUNT(*) FROM protocolo WHERE sta_protocolo='P'",
         fat["processos"]["alvo"]),
        ("documentos gerados (G)",
         "SELECT COUNT(*) FROM protocolo WHERE sta_protocolo='G'",
         fat["documentos_gerados"]["alvo"]),
        ("documentos externos (R)",
         "SELECT COUNT(*) FROM protocolo WHERE sta_protocolo='R'",
         fat["documentos_externos"]["alvo"]),
        ("procedimento",
         "SELECT COUNT(*) FROM procedimento", fat["processos"]["alvo"]),
        ("documento",
         "SELECT COUNT(*) FROM documento",
         fat["documentos_gerados"]["alvo"] + fat["documentos_externos"]["alvo"]),
        ("assinatura",
         "SELECT COUNT(*) FROM assinatura", fat["assinaturas"]["alvo"]),
        ("movimentacao (atividade tarefa=32)",
         "SELECT COUNT(*) FROM atividade WHERE id_tarefa=32",
         fat["movimentacao"]["alvo"]),
        ("anexo",
         "SELECT COUNT(*) FROM anexo",
         fat["documentos_gerados"].get("com_anexo", 0)
         + fat["documentos_externos"].get("com_anexo", 0)),
        ("proc. restritos (P, nivel<>0, hipotese)",
         "SELECT COUNT(*) FROM protocolo WHERE sta_protocolo='P' "
         "AND sta_nivel_acesso_global<>'0' AND id_hipotese_legal IS NOT NULL",
         fat["processos_com_hipotese"]["alvo"]),
    ]

    print(f"  {'métrica':42s} {'obtido':>10s} {'alvo':>10s}  ok?")
    todas_ok = True
    for rot, sql, alvo in checagens:
        try:
            got = _cont(cur, sql)
        except Exception as e:
            print(f"  {rot:42s} ERRO: {e}")
            todas_ok = False
            continue
        ok = got == alvo
        todas_ok = todas_ok and ok
        print(f"  {rot:42s} {got:>10d} {alvo:>10d}  {'OK' if ok else 'DIFERE'}")

    # ---- fidelidade da distribuição de datas de protocolo(P) ----
    cur.execute(
        "SELECT YEAR(dta_inclusao), MONTH(dta_inclusao), WEEKDAY(dta_inclusao), "
        "COUNT(*) FROM protocolo WHERE sta_protocolo='P' GROUP BY 1,2,3"
    )
    obt = {f"{a}-{m}-{d}": c for a, m, d, c in cur.fetchall()}
    alvo_d = fat["processos"]["datas"]
    difs = sum(abs(obt.get(k, 0) - v) for k, v in alvo_d.items())
    extras = sum(v for k, v in obt.items() if k not in alvo_d)
    print(f"\n  distribuição datas protocolo(P): {len(alvo_d)} buckets alvo, "
          f"desvio_total={difs + extras} (0 = idêntico)")

    cur.close()
    conn.close()
    print("\nResultado:", "TUDO OK" if todas_ok else "há divergências (ver acima)")
    return todas_ok


def apagar(confirmar):
    import tabelas
    nome = config.valida_destino()
    conn = db.conectar_destino()
    cur = conn.cursor()
    if not confirmar:
        # dupla confirmação: sem a flag, apenas mostra o que faria
        print("== APAGAR (simulação) == use --confirmar para truncar de fato.")
        print(f"   Truncaria {len(tabelas.TABELAS_DADOS)} tabelas em '{nome}'.")
        cur.close(); conn.close()
        return
    print(f"== APAGAR == truncando dados de '{nome}' (estrutura preservada)")
    cur.execute("SET FOREIGN_KEY_CHECKS=0")
    for t in tabelas.TABELAS_DADOS:
        if db.tabela_existe(cur, nome, t):
            cur.execute(f"TRUNCATE TABLE `{t}`")
    cur.execute("SET FOREIGN_KEY_CHECKS=1")
    conn.commit()
    cur.close()
    conn.close()
    print("Concluído.")
