-- Etapa 4: pontuação de prioridade (lead scoring) e lista final por região.

CREATE OR REPLACE TABLE pontuados AS
SELECT *,
         n_cnaes_icp * getvariable('peso_por_cnae_icp')
       + least(n_socios, getvariable('max_pontos_socios'))
       + CASE WHEN regexp_matches(nome_busca, '(' || array_to_string(getvariable('palavras_nicho'), '|') || ')')
              THEN getvariable('pontos_nicho') ELSE 0 END
       + CASE WHEN regexp_matches(nome_busca, '(' || array_to_string(getvariable('palavras_multi'), '|') || ')')
              THEN getvariable('pontos_multi') ELSE 0 END
       + CASE WHEN capital_social >= getvariable('capital_minimo')
              THEN getvariable('pontos_capital') ELSE 0 END
         AS pontuacao
FROM etapa3_nome;

-- Lista final: os melhores do município sede + os melhores dos demais
CREATE OR REPLACE TABLE lista_priorizada AS
WITH r AS (
    SELECT *,
           CASE WHEN nm_municipio = getvariable('municipios')[1] THEN 'sede' ELSE 'demais' END AS grupo,
           row_number() OVER (
               PARTITION BY CASE WHEN nm_municipio = getvariable('municipios')[1] THEN 'sede' ELSE 'demais' END
               ORDER BY pontuacao DESC, capital_social DESC NULLS LAST, data_inicio_atividade) AS posicao
    FROM pontuados
)
SELECT *
FROM r
WHERE (grupo = 'sede'   AND posicao <= getvariable('top_capital'))
   OR (grupo = 'demais' AND posicao <= getvariable('top_demais'));

-- Resumo do funil (quantas empresas sobram em cada etapa)
CREATE OR REPLACE TABLE funil AS
SELECT 1 AS etapa, 'Ativas, nos municípios-alvo, com CNAE do ICP' AS descricao, count(*) AS empresas FROM etapa1_base
UNION ALL SELECT 2, 'Multidisciplinares e com sócios cadastrados', count(*) FROM etapa2_multidisciplinar
UNION ALL SELECT 3, 'Com nome de clínica', count(*) FROM etapa3_nome
UNION ALL SELECT 4, 'Lista priorizada (top por região)', count(*) FROM lista_priorizada
ORDER BY etapa;
