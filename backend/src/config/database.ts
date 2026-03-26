import { Pool } from "pg";
import dotenv from "dotenv";

dotenv.config();

const pool = new Pool({
  host: process.env.DB_HOST || "localhost",
  port: parseInt(process.env.DB_PORT || "5432"),
  user: process.env.DB_USER || "easy_social_user",
  password: process.env.DB_PASSWORD || "",
  database: process.env.DB_NAME || "easy_social_db",
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

pool.on("error", (err) => {
  console.error("Erro inesperado no cliente PostgreSQL", err);
  process.exit(-1);
});

/**
 * Criar tabelas se não existirem
 */
export async function initializeDatabase() {
  const client = await pool.connect();

  try {
    // Tabela de uploads
    await client.query(`
      CREATE TABLE IF NOT EXISTS uploads (
        id SERIAL PRIMARY KEY,
        file_name VARCHAR(255) NOT NULL,
        file_size BIGINT NOT NULL,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status VARCHAR(50) DEFAULT 'processing',
        analysis_data JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `);

    // Tabela ANALISE NATUREZA
    await client.query(`
      CREATE TABLE IF NOT EXISTS analise_natureza (
        id SERIAL PRIMARY KEY,
        upload_id INTEGER REFERENCES uploads(id),
        col_a VARCHAR(255),
        col_b VARCHAR(255),
        col_c VARCHAR(255),
        col_d VARCHAR(255),
        col_e VARCHAR(255),
        col_f VARCHAR(255),
        col_g VARCHAR(255),
        col_h VARCHAR(255),
        col_i VARCHAR(255),
        col_j VARCHAR(255),
        raw_data JSONB,
        row_number INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `);

    // Tabela Dinamica
    await client.query(`
      CREATE TABLE IF NOT EXISTS dinamica (
        id SERIAL PRIMARY KEY,
        upload_id INTEGER REFERENCES uploads(id),
        col_a VARCHAR(255),
        col_b VARCHAR(255),
        col_c VARCHAR(255),
        col_d VARCHAR(255),
        col_e VARCHAR(255),
        col_f VARCHAR(255),
        col_g VARCHAR(255),
        col_h VARCHAR(255),
        col_i VARCHAR(255),
        col_j VARCHAR(255),
        raw_data JSONB,
        row_number INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `);

    // Tabela Eventos GI
    await client.query(`
      CREATE TABLE IF NOT EXISTS tabela_eventos_gl (
        id SERIAL PRIMARY KEY,
        upload_id INTEGER REFERENCES uploads(id),
        col_a VARCHAR(255),
        col_b VARCHAR(255),
        col_c VARCHAR(255),
        col_d VARCHAR(255),
        col_e VARCHAR(255),
        col_f VARCHAR(255),
        col_g VARCHAR(255),
        col_h VARCHAR(255),
        col_i VARCHAR(255),
        col_j VARCHAR(255),
        raw_data JSONB,
        row_number INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `);

    // Tabela EB
    await client.query(`
      CREATE TABLE IF NOT EXISTS tabela_eb (
        id SERIAL PRIMARY KEY,
        upload_id INTEGER REFERENCES uploads(id),
        col_a VARCHAR(255),
        col_b VARCHAR(255),
        col_c VARCHAR(255),
        col_d VARCHAR(255),
        col_e VARCHAR(255),
        col_f VARCHAR(255),
        col_g VARCHAR(255),
        col_h VARCHAR(255),
        col_i VARCHAR(255),
        col_j VARCHAR(255),
        raw_data JSONB,
        row_number INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `);

    // Tabela de correções de rubricas (Ponto 1)
    await client.query(`
      CREATE TABLE IF NOT EXISTS rubrica_corrections (
        id SERIAL PRIMARY KEY,
        tabela_eb_id INTEGER REFERENCES tabela_eb(id),
        cod_rubrica TEXT NOT NULL,
        descricao TEXT,
        inss_antes TEXT,
        irrf_antes TEXT,
        fgts_antes TEXT,
        inss_correto TEXT,
        irrf_correto TEXT,
        fgts_correto TEXT,
        status VARCHAR(50) DEFAULT 'pendente',
        corrigido_em TIMESTAMP,
        observacao TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `);

    // Tabela de naturezas eSocial (carregada do TXT governamental)
    await client.query(`
      CREATE TABLE IF NOT EXISTS naturezas_esocial (
        id SERIAL PRIMARY KEY,
        codigo VARCHAR(10) NOT NULL,
        nome VARCHAR(500) NOT NULL,
        descricao TEXT,
        data_inicio DATE,
        data_fim DATE,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `);

    // Tabela de auditoria de correções de natureza
    await client.query(`
      CREATE TABLE IF NOT EXISTS auditoria_naturezas (
        id SERIAL PRIMARY KEY,
        analise_natureza_id INTEGER REFERENCES analise_natureza(id),
        codigoevento VARCHAR(255),
        natureza_anterior TEXT,
        natureza_nova TEXT,
        usuario VARCHAR(255) DEFAULT 'sistema',
        data_alteracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        motivo TEXT
      );
    `);

    // Colunas adicionais para controle de correção de natureza
    await client.query(`
      ALTER TABLE analise_natureza ADD COLUMN IF NOT EXISTS natureza_anterior TEXT;
      ALTER TABLE analise_natureza ADD COLUMN IF NOT EXISTS natureza_nova TEXT;
      ALTER TABLE analise_natureza ADD COLUMN IF NOT EXISTS usuario_correcao VARCHAR(255);
      ALTER TABLE analise_natureza ADD COLUMN IF NOT EXISTS data_correcao TIMESTAMP;
    `);

    // Criar índices
    await client.query(`
      CREATE INDEX IF NOT EXISTS idx_uploads_status ON uploads(status);
      CREATE INDEX IF NOT EXISTS idx_analise_natureza_upload ON analise_natureza(upload_id);
      CREATE INDEX IF NOT EXISTS idx_dinamica_upload ON dinamica(upload_id);
      CREATE INDEX IF NOT EXISTS idx_eventos_gl_upload ON tabela_eventos_gl(upload_id);
      CREATE INDEX IF NOT EXISTS idx_tabela_eb_upload ON tabela_eb(upload_id);
      CREATE INDEX IF NOT EXISTS idx_rubrica_corrections_status ON rubrica_corrections(status);
      CREATE INDEX IF NOT EXISTS idx_rubrica_corrections_eb ON rubrica_corrections(tabela_eb_id);
      CREATE INDEX IF NOT EXISTS idx_naturezas_codigo ON naturezas_esocial(codigo);
      CREATE INDEX IF NOT EXISTS idx_auditoria_naturezas_an ON auditoria_naturezas(analise_natureza_id);
    `);

    console.log("✅ Banco de dados inicializado com sucesso");
  } catch (error: any) {
    console.error("❌ Erro ao inicializar banco de dados:", error);
    throw error;
  } finally {
    client.release();
  }
}

export default pool;
