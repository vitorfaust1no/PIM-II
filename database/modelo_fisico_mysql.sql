-- =====================================================================
-- PIM II - Cardápio Digital Sabor & Cia Bistrô
-- Modelo físico (MySQL 8.0.16 ou superior; testado também em MariaDB)
-- =====================================================================
 
DROP DATABASE IF EXISTS sabor_cia;
CREATE DATABASE sabor_cia CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE sabor_cia;
 
-- ---------------------------------------------------------------------
-- 1. CRIAÇÃO DAS TABELAS (DDL)
-- ---------------------------------------------------------------------
 
CREATE TABLE filial (
    id_filial   INT AUTO_INCREMENT PRIMARY KEY,
    nome        VARCHAR(80)  NOT NULL,
    endereco    VARCHAR(150) NOT NULL,
    bairro      VARCHAR(60)  NOT NULL,
    url_qrcode  VARCHAR(255) NOT NULL UNIQUE
);
 
-- Administrador e Gerente ficam na mesma tabela (herança de tabela única).
-- Regra: gerente sempre tem filial; administrador (matriz) nunca tem.
CREATE TABLE usuario (
    id_usuario  INT AUTO_INCREMENT PRIMARY KEY,
    nome        VARCHAR(100) NOT NULL,
    email       VARCHAR(120) NOT NULL UNIQUE,
    senha_hash  CHAR(60)     NOT NULL,          -- RNF04: hash bcrypt, nunca a senha
    perfil      ENUM('ADMIN','GERENTE') NOT NULL,
    id_filial   INT NULL,
    CONSTRAINT fk_usuario_filial FOREIGN KEY (id_filial)
        REFERENCES filial (id_filial),
    CONSTRAINT ck_usuario_perfil CHECK (
        (perfil = 'ADMIN'   AND id_filial IS NULL) OR
        (perfil = 'GERENTE' AND id_filial IS NOT NULL)
    )
);
 
-- RF10: cada maquininha tem um token de API vinculado a uma filial.
-- A API usa esse vínculo para saber de qual unidade é o catálogo.
CREATE TABLE dispositivo (
    id_dispositivo INT AUTO_INCREMENT PRIMARY KEY,
    id_filial      INT NOT NULL,
    descricao      VARCHAR(60) NOT NULL,
    token_hash     CHAR(64) NOT NULL UNIQUE,     -- SHA-256 do token, nunca o token
    ativo          BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_dispositivo_filial FOREIGN KEY (id_filial)
        REFERENCES filial (id_filial)
);
 
CREATE TABLE categoria (
    id_categoria    INT AUTO_INCREMENT PRIMARY KEY,
    nome_pt         VARCHAR(60) NOT NULL UNIQUE,
    nome_en         VARCHAR(60) NOT NULL,
    ordem_exibicao  INT NOT NULL
);
 
CREATE TABLE produto (
    id_produto       INT AUTO_INCREMENT PRIMARY KEY,
    id_categoria     INT NOT NULL,
    nome_pt          VARCHAR(100) NOT NULL,
    nome_en          VARCHAR(100) NOT NULL,
    descricao_pt     TEXT,
    descricao_en     TEXT,
    ingredientes_pt  TEXT,   -- texto descritivo exibido ao cliente (não é consultado)
    ingredientes_en  TEXT,
    preco            DECIMAL(10,2) NOT NULL,
    url_foto         VARCHAR(255),
    CONSTRAINT fk_produto_categoria FOREIGN KEY (id_categoria)
        REFERENCES categoria (id_categoria),
    CONSTRAINT ck_produto_preco CHECK (preco > 0)
);
 
-- Nomes seguem a lista de alergênicos da Anvisa (ex.: "Leite", não "Lactose")
CREATE TABLE alergeno (
    id_alergeno  INT AUTO_INCREMENT PRIMARY KEY,
    nome_pt      VARCHAR(50) NOT NULL UNIQUE,
    nome_en      VARCHAR(50) NOT NULL
);
 
-- N:N produto x alérgeno
CREATE TABLE produto_alergeno (
    id_produto   INT NOT NULL,
    id_alergeno  INT NOT NULL,
    PRIMARY KEY (id_produto, id_alergeno),
    CONSTRAINT fk_pa_produto  FOREIGN KEY (id_produto)
        REFERENCES produto (id_produto) ON DELETE CASCADE,
    CONSTRAINT fk_pa_alergeno FOREIGN KEY (id_alergeno)
        REFERENCES alergeno (id_alergeno)
);
 
