-- Funil do modo TEA: espaços terapêuticos para crianças com autismo, TDAH e síndromes
-- correlatas. As regras ficam no config_tea_brasil.toml.

-- Etapa 1: estabelecimentos ATIVOS (já filtrados na leitura) com CNAE de terapia
CREATE OR REPLACE TABLE tea1_base AS
WITH e AS (
    SELECT es.*,
           m.nm_municipio,
           list_distinct(list_filter(
               list_prepend(es.cnae_principal, string_split(coalesce(es.cnaes_secundarios, ''), ',')),
               lambda c: c <> '')) AS cnaes
    FROM estabelecimentos es
    LEFT JOIN municipios m USING (cd_municipio)
)
SELECT *,
       list_intersect(cnaes, getvariable('cnaes_terapia')) AS cnaes_terapia_empresa
FROM e
WHERE len(list_intersect(cnaes, getvariable('cnaes_terapia'))) > 0
   OR list_contains(cnaes, getvariable('cnae_outros_saude'));

-- Etapa 2: tira órgãos públicos, SCPs, empresários individuais e nomes fora do perfil
CREATE OR REPLACE TABLE tea2_elegiveis AS
WITH j AS (
    SELECT b.*,
           emp.razao_social, emp.natureza_juridica, emp.capital_social, emp.porte,
           upper(strip_accents(coalesce(emp.razao_social, '') || ' | ' || coalesce(b.nome_fantasia, ''))) AS nome_busca
    FROM tea1_base b
    JOIN empresas emp USING (cnpj_basico)
)
SELECT *,
       regexp_extract(nome_busca, '(' || array_to_string(getvariable('palavras_fortes'), '|') || ')') AS kw_forte,
       regexp_extract(nome_busca, '(' || array_to_string(getvariable('palavras_infantis'), '|') || ')') AS kw_infantil
FROM j
WHERE natureza_juridica NOT LIKE '1%'
  AND NOT list_contains(getvariable('naturezas_excluidas'), natureza_juridica)
  AND (NOT regexp_matches(nome_busca, '(' || array_to_string(getvariable('palavras_exclusao'), '|') || ')')
       OR regexp_matches(nome_busca, '(' || array_to_string(getvariable('palavras_fortes'), '|') || ')'));

-- Etapa 3: perfil
--   A = nome com TEA/autismo/TDAH/ABA/neurodesenvolvimento... e terapia (ou "outras saúde")
--   B = nome infantil e terapia ocupacional ou fonoaudiologia
CREATE OR REPLACE TABLE tea3_perfil AS
SELECT *,
       CASE WHEN kw_forte <> '' THEN 'A - TEA explícito no nome'
            ELSE 'B - Clínica infantil com TO/Fono' END AS perfil,
       CASE WHEN kw_forte <> '' THEN kw_forte ELSE kw_infantil END AS palavra_chave
FROM tea2_elegiveis
WHERE (kw_forte <> '' AND (len(cnaes_terapia_empresa) > 0 OR list_contains(cnaes, getvariable('cnae_outros_saude'))))
   OR (kw_infantil <> '' AND (list_contains(cnaes, '8650005') OR list_contains(cnaes, '8650006')));
