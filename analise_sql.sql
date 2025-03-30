--#1. Quantos chamados foram abertos no dia 01/04/2023?
--Resposta:
    --1903
--Query utilizada:
    SELECT COUNT(*) as total_chamados FROM `datario.adm_central_atendimento_1746.chamado` WHERE data_inicio BETWEEN '2023-04-01 00:00:00' AND '2023-04-01 23:59:59' ;

--#2.Qual o tipo de chamado que teve mais teve chamados abertos no dia 01/04/2023?
--Resposta: 
    --O tipo de chamado com mais incidencia
--Query utilizada:
    SELECT tipo, COUNT(*) as total_tipo_chamado FROM `datario.adm_central_atendimento_1746.chamado` 
    WHERE DATE(data_inicio) = '2023-04-01' 
    GROUP BY tipo 
    ORDER BY total_tipo_chamado DESC
    LIMIT 1;

--#3. Quais os nomes dos 3 bairros que mais tiveram chamados abertos nesse dia?
--Resposta: 
    --Campo Grande, Tijuca, Barra da Tijuca
--Query utilizada:
    SELECT bairro.nome, COUNT(*) AS bairros_chamados
    FROM `datario.adm_central_atendimento_1746.chamado` chamado
    JOIN `datario.dados_mestres.bairro` bairro
    ON chamado.id_bairro = bairro.id_bairro
    WHERE DATE(chamado.data_inicio) = '2023-04-01' 
    GROUP BY bairro.nome
    ORDER BY bairros_chamados DESC 
    LIMIT 3;
--#4. Qual o nome da subprefeitura com mais chamados abertos nesse dia?
--Resposta:
    --Subprefeitura da Zona Norte
--Query utilizaada:
    SELECT bairro.subprefeitura, COUNT(*) AS subprefeitura_chamados
    FROM `datario.adm_central_atendimento_1746.chamado` chamado
    JOIN `datario.dados_mestres.bairro` bairro
    ON chamado.id_bairro = bairro.id_bairro
    WHERE DATE(chamado.data_inicio) = '2023-04-01' 
    GROUP BY bairro.subprefeitura
    ORDER BY subprefeitura_chamados DESC 
    LIMIT 1;
--#5. Existe algum chamado aberto nesse dia que não foi associado a um bairro ou subprefeitura na tabela de bairros? Se sim, por que isso acontece?
    --Resposta:
        --Sim, é possivel encontrar no banco alguns chamados que não apresentam o campos preenchidos 
        -- possiveis causas:
        -- O dado pode ter sido registrado sem um bairro associado fazendo assim que não haja a associação com a subprefeitura
        -- Pode ocorrer erro de comunicação do sistema fazendo com que não ocorra a associação correta
    --Query utilizaada:
    SELECT bairro.subprefeitura, chamado.data_inicio 
    FROM `datario.adm_central_atendimento_1746.chamado` chamado
    LEFT JOIN `datario.dados_mestres.bairro` bairro
    ON chamado.id_bairro = bairro.id_bairro
    WHERE DATE(chamado.data_inicio) = '2023-04-01'
    AND (chamado.id_bairro IS NULL OR bairro.subprefeitura IS NULL);
--#6. Quantos chamados de Perturbação do sossego foram abertos nesse período?
    --Resposta:
        --56758
    --Query utilizada:
    SELECT COUNT(*) AS total_chamados
    FROM `datario.adm_central_atendimento_1746.chamado`
    WHERE data_inicio BETWEEN '2022-01-01' AND '2024-12-31'
    AND id_subtipo = '5071';
