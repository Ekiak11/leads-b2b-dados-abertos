-- Pontuação do modo TEA e lista final por estado.

CREATE OR REPLACE TABLE pontuados AS
SELECT p.*,
       coalesce(s.n_socios, 0) AS n_socios,
       array_to_string(list_transform(list_sort(cnaes_terapia_empresa), lambda c:
           CASE c WHEN '8650003' THEN 'psicologia' WHEN '8650004' THEN 'fisioterapia'
                  WHEN '8650005' THEN 'terapia ocupacional' WHEN '8650006' THEN 'fonoaudiologia' END), ', ') AS terapias,
         CASE WHEN perfil LIKE 'A%' THEN getvariable('pontos_perfil_a') ELSE getvariable('pontos_perfil_b') END
       + len(cnaes_terapia_empresa) * getvariable('pontos_por_terapia')
       + CASE WHEN list_contains(cnaes, '8650005') AND list_contains(cnaes, '8650006')
              THEN getvariable('pontos_to_e_fono') ELSE 0 END
       + least(coalesce(s.n_socios, 0), getvariable('max_pontos_socios'))
       + CASE WHEN capital_social >= getvariable('capital_minimo') THEN getvariable('pontos_capital') ELSE 0 END
         AS pontuacao
FROM tea3_perfil p
LEFT JOIN socios_por_empresa s USING (cnpj_basico);

CREATE OR REPLACE TABLE lista_priorizada AS
WITH r AS (
    SELECT *,
           row_number() OVER (PARTITION BY uf
                              ORDER BY pontuacao DESC, capital_social DESC NULLS LAST, data_inicio_atividade) AS posicao_uf
    FROM pontuados
)
SELECT * FROM r
WHERE getvariable('top_por_uf') = 0 OR posicao_uf <= getvariable('top_por_uf');

CREATE OR REPLACE TABLE funil AS
SELECT 1 AS etapa, 'Ativas com CNAE de terapia' AS descricao, count(*) AS empresas FROM tea1_base
UNION ALL SELECT 2, 'Sem órgãos públicos, SCP, empresário individual e nomes fora do perfil', count(*) FROM tea2_elegiveis
UNION ALL SELECT 3, 'Perfil A (TEA no nome) ou B (infantil com TO/fono)', count(*) FROM tea3_perfil
UNION ALL SELECT 4, 'Lista final', count(*) FROM lista_priorizada
ORDER BY etapa;
