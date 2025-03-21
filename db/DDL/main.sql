-- Criação da tabela de usuários
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    senha VARCHAR(255) NOT NULL,
    nome VARCHAR(255) NOT NULL
);

-- Criação da tabela de roles (cargos)
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE
);

-- Populando a tabela de roles com os cargos definidos
INSERT INTO roles (role_name)
VALUES ('Redator'),
       ('Avaliador'),
       ('ADM'),
       ('Visualizador'),
       ('Moderador');

-- Tabela de associação entre usuários e cargos (relação muitos-para-muitos)
CREATE TABLE usuario_roles (
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (usuario_id, role_id)
);

-- Tabela de processos seletivos
CREATE TABLE processos_seletivos (
    id SERIAL PRIMARY KEY,
    -- Referência ao usuário responsável por atualizar o processo seletivo
    responsavel_id INTEGER REFERENCES usuarios(id)
    -- Outros atributos do processo seletivo podem ser adicionados aqui se necessário
);

-- Tabela para associar os 3 professores avaliadores a cada processo seletivo
CREATE TABLE processo_avaliadores (
    processo_id INTEGER NOT NULL REFERENCES processos_seletivos(id) ON DELETE CASCADE,
    avaliador_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    PRIMARY KEY (processo_id, avaliador_id)
);
-- OBS.: A aplicação (ou triggers) deverá garantir que haja exatamente 3 avaliadores por processo.

-- Criação de um tipo ENUM para status dos candidatos
CREATE TYPE candidate_status AS ENUM ('concorrendo', 'pendente', 'aprovado');

-- Tabela para candidatos vinculados aos processos seletivos com seu status
CREATE TABLE processo_candidatos (
    processo_id INTEGER NOT NULL REFERENCES processos_seletivos(id) ON DELETE CASCADE,
    candidato_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    status candidate_status NOT NULL,
    PRIMARY KEY (processo_id, candidato_id)
);

-- Tabela de notícias
CREATE TABLE noticias (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    -- Link para o processo seletivo relacionado à notícia
    processo_seletivo_id INTEGER REFERENCES processos_seletivos(id),
    -- Link do edital armazenado (storage)
    edital_storage_link TEXT,
    texto TEXT NOT NULL
);

-- Tabela de editais
CREATE TABLE editais (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    -- Caso o edital esteja vinculado a um processo seletivo, este campo referencia-o
    processo_seletivo_id INTEGER REFERENCES processos_seletivos(id),
    -- Link do edital armazenado (storage)
    edital_storage_link TEXT NOT NULL
);
