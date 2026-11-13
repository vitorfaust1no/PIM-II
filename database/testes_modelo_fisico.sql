-- =====================================================================
-- PIM II - Sabor & Cia Bistrô
-- Testes do modelo físico (executar DEPOIS de modelo_fisico_mysql.sql)
--
-- Cada teste começa com um comentário que o identifica (STnn). Os testes
-- negativos DEVEM terminar em erro: o cliente mysql precisa ser executado
-- com --force para seguir adiante após cada erro esperado.
-- Uso automatizado: python tests/executar_testes_sql.py (MySQL 8.0 em Docker).
-- =====================================================================

USE sabor_cia;

-- ST01 - Estrutura criada (tabelas e triggers)
SELECT COUNT(*) AS tabelas FROM information_schema.tables
 WHERE table_schema = 'sabor_cia';
SELECT trigger_name, event_manipulation AS evento, event_object_table AS tabela
  FROM information_schema.triggers WHERE trigger_schema = 'sabor_cia'
 ORDER BY trigger_name;

-- ST02 - Carga de exemplo
SELECT (SELECT COUNT(*) FROM filial)           AS filiais,
       (SELECT COUNT(*) FROM usuario)          AS usuarios,
       (SELECT COUNT(*) FROM produto)          AS produtos,
       (SELECT COUNT(*) FROM produto_alergeno) AS prod_alergenos,
       (SELECT COUNT(*) FROM disponibilidade)  AS disponibilidades;

-- ST03 - Transacao RF06/RF11: risoto inativo na filial 1
SELECT d.id_filial, p.nome_pt, d.ativo
  FROM disponibilidade d JOIN produto p ON p.id_produto = d.id_produto
 WHERE d.id_produto = 2 ORDER BY d.id_filial;
SELECT id_produto, id_filial, id_usuario, acao
  FROM historico_disponibilidade
 WHERE id_produto = 2 AND data_hora >= NOW() - INTERVAL 1 HOUR;

-- ST04 - Repetir a desativacao nao gera novo historico
SET @usuario = 2, @produto = 2;
SELECT COUNT(*) INTO @antes FROM historico_disponibilidade;
START TRANSACTION;
UPDATE disponibilidade d
JOIN usuario u ON u.id_usuario = @usuario AND u.perfil = 'GERENTE'
SET d.ativo = FALSE
WHERE d.id_produto = @produto AND d.id_filial = u.id_filial AND d.ativo = TRUE;
SET @alterou = ROW_COUNT();
INSERT INTO historico_disponibilidade (id_produto, id_filial, id_usuario, acao)
SELECT @produto, u.id_filial, u.id_usuario, 'DESATIVAR'
FROM usuario u WHERE u.id_usuario = @usuario AND @alterou > 0;
COMMIT;
SELECT @alterou AS linhas_alteradas,
       (SELECT COUNT(*) FROM historico_disponibilidade) - @antes AS novos_eventos;

-- ST05 - ROLLBACK desfaz a alteracao
START TRANSACTION;
UPDATE disponibilidade SET ativo = FALSE WHERE id_produto = 1 AND id_filial = 2;
SELECT ativo AS dentro_da_transacao FROM disponibilidade
 WHERE id_produto = 1 AND id_filial = 2;
ROLLBACK;
SELECT ativo AS apos_rollback FROM disponibilidade
 WHERE id_produto = 1 AND id_filial = 2;

-- ST06 - CHECK: preco deve ser maior que zero (deve falhar)
INSERT INTO produto (id_categoria, nome_pt, nome_en, preco)
VALUES (1, 'Pao de queijo', 'Cheese bread', 0);

-- ST07 - CHECK: gerente sem filial e admin com filial (devem falhar)
INSERT INTO usuario (nome, email, senha_hash, perfil, id_filial)
VALUES ('Teste', 'teste1@saborecia.com.br', REPEAT('x', 60), 'GERENTE', NULL);
INSERT INTO usuario (nome, email, senha_hash, perfil, id_filial)
VALUES ('Teste', 'teste2@saborecia.com.br', REPEAT('x', 60), 'ADMIN', 1);

