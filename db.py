# -*- coding: utf-8 -*-
"""Conexões e helpers de banco (pymysql), no mesmo padrão dos scripts existentes."""
import contextlib
import time

import pymysql

import config


def conectar(cfg):
    return pymysql.connect(**cfg)


def conectar_dw():
    return conectar(config.CONN_DW)


def conectar_estrutura():
    return conectar(config.CONN_ESTRUTURA)


def conectar_destino():
    config.valida_destino()
    return conectar(config.CONN_DESTINO)


@contextlib.contextmanager
def checks_desligados(cursor):
    """Desliga apenas FK checks durante a carga (tabelas carregadas em ordem,
    algumas referenciam catálogos não populados como tarja_assinatura).

    NÃO desliga UNIQUE_CHECKS: com dados eventualmente duplicados em chaves
    únicas, UNIQUE_CHECKS=0 corrompe o índice e o COMMIT falha com erro 1180
    ("Operation not permitted"); mantendo-o ligado, uma duplicata vira um 1062
    claro e evita a corrupção.
    """
    cursor.execute("SET FOREIGN_KEY_CHECKS=0")
    try:
        yield
    finally:
        cursor.execute("SET FOREIGN_KEY_CHECKS=1")


def _fmt_dur(seg):
    seg = int(seg)
    h, r = divmod(seg, 3600)
    m, s = divmod(r, 60)
    if h:
        return f"{h}h{m:02d}m"
    if m:
        return f"{m}m{s:02d}s"
    return f"{s}s"


def _barra(rotulo, feitos, total, inicio):
    dec = time.time() - inicio
    taxa = feitos / dec if dec > 0 else 0
    if total and total > 0:
        pct = 100.0 * feitos / total
        n = int(pct / 5)
        barra = "#" * n + "." * (20 - n)
        eta = _fmt_dur((total - feitos) / taxa) if taxa > 0 else "?"
        txt = (f"\r  {rotulo:26s} [{barra}] {pct:5.1f}%  "
               f"{feitos:>10,}/{total:<10,} {taxa:>7,.0f}/s ETA {eta:>6s}")
    else:
        txt = f"\r  {rotulo:26s} {feitos:>10,} linhas  {taxa:>7,.0f}/s"
    import sys
    sys.stdout.write(txt)
    sys.stdout.flush()


def inserir_em_lote(conn, cursor, tabela, colunas, gerador, tam_lote=None,
                    total=None, rotulo=""):
    """Consome um gerador de tuplas e insere em `tabela` via executemany.

    Retorna o total de linhas inseridas. Faz commit a cada lote e, se `total`
    for informado, imprime uma barra de progresso (%, taxa e ETA) na mesma linha.
    """
    tam_lote = tam_lote or config.TAM_LOTE
    inicio = time.time()
    cols_sql = ", ".join(f"`{c}`" for c in colunas)
    ph = ", ".join(["%s"] * len(colunas))
    sql = f"INSERT INTO `{tabela}` ({cols_sql}) VALUES ({ph})"

    def _grava(lote):
        # retenta em erros transitórios do Windows (EPERM 1180 por antivírus
        # travando o .ibd sob IO pesado). Backoff crescente; reconecta se cair.
        nonlocal cursor
        ultimo = None
        for tentativa in range(8):
            try:
                cursor.executemany(sql, lote)
                conn.commit()
                return
            except (pymysql.err.OperationalError,
                    pymysql.err.InternalError,
                    pymysql.err.InterfaceError) as e:
                ultimo = e
                try:
                    conn.rollback()
                except Exception:
                    try:
                        conn.ping(reconnect=True)
                        cursor = conn.cursor()
                        cursor.execute("SET FOREIGN_KEY_CHECKS=0")
                    except Exception:
                        pass
                time.sleep(min(2.0 * (tentativa + 1), 10.0))
        raise ultimo

    lote = []
    feitos = 0
    ult_draw = 0.0
    for linha in gerador:
        lote.append(linha)
        if len(lote) >= tam_lote:
            _grava(lote)
            feitos += len(lote)
            lote = []
            if rotulo and time.time() - ult_draw >= 0.5:
                _barra(rotulo, feitos, total, inicio)
                ult_draw = time.time()
    if lote:
        _grava(lote)
        feitos += len(lote)
    if rotulo:
        _barra(rotulo, feitos, total, inicio)
        import sys
        sys.stdout.write("\n")
        sys.stdout.flush()
    return feitos


def contar(cursor, db, tabela):
    cursor.execute(f"SELECT COUNT(*) FROM `{db}`.`{tabela}`")
    return cursor.fetchone()[0]


def tabela_existe(cursor, db, tabela):
    cursor.execute(
        "SELECT 1 FROM information_schema.tables "
        "WHERE table_schema=%s AND table_name=%s",
        (db, tabela),
    )
    return cursor.fetchone() is not None
