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
    col_a TEXT, col_b TEXT, col_c TEXT, col_d TEXT, col_e TEXT,
    col_f TEXT, col_g TEXT, col_h TEXT, col_i TEXT, col_j TEXT,
    col_k TEXT, col_l TEXT, col_m TEXT, col_n TEXT, col_o TEXT,
    col_p TEXT, col_q TEXT, col_r TEXT, col_s TEXT, col_t TEXT,
    col_u TEXT, col_v TEXT, col_w TEXT, col_x TEXT, col_y TEXT, col_z TEXT,
    col_aa TEXT, col_ab TEXT, col_ac TEXT, col_ad TEXT, col_ae TEXT,
    col_af TEXT, col_ag TEXT, col_ah TEXT, col_ai TEXT, col_aj TEXT,
    col_ak TEXT, col_al TEXT, col_am TEXT, col_an TEXT, col_ao TEXT,
    col_ap TEXT, col_aq TEXT, col_ar TEXT, col_as TEXT, col_at TEXT,
    col_au TEXT, col_av TEXT, col_aw TEXT, col_ax TEXT, col_ay TEXT, col_az TEXT,
    col_ba TEXT, col_bb TEXT,
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 1b. ANALISE NATUREZA CERTO (cópia corrigida)
-- Criada como cópia de analise_natureza, alterações aplicadas aqui
-- ============================================================
CREATE TABLE IF NOT EXISTS analise_natureza_certo (
    id SERIAL PRIMARY KEY,
    upload_id INTEGER REFERENCES uploads(id) ON DELETE CASCADE,
    row_number INTEGER,
    col_a TEXT, col_b TEXT, col_c TEXT, col_d TEXT, col_e TEXT,
    col_f TEXT, col_g TEXT, col_h TEXT, col_i TEXT, col_j TEXT,
    col_k TEXT, col_l TEXT, col_m TEXT, col_n TEXT, col_o TEXT,
    col_p TEXT, col_q TEXT, col_r TEXT, col_s TEXT, col_t TEXT,
    col_u TEXT, col_v TEXT, col_w TEXT, col_x TEXT, col_y TEXT, col_z TEXT,
    col_aa TEXT, col_ab TEXT, col_ac TEXT, col_ad TEXT, col_ae TEXT,
    col_af TEXT, col_ag TEXT, col_ah TEXT, col_ai TEXT, col_aj TEXT,
    col_ak TEXT, col_al TEXT, col_am TEXT, col_an TEXT, col_ao TEXT,
    col_ap TEXT, col_aq TEXT, col_ar TEXT, col_as TEXT, col_at TEXT,
    col_au TEXT, col_av TEXT, col_aw TEXT, col_ax TEXT, col_ay TEXT, col_az TEXT,
    col_ba TEXT, col_bb TEXT,
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    natureza_anterior TEXT,
    natureza_nova TEXT,
    usuario_correcao VARCHAR(255),
    data_correcao TIMESTAMP
);