-- N:N auto-relacionamento: prato harmoniza com vinho
CREATE TABLE harmonizacao (
    id_prato  INT NOT NULL,
    id_vinho  INT NOT NULL,
    PRIMARY KEY (id_prato, id_vinho),
    CONSTRAINT fk_harm_prato FOREIGN KEY (id_prato)
        REFERENCES produto (id_produto) ON DELETE CASCADE,
    CONSTRAINT fk_harm_vinho FOREIGN KEY (id_vinho)
        REFERENCES produto (id_produto) ON DELETE CASCADE,
    CONSTRAINT ck_harm_diferente CHECK (id_prato <> id_vinho)
);
 
-- N:N produto x filial com atributos: coração do sistema
CREATE TABLE disponibilidade (
    id_produto     INT NOT NULL,
    id_filial      INT NOT NULL,
    ativo          BOOLEAN  NOT NULL DEFAULT TRUE,
    atualizado_em  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                   ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id_produto, id_filial),
    CONSTRAINT fk_disp_produto FOREIGN KEY (id_produto)
        REFERENCES produto (id_produto) ON DELETE CASCADE,
    CONSTRAINT fk_disp_filial  FOREIGN KEY (id_filial)
        REFERENCES filial (id_filial) ON DELETE CASCADE
);
 
-- RF11: histórico de alterações de disponibilidade.
-- Sem ON DELETE CASCADE: o histórico precisa sobreviver ao produto.
CREATE TABLE historico_disponibilidade (
    id_historico  BIGINT AUTO_INCREMENT PRIMARY KEY,
    id_produto    INT NOT NULL,
    id_filial     INT NOT NULL,
    id_usuario    INT NOT NULL,
    acao          ENUM('ATIVAR','DESATIVAR') NOT NULL,
    data_hora     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_hist_produto FOREIGN KEY (id_produto) REFERENCES produto (id_produto),
    CONSTRAINT fk_hist_filial  FOREIGN KEY (id_filial)  REFERENCES filial (id_filial),
    CONSTRAINT fk_hist_usuario FOREIGN KEY (id_usuario) REFERENCES usuario (id_usuario)
);

-- Caixa de saída da replicação para o MongoDB (seção 5.4): cada evento do
-- histórico ainda não copiado. A linha nasce pelo trigger
-- trg_historico_pendente, na MESMA transação do evento, e é apagada pelo
-- serviço de replicação (previsto para produção) depois que o MongoDB
-- confirma a gravação. Não há "ponto de controle": um evento confirmado
-- fora da ordem dos ids continua pendente até ser copiado.
CREATE TABLE replicacao_pendente (
    id_historico  BIGINT PRIMARY KEY,
    criado_em     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_pend_historico FOREIGN KEY (id_historico)
        REFERENCES historico_disponibilidade (id_historico)
);
 
-- Índices para as consultas mais frequentes
CREATE INDEX idx_disp_filial_ativo ON disponibilidade (id_filial, ativo);
CREATE INDEX idx_hist_filial_data  ON historico_disponibilidade (id_filial, data_hora);
 
-- Regra de negócio que um CHECK não alcança (depende de outra tabela):
-- em harmonizacao, id_vinho precisa ser da categoria "Vinhos" e id_prato não.
-- A regra vale na inclusão e na alteração, por isso há dois triggers.
DELIMITER //
CREATE TRIGGER trg_harmonizacao_valida_ins
BEFORE INSERT ON harmonizacao
FOR EACH ROW
BEGIN
    IF (SELECT c.nome_pt FROM produto p JOIN categoria c ON c.id_categoria = p.id_categoria
        WHERE p.id_produto = NEW.id_vinho) <> 'Vinhos'
       OR (SELECT c.nome_pt FROM produto p JOIN categoria c ON c.id_categoria = p.id_categoria
           WHERE p.id_produto = NEW.id_prato) = 'Vinhos' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Harmonizacao deve ligar um prato a um vinho';
    END IF;
END //
 
CREATE TRIGGER trg_harmonizacao_valida_upd
BEFORE UPDATE ON harmonizacao
FOR EACH ROW
BEGIN
    IF (SELECT c.nome_pt FROM produto p JOIN categoria c ON c.id_categoria = p.id_categoria
        WHERE p.id_produto = NEW.id_vinho) <> 'Vinhos'
       OR (SELECT c.nome_pt FROM produto p JOIN categoria c ON c.id_categoria = p.id_categoria
           WHERE p.id_produto = NEW.id_prato) = 'Vinhos' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Harmonizacao deve ligar um prato a um vinho';
    END IF;
END //
 
