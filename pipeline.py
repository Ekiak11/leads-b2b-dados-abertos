#!/usr/bin/env python3
"""
Lista de leads B2B priorizada a partir dos dados abertos do CNPJ (Receita Federal).

Etapas (cada uma em SQL, na pasta sql/):
  01_carregar.sql   carrega estabelecimentos, empresas, sócios (só contagem) e municípios
  02_funil.sql      ativa + município + CNAE do ICP -> multidisciplinar com QSA -> nome de clínica
  03_pontuacao.sql  lead scoring e lista final por região

Uso:
  pip3 install duckdb
  python3 pipeline.py                      # usa config.toml (por padrão, os dados fictícios de exemplo/)
  python3 pipeline.py --config outro.toml
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
COLUNAS_CONTATO = ["telefone_1", "email"]


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

    variaveis = {"pasta": pasta}
    for secao in ("icp", "pontuacao", "saida"):
        variaveis.update(cfg[secao])

    con = duckdb.connect()
    for nome, valor in variaveis.items():
        con.execute(f"SET VARIABLE {nome} = {sql_literal(valor)}")

    for arquivo in ("01_carregar.sql", "02_funil.sql", "03_pontuacao.sql"):
        rodar_sql(con, arquivo)

    os.makedirs(args.saida, exist_ok=True)
    colunas = COLUNAS_SAIDA + (COLUNAS_CONTATO if cfg["saida"]["incluir_contatos"] else [])
    destino = os.path.join(args.saida, "lista_priorizada.csv")
    con.execute(f"""
        COPY (SELECT {', '.join(colunas)} FROM lista_priorizada ORDER BY grupo DESC, posicao)
        TO '{destino}' (HEADER, DELIMITER ';')""")
    con.execute(f"COPY funil TO '{os.path.join(args.saida, 'funil.csv')}' (HEADER, DELIMITER ';')")

    print("\nFunil")
    con.sql("SELECT * FROM funil").show()
    print("Top 10")
    con.sql("""SELECT posicao, grupo, pontuacao, coalesce(nullif(nome_fantasia, ''), razao_social) AS nome,
                      nm_municipio, n_cnaes_icp, n_socios
               FROM lista_priorizada ORDER BY pontuacao DESC, posicao LIMIT 10""").show()
    print(f"Arquivos gerados em {args.saida}/")


if __name__ == "__main__":
    main()
