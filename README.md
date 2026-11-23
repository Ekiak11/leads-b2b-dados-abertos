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

## Segundo caso: espaços para TEA/TDAH no Brasil inteiro

Depois do Grande Rio, o ICP ficou mais estreito: só **espaços terapêuticos para crianças com autismo (TEA), TDAH e síndromes correlatas**, em todo o país. Contar CNAEs não resolve, porque psicologia + fono + TO também descreve clínicas de adultos. O que separa o público é o **nome da empresa**. O modo `tea` (`config_tea_brasil.toml`) usa dois perfis:

| Perfil | Regra | Por quê |
|---|---|---|
| A — TEA explícito no nome | Nome com autismo, TEA, ABA, TDAH, neurodesenvolvimento, desenvolvimento infantil, intervenção precoce, síndrome, integração sensorial… **e** CNAE de terapia (ou "outras atividades de saúde", comum em clínicas ABA) | O próprio nome declara o público |
| B — Clínica infantil com TO/Fono | Nome infantil (kids, criança, pediatria, neuro, sensorial, psicopedagogia, brincar…) **e** terapia ocupacional ou fonoaudiologia no CNAE | TO e fono para criança é o desenho típico do atendimento TEA |

Saem: órgãos públicos, sociedades em conta de participação, empresários individuais e nomes fora do perfil (odonto, estética, hospital, escola, pilates, home care, comunidade terapêutica…), a não ser que o nome tenha uma palavra forte de TEA.

Na base de novembro de 2026 (74,4 milhões de estabelecimentos), isso deu **cerca de 7,2 mil espaços em todos os estados**: 3.536 no perfil A e 3.650 no perfil B. Ficaram de fora cerca de 22 mil clínicas que só combinam psicologia, TO e fono sem nada no nome que indique público infantil — muitas são de adultos ou SCPs.

> A execução real foi feita com scripts Python em streaming (a máquina tinha 4 GB de RAM). O SQL deste repositório reproduz as mesmas regras; os números podem variar um pouco conforme o mês da base.

```bash
python3 pipeline.py --config config_tea_brasil.toml
```

A saída traz `perfil`, `palavra_chave` (a palavra que colocou a empresa na lista, para conferência rápida), `terapias`, `uf` e a posição dentro de cada estado (`top_por_uf` no config limita a lista).

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

1. Baixe os arquivos de **Estabelecimentos**, **Empresas**, **Sócios** e **Municípios** da Receita Federal. Desde 2025 eles ficam no repositório da Receita em [arquivos.receitafederal.gov.br](https://arquivos.receitafederal.gov.br/index.php/s/YggdBLfdninEJX9), numa pasta por mês (`AAAA-MM`), com 10 zips de cada tipo (`Estabelecimentos0.zip` a `Estabelecimentos9.zip` etc.). São cerca de 7 GB compactados.
2. Descompacte tudo numa pasta `dados/` (ela está no `.gitignore` e nunca vai para o GitHub).
3. No config, troque `pasta = "exemplo"` por `pasta = "dados"`.
4. `python3 pipeline.py` (Grande Rio) ou `python3 pipeline.py --config config_tea_brasil.toml` (Brasil, TEA/TDAH)

A base nacional tem dezenas de milhões de linhas. O DuckDB lê os arquivos direto do disco, e o pipeline já filtra por situação cadastral (e por UF, quando o config define uma) na leitura. Com `uf = ""` ele percorre o país inteiro; num notebook comum isso leva alguns minutos.

## Estrutura

```
config.toml              ICP 1: clínicas multidisciplinares no Grande Rio
config_tea_brasil.toml   ICP 2: espaços para TEA/TDAH no Brasil inteiro
pipeline.py              escolhe o modo pelo config, roda as etapas e grava a saída
sql/01_carregar.sql      leitura dos arquivos da Receita (layout oficial)
sql/02_funil.sql         modo multidisciplinar: etapas 1 a 3 do funil
sql/03_pontuacao.sql     modo multidisciplinar: lead scoring, lista final e resumo
sql/02_funil_tea.sql     modo TEA: CNAE de terapia, exclusões e perfis A/B
sql/03_pontuacao_tea.sql modo TEA: pontuação, lista por estado e resumo
exemplo/               gerador de dados fictícios no mesmo layout
```

## Privacidade (LGPD)

- O quadro de sócios tem nome de pessoas físicas. O pipeline usa **só a contagem** de sócios; nomes e documentos não saem da etapa de leitura.
- Telefone e e-mail ficam fora da saída por padrão (`incluir_contatos = false`). Ative só para uso interno do time comercial.
- Os dados de exemplo são inventados: CNPJs começam com `000` e nenhum nome corresponde a uma empresa real.

## Autor

**Kaike Souza da Cunha** — Revenue Operations e análise de dados comerciais.
[LinkedIn](https://linkedin.com/in/kaike-souza)
