-- ============================================================
-- Easy Social - Schema PostgreSQL
-- Developed By Xandao
-- Banco: easy_social_db
-- ============================================================

-- Tabela de controle de uploads
CREATE TABLE IF NOT EXISTS uploads (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(500) NOT NULL,
    original_name VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pendente',
    sheets_processed INTEGER DEFAULT 0
);

-- ============================================================
-- 1. ANALISE NATUREZA
-- Referência de colunas: A, B, C, D, E, F...
-- ============================================================
CREATE TABLE IF NOT EXISTS analise_natureza (
    id SERIAL PRIMARY KEY,
    upload_id INTEGER REFERENCES uploads(id) ON DELETE CASCADE,
    row_number INTEGER,
    col_a TEXT,
    col_b TEXT,
    col_c TEXT,
    col_d TEXT,
    col_e TEXT,
    col_f TEXT,
    col_g TEXT,
    col_h TEXT,
    col_i TEXT,
    col_j TEXT,
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 2. Dinamica
-- ============================================================
CREATE TABLE IF NOT EXISTS dinamica (
    id SERIAL PRIMARY KEY,
    upload_id INTEGER REFERENCES uploads(id) ON DELETE CASCADE,
    row_number INTEGER,
    col_a TEXT,
    col_b TEXT,
    col_c TEXT,
    col_d TEXT,
    col_e TEXT,
    col_f TEXT,
    col_g TEXT,
    col_h TEXT,
    col_i TEXT,
    col_j TEXT,
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 3. Base Ficha Financeira 2025
-- ============================================================
CREATE TABLE IF NOT EXISTS base_ficha_financeira (
    id SERIAL PRIMARY KEY,
    upload_id INTEGER REFERENCES uploads(id) ON DELETE CASCADE,
    row_number INTEGER,
    col_a TEXT,
    col_b TEXT,
    col_c TEXT,
    col_d TEXT,
    col_e TEXT,
    col_f TEXT,
    col_g TEXT,
    col_h TEXT,
    col_i TEXT,
    col_j TEXT,
    col_k TEXT,
    col_l TEXT,
    col_m TEXT,
    col_n TEXT,
    col_o TEXT,
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 4. Planilha 1
-- ============================================================
CREATE TABLE IF NOT EXISTS planilha_1 (
    id SERIAL PRIMARY KEY,
    upload_id INTEGER REFERENCES uploads(id) ON DELETE CASCADE,
    row_number INTEGER,
    col_a TEXT,
    col_b TEXT,
    col_c TEXT,
    col_d TEXT,
    col_e TEXT,
    col_f TEXT,
    col_g TEXT,
    col_h TEXT,
    col_i TEXT,
    col_j TEXT,
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 5. Tabela Eventos Gl
-- Colunas observadas: código, código_aux, descrição, vencimento_valor, tipo, categoria
-- ============================================================
CREATE TABLE IF NOT EXISTS tabela_eventos_gl (
    id SERIAL PRIMARY KEY,
    upload_id INTEGER REFERENCES uploads(id) ON DELETE CASCADE,
    row_number INTEGER,
    col_a TEXT,  -- código (ex: 0042)
    col_b TEXT,  -- código auxiliar (ex: 00)
    col_c TEXT,  -- descrição (ex: DIF. DISSIDIO - 04/2010)
    col_d TEXT,  -- vencimento/valor
    col_e TEXT,  -- tipo (ex: Normal)
    col_f TEXT,  -- categoria (ex: Salário)
    col_g TEXT,
    col_h TEXT,
    col_i TEXT,
    col_j TEXT,
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 6. Tabela EB
-- ============================================================
CREATE TABLE IF NOT EXISTS tabela_eb (
    id SERIAL PRIMARY KEY,
    upload_id INTEGER REFERENCES uploads(id) ON DELETE CASCADE,
    row_number INTEGER,
    col_a TEXT,
    col_b TEXT,
    col_c TEXT,
    col_d TEXT,
    col_e TEXT,
    col_f TEXT,
    col_g TEXT,
    col_h TEXT,
    col_i TEXT,
    col_j TEXT,
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Índices
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_analise_natureza_upload ON analise_natureza(upload_id);
CREATE INDEX IF NOT EXISTS idx_dinamica_upload ON dinamica(upload_id);
CREATE INDEX IF NOT EXISTS idx_base_ficha_upload ON base_ficha_financeira(upload_id);
CREATE INDEX IF NOT EXISTS idx_planilha1_upload ON planilha_1(upload_id);
CREATE INDEX IF NOT EXISTS idx_eventos_gl_upload ON tabela_eventos_gl(upload_id);
CREATE INDEX IF NOT EXISTS idx_tabela_eb_upload ON tabela_eb(upload_id);