-- ST08 - Trigger: harmonizacao exige prato + vinho (devem falhar)
INSERT INTO harmonizacao (id_prato, id_vinho) VALUES (1, 2);
UPDATE harmonizacao SET id_vinho = 3 WHERE id_prato = 2 AND id_vinho = 5;

-- ST09 - FK: disponibilidade de produto inexistente (deve falhar)
INSERT INTO disponibilidade (id_produto, id_filial) VALUES (99, 1);

-- ST10 - UNIQUE: e-mail de usuario repetido (deve falhar)
INSERT INTO usuario (nome, email, senha_hash, perfil, id_filial)
VALUES ('Outro Bruno', 'bruno@saborecia.com.br', REPEAT('x', 60), 'GERENTE', 1);

-- ST11 - Historico preservado: produto com historico nao e apagado (deve falhar)
DELETE FROM produto WHERE id_produto = 2;

-- ST12 - Nenhum teste negativo alterou os dados
SELECT (SELECT COUNT(*) FROM produto)      AS produtos,
       (SELECT COUNT(*) FROM usuario)      AS usuarios,
       (SELECT COUNT(*) FROM harmonizacao) AS harmonizacoes,
       (SELECT COUNT(*) FROM disponibilidade) AS disponibilidades;

-- ST13 - Caixa de saida da replicacao (trigger trg_historico_pendente)
-- (a) todo evento do historico tem pendencia de replicacao
SELECT (SELECT COUNT(*) FROM historico_disponibilidade) AS eventos,
       (SELECT COUNT(*) FROM replicacao_pendente)       AS pendentes;
-- (b) e (c) usam a transacao RF06/RF11 completa (como no ST04): o gerente 2
-- (filial 1) desativa o produto 1, e o evento so existe se o estado mudou.
SET @usuario = 2, @produto = 1;
-- (b) transacao desfeita por ROLLBACK nao deixa evento nem pendencia
SELECT COUNT(*) INTO @pend_antes FROM replicacao_pendente;
START TRANSACTION;
UPDATE disponibilidade d
JOIN usuario u ON u.id_usuario = @usuario AND u.perfil = 'GERENTE'
SET d.ativo = FALSE
WHERE d.id_produto = @produto AND d.id_filial = u.id_filial AND d.ativo = TRUE;
SET @alterou = ROW_COUNT();
INSERT INTO historico_disponibilidade (id_produto, id_filial, id_usuario, acao)
SELECT @produto, u.id_filial, u.id_usuario, 'DESATIVAR'
FROM usuario u WHERE u.id_usuario = @usuario AND @alterou > 0;
-- dentro da transacao o evento e a pendencia existem (senao o teste seria vazio)
SELECT @alterou AS dentro_linhas_alteradas,
       (SELECT COUNT(*) FROM replicacao_pendente) - @pend_antes AS dentro_pendencias;
ROLLBACK;
SELECT (SELECT COUNT(*) FROM replicacao_pendente) - @pend_antes AS pendencias_apos_rollback,
       (SELECT ativo FROM disponibilidade WHERE id_produto = 1 AND id_filial = 1) AS ativo_apos_rollback;
-- (c) transacao confirmada: o produto e desativado e o evento gera pendencia com o mesmo id
START TRANSACTION;
UPDATE disponibilidade d
JOIN usuario u ON u.id_usuario = @usuario AND u.perfil = 'GERENTE'
SET d.ativo = FALSE
WHERE d.id_produto = @produto AND d.id_filial = u.id_filial AND d.ativo = TRUE;
SET @alterou = ROW_COUNT();
INSERT INTO historico_disponibilidade (id_produto, id_filial, id_usuario, acao)
SELECT @produto, u.id_filial, u.id_usuario, 'DESATIVAR'
FROM usuario u WHERE u.id_usuario = @usuario AND @alterou > 0;
-- o INSERT so ocorre se @alterou > 0; sem ele, LAST_INSERT_ID() guardaria o id de
-- um INSERT anterior e a conferencia abaixo daria falso positivo: usa NULL
SET @novo = IF(@alterou > 0, LAST_INSERT_ID(), NULL);
COMMIT;
SELECT @alterou AS linhas_alteradas,
       (SELECT COUNT(*) FROM replicacao_pendente WHERE id_historico = @novo) AS pendencia_do_novo_evento;
