# -*- coding: utf-8 -*-
"""CLI do simula_sei_2026.

Uso:
  python simula.py [-anos N|todos] [-massa F] [-seed S] [--force] [--confirmar] ACAO

AÇÕES:
  PREPARAR   cria/recria a estrutura de sei_simulado (511 tabelas)
  PERFIL     consulta o DW e grava perfil_agregado.json (aplica -anos/-massa)
  GERAR      dry-run: conta as linhas que seriam geradas (não escreve)
  CARREGAR   gera e INSERE no sei_simulado (aplica no banco)
  DUMPAR     gera arquivos .sql por tabela em saida_sql/ (ordem referencial)
  VALIDAR    compara contagens/distribuições do sei_simulado com o perfil
  APAGAR     trunca as tabelas de dados do sei_simulado (exige --confirmar)

Exemplos:
  simula.py -anos 2 -massa 0.5 CARREGAR
  simula.py -anos todos -massa 1 DUMPAR
"""
import argparse
import sys

import config


def _parse(argv):
    p = argparse.ArgumentParser(prog="simula", add_help=True)
    p.add_argument("-anos", default="todos",
                   help="janela de anos: N (últimos N) ou 'todos'")
    p.add_argument("-massa", type=float, default=0.005,
                   help="fração do total (0.005=0,5%%, 0.5=50%%, 1=100%%)")
    p.add_argument("-seed", type=int, default=config.SEED_PADRAO)
    p.add_argument("--force", action="store_true",
                   help="sobrescreve tabelas operacionais já preenchidas")
    p.add_argument("--confirmar", action="store_true",
                   help="confirma operações destrutivas (APAGAR)")
    p.add_argument("--usar-cache", action="store_true",
                   help="usa perfil_agregado.json existente (não reconsulta o DW)")
    p.add_argument("acao", help="PREPARAR|PERFIL|GERAR|CARREGAR|DUMPAR|VALIDAR|APAGAR")
    return p.parse_args(argv)


def _valida_anos(v):
    if v == "todos":
        return v
    try:
        n = int(v)
        if n <= 0:
            raise ValueError
        return n
    except ValueError:
        raise SystemExit(f"-anos inválido: {v!r} (use inteiro > 0 ou 'todos')")


def _garante_perfil(args):
    import perfil as perfil_mod
    if args.usar_cache:
        import os
        if os.path.isfile(config.PERFIL_JSON):
            print("Usando perfil em cache:", config.PERFIL_JSON)
            return
    anos = _valida_anos(args.anos)
    print(f"Construindo perfil (massa={args.massa}, anos={anos}, seed={args.seed})...")
    perfil_mod.construir_perfil(args.massa, anos, args.seed)


def main(argv=None):
    args = _parse(argv if argv is not None else sys.argv[1:])
    acao = args.acao.upper()
    config.valida_destino()

    if acao == "PREPARAR":
        import preparar
        preparar.executar()
        return

    if acao == "PERFIL":
        _garante_perfil(args)
        return

    if acao == "APAGAR":
        import validar
        validar.apagar(args.confirmar)
        return

    if acao in ("GERAR", "CARREGAR", "DUMPAR", "VALIDAR"):
        import contexto
        if acao == "VALIDAR":
            # valida contra o perfil já existente (ou reconstrói se pedido)
            if not args.usar_cache:
                _garante_perfil(args)
            ctx = contexto.carregar_contexto(args.seed)
            import validar
            validar.executar(ctx)
            return

        _garante_perfil(args)
        ctx = contexto.carregar_contexto(args.seed)
        if acao == "GERAR":
            import carga
            carga.executar(ctx, aplicar=False)
        elif acao == "CARREGAR":
            import carga
            carga.executar(ctx, aplicar=True, force=args.force)
        elif acao == "DUMPAR":
            import dump
            dump.executar(ctx)
        return

    raise SystemExit(f"Ação desconhecida: {args.acao!r}")


if __name__ == "__main__":
    main()
