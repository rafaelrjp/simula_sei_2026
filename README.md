# simula_sei_2026

Gerador de **massa de teste 100% sintética** para o SEI, dirigido pelos volumes e
distribuições agregadas do **Data Warehouse** (`sei_dw_bd`).

Produz o banco **`sei_simulado`** (mesma estrutura do `sei`, 511 tabelas) com dados
inventados que, ao serem reprocessados pelo ETL e pelos painéis Power BI,
reproduzem os mesmos números do DW — **escalável por fração de massa e janela de
anos**, sem nenhum dado real (usuários, nomes de arquivo, CPF/CNPJ, textos, anexos).

## Por que dirigido pelo DW

O DW não guarda data real, apenas as partes `ano_id`, `mes_id`, `trimestre_id`,
`dia_semana_id` (`YEAR`, `MONTH`, `QUARTER`, `WEEKDAY`). O gerador lê essas partes
em cada tabela-fato e reconstrói datas concretas em `sei_simulado` que **respeitam
exatamente a distribuição (ano × mês × dia-da-semana)** observada — além dos volumes
por categoria (tipo de processo, série, unidade, usuário, hipótese legal, situação…).

## Requisitos

- Python 3 com `pymysql`.
- MariaDB/MySQL local com os bancos `sei_dw_bd`, `sei` e `sei_simulado`.
- Credenciais lidas de `../projeto-simula-sei/acesso_bds.txt` (nada é duplicado aqui).
- Trava de segurança: o destino **tem** de ser o schema `sei_simulado`.

## Uso

```
script.bat [-anos N|todos] [-massa F] [-seed S] [--force] [--confirmar] ACAO
```

| Parâmetro     | Significado                                                        |
|---------------|-------------------------------------------------------------------|
| `-massa F`    | fração do total: `0.005`=0,5%, `0.5`=50%, `1`=100% (default 0.005) |
| `-anos N`     | últimos N anos; `todos` = todos os anos (default `todos`)          |
| `-seed S`     | semente determinística (mesmos parâmetros ⇒ mesma saída)          |
| `--force`     | permite carregar sobre tabelas operacionais já preenchidas         |
| `--confirmar` | confirma o APAGAR (destrutivo)                                     |
| `--usar-cache`| usa `perfil_agregado.json` existente (não reconsulta o DW)         |

### Ações

| Ação       | O que faz                                                              |
|------------|-----------------------------------------------------------------------|
| `PREPARAR` | cria/recria a estrutura de `sei_simulado` (511 tabelas)               |
| `PERFIL`   | consulta o DW e grava `perfil_agregado.json` (aplica `-anos`/`-massa`) |
| `GERAR`    | dry-run: conta as linhas que seriam geradas, sem escrever             |
| `CARREGAR` | gera e **insere** no `sei_simulado`                                    |
| `DUMPAR`   | gera arquivos `.sql` por tabela em `saida_sql/` (ordem referencial)    |
| `VALIDAR`  | compara contagens/distribuições do `sei_simulado` com o perfil        |
| `APAGAR`   | trunca as tabelas de dados do `sei_simulado` (exige `--confirmar`)     |

### Exemplos

```bat
script.bat PREPARAR
script.bat -anos 2 -massa 0.5 CARREGAR      REM 50% dos últimos 2 anos, no banco
script.bat -anos todos -massa 1 DUMPAR      REM 100% de tudo, em arquivos .sql
script.bat -anos 2 -massa 0.005 VALIDAR
script.bat APAGAR --confirmar
```

## Fluxo típico

```bat
script.bat PREPARAR
script.bat -anos 2 -massa 0.005 CARREGAR
script.bat -anos 2 -massa 0.005 VALIDAR
```

Para gerar um pacote SQL aplicável em outra máquina:

```bat
script.bat -anos todos -massa 1 DUMPAR
REM aplique os arquivos na ordem numérica em saida_sql\:
REM   mysql -u root -p sei_simulado < saida_sql\01_tipo_procedimento.sql  ...
```

## Arquitetura

```
script.bat / simula.py   CLI e wrapper (parse de -anos/-massa/-seed/ACAO)
config.py                credenciais (parse do acesso_bds.txt) e caminhos
db.py                    conexões pymysql + inserção em lote (executemany)
perfil.py                PERFIL: agrega o DW -> perfil_agregado.json
fatos.py                 mapa dos fatos do DW (colunas de data e categorias)
contexto.py              Plano/espinha de processos + amostragem determinística
datas.py                 (ano,mes,dia_semana,qtd) -> datas concretas
fake.py                  textos sintéticos (siglas, nomes, protocolos, anexos)
geradores/               base, processos, documentos, atividades, modulos
tabelas.py               registro das tabelas em ORDEM REFERENCIAL
carga.py                 GERAR (dry-run) / CARREGAR (aplica no banco)
dump.py                  DUMPAR (arquivos .sql por tabela)
validar.py               VALIDAR e APAGAR
preparar.py              PREPARAR (importa a estrutura)
```

## Fidelidade e limites

- **Exatos por construção**: volumes e distribuição (categoria × ano × mês ×
  dia-da-semana) dos fatos-mestre — processos, documentos gerados ('G') e externos
  ('R'), movimentação (tarefa 32) e assinaturas — e o total escalado pela massa.
- **Aproximados**: fatos derivados (cancelados, restritos, situação, limbo, 180,
  desempenho) são reproduzidos por atribuição/seleção sobre a espinha gerada;
  casam contagem e distribuição por categoria, mas sem garantia de consistência
  conjunta perfeita entre todos os fatos simultaneamente.
- **Privacidade**: nomes, siglas e nomes de arquivo são inventados; e-mails usam
  `@example.invalid`; não há CPF/CNPJ válido, senha ou conteúdo de documento/anexo.
- **Reprodutibilidade**: IDs, datas e escolhas derivam da `seed`.

> Observação: os SQLs de ETL em `sql_refatora_sei/` têm prefixos fixos
> `sei.` (apontam para o schema real). Para reprocessá-los sobre `sei_simulado`,
> troque `sei.` por `sei_simulado.` (ou rode-os com esse schema como default).