-- ============================================================
-- 2. Dinamica
-- ============================================================
CREATE TABLE IF NOT EXISTS dinamica (
    id SERIAL PRIMARY KEY,
    upload_id INTEGER REFERENCES uploads(id) ON DELETE CASCADE,
    row_number INTEGER,
    col_a TEXT, col_b TEXT, col_c TEXT, col_d TEXT, col_e TEXT,
    col_f TEXT, col_g TEXT, col_h TEXT, col_i TEXT, col_j TEXT,
    col_k TEXT, col_l TEXT, col_m TEXT, col_n TEXT, col_o TEXT,
    col_p TEXT, col_q TEXT, col_r TEXT, col_s TEXT, col_t TEXT,
    col_u TEXT, col_v TEXT, col_w TEXT, col_x TEXT, col_y TEXT, col_z TEXT,
    col_aa TEXT, col_ab TEXT, col_ac TEXT, col_ad TEXT, col_ae TEXT,
    col_af TEXT, col_ag TEXT, col_ah TEXT, col_ai TEXT, col_aj TEXT,
    col_ak TEXT, col_al TEXT, col_am TEXT, col_an TEXT, col_ao TEXT,
    col_ap TEXT, col_aq TEXT, col_ar TEXT, col_as TEXT, col_at TEXT,
    col_au TEXT, col_av TEXT, col_aw TEXT, col_ax TEXT, col_ay TEXT, col_az TEXT,
    col_ba TEXT, col_bb TEXT,
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
    col_a TEXT, col_b TEXT, col_c TEXT, col_d TEXT, col_e TEXT,
    col_f TEXT, col_g TEXT, col_h TEXT, col_i TEXT, col_j TEXT,
    col_k TEXT, col_l TEXT, col_m TEXT, col_n TEXT, col_o TEXT,
    col_p TEXT, col_q TEXT, col_r TEXT, col_s TEXT, col_t TEXT,
    col_u TEXT, col_v TEXT, col_w TEXT, col_x TEXT, col_y TEXT, col_z TEXT,
    col_aa TEXT, col_ab TEXT, col_ac TEXT, col_ad TEXT, col_ae TEXT,
    col_af TEXT, col_ag TEXT, col_ah TEXT, col_ai TEXT, col_aj TEXT,
    col_ak TEXT, col_al TEXT, col_am TEXT, col_an TEXT, col_ao TEXT,
    col_ap TEXT, col_aq TEXT, col_ar TEXT, col_as TEXT, col_at TEXT,
    col_au TEXT, col_av TEXT, col_aw TEXT, col_ax TEXT, col_ay TEXT, col_az TEXT,
    col_ba TEXT, col_bb TEXT,
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
    col_a TEXT, col_b TEXT, col_c TEXT, col_d TEXT, col_e TEXT,
    col_f TEXT, col_g TEXT, col_h TEXT, col_i TEXT, col_j TEXT,
    col_k TEXT, col_l TEXT, col_m TEXT, col_n TEXT, col_o TEXT,
    col_p TEXT, col_q TEXT, col_r TEXT, col_s TEXT, col_t TEXT,
    col_u TEXT, col_v TEXT, col_w TEXT, col_x TEXT, col_y TEXT, col_z TEXT,
    col_aa TEXT, col_ab TEXT, col_ac TEXT, col_ad TEXT, col_ae TEXT,
    col_af TEXT, col_ag TEXT, col_ah TEXT, col_ai TEXT, col_aj TEXT,
    col_ak TEXT, col_al TEXT, col_am TEXT, col_an TEXT, col_ao TEXT,
    col_ap TEXT, col_aq TEXT, col_ar TEXT, col_as TEXT, col_at TEXT,
    col_au TEXT, col_av TEXT, col_aw TEXT, col_ax TEXT, col_ay TEXT, col_az TEXT,
    col_ba TEXT, col_bb TEXT,
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
    col_g TEXT, col_h TEXT, col_i TEXT, col_j TEXT,
    col_k TEXT, col_l TEXT, col_m TEXT, col_n TEXT, col_o TEXT,
    col_p TEXT, col_q TEXT, col_r TEXT, col_s TEXT, col_t TEXT,
    col_u TEXT, col_v TEXT, col_w TEXT, col_x TEXT, col_y TEXT, col_z TEXT,
    col_aa TEXT, col_ab TEXT, col_ac TEXT, col_ad TEXT, col_ae TEXT,
    col_af TEXT, col_ag TEXT, col_ah TEXT, col_ai TEXT, col_aj TEXT,
    col_ak TEXT, col_al TEXT, col_am TEXT, col_an TEXT, col_ao TEXT,
    col_ap TEXT, col_aq TEXT, col_ar TEXT, col_as TEXT, col_at TEXT,
    col_au TEXT, col_av TEXT, col_aw TEXT, col_ax TEXT, col_ay TEXT, col_az TEXT,
    col_ba TEXT, col_bb TEXT,
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
    col_a TEXT, col_b TEXT, col_c TEXT, col_d TEXT, col_e TEXT,
    col_f TEXT, col_g TEXT, col_h TEXT, col_i TEXT, col_j TEXT,
    col_k TEXT, col_l TEXT, col_m TEXT, col_n TEXT, col_o TEXT,
    col_p TEXT, col_q TEXT, col_r TEXT, col_s TEXT, col_t TEXT,
    col_u TEXT, col_v TEXT, col_w TEXT, col_x TEXT, col_y TEXT, col_z TEXT,
    col_aa TEXT, col_ab TEXT, col_ac TEXT, col_ad TEXT, col_ae TEXT,
    col_af TEXT, col_ag TEXT, col_ah TEXT, col_ai TEXT, col_aj TEXT,
    col_ak TEXT, col_al TEXT, col_am TEXT, col_an TEXT, col_ao TEXT,
    col_ap TEXT, col_aq TEXT, col_ar TEXT, col_as TEXT, col_at TEXT,
    col_au TEXT, col_av TEXT, col_aw TEXT, col_ax TEXT, col_ay TEXT, col_az TEXT,
    col_ba TEXT, col_bb TEXT,
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- CRUZAMENTO DE TABELAS - Upload de referência
-- ============================================================
CREATE TABLE IF NOT EXISTS cruzamento_uploads (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(500) NOT NULL,
    original_name VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sheet_count INTEGER DEFAULT 0,
    sheet_names TEXT[]
);

-- Tabela A do cruzamento (1a aba do arquivo)
CREATE TABLE IF NOT EXISTS cruzamento_tabela_a (
    id SERIAL PRIMARY KEY,
    cruzamento_upload_id INTEGER REFERENCES cruzamento_uploads(id) ON DELETE CASCADE,
    row_number INTEGER,
    col_a TEXT, col_b TEXT, col_c TEXT, col_d TEXT, col_e TEXT,
    col_f TEXT, col_g TEXT, col_h TEXT, col_i TEXT, col_j TEXT,
    col_k TEXT, col_l TEXT, col_m TEXT, col_n TEXT, col_o TEXT,
    col_p TEXT, col_q TEXT, col_r TEXT, col_s TEXT, col_t TEXT,
    col_u TEXT, col_v TEXT, col_w TEXT, col_x TEXT, col_y TEXT, col_z TEXT,
    col_aa TEXT, col_ab TEXT, col_ac TEXT, col_ad TEXT, col_ae TEXT,
    col_af TEXT, col_ag TEXT, col_ah TEXT, col_ai TEXT, col_aj TEXT,
    col_ak TEXT, col_al TEXT, col_am TEXT, col_an TEXT, col_ao TEXT,
    col_ap TEXT, col_aq TEXT, col_ar TEXT, col_as TEXT, col_at TEXT,
    col_au TEXT, col_av TEXT, col_aw TEXT, col_ax TEXT, col_ay TEXT, col_az TEXT,
    col_ba TEXT, col_bb TEXT,
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela B do cruzamento (2a aba do arquivo)
CREATE TABLE IF NOT EXISTS cruzamento_tabela_b (
    id SERIAL PRIMARY KEY,
    cruzamento_upload_id INTEGER REFERENCES cruzamento_uploads(id) ON DELETE CASCADE,
    row_number INTEGER,
    col_a TEXT, col_b TEXT, col_c TEXT, col_d TEXT, col_e TEXT,
    col_f TEXT, col_g TEXT, col_h TEXT, col_i TEXT, col_j TEXT,
    col_k TEXT, col_l TEXT, col_m TEXT, col_n TEXT, col_o TEXT,
    col_p TEXT, col_q TEXT, col_r TEXT, col_s TEXT, col_t TEXT,
    col_u TEXT, col_v TEXT, col_w TEXT, col_x TEXT, col_y TEXT, col_z TEXT,
    col_aa TEXT, col_ab TEXT, col_ac TEXT, col_ad TEXT, col_ae TEXT,
    col_af TEXT, col_ag TEXT, col_ah TEXT, col_ai TEXT, col_aj TEXT,
    col_ak TEXT, col_al TEXT, col_am TEXT, col_an TEXT, col_ao TEXT,
    col_ap TEXT, col_aq TEXT, col_ar TEXT, col_as TEXT, col_at TEXT,
    col_au TEXT, col_av TEXT, col_aw TEXT, col_ax TEXT, col_ay TEXT, col_az TEXT,
    col_ba TEXT, col_bb TEXT,
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Resultado do cruzamento (tabela final unindo A e B)
CREATE TABLE IF NOT EXISTS cruzamento_resultado (
    id SERIAL PRIMARY KEY,
    cruzamento_upload_id INTEGER REFERENCES cruzamento_uploads(id) ON DELETE CASCADE,
    codigo TEXT,
    nome_evento TEXT,
    natureza_esocial TEXT,
    cod_fgts TEXT,
    cod_inss TEXT,
    cod_irrf TEXT,
    row_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela Cruzamento (formato col_a..col_bb para o visualizador de tabelas)
CREATE TABLE IF NOT EXISTS tabela_cruzamento (
    id SERIAL PRIMARY KEY,
    upload_id INTEGER,
    row_number INTEGER,
    col_a TEXT, col_b TEXT, col_c TEXT, col_d TEXT, col_e TEXT,
    col_f TEXT, col_g TEXT, col_h TEXT, col_i TEXT, col_j TEXT,
    col_k TEXT, col_l TEXT, col_m TEXT, col_n TEXT, col_o TEXT,
    col_p TEXT, col_q TEXT, col_r TEXT, col_s TEXT, col_t TEXT,
    col_u TEXT, col_v TEXT, col_w TEXT, col_x TEXT, col_y TEXT, col_z TEXT,
    col_aa TEXT, col_ab TEXT, col_ac TEXT, col_ad TEXT, col_ae TEXT,
    col_af TEXT, col_ag TEXT, col_ah TEXT, col_ai TEXT, col_aj TEXT,
    col_ak TEXT, col_al TEXT, col_am TEXT, col_an TEXT, col_ao TEXT,
    col_ap TEXT, col_aq TEXT, col_ar TEXT, col_as TEXT, col_at TEXT,
    col_au TEXT, col_av TEXT, col_aw TEXT, col_ax TEXT, col_ay TEXT, col_az TEXT,
    col_ba TEXT, col_bb TEXT,
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