-- Todo evento do histórico entra na caixa de saída. O trigger faz parte da
-- transação do INSERT: se ela for desfeita (ROLLBACK), a pendência também é.
CREATE TRIGGER trg_historico_pendente
AFTER INSERT ON historico_disponibilidade
FOR EACH ROW
BEGIN
    INSERT INTO replicacao_pendente (id_historico) VALUES (NEW.id_historico);
END //
DELIMITER ;
 
-- ---------------------------------------------------------------------
-- 2. CARGA DE EXEMPLO (DML)
-- ---------------------------------------------------------------------
 
INSERT INTO filial (nome, endereco, bairro, url_qrcode) VALUES
('Sabor & Cia Bistrô Jardins',   'Rua Exemplo, 100', 'Jardins',
    'https://cardapio.saborecia.com.br/f/1'),
('Sabor & Cia Bistrô Itaim',     'Rua Exemplo, 200', 'Itaim Bibi',
    'https://cardapio.saborecia.com.br/f/2'),
('Sabor & Cia Bistrô Pinheiros', 'Rua Exemplo, 300', 'Pinheiros',
    'https://cardapio.saborecia.com.br/f/3');
 
INSERT INTO usuario (nome, email, perfil, id_filial, senha_hash) VALUES
('Ana Matriz',    'ana@saborecia.com.br',   'ADMIN',   NULL,
    '$2b$12$abcdefghijklmnopqrstuuABCDEFGHIJKLMNOPQRSTUVWXYZ01234'),
('Bruno Jardins', 'bruno@saborecia.com.br', 'GERENTE', 1,
    '$2b$12$abcdefghijklmnopqrstuuABCDEFGHIJKLMNOPQRSTUVWXYZ01235'),
('Carla Itaim',   'carla@saborecia.com.br', 'GERENTE', 2,
    '$2b$12$abcdefghijklmnopqrstuuABCDEFGHIJKLMNOPQRSTUVWXYZ01236');
 
-- Tokens de exemplo (valores de SHA-256 fictícios)
INSERT INTO dispositivo (id_filial, descricao, token_hash) VALUES
(1, 'Maquininha salão 01', SHA2('token-exemplo-jardins-01', 256)),
(2, 'Maquininha salão 01', SHA2('token-exemplo-itaim-01', 256));
 
INSERT INTO categoria (nome_pt, nome_en, ordem_exibicao) VALUES
('Entradas', 'Starters', 1),
('Pratos principais', 'Main courses', 2),
('Sobremesas', 'Desserts', 3),
('Vinhos', 'Wines', 4);
 
INSERT INTO produto (id_categoria, nome_pt, nome_en,
                     ingredientes_pt, ingredientes_en, preco) VALUES
(1, 'Burrata com tomates confitados', 'Burrata with confit tomatoes',
    'burrata, tomate, manjericão, azeite', 'burrata, tomato, basil, olive oil', 68.00),
(2, 'Risoto de cogumelos', 'Mushroom risotto',
    'arroz arbóreo, cogumelos, parmesão, manteiga',
    'arborio rice, mushrooms, parmesan, butter', 98.00),
(2, 'Salmão em crosta de castanhas', 'Nut-crusted salmon',
    'salmão, castanha-de-caju, purê de mandioquinha',
    'salmon, cashew nuts, arracacha purée', 112.00),
(3, 'Petit gâteau', 'Petit gâteau',
    'chocolate, ovos, farinha de trigo, sorvete',
    'chocolate, eggs, wheat flour, ice cream', 42.00),
(4, 'Chardonnay (taça)', 'Chardonnay (glass)', NULL, NULL, 45.00);
 
INSERT INTO alergeno (nome_pt, nome_en) VALUES
('Leite', 'Milk'), ('Trigo', 'Wheat'), ('Castanha-de-caju', 'Cashew'),
('Ovos', 'Eggs'), ('Peixe', 'Fish');
 
INSERT INTO produto_alergeno (id_produto, id_alergeno) VALUES
(1,1), (2,1), (3,3), (3,5), (4,1), (4,2), (4,4);
 
INSERT INTO harmonizacao (id_prato, id_vinho) VALUES (2,5), (3,5);
 
-- Todo produto começa disponível em todas as filiais
INSERT INTO disponibilidade (id_produto, id_filial)
SELECT p.id_produto, f.id_filial FROM produto p CROSS JOIN filial f;
 
-- ---------------------------------------------------------------------
-- 3. PRINCIPAIS COMANDOS DO SISTEMA
-- ---------------------------------------------------------------------
 