--#7. Selecione os chamados com esse subtipo que foram abertos durante os eventos contidos na tabela de eventos (Reveillon, Carnaval e Rock in Rio).
    --Resposta: 
        -- A resposta para essa pergunta contem 1345 linhas
    -- Query utilzida:
    SELECT chamado.*
    FROM `datario.adm_central_atendimento_1746.chamado` chamado 
    JOIN `datario.turismo_fluxo_visitantes.rede_hoteleira_ocupacao_eventos` evento
    ON DATE(chamado.data_inicio) BETWEEN evento.data_inicial AND evento.data_final
    WHERE chamado.id_subtipo = '5071'
    AND evento.evento IN ('Réveillon','Carnaval','Rock in Rio');
--#8. Quantos chamados desse subtipo foram abertos em cada evento?
    --Resposta:
        --1	Rock in Rio 946
        --2	Carnaval    252
        --3 Réveillon   147
    --Query utilizada:
        SELECT eventos.evento AS evento, COUNT(*) AS total_chamados
        FROM `datario.adm_central_atendimento_1746.chamado` chamado
        JOIN `datario.turismo_fluxo_visitantes.rede_hoteleira_ocupacao_eventos` eventos
        ON DATE(chamado.data_inicio) BETWEEN eventos.data_inicial AND eventos.data_final
        WHERE chamado.id_subtipo = '5071'
        AND eventos.evento IN ('Réveillon','Carnaval','Rock in Rio')
        GROUP BY eventos.evento
        ORDER BY total_chamados DESC;
--#9. Qual evento teve a maior média diária de chamados abertos desse subtipo?
    --Resposta:
        --Rock in Rio 94.6
    --Query utilizada:
        SELECT eventos.evento AS evento, COUNT(*)/(DATE_DIFF(MAX(eventos.data_final), MIN(eventos.data_inicial), DAY)+1) AS media_eventos
        FROM `datario.adm_central_atendimento_1746.chamado` chamado
        JOIN `datario.turismo_fluxo_visitantes.rede_hoteleira_ocupacao_eventos` eventos
        ON DATE(chamado.data_inicio) BETWEEN eventos.data_inicial AND eventos.data_final
        WHERE chamado.id_subtipo = '5071'
        AND eventos.evento IN ('Réveillon','Carnaval','Rock in Rio')
        GROUP BY eventos.evento
        ORDER BY media_eventos DESC
        LIMIT 1;
--#10. Compare as médias diárias de chamados abertos desse subtipo durante os eventos específicos (Reveillon, Carnaval e Rock in Rio) e a média diária de chamados abertos desse subtipo considerando todo o período de 01/01/2022 até 31/12/2024.
    --Resposta:
        --1	Rock in Rio 94.6
        --2 Media periodo determinado 77.750684931506854
        --3 Carnaval 63.0
        --4 Réveillon 49.0
    --Query utilizada:
    WITH media_eventos AS (
    SELECT eventos.evento AS evento, COUNT(*)/(DATE_DIFF(MAX(eventos.data_final), MIN(eventos.data_inicial), DAY)+1) AS media_chamados
    FROM `datario.adm_central_atendimento_1746.chamado` chamado
    JOIN `datario.turismo_fluxo_visitantes.rede_hoteleira_ocupacao_eventos` eventos
    ON DATE(chamado.data_inicio) BETWEEN eventos.data_inicial AND eventos.data_final
    WHERE chamado.id_subtipo = '5071'
        AND eventos.evento IN ('Réveillon','Carnaval','Rock in Rio')
    GROUP BY eventos.evento
    ),
    media_data AS (
    SELECT 'Media periodo determinado' AS evento,
    COUNT(*) /(DATE_DIFF('2023-12-31', '2022-01-01', DAY)+1) AS media_chamados
    FROM `datario.adm_central_atendimento_1746.chamado` chamado
    WHERE data_inicio BETWEEN '2022-01-01' AND '2024-12-31'
        AND chamado.id_subtipo = '5071'
        AND DATE(chamado.data_inicio) BETWEEN '2022-01-01' AND '2024-12-31'
    )
    SELECT evento,media_chamados
    FROM media_eventos
    UNION ALL
    SELECT evento,media_chamados 
    FROM media_data
    ORDER BY media_chamados DESC;