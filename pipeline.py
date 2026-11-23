#!/usr/bin/env python3
"""
Lista de leads B2B priorizada a partir dos dados abertos do CNPJ (Receita Federal).

Dois modos (campo `modo` em [icp] no config):
  multidisciplinar  (config.toml)            clínicas de terapia de uma região
    01_carregar.sql > 02_funil.sql > 03_pontuacao.sql
  tea               (config_tea_brasil.toml)  espaços terapêuticos para TEA/TDAH no Brasil inteiro
    01_carregar.sql > 02_funil_tea.sql > 03_pontuacao_tea.sql

Uso:
  pip3 install duckdb
  python3 pipeline.py                      # usa config.toml (por padrão, os dados fictícios de exemplo/)
  python3 pipeline.py --config config_tea_brasil.toml
"""
import argparse
import os
import re
try:
    import tomllib                      # Python 3.11+
except ModuleNotFoundError:
    import tomli as tomllib             # Python 3.10 ou anterior: pip3 install tomli

import duckdb

AQUI = os.path.dirname(os.path.abspath(__file__))

COLUNAS_SAIDA = ["posicao", "grupo", "pontuacao", "cnpj", "razao_social", "nome_fantasia",
                 "nm_municipio", "bairro", "cep", "data_inicio_atividade", "porte",
                 "capital_social", "n_cnaes_icp", "n_socios", "cnae_principal"]
COLUNAS_TEA = ["posicao_uf", "pontuacao", "perfil", "palavra_chave", "cnpj", "razao_social",
               "nome_fantasia", "uf", "nm_municipio", "bairro", "data_inicio_atividade", "porte",
               "capital_social", "terapias", "n_socios"]
COLUNAS_CONTATO = ["telefone_1", "email"]
ETAPAS = {
    "multidisciplinar": ("01_carregar.sql", "02_funil.sql", "03_pontuacao.sql"),
    "tea": ("01_carregar.sql", "02_funil_tea.sql", "03_pontuacao_tea.sql"),
}


def sql_literal(valor):
    """Converte um valor do config em literal SQL para SET VARIABLE."""
    if isinstance(valor, bool):
        return "true" if valor else "false"
    if isinstance(valor, (int, float)):
        return str(valor)
    if isinstance(valor, list):
        return "[" + ", ".join(sql_literal(v) for v in valor) + "]"
    return "'" + str(valor).replace("'", "''") + "'"


def rodar_sql(con, arquivo):
    texto = open(os.path.join(AQUI, "sql", arquivo), encoding="utf-8").read()
    for bloco in re.split(r";\s*\n", texto):
        corpo = "\n".join(l for l in bloco.splitlines() if not l.strip().startswith("--")).strip()
        if corpo:
            con.execute(corpo)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(AQUI, "config.toml"))
    ap.add_argument("--saida", default=os.path.join(AQUI, "saida"))
    args = ap.parse_args()

    cfg = tomllib.load(open(args.config, "rb"))
    pasta = cfg["fontes"]["pasta"]
    if not os.path.isabs(pasta):
        pasta = os.path.join(AQUI, pasta)

    modo = cfg["icp"].get("modo", "multidisciplinar")
    variaveis = {"pasta": pasta}
    for secao, valores in cfg.items():
        if secao != "fontes":
            variaveis.update({k: v for k, v in valores.items() if k != "modo"})

    con = duckdb.connect()
    for nome, valor in variaveis.items():
        con.execute(f"SET VARIABLE {nome} = {sql_literal(valor)}")

    for arquivo in ETAPAS[modo]:
        rodar_sql(con, arquivo)

    os.makedirs(args.saida, exist_ok=True)
    base = COLUNAS_TEA if modo == "tea" else COLUNAS_SAIDA
    ordem = "uf, posicao_uf" if modo == "tea" else "grupo DESC, posicao"
    colunas = base + (COLUNAS_CONTATO if cfg["saida"]["incluir_contatos"] else [])
    destino = os.path.join(args.saida, "lista_priorizada.csv")
    con.execute(f"""
        COPY (SELECT {', '.join(colunas)} FROM lista_priorizada ORDER BY {ordem})
        TO '{destino}' (HEADER, DELIMITER ';')""")
    con.execute(f"COPY funil TO '{os.path.join(args.saida, 'funil.csv')}' (HEADER, DELIMITER ';')")

    print("\nFunil")
    con.sql("SELECT * FROM funil").show()
    print("Top 10")
    if modo == "tea":
        con.sql("""SELECT pontuacao, perfil, palavra_chave, coalesce(nullif(nome_fantasia, ''), razao_social) AS nome,
                          uf, nm_municipio, terapias
                   FROM lista_priorizada ORDER BY pontuacao DESC, uf LIMIT 10""").show()
    else:
        con.sql("""SELECT posicao, grupo, pontuacao, coalesce(nullif(nome_fantasia, ''), razao_social) AS nome,
                          nm_municipio, n_cnaes_icp, n_socios
                   FROM lista_priorizada ORDER BY pontuacao DESC, posicao LIMIT 10""").show()
    print(f"Arquivos gerados em {args.saida}/")


if __name__ == "__main__":
    main()
