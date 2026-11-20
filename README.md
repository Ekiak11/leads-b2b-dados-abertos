# Leads B2B com dados abertos do CNPJ

Pipeline em **SQL (DuckDB) + Python** que transforma a base pública de CNPJs da Receita Federal numa **lista de prospecção priorizada**: filtra o perfil de cliente ideal (ICP), descarta quem não tem cara de cliente e pontua cada empresa para o time comercial saber por onde começar.

## O problema

Em mercados com **baixa presença digital** — clínicas pequenas, prestadores de serviço locais — não adianta esperar o lead chegar por anúncio ou inbound. O caminho é outbound: ligação, WhatsApp e visita. A pergunta passa a ser **quem abordar primeiro**.

Os dados abertos do CNPJ respondem boa parte disso de graça: atividade econômica (CNAE), endereço, porte, capital social, data de abertura e quadro de sócios.

## O caso real

Construí este fluxo para a operação comercial de uma healthtech que vende para **clínicas de terapia** (fonoaudiologia, terapia ocupacional, psicologia) no Grande Rio. O funil ficou assim:

| Etapa | Critério | Empresas |
|---|---|---|
| 1 | Ativas, no Rio, Baixada, Niterói e São Gonçalo, com CNAE de terapia | 3.121 |
| 2 | Multidisciplinares (2+ CNAEs do ICP) e com sócios cadastrados | 2.018 |
| 3 | Nome com cara de clínica (clínica, espaço, centro, terapia, TEA, infantil…) | 1.403 |
| 4 | Melhor pontuação: 300 no Rio + 170 nos demais municípios | 470 |
| 5 | Validação manual (Google: está ativa? tem avaliações?) → listas semanais de ligação | ~30 por dia |

No projeto, as buscas foram feitas pela Casa dos Dados e o quadro de sócios pela API Minha Receita. **Este repositório reimplementa a mesma lógica em SQL sobre os arquivos brutos da Receita**, para ser reprodutível por qualquer pessoa e adaptável a outro ICP. A base e as listas do cliente **não** estão aqui.

## Como a pontuação funciona

| Sinal | Pontos | Por quê |
|---|---|---|
| Cada CNAE do ICP | 2 | Mais especialidades, operação maior |
| Sócios cadastrados | 1 por sócio, até 3 | Empresa estruturada, com mais de um decisor |
| Nome de nicho (TEA, ABA, neuro, infantil…) | 4 | Segmento prioritário do ICP |
| Nome multidisciplinar (multi, integrado…) | 2 | Operação com várias terapias |
| Capital social ≥ R$ 50 mil | 1 | Sinal de porte |

Todos os pesos, CNAEs, municípios e palavras-chave ficam no `config.toml`. Trocar de mercado é trocar o arquivo, sem mexer no SQL.

## Rodar agora (dados fictícios)

```bash
pip3 install -r requirements.txt
python3 exemplo/gerar_exemplo.py   # cria 120 empresas fictícias no layout da Receita
python3 pipeline.py
```

Saída em `saida/`:
- `funil.csv` — quantas empresas sobram em cada etapa
- `lista_priorizada.csv` — a lista final, ordenada por pontuação dentro de cada grupo

## Rodar com os dados reais

1. Baixe os arquivos de **Estabelecimentos**, **Empresas**, **Sócios** e **Municípios** no portal de dados abertos do CNPJ da Receita Federal (busque "Cadastro Nacional da Pessoa Jurídica" em dados.gov.br).
2. Descompacte tudo numa pasta `dados/` (ela está no `.gitignore` e nunca vai para o GitHub).
3. No `config.toml`, troque `pasta = "exemplo"` por `pasta = "dados"`.
4. `python3 pipeline.py`

A base nacional tem dezenas de milhões de linhas. O DuckDB lê os arquivos direto do disco, e o pipeline já filtra por UF e situação cadastral na leitura, então roda num notebook comum.

## Estrutura

```
config.toml            ICP, pesos da pontuação e tamanho da lista final
pipeline.py            orquestra as etapas e grava a saída
sql/01_carregar.sql    leitura dos arquivos da Receita (layout oficial)
sql/02_funil.sql       etapas 1 a 3 do funil
sql/03_pontuacao.sql   lead scoring, lista final e resumo do funil
exemplo/               gerador de dados fictícios no mesmo layout
```

## Privacidade (LGPD)

- O quadro de sócios tem nome de pessoas físicas. O pipeline usa **só a contagem** de sócios; nomes e documentos não saem da etapa de leitura.
- Telefone e e-mail ficam fora da saída por padrão (`incluir_contatos = false`). Ative só para uso interno do time comercial.
- Os dados de exemplo são inventados: CNPJs começam com `000` e nenhum nome corresponde a uma empresa real.

## Autor

**Kaike Souza da Cunha** — Revenue Operations e análise de dados comerciais.
[LinkedIn](https://linkedin.com/in/kaike-souza)