-- RF06 + RF11: o gerente Bruno (id_usuario 2, filial 1) desativa o risoto.
-- A filial vem do cadastro do usuário, não de um campo digitado. Atenção:
-- quem garante que @usuario é o gerente autenticado é a API (pelo login);
-- o banco apenas aplica a filial desse usuário. Se @usuario for um ADMIN
-- (sem filial), nenhuma linha é alterada.
-- O valor é explícito (FALSE), então repetir o comando não desfaz nada.
SET @usuario = 2, @produto = 2;
START TRANSACTION;
UPDATE disponibilidade d
JOIN usuario u ON u.id_usuario = @usuario AND u.perfil = 'GERENTE'
SET d.ativo = FALSE
WHERE d.id_produto = @produto
  AND d.id_filial = u.id_filial
  AND d.ativo = TRUE;             -- só registra se o estado realmente mudar
SET @alterou = ROW_COUNT();     -- lido logo após o UPDATE
INSERT INTO historico_disponibilidade (id_produto, id_filial, id_usuario, acao)
SELECT @produto, u.id_filial, u.id_usuario, 'DESATIVAR'
FROM usuario u
WHERE u.id_usuario = @usuario AND @alterou > 0;
COMMIT;
 
-- Mais alguns eventos de exemplo para o relatório de frequência (RF12)
INSERT INTO historico_disponibilidade
    (id_produto, id_filial, id_usuario, acao, data_hora) VALUES
(3, 2, 3, 'DESATIVAR', '2026-09-20 20:15:00'),
(3, 2, 3, 'ATIVAR',    '2026-09-21 11:00:00'),
(3, 2, 3, 'DESATIVAR', '2026-09-26 21:05:00'),
(3, 2, 3, 'ATIVAR',    '2026-09-27 11:00:00'),
(2, 1, 2, 'DESATIVAR', '2026-09-22 13:40:00'),
(2, 1, 2, 'ATIVAR',    '2026-09-23 11:00:00');
 
-- RF07 / RF10: cardápio disponível da filial 1 (cliente e maquininha)
SELECT c.nome_pt AS categoria, p.nome_pt AS produto, p.preco
FROM disponibilidade d
JOIN produto   p ON p.id_produto   = d.id_produto
JOIN categoria c ON c.id_categoria = p.id_categoria
WHERE d.id_filial = 1 AND d.ativo = TRUE
ORDER BY c.ordem_exibicao, p.nome_pt;
 
-- RF10: a maquininha se identifica pelo token; a filial vem do dispositivo
SELECT p.id_produto, p.nome_pt, p.preco
FROM dispositivo disp
JOIN disponibilidade d ON d.id_filial = disp.id_filial AND d.ativo = TRUE
JOIN produto p ON p.id_produto = d.id_produto
WHERE disp.token_hash = SHA2('token-exemplo-jardins-01', 256) AND disp.ativo = TRUE;
 
-- RF09: cardápio da filial 1 sem leite (para quem tem alergia ao leite)
SELECT p.nome_pt, p.preco
FROM disponibilidade d
JOIN produto p ON p.id_produto = d.id_produto
WHERE d.id_filial = 1 AND d.ativo = TRUE
  AND NOT EXISTS (
      SELECT 1 FROM produto_alergeno pa
      JOIN alergeno a ON a.id_alergeno = pa.id_alergeno
      WHERE pa.id_produto = p.id_produto AND a.nome_pt = 'Leite'
  );
 
-- Harmonizações sugeridas
SELECT prato.nome_pt AS prato, vinho.nome_pt AS vinho_sugerido
FROM harmonizacao h
JOIN produto prato ON prato.id_produto = h.id_prato
JOIN produto vinho ON vinho.id_produto = h.id_vinho;
 
-- RF12: itens indisponíveis agora, por filial (inclui filiais com zero)
SELECT f.nome, COALESCE(SUM(d.ativo = FALSE), 0) AS itens_indisponiveis
FROM filial f
LEFT JOIN disponibilidade d ON d.id_filial = f.id_filial
GROUP BY f.id_filial, f.nome
ORDER BY f.id_filial;
 
-- RF12: quantas vezes cada produto esgotou em cada filial nos últimos 30 dias
SELECT f.nome AS filial, p.nome_pt AS produto, COUNT(*) AS vezes_esgotado
FROM historico_disponibilidade h
JOIN filial  f ON f.id_filial  = h.id_filial
JOIN produto p ON p.id_produto = h.id_produto
WHERE h.acao = 'DESATIVAR'
  AND h.data_hora >= NOW() - INTERVAL 30 DAY
GROUP BY f.nome, p.nome_pt
ORDER BY vezes_esgotado DESC, f.nome;
