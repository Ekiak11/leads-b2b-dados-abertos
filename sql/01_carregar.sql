-- Etapa 0: carrega os arquivos de dados abertos do CNPJ (Receita Federal).
-- Layout oficial: sem cabeçalho, separador ';', texto entre aspas, codificação latin-1.
-- getvariable('pasta') é definido pelo pipeline.py a partir do config.toml.

CREATE OR REPLACE TABLE municipios AS
SELECT cd_municipio, nm_municipio
FROM read_csv(getvariable('pasta') || '/*MUNIC*', delim = ';', header = false, all_varchar = true,
              encoding = 'latin-1', names = ['cd_municipio', 'nm_municipio']);

-- Empresas e sócios ficam como VIEW: a base nacional é grande e só as linhas
-- que cruzam com os estabelecimentos filtrados chegam a ser lidas de fato.
CREATE OR REPLACE VIEW empresas AS
SELECT cnpj_basico, razao_social, natureza_juridica,
       TRY_CAST(replace(capital_social, ',', '.') AS DOUBLE) AS capital_social,
       porte
FROM read_csv(getvariable('pasta') || '/*EMPRE*', delim = ';', header = false, all_varchar = true,
              encoding = 'latin-1',
              names = ['cnpj_basico', 'razao_social', 'natureza_juridica', 'qualificacao_responsavel',
                       'capital_social', 'porte', 'ente_federativo']);

CREATE OR REPLACE TABLE estabelecimentos AS
SELECT cnpj_basico || cnpj_ordem || cnpj_dv AS cnpj,
       cnpj_basico, nome_fantasia,
       situacao_cadastral,                      -- 02 = ativa
       data_inicio_atividade, cnae_principal,
       cnaes_secundarios,                       -- lista separada por vírgula
       bairro, cep, uf, cd_municipio,
       ddd_1 || telefone_1 AS telefone_1,
       email
FROM read_csv(getvariable('pasta') || '/*ESTABELE*', delim = ';', header = false, all_varchar = true,
              encoding = 'latin-1',
              names = ['cnpj_basico', 'cnpj_ordem', 'cnpj_dv', 'matriz_filial', 'nome_fantasia',
                       'situacao_cadastral', 'data_situacao', 'motivo_situacao', 'cidade_exterior', 'pais',
                       'data_inicio_atividade', 'cnae_principal', 'cnaes_secundarios', 'tipo_logradouro',
                       'logradouro', 'numero', 'complemento', 'bairro', 'cep', 'uf', 'cd_municipio',
                       'ddd_1', 'telefone_1', 'ddd_2', 'telefone_2', 'ddd_fax', 'fax', 'email',
                       'situacao_especial', 'data_situacao_especial'])
-- já filtra na leitura: só ativas (02) da UF do ICP, para não carregar o país inteiro
WHERE situacao_cadastral = '02' AND uf = getvariable('uf');

-- Sócios: só a contagem por empresa. Nomes e documentos não saem desta etapa.
CREATE OR REPLACE VIEW socios_por_empresa AS
SELECT cnpj_basico, count(*) AS n_socios
FROM read_csv(getvariable('pasta') || '/*SOCIO*', delim = ';', header = false, all_varchar = true,
              encoding = 'latin-1',
              names = ['cnpj_basico', 'tipo_socio', 'nome_socio', 'documento_socio', 'qualificacao',
                       'data_entrada', 'pais', 'representante_legal', 'nome_representante',
                       'qualificacao_representante', 'faixa_etaria'])
GROUP BY 1;
