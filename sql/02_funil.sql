-- Etapas 1 a 3 do funil: do universo de CNPJs ao público com cara de cliente.

-- Etapa 1: estabelecimentos ATIVOS, nos municípios-alvo, com pelo menos um CNAE do ICP
CREATE OR REPLACE TABLE etapa1_base AS
WITH e AS (
    SELECT es.*,
           m.nm_municipio,
           list_distinct(list_filter(
               list_prepend(es.cnae_principal, string_split(coalesce(es.cnaes_secundarios, ''), ',')),
               lambda c: c <> '')) AS cnaes
    FROM estabelecimentos es
    JOIN municipios m USING (cd_municipio)
    WHERE es.situacao_cadastral = '02'
      AND es.uf = getvariable('uf')
      AND list_contains(getvariable('municipios'), m.nm_municipio)
)
SELECT *,
       len(list_intersect(cnaes, getvariable('cnaes'))) AS n_cnaes_icp
FROM e
WHERE len(list_intersect(cnaes, getvariable('cnaes'))) > 0;

-- Etapa 2: multidisciplinares (>= N CNAEs do ICP) e com sócios cadastrados
CREATE OR REPLACE TABLE etapa2_multidisciplinar AS
SELECT b.*,
       coalesce(s.n_socios, 0) AS n_socios,
       emp.razao_social,
       emp.capital_social,
       emp.porte
FROM etapa1_base b
JOIN empresas emp USING (cnpj_basico)
LEFT JOIN socios_por_empresa s USING (cnpj_basico)
WHERE b.n_cnaes_icp >= getvariable('min_cnaes_icp')
  AND (NOT getvariable('exigir_qsa') OR coalesce(s.n_socios, 0) > 0);

-- Etapa 3: nome com cara de clínica (fantasia ou razão social)
CREATE OR REPLACE TABLE etapa3_nome AS
SELECT *,
       upper(strip_accents(coalesce(razao_social, '') || ' ' || coalesce(nome_fantasia, ''))) AS nome_busca
FROM etapa2_multidisciplinar
WHERE regexp_matches(
        upper(strip_accents(coalesce(razao_social, '') || ' ' || coalesce(nome_fantasia, ''))),
        '\b(' || array_to_string(getvariable('palavras_nome'), '|') || ')');
